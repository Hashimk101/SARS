import sys,glob,os
from matplotlib.path import Path
d=sys.argv[1]; pt=(66.99,30.18)
for f in sorted(glob.glob(d+'/*.txt')):
    try:
        pts=[tuple(map(float,l.split()[:2])) for l in open(f) if l.strip()]
        if len(pts)>=3 and Path(pts).contains_point(pt): print(os.path.basename(f)[:-4])
    except Exception as e: pass
