#!/usr/bin/env python
"""Quetta subsidence SCENARIO + damage-risk + exposure pipeline (single entry point).

    python -I impact_pipeline.py --rate <vertical-velocity.tif cm/yr, negative=sinking> \
                                 --rate-unc <1-sigma uncertainty.tif cm/yr> \
                                 --out <output dir> [--data <cache dir>] [--label PROVISIONAL]

These are RISK SCENARIOS WITH UNCERTAINTY, not forecasts.  See METHODS.md.
"""
import argparse, os, sys, json, gzip, math, csv, urllib.request, datetime as dt
import numpy as np
import rasterio
from rasterio.transform import from_origin, Affine
from rasterio.warp import reproject, Resampling
from rasterio.merge import merge
from scipy import ndimage as ndi

# ----------------------------------------------------------------------------- constants
AOI = (66.80, 67.20, 30.00, 30.40)           # lon_min, lon_max, lat_min, lat_max
T0 = 2026.0                                  # cumulative subsidence counted from 1 Jan 2026
YEARS = list(range(2026, 2051))
OUT_YEARS = [2030, 2040, 2050]
DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{t}_00_DEM/Copernicus_DSM_COG_10_{t}_00_DEM.tif"
DEM_TILES = ["N30_00_E066", "N30_00_E067"]
MS_LINKS = "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv"
POP_URL = "https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2025/PAK/v1/100m/constrained/pak_pop_2025_CN_100m_R2025A_v1.tif"

# valley mask (see METHODS.md)
ELEV_MAX = 1750.0          # m a.s.l. (valley floor ~1,600-1,700 m; city ~1,680 m)
SLOPE_MAX = 4.0            # degrees, mean slope on the analysis grid
MASK_BBOX = (66.88, 67.10, 30.04, 30.30)

# scenario parameters (see METHODS.md for justification)
S2_GROWTH = (0.5, 2.6, 4.0)      # %/yr triangular(min, mode, max); history gives 2.6 %/yr
S2_CAP = (1.3, 1.8)              # cap on rate as multiple of today's local rate, uniform
S3_INTERV = (2027, 2030)         # intervention year, uniform integer
S3_TAU = (5.0, 15.0)             # e-folding time (yr), log-uniform
CORR_PX = 12                     # correlation length of rate-error field (pixels ~ 1 km)
RHO = 0.7                        # share of rate-uncertainty variance that is spatially common

# damage classes on angular distortion beta (m/m)
BETA_EDGES = [1 / 1000, 1 / 500, 1 / 300, 1 / 150]
CLASS_NAMES = ["0 negligible (<1/1000)", "1 low (1/1000-1/500)", "2 slight: cracking onset (1/500-1/300)",
               "3 moderate: panel/brick wall cracking (1/300-1/150)", "4 severe: structural damage risk (>=1/150)"]
CLASS_SHORT = ["negligible", "low", "slight", "moderate", "severe"]
SCEN = {"S1": "Current trend", "S2": "Keeps accelerating", "S3": "Pumping controlled"}


def log(*a):
    print(*a, flush=True)


# ----------------------------------------------------------------------------- download helpers
def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    log("downloading", url)
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "quetta-impact-pipeline"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(tmp, dest)
    return dest


def quadkey(lon, lat, z=9):
    x = int((lon + 180) / 360 * 2 ** z)
    s = math.sin(math.radians(lat))
    y = int((0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * 2 ** z)
    q = ""
    for i in range(z, 0, -1):
        d = 0
        m = 1 << (i - 1)
        if x & m: d += 1
        if y & m: d += 2
        q += str(d)
    return q


def get_buildings(data):
    """Microsoft Global ML Building Footprints (GeoJSONL) -> centroid array (lon, lat)."""
    cache = os.path.join(data, "bld", "centroids_aoi.npy")
    if os.path.exists(cache):
        return np.load(cache)
    links = fetch(MS_LINKS, os.path.join(data, "bld", "dataset-links.csv"))
    qks = set()
    for lo in np.linspace(AOI[0], AOI[1], 9):
        for la in np.linspace(AOI[2], AOI[3], 9):
            qks.add(quadkey(lo, la))
    urls = []
    with open(links, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Location"] == "Pakistan" and r["QuadKey"] in qks:
                urls.append((r["QuadKey"], r["Url"]))
    log("building quadkeys", urls and [u[0] for u in urls])
    pts = []
    for qk, url in urls:
        p = fetch(url, os.path.join(data, "bld", f"q{qk}.csv.gz"))
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    g = json.loads(line)["geometry"]["coordinates"][0]
                except Exception:
                    continue
                a = np.asarray(g, float)
                cx, cy = a[:, 0].mean(), a[:, 1].mean()   # vertex mean ~ centroid for small footprints
                if AOI[0] <= cx <= AOI[1] and AOI[2] <= cy <= AOI[3]:
                    pts.append((cx, cy))
    pts = np.array(pts, float)
    np.save(cache, pts)
    return pts


# ----------------------------------------------------------------------------- grid / inputs
def read_on_grid(path, ref_prof):
    with rasterio.open(path) as src:
        dst = np.full((ref_prof["height"], ref_prof["width"]), np.nan, "float32")
        reproject(rasterio.band(src, 1), dst, src_transform=src.transform, src_crs=src.crs,
                  dst_transform=ref_prof["transform"], dst_crs=ref_prof["crs"], resampling=Resampling.bilinear,
                  src_nodata=src.nodata, dst_nodata=np.nan)
    return dst


def metre_scales(lat):
    return 111320.0 * np.cos(np.radians(lat)), 110574.0


def make_mask(rate, lon, lat, elev, slope):
    m = np.isfinite(rate) & np.isfinite(elev)
    m &= (lon >= MASK_BBOX[0]) & (lon <= MASK_BBOX[1]) & (lat >= MASK_BBOX[2]) & (lat <= MASK_BBOX[3])
    m &= (elev <= ELEV_MAX) & (slope <= SLOPE_MAX)
    m = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s >= 200]
        m = np.isin(lab, keep)
    m = ndi.binary_fill_holes(m)
    return m


# ----------------------------------------------------------------------------- scenarios
def sample_params(rng, n):
    P = {}
    P["zg"] = rng.standard_normal(n)
    P["g"] = rng.triangular(S2_GROWTH[0], S2_GROWTH[1], S2_GROWTH[2], n) / 100.0
    P["cap"] = rng.uniform(*S2_CAP, n)
    P["Ti"] = rng.integers(S3_INTERV[0], S3_INTERV[1] + 1, n).astype(float)
    P["tau"] = np.exp(rng.uniform(np.log(S3_TAU[0]), np.log(S3_TAU[1]), n))
    return P


def cum_factor(scen, year, P, r0):
    """Cumulative subsidence (cm, positive down) from T0 to `year` for sinking rate r0 (cm/yr >=0,
    shape (npix, ndraw)); parameters per draw are arrays (ndraw,)."""
    t = year - T0
    if scen == "S1":
        return r0 * t
    if scen == "S2":
        g = P["g"][None, :]
        cap = P["cap"][None, :]
        # rate(t)=r0*min(exp(g t), cap)  (continuous compounding approx of g %/yr)
        tc = np.log(cap) / g                       # time at which cap is reached (draw, pix)
        tc = np.clip(tc, 0, None)
        tt = np.minimum(t, tc)
        grow = (np.exp(g * tt) - 1) / g
        after = cap * np.maximum(t - tc, 0)
        return r0 * (grow + after)
    if scen == "S3":
        Ti = P["Ti"][None, :] - T0
        tau = P["tau"][None, :]
        t1 = np.minimum(t, Ti)
        t2 = np.maximum(t - Ti, 0)
        return r0 * (t1 + tau * (1 - np.exp(-t2 / tau)))
    raise ValueError(scen)


# ----------------------------------------------------------------------------- damage
def beta_field(cum_cm, mask, lat, res):
    """Angular distortion proxy = |grad(subsidence)| in m/m, lightly smoothed (sigma 1 px)."""
    z = np.where(mask, cum_cm / 100.0, np.nan)
    # fill outside mask by nearest valid so the gradient does not see the mask edge as a cliff
    idx = ndi.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    zf = z[tuple(idx)]
    zs = ndi.gaussian_filter(zf, 1.0)
    mx, my = metre_scales(lat)
    dx = res * mx
    dy = res * my
    gy, gx = np.gradient(zs)
    gx = gx / dx
    gy = -gy / dy   # rows go southward
    b = np.hypot(gx, gy)
    b[~mask] = np.nan
    return b


def classify(beta):
    c = np.full(beta.shape, 255, np.uint8)
    ok = np.isfinite(beta)
    c[ok] = np.digitize(beta[ok], BETA_EDGES).astype(np.uint8)
    return c


def fissure_zone(cum_cm, beta, mask):
    ok = mask & np.isfinite(beta)
    mx = np.nanmax(cum_cm[ok])
    flank = ok & (cum_cm >= 0.10 * mx) & (cum_cm <= 0.70 * mx) & (cum_cm >= 20)
    if flank.sum() < 20:
        return np.zeros(mask.shape, bool)
    thr = max(np.nanpercentile(beta[flank], 90), BETA_EDGES[0])
    return flank & (beta >= thr)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rate", required=True)
    ap.add_argument("--rate-unc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--data", default=None, help="download cache dir (default: <out>/../_impact_data)")
    ap.add_argument("--label", default="", help="e.g. PROVISIONAL; stamped on every output")
    ap.add_argument("--draws", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20260)
    ap.add_argument("--no-rf", action="store_true")
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    data = os.path.abspath(a.data) if a.data else os.path.join(os.path.dirname(out), "_impact_data")
    os.makedirs(out, exist_ok=True)
    os.makedirs(data, exist_ok=True)
    label = a.label.strip()
    suffix = f"_{label}" if label else ""
    rng = np.random.default_rng(a.seed)

    # ---- grid from the rate raster
    with rasterio.open(a.rate) as src:
        assert src.crs and src.crs.to_epsg() == 4326, "rate raster must be EPSG:4326"
        prof = dict(height=src.height, width=src.width, transform=src.transform, crs=src.crs)
        rate_in = src.read(1).astype("float32")
        if src.nodata is not None and not np.isnan(src.nodata):
            rate_in[rate_in == src.nodata] = np.nan
    H, W = prof["height"], prof["width"]
    tf = prof["transform"]
    res = tf.a
    lons = tf.c + (np.arange(W) + 0.5) * tf.a
    lats = tf.f + (np.arange(H) + 0.5) * tf.e
    LON, LAT = np.meshgrid(lons, lats)
    unc_in = read_on_grid(a.rate_unc, prof)
    log("grid", H, W, "res", res)

    # ---- DEM -> elevation/slope on grid
    dems = [fetch(DEM_URL.format(t=t), os.path.join(data, "dem", f"{t}.tif")) for t in DEM_TILES]
    srcs = [rasterio.open(p) for p in dems]
    mos, mtf = merge(srcs, bounds=(AOI[0] - 0.02, AOI[2] - 0.02, AOI[1] + 0.02, AOI[3] + 0.02), nodata=-9999)
    for s in srcs: s.close()
    dem30 = mos[0].astype("float32")
    dem30[dem30 < -1000] = np.nan
    # slope at 30 m
    mx0, my0 = metre_scales(30.2)
    gy, gx = np.gradient(np.nan_to_num(dem30, nan=np.nanmedian(dem30)), mtf.e * -1 * my0, mtf.a * mx0)
    slope30 = np.degrees(np.arctan(np.hypot(gx, gy))).astype("float32")
    def to_grid(arr, method=Resampling.average):
        dst = np.full((H, W), np.nan, "float32")
        reproject(arr, dst, src_transform=mtf, src_crs="EPSG:4326", dst_transform=tf, dst_crs="EPSG:4326",
                  resampling=method, src_nodata=np.nan, dst_nodata=np.nan)
        return dst
    elev = to_grid(dem30)
    slope = to_grid(slope30)
    # hillshade for maps (30 m -> grid)
    az, alt = np.radians(315), np.radians(45)
    asp = np.arctan2(-gx, gy)
    hs = np.sin(alt) * np.cos(np.arctan(np.hypot(gx, gy))) + np.cos(alt) * np.sin(np.arctan(np.hypot(gx, gy))) * np.cos(az - asp)
    hill = to_grid(hs.astype("float32"))

    mask = make_mask(rate_in, LON, LAT, elev, slope)
    log("valley mask pixels", int(mask.sum()), "of", H * W)

    # fill no-data holes inside the mask (e.g. decorrelated core) with nearest valid value; uncertainty inflated x1.5 there
    bad = mask & ~(np.isfinite(rate_in) & np.isfinite(unc_in))
    frac_filled = float(bad.sum() / max(mask.sum(), 1))
    good = np.isfinite(rate_in) & np.isfinite(unc_in)
    idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    rate_f = rate_in[tuple(idx)]
    unc_f = unc_in[tuple(idx)] * np.where(bad, 1.5, 1.0)
    rate = np.where(mask, rate_f, np.nan)
    unc = np.where(mask, unc_f, np.nan)
    log("mask pixels filled from nearest valid:", f"{100*frac_filled:.1f}%")
    # sinking rate magnitude (cm/yr, >=0); uplift/noise treated as 0 sinking in the median
    sink0 = np.clip(-rate[mask], 0, None)
    sig = unc[mask]
    npx = int(mask.sum())

    # pixel area km2
    mxg, myg = metre_scales(LAT)
    pix_km2 = (res * mxg * res * myg) / 1e6
    pix_km2_m = pix_km2[mask]

    # ---- Monte Carlo
    nd = a.draws
    P = sample_params(rng, nd)
    # pixel-level error: spatially correlated Gaussian field (correlation length ~ CORR_PX pixels) per draw,
    # because InSAR atmospheric/orbital errors are spatially correlated (independent per-pixel noise would
    # inflate the bowl maximum by selecting the luckiest pixel).
    nrm = 1.0 / math.sqrt(4 * math.pi * CORR_PX ** 2)
    zp = np.empty((npx, nd), "float32")
    for k in range(nd):
        f = ndi.gaussian_filter(rng.standard_normal((H, W)), CORR_PX, mode="reflect") / nrm
        zp[:, k] = f[mask]
    z = (math.sqrt(RHO) * P["zg"][None, :] + math.sqrt(1 - RHO) * zp).astype("float32")
    r0 = np.clip(-(rate[mask][:, None] + sig[:, None] * z), 0, None).astype("float32")   # sinking cm/yr (npx, nd)
    del zp, z
    res_med, res_p10, res_p90 = {}, {}, {}
    ts = {}              # scenario -> year -> dict(max med/p10/p90)
    area_exceed = {}     # scenario -> year -> thr -> (p10, med, p90) km2
    thresholds = [0.5, 1.0, 2.0, 3.0]
    for sc in SCEN:
        ts[sc] = {}
        area_exceed[sc] = {}
        for y in YEARS:
            D = cum_factor(sc, y, P, r0).astype("float32")
            mxd = D.max(0)
            ts[sc][y] = [float(np.percentile(mxd, q)) for q in (10, 50, 90)]
            if y in OUT_YEARS:
                p = np.percentile(D, [10, 50, 90], axis=1)
                res_p10[(sc, y)], res_med[(sc, y)], res_p90[(sc, y)] = p[0], p[1], p[2]
                ae = {}
                for th in thresholds:
                    A = ((D >= th * 100) * pix_km2_m[:, None]).sum(0)
                    ae[th] = [float(np.percentile(A, q)) for q in (10, 50, 90)]
                area_exceed[sc][y] = ae
            del D
        log("scenario done", sc)

    def full(v):
        o = np.full((H, W), np.nan, "float32")
        o[mask] = v
        return o

    # ---- exposure inputs
    bpts = get_buildings(data)
    log("building centroids in AOI", len(bpts))
    bi = np.floor((tf.f - bpts[:, 1]) / res).astype(int)
    bj = np.floor((bpts[:, 0] - tf.c) / res).astype(int)
    okb = (bi >= 0) & (bi < H) & (bj >= 0) & (bj < W)
    bcount = np.zeros((H, W), np.float32)
    np.add.at(bcount, (bi[okb], bj[okb]), 1)
    popfile = fetch(POP_URL, os.path.join(data, "pop", "pak_pop_2025_CN_100m_R2025A_v1.tif"))
    with rasterio.open(popfile) as ps:
        win = rasterio.windows.from_bounds(AOI[0], AOI[2], AOI[1], AOI[3], ps.transform)
        win = win.round_offsets().round_lengths()
        parr = ps.read(1, window=win).astype("float64")
        ptf = ps.window_transform(win)
        pn = ps.nodata
    if pn is not None:
        parr[parr == pn] = 0
    parr[~np.isfinite(parr) | (parr < 0)] = 0
    pr, pc = np.nonzero(parr > 0)
    plon = ptf.c + (pc + 0.5) * ptf.a
    plat = ptf.f + (pr + 0.5) * ptf.e
    pi = np.floor((tf.f - plat) / res).astype(int)
    pj = np.floor((plon - tf.c) / res).astype(int)
    okp = (pi >= 0) & (pi < H) & (pj >= 0) & (pj < W)
    pcount = np.zeros((H, W), np.float64)
    np.add.at(pcount, (pi[okp], pj[okp]), parr[pr[okp], pc[okp]])
    pop_total_aoi = float(parr.sum())
    log("population in AOI", pop_total_aoi, "in valley mask", float(pcount[mask].sum()))
    bc_m = np.where(mask, bcount, 0)
    pc_m = np.where(mask, pcount, 0)

    # ---- damage classes + exposure
    exposure_rows = []
    classes, betas, fissures = {}, {}, {}
    for sc in SCEN:
        for y in OUT_YEARS:
            for fld, store in (("median", res_med), ("p10", res_p10), ("p90", res_p90)):
                cum = full(store[(sc, y)])
                b = beta_field(cum, mask, LAT, res)
                c = classify(b)
                fz = fissure_zone(cum, b, mask)
                if fld == "median":
                    classes[(sc, y)], betas[(sc, y)], fissures[(sc, y)] = c, b, fz
                for k in range(5):
                    sel = (c == k)
                    exposure_rows.append(dict(scenario=sc, scenario_name=SCEN[sc], year=y, field=fld, zone=f"class_{k}_{CLASS_SHORT[k]}",
                                              area_km2=float(pix_km2[sel].sum()), buildings=int(bc_m[sel].sum()),
                                              people=float(pc_m[sel].sum())))
                exposure_rows.append(dict(scenario=sc, scenario_name=SCEN[sc], year=y, field=fld, zone="fissure_risk_flank",
                                          area_km2=float(pix_km2[fz].sum()), buildings=int(bc_m[fz].sum()), people=float(pc_m[fz].sum())))
                for th in (0.5, 1.0, 2.0):
                    sel = np.isfinite(cum) & (cum >= th * 100)
                    exposure_rows.append(dict(scenario=sc, scenario_name=SCEN[sc], year=y, field=fld, zone=f"cum_ge_{th}m",
                                              area_km2=float(pix_km2[sel].sum()), buildings=int(bc_m[sel].sum()), people=float(pc_m[sel].sum())))
    for th in (5, 10):
        sel = mask & (-rate >= th)
        exposure_rows.append(dict(scenario="today", scenario_name="measured rate", year=2026, field="median", zone=f"rate_ge_{th}cm_yr",
                                  area_km2=float(pix_km2[sel].sum()), buildings=int(bc_m[sel].sum()), people=float(pc_m[sel].sum())))
    exposure_rows.append(dict(scenario="all", scenario_name="valley mask total", year=2026, field="median", zone="valley_mask_total",
                              area_km2=float(pix_km2[mask].sum()), buildings=int(bc_m[mask].sum()), people=float(pc_m[mask].sum())))
    for r in exposure_rows:
        r["label"] = label or "FINAL"

    # ---- write rasters
    def wtif(name, arr, dtype="float32", nodata=np.nan, desc=""):
        p = os.path.join(out, "geotiffs", name + suffix + ".tif")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with rasterio.open(p, "w", driver="GTiff", height=H, width=W, count=1, dtype=dtype, crs="EPSG:4326",
                           transform=tf, nodata=nodata, compress="deflate") as d:
            d.write(arr.astype(dtype), 1)
            d.update_tags(DESCRIPTION=desc, STATUS=label or "FINAL", NOTE="Scenario output, not a forecast")
        return p
    for sc in SCEN:
        for y in OUT_YEARS:
            for fld, store in (("median", res_med), ("p10", res_p10), ("p90", res_p90)):
                wtif(f"cum_subsidence_{sc}_{y}_{fld}_cm", full(store[(sc, y)]), desc=f"{SCEN[sc]} {y} {fld} cumulative subsidence since 2026-01-01, cm (positive = down)")
            wtif(f"damage_class_{sc}_{y}", np.where(classes[(sc, y)] == 255, 255, classes[(sc, y)]), "uint8", 255,
                 "0 negligible,1 low,2 slight,3 moderate,4 severe (zone-level angular-distortion screening class, median field)")
            wtif(f"angular_distortion_{sc}_{y}", betas[(sc, y)], desc="angular distortion proxy m/m from median field (80 m grid)")
            wtif(f"fissure_risk_{sc}_{y}", fissures[(sc, y)].astype("uint8"), "uint8", 255, "1 = heuristic fissure-risk flank zone")
    wtif("rate_used_cm_yr", rate, desc="vertical velocity used, valley-masked")
    wtif("rate_unc_used_cm_yr", np.where(mask, unc, np.nan), desc="rate 1-sigma used")
    wtif("valley_mask", mask.astype("uint8"), "uint8", 255, "1 = valley floor")
    wtif("buildings_per_pixel", np.where(mask, bcount, np.nan), desc="Microsoft ML building centroids per pixel")
    wtif("population_per_pixel", np.where(mask, pcount, np.nan).astype("float32"), desc="WorldPop 2025 constrained 100 m, people per pixel")
    wtif("elevation_m", elev, desc="Copernicus GLO-30 mean elevation")

    # ---- headline numbers
    ctr = (66.99, 30.18)
    ci, cj = int((tf.f - ctr[1]) / res), int((ctr[0] - tf.c) / res)
    summary = dict(
        label=label or "FINAL", disclaimer="Scenario analysis with uncertainty, not a forecast. Zone-level screening, not building assessment.",
        generated=dt.datetime.now().isoformat(timespec="seconds"), inputs=dict(rate=os.path.abspath(a.rate), rate_unc=os.path.abspath(a.rate_unc)),
        draws=nd, seed=a.seed, t0=T0,
        parameters=dict(S1="constant rate", S2=dict(growth_pct_per_yr_triangular=S2_GROWTH, cap_multiple_of_current_rate_uniform=S2_CAP),
                        S3=dict(intervention_year_uniform_int=S3_INTERV, efolding_yr_loguniform=S3_TAU),
                        spatial_common_fraction_of_rate_uncertainty=RHO, error_field_corr_length_px=CORR_PX, valley_mask=dict(elev_max_m=ELEV_MAX, slope_max_deg=SLOPE_MAX, bbox=MASK_BBOX),
                        beta_class_edges=BETA_EDGES),
        valley=dict(pixels=npx, frac_pixels_filled_from_neighbours=frac_filled, area_km2=float(pix_km2_m.sum()), buildings=int(bc_m.sum()), people=float(pc_m.sum()),
                    people_whole_aoi_worldpop=pop_total_aoi, building_centroids_aoi=int(len(bpts))),
        rate_today=dict(max_sinking_cm_yr=float(-np.nanmin(rate)), p99_sinking_cm_yr=float(-np.nanpercentile(rate, 1)),
                        city_centre_cm_yr=float(rate[ci, cj]) if np.isfinite(rate[ci, cj]) else None,
                        median_unc_cm_yr=float(np.nanmedian(unc))),
        scenarios={})
    for sc in SCEN:
        sd = dict(name=SCEN[sc], bowl_max_cm={}, area_km2_exceeding={}, bowl_max_timeseries_cm={str(y): ts[sc][y] for y in YEARS})
        for y in OUT_YEARS:
            sd.setdefault("bowl_max_of_median_field_cm", {})[str(y)] = float(np.max(res_med[(sc, y)]))
            sd["bowl_max_cm"][str(y)] = dict(p10=ts[sc][y][0], median=ts[sc][y][1], p90=ts[sc][y][2])
            sd["area_km2_exceeding"][str(y)] = {f"{th}m": dict(p10=v[0], median=v[1], p90=v[2]) for th, v in area_exceed[sc][y].items()}
        summary["scenarios"][sc] = sd
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(out, "exposure.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["label", "scenario", "scenario_name", "year", "field", "zone", "area_km2", "buildings", "people"])
        w.writeheader()
        for r in exposure_rows:
            w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    # pixel table for apps
    import pandas as pd
    df = pd.DataFrame(dict(lon=LON[mask], lat=LAT[mask], rate_cm_yr=rate[mask], rate_unc_cm_yr=unc[mask], elev_m=elev[mask],
                           buildings=bc_m[mask], people=pc_m[mask]))
    for sc in SCEN:
        for y in OUT_YEARS:
            df[f"{sc}_{y}_med_cm"] = res_med[(sc, y)]
            df[f"{sc}_{y}_p10_cm"] = res_p10[(sc, y)]
            df[f"{sc}_{y}_p90_cm"] = res_p90[(sc, y)]
            df[f"{sc}_{y}_class"] = classes[(sc, y)][mask]
            df[f"{sc}_{y}_fissure"] = fissures[(sc, y)][mask].astype(int)
    df.round(4).to_csv(os.path.join(out, f"pixel_table{suffix}.csv.gz"), index=False, compression="gzip")

    ctx = dict(mask=mask, rate=rate, unc=unc, elev=elev, hill=hill, lons=lons, lats=lats, LON=LON, LAT=LAT, bcount=bcount, pcount=pcount,
               res_med=res_med, res_p10=res_p10, res_p90=res_p90, full=full, ts=ts, classes=classes, betas=betas, fissures=fissures,
               exposure_rows=exposure_rows, summary=summary, label=label, out=out, pix_km2=pix_km2, bpts=bpts, slope=slope)
    if not a.no_figures:
        import make_figures
        make_figures.run(ctx)
    if not a.no_rf:
        try:
            import drivers_rf
            drivers_rf.run(ctx)
        except Exception as e:  # optional
            log("RF drivers skipped:", repr(e))
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    log("done ->", out)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
