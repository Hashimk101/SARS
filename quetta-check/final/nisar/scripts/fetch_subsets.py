"""Parallel helper: stream AOI subsets for some pairs of a track's chain into the pipeline cache (same cache-first
get_subset as `nisar_quetta.py run`). Run several workers per track, then run the normal `run` command (all cache hits).
usage: fetch_subsets.py <pipeline_scripts_dir> <track> <frame> <worker_id> <n_workers>"""
import argparse, sys, time
sys.path.insert(0, sys.argv[1])
import nisar_quetta as nq
track, frame, wid, nw = map(int, sys.argv[2:6])
a = argparse.Namespace(offline=False, search_start="2025-10-01", search_end="2026-11-14",
                       geojson=str(nq.DATA_DIR / "asf" / "quetta_gunw.geojson"), track=track, frame=frame,
                       start="2026-06-01", end="2026-12-31", max_pairs=0, pol=None)
chain = nq.get_chain(a)
session = {}
for i, p in enumerate(chain):
    if i % nw != wid:
        continue
    for attempt in range(3):
        try:
            nq.get_subset(p, a, session); break
        except Exception as e:
            print("retry", i, type(e).__name__, flush=True); time.sleep(5)
print("worker done", wid, flush=True)
