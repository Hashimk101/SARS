import sys,matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.image as mi
d=sys.argv[1]
fig,ax=plt.subplots(1,2,figsize=(22,13),dpi=120)
for a,(f,t) in zip(ax,((f"{d}/A_336d_zoom.png","2025-11-25 \u2192 2026-10-27 (336 d, BETA v1.0.2 vs v1.0.20): decorrelated"),(f"{d}/B_132d_zoom.png","2026-06-17 \u2192 2026-10-27 (132 d, v1.0.11 vs v1.0.20): coherent"))):
    a.imshow(mi.imread(f)); a.axis("off"); a.set_title(t,fontsize=15,weight="bold")
plt.tight_layout(); fig.savefig(f"{d}/side_by_side_336d_vs_132d.png")
