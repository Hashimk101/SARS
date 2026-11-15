import sys,numpy as np
from PIL import Image
import matplotlib
a=np.asarray(Image.open(sys.argv[1]))
print(a.shape,a.dtype)
v=a[...,3]>0
print("alpha values",np.unique(a[...,3])[:10], "valid frac",v.mean())
rgb=a[v][:,:3].astype(int)
u,c=np.unique(rgb,axis=0,return_counts=True)
print("unique colors",len(u))
for name in ("twilight_shifted","twilight"):
    lut=(matplotlib.colormaps[name](np.arange(256))[:,:3]*255).round().astype(int)
    d=np.abs(u[:,None,:]-lut[None]).sum(2)
    best=d.min(1)
    print(name,"exact-match frac of pixels",(c[best==0].sum()/c.sum()),"max dist",best.max(),"mean",(best*c).sum()/c.sum())
    idx=d.argmin(1)
    h=np.bincount(np.repeat(idx,c),minlength=256)
    print(" idx hist (16 bins)",np.add.reduceat(h,np.arange(0,256,16)))
# non-lut colors (nodata?)
print("most common colors",u[np.argsort(-c)[:5]],np.sort(c)[::-1][:5])
