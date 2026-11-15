"""Render an RGB (HH,HV,HH) mosaic time series of NISAR browse quicklooks for a lon/lat box.

usage: timeseries.py <browse_dir> <out_png> lon0 lat0 lon1 lat1 date1 [date2 ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

browse = Path(sys.argv[1])
out = Path(sys.argv[2])
lon0, lat0, lon1, lat1 = map(float, sys.argv[3:7])
dates = sys.argv[7:]
index = json.loads((browse / "index.json").read_text())
DLON, DLAT, SCALE = 0.0018, 0.00155, 2
FRAMES = ["t84f17", "t84f18"]
TOWNS = {
    "Muridke": (74.255, 31.802), "Kamoke": (74.223, 31.975),
    "Gujranwala": (74.188, 32.161), "Daska": (74.350, 32.325),
    "Sialkot": (74.531, 32.494), "Pasrur": (74.663, 32.262),
    "Narowal": (74.873, 32.102), "Sheikhupura": (73.985, 31.713),
}
lons = np.arange(lon0, lon1, DLON)
lats = np.arange(lat1, lat0, -DLAT)
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


labels = {"20260702": "2 Jul (before)", "20260714": "14 Jul (before)",
          "20260726": "26 Jul (flooding)", "20260819": "19 Aug (after)"}
tiles = []
for dt in dates:
    rgb = np.zeros(LON.shape + (3,), np.uint8)
    ok = np.zeros(LON.shape, bool)
    for fr in FRAMES:
        key = f"{fr}_{dt}"
        arr = np.asarray(Image.open(browse / f"{key}_latlon.png").convert("RGB"))
        a, b, c, d = fit(arr, index[key]["poly"])
        px = np.round(a * LON + b).astype(int)
        py = np.round(c * LAT + d).astype(int)
        inb = (px >= 0) & (px < arr.shape[1]) & (py >= 0) & (py < arr.shape[0])
        vals = np.zeros(LON.shape + (3,), np.uint8)
        vals[inb] = arr[py[inb], px[inb]]
        v = (vals.sum(axis=2) > 0) & ~ok
        rgb[v] = vals[v]
        ok |= v
    im = Image.fromarray(rgb).resize((LON.shape[1] * SCALE, LON.shape[0] * SCALE), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    for name, (lo, la) in TOWNS.items():
        if lon0 <= lo <= lon1 and lat0 <= la <= lat1:
            x = (lo - lon0) / DLON * SCALE; y = (lat1 - la) / DLAT * SCALE
            dr.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(255, 255, 0), width=2)
            dr.text((x + 8, y - 6), name, fill=(255, 255, 0))
    dr.rectangle((0, 0, 150, 18), fill=(0, 0, 0))
    dr.text((6, 3), labels.get(dt, dt), fill=(255, 255, 255))
    tiles.append(im)

gap = 8
canvas = Image.new("RGB", (sum(t.width for t in tiles) + gap * (len(tiles) - 1), tiles[0].height), (255, 255, 255))
x = 0
for t in tiles:
    canvas.paste(t, (x, 0)); x += t.width + gap
canvas.save(out)
print("saved", out, canvas.size)
