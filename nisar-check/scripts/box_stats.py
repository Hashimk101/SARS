"""Per-date HH/HV brightness in named boxes, from the mosaicked browse quicklooks.

usage: box_stats.py <browse_dir> <date1> [date2 ...]
"""
import sys
from pathlib import Path

import numpy as np

sys.argv = [sys.argv[0], sys.argv[1], "unused.png", "x", "x", "x", "x"] + sys.argv[2:]
# reuse mosaic + fit from change_map without running its main block
src = (Path(__file__).parent / "change_map.py").read_text().split("dates = sorted(")[0]
src = src.replace("ctrl_a, ctrl_b, ev_a, ev_b = sys.argv[3:7]", "")
ns = {"__file__": __file__}
exec(compile(src, "change_map_head", "exec"), ns)

dates = sys.argv[7:]
LON, LAT, mosaic = ns["LON"], ns["LAT"], ns["mosaic"]

BOXES = {
    "Aik/Deg belt (Sialkot-Pasrur, east)": (74.58, 32.00, 74.78, 32.55),
    "  same latitudes, 15 km further west": (74.40, 32.00, 74.55, 32.55),
    "East of Muridke (GT Road)": (74.28, 31.72, 74.45, 31.86),
    "West of Gujranwala (control)": (73.85, 32.05, 74.05, 32.25),
}
mos = {d: mosaic(d) for d in dates}
print(f"{'box':40s} " + " ".join(f"{d:>9s}" for d in dates) + "   (mean HH 0-255; % pixels HH<60)")
for name, (lo0, la0, lo1, la1) in BOXES.items():
    m = (LON >= lo0) & (LON <= lo1) & (LAT >= la0) & (LAT <= la1)
    cells = []
    for d in dates:
        hh, ok = mos[d]
        v = hh[m & ok]
        cells.append(f"{v.mean():5.0f}/{(v < 60).mean()*100:3.0f}%")
    print(f"{name:40s} " + " ".join(f"{c:>9s}" for c in cells))
