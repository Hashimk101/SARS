# usage: analyze.py OUTPNG label:unw.tif:cc.tif:YYYYMMDD:YYYYMMDD ...  (panels)
import sys, tifffile, numpy as np, datetime as dt
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter
LON0,LAT0,D=64.774169921875,32.01583480834961,0.001
WL=0.05546576
BOX=(66.75,67.25,29.95,30.45)
CITY=(66.99,30.18); REFS={'REF1 66.80E 30.25N':(66.80,30.25),'REF2 67.15E 30.20N':(67.15,30.20)}
def rc(lon,lat): return int(round((LAT0-lat)/D-0.5)), int(round((lon-LON0)/D-0.5))
def crop(f):
    a=tifffile.imread(f); r0,c0=rc(BOX[0],BOX[3]); r1,c1=rc(BOX[1],BOX[2]); return a[r0:r1,c0:c1].astype(float),r0,c0
def win(x,lon,lat,r0,c0,h=10):  # median in (2h+1)^2 px window (~2 km)
    r,c=rc(lon,lat); r-=r0; c-=c0; w=x[r-h:r+h+1,c-h:c+h+1]; return np.nanmedian(w), np.nanstd(w), np.isfinite(w).mean()
out=sys.argv[1]; items=[a.split(':') for a in sys.argv[2:]]
fig,axs=plt.subplots(1,len(items),figsize=(6.2*len(items),5.6),squeeze=False); axs=axs[0]
res=[]
for ax,(lab,fu,fc,d1,d2) in zip(axs,items):
    u,r0,c0=crop(fu); cc,_,_=crop(fc)
    u[(u==0)|(cc<50)]=np.nan      # cc stored 0-255 (coherence*255); mask <~0.2
    disp=-u*WL/(4*np.pi)*100      # cm; +ve = toward satellite (uplift), -ve = away (subsidence)
    ndays=(dt.datetime.strptime(d2,'%Y%m%d')-dt.datetime.strptime(d1,'%Y%m%d')).days
    refv={k:win(disp,*v,r0,c0) for k,v in REFS.items()}
    ref=refv['REF1 66.80E 30.25N'][0]
    disp-=ref
    rate=disp*365.25/ndays
    sm=uniform_filter(np.where(np.isfinite(rate),rate,0),11)/np.maximum(uniform_filter(np.isfinite(rate).astype(float),11),1e-3)
    ok=uniform_filter(np.isfinite(rate).astype(float),11)>0.7
    sm[~ok]=np.nan
    i=np.nanargmin(sm); r,c=np.unravel_index(i,sm.shape)
    lon=LON0+(c+c0+0.5)*D; lat=LAT0-(r+r0+0.5)*D
    cy=win(rate,*CITY,r0,c0); r2=win(rate,*REFS['REF2 67.15E 30.20N'],r0,c0)
    print(f'== {lab} {d1}-{d2} ({ndays} d)')
    print(f'  ref1 raw median disp {refv["REF1 66.80E 30.25N"][0]:.2f} cm (std {refv["REF1 66.80E 30.25N"][1]:.2f}); ref2 raw {refv["REF2 67.15E 30.20N"][0]:.2f} cm (std {refv["REF2 67.15E 30.20N"][1]:.2f}); ref2 rate after ref1 = {r2[0]:.2f} cm/yr')
    print(f'  max subsidence (1.1km-smoothed) rate {sm[r,c]:.2f} cm/yr LOS (cum {sm[r,c]*ndays/365.25:.2f} cm) at {lon:.4f}E {lat:.4f}N; unsmoothed min cum {np.nanmin(disp):.2f} cm')
    print(f'  city centre rate {cy[0]:.2f} cm/yr (2km median; std {cy[1]:.2f}; valid {cy[2]*100:.0f}%)')
    print(f'  fraction valid px {np.isfinite(rate).mean():.2f}')
    e=[BOX[0],BOX[1],BOX[2],BOX[3]]
    v=np.nanpercentile(np.abs(disp),99.5)
    im=ax.imshow(disp,cmap='RdBu',vmin=-v,vmax=v,extent=e,interpolation='nearest')
    ax.plot(*CITY,'k*',ms=12,mfc='yellow'); ax.annotate('Quetta',CITY,xytext=(CITY[0]+0.02,CITY[1]-0.05),fontsize=10,weight='bold',bbox=dict(fc='w',alpha=.7,pad=1))
    for k,p in REFS.items(): ax.plot(*p,'ks',ms=6,mfc='lime'); 
    ax.plot(lon,lat,'kx',ms=8,mew=2)
    ax.set_title(f'{lab}\n{d1}-{d2} ({ndays} d): cum. LOS disp.\n(+ toward sat., - away/subsidence); ref = green sq. W',fontsize=8)
    ax.set_xlabel('Lon E'); ax.set_ylabel('Lat N'); cb=plt.colorbar(im,ax=ax,shrink=.8); cb.set_label('LOS displacement (cm)')
plt.tight_layout(); plt.savefig(out,dpi=130)
