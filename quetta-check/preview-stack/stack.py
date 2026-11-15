"""Invert NISAR GUNW LATLON browse PNGs (twilight_shifted, rewrapped to [0, REWRAP*pi)) to phase,
resample to a common grid, reference to a stable point, wrap, and sum.
usage: stack.py <datadir> <outdir> <tag> <ref_lon> <ref_lat> name1 name2 ...   (names = <datadir>/<name>.png/.poly, in time order)
"""
import json, sys
from pathlib import Path
import numpy as np, matplotlib
from PIL import Image
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter, binary_erosion

REWRAP = 7.0                 # multiple of pi (nisarqa default; inferred, not verifiable from PNG alone)
L = REWRAP * np.pi
LAM = 0.2384
CM_PER_RAD = LAM / (4 * np.pi) * 100
LON0, LON1, LAT0, LAT1, STEP = 66.75, 67.25, 29.95, 30.45, 0.005
glon = np.arange(LON0, LON1 + 1e-9, STEP); glat = np.arange(LAT1, LAT0 - 1e-9, -STEP)
GX, GY = np.meshgrid(glon, glat)

cm = matplotlib.colormaps["twilight_shifted"]
T = np.linspace(0, 1, 4096)
curve = cm(T)[:, :3] * 255
tree = cKDTree(curve)
DARK = (cm(0.0)[:3] * np.array([255, 255, 255])).round().astype(int)   # fill colour (value 0)

def load(d, n):
    im = np.asarray(Image.open(d / f"{n}.png").convert("RGBA"))
    alpha = im[..., 3] > 0
    rgb = im[..., :3]
    dist, idx = tree.query(rgb.reshape(-1, 3).astype(float))
    t = T[idx].reshape(alpha.shape)
    good = alpha & (dist.reshape(alpha.shape) < 6)
    fill = (np.abs(rgb.astype(int) - DARK).sum(2) <= 1)       # exact value-0 colour = fill/nodata
    good &= ~fill
    good = binary_erosion(good, iterations=2)
    ys, xs = np.nonzero(alpha)
    poly = np.array(json.loads((d / f"{n}.poly").read_text())[:-1])
    verts = [poly[poly[:, 0].argmin()], poly[poly[:, 0].argmax()], poly[poly[:, 1].argmax()], poly[poly[:, 1].argmin()]]
    pts = [(xs.min(), ys[xs.argmin()]), (xs.max(), ys[xs.argmax()]), (xs[ys.argmin()], ys.min()), (xs[ys.argmax()], ys.max())]
    a, b = np.polyfit([v[0] for v in verts], [q[0] for q in pts], 1)
    c, dd = np.polyfit([v[1] for v in verts], [q[1] for q in pts], 1)
    return t, good, (a, b, c, dd), float(dist[alpha.ravel()].mean())

def to_grid(t, good, g):
    a, b, c, dd = g
    z = np.exp(2j * np.pi * t) * good
    k = max(1, int(round(STEP * a)))
    k += (k % 2 == 0)
    zs = uniform_filter(z.real, k) + 1j * uniform_filter(z.imag, k)
    ws = uniform_filter(good.astype(float), k)
    px = np.rint(a * GX + b).astype(int); py = np.rint(c * GY + dd).astype(int)
    ok = (px >= 0) & (px < t.shape[1]) & (py >= 0) & (py < t.shape[0])
    px = np.clip(px, 0, t.shape[1] - 1); py = np.clip(py, 0, t.shape[0] - 1)
    zz = zs[py, px]; ww = ws[py, px]
    ok &= ww > 0.6
    tg = (np.angle(zz) / (2 * np.pi)) % 1.0
    out = np.where(ok, tg * L, np.nan)
    return out, k

def wrapc(x): return (x + L / 2) % L - L / 2

def circ_ref(ph, lon, lat, r=0.02):
    m = (np.abs(GX - lon) <= r) & (np.abs(GY - lat) <= r) & np.isfinite(ph)
    if m.sum() < 3: return np.nan
    return (np.angle(np.exp(2j * np.pi * ph[m] / L).mean()) / (2 * np.pi)) % 1.0 * L

if __name__ == "__main__":
    d = Path(sys.argv[1]); out = Path(sys.argv[2]); tag = sys.argv[3]
    rlon, rlat = float(sys.argv[4]), float(sys.argv[5]); names = sys.argv[6:]
    out.mkdir(exist_ok=True)
    pairs = []
    for n in names:
        t, good, g, md = load(d, n)
        ph, k = to_grid(t, good, g)
        r = circ_ref(ph, rlon, rlat)
        rel = wrapc(ph - r)
        pairs.append(rel)
        print(n, "mean colour->curve dist %.2f" % md, "box", k, "valid grid frac %.2f" % np.isfinite(ph).mean(), "ref phase %.2f" % r)
    P = np.array(pairs)
    np.save(out / f"{tag}_pairs_rad.npy", P)
    np.savez(out / f"{tag}_grid.npz", lon=glon, lat=glat)
    print("saved", P.shape)
