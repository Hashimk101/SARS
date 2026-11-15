"""Georeference NISAR LATLON browse PNGs from their footprint polygons and crop an area.

The LATLON browse image is in plain lat/lon, so x is linear in lon and y is linear
in lat. We match the extreme valid pixels (left/right/top/bottom) of the image to
the footprint polygon's min-lon/max-lon/max-lat/min-lat vertices and fit
x = a*lon + b, y = c*lat + d by least squares.

usage: georef_crop.py <browse_dir> <scene_prefix> <out_png> lon0 lat0 lon1 lat1 date1 [date2 ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

TOWNS = {
    "Sheikhupura": (73.985, 31.713),
    "Muridke": (74.255, 31.802),
    "Kamoke": (74.223, 31.975),
    "Gujranwala": (74.188, 32.161),
    "Lahore": (74.343, 31.549),
    "Nankana": (73.707, 31.450),
    "Daska": (74.350, 32.325),
    "Sialkot": (74.531, 32.494),
    "Pasrur": (74.663, 32.262),
    "Narowal": (74.873, 32.102),
}

browse = Path(sys.argv[1])
prefix = sys.argv[2]
out = Path(sys.argv[3])
lon0, lat0, lon1, lat1 = map(float, sys.argv[4:8])
dates = sys.argv[8:]
index = json.loads((browse / "index.json").read_text())


def fit(img_arr, poly):
    valid = img_arr.sum(axis=2) > 0
    ys, xs = np.nonzero(valid)
    pts = {
        "left": (xs.min(), ys[xs.argmin()]),
        "right": (xs.max(), ys[xs.argmax()]),
        "top": (xs[ys.argmin()], ys.min()),
        "bottom": (xs[ys.argmax()], ys.max()),
    }
    p = np.array(poly[:-1])
    verts = {
        "left": p[p[:, 0].argmin()],
        "right": p[p[:, 0].argmax()],
        "top": p[p[:, 1].argmax()],
        "bottom": p[p[:, 1].argmin()],
    }
    lons = np.array([verts[k][0] for k in pts])
    lats = np.array([verts[k][1] for k in pts])
    px = np.array([pts[k][0] for k in pts], float)
    py = np.array([pts[k][1] for k in pts], float)
    a, b = np.polyfit(lons, px, 1)
    c, d = np.polyfit(lats, py, 1)
    res_x = px - (a * lons + b)
    res_y = py - (c * lats + d)
    return (a, b, c, d), np.abs(np.concatenate([res_x, res_y])).max()


tiles = []
for dt in dates:
    key = f"{prefix}_{dt}"
    im = Image.open(browse / f"{key}_latlon.png").convert("RGB")
    arr = np.asarray(im)
    (a, b, c, d), maxres = fit(arr, index[key]["poly"])
    print(f"{key}: deg/px lon={1/a:.5f} lat={-1/c:.5f}  max corner residual={maxres:.1f}px")
    x0, x1 = sorted([a * lon0 + b, a * lon1 + b])
    y0, y1 = sorted([c * lat0 + d, c * lat1 + d])
    crop = im.crop((int(x0), int(y0), int(x1), int(y1)))
    scale = 2
    crop = crop.resize((crop.width * scale, crop.height * scale), Image.NEAREST)
    dr = ImageDraw.Draw(crop)
    for name, (lo, la) in TOWNS.items():
        if lon0 <= lo <= lon1 and lat0 <= la <= lat1:
            cx = (a * lo + b - int(x0)) * scale
            cy = (c * la + d - int(y0)) * scale
            dr.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), outline=(255, 255, 0), width=2)
            dr.text((cx + 6, cy - 6), name, fill=(255, 255, 0))
    dr.rectangle((0, 0, 90, 16), fill=(0, 0, 0))
    dr.text((4, 2), dt, fill=(255, 255, 255))
    tiles.append(crop)

gap = 8
w = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
h = max(t.height for t in tiles)
canvas = Image.new("RGB", (w, h), (255, 255, 255))
x = 0
for t in tiles:
    canvas.paste(t, (x, 0))
    x += t.width + gap
canvas.save(out)
print("saved", out, canvas.size)
