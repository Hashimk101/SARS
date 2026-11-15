"""Presentation PNGs from the products written by make_products.py.
usage: make_figures.py <outdir>      (needs numpy, scipy, matplotlib; run with -I)"""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nlib

out = Path(sys.argv[1])
S = json.loads((out / "work" / "summary_partial.json").read_text())
g = np.load(out / "work" / "grid4326.npz")
lon, lat = g["lon"], g["lat"]
LON, LAT = np.meshgrid(lon, lat)
KEYS = ["041", "142", "092", "020"]
tr = S["tracks"]
d0 = min(tr[k]["dates"][0] for k in KEYS); d1 = max(tr[k]["dates"][-1] for k in KEYS)
XL, YL = (66.80, 67.20), (30.00, 30.40)
ASPECT = 1 / np.cos(np.radians(30.2))
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12})
CM = plt.get_cmap("RdBu").copy(); CM.set_bad("#e6e6e6")


def decorate(ax, label=True):
    ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_aspect(ASPECT)
    ax.plot(66.99, 30.18, "k*", ms=15, mfc="yellow", mec="k", zorder=5)
    if label:
        ax.annotate("Quetta", (66.99, 30.18), xytext=(8, -16), textcoords="offset points", weight="bold", fontsize=12,
                    path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=3, foreground="w")], zorder=6)
    ax.set_xlabel("longitude (deg E)"); ax.set_ylabel("latitude (deg N)")


# ---------------------------------------------------------------- 1. vertical velocity
vs = nlib.smooth(g["vert"], 5)
lim = 12
fig, ax = plt.subplots(figsize=(11.5, 10.2), dpi=160)
pm = ax.pcolormesh(LON, LAT, np.ma.masked_invalid(vs), cmap=CM, vmin=-lim, vmax=lim, shading="auto", rasterized=True)
cs = ax.contour(LON, LAT, np.nan_to_num(vs, nan=0), levels=[-10, -5, -2], colors=["k", "#333", "#666"], linewidths=[1.4, 1.0, 0.8])
ax.clabel(cs, fmt="%d cm/yr", fontsize=8)
cb = fig.colorbar(pm, ax=ax, shrink=0.8, pad=0.02, extend="both")
cb.set_label("vertical velocity (cm/yr)   negative = sinking, positive = rising")
decorate(ax)
v = S["vertical"]
ax.set_title(f"Quetta land subsidence from NISAR (L-band): vertical velocity\n{d0} to {d1}, ascending + descending tracks combined; negative = sinking",
             fontsize=13)
ax.text(0.01, 0.01, f"bowl median {v.get('bowl_median_cm_yr', float('nan')):+.1f} cm/yr; max {v.get('max_sinking_cm_yr_smoothed5x5', float('nan')):+.1f} cm/yr "
        f"at {v.get('max_sinking_lon', float('nan')):.3f}E {v.get('max_sinking_lat', float('nan')):.3f}N\n"
        f"5x5-pixel smoothed (~400 m); 120-day rate extrapolated to a year; residual mountain blobs = weather/terrain noise"
        + ("\nAPPROXIMATE geometry" if v.get("approximate_geometry") else ""),
        transform=ax.transAxes, fontsize=8.5, va="bottom", bbox=dict(fc="w", ec="0.6", alpha=0.85))
fig.tight_layout(); fig.savefig(out / "vertical_velocity_map.png"); plt.close(fig)

# ---------------------------------------------------------------- 2. four LOS maps
fig, axes = plt.subplots(1, 4, figsize=(21, 6.4), dpi=100, sharey=True)
for ax, k in zip(axes, KEYS):
    a = nlib.smooth(g[f"v{k}"], 5)
    pm = ax.pcolormesh(LON, LAT, np.ma.masked_invalid(a), cmap=CM, vmin=-lim, vmax=lim, shading="auto", rasterized=True)
    decorate(ax)
    t = tr[k]
    ax.set_title(f"Track {t['track']} ({t['pass_direction']})\n{t['dates'][0]} to {t['dates'][-1]}, r vs S1 = {t['r_vs_s1']:.2f}"
                 f"{'' if t['correction_used']=='none' else ' (DEM-corrected)'}", fontsize=11)
fig.colorbar(pm, ax=axes.tolist(), shrink=0.85, pad=0.01, extend="both").set_label("LOS velocity (cm/yr), negative = away from satellite = sinking")
fig.suptitle("NISAR line-of-sight velocity per track, Quetta (negative = sinking; Jun-Oct 2026 rate, 5x5 smoothed)", fontsize=14, y=1.0)
fig.savefig(out / "los_velocity_4tracks.png", bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- 3. validation vs Sentinel-1
fig = plt.figure(figsize=(23, 10.5), dpi=100)
gs = fig.add_gridspec(2, 5, hspace=0.32, wspace=0.28)
ax = fig.add_subplot(gs[0, 0])
s1m = g["s1"]
ax.pcolormesh(LON, LAT, np.ma.masked_invalid(s1m), cmap=CM, vmin=-lim, vmax=lim, shading="auto", rasterized=True)
decorate(ax, label=False); ax.set_title("Sentinel-1 ascending\n2024-09-09 to 2025-09-04 (LOS cm/yr)", fontsize=11)
for i, k in enumerate(KEYS):
    ax = fig.add_subplot(gs[0, i + 1])
    pm = ax.pcolormesh(LON, LAT, np.ma.masked_invalid(nlib.smooth(g[f"v{k}"], 5)), cmap=CM, vmin=-lim, vmax=lim, shading="auto", rasterized=True)
    decorate(ax, label=False); t = tr[k]
    ax.set_title(f"NISAR track {t['track']} ({t['pass_direction'][:3]}.)\n{t['dates'][0][5:]} to {t['dates'][-1][5:]} 2026", fontsize=11)
fig.colorbar(pm, ax=fig.axes[:5], shrink=0.8, pad=0.01, extend="both", location="right").set_label("LOS velocity (cm/yr); negative = sinking")
# profile
ax = fig.add_subplot(gs[1, 0])
sel = (lon >= 66.97) & (lon <= 67.01)
ax.plot(np.nanmedian(s1m[:, sel], 1), lat, "k", lw=2.5, label="Sentinel-1 2024-25")
cols = ["#d95f02", "#e6ab02", "#1b9e77", "#7570b3"]
for k, c in zip(KEYS, cols):
    ax.plot(np.nanmedian(nlib.smooth(g[f"v{k}"], 5)[:, sel], 1), lat, color=c, lw=1.6, label=f"NISAR t{int(k)}")
ax.axvline(0, color="0.6", lw=0.8); ax.set_ylim(30.0, 30.4); ax.set_xlim(-16, 8)
ax.set_xlabel("LOS velocity (cm/yr)"); ax.set_ylabel("latitude"); ax.set_title("N-S profile, 66.97-67.01E median", fontsize=11)
ax.legend(fontsize=8, loc="lower left"); ax.grid(alpha=0.3)
for i, k in enumerate(KEYS):
    ax = fig.add_subplot(gs[1, i + 1])
    n = np.load(out / "work" / f"track{k}_native.npz")
    m = nlib.box(n["lon"], n["lat"], nlib.VALLEY) & np.isfinite(n["smooth_v"]) & np.isfinite(n["s1"])
    ax.hexbin(n["s1"][m], n["smooth_v"][m], gridsize=60, extent=(-16, 8, -16, 12), cmap="viridis", mincnt=1, bins="log")
    ax.plot([-16, 8], [-16, 8], "r--", lw=1); ax.set_xlim(-16, 8); ax.set_ylim(-16, 12)
    t = tr[k]
    ax.set_title(f"t{t['track']}: r = {t['r_vs_s1']:.2f}; bowl median {t['median_in_s1_bowl_cm_yr']:+.1f} (S1 {t['s1_median_in_bowl_cm_yr']:+.1f})\n"
                 f"outside bowl {t['median_valley_outside_bowl_cm_yr']:+.1f} (S1 {t['s1_median_valley_outside_bowl_cm_yr']:+.1f}) cm/yr", fontsize=9.5)
    ax.set_xlabel("Sentinel-1 LOS rate (cm/yr)"); ax.set_ylabel("NISAR LOS rate (cm/yr)"); ax.grid(alpha=0.3)
fig.suptitle("Validation: NISAR (Jun-Oct 2026) vs Sentinel-1 (2024-25) over Quetta valley; negative = sinking. Different years/wavelengths/geometry: compare shape and magnitude, not exact values",
             fontsize=13, y=0.98)
fig.savefig(out / "validation_nisar_vs_sentinel1.png", bbox_inches="tight"); plt.close(fig)
print("figures written")
