import sys,json,numpy as np
def mm(p):
    m=json.load(open(p+".json"))
    with open(p+".npy","rb") as fh:
        fh.read(8); hl=int.from_bytes(fh.read(2),"little"); off=10+hl
    return np.memmap(p+".npy",dtype=np.complex64,mode="r",offset=off,shape=tuple(m["shape"]))
a=mm("data/t41_20251125"); b=mm("data/t41_20261027")
def fshift(z,dr,dc):
    R,C=z.shape; fr=np.fft.fftfreq(R)[:,None]; fc=np.fft.fftfreq(C)[None,:]
    return np.fft.ifft2(np.fft.fft2(z)*np.exp(-2j*np.pi*(fr*dr+fc*dc)))
def est(x,y,up=20):
    ax=np.abs(x)-np.abs(x).mean(); ay=np.abs(y)-np.abs(y).mean()
    cc=np.fft.ifft2(np.fft.fft2(ax)*np.conj(np.fft.fft2(ay))).real
    i,j=np.unravel_index(np.argmax(cc),cc.shape)
    # sub-pixel by parabola
    def par(m,p,n): return 0.5*(m-n)/(m-2*p+n)
    R,C=cc.shape
    di=par(cc[(i-1)%R,j],cc[i,j],cc[(i+1)%R,j]); dj=par(cc[i,(j-1)%C],cc[i,j],cc[i,(j+1)%C])
    si=(i+di+R/2)%R-R/2; sj=(j+dj+C/2)%C-C/2
    return si,sj  # y ~ x shifted: ay(r) = ax(r+...)?? sign checked empirically
for r0,c0 in [(5000,3700),(2000,1000),(7000,6000)]:
    N=1024
    x=np.array(a[r0:r0+N,c0:c0+N]); y=np.array(b[r0:r0+N,c0:c0+N])
    si,sj=est(x,y); print(r0,c0,"offset est",si,sj)
    for sgn in (1,-1):
        ys=fshift(y,sgn*si,sgn*sj)[16:-16,16:-16]; xs=x[16:-16,16:-16]
        k=8; n=xs.shape[0]//k*k
        f=lambda z:z[:n,:n].reshape(n//k,k,n//k,k).sum((1,3))
        coh=np.abs(f(xs*np.conj(ys)))/np.sqrt(f(abs(xs)**2)*f(abs(ys)**2)); print(" sgn",sgn,"coh",coh.mean())
