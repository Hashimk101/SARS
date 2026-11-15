import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
L=7*np.pi; K=23.84/(4*np.pi)
tag,out=sys.argv[1],sys.argv[2]
P=np.load(f"{out}/{tag}_pairs_rad.npy"); g=np.load(f"{out}/{tag}_grid.npz")
lon,lat=g["lon"],g["lat"]
wr=lambda x:(x+L/2)%L-L/2
for i,p in enumerate(P):
    f=p[np.isfinite(p)]
    print(i,"std %.2f rad"%f.std(),"p5/p95 %.1f %.1f"%tuple(np.percentile(f,[5,95])),"frac|x|>9: %.2f"%(np.abs(f)>9).mean())
S=np.nansum(P,0); S[np.isnan(P).any(0)]=np.nan
T=wr(S)
print("total (wrapped) std %.2f rad = %.1f cm"%(np.nanstd(T),np.nanstd(T)*K), "p5,p95",np.nanpercentile(T,[5,95])*K)
fig,ax=plt.subplots(1,2,figsize=(12,5))
ext=[lon[0],lon[-1],lat[-1],lat[0]]
im=ax[0].imshow(S*K,extent=ext,cmap="RdBu_r",vmin=-40,vmax=40);ax[0].set_title("sum of wrapped (cm)");plt.colorbar(im,ax=ax[0])
im=ax[1].imshow(T*K,extent=ext,cmap="RdBu_r",vmin=-20,vmax=20);ax[1].set_title("wrapped total (cm)");plt.colorbar(im,ax=ax[1])
for a in ax:a.plot(66.99,30.19,"k+")
fig.savefig(f"{out}/{tag}_explore.png",dpi=70)
