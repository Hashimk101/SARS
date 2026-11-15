"""usage: analyze.py <outdir> tag1 tag2 ...  -> cumulative LOS maps, stats, figure"""
import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
L=7*np.pi; K=23.84/(4*np.pi)   # cm per rad (range change; + = away from satellite for ref=earlier date, ASSUMED)
wr=lambda x:(x+L/2)%L-L/2
out=sys.argv[1]; tags=sys.argv[2:]
QLON,QLAT=66.99,30.19
res={}
fig,axs=plt.subplots(2,len(tags),figsize=(6.2*len(tags),11),squeeze=False)
for j,tag in enumerate(tags):
    P=np.load(f"{out}/{tag}_pairs_rad.npy"); g=np.load(f"{out}/{tag}_grid.npz"); lon,lat=g["lon"],g["lat"]
    GX,GY=np.meshgrid(lon,lat)
    # per-pair valid mask: need all pairs; sum mod L then wrap
    S=np.where(np.isnan(P).any(0),np.nan,wr(P.sum(0)))
    cm_=S*K
    # plane fit outside valley zone (robust: exclude 0.18 deg radius around Quetta)
    r=np.hypot((GX-QLON)*np.cos(np.radians(30.2)),GY-QLAT)
    fitm=np.isfinite(cm_)&(r>0.18)
    A=np.c_[np.ones(fitm.sum()),GX[fitm],GY[fitm]]
    co=np.linalg.lstsq(A,cm_[fitm],rcond=None)[0]
    plane=co[0]+co[1]*GX+co[2]*GY
    D=cm_-plane
    box=(np.abs(GX-QLON)<=0.02)&(np.abs(GY-QLAT)<=0.02)&np.isfinite(D)
    city_raw=np.nanmean(cm_[box]); city=np.nanmean(D[box])
    # noise: std of detrended field outside valley; and distribution of 4x4-cell box means
    out_std=np.nanstd(D[fitm]); 
    # box means over whole scene (9x9 cells box = 0.04deg)
    from scipy.ndimage import uniform_filter
    v=np.isfinite(D); Z=np.where(v,D,0.0)
    bm=uniform_filter(Z,9)/np.maximum(uniform_filter(v.astype(float),9),1e-9); bv=uniform_filter(v.astype(float),9)>0.7
    bm=np.where(bv,bm,np.nan)
    bsd=np.nanstd(bm[fitm]); rank=(bm[fitm]<city).mean()
    # valley extremes within 0.15 deg of Quetta
    near=(r<0.15)&np.isfinite(bm)
    imin=np.nanargmin(np.where(near,bm,np.inf)); imax=np.nanargmax(np.where(near,bm,-np.inf))
    # pair-sum diagnostics
    print(f"== {tag}: n_pairs={len(P)} valid cells {np.isfinite(cm_).mean():.2f}")
    print(f"   city box (0.04deg) cumulative: raw {city_raw:.1f} cm, plane-removed {city:.1f} cm (positive = range increase)")
    print(f"   noise outside valley: pixel std {out_std:.1f} cm; 0.04deg box-mean std {bsd:.1f} cm; city percentile among box means {100*rank:.0f}%")
    print(f"   within 0.15deg: min box-mean {bm.flat[imin]:.1f} cm at lon {GX.flat[imin]:.3f} lat {GY.flat[imin]:.3f}; max {bm.flat[imax]:.1f} cm at lon {GX.flat[imax]:.3f} lat {GY.flat[imax]:.3f}")
    print(f"   scene-wide plane-removed range p2/p98: {np.nanpercentile(D,2):.1f} / {np.nanpercentile(D,98):.1f} cm")
    print(f"   per-pair std (rad): "+" ".join(f"{np.nanstd(p):.1f}" for p in P))
    ext=[lon[0]-.0025,lon[-1]+.0025,lat[-1]-.0025,lat[0]+.0025]
    for i,(M,tt) in enumerate([(cm_,"referenced cumulative, no ramp removal"),(D,"ramp removed (fit outside 0.18 deg of Quetta)")]):
        a=axs[i,j]; im=a.imshow(M,extent=ext,cmap="RdBu_r",vmin=-20,vmax=20)
        a.plot(QLON,QLAT,"k+",ms=12); a.annotate("Quetta",(QLON,QLAT),xytext=(6,6),textcoords="offset points",fontsize=11,weight="bold")
        a.add_patch(plt.Circle((QLON,QLAT),0.18,fill=False,ls="--",lw=.8,ec="k"))
        a.set_title(f"{tag}: {tt}\ncity-box {city_raw if i==0 else city:+.1f} cm; noise(box-mean) {bsd:.1f} cm",fontsize=9)
        a.set_xlabel("lon");a.set_ylabel("lat")
        fig.colorbar(im,ax=a,shrink=.8,label="LOS range change (cm), mod 41.7-cm rewrap; white = no data")
fig.suptitle("NISAR GUNW browse-PNG inversion, cumulative ~108-120 d (Jun-Oct 2026). Expected bowl: +2 to +5 cm (subsidence)",fontsize=11)
fig.tight_layout(); fig.savefig(f"{out}/quetta_cumulative.png",dpi=90)
