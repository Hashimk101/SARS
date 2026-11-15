"""Compare NISAR (track 41, Jun-Oct 2026) per-pixel LOS rates with the Sentinel-1 ascending
360-day rate map (Sep 2024 - Sep 2025) over Quetta.

usage: compare_nisar_s1.py <nisar_npz_noiono> <nisar_npz_iono> <s1_unw_tif> <s1_cc_tif> <out_png>
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tifffile

f_no, f_io, f_unw, f_cc, out = sys.argv[1:6]
LAM_S1 = 0.05546576
REF = (66.80, 30.25)
VALLEY = (66.93, 30.05, 67.05, 30.28)


def nisar_rate(path):
    z = np.load(path)
    cum = z["cum_cm"].astype(np.float64)                     # (T, ny, nx)
    days = np.array([(np.datetime64(d) - np.datetime64(str(z["dates"][0]))).astype(int) for d in z["dates"]], float)
    t = days / 365.25
    valid = np.isfinite(cum)
    n = valid.sum(0)
    tt = np.where(valid, t[:, None, None], np.nan)
    tm = np.nanmean(tt, 0); ym = np.nanmean(cum, 0)
    cov = np.nansum((tt - tm) * (cum - ym), 0); var = np.nansum((tt - tm) ** 2, 0)
    slope = np.where((n >= 8) & (var > 0), cov / np.where(var > 0, var, 1), np.nan)
    return slope, z["lon"], z["lat"]


def smooth(a, k=5):
    p = k // 2
    v = np.isfinite(a)
    x = np.where(v, a, 0.0)
    def bs(m):
        m = np.pad(m, p, mode="constant")
        c = m.cumsum(0).cumsum(1); c = np.pad(c, ((1, 0), (1, 0)))
        return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    s, n = bs(x), bs(v.astype(float))
    return np.where(n >= k * k * 0.4, s / np.maximum(n, 1), np.nan)


def s1_rate():
    with tifffile.TiffFile(f_unw) as t:
        p = t.pages[0]; unw = p.asarray().astype(np.float64)
        sx, sy = p.tags["ModelPixelScaleTag"].value[:2]; tp = p.tags["ModelTiepointTag"].value
    cc = tifffile.imread(f_cc).astype(np.float64)
    x0, y0 = tp[3], tp[4]
    unw[(unw == 0) | (cc < 50)] = np.nan
    cm = -unw * LAM_S1 / (4 * np.pi) * 100
    r = int((y0 - REF[1]) / sy); c = int((REF[0] - x0) / sx)
    cm -= np.nanmedian(cm[r - 10:r + 11, c - 10:c + 11])
    return cm * 365.25 / 360.0, x0, y0, sx, sy


s1, x0, y0, sx, sy = s1_rate()
results = {}
for label, f in (("NISAR (no iono corr.)", f_no), ("NISAR (iono corrected)", f_io)):
    rate, lon, lat = nisar_rate(f)
    rate_s = smooth(rate)
    ri = np.clip(((y0 - lat) / sy).astype(int), 0, s1.shape[0] - 1)
    ci = np.clip(((lon - x0) / sx).astype(int), 0, s1.shape[1] - 1)
    s1_on_n = s1[ri, ci]
    inval = (lon >= VALLEY[0]) & (lon <= VALLEY[2]) & (lat >= VALLEY[1]) & (lat <= VALLEY[3])
    bowl = inval & (s1_on_n < -5)
    calm = inval & (s1_on_n > -1.5)
    ok = inval & np.isfinite(rate_s) & np.isfinite(s1_on_n)
    r_corr = np.corrcoef(rate_s[ok], s1_on_n[ok])[0, 1]
    mb = np.nanmedian(rate_s[bowl & np.isfinite(rate_s)]); mc = np.nanmedian(rate_s[calm & np.isfinite(rate_s)])
    nb = int((bowl & np.isfinite(rate_s)).sum()); nc = int((calm & np.isfinite(rate_s)).sum())
    # simple significance: bootstrap the bowl-minus-calm median difference
    rng = np.random.default_rng(0)
    vb = rate_s[bowl & np.isfinite(rate_s)]; vc = rate_s[calm & np.isfinite(rate_s)]
    boots = [np.median(rng.choice(vb, vb.size)) - np.median(rng.choice(vc, vc.size)) for _ in range(500)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    s1_b = np.nanmedian(s1_on_n[bowl]); s1_c = np.nanmedian(s1_on_n[calm])
    print(f"{label}: valley pixels compared {ok.sum()}, correlation with S1 r={r_corr:.2f}")
    print(f"   inside S1 bowl (S1<-5 cm/yr, n={nb}): NISAR median {mb:+.1f} cm/yr   [S1 median {s1_b:+.1f}]")
    print(f"   valley outside bowl (S1>-1.5, n={nc}): NISAR median {mc:+.1f} cm/yr   [S1 median {s1_c:+.1f}]")
    print(f"   bowl minus outside: NISAR {mb-mc:+.1f} cm/yr (95% bootstrap {lo:+.1f} to {hi:+.1f})")
    results[label] = (rate_s, lon, lat)

fig, axes = plt.subplots(1, 3, figsize=(17, 6))
ext_s1 = [x0, x0 + s1.shape[1] * sx, y0 - s1.shape[0] * sy, y0]
ax = axes[0]
im = ax.imshow(s1, cmap="RdBu", vmin=-15, vmax=15, extent=ext_s1, interpolation="nearest")
ax.set_title("Sentinel-1 ascending, Sep 2024 - Sep 2025\nLOS rate (cm/yr)", fontsize=10)
for ax, (label, (rate_s, lon, lat)) in zip(axes[1:], results.items()):
    ax.pcolormesh(lon, lat, rate_s, cmap="RdBu", vmin=-15, vmax=15, shading="auto")
    ax.set_title(f"{label}, Jun - Oct 2026\nLOS rate (cm/yr), 5x5 smoothed", fontsize=10)
for ax in axes:
    ax.set_xlim(66.80, 67.20); ax.set_ylim(30.0, 30.40)
    ax.plot(66.99, 30.18, "k*", ms=12, mec="w")
    ax.add_patch(plt.Rectangle(VALLEY[:2], VALLEY[2] - VALLEY[0], VALLEY[3] - VALLEY[1], fill=False, ec="k", ls="--"))
    ax.set_aspect(1 / np.cos(np.radians(30.2)))
fig.colorbar(im, ax=axes.tolist(), shrink=0.8, label="LOS rate (cm/yr); red = moving away (sinking)")
fig.savefig(out, dpi=110, bbox_inches="tight")
print("saved", out)
