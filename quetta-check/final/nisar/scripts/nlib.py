"""Shared helpers for the final NISAR Quetta products (numpy/scipy/tifffile only)."""
import numpy as np
import tifffile

LAM_S1 = 0.05546576                 # Sentinel-1 C-band wavelength (m)
REF = (66.80, 30.25)                # bedrock reference (lon, lat)
VALLEY = (66.93, 30.05, 67.05, 30.28)   # lon0, lat0, lon1, lat1: comparison box (same as compare_nisar_s1.py)
EXCL = (66.90, 30.03, 67.08, 30.30)     # box excluded from stable-ground fits (valley / bowl)
CITY = (66.99, 30.18)


# ------------------------------------------------------------------ loading
def load_track(npz_path):
    z = np.load(npz_path)
    dates = np.array([np.datetime64(str(d)) for d in z["dates"]])
    t = (dates - dates[0]).astype(int) / 365.25
    return dict(cum=z["cum_cm"].astype(np.float64), lon=z["lon"].astype(np.float64), lat=z["lat"].astype(np.float64),
                x=z["x"], y=z["y"], epsg=int(z["epsg"]), dates=[str(d) for d in z["dates"]], t=t)


def box(lon, lat, b):
    return (lon >= b[0]) & (lon <= b[2]) & (lat >= b[1]) & (lat <= b[3])


def smooth(a, k=5, min_frac=0.4):
    """NaN-aware k x k box mean (needs >= min_frac of the window valid)."""
    p = k // 2
    v = np.isfinite(a)
    x = np.where(v, a, 0.0)

    def bs(m):
        m = np.pad(m, p, mode="constant")
        c = np.pad(m.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    s, n = bs(x), bs(v.astype(float))
    return np.where(n >= k * k * min_frac, s / np.maximum(n, 1), np.nan)


# ------------------------------------------------------------------ velocity
def fit_velocity(cum, t, nmin=8):
    """Per-pixel least-squares line through all epochs (cum: (T,ny,nx) cm, t in years).
    Pixels are valid on a prefix of epochs (pipeline NaN-propagation); needs >= nmin valid epochs.
    Returns dict: v (cm/yr), se_reg (cm/yr, from residuals of the cumulative series), se_inc (cm/yr, random-walk-aware:
    slope written as a weighted sum of the pair increments; a diagnostic only: it assumes random-walk noise and is ~5x larger, because the dominant noise (atmosphere) is independent per date, i.e. white in the cumulative series), se = se_reg (the reported standard error),
    n (valid epochs), rms (cm)."""
    T, ny, nx = cum.shape
    nv = np.isfinite(cum).sum(0)
    v = np.full((ny, nx), np.nan); se_reg = v.copy(); se_inc = v.copy(); rms = v.copy()
    for n in range(nmin, T + 1):
        m = nv == n
        if not m.any():
            continue
        y = cum[:n][:, m]                       # (n, P)
        tt = t[:n]
        tb = tt.mean(); sxx = ((tt - tb) ** 2).sum()
        w = (tt - tb) / sxx                     # slope weights on epochs
        slope = (w[:, None] * y).sum(0)
        icpt = y.mean(0) - slope * tb
        res = y - (icpt + slope * tt[:, None])
        s2 = (res ** 2).sum(0) / (n - 2)
        v[m] = slope; se_reg[m] = np.sqrt(s2 / sxx); rms[m] = np.sqrt((res ** 2).mean(0))
        # increments d_i = y_i - y_{i-1}; slope = sum_i a_i d_i with a_i = sum_{k>=i} w_k
        a = np.cumsum(w[::-1])[::-1][1:]
        d = np.diff(y, axis=0); dt = np.diff(tt)
        rd = d - slope * dt[:, None]
        sig2 = (rd ** 2).sum(0) / (n - 2)
        se_inc[m] = np.sqrt(sig2 * (a ** 2).sum())
    return dict(v=v, se_reg=se_reg, se_inc=se_inc, se=se_reg, n=nv, rms=rms)


# ------------------------------------------------------------------ Sentinel-1
def load_s1(unw_tif, cc_tif, ref=REF):
    """S1 ascending 2024-09-09/2025-09-04 -> LOS rate in cm/yr (negative = away), referenced at `ref`."""
    with tifffile.TiffFile(unw_tif) as tf:
        p = tf.pages[0]; unw = p.asarray().astype(np.float64)
        sx, sy = p.tags["ModelPixelScaleTag"].value[:2]; tp = p.tags["ModelTiepointTag"].value
    cc = tifffile.imread(cc_tif).astype(np.float64)
    x0, y0 = tp[3], tp[4]
    unw[(unw == 0) | (cc < 50)] = np.nan
    cm = -unw * LAM_S1 / (4 * np.pi) * 100
    r = int((y0 - ref[1]) / sy); c = int((ref[0] - x0) / sx)
    cm -= np.nanmedian(cm[r - 10:r + 11, c - 10:c + 11])
    return dict(rate=cm * 365.25 / 360.0, x0=x0, y0=y0, sx=sx, sy=sy)


def s1_on_grid(s1, lon, lat):
    ri = np.clip(((s1["y0"] - lat) / s1["sy"]).astype(int), 0, s1["rate"].shape[0] - 1)
    ci = np.clip(((lon - s1["x0"]) / s1["sx"]).astype(int), 0, s1["rate"].shape[1] - 1)
    out = s1["rate"][ri, ci]
    inside = (lat <= s1["y0"]) & (lat >= s1["y0"] - s1["rate"].shape[0] * s1["sy"]) & (lon >= s1["x0"]) & \
             (lon <= s1["x0"] + s1["rate"].shape[1] * s1["sx"])
    return np.where(inside, out, np.nan)


def metrics(rate_s, lon, lat, s1g):
    """Same definitions as compare_nisar_s1.py. rate_s: (smoothed) NISAR LOS rate cm/yr on the track grid."""
    inval = box(lon, lat, VALLEY)
    bowl = inval & (s1g < -5)
    calm = inval & (s1g > -1.5)
    ok = inval & np.isfinite(rate_s) & np.isfinite(s1g)
    out = dict(n_compared=int(ok.sum()), r=float(np.corrcoef(rate_s[ok], s1g[ok])[0, 1]))
    bb = bowl & np.isfinite(rate_s); cc_ = calm & np.isfinite(rate_s)
    out.update(bowl_n=int(bb.sum()), bowl_median=float(np.median(rate_s[bb])) if bb.any() else np.nan,
               calm_n=int(cc_.sum()), calm_median=float(np.median(rate_s[cc_])) if cc_.any() else np.nan,
               s1_bowl_median=float(np.nanmedian(s1g[bowl])), s1_calm_median=float(np.nanmedian(s1g[calm])))
    out["bowl_minus_calm"] = out["bowl_median"] - out["calm_median"]
    # "fake sinking" blobs: valid pixels outside the valley box (inside S1 coverage) below -3 cm/yr, and the
    # robust spread of the smoothed rate there
    outside = ~box(lon, lat, EXCL) & np.isfinite(rate_s) & np.isfinite(s1g)
    vals = rate_s[outside]
    out.update(outside_n=int(outside.sum()), outside_frac_below_m3=float((vals < -3).mean()),
               outside_robust_sigma=float(1.4826 * np.median(np.abs(vals - np.median(vals)))),
               outside_std=float(vals.std()))
    return out


# ------------------------------------------------------------------ DEM
def dem_on_grid(dem_npz, lon, lat):
    from scipy.ndimage import map_coordinates, uniform_filter
    z = np.load(dem_npz)
    dem, dl, dt_ = z["dem"].astype(np.float64), z["lon"], z["lat"]
    dem = uniform_filter(dem, 3)                        # ~90 m footprint, similar to the 80 m SAR pixels
    fx = (lon - dl[0]) / (dl[1] - dl[0]); fy = (lat - dt_[0]) / (dt_[1] - dt_[0])
    return map_coordinates(dem, [fy, fx], order=1, mode="nearest")


def stable_mask(lon, lat, s1g=None, s1_flag=-2.0):
    """Stable ground for atmosphere fits: outside the EXCL box and not flagged as sinking by Sentinel-1."""
    st = ~box(lon, lat, EXCL)
    if s1g is not None:
        from scipy.ndimage import binary_dilation
        fl = smooth(s1g, 5) < s1_flag
        st &= ~binary_dilation(np.nan_to_num(fl, nan=0).astype(bool), iterations=10)
    return st


def dem_correct(cum, h, lon, lat, stable, ref=REF, nclip=3.0):
    """Per epoch k>=1: robust fit cum_k = a + b*h on stable pixels, subtract b*(h - h_ref) everywhere (bedrock
    reference level unchanged). Returns corrected cum and b (cm per km of elevation) per epoch."""
    refm = box(lon, lat, (ref[0] - .02, ref[1] - .02, ref[0] + .02, ref[1] + .02))
    href = np.nanmedian(h[refm])
    out = cum.copy(); bs = [0.0]
    for k in range(1, cum.shape[0]):
        m = stable & np.isfinite(cum[k])
        hk, yk = h[m], cum[k][m]
        ok = np.ones(hk.size, bool)
        for _ in range(3):
            A = np.column_stack([np.ones(ok.sum()), hk[ok] / 1000.0])
            coef, *_ = np.linalg.lstsq(A, yk[ok], rcond=None)
            r = yk - (coef[0] + coef[1] * hk / 1000.0)
            s = 1.4826 * np.median(np.abs(r[ok] - np.median(r[ok])))
            ok = np.abs(r) < nclip * max(s, 1e-6)
        b = coef[1]                                     # cm per km of elevation
        out[k] = cum[k] - b * (h - href) / 1000.0
        bs.append(float(b))
    return out, np.array(bs)
