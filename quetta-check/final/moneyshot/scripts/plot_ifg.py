"""plot_ifg.py ifg.npz tag title outdir [subtitle] -> figures, GeoTIFF, stats json
Phase convention: ifg = s_early * conj(s_late); positive phase = range increase = motion AWAY from satellite."""
import sys, json, datetime as dt, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tifffile
from pyproj import Transformer

npz, tag, title, outdir = sys.argv[1:5]
sub = sys.argv[5] if len(sys.argv) > 5 else ""
d = np.load(npz, allow_pickle=False); meta = json.loads(str(d["meta"]))
ifg = d["ifg_f"]; raw = d["ifg"]; coh = d["coh"]
x0, y0, dx, dy = [float(d[k]) for k in ("x0", "y0", "dx", "dy")]; epsg = int(d["epsg"])
H, W = ifg.shape; X = x0 + dx * np.arange(W); Y = y0 + dy * np.arange(H)
T = Transformer.from_crs(4326, epsg, always_xy=True); Ti = Transformer.from_crs(epsg, 4326, always_xy=True)
lam = 299792458.0 / meta["m1"]["freq"]


def ij(lon, lat):
    x, y = T.transform(lon, lat); return int(round((y - y0) / dy)), int(round((x - x0) / dx))


# reference phase: coherent pixels around 66.80E 30.25N
ri, rj = ij(66.80, 30.25); w = int(2000 / abs(dx)) + 1
sl = (slice(ri - w, ri + w + 1), slice(rj - w, rj + w + 1))
ok = coh[sl] > 0.4
sel = ifg[sl][ok]
refph = np.angle(np.sum(sel / np.maximum(np.abs(sel), 1e-9))) if ok.sum() > 5 else np.angle(np.nansum(ifg[sl]))
print("ref phase", refph, "ref coh", np.nanmean(coh[sl]), "n ok", ok.sum())
ph = np.angle(ifg * np.exp(-1j * refph)); phr = np.angle(raw * np.exp(-1j * refph))
mask = np.isnan(coh)
extent = [X[0] - dx / 2, X[-1] + dx / 2, Y[-1] + abs(dy) / 2, Y[0] - abs(dy) / 2]
a_, b_ = meta["m1"]["date"], meta["m2"]["date"]
days = (dt.date.fromisoformat(b_) - dt.date.fromisoformat(a_)).days


def rgba(phase, c):
    rgb = plt.get_cmap("hsv")((phase + np.pi) / (2 * np.pi))[..., :3]
    a = np.clip((np.nan_to_num(c) - 0.12) / 0.33, 0, 1)[..., None]
    return rgb * a + np.array([0.12, 0.12, 0.14]) * (1 - a)


def colorbar(fig, label):
    cax = fig.add_axes([0.30, 0.075, 0.40, 0.025]); g = np.linspace(-np.pi, np.pi, 256)[None, :]
    cax.imshow(plt.get_cmap("hsv")((g + np.pi) / (2 * np.pi)), extent=[-np.pi, np.pi, 0, 1], aspect="auto"); cax.set_yticks([])
    cax.set_xticks([-np.pi, 0, np.pi]); cax.set_xticklabels(["-π", "0", "+π"]); cax.set_xlabel(label, fontsize=9)


LBL = (f"Wrapped phase. One colour cycle ≈ {lam/2*100:.0f} cm of ground motion toward/away from the satellite (line of sight).\n"
       "Positive phase = range increase (away from satellite). Faded = low coherence. Referenced to bedrock at 66.80°E 30.25°N.")


def label_quetta(ax, bold=13):
    qx, qy = T.transform(66.99, 30.18); ax.plot(qx, qy, "k+", ms=14, mew=2.5); ax.plot(qx, qy, "w+", ms=14, mew=1)
    ax.annotate("Quetta", (qx, qy), xytext=(8, 8), textcoords="offset points", color="w", fontsize=bold, weight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="k", alpha=0.55, lw=0))


def style_full(ax):
    lon_t = [66.8, 66.9, 67.0, 67.1, 67.2]; lat_t = [30.0, 30.1, 30.2, 30.3, 30.4]
    ax.set_xticks([T.transform(l, 30.2)[0] for l in lon_t]); ax.set_xticklabels([f"{l:.1f}°E" for l in lon_t])
    ax.set_yticks([T.transform(67.0, l)[1] for l in lat_t]); ax.set_yticklabels([f"{l:.1f}°N" for l in lat_t])
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3]); label_quetta(ax)
    rx, ry = T.transform(66.80, 30.25); ax.plot(rx, ry, "s", mfc="none", mec="k", ms=9)
    ax.annotate("ref (bedrock)", (rx, ry), xytext=(6, -14), textcoords="offset points", fontsize=9, color="k",
                bbox=dict(boxstyle="round,pad=0.15", fc="w", alpha=0.6, lw=0))
    sx = extent[0] + 3000; sy = extent[2] + 3000
    ax.plot([sx, sx + 10000], [sy, sy], "k-", lw=4); ax.plot([sx, sx + 10000], [sy, sy], "w-", lw=1.5)
    ax.text(sx + 5000, sy + 800, "10 km", ha="center", fontsize=9, color="k", bbox=dict(fc="w", alpha=.6, lw=0, pad=1))


def mainfig(phase, fn, ttl):
    fig = plt.figure(figsize=(11, 12.5), dpi=150); ax = fig.add_axes([0.1, 0.16, 0.86, 0.74])
    ax.imshow(rgba(phase, coh), extent=extent, interpolation="nearest", aspect="equal"); style_full(ax)
    ax.set_title(ttl, fontsize=13, weight="bold", loc="left"); colorbar(fig, LBL); fig.savefig(fn); plt.close(fig)


ttl = f"{title}\nNISAR L-band GSLC interferogram, {a_} → {b_} ({days} days)\n{sub}, {abs(dx):.0f} m multilook"
mainfig(ph, f"{outdir}/{tag}_interferogram_filtered.png", ttl)
mainfig(phr, f"{outdir}/{tag}_interferogram_unfiltered.png", ttl)

fig = plt.figure(figsize=(11, 10.5), dpi=150); ax = fig.add_axes([0.1, 0.1, 0.78, 0.8])
im = ax.imshow(coh, extent=extent, cmap="viridis", vmin=0, vmax=1, aspect="equal"); style_full(ax)
ax.set_title(f"Coherence, {a_} → {b_} ({days} d), {abs(dx):.0f} m multilook", fontsize=13, weight="bold", loc="left")
fig.colorbar(im, cax=fig.add_axes([0.9, 0.2, 0.02, 0.6]), label="coherence"); fig.savefig(f"{outdir}/{tag}_coherence.png"); plt.close(fig)

# ---- statistics
LON, LAT = Ti.transform(*np.meshgrid(X, Y))
bowl = (np.abs(LON - 66.99) < 0.03) & (LAT > 30.10) & (LAT < 30.25)
outside = ((LON < 66.88) | (LON > 67.10)) & (LAT > 30.05) & (LAT < 30.35)
stats = dict(pair=[a_, b_], days=days, multilook_m=abs(dx), coh_mean_all=float(np.nanmean(coh)),
             coh_mean_bowl=float(np.nanmean(coh[bowl])), coh_mean_outside=float(np.nanmean(coh[outside])),
             coh_median_bowl=float(np.nanmedian(coh[bowl])), frac_coh_gt_0p3_bowl=float(np.nanmean(coh[bowl] > 0.3)),
             frac_coh_gt_0p3_all=float(np.nanmean(coh > 0.3)), ref_phase_rad=float(refph), wavelength_m=float(lam),
             fringe_cm=float(lam / 2 * 100), versions=[meta["m1"]["version"], meta["m2"]["version"]],
             coreg=meta.get("coreg"))

# ---- transects
ci, cj = ij(66.99, 30.18)
fig, axs = plt.subplots(2, 2, figsize=(13, 7), dpi=130)
for k, kind in enumerate(("EW", "NS")):
    if kind == "EW":
        ii = slice(ci - 2, ci + 3); v = np.nanmean(np.where(mask[ii, :], np.nan, np.exp(1j * ph[ii, :])), 0); c = np.nanmean(coh[ii, :], 0); pos = LON[ci, :]; cpos = 66.99
    else:
        jj = slice(cj - 2, cj + 3); v = np.nanmean(np.where(mask[:, jj], np.nan, np.exp(1j * ph[:, jj])), 1); c = np.nanmean(coh[:, jj], 1); pos = LAT[:, cj]; cpos = 30.18
    p = np.angle(v); good = np.isfinite(p) & (c > 0.3)
    axs[0, k].plot(pos, np.where(good, p, np.nan), ".", ms=2); axs[0, k].set_ylabel("wrapped phase (rad)")
    axs[0, k].set_title(f"{kind} transect through 66.99E 30.18N (5 px wide)")
    axs[1, k].plot(pos, c); axs[1, k].axhline(0.3, c="r", ls=":"); axs[1, k].set_ylabel("coherence")
    ctr = int(np.argmin(abs(pos - cpos))); lo = ctr
    if good[ctr]:
        while lo > 0 and good[lo - 1]: lo -= 1
        hi = ctr
        while hi < len(p) - 1 and good[hi + 1]: hi += 1
        u = np.unwrap(p[lo:hi + 1])
        stats[f"{kind}_contiguous_run_deg"] = [float(pos[lo]), float(pos[hi])]
        stats[f"{kind}_unwrapped_range_cycles"] = float((u.max() - u.min()) / (2 * np.pi))
        stats[f"{kind}_centre_minus_run_ends_cycles"] = [float((u[ctr - lo] - u[0]) / (2 * np.pi)), float((u[ctr - lo] - u[-1]) / (2 * np.pi))]
        axs[0, k].plot(pos[lo:hi + 1], u, "r-", lw=1, alpha=.6)
plt.tight_layout(); fig.savefig(f"{outdir}/{tag}_transects.png"); plt.close(fig)


# ---- high-pass (12 km box, coherence-weighted complex mean removed) + zoom figures
def boxmean(z, n):
    zz = np.nan_to_num(z); wgt = np.clip(np.nan_to_num(coh), 0, 1)

    def bf(a):
        c = np.pad(np.cumsum(np.cumsum(a, 0), 1), ((1, 0), (1, 0))); h = n // 2; Hh, Ww = a.shape
        i0 = np.clip(np.arange(Hh) - h, 0, Hh); i1 = np.clip(np.arange(Hh) + h + 1, 0, Hh)
        j0 = np.clip(np.arange(Ww) - h, 0, Ww); j1 = np.clip(np.arange(Ww) + h + 1, 0, Ww)
        return c[i1][:, j1] - c[i0][:, j1] - c[i1][:, j0] + c[i0][:, j0]
    return bf(zz * wgt) / np.maximum(bf(wgt), 1e-6)


unit = np.nan_to_num(ifg / np.maximum(np.abs(ifg), 1e-9))
lp = boxmean(unit, int(12000 / abs(dx)))
hp = np.angle(unit * np.conj(lp / np.maximum(np.abs(lp), 1e-9)))
x0z, x1z = T.transform(66.90, 30.10)[0], T.transform(67.08, 30.10)[0]; y0z, y1z = T.transform(67.0, 30.10)[1], T.transform(67.0, 30.28)[1]
for nm, phase, tt in (("zoom", ph, "Zoom on the Quetta basin, referenced to bedrock"),
                      ("zoom_highpass", hp, "Zoom, smooth ramps removed (12 km high-pass): local signals only")):
    fig = plt.figure(figsize=(11, 12.5), dpi=150); ax = fig.add_axes([0.1, 0.16, 0.86, 0.74])
    ax.imshow(rgba(phase, coh), extent=extent, interpolation="nearest", aspect="equal"); ax.set_xlim(x0z, x1z); ax.set_ylim(y0z, y1z)
    ax.set_xticks([T.transform(l, 30.2)[0] for l in (66.9, 66.95, 67.0, 67.05)]); ax.set_xticklabels(["66.90°E", "66.95°E", "67.00°E", "67.05°E"])
    ax.set_yticks([T.transform(67.0, l)[1] for l in (30.1, 30.15, 30.2, 30.25)]); ax.set_yticklabels(["30.10°N", "30.15°N", "30.20°N", "30.25°N"])
    label_quetta(ax)
    sx = x0z + 1000; sy = y0z + 800; ax.plot([sx, sx + 5000], [sy, sy], "w-", lw=3); ax.text(sx + 2500, sy + 300, "5 km", ha="center", color="w", fontsize=10)
    ax.set_title(f"{tt}\nNISAR L-band GSLC {a_} → {b_} ({days} d)", fontsize=13, weight="bold", loc="left")
    colorbar(fig, f"One colour cycle ≈ {lam/2*100:.0f} cm of line-of-sight motion. Positive = away from satellite. Faded = low coherence.")
    fig.savefig(f"{outdir}/{tag}_{nm}.png"); plt.close(fig)
r = int(1500 / abs(dx)); cb = (slice(ci - r, ci + r + 1), slice(cj - r, cj + r + 1))
ang = np.angle(np.nansum(np.exp(1j * hp[cb]) * np.nan_to_num(coh[cb])))
stats["highpass_phase_city_3km_rad"] = float(ang); stats["highpass_los_cm_city_away_positive"] = float(ang * lam / (4 * np.pi) * 100)

# ---- GeoTIFF (band 1 = wrapped phase rad, referenced; band 2 = coherence)
arr = np.stack([ph.astype(np.float32), np.nan_to_num(coh, nan=0).astype(np.float32)])
tifffile.imwrite(f"{outdir}/{tag}_phase_coh.tif", arr, photometric="minisblack", planarconfig="separate",
                 extratags=[(33550, "d", 3, (abs(dx), abs(dy), 0.0), False),
                            (33922, "d", 6, (0, 0, 0, X[0] - dx / 2, Y[0] + abs(dy) / 2, 0), False),
                            (34735, "H", 16, (1, 1, 0, 3, 1024, 0, 1, 1, 1025, 0, 1, 1, 3072, 0, 1, epsg), False)])
json.dump(stats, open(f"{outdir}/{tag}_stats.json", "w"), indent=1); print(json.dumps(stats, indent=1))
