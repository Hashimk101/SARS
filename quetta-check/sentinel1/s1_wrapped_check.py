"""Compare LiCSAR wrapped phase + coherence over Quetta for ascending vs descending pairs.

If the descending wrapped phase shows a ring pattern over the valley where the unwrapped
product showed nothing, the descending 'no bowl' result is an unwrapping failure, not
absence of motion.

usage: s1_wrapped_check.py <data_dir> <out_png> <prefix1> [prefix2 ...]
  (each prefix -> <prefix>.diff_pha.tif and <prefix>.cc.tif)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tifffile

LON0, LAT0, LON1, LAT1 = 66.75, 29.95, 67.25, 30.45
VALLEY = (66.95, 30.10, 67.03, 30.25)
OUTSIDE = (66.78, 30.22, 66.84, 30.28)

d = Path(sys.argv[1])
out = Path(sys.argv[2])
prefixes = sys.argv[3:]


def read(path):
    with tifffile.TiffFile(path) as t:
        p = t.pages[0]
        a = p.asarray().astype(np.float32)
        sx, sy = p.tags["ModelPixelScaleTag"].value[:2]
        tp = p.tags["ModelTiepointTag"].value
        x0, y0 = tp[3], tp[4]
    lons = x0 + (np.arange(a.shape[1]) + 0.5) * sx
    lats = y0 - (np.arange(a.shape[0]) + 0.5) * sy
    c = (lons >= LON0) & (lons <= LON1)
    r = (lats >= LAT0) & (lats <= LAT1)
    return a[np.ix_(r, c)], lons[c], lats[r]


def box_stat(arr, lons, lats, box):
    c = (lons >= box[0]) & (lons <= box[2])
    r = (lats >= box[1]) & (lats <= box[3])
    v = arr[np.ix_(r, c)]
    v = v[np.isfinite(v) & (v != 0)]
    return v


fig, axes = plt.subplots(2, len(prefixes), figsize=(5.2 * len(prefixes), 9.5))
axes = np.atleast_2d(axes).reshape(2, len(prefixes))
for i, pre in enumerate(prefixes):
    pha, lons, lats = read(d / f"{pre}.diff_pha.tif")
    cc, _, _ = read(d / f"{pre}.cc.tif")
    ccn = cc / 255.0 if cc.max() > 1.5 else cc
    pha_m = np.where((pha == 0) | ~np.isfinite(pha), np.nan, pha)
    ext = [lons[0], lons[-1], lats[-1], lats[0]]
    ax = axes[0, i]
    ax.imshow(pha_m, cmap="hsv", vmin=-np.pi, vmax=np.pi, extent=ext, interpolation="nearest")
    ax.set_title(f"{pre}\nwrapped phase (one colour cycle = 2.8 cm LOS)", fontsize=9)
    ax2 = axes[1, i]
    im2 = ax2.imshow(ccn, cmap="gray", vmin=0, vmax=1, extent=ext, interpolation="nearest")
    ax2.set_title(f"{pre}\ncoherence", fontsize=9)
    for a in (ax, ax2):
        a.plot(66.99, 30.18, "k*", ms=12, mec="w")
        a.add_patch(plt.Rectangle(VALLEY[:2], VALLEY[2] - VALLEY[0], VALLEY[3] - VALLEY[1], fill=False, ec="k", lw=1.2, ls="--"))
    cv = box_stat(ccn, lons, lats, VALLEY)
    co = box_stat(ccn, lons, lats, OUTSIDE)
    pv = box_stat(pha_m, lons, lats, VALLEY)
    # phase roughness: mean |gradient| in valley -> many fringes => high value
    g = np.abs(np.angle(np.exp(1j * np.diff(np.nan_to_num(pha_m), axis=0))))
    c = (lons >= VALLEY[0]) & (lons <= VALLEY[2]); r = (lats[:-1] >= VALLEY[1]) & (lats[:-1] <= VALLEY[3])
    print(f"{pre}: coherence valley median {np.median(cv):.2f} (n={cv.size}), outside {np.median(co):.2f}; "
          f"valley valid phase px {pv.size}; mean |dphase/dy| in valley {np.nanmean(g[np.ix_(r, c)]):.2f} rad/px")
fig.colorbar(im2, ax=axes[1, :].tolist(), shrink=0.6, label="coherence")
fig.savefig(out, dpi=110, bbox_inches="tight")
print("saved", out)
