"""Mosaic NISAR LATLON browse PNGs (frames 17+18, track 84) onto one lat/lon grid,
then map pixels that turned dark in HH (open-water candidates) between dates.

Browse PNGs are 8-bit quicklooks with RGB = HH, HV, HH. This is a screening check,
not calibrated backscatter.

usage: change_map.py <browse_dir> <out_png> <ctrl_a> <ctrl_b> <event_a> <event_b>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

LON0, LAT0, LON1, LAT1 = 73.55, 31.35, 74.95, 32.60
DLON, DLAT = 0.0018, 0.00155
PIX_KM2 = (DLON * 111.32 * np.cos(np.radians(32.0))) * (DLAT * 110.9)
FRAMES = ["t84f17", "t84f18"]
TOWNS = {
    "Sheikhupura": (73.985, 31.713), "Muridke": (74.255, 31.802),
    "Kamoke": (74.223, 31.975), "Gujranwala": (74.188, 32.161),
    "Lahore": (74.343, 31.549), "Nankana": (73.707, 31.450),
    "Daska": (74.350, 32.325), "Sialkot": (74.531, 32.494),
    "Pasrur": (74.663, 32.262), "Narowal": (74.873, 32.102),
}

browse = Path(sys.argv[1])
out = Path(sys.argv[2])
ctrl_a, ctrl_b, ev_a, ev_b = sys.argv[3:7]
index = json.loads((browse / "index.json").read_text())

lons = np.arange(LON0, LON1, DLON)
lats = np.arange(LAT1, LAT0, -DLAT)
LON, LAT = np.meshgrid(lons, lats)


def fit(arr, poly):
    valid = arr.sum(axis=2) > 0
    ys, xs = np.nonzero(valid)
    pts = [(xs.min(), ys[xs.argmin()]), (xs.max(), ys[xs.argmax()]),
           (xs[ys.argmin()], ys.min()), (xs[ys.argmax()], ys.max())]
    p = np.array(poly[:-1])
    verts = [p[p[:, 0].argmin()], p[p[:, 0].argmax()], p[p[:, 1].argmax()], p[p[:, 1].argmin()]]
    a, b = np.polyfit([v[0] for v in verts], [q[0] for q in pts], 1)
    c, d = np.polyfit([v[1] for v in verts], [q[1] for q in pts], 1)
    return a, b, c, d


def mosaic(date):
    hh = np.zeros(LON.shape, np.float32)
    ok = np.zeros(LON.shape, bool)
    for fr in FRAMES:
        key = f"{fr}_{date}"
        arr = np.asarray(Image.open(browse / f"{key}_latlon.png").convert("RGB"))
        a, b, c, d = fit(arr, index[key]["poly"])
        px = np.round(a * LON + b).astype(int)
        py = np.round(c * LAT + d).astype(int)
        inb = (px >= 0) & (px < arr.shape[1]) & (py >= 0) & (py < arr.shape[0])
        samp = np.zeros(arr.shape[:2] + (3,), arr.dtype)
        vals = np.zeros(LON.shape + (3,), np.uint8)
        vals[inb] = arr[py[inb], px[inb]]
        v = (vals.sum(axis=2) > 0) & ~ok
        hh[v] = vals[..., 0][v]
        ok |= v
    return hh, ok


def box(x, k=5):
    p = k // 2
    xp = np.pad(x, p, mode="edge").astype(np.float64)
    c = xp.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def otsu(v):
    hist, edges = np.histogram(v, bins=256, range=(0, 255))
    w0 = hist.cumsum(); w1 = w0[-1] - w0
    m = (hist * edges[:-1]).cumsum()
    mu0 = m / np.maximum(w0, 1); mu1 = (m[-1] - m) / np.maximum(w1, 1)
    return edges[np.argmax(w0 * w1 * (mu0 - mu1) ** 2)]


dates = sorted({ctrl_a, ctrl_b, ev_a, ev_b})
data = {}
for dt in dates:
    hh, ok = mosaic(dt)
    data[dt] = (box(hh), box(ok.astype(float)) > 0.999)

common = np.logical_and.reduce([data[d][1] for d in dates])
thr = otsu(np.concatenate([data[d][0][common] for d in dates]))
print(f"grid {LON.shape}, pixel {PIX_KM2:.4f} km2, common valid area {common.sum()*PIX_KM2:,.0f} km2")
print(f"dark (open-water) threshold on smoothed HH: {thr:.0f}/255")
for dt in dates:
    dark = (data[dt][0] < thr) & common
    print(f"  {dt}: dark area {dark.sum()*PIX_KM2:,.0f} km2 ({dark.mean()/common.mean()*100:.1f}% of valid)")


def newly_dark(a, b):
    return (data[a][0] >= thr + 8) & (data[b][0] < thr - 8) & common


ctrl = newly_dark(ctrl_a, ctrl_b)
ev = newly_dark(ev_a, ev_b)
print(f"newly dark {ctrl_a}->{ctrl_b} (control): {ctrl.sum()*PIX_KM2:,.0f} km2")
print(f"newly dark {ev_a}->{ev_b} (flood window): {ev.sum()*PIX_KM2:,.0f} km2")

# per-town 10 km neighbourhood stats
R = 0.09
for name, (lo, la) in TOWNS.items():
    near = (np.abs(LON - lo) < R) & (np.abs(LAT - la) < R * 0.85) & common
    if near.sum() > 50:
        print(f"  {name:12s} ~10km box: control {ctrl[near].mean()*100:5.1f}%  flood-window {ev[near].mean()*100:5.1f}%")


def panel(base_dt, mask, color, title):
    g = np.clip(data[base_dt][0], 0, 255).astype(np.uint8)
    rgb = np.stack([g, g, g], -1)
    rgb[~common] = (40, 40, 40)
    rgb[mask] = color
    im = Image.fromarray(rgb).resize((LON.shape[1], LON.shape[0]))
    im = im.resize((im.width * 1, im.height * 1))
    dr = ImageDraw.Draw(im)
    for name, (lo, la) in TOWNS.items():
        x = (lo - LON0) / DLON; y = (LAT1 - la) / DLAT
        dr.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(255, 255, 0), width=2)
        dr.text((x + 6, y - 6), name, fill=(255, 255, 0))
    dr.rectangle((0, 0, im.width, 18), fill=(0, 0, 0))
    dr.text((6, 3), title, fill=(255, 255, 255))
    return im


p1 = panel(ctrl_b, ctrl, (0, 200, 255), f"Control: newly dark {ctrl_a} -> {ctrl_b} (cyan)")
p2 = panel(ev_b, ev, (255, 40, 40), f"Flood window: newly dark {ev_a} -> {ev_b} (red)")
canvas = Image.new("RGB", (p1.width * 2 + 8, p1.height), (255, 255, 255))
canvas.paste(p1, (0, 0)); canvas.paste(p2, (p1.width + 8, 0))
canvas.save(out)
print("saved", out, canvas.size)
