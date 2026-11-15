"""Presentation-quality PNG maps and charts for the Quetta impact module."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

SCEN = {"S1": "S1 Current trend", "S2": "S2 Keeps accelerating", "S3": "S3 Pumping controlled"}
SC_COL = {"S1": "#1f77b4", "S2": "#d62728", "S3": "#2ca02c"}
CLS_COL = ["#e8e8e8", "#fff2a8", "#fdb863", "#e66101", "#7f0000"]
CLS_LAB = ["Negligible  (< 1/1000)", "Low  (1/1000 - 1/500)", "Slight: cracking onset  (1/500 - 1/300)",
           "Moderate: wall cracking  (1/300 - 1/150)", "Severe: structural-damage risk  (>= 1/150)"]
VIEW = (66.86, 67.12, 30.02, 30.34)
CITY = (66.99, 30.18)


def _base(ax, c, title):
    lo0, lo1, la0, la1 = VIEW
    ax.imshow(c["hill"], extent=[c["lons"][0], c["lons"][-1], c["lats"][-1], c["lats"][0]], cmap="gray", vmin=0.2, vmax=1.0,
              alpha=0.55, interpolation="bilinear")
    ax.set_xlim(lo0, lo1)
    ax.set_ylim(la0, la1)
    ax.set_aspect(1 / np.cos(np.radians(30.2)))
    ax.set_title(title, fontsize=11)
    ax.plot(*CITY, marker="*", color="k", ms=11, mec="w", mew=0.8)
    ax.annotate("Quetta", CITY, xytext=(5, 6), textcoords="offset points", fontsize=10, fontweight="bold",
                color="k", path_effects=None, bbox=dict(boxstyle="round,pad=0.15", fc="w", ec="none", alpha=0.7))
    ax.tick_params(labelsize=8)
    ax.set_xlabel("Longitude (E)", fontsize=8)


def _ext(c):
    return [c["lons"][0] - (c["lons"][1] - c["lons"][0]) / 2, c["lons"][-1] + (c["lons"][1] - c["lons"][0]) / 2,
            c["lats"][-1] - (c["lats"][0] - c["lats"][1]) / 2 * -1 if False else c["lats"][-1] - abs(c["lats"][1] - c["lats"][0]) / 2,
            c["lats"][0] + abs(c["lats"][1] - c["lats"][0]) / 2]


def _show(ax, c, arr, **kw):
    return ax.imshow(arr, extent=_ext(c), interpolation="nearest", **kw)


def _stamp(fig, c, extra=""):
    lab = c["label"]
    s = ("SCENARIO, NOT A FORECAST: what-if sinking under stated assumptions, with Monte Carlo uncertainty.\n"
         "Zone-level screening, not a building-by-building assessment.")
    fig.text(0.5, 0.008, s, ha="center", va="bottom", fontsize=9, style="italic", color="#444")
    if lab:
        fig.text(0.5, 0.935, f"Input: {lab} (rates from ~4 months of NISAR data, Jun-Oct 2026)", ha="center", fontsize=10,
                 fontweight="bold", color="#333")
    if extra:
        fig.text(0.5, 0.06, extra, ha="center", fontsize=8.5, color="#333")


def run(c):
    out = os.path.join(c["out"], "figures")
    os.makedirs(out, exist_ok=True)
    lab = c["label"]
    sfx = f"_{lab}" if lab else ""
    S = c["summary"]
    top = 0.90 if lab else 0.93

    # 1. current rate
    fig, ax = plt.subplots(figsize=(9, 9), dpi=200)
    _base(ax, c, "Measured vertical velocity (valley floor), cm/yr")
    vmax = np.ceil(np.nanpercentile(-c["rate"], 99.5))
    im = _show(ax, c, -c["rate"], cmap="magma_r", vmin=0, vmax=max(vmax, 10))
    for th, ls in ((5, "--"), (10, "-")):
        ax.contour(c["lons"], c["lats"], np.nan_to_num(-c["rate"]), levels=[th], colors="w", linewidths=1.0, linestyles=ls)
    cb = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
    cb.set_label("Sinking rate (cm/yr; white contours = 5 and 10 cm/yr)")
    _stamp(fig, c, "Mountains masked using Copernicus DEM (elevation < 1,750 m, slope < 4 deg).")
    fig.subplots_adjust(top=0.9 if lab else 0.94, bottom=0.12)
    fig.savefig(os.path.join(out, f"map_rate_today{sfx}.png")); plt.close(fig)

    # 2. cumulative 2050 median per scenario
    fig, axs = plt.subplots(1, 3, figsize=(18, 7.2), dpi=130, sharey=True)
    allv = [np.nanmax(c["full"](c["res_med"][(sc, 2050)])) for sc in SCEN]
    vmax = np.ceil(max(allv) / 50) * 50
    for ax, sc in zip(axs, SCEN):
        m = c["full"](c["res_med"][(sc, 2050)])
        _base(ax, c, SCEN[sc])
        im = _show(ax, c, m / 100.0, cmap="viridis_r", vmin=0, vmax=vmax / 100)
        ax.contour(c["lons"], c["lats"], np.nan_to_num(m / 100), levels=[1, 2, 3], colors="w", linewidths=0.8)
        b = S["scenarios"][sc]["bowl_max_cm"]["2050"]
        ax.text(0.02, 0.02, f"Bowl max by 2050 (median, p10-p90):\n{b['median']/100:.1f} m  ({b['p10']/100:.1f}-{b['p90']/100:.1f} m)",
                transform=ax.transAxes, fontsize=9.5, bbox=dict(fc="w", alpha=0.85, ec="none"))
    fig.subplots_adjust(left=0.05, right=0.9, top=0.87 if lab else 0.92, bottom=0.12, wspace=0.08)
    cb = fig.colorbar(im, cax=fig.add_axes([0.92, 0.25, 0.012, 0.5]))
    cb.set_label("Cumulative subsidence 2026 to 2050 (m, median; white contours 1, 2, 3 m)")
    fig.suptitle("Quetta valley: cumulative subsidence scenarios to 2050", fontsize=15, y=0.985)
    _stamp(fig, c)
    fig.savefig(os.path.join(out, f"map_cumulative_2050_scenarios{sfx}.png")); plt.close(fig)

    # 3. damage classes 3x3 and 2050 row
    cmap = ListedColormap(CLS_COL)
    norm = BoundaryNorm(np.arange(-0.5, 5), 5)
    def dmg_panel(ax, sc, y, title=None):
        _base(ax, c, title or f"{SCEN[sc]}, {y}")
        cl = c["classes"][(sc, y)].astype(float)
        cl[cl == 255] = np.nan
        _show(ax, c, cl, cmap=cmap, norm=norm)
        fz = c["fissures"][(sc, y)]
        ax.contour(c["lons"], c["lats"], fz.astype(float), levels=[0.5], colors="#0033cc", linewidths=0.9)
    handles = [Patch(fc=CLS_COL[i], ec="k", lw=0.3, label=CLS_LAB[i]) for i in range(5)] + [Patch(fc="none", ec="#0033cc", label="Heuristic fissure-risk flank zone")]
    fig, axs = plt.subplots(1, 3, figsize=(18, 7.2), dpi=130, sharey=True)
    for ax, sc in zip(axs, SCEN):
        dmg_panel(ax, sc, 2050)
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.06))
    fig.suptitle("Damage-risk screening zones in 2050 (angular distortion of median scenario field, 80 m grid)", fontsize=14, y=0.985)
    _stamp(fig, c)
    fig.subplots_adjust(top=0.87 if lab else 0.92, bottom=0.2)
    fig.savefig(os.path.join(out, f"map_damage_zones_2050{sfx}.png")); plt.close(fig)

    fig, axs = plt.subplots(3, 3, figsize=(16, 16), dpi=110, sharex=True, sharey=True)
    for i, sc in enumerate(SCEN):
        for j, y in enumerate((2030, 2040, 2050)):
            dmg_panel(axs[i, j], sc, y)
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.03))
    fig.suptitle("Damage-risk screening zones, 2030 / 2040 / 2050 (rows: scenarios)", fontsize=15, y=0.985)
    _stamp(fig, c)
    fig.subplots_adjust(top=0.88 if lab else 0.93, bottom=0.1, hspace=0.18)
    fig.savefig(os.path.join(out, f"map_damage_zones_grid{sfx}.png")); plt.close(fig)

    # 4. time series
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=170)
    yrs = list(range(2026, 2051))
    for sc in SCEN:
        arr = np.array([c["ts"][sc][y] for y in yrs]) / 100.0
        ax.fill_between(yrs, arr[:, 0], arr[:, 2], color=SC_COL[sc], alpha=0.2, lw=0)
        ax.plot(yrs, arr[:, 1], color=SC_COL[sc], lw=2.2, label=f"{SCEN[sc]} (median; band = p10-p90)")
    ax.set_xlabel("Year"); ax.set_ylabel("Cumulative subsidence at the bowl maximum since Jan 2026 (m)")
    ax.set_title("Bowl-maximum subsidence scenarios, 2026-2050" + (f"  [{lab}]" if lab else ""), fontsize=13)
    ax.grid(alpha=0.3); ax.legend(loc="upper left", fontsize=9)
    ax.set_xlim(2026, 2050)
    fig.text(0.5, 0.01, "Scenario, not a forecast. Uncertainty includes rate-map error and scenario parameters; it excludes structural surprises (e.g. wells drying, policy shocks).",
             ha="center", fontsize=8, style="italic")
    fig.subplots_adjust(bottom=0.12)
    fig.savefig(os.path.join(out, f"chart_bowl_max_timeseries{sfx}.png")); plt.close(fig)

    # 5. exposure bars
    rows = [r for r in c["exposure_rows"] if r["field"] == "median" and r["year"] == 2050 and r["zone"].startswith("class_")]
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), dpi=130)
    w = 0.26
    for k, (key, tl) in enumerate((("buildings", "Buildings"), ("people", "People"))):
        for i, sc in enumerate(SCEN):
            vals = [next(r[key] for r in rows if r["scenario"] == sc and r["zone"].startswith(f"class_{q}_")) for q in range(5)]
            axs[k].bar(np.arange(5) + (i - 1) * w, vals, w, color=SC_COL[sc], label=SCEN[sc])
        axs[k].set_xticks(range(5)); axs[k].set_xticklabels(["negligible", "low", "slight", "moderate", "severe"])
        axs[k].set_title(f"{tl} per damage-risk zone, 2050 (median scenario field)"); axs[k].grid(alpha=0.3, axis="y")
        axs[k].set_yscale("symlog", linthresh=100)
    axs[0].legend(fontsize=9)
    fig.text(0.5, 0.01, "Log-ish axis. Scenario, not a forecast. Counts = footprint centroids (Microsoft) / WorldPop 2025 inside the valley mask." + (f"  [{lab}]" if lab else ""),
             ha="center", fontsize=8, style="italic")
    fig.subplots_adjust(bottom=0.12)
    fig.savefig(os.path.join(out, f"chart_exposure_2050{sfx}.png")); plt.close(fig)
