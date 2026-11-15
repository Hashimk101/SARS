"""Stream AOI subset of GSLC HH to a .npy (complex64) + .json meta. usage: extract_gslc.py list.json key outprefix"""
import sys,json,time,numpy as np,earthaccess,h5py
from pyproj import Transformer
rows=json.load(open(sys.argv[1])); key=sys.argv[2]; out=sys.argv[3]
r=[x for x in rows if key in x[3]][0]
AOI=dict(lon0=66.80,lon1=67.20,lat0=30.00,lat1=30.40)
earthaccess.login(strategy="netrc")
f=earthaccess.open([r[4]],open_kwargs={"block_size":16*2**20})[0]
g="/science/LSAR/GSLC/grids/frequencyA"
with h5py.File(f,"r") as h:
    x=h[g+"/xCoordinates"][()]; y=h[g+"/yCoordinates"][()]
    epsg=int(h[g+"/projection"][()])
    T=Transformer.from_crs(4326,epsg,always_xy=True)
    lo,la=np.meshgrid(np.linspace(AOI['lon0'],AOI['lon1'],9),np.linspace(AOI['lat0'],AOI['lat1'],9))
    ex,ey=T.transform(lo,la)
    xi=np.where((x>=ex.min())&(x<=ex.max()))[0]; yi=np.where((y>=ey.min())&(y<=ey.max()))[0]
    ds=h[g+"/HH"]; print("HH",ds.shape,ds.chunks,ds.compression,flush=True)
    ch=ds.chunks
    # align to chunks
    c0=(xi[0]//ch[1])*ch[1]; c1=min(((xi[-1]//ch[1])+1)*ch[1],len(x))
    r0=(yi[0]//ch[0])*ch[0]; r1=min(((yi[-1]//ch[0])+1)*ch[0],len(y))
    print("window rows",r0,r1,"cols",c0,c1,flush=True)
    arr=np.lib.format.open_memmap(out+".npy",mode="w+",dtype=np.complex64,shape=(r1-r0,c1-c0))
    t=time.time(); step=ch[0]*2
    for a in range(r0,r1,step):
        b=min(a+step,r1)
        arr[a-r0:b-r0]=ds[a:b,c0:c1]
        print(f"rows {a}-{b} {100*(b-r0)/(r1-r0):.0f}% t={time.time()-t:.0f}s",flush=True)
    arr.flush()
    ver=h["/science/LSAR/identification/productVersion"][()].decode()
    fq=float(h[g+"/centerFrequency"][()])
    json.dump(dict(scene=r[3],date=r[1],x=[float(x[c0]),float(x[c1-1])],y=[float(y[r0]),float(y[r1-1])],dx=float(x[1]-x[0]),dy=float(y[1]-y[0]),epsg=epsg,version=ver,freq=fq,shape=arr.shape),open(out+".json","w"))
print("done",flush=True)
