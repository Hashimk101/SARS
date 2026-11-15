"""Does the GUNW ionosphere screen look like the ionospheric part of unwrappedPhase (sign and scale)?
Per pair, on stable ground (outside the valley box, valid pixels): fit  unw = a + b*iono  (b ~ +1 means the screen has
the same sign/scale as the signal in unwrappedPhase, so SUBTRACT is the right operation; b ~ -1 means flipped sign),
once with raw fields and once after removing a best-fit plane from both (so only non-planar structure counts).
usage: iono_regress.py <pipeline_scripts_dir> <track> <frame> <out.json>"""
import argparse, json, sys
sys.path.insert(0, sys.argv[1])
import numpy as np
import nisar_quetta as nq

track, frame = int(sys.argv[2]), int(sys.argv[3])
a = argparse.Namespace(offline=True, search_start="2025-10-01", search_end="2026-11-14",
                       geojson=str(nq.DATA_DIR / "asf" / "quetta_gunw.geojson"), track=track, frame=frame,
                       start="2026-06-01", end="2026-12-31", max_pairs=0, pol=None)
chain = nq.get_chain(a)
rows = []
for p in chain:
    s = dict(np.load(nq.cache_path(p, None, nq.AOI)))
    X, Y = np.meshgrid(s["x"], s["y"])
    LON, LAT = nq.xy_to_lonlat(X, Y, int(s["epsg"]))
    u, io = s["unw"].astype(float), s["iono"].astype(float)
    v = np.isfinite(u) & (s["coh"] >= 0.3) & (s["cc"] > 0) & (s["cc"] != 65535) & ~nq.box_mask(LON, LAT, nq.VALLEY)
    xk, yk = (X - X.mean()) / 1000, (Y - Y.mean()) / 1000
    A = np.column_stack([np.ones(v.sum()), xk[v], yk[v]])
    res = {}
    for name, f in (("unw", u), ("iono", io)):
        c, *_ = np.linalg.lstsq(A, f[v], rcond=None)
        res[name] = f[v] - A @ c
    b_raw = np.polyfit(io[v], u[v], 1)[0]
    b_np = np.polyfit(res["iono"], res["unw"], 1)[0]
    r_np = np.corrcoef(res["iono"], res["unw"])[0, 1]
    rows.append(dict(pair=f"{p['ref_start']:%m%d}->{p['sec_start']:%m%d}", slope_raw=float(b_raw), slope_nonplanar=float(b_np),
                     corr_nonplanar=float(r_np), iono_std_nonplanar=float(res["iono"].std()), unw_std_nonplanar=float(res["unw"].std())))
    print(rows[-1], flush=True)
json.dump(rows, open(sys.argv[4], "w"), indent=1)
