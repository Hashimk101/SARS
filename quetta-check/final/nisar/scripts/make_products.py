"""Final NISAR Quetta products: per-track LOS velocity (+ optional DEM atmosphere correction), resampling to EPSG:4326,
ascending+descending inversion for vertical and east velocity, GeoTIFFs, summary.json and an intermediate npz for figures.

usage: make_products.py <pipeline_scripts_dir> <pipeline_out_dir> <dem_npz|none> <geom_dir> <s1_unw.tif> <s1_cc.tif> <outdir>
  pipeline_out_dir: folder holding the track dirs written by nisar_quetta.py (track041_frame017_noiono, track142_frame017,
  track092_frame073, track020_frame073). Run with a venv that has numpy+scipy+tifffile (-I)."""
import json, sys
from pathlib import Path
import numpy as np
import tifffile
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, sys.argv[1])
import nlib
import nisar_quetta as nq
from scipy.ndimage import map_coordinates

pipe_out, dem_npz, geom_dir, s1_unw, s1_cc, outdir = sys.argv[2:8]
pipe_out, geom_dir, outdir = Path(pipe_out), Path(geom_dir), Path(outdir)
(outdir / "geotiff").mkdir(parents=True, exist_ok=True); (outdir / "work").mkdir(exist_ok=True)

TRACKS = [  # key, track, frame, pass, directory, nominal geometry used only if geom file is missing
    dict(key="041", track=41, frame=17, pas="ascending", dir="track041_frame017_noiono"),
    dict(key="142", track=142, frame=17, pas="ascending", dir="track142_frame017_iono", iono=True),
    dict(key="092", track=92, frame=73, pas="descending", dir="track092_frame073"),
    dict(key="020", track=20, frame=73, pas="descending", dir="track020_frame073_iono", iono=True),
]
AOI = nq.AOI
STEP = 0.00075
lon1 = np.arange(AOI["lon0"], AOI["lon1"] + 1e-9, STEP) + STEP / 2
lat1 = np.arange(AOI["lat1"], AOI["lat0"] - 1e-9, -STEP) - STEP / 2          # north-up
LON, LAT = np.meshgrid(lon1, lat1)
PIX_KM2 = (STEP * 111.195) * (STEP * 111.195 * np.cos(np.radians(30.2)))

s1 = nlib.load_s1(s1_unw, s1_cc)
s1_grid = nlib.s1_on_grid(s1, LON, LAT)
dem_ok = dem_npz.lower() != "none" and Path(dem_npz).exists()


def to_grid(arr, x, y, epsg, valid_thresh=0.5, nan_aware=True):
    """Bilinear resampling of an (ny,nx) UTM-grid array onto the 4326 grid; NaN-aware (normalised weights)."""
    X, Y = nq.lonlat_to_xy(LON, LAT, epsg)
    ci = (X - x[0]) / (x[1] - x[0]); ri = (Y - y[0]) / (y[1] - y[0])
    if not nan_aware:
        return map_coordinates(arr.astype(float), [ri, ci], order=1, mode="constant", cval=np.nan)
    v = np.isfinite(arr)
    a = np.where(v, arr, 0.0).astype(float)
    num = map_coordinates(a, [ri, ci], order=1, mode="constant", cval=0.0)
    w = map_coordinates(v.astype(float), [ri, ci], order=1, mode="constant", cval=0.0)
    return np.where(w >= valid_thresh, num / np.maximum(w, 1e-9), np.nan)


def reg_series(t, y):
    ok = np.isfinite(y)
    t, y = t[ok], y[ok]
    n = len(t)
    A = np.column_stack([np.ones(n), t])
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ c
    sxx = ((t - t.mean()) ** 2).sum()
    return float(c[1]), float(np.sqrt((res ** 2).sum() / (n - 2) / sxx))


summary = dict(tracks={}, corrections={}, notes=[])
per = {}
for T in TRACKS:
    d = pipe_out / T["dir"]
    npz = sorted(d.glob("*_cumulative_disp.npz"))[0]
    tr = nlib.load_track(npz)
    lon, lat, cum, t = tr["lon"], tr["lat"], tr["cum"], tr["t"]
    s1g = nlib.s1_on_grid(s1, lon, lat)
    stable = nlib.stable_mask(lon, lat, s1g)
    # --- raw velocity + metrics
    fv0 = nlib.fit_velocity(cum, t)
    m0 = nlib.metrics(nlib.smooth(fv0["v"]), lon, lat, s1g)
    chosen, cum_use, fv, mD, bcoef, h = "none", cum, fv0, None, None, None
    dem_info = dict(applied=False)
    if dem_ok:
        h = nlib.dem_on_grid(dem_npz, lon, lat)
        cumD, bcoef = nlib.dem_correct(cum, h, lon, lat, stable)
        fvD = nlib.fit_velocity(cumD, t)
        mD = nlib.metrics(nlib.smooth(fvD["v"]), lon, lat, s1g)
        keep = (mD["r"] >= m0["r"] - 0.01) and (mD["outside_robust_sigma"] < 0.97 * m0["outside_robust_sigma"])
        dem_info = dict(applied=bool(keep), r_before=m0["r"], r_after=mD["r"],
                        outside_sigma_before=m0["outside_robust_sigma"], outside_sigma_after=mD["outside_robust_sigma"],
                        outside_frac_below_m3_before=m0["outside_frac_below_m3"], outside_frac_below_m3_after=mD["outside_frac_below_m3"],
                        bowl_median_before=m0["bowl_median"], bowl_median_after=mD["bowl_median"],
                        elevation_slope_cm_per_km_per_epoch=[round(float(b), 3) for b in bcoef],
                        rule="keep if r does not drop by >0.01 and robust sigma of rate outside the valley falls by >3%")
        if keep:
            chosen, cum_use, fv = "dem", cumD, fvD
    m = mD if (chosen == "dem") else m0
    rs = nlib.smooth(fv["v"])
    # --- stable-ground empirical noise (unsmoothed rate)
    st_v = fv["v"][stable & np.isfinite(fv["v"])]
    floor = float(1.4826 * np.median(np.abs(st_v - np.median(st_v))))
    med_se = float(np.nanmedian(fv["se"][stable]))
    # --- city centre
    ci_, cj_ = nlib.nearest = None, None
    d2 = ((lon - nlib.CITY[0]) * np.cos(np.radians(30.18))) ** 2 + (lat - nlib.CITY[1]) ** 2
    i0, j0 = np.unravel_index(np.argmin(d2), d2.shape)
    win = cum_use[:, i0 - 1:i0 + 2, j0 - 1:j0 + 2]
    cser = np.array([np.nanmedian(w) if np.isfinite(w).any() else np.nan for w in win])
    cv, cse = reg_series(t, cser)
    cser_raw = np.array([np.nanmedian(w) if np.isfinite(w).any() else np.nan for w in cum[:, i0 - 1:i0 + 2, j0 - 1:j0 + 2]])
    # --- valid fractions
    inaoi = (lon >= AOI["lon0"]) & (lon <= AOI["lon1"]) & (lat >= AOI["lat0"]) & (lat <= AOI["lat1"])
    invalley = nlib.box(lon, lat, nlib.VALLEY)
    summary["tracks"][T["key"]] = dict(
        track=T["track"], frame=T["frame"], pass_direction=T["pas"], dates=tr["dates"], n_pairs=len(tr["dates"]) - 1,
        span_days=int((np.datetime64(tr["dates"][-1]) - np.datetime64(tr["dates"][0])).astype(int)),
        valid_fraction_aoi=float(np.isfinite(fv["v"][inaoi]).mean()), valid_fraction_valley_box=float(np.isfinite(fv["v"][invalley]).mean()),
        correction_used=chosen, r_vs_s1=m["r"], n_compared_px=m["n_compared"],
        median_in_s1_bowl_cm_yr=m["bowl_median"], median_valley_outside_bowl_cm_yr=m["calm_median"],
        s1_median_in_bowl_cm_yr=m["s1_bowl_median"], s1_median_valley_outside_bowl_cm_yr=m["s1_calm_median"],
        bowl_n_px=m["bowl_n"], calm_n_px=m["calm_n"],
        outside_valley_robust_sigma_cm_yr=m["outside_robust_sigma"], outside_valley_frac_below_minus3=m["outside_frac_below_m3"],
        metrics_without_dem=m0, metrics_with_dem=mD,
        stable_ground_empirical_sigma_cm_yr=floor, median_formal_se_cm_yr=med_se,
        city_centre=dict(cumulative_cm_end=float(cser[-1]), velocity_cm_yr=cv, velocity_se_cm_yr=cse,
                         series_dates=tr["dates"], series_cm=[None if not np.isfinite(v) else round(float(v), 3) for v in cser],
                         series_cm_without_dem=[None if not np.isfinite(v) else round(float(v), 3) for v in cser_raw]))
    summary["corrections"].setdefault("dem", {})[T["key"]] = dem_info
    per[T["key"]] = dict(tr=tr, fv=fv, floor=floor, med_se=med_se, rs=rs, s1g=s1g, h=h, chosen=chosen)
    print(T["key"], T["pas"], "corr", chosen, "r %.2f" % m["r"], "bowl %.1f calm %.1f" % (m["bowl_median"], m["calm_median"]),
          "floor %.2f se %.2f" % (floor, med_se), "DEM:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in dem_info.items() if k != "elevation_slope_cm_per_km_per_epoch"}, flush=True)
    np.savez_compressed(outdir / "work" / f"track{T['key']}_native.npz", lon=lon, lat=lat, v=fv["v"], se=fv["se"], n=fv["n"],
                        cum=cum_use.astype(np.float32), t=t, dates=np.array(tr["dates"]), s1=s1g, smooth_v=rs)

# --------------------------------------------------------------------- geometry
geomq = {}
for T in TRACKS:
    gp = geom_dir / f"geom_track{T['track']:03d}.npz"
    ap = geom_dir / f"attrs_track{T['track']:03d}.json"
    if gp.exists():
        g = np.load(gp)
        look = None
        if ap.exists():
            look = json.loads(ap.read_text()).get("identification", {}).get("lookDirection")
        ex, ey, inc = (to_grid(g[k], g["x"], g["y"], int(g["epsg"]), nan_aware=False) for k in ("losUnitVectorX", "losUnitVectorY", "incidenceAngle"))
        ez = np.sqrt(np.clip(1 - ex ** 2 - ey ** 2, 0, 1))
        # direction convention: make the vector point ground -> satellite using the look direction expected sign of East
        mid = (np.nanmedian(ex), np.nanmedian(ey))
        asc = T["pas"] == "ascending"
        left = (look or "").lower().startswith("l")
        want_e_sign = (+1 if asc else -1) if left else (-1 if asc else +1)   # East component of ground->satellite
        flip = np.sign(mid[0]) != want_e_sign
        if flip:
            ex, ey = -ex, -ey
        geomq[T["key"]] = dict(source="GUNW metadata radarGrid (file)", look=look, flipped=bool(flip), median_incidence_deg=float(np.nanmedian(inc)),
                               east=float(np.nanmedian(ex)), north=float(np.nanmedian(ey)), up=float(np.nanmedian(ez)), ex=ex, ey=ey, ez=ez, inc=inc)
    else:
        geomq[T["key"]] = None
summary["geometry"] = {k: (None if v is None else {kk: vv for kk, vv in v.items() if not isinstance(vv, np.ndarray)}) for k, v in geomq.items()}

# --------------------------------------------------------------------- resample LOS velocity to 4326 + inversion
V, S = {}, {}
for T in TRACKS:
    k = T["key"]; p = per[k]
    V[k] = to_grid(p["fv"]["v"], p["tr"]["x"], p["tr"]["y"], p["tr"]["epsg"])
    S[k] = to_grid(p["fv"]["se"], p["tr"]["x"], p["tr"]["y"], p["tr"]["epsg"])
for T in TRACKS:
    summary["tracks"][T["key"]]["iono_subtracted"] = bool(T.get("iono", False))
INCLUDE_R = 0.5   # a track enters the inversion only if its r vs Sentinel-1 (after chosen corrections) is >= this
nan = np.full(LON.shape, np.nan)


def invert(keys):
    keys = [k for k in keys if geomq.get(k) is not None]
    sig = {k: np.sqrt(S[k] ** 2 + max(per[k]["floor"] ** 2 - per[k]["med_se"] ** 2, 0.0)) for k in keys}
    ok = {k: np.isfinite(V[k]) & np.isfinite(sig[k]) & np.isfinite(geomq[k]["ez"]) for k in keys}
    a11, a12, a22, b1, b2 = (np.zeros(LON.shape) for _ in range(5))
    hasasc, hasdsc, ntr = np.zeros(LON.shape, bool), np.zeros(LON.shape, bool), np.zeros(LON.shape, int)
    for k in keys:
        w = np.where(ok[k], 1.0 / sig[k] ** 2, 0.0)
        ue, uu = geomq[k]["ex"], geomq[k]["ez"]
        a11 += w * ue * ue; a12 += w * ue * uu; a22 += w * uu * uu
        b1 += w * ue * np.nan_to_num(V[k]); b2 += w * uu * np.nan_to_num(V[k])
        ntr += ok[k]
        if [t for t in TRACKS if t["key"] == k][0]["pas"] == "ascending":
            hasasc |= ok[k]
        else:
            hasdsc |= ok[k]
    det = a11 * a22 - a12 ** 2
    good = hasasc & hasdsc & (det > 1e-9)
    dd = np.where(good, det, 1)
    return dict(east=np.where(good, (a22 * b1 - a12 * b2) / dd, np.nan), vert=np.where(good, (a11 * b2 - a12 * b1) / dd, np.nan),
                vert_se=np.where(good, np.sqrt(a11 / dd), np.nan), east_se=np.where(good, np.sqrt(a22 / dd), np.nan),
                ntr=np.where(good, ntr, 0))


used = [k for k in V if summary["tracks"][k]["r_vs_s1"] >= INCLUDE_R and geomq.get(k) is not None]
summary["inversion_tracks_used"] = used
summary["inversion_tracks_excluded"] = {k: f"r vs S1 = {summary['tracks'][k]['r_vs_s1']:.2f} < {INCLUDE_R} (noisy: stable-ground sigma "
                                        f"{summary['tracks'][k]['stable_ground_empirical_sigma_cm_yr']:.1f} cm/yr)" for k in V if k not in used}
R = invert(used)
vert, east, vert_se, east_se, ntr = R["vert"], R["east"], R["vert_se"], R["east_se"], R["ntr"]
R4 = invert(list(V))
approx = False

# --------------------------------------------------------------------- GeoTIFFs (EPSG:4326)
def write_geotiff4326(path, arr):
    arr = np.asarray(arr, np.float32)
    geokeys = (1, 1, 0, 3, 1024, 0, 1, 2, 1025, 0, 1, 1, 2048, 0, 1, 4326)
    tifffile.imwrite(path, arr, photometric="minisblack", compression="deflate",
                     extratags=[(33550, "d", 3, (STEP, STEP, 0.0), True),
                                (33922, "d", 6, (0.0, 0.0, 0.0, AOI["lon0"], AOI["lat1"], 0.0), True),
                                (34735, "H", len(geokeys), geokeys, True), (42113, "s", 4, "nan", True)])


G = outdir / "geotiff"
for k in V:
    write_geotiff4326(G / f"los_velocity_track{k}_cm_yr.tif", V[k])
    write_geotiff4326(G / f"los_velocity_se_track{k}_cm_yr.tif", S[k])
write_geotiff4326(G / "vertical_velocity_cm_yr.tif", vert)
write_geotiff4326(G / "vertical_velocity_uncertainty_cm_yr.tif", vert_se)
write_geotiff4326(G / "east_velocity_cm_yr.tif", east)
write_geotiff4326(G / "east_velocity_uncertainty_cm_yr.tif", east_se)

# --------------------------------------------------------------------- combined stats
vs = nlib.smooth(vert, 5)
inbox = nlib.box(LON, LAT, nlib.EXCL)
valley = nlib.box(LON, LAT, nlib.VALLEY)
bowl = valley & (s1_grid < -5)
calm = valley & (s1_grid > -1.5)
cv = {}
if np.isfinite(vs).any():
    cv["bowl_median_cm_yr"] = float(np.nanmedian(vs[bowl & np.isfinite(vs)]))
    cv["valley_outside_bowl_median_cm_yr"] = float(np.nanmedian(vs[calm & np.isfinite(vs)]))
    cv["bowl_n_px"] = int((bowl & np.isfinite(vs)).sum())
    msk = np.where(inbox & np.isfinite(vs), vs, np.inf)
    i, j = np.unravel_index(np.argmin(msk), msk.shape)
    cv["max_sinking_cm_yr_smoothed5x5"] = float(vs[i, j]); cv["max_sinking_lon"] = float(LON[i, j]); cv["max_sinking_lat"] = float(LAT[i, j])
    pk = np.nanmin(np.where(inbox, vert, np.nan)); cv["max_sinking_cm_yr_single_pixel"] = float(pk)
    ci, cj = np.unravel_index(np.argmin((LON - 66.99) ** 2 + (LAT - 30.18) ** 2), LON.shape)
    cv["city_centre_vertical_cm_yr_5x5"] = float(vs[ci, cj]); cv["city_centre_vertical_se_cm_yr"] = float(vert_se[ci, cj])
    cv["area_km2_faster_than"] = {}
    for thr in (2, 5, 10):
        cv["area_km2_faster_than"][str(thr)] = dict(
            in_valley_box=round(float(((vs < -thr) & inbox).sum() * PIX_KM2), 2),
            whole_aoi_incl_residual_mountain_artifacts=round(float((vs < -thr).sum() * PIX_KM2), 2))
    cv["valid_fraction_aoi"] = float(np.isfinite(vert).mean())
    cv["median_vertical_se_cm_yr_in_bowl"] = float(np.nanmedian(vert_se[bowl & np.isfinite(vert_se)]))
    # compare with Sentinel-1 ascending LOS-equivalent: S1 LOS -> vertical assuming purely vertical motion, incidence ~39 deg
    cv["s1_bowl_median_los_cm_yr"] = float(np.nanmedian(s1_grid[bowl]))
    cv["s1_bowl_median_vertical_equiv_cm_yr_if_pure_vertical_inc39"] = float(np.nanmedian(s1_grid[bowl]) / np.cos(np.radians(39)))
    ok_ = valley & np.isfinite(vs) & np.isfinite(s1_grid)
    cv["r_vertical_vs_s1_los_valley"] = float(np.corrcoef(vs[ok_], s1_grid[ok_])[0, 1])
    bw = bowl & np.isfinite(east)
    cv["east_median_in_bowl_cm_yr"] = float(np.nanmedian(nlib.smooth(east, 5)[bowl & np.isfinite(nlib.smooth(east, 5))]))
cv["approximate_geometry"] = bool(approx)
vs4 = nlib.smooth(R4["vert"], 5)
cv["sensitivity_all_four_tracks"] = dict(bowl_median_cm_yr=float(np.nanmedian(vs4[bowl & np.isfinite(vs4)])),
    valley_outside_bowl_median_cm_yr=float(np.nanmedian(vs4[calm & np.isfinite(vs4)])),
    robust_sigma_outside_valley=float(1.4826*np.nanmedian(np.abs(vs4[~inbox & np.isfinite(vs4)] - np.nanmedian(vs4[~inbox])))))
cv["robust_sigma_outside_valley_cm_yr_used_tracks"] = float(1.4826*np.nanmedian(np.abs(vs[~inbox & np.isfinite(vs)] - np.nanmedian(vs[~inbox]))))
summary["vertical"] = cv
np.savez_compressed(outdir / "work" / "grid4326.npz", lon=lon1, lat=lat1, vert=vert, vert_se=vert_se, east=east, east_se=east_se,
                    s1=s1_grid, ntr=ntr, **{f"v{k}": V[k] for k in V}, **{f"se{k}": S[k] for k in S})
ion = {}
for t in (41, 92, 142, 20):
    p = outdir / "work" / f"iono_t{t}.json"
    if p.exists():
        j = json.loads(p.read_text())["variants"]
        ion[str(t)] = [{k: v[k] for k in ("label", "r", "bowl_median", "calm_median", "outside_robust_sigma", "outside_frac_below_m3")} for v in j]
    p = outdir / "work" / f"ionoreg_t{t}.json"
    if p.exists():
        rr = json.loads(p.read_text())
        ion.setdefault(str(t) + "_regression_unw_on_iono", [{k: round(x[k], 3) if isinstance(x[k], float) else x[k] for k in ("pair", "slope_raw", "slope_nonplanar", "corr_nonplanar")} for x in rr])
summary["corrections"]["ionosphere_tests"] = ion
summary["corrections"]["ionosphere_choice"] = {"41": "not applied", "92": "not applied", "142": "subtracted (reduces stable-ground noise 13.9->7.2 cm/yr, r 0.08->0.49)",
    "20": "subtracted (noise 21->17 cm/yr; track remains unusable)", "rule": "apply only where it cuts stable-ground noise by >20% and does not reduce r vs Sentinel-1"}
summary["corrections"]["mask_layer"] = {"41": "used", "92": "used", "142": "not used (--no-mask-layer): valid fraction 58% -> 74%", "20": "not used (--no-mask-layer): its mask layer has a different encoding and removed 85% of every second pair"}
(outdir / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
(outdir / "work" / "summary_partial.json").write_text(json.dumps(summary, indent=1, default=str))
print(json.dumps(cv, indent=1, default=str))
