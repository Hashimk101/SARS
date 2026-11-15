"""Print the group tree (groups + datasets with shapes) of one remote GUNW file below a path, to depth N.
usage: probe_tree.py <pipeline_scripts_dir> <url> <path> <depth>"""
import sys
sys.path.insert(0, sys.argv[1])
import h5py, nisar_quetta as nq
ea, _ = nq.earthdata_login()
f = nq.open_remote(ea, sys.argv[2])
base, depth = sys.argv[3], int(sys.argv[4])
with h5py.File(f, "r") as h:
    def rec(g, p, d):
        for k in g.keys():
            o = g[k]
            if isinstance(o, h5py.Dataset):
                print(f"D {p}/{k} {o.shape} {o.dtype}")
            else:
                print(f"G {p}/{k}")
                if d < depth: rec(o, f"{p}/{k}", d + 1)
    rec(h[base], base, 1)
