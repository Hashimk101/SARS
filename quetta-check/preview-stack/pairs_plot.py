import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
tag, out = sys.argv[1], sys.argv[2]
P = np.load(f"{out}/{tag}_pairs_rad.npy"); g = np.load(f"{out}/{tag}_grid.npz")
ext = [g["lon"][0], g["lon"][-1], g["lat"][-1], g["lat"][0]]
n = len(P); c = 3; r = (n + c - 1) // c
fig, ax = plt.subplots(r, c, figsize=(13, 4 * r))
for i, a in enumerate(ax.flat):
    if i < n:
        im = a.imshow(P[i], extent=ext, cmap="RdBu_r", vmin=-8, vmax=8); a.plot(66.99, 30.19, "k+"); a.set_title(f"pair {i} (rad, ref-wrapped)")
    else: a.axis("off")
fig.colorbar(im, ax=ax, shrink=.5); fig.savefig(f"{out}/{tag}_pairs.png", dpi=70)
