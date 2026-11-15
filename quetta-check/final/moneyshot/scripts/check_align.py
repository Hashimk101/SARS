import sys,json,numpy as np
def mm(p):
    m=json.load(open(p+".json"))
    with open(p+".npy","rb") as fh:
        fh.read(8); hl=int.from_bytes(fh.read(2),"little"); off=10+hl
    return np.memmap(p+".npy",dtype=np.complex64,mode="r",offset=off,shape=tuple(m["shape"]))
a=mm(sys.argv[1]); b=mm(sys.argv[2])
r0,c0=int(sys.argv[3]),int(sys.argv[4]); N=1024
A=np.array(a[r0:r0+N+16,c0:c0+N+16]); B=np.array(b[r0:r0+N+16,c0:c0+N+16])
print("finite frac",np.isfinite(A).mean(),np.isfinite(B).mean(),"zero",(A==0).mean())
A=np.nan_to_num(A);B=np.nan_to_num(B)
best=[]
for dr in range(-6,7,1):
  for dc in range(-6,7,1):
    x=A[8:8+N,8:8+N]; y=B[8+dr:8+dr+N,8+dc:8+dc+N]
    # amplitude corr
    ax=np.abs(x);ay=np.abs(y); ca=np.corrcoef(ax.ravel(),ay.ravel())[0,1]
    k=64; i=x*np.conj(y); f=lambda z:z.reshape(-1,k,N//k*0+z.shape[1]//k,k).sum((1,3)) if False else z.reshape(N//8,8,N//8,8).sum((1,3))
    coh=np.abs(f(i))/np.sqrt(f(np.abs(x)**2)*f(np.abs(y)**2)+1e-20)
    best.append((np.mean(coh),ca,dr,dc))
best.sort(reverse=True); print(best[:4]); print([t for t in best if t[2]==0 and t[3]==0])
