"""Test how the GUNW ionospherePhaseScreen affects the Quetta result (cached subsets only, no downloads).
Variants applied per pair BEFORE referencing/plane removal: none, subtract (as the pipeline's --iono), add (flipped sign),
scaled subtract (x0.5, x2), subtract a low-pass (Gaussian) version of the screen, and the screen alone (cumulated).
usage: iono_test.py <pipeline_scripts_dir> <track> <frame> <s1_unw.tif> <s1_cc.tif> <out.json>
(run with the venv that has numpy+scipy+tifffile, e.g. s1_check venv; -I)"""
import argparse, json, sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np
from scipy.ndimage import gaussian_filter
import nisar_quetta as nq, nlib

track, frame = int(sys.argv[2]), int(sys.argv[3])
s1 = nlib.load_s1(sys.argv[4], sys.argv[5])
a = argparse.Namespace(offline=True, search_start="2025-10-01", search_end="2026-11-14",
                       geojson=str(nq.DATA_DIR / "asf" / "quetta_gunw.geojson"), track=track, frame=frame,
                       start="2026-06-01", end="2026-12-31", max_pairs=0, pol=None)
chain = nq.get_chain(a)
subs = [dict(np.load(nq.cache_path(p, None, nq.AOI))) for p in chain]  # cache only (no network, no h5py)
cfg = argparse.Namespace(coh_min=0.3, iono=True, plane=True, use_mask=(len(sys.argv) < 8), ref_center=nq.REF_CENTER, ref_half=0.02,
                         min_ref_pixels=20, phase_sign=1.0, win_px=1)


def run(transform, label, iono_only=False):
    ss = []
    for s in subs:
        s = dict(s)
        io = s["iono"].astype(np.float64)
        if iono_only:                       # the screen alone, treated like an interferogram
            s["unw"] = io.astype(np.float32)
        else:
            s["iono"] = transform(io).astype(np.float32)
        ss.append(s)
    res = nq.process_chain(chain, ss, cfg, log=lambda *x: None)
    tr = dict(cum=res["cum_cm"].astype(float), lon=res["LON"], lat=res["LAT"], t=np.array([(d - res["dates"][0]).days for d in res["dates"]]) / 365.25)
    fv = nlib.fit_velocity(tr["cum"], tr["t"])
    rs = nlib.smooth(fv["v"])
    g = nlib.s1_on_grid(s1, tr["lon"], tr["lat"])
    m = nlib.metrics(rs, tr["lon"], tr["lat"], g)
    bowl = nlib.box(tr["lon"], tr["lat"], nlib.VALLEY) & (g < -5)
    m["label"] = label
    m["rate_median_in_s1_bowl_all_px"] = float(np.nanmedian(rs[bowl]))
    return m


zero = lambda io: np.zeros_like(io)
variants = [
    ("none (no iono correction)", zero),
    ("subtract screen (x +1)", lambda io: io),
    ("add screen (x -1)", lambda io: -io),
    ("subtract 0.5 x screen", lambda io: 0.5 * io),
    ("subtract 2 x screen", lambda io: 2.0 * io),
    ("subtract Gaussian low-pass sigma 60 px (~4.8 km)", lambda io: gaussian_filter(io, 60, mode="nearest")),
    ("subtract Gaussian low-pass sigma 150 px (~12 km)", lambda io: gaussian_filter(io, 150, mode="nearest")),
]
out = []
for lab, f in variants:
    m = run(f, lab)
    out.append(m)
    print(f"{lab:52s} r={m['r']:.2f} bowl={m['bowl_median']:+.1f} calm={m['calm_median']:+.1f} "
          f"sigma_outside={m['outside_robust_sigma']:.2f} frac<-3={m['outside_frac_below_m3']:.2f}", flush=True)
m = run(None, "screen alone (cumulated, same processing)", iono_only=True)
out.append(m)
print(f"{m['label']:52s} r={m['r']:.2f} bowl={m['bowl_median']:+.1f} calm={m['calm_median']:+.1f}  (rate of the iono screen itself)")
json.dump(dict(track=track, frame=frame, variants=out), open(sys.argv[6], "w"), indent=1)
