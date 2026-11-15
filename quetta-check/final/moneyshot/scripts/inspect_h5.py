import sys,json,time,earthaccess,h5py
rows=json.load(open(sys.argv[1]))
key=sys.argv[2]
r=[x for x in rows if key in x[3]][0]
earthaccess.login(strategy="netrc")
t=time.time()
f=earthaccess.open([r[4]],open_kwargs={"block_size":8*2**20})[0]
print("opened",time.time()-t)
with h5py.File(f,"r") as h:
    def v(n,o):
        if isinstance(o,h5py.Dataset):
            if "/grids/" in n or "identification" in n:
                print("D",n,o.shape,o.dtype,o.chunks,o.compression)
        elif "/grids/" in n: print("G",n)
    h.visititems(v)
    g="/science/LSAR/GSLC/grids/frequencyA"
    for k in ("listOfPolarizations","centerFrequency","xCoordinateSpacing","yCoordinateSpacing"):
        if g+"/"+k in h: print(k,h[g+"/"+k][()])
    p=h[g+"/projection"]; print("proj",p[()],dict(p.attrs))
    x=h[g+"/xCoordinates"][()];y=h[g+"/yCoordinates"][()]
    print("x",x[0],x[-1],len(x),"y",y[0],y[-1],len(y))
    for n in ("productVersion","processingCenter","orbitPassDirection","trackNumber","frameNumber"):
        for pth in ("/science/LSAR/identification/"+n,):
            if pth in h: print(n,h[pth][()])
    # descriptions
    for n in ("HH",):
        d=h[g+"/"+n]; print({k:d.attrs[k] for k in d.attrs})
    print("time",time.time()-t)
