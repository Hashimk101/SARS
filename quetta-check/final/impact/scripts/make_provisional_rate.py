"""Build a PROVISIONAL vertical-velocity + uncertainty GeoTIFF from the two existing NISAR
cumulative-displacement npz files (track 92 descending, track 41 ascending).

THIS IS A DEVELOPMENT STAND-IN, NOT THE FINAL NISAR PRODUCT.  Only ~120 days of data per track.

Steps: per-pixel linear regression of cumulative LOS displacement vs time (cm/yr + standard error)
-> average the two tracks where both valid (inverse-variance NOT used; simple mean, SE combined)
-> divide by cos(38 deg) (approximate LOS->vertical, assumes purely vertical motion)
-> Gaussian smoothing (sigma 3 px = 240 m) -> resample to EPSG:4326 (0.00075 deg) -> write rate and uncertainty tifs.

Uncertainty (cm/yr, 1-sigma) = sqrt( SE_reg^2 + (0.25*|rate|)^2 + 1.0^2 )
  SE_reg : regression standard error of the slope (combined across tracks / sqrt(n_tracks))
  25 %   : LOS->vertical / track-mix / short-record systematic allowance
  1.0    : cm/yr floor for residual atmosphere (regression SE ignores spatially correlated atmosphere)
"""
import argparse, datetime as dt
import numpy as np
import rasterio
from rasterio.transform import from_origin
from pyproj import Transformer
from scipy.ndimage import gaussian_filter, map_coordinates

ap = argparse.ArgumentParser()
ap.add_argument("--t92", required=True)
ap.add_argument("--t41", required=True)
ap.add_argument("--out-rate", required=True)
ap.add_argument("--out-unc", required=True)
ap.add_argument("--inc", type=float, default=38.0)
a = ap.parse_args()

AOI = (66.80, 67.20, 30.00, 30.40)
RES = 0.00075


def track_rate(path):
    d = np.load(path, allow_pickle=True)
    t = np.array([(dt.date.fromisoformat(s) - dt.date(2026, 1, 1)).days for s in d["dates"]], float) / 365.25
    cum = d["cum_cm"].astype("float64")
    ok = np.isfinite(cum)
    n = ok.sum(0)
    tt = np.where(ok, t[:, None, None], np.nan)
    tm = np.nanmean(tt, 0)
    dtm = np.where(ok, t[:, None, None] - tm, 0.0)
    ym = np.nanmean(np.where(ok, cum, np.nan), 0)
    dy = np.where(ok, cum - ym, 0.0)
    sxx = (dtm ** 2).sum(0)
    slope = (dtm * dy).sum(0) / sxx
    resid = dy - slope * dtm
    s2 = (resid ** 2).sum(0) / np.maximum(n - 2, 1)
    se = np.sqrt(s2 / sxx)
    bad = (n < 7) | (sxx <= 0)
    slope[bad] = np.nan
    se[bad] = np.nan
    return d["x"], d["y"], slope, se


x1, y1, r92, se92 = track_rate(a.t92)
x2, y2, r41, se41 = track_rate(a.t41)
assert np.allclose(x1, x2) and np.allclose(y1, y2), "grids differ"
stack = np.stack([r92, r41])
sestack = np.stack([se92, se41])
n = np.isfinite(stack).sum(0)
los = np.nanmean(stack, 0)
se = np.sqrt(np.nansum(sestack ** 2, 0)) / np.maximum(n, 1)
los[n == 0] = np.nan
se[n == 0] = np.nan
c = np.cos(np.radians(a.inc))
vert = los / c
se_v = se / c
# light smoothing (NaN-aware)
def nan_smooth(z, s):
    m = np.isfinite(z).astype(float)
    num = gaussian_filter(np.nan_to_num(z), s)
    den = gaussian_filter(m, s)
    out = num / np.maximum(den, 1e-6)
    out[(den < 0.5) | ~np.isfinite(z)] = np.nan
    return out
vert = nan_smooth(vert, 3.0)
se_v = nan_smooth(se_v, 3.0)
sig = np.sqrt(se_v ** 2 + (0.25 * vert) ** 2 + 1.0 ** 2)

# resample to EPSG:4326
lons = np.arange(AOI[0] + RES / 2, AOI[1], RES)
lats = np.arange(AOI[3] - RES / 2, AOI[2], -RES)
LON, LAT = np.meshgrid(lons, lats)
tr = Transformer.from_crs(4326, 32642, always_xy=True)
X, Y = tr.transform(LON, LAT)
# x ascending, y descending (check)
dx = x1[1] - x1[0]
dy_ = y1[1] - y1[0]
cj = (X - x1[0]) / dx
ci = (Y - y1[0]) / dy_
def samp(z):
    zz = np.nan_to_num(z, nan=0.0)
    m = np.isfinite(z).astype(float)
    v = map_coordinates(zz, [ci, cj], order=1, mode="constant", cval=0.0)
    w = map_coordinates(m, [ci, cj], order=1, mode="constant", cval=0.0)
    out = v / np.maximum(w, 1e-6)
    out[w < 0.99] = np.nan
    return out.astype("float32")
R = samp(vert)
U = samp(sig)
prof = dict(driver="GTiff", height=R.shape[0], width=R.shape[1], count=1, dtype="float32",
            crs="EPSG:4326", transform=from_origin(AOI[0], AOI[3], RES, RES), nodata=np.nan, compress="deflate")
tags_common = dict(STATUS="PROVISIONAL - built from 2x ~120-day NISAR tracks (t92D+t41A), LOS/cos(38deg); NOT the final product",
                   UNITS="cm/yr")
with rasterio.open(a.out_rate, "w", **prof) as f:
    f.write(R, 1)
    f.update_tags(DESCRIPTION="PROVISIONAL vertical velocity, negative = sinking", **tags_common)
with rasterio.open(a.out_unc, "w", **prof) as f:
    f.write(U, 1)
    f.update_tags(DESCRIPTION="PROVISIONAL 1-sigma uncertainty of vertical velocity", **tags_common)
print("rate min/p1/median/max", np.nanmin(R), np.nanpercentile(R, 1), np.nanmedian(R), np.nanmax(R))
print("unc median", np.nanmedian(U), "valid frac", np.isfinite(R).mean())
