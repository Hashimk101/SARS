"""ifg = s1 * conj(s2), s1 = EARLIER (reference) date, s2 = LATER. Multilook NxN boxcar, coherence, Goldstein.
usage: make_ifg.py data/early data/late out.npz [looks=12]
Convention: phase = phi1 - phi2. With SAR phase = -4*pi*R/lambda, positive phase => R increased
(ground moved AWAY from satellite, i.e. subsidence for mostly-vertical motion)."""
import sys,json,numpy as np
p1,p2,out=sys.argv[1:4]; L=int(sys.argv[4]) if len(sys.argv)>4 else 12
m1=json.load(open(p1+".json")); m2=json.load(open(p2+".json"))
for k in ("x","y","dx","dy","shape","epsg"): assert m1[k]==m2[k],("grid mismatch",k,m1[k],m2[k])
def mm(p,m):
    # npy header may contain np.int64(...) (written with numpy2 + numpy-int shape): open raw
    with open(p+".npy","rb") as fh:
        fh.read(8); hl=int.from_bytes(fh.read(2),"little"); off=10+hl
    return np.memmap(p+".npy",dtype=np.complex64,mode="r",offset=off,shape=tuple(m["shape"]))
a=mm(p1,m1); b=mm(p2,m2)
R,C=a.shape; R2,C2=R//L,C//L
num=np.zeros((R2,C2),np.complex64); p_a=np.zeros((R2,C2),np.float32); p_b=np.zeros((R2,C2),np.float32); nvalid=np.zeros((R2,C2),np.float32)

# ---- coregistration: estimate (dr,dc) of s2 relative to s1 by amplitude cross-correlation on patches, fit affine model
def fshift(z,dr,dc):
    Rr,Cc=z.shape; fr=np.fft.fftfreq(Rr)[:,None]; fc=np.fft.fftfreq(Cc)[None,:]
    return np.fft.ifft2(np.fft.fft2(z)*np.exp(-2j*np.pi*(fr*dr+fc*dc)))
def est(x,y):
    ax=np.abs(x)-np.abs(x).mean(); ay=np.abs(y)-np.abs(y).mean()
    cc=np.fft.ifft2(np.fft.fft2(ax)*np.conj(np.fft.fft2(ay))).real
    i,j=np.unravel_index(np.argmax(cc),cc.shape); Rr,Cc=cc.shape
    par=lambda m,p,n:0.5*(m-n)/(m-2*p+n)
    di=par(cc[(i-1)%Rr,j],cc[i,j],cc[(i+1)%Rr,j]); dj=par(cc[i,(j-1)%Cc],cc[i,j],cc[i,(j+1)%Cc])
    pk=cc[i,j]/(np.sqrt((ax**2).sum()*(ay**2).sum())+1e-9)
    return (i+di+Rr/2)%Rr-Rr/2,(j+dj+Cc/2)%Cc-Cc/2,pk
P=[];N=512
rs=list(range(0,R-N+1,N)); cs_=list(range(0,C-N+1,N))
OR=np.zeros((len(rs),len(cs_)));OC=np.zeros_like(OR);PK=np.zeros_like(OR)
for ii,r0 in enumerate(rs):
    for jj,c0 in enumerate(cs_):
        x=np.nan_to_num(np.array(a[r0:r0+N,c0:c0+N])); y=np.nan_to_num(np.array(b[r0:r0+N,c0:c0+N]))
        OR[ii,jj],OC[ii,jj],PK[ii,jj]=est(x,y)
# robust: reject low-peak or outlier patches (|off - median|>1.5px), fill with median of neighbours, then 3x3 median smoothing
def medfill(Z,bad):
    Z=Z.copy(); Z[bad]=np.nan; out=Z.copy()
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            nb=Z[max(i-1,0):i+2,max(j-1,0):j+2]
            out[i,j]=np.nanmedian(nb) if np.isfinite(nb).any() else np.nanmedian(Z)
    return out
bad=(PK<np.percentile(PK,20))|(abs(OR-np.median(OR))>2)|(abs(OC-np.median(OC))>3)
ORs=medfill(OR,bad); OCs=medfill(OC,bad)
print("patch offsets rows: median",np.median(OR),"cols median",np.median(OC),"n bad",bad.sum(),"of",bad.size)
pr=np.array(rs)+N/2; pc=np.array(cs_)+N/2
def interp(Z,rc,ccn):
    i=np.clip(np.interp(rc,pr,np.arange(len(pr))),0,len(pr)-1); j=np.clip(np.interp(ccn,pc,np.arange(len(pc))),0,len(pc)-1)
    i0=int(min(i,len(pr)-2)); j0=int(min(j,len(pc)-2)); fi=i-i0; fj=j-j0
    return (Z[i0,j0]*(1-fi)*(1-fj)+Z[i0+1,j0]*fi*(1-fj)+Z[i0,j0+1]*(1-fi)*fj+Z[i0+1,j0+1]*fi*fj)
offs=dict(patch=N,median_row_px=float(np.median(OR)),median_col_px=float(np.median(OC)),n_bad=int(bad.sum()),n=int(bad.size))
pad=24; B=240; B=(B//L)*L
num=np.zeros((R2,C2),np.complex64); p_a=np.zeros((R2,C2),np.float32); p_b=np.zeros((R2,C2),np.float32); nvalid=np.zeros((R2,C2),np.float32)
f=lambda z:z.reshape(z.shape[0]//L,L,z.shape[1]//L,L).sum((1,3))
for r in range(0,R2*L,B):
    for c in range(0,C2*L,B):
        Br=min(B,R2*L-r); Bc=min(B,C2*L-c)
        ra,rb=max(r-pad,0),min(r+B+pad,R); ca,cb=max(c-pad,0),min(c+B+pad,C)
        x=np.nan_to_num(np.array(a[ra:rb,ca:cb])); y=np.nan_to_num(np.array(b[ra:rb,ca:cb]))
        rc,ccn=r+Br/2,c+Bc/2
        dr=interp(ORs,rc,ccn); dc=interp(OCs,rc,ccn)
        ys=fshift(y,dr,dc)[r-ra:r-ra+Br,c-ca:c-ca+Bc]; xs=x[r-ra:r-ra+Br,c-ca:c-ca+Bc]
        ok=(xs!=0)&(ys!=0)
        rr=slice(r//L,(r+Br)//L); cs=slice(c//L,(c+Bc)//L)
        num[rr,cs]=f(xs*np.conj(ys)); p_a[rr,cs]=f(np.abs(xs)**2); p_b[rr,cs]=f(np.abs(ys)**2); nvalid[rr,cs]=f(ok.astype(np.float32))
coh=np.abs(num)/np.sqrt(np.maximum(p_a*p_b,1e-20)); coh[nvalid<0.5*L*L]=np.nan
ifg=num/np.maximum(nvalid,1)
def goldstein(z,coh,alpha=0.6,w=32,step=8):
    z=np.nan_to_num(z); H,W=z.shape; outz=np.zeros_like(z); wt=np.zeros(z.shape,np.float32)
    win=np.outer(np.hanning(w+2)[1:-1],np.hanning(w+2)[1:-1]).astype(np.float32)
    for r in range(0,H-w+1,step):
        for c in range(0,W-w+1,step):
            blk=z[r:r+w,c:c+w]
            if not np.any(blk): continue
            F=np.fft.fft2(blk*win); S=np.abs(F)
            from numpy import fft
            k=np.ones((3,3))/9; Sp=np.real(fft.ifft2(fft.fft2(S)*fft.fft2(k,s=S.shape)))  # 3x3 smoothing
            G=np.fft.ifft2(F*(Sp/ (Sp.max()+1e-12))**alpha)
            outz[r:r+w,c:c+w]+=G*win; wt[r:r+w,c:c+w]+=win**2
    return outz/np.maximum(wt,1e-6)
ifg_f=goldstein(ifg,coh)
# keep amplitude of filtered, phase from filtered
meta=dict(m1=m1,m2=m2,looks=L,coreg=offs)
np.savez_compressed(out,ifg=ifg.astype(np.complex64),ifg_f=ifg_f.astype(np.complex64),coh=coh.astype(np.float32),
    x0=m1["x"][0]+(L-1)/2*m1["dx"],y0=m1["y"][0]+(L-1)/2*m1["dy"],dx=m1["dx"]*L,dy=m1["dy"]*L,epsg=m1["epsg"],meta=json.dumps(meta))
print("coh median",np.nanmedian(coh),"mean",np.nanmean(coh),ifg.shape)
