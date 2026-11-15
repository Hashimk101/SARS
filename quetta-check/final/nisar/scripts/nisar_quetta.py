#!/usr/bin/env python
"""
nisar_quetta.py - NISAR GUNW chain -> cumulative LOS displacement for Quetta, Pakistan.

Sub-commands
  select      search ASF (no login) and print the chain of consecutive GUNW pairs
  auth-check  try non-interactive Earthdata login (env vars / netrc) and report
  list-h5     print groups/datasets of one GUNW file (remote URL or local path)
  run         select -> login -> stream AOI subsets -> process -> outputs
  demo        run the processing + plotting path on SYNTHETIC data (no login)

Credentials: this script never reads, prints or stores credentials. It only calls
earthaccess.login(strategy="environment") then strategy="netrc"; earthaccess does the rest.

Sign / unit conventions (see README): displacement_cm = -phase_sign * phase * lambda/(4 pi) * 100
with phase_sign=+1 by default (positive unwrapped phase = range increase = ground moving AWAY from
the satellite). So in the output NEGATIVE = away from satellite (sinking), POSITIVE = toward
satellite (rising). The GUNW spec does not state the phase sign; verify (README, "Sign check").
"""
import argparse
import csv
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "out"

# ----------------------------------------------------------------------------- constants
AOI = dict(lon0=66.75, lon1=67.25, lat0=29.95, lat1=30.45)
VALLEY = dict(lon0=66.85, lon1=67.10, lat0=30.05, lat1=30.40)
REF_CENTER = (66.80, 30.25)  # lon, lat  (stable-ground reference; configurable)
POINTS = {"city_center": (66.99, 30.18), "airport": (66.94, 30.25)}
DEFAULT_WAVELENGTH = 0.2384  # m, NISAR L-band (c / 1.2575 GHz); overridden by file's centerFrequency
C_LIGHT = 299792458.0

ASF_API = "https://api.daac.asf.alaska.edu/services/search/param"
SPEC_GRID = "/science/LSAR/GUNW/grids/frequencyA"
SPEC_IFG = SPEC_GRID + "/unwrappedInterferogram"  # per-polarization layers live in <SPEC_IFG>/<POL>/
LAYER_NAMES = {
    "unw": "unwrappedPhase",
    "coh": "coherenceMagnitude",
    "cc": "connectedComponents",
    "iono": "ionospherePhaseScreen",
}
SCENE_RE = re.compile(
    r"NISAR_L2_PR_GUNW_(?P<cyc>\d{3})_(?P<track>\d{3})_(?P<dir>[AD])_(?P<frame>\d{3})_(?P<n>\d{3})_"
    r"(?P<res>\d{4})_(?P<mode>\w{2})_(?P<r0>\d{8}T\d{6})_(?P<r1>\d{8}T\d{6})_(?P<s0>\d{8}T\d{6})_"
    r"(?P<s1>\d{8}T\d{6})_(?P<crid>[A-Z]\d{5})_\w_\w_\w_(?P<ver>\d{3})$"
)

LOGIN_HELP = """\
Earthdata login is not available (non-interactive strategies 'environment' and 'netrc' both failed).
Set it up yourself, then re-run:
  1. Create an account at https://urs.earthdata.nasa.gov (and accept the ASF/NISAR data EULA if asked).
  2. EITHER set an environment variable in your shell:
         EARTHDATA_TOKEN=<your EDL token>              (token generated on your URS profile page)
     or  EARTHDATA_USERNAME=<user>  and  EARTHDATA_PASSWORD=<password>
     OR create a netrc file (~/.netrc, or %USERPROFILE%\\_netrc on Windows, chmod 600 on Unix) with:
         machine urs.earthdata.nasa.gov login <user> password <password>
This script never reads or prints these values; earthaccess does the login."""


# ----------------------------------------------------------------------------- UTM (WGS84)
_A = 6378137.0
_F = 1 / 298.257223563
_N = _F / (2 - _F)
_K0 = 0.9996
_AA = _A / (1 + _N) * (1 + _N**2 / 4 + _N**4 / 64)
_ALPHA = (
    _N / 2 - 2 * _N**2 / 3 + 5 * _N**3 / 16,
    13 * _N**2 / 48 - 3 * _N**3 / 5,
    61 * _N**3 / 240,
)
_BETA = (
    _N / 2 - 2 * _N**2 / 3 + 37 * _N**3 / 96,
    _N**2 / 48 + _N**3 / 15,
    17 * _N**3 / 480,
)
_DELTA = (2 * _N - 2 * _N**2 / 3 - 2 * _N**3, 7 * _N**2 / 3 - 8 * _N**3 / 5, 56 * _N**3 / 15)


def utm_zone_from_epsg(epsg):
    epsg = int(epsg)
    if 32601 <= epsg <= 32660:
        return epsg - 32600, True
    if 32701 <= epsg <= 32760:
        return epsg - 32700, False
    return None


def lonlat_to_xy(lon, lat, epsg):
    """lon/lat (deg) -> projected x,y (m) for a WGS84 UTM EPSG (326xx/327xx); pyproj fallback."""
    z = utm_zone_from_epsg(epsg)
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    if z is None:
        from pyproj import Transformer  # optional dependency for non-UTM grids

        return Transformer.from_crs(4326, int(epsg), always_xy=True).transform(lon, lat)
    zone, north = z
    lam = np.radians(lon - ((zone - 1) * 6 - 180 + 3))
    phi = np.radians(lat)
    q = np.sqrt(_N) * 2 / (1 + _N)
    t = np.sinh(np.arctanh(np.sin(phi)) - q * np.arctanh(q * np.sin(phi)))
    xi_p = np.arctan2(t, np.cos(lam))
    eta_p = np.arctanh(np.sin(lam) / np.sqrt(1 + t * t))
    xi = xi_p + sum(a * np.sin(2 * (j + 1) * xi_p) * np.cosh(2 * (j + 1) * eta_p) for j, a in enumerate(_ALPHA))
    eta = eta_p + sum(a * np.cos(2 * (j + 1) * xi_p) * np.sinh(2 * (j + 1) * eta_p) for j, a in enumerate(_ALPHA))
    return 500000.0 + _K0 * _AA * eta, (0.0 if north else 1e7) + _K0 * _AA * xi


def xy_to_lonlat(x, y, epsg):
    z = utm_zone_from_epsg(epsg)
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if z is None:
        from pyproj import Transformer

        return Transformer.from_crs(int(epsg), 4326, always_xy=True).transform(x, y)
    zone, north = z
    xi = ((y - (0.0 if north else 1e7)) / (_K0 * _AA))
    eta = (x - 500000.0) / (_K0 * _AA)
    xi_p = xi - sum(b * np.sin(2 * (j + 1) * xi) * np.cosh(2 * (j + 1) * eta) for j, b in enumerate(_BETA))
    eta_p = eta - sum(b * np.cos(2 * (j + 1) * xi) * np.sinh(2 * (j + 1) * eta) for j, b in enumerate(_BETA))
    chi = np.arcsin(np.sin(xi_p) / np.cosh(eta_p))
    phi = chi + sum(d * np.sin(2 * (j + 1) * chi) for j, d in enumerate(_DELTA))
    lam = np.arctan2(np.sinh(eta_p), np.cos(xi_p))
    return np.degrees(lam) + ((zone - 1) * 6 - 180 + 3), np.degrees(phi)


# ----------------------------------------------------------------------------- search / selection
def parse_scene(name):
    m = SCENE_RE.match(name)
    if not m:
        return None
    g = m.groupdict()
    fmt = "%Y%m%dT%H%M%S"
    return dict(
        name=name, track=int(g["track"]), frame=int(g["frame"]), direction=g["dir"],
        ref_start=datetime.strptime(g["r0"], fmt), sec_start=datetime.strptime(g["s0"], fmt),
        crid=g["crid"], version=int(g["ver"]),
    )


def asf_search(start, end, lon=66.99, lat=30.19, max_results=250, timeout=60):
    params = {
        "dataset": "NISAR", "processingLevel": "GUNW", "intersectsWith": f"POINT({lon} {lat})",
        "start": f"{start}T00:00:00Z", "end": f"{end}T23:59:59Z", "output": "geojson",
        "maxResults": str(max_results),
    }
    url = ASF_API + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"User-Agent": "nisar-quetta-pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def products_from_geojson(gj):
    out = []
    for f in gj.get("features", []):
        p = f.get("properties", {})
        info = parse_scene(p.get("sceneName", ""))
        url = p.get("url")
        if info and url and url.endswith(".h5"):
            info["url"] = url
            out.append(info)
    return out


def select_chain(products, track, frame, start="2026-06-01", end="2026-12-31"):
    """Filter by track/frame/ref-date window, dedupe repeats, return the longest contiguous chain
    (each pair's secondary date == next pair's reference date) as (chain, info_dict)."""
    d0 = datetime.strptime(start, "%Y-%m-%d")
    d1 = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
    cand = [p for p in products if p["track"] == track and p["frame"] == frame and d0 <= p["ref_start"] < d1]
    n_raw = len(cand)
    best = {}
    for p in cand:  # dedupe on (ref date, sec date); keep highest product version
        k = (p["ref_start"].date(), p["sec_start"].date())
        if k not in best or (p["version"], p["name"]) > (best[k]["version"], best[k]["name"]):
            best[k] = p
    uniq = sorted(best.values(), key=lambda p: p["ref_start"])
    runs, cur = [], []
    for p in uniq:
        if cur and cur[-1]["sec_start"].date() == p["ref_start"].date():
            cur.append(p)
        else:
            if cur:
                runs.append(cur)
            cur = [p]
    if cur:
        runs.append(cur)
    chain = max(runs, key=lambda r: (len(r), r[-1]["sec_start"])) if runs else []
    return chain, dict(n_raw=n_raw, n_unique=len(uniq), n_runs=len(runs), run_lengths=[len(r) for r in runs])


def load_products(args):
    """ASF live search; on failure (or --offline) use the saved geojson."""
    if not args.offline:
        try:
            gj = asf_search(args.search_start, args.search_end)
            print(f"[search] ASF API returned {len(gj.get('features', []))} GUNW features")
            return products_from_geojson(gj)
        except Exception as e:  # network down, API error, ...
            print(f"[search] live ASF search failed ({type(e).__name__}); using saved geojson", file=sys.stderr)
    path = Path(args.geojson)
    print(f"[search] using saved geojson {path}")
    return products_from_geojson(json.loads(path.read_text(encoding="utf-8")))


def print_chain(chain, info):
    print(f"[select] raw={info['n_raw']} unique={info['n_unique']} contiguous runs={info['run_lengths']} "
          f"-> selected {len(chain)} products")
    for i, p in enumerate(chain, 1):
        print(f"  {i:2d}. {p['ref_start']:%m%d}->{p['sec_start']:%m%d}  "
              f"({(p['sec_start'] - p['ref_start']).days:2d} d)  {p['name']}")


# ----------------------------------------------------------------------------- earthaccess
def earthdata_login():
    """Non-interactive only. Returns (earthaccess_module, strategy) or None. Never touches credentials."""
    try:
        import earthaccess
    except ImportError:
        print("earthaccess is not installed (pip install earthaccess).", file=sys.stderr)
        return None
    for strat in ("environment", "netrc"):
        try:
            auth = earthaccess.login(strategy=strat)
            if getattr(auth, "authenticated", False):
                return earthaccess, strat
        except Exception as e:  # unavailable strategy or rejected login; do not echo message text
            print(f"[auth] strategy '{strat}' not usable ({type(e).__name__})")
    return None


def open_remote(earthaccess, url):
    """Return a seekable file-like streaming `url` over HTTPS (range requests)."""
    try:
        files = earthaccess.open([url], open_kwargs={"block_size": 8 * 2**20})
    except TypeError:
        files = earthaccess.open([url])
    if not files:
        raise RuntimeError(f"earthaccess.open returned nothing for {url}")
    return files[0]


# ----------------------------------------------------------------------------- HDF5 access
def h5_listing(h):
    rows = []

    def visit(name, obj):
        import h5py

        if isinstance(obj, h5py.Dataset):
            rows.append(f"D /{name}  shape={obj.shape} dtype={obj.dtype}")
        else:
            rows.append(f"G /{name}")

    h.visititems(visit)
    return rows


def _datasets_named(h, name):
    import h5py

    hits = []

    def visit(path, obj):
        if isinstance(obj, h5py.Dataset) and path.split("/")[-1] == name:
            hits.append("/" + path)

    h.visititems(visit)
    return hits


def find_dataset(h, name, pol, subdir=None):
    """Spec path first, then fall back to searching dataset names (ranked by plausibility)."""
    spec = f"{SPEC_IFG}/{pol}/{name}" if subdir is None else f"{SPEC_IFG}/{subdir}"
    if spec in h:
        return spec
    hits = [p for p in _datasets_named(h, name) if "pixelOffsets" not in p and "wrappedInterferogram" not in p.replace("unwrappedInterferogram", "")]
    if not hits:
        return None

    def score(p):
        return (("GUNW" in p) * 4 + ("unwrappedInterferogram" in p) * 4 + (f"/{pol}/" in p) * 2 + ("frequencyA" in p), -len(p))

    return sorted(hits, key=score, reverse=True)[0]


def choose_pol(h, want=None):
    cands = []
    if SPEC_GRID + "/listOfPolarizations" in h:
        raw = h[SPEC_GRID + "/listOfPolarizations"][()]
        cands = [x.decode() if isinstance(x, bytes) else str(x) for x in np.atleast_1d(raw)]
    if want and want in cands:
        return want
    if want and not cands:
        return want
    for p in ("HH", "VV", "HV", "VH"):
        if p in cands or (not cands and f"{SPEC_IFG}/{p}" in h):
            return p
    return want or "HH"


def aoi_slices(x, y, epsg, aoi, margin=2):
    corners_lon = np.linspace(aoi["lon0"], aoi["lon1"], 11)
    corners_lat = np.linspace(aoi["lat0"], aoi["lat1"], 11)
    LO, LA = np.meshgrid(corners_lon, corners_lat)
    ex, ey = lonlat_to_xy(LO, LA, epsg)
    xi = np.where((x >= ex.min()) & (x <= ex.max()))[0]
    yi = np.where((y >= ey.min()) & (y <= ey.max()))[0]
    if xi.size == 0 or yi.size == 0:
        return None
    return (slice(max(yi[0] - margin, 0), min(yi[-1] + margin + 1, y.size)),
            slice(max(xi[0] - margin, 0), min(xi[-1] + margin + 1, x.size)))


def extract_subset(h, aoi, pol=None, log=print):
    """Read the AOI subset of the needed layers from an open h5py.File. Returns dict of arrays."""
    pol = choose_pol(h, pol)
    paths = {k: find_dataset(h, n, pol) for k, n in LAYER_NAMES.items()}
    if paths["unw"] is None:
        raise RuntimeError("unwrappedPhase not found; run `list-h5` on this file and adjust SPEC_IFG paths")
    log(f"    pol={pol} paths: " + ", ".join(f"{k}={v}" for k, v in paths.items()))
    base = paths["unw"].rsplit("/", 1)[0]
    xp = next((p for p in (base + "/xCoordinates", SPEC_IFG + "/xCoordinates") if p in h), None) or \
        (_datasets_named(h, "xCoordinates") or [None])[0]
    yp = next((p for p in (base + "/yCoordinates", SPEC_IFG + "/yCoordinates") if p in h), None) or \
        (_datasets_named(h, "yCoordinates") or [None])[0]
    if not xp or not yp:
        raise RuntimeError("x/yCoordinates not found")
    x, y = h[xp][()], h[yp][()]
    ep = next((p for p in (base + "/projection", SPEC_IFG + "/projection") if p in h), None)
    epsg = None
    if ep:
        d = h[ep]
        epsg = int(d.attrs.get("epsg_code", d[()]))
    if not epsg:
        raise RuntimeError("projection/EPSG not found")
    sl = aoi_slices(x, y, epsg, aoi)
    if sl is None:
        raise RuntimeError("AOI does not intersect this product's grid")
    out = dict(x=x[sl[1]], y=y[sl[0]], epsg=np.int64(epsg), pol=np.str_(pol))
    for k in ("unw", "coh", "cc", "iono"):
        if paths[k]:
            out[k] = h[paths[k]][sl]
        else:
            log(f"    WARNING layer {k} ({LAYER_NAMES[k]}) not found; continuing without it")
    mp = f"{SPEC_IFG}/mask"
    if mp in h:
        out["mask"] = h[mp][sl]
    cf = SPEC_GRID + "/centerFrequency"
    out["wavelength"] = np.float64(C_LIGHT / float(h[cf][()]) if cf in h else DEFAULT_WAVELENGTH)
    return out


def cache_path(prod, pol, aoi):
    tag = "{lon0}_{lon1}_{lat0}_{lat1}".format(**aoi)
    return DATA_DIR / "cache" / f"{prod['name']}__{pol or 'auto'}__{tag}.npz"


def get_subset(prod, args, session):
    """Cache-first loader. `session` is a lazily created earthaccess handle (dict)."""
    import h5py

    cp = cache_path(prod, args.pol, AOI)
    if cp.exists():
        print(f"  cache hit  {cp.name}")
        return dict(np.load(cp, allow_pickle=False))
    if session.get("ea") is None:
        res = earthdata_login()
        if res is None:
            print(LOGIN_HELP, file=sys.stderr)
            sys.exit(2)
        session["ea"], session["strategy"] = res
        print(f"[auth] logged in via '{res[1]}'")
    print(f"  streaming  {prod['name']}")
    f = open_remote(session["ea"], prod["url"])
    try:
        with h5py.File(f, "r") as h:
            sub = extract_subset(h, AOI, args.pol)
    finally:
        try:
            f.close()
        except Exception:
            pass
    cp.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cp, **sub)
    return sub


# ----------------------------------------------------------------------------- processing math
def box_mask(LON, LAT, box):
    return (LON >= box["lon0"]) & (LON <= box["lon1"]) & (LAT >= box["lat0"]) & (LAT <= box["lat1"])


def ref_box_from_center(center, half_deg):
    return dict(lon0=center[0] - half_deg, lon1=center[0] + half_deg,
                lat0=center[1] - half_deg, lat1=center[1] + half_deg)


def fit_plane(X, Y, Z, use):
    """Least-squares plane Z = a + b*X + c*Y on pixels `use`. Returns (a, b, c)."""
    xs, ys, zs = X[use], Y[use], Z[use]
    if xs.size > 200000:
        idx = np.random.default_rng(0).choice(xs.size, 200000, replace=False)
        xs, ys, zs = xs[idx], ys[idx], zs[idx]
    A = np.column_stack([np.ones_like(xs), xs, ys])
    coef, *_ = np.linalg.lstsq(A, zs, rcond=None)
    return coef


def prepare_pair(sub, X, Y, LON, LAT, cfg, ref_box, valley_box, log=print):
    """Mask, (optionally) de-iono, reference and de-plane one pair. Returns float32 phase (rad) with NaN
    where invalid. Raises RuntimeError if the reference box has too few valid pixels."""
    unw = sub["unw"].astype(np.float64)
    valid = np.isfinite(unw)
    if "coh" in sub:
        coh = sub["coh"]
        valid &= np.isfinite(coh) & (coh >= cfg.coh_min)
    cc = sub.get("cc")
    if cc is not None:
        valid &= (cc > 0) & (cc != 65535)
    m = sub.get("mask")
    if m is not None and cfg.use_mask:
        m = m.astype(np.int32)
        valid &= (m != 255) & ((m // 10) % 10 > 0) & (m % 10 > 0) & (m // 100 != 1)
    phase = unw
    if cfg.iono:
        if "iono" not in sub:
            raise RuntimeError("--iono requested but ionospherePhaseScreen not available")
        phase = phase - sub["iono"].astype(np.float64)
        valid &= np.isfinite(phase)
    refm = ref_box & valid
    if refm.sum() < cfg.min_ref_pixels:
        raise RuntimeError(f"only {int(refm.sum())} valid pixels in reference box (need {cfg.min_ref_pixels})")
    if cc is not None:  # keep only the connected component that holds the reference (unwrapping offsets differ per component)
        vals, cnt = np.unique(cc[refm], return_counts=True)
        comp = vals[np.argmax(cnt)]
        valid &= cc == comp
        refm &= valid
    phase = phase - np.median(phase[refm])
    if cfg.plane:
        stable = valid & ~box_mask(LON, LAT, valley_box)
        if stable.sum() >= 1000:
            xk, yk = (X - X.mean()) / 1000.0, (Y - Y.mean()) / 1000.0
            a, b, c = fit_plane(xk, yk, phase, stable)
            phase = phase - (a + b * xk + c * yk)
            phase = phase - np.median(phase[refm])
        else:
            log(f"    WARNING only {int(stable.sum())} stable pixels outside valley; plane removal skipped")
    phase[~valid] = np.nan
    return phase.astype(np.float32), float(valid.mean())


def phase_to_los_cm(phase, wavelength=DEFAULT_WAVELENGTH, phase_sign=1.0):
    """Radians -> cm of LOS displacement. phase_sign=+1: positive phase = range increase (away from
    satellite), so displacement = -phase*lambda/(4 pi); NEGATIVE = away/sinking, POSITIVE = toward."""
    return -phase_sign * np.asarray(phase) * wavelength / (4 * np.pi) * 100.0


def cumulate(phases):
    """Sum consecutive-pair phases -> cumulative stack with a leading zero epoch, shape (n+1,H,W).
    NaN in any pair propagates to all later epochs (strict)."""
    st = np.stack(phases).astype(np.float64)
    cum = np.cumsum(st, axis=0)
    return np.concatenate([np.zeros((1,) + st.shape[1:]), cum], axis=0)


def nan_box_mean(a, win=5, min_frac=0.5):
    from numpy.lib.stride_tricks import sliding_window_view

    r = win // 2
    p = np.pad(a, r, constant_values=np.nan)
    v = sliding_window_view(p, (win, win))
    n = np.isfinite(v).sum(axis=(-1, -2))
    with np.errstate(all="ignore"):
        s = np.nansum(v, axis=(-1, -2)) / np.maximum(n, 1)
    s[n < min_frac * win * win] = np.nan
    return s


def nearest_pixel(LON, LAT, lon, lat):
    d = ((LON - lon) * math.cos(math.radians(lat))) ** 2 + (LAT - lat) ** 2
    return np.unravel_index(np.argmin(d), d.shape)


def point_series(stack_cm, LON, LAT, lon, lat, half=1):
    i, j = nearest_pixel(LON, LAT, lon, lat)
    w = stack_cm[:, max(i - half, 0): i + half + 1, max(j - half, 0): j + half + 1]
    with np.errstate(all="ignore"):
        return np.array([np.nanmedian(w[k]) if np.isfinite(w[k]).any() else np.nan for k in range(w.shape[0])])


def summarize(disp_cm, LON, LAT, valley_box, days, smooth=5):
    sm = nan_box_mean(disp_cm, smooth)
    inval = box_mask(LON, LAT, valley_box) & np.isfinite(sm)
    if not inval.any():
        return None
    idx = np.where(inval, sm, np.inf)
    i, j = np.unravel_index(np.argmin(idx), idx.shape)
    v = float(sm[i, j])
    return dict(max_sink_cm=v, lon=float(LON[i, j]), lat=float(LAT[i, j]), days=days,
                rate_cm_yr=v / days * 365.25 if days else float("nan"),
                valley_valid_frac=float(np.isfinite(disp_cm[box_mask(LON, LAT, valley_box)]).mean()))


def regrid_to(ref_x, ref_y, sub):
    """Nearest-index reindex of a subset onto the reference grid (no-op if identical)."""
    x, y = sub["x"], sub["y"]
    if x.shape == ref_x.shape and y.shape == ref_y.shape and np.abs(x - ref_x).max() < 1 and np.abs(y - ref_y).max() < 1:
        return sub
    dx, dy = ref_x[1] - ref_x[0], ref_y[1] - ref_y[0]
    ix = np.rint((ref_x - x[0]) / (x[1] - x[0])).astype(int)
    iy = np.rint((ref_y - y[0]) / (y[1] - y[0])).astype(int)
    ok_x, ok_y = (ix >= 0) & (ix < x.size), (iy >= 0) & (iy < y.size)
    out = dict(sub)
    for k in ("unw", "coh", "cc", "iono", "mask"):
        if k not in sub:
            continue
        fill = {"cc": 65535, "mask": 255}.get(k, np.nan)
        arr = np.full((ref_y.size, ref_x.size), fill, dtype=sub[k].dtype)
        arr[np.ix_(ok_y, ok_x)] = sub[k][np.ix_(iy[ok_y], ix[ok_x])]
        out[k] = arr
    out["x"], out["y"] = ref_x, ref_y
    return out


def process_chain(chain, subs, cfg, log=print):
    """chain: list of product dicts (ref_start, sec_start). subs: list of subset dicts. Returns result dict."""
    base = subs[0]
    X, Y = np.meshgrid(base["x"], base["y"])
    epsg = int(base["epsg"])
    LON, LAT = xy_to_lonlat(X, Y, epsg)
    ref_box = ref_box_from_center(cfg.ref_center, cfg.ref_half)
    valley_box = VALLEY
    rb = box_mask(LON, LAT, ref_box)
    if not rb.any():
        raise RuntimeError("reference box lies outside the AOI subset; choose --ref-lon/--ref-lat inside the AOI")
    wl = float(base.get("wavelength", DEFAULT_WAVELENGTH))
    phases, used, fracs = [], [], []
    for p, s in zip(chain, subs):
        s = regrid_to(base["x"], base["y"], s)
        try:
            ph, vf = prepare_pair(s, X, Y, LON, LAT, cfg, rb, valley_box, log)
        except RuntimeError as e:
            log(f"  pair {p['ref_start']:%m%d}->{p['sec_start']:%m%d}: SKIPPED ({e})")
            phases.append(np.full(LON.shape, np.nan, np.float32))
            fracs.append(0.0)
            continue
        phases.append(ph)
        fracs.append(vf)
        log(f"  pair {p['ref_start']:%m%d}->{p['sec_start']:%m%d}: valid {vf*100:5.1f}%")
    cum_phase = cumulate(phases)
    cum_cm = phase_to_los_cm(cum_phase, wl, cfg.phase_sign)
    dates = [chain[0]["ref_start"].date()] + [p["sec_start"].date() for p in chain]
    days = (dates[-1] - dates[0]).days
    final = cum_cm[-1].astype(np.float32)
    series = {n: point_series(cum_cm, LON, LAT, *ll, half=cfg.win_px) for n, ll in POINTS.items()}
    series["reference"] = point_series(cum_cm, LON, LAT, *cfg.ref_center, half=cfg.win_px)
    summ = summarize(final, LON, LAT, valley_box, days)
    return dict(disp_cm=final, cum_cm=cum_cm.astype(np.float32), x=base["x"], y=base["y"], LON=LON, LAT=LAT,
                epsg=epsg, dates=dates, days=days, series=series, summary=summ, wavelength=wl,
                pair_valid_frac=fracs, ref_box=ref_box, valley_box=valley_box)


# ----------------------------------------------------------------------------- outputs
def write_geotiff(path, arr, x, y, epsg):
    """North-up GeoTIFF (float32, nodata=NaN). Assumes x/y coordinates are pixel centers."""
    import tifffile

    arr = np.asarray(arr, np.float32)
    if y[1] > y[0]:  # ascending y -> flip to north-up
        arr, y = arr[::-1], y[::-1]
    dx, dy = abs(float(x[1] - x[0])), abs(float(y[1] - y[0]))
    ulx, uly = float(x[0]) - dx / 2, float(y[0]) + dy / 2
    geokeys = (1, 1, 0, 3, 1024, 0, 1, 1, 1025, 0, 1, 1, 3072, 0, 1, int(epsg))
    tifffile.imwrite(
        path, arr, photometric="minisblack",
        extratags=[(33550, "d", 3, (dx, dy, 0.0), True), (33922, "d", 6, (0.0, 0.0, 0.0, ulx, uly, 0.0), True),
                   (34735, "H", len(geokeys), geokeys, True), (42113, "s", 4, "nan", True)],
    )


def make_map(res, path, title, cfg):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    LON, LAT, d = res["LON"], res["LAT"], res["disp_cm"]
    fin = d[np.isfinite(d)]
    lim = max(float(np.nanpercentile(np.abs(fin), 98)), 0.5) if fin.size else 1.0
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.5, 6), gridspec_kw=dict(width_ratios=[1.25, 1]))
    pm = ax.pcolormesh(LON, LAT, np.ma.masked_invalid(d), cmap="RdBu", vmin=-lim, vmax=lim, shading="auto", rasterized=True)
    cb = fig.colorbar(pm, ax=ax, pad=0.02, shrink=0.9)
    cb.set_label("cumulative LOS displacement (cm)\nnegative = away from satellite (sinking)")
    for box, st in ((res["valley_box"], dict(color="k", ls="--", lw=1)), (res["ref_box"], dict(color="g", ls="-", lw=1.5))):
        ax.plot([box["lon0"], box["lon1"], box["lon1"], box["lon0"], box["lon0"]],
                [box["lat0"], box["lat0"], box["lat1"], box["lat1"], box["lat0"]], **st)
    ax.plot(*POINTS["city_center"], "k*", ms=14, mfc="yellow")
    ax.annotate("Quetta", POINTS["city_center"], xytext=(6, -14), textcoords="offset points", weight="bold")
    ax.plot(*POINTS["airport"], "k^", ms=8, mfc="white")
    ax.annotate("Airport", POINTS["airport"], xytext=(6, 4), textcoords="offset points", fontsize=8)
    ax.plot(*cfg.ref_center, "gs", ms=6)
    ax.annotate("reference", cfg.ref_center, xytext=(4, 6), textcoords="offset points", fontsize=8, color="g")
    s = res["summary"]
    if s:
        ax.plot(s["lon"], s["lat"], "mx", ms=10, mew=2)
    ax.set_xlim(AOI["lon0"], AOI["lon1"])
    ax.set_ylim(AOI["lat0"], AOI["lat1"])
    ax.set_aspect(1 / math.cos(math.radians(30.2)))
    ax.set_xlabel("longitude (deg E)")
    ax.set_ylabel("latitude (deg N)")
    ax.set_title(title, fontsize=10)
    dts = res["dates"]
    for n, v in res["series"].items():
        ax2.plot(dts, v, "o-", label=n.replace("_", " "))
    ax2.axhline(0, color="gray", lw=0.7)
    ax2.set_ylabel("cumulative LOS displacement (cm)")
    ax2.set_title("time series at points", fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def write_outputs(res, outdir, tag, title, cfg):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(outdir / f"{tag}_cumulative_disp.npz", disp_cm=res["disp_cm"], x=res["x"], y=res["y"],
                        lon=res["LON"].astype(np.float32), lat=res["LAT"].astype(np.float32), epsg=res["epsg"],
                        dates=np.array([str(d) for d in res["dates"]]), cum_cm=res["cum_cm"])
    write_geotiff(outdir / f"{tag}_cumulative_disp_cm.tif", res["disp_cm"], res["x"], res["y"], res["epsg"])
    make_map(res, outdir / f"{tag}_map.png", title, cfg)
    with open(outdir / f"{tag}_timeseries.csv", "w", newline="") as f:
        w = csv.writer(f)
        names = list(res["series"])
        w.writerow(["date", "days"] + [f"{n}_cm" for n in names])
        for k, d in enumerate(res["dates"]):
            w.writerow([d.isoformat(), (d - res["dates"][0]).days] + [f"{res['series'][n][k]:.3f}" for n in names])
    return outdir


def print_summary(res, cfg, tag):
    s = res["summary"]
    print("\n==== SUMMARY ====")
    print(f"{tag}: {res['dates'][0]} -> {res['dates'][-1]} ({res['days']} days), wavelength {res['wavelength']:.4f} m, "
          f"phase_sign={cfg.phase_sign:+g}, iono={'on' if cfg.iono else 'off'}, plane={'on' if cfg.plane else 'off'}")
    print("Convention: LOS cm, NEGATIVE = away from satellite (sinking), POSITIVE = toward satellite.")
    if s is None:
        print("No valid pixels inside the valley box - cannot summarize.")
        return
    print(f"Max LOS sinking (5x5 smoothed, inside valley box): {s['max_sink_cm']:.2f} cm at "
          f"{s['lon']:.3f}E {s['lat']:.3f}N")
    print(f"Implied rate: {s['rate_cm_yr']:.1f} cm/yr (LOS, over {s['days']} days; vertical ~ LOS/cos(incidence))")
    for n, v in res["series"].items():
        print(f"  {n:12s} final cumulative: {v[-1]:.2f} cm")
    print(f"Valid fraction of valley box: {s['valley_valid_frac']*100:.0f}%")
    if s["max_sink_cm"] > 0:
        print("NOTE: no net sinking found in the valley (largest signal is positive). If uplift is shown over a known "
              "subsiding basin, the phase sign convention is likely flipped: re-run with --phase-sign -1.")


# ----------------------------------------------------------------------------- synthetic data
def synthetic_chain(n_pairs=9, rate_cm_yr=14.0, seed=1, plane=True, noise_rad=0.15, wl=DEFAULT_WAVELENGTH,
                    phase_sign=1.0):
    """Synthetic GUNW-like subsets on a UTM 42N 80 m grid: Gaussian bowl centered near Quetta that sinks
    (moves away from the satellite) at rate_cm_yr, plus a tilt ramp and noise. Returns (chain, subs, truth_cm)."""
    rng = np.random.default_rng(seed)
    epsg = 32642
    x0, y0 = lonlat_to_xy(AOI["lon0"] - 0.01, AOI["lat1"] + 0.01, epsg)
    x1, y1 = lonlat_to_xy(AOI["lon1"] + 0.01, AOI["lat0"] - 0.01, epsg)
    x = np.arange(x0, x1, 80.0)
    y = np.arange(y0, y1, -80.0)
    X, Y = np.meshgrid(x, y)
    LON, LAT = xy_to_lonlat(X, Y, epsg)
    cx, cy = 66.99, 30.19
    r2 = (((LON - cx) * 96.4) ** 2 + ((LAT - cy) * 111.0) ** 2)  # km^2
    shape = np.exp(-r2 / (2 * 6.0**2))  # sigma 6 km (~valley scale)
    dates = [datetime(2026, 6, 17), datetime(2026, 6, 29), datetime(2026, 7, 11), datetime(2026, 7, 23),
             datetime(2026, 8, 16), datetime(2026, 8, 28), datetime(2026, 9, 9), datetime(2026, 9, 21),
             datetime(2026, 10, 3), datetime(2026, 10, 15)][: n_pairs + 1]
    chain, subs = [], []
    truth_prev = np.zeros_like(shape)
    t0 = dates[0]
    for k in range(n_pairs):
        t = (dates[k + 1] - t0).days
        truth = -rate_cm_yr * t / 365.25 * shape  # LOS cm, negative = away
        d_cm = truth - truth_prev
        truth_prev = truth
        phase = -phase_sign * d_cm / 100.0 * 4 * np.pi / wl  # inverse of phase_to_los_cm
        if plane:
            phase = phase + 0.8 * rng.uniform(-1, 1) + 0.04 * ((X - X.mean()) / 1000) * rng.uniform(-1, 1) \
                + 0.03 * ((Y - Y.mean()) / 1000) * rng.uniform(-1, 1)
        phase = phase + 0.0 * rng.normal(size=phase.shape) + noise_rad * rng.normal(size=phase.shape)
        coh = np.clip(0.75 + 0.1 * rng.normal(size=phase.shape), 0, 1).astype(np.float32)
        coh[(LON > 67.18) & (LAT > 30.35)] = 0.1  # a decorrelated corner
        cc = np.ones(phase.shape, np.uint16)
        cc[coh < 0.3] = 0
        phase[coh < 0.3] = np.nan
        subs.append(dict(unw=phase.astype(np.float32), coh=coh, cc=cc, x=x, y=y, epsg=np.int64(epsg),
                         wavelength=np.float64(wl), iono=np.zeros_like(phase, np.float32)))
        chain.append(dict(ref_start=dates[k], sec_start=dates[k + 1], name=f"SYNTHETIC_PAIR_{k+1:02d}"))
    return chain, subs, truth_prev  # truth_prev is the final cumulative truth (cm)


# ----------------------------------------------------------------------------- CLI
def add_proc_args(p):
    p.add_argument("--coh-min", type=float, default=0.3, help="mask coherence below this (default 0.3)")
    p.add_argument("--iono", action="store_true", help="subtract ionospherePhaseScreen (default: not applied)")
    p.add_argument("--plane", action="store_true", help="remove best-fit plane estimated outside the valley box")
    p.add_argument("--no-mask-layer", dest="use_mask", action="store_false", help="ignore the GUNW 'mask' layer")
    p.add_argument("--ref-lon", type=float, default=REF_CENTER[0])
    p.add_argument("--ref-lat", type=float, default=REF_CENTER[1])
    p.add_argument("--ref-half", type=float, default=0.02, help="half-width of reference box in degrees (default 0.02)")
    p.add_argument("--min-ref-pixels", type=int, default=20)
    p.add_argument("--phase-sign", type=float, default=1.0, choices=[1.0, -1.0],
                   help="+1: positive unwrapped phase = range increase (away). Flip to -1 if sign check fails")
    p.add_argument("--win-px", type=int, default=1, help="half-window (pixels) for point time series medians")


def finish_cfg(a):
    a.ref_center = (a.ref_lon, a.ref_lat)
    return a


def add_select_args(p):
    p.add_argument("--track", type=int, default=41)
    p.add_argument("--frame", type=int, default=17)
    p.add_argument("--start", default="2026-06-01", help="earliest reference date to include")
    p.add_argument("--end", default="2026-12-31", help="latest reference date to include")
    p.add_argument("--search-start", default="2025-10-01")
    p.add_argument("--search-end", default="2026-11-14")
    p.add_argument("--offline", action="store_true", help="skip the live ASF search, use --geojson")
    p.add_argument("--geojson", default=str(DATA_DIR / "asf" / "quetta_gunw.geojson"))
    p.add_argument("--max-pairs", type=int, default=0, help="limit chain length (0 = all)")


def get_chain(a):
    prods = load_products(a)
    chain, info = select_chain(prods, a.track, a.frame, a.start, a.end)
    if a.max_pairs:
        chain = chain[: a.max_pairs]
    print_chain(chain, info)
    return chain


def cmd_select(a):
    chain = get_chain(a)
    return 0 if chain else 1


def cmd_auth(a):
    res = earthdata_login()
    if res is None:
        print(LOGIN_HELP, file=sys.stderr)
        return 2
    print(f"[auth] OK via '{res[1]}'")
    return 0


def cmd_list(a):
    import h5py

    if Path(a.target).exists():
        with h5py.File(a.target, "r") as h:
            print("\n".join(h5_listing(h)))
        return 0
    res = earthdata_login()
    if res is None:
        print(LOGIN_HELP, file=sys.stderr)
        return 2
    f = open_remote(res[0], a.target)
    with h5py.File(f, "r") as h:
        print("\n".join(h5_listing(h)))
    return 0


def cmd_run(a):
    chain = get_chain(a)
    if not chain:
        print("No chain found.", file=sys.stderr)
        return 1
    session = {}
    subs = []
    print("[fetch] AOI subsets (cache first, streaming only what is missing)")
    for p in chain:
        subs.append(get_subset(p, a, session))
    res = process_chain(chain, subs, a)
    tag = f"track{a.track:03d}_frame{a.frame:03d}"
    title = (f"NISAR GUNW track {a.track} frame {a.frame}: cumulative LOS displacement\n"
             f"{res['dates'][0]} to {res['dates'][-1]} (ref = green box)")
    od = write_outputs(res, OUT_DIR / tag, tag, title, a)
    print_summary(res, a, tag)
    print(f"\nOutputs in {od}")
    return 0


def cmd_demo(a):
    chain, subs, truth = synthetic_chain(plane=True)
    a.plane = True
    res = process_chain(chain, subs, a)
    od = write_outputs(res, OUT_DIR / "demo", "synthetic",
                       "SYNTHETIC DEMO (not real data): Gaussian bowl, 14 cm/yr\n"
                       f"{res['dates'][0]} to {res['dates'][-1]}", a)
    print_summary(res, a, "synthetic")
    print(f"synthetic truth at bowl center: {truth.min():.2f} cm")
    print(f"\nOutputs in {od}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("select", help="search + print chain (no login)")
    add_select_args(p)
    p.set_defaults(fn=cmd_select)
    p = sub.add_parser("auth-check", help="try non-interactive Earthdata login")
    p.set_defaults(fn=cmd_auth)
    p = sub.add_parser("list-h5", help="list groups/datasets of a GUNW .h5 (URL or local path)")
    p.add_argument("target")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("run", help="full pipeline")
    add_select_args(p)
    add_proc_args(p)
    p.add_argument("--pol", default=None, help="polarization layer (default: HH if present, else first)")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("demo", help="synthetic-data run of processing + plotting")
    add_proc_args(p)
    p.set_defaults(fn=cmd_demo)
    a = ap.parse_args(argv)
    if hasattr(a, "ref_lon"):
        finish_cfg(a)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
