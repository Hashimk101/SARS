"""Fetch the AOI window of Copernicus DEM GLO-30 (public AWS bucket, no login) using HTTP range requests on the
cloud-optimised GeoTIFF tiles (only the needed internal tiles are downloaded), mosaic, save as npz.
usage: dem_prep.py <out_npz> [lon0 lon1 lat0 lat1]    (default 66.70 67.30 29.90 30.50)
Needs numpy + tifffile + imagecodecs (the s1_check venv)."""
import io, sys, math, urllib.request
import numpy as np, tifffile
out = sys.argv[1]
lon0, lon1, lat0, lat1 = (map(float, sys.argv[2:6]) if len(sys.argv) >= 6 else (66.70, 67.30, 29.90, 30.50))
BASE = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{n}_DEM/Copernicus_DSM_COG_10_{n}_DEM.tif"


class RangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url, self.pos = url, 0
        for k in range(8):
            try:
                r = urllib.request.urlopen(urllib.request.Request(url, headers={"Range": "bytes=0-0"}), timeout=60)
                self.size = int(r.headers["Content-Range"].split("/")[1]); r.read(); break
            except Exception:
                if k == 7: raise
                import time; time.sleep(5)
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off); return self.pos
    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0: return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        for k in range(6):
            try:
                d = urllib.request.urlopen(req, timeout=120).read(); break
            except Exception:
                if k == 5: raise
                import time; time.sleep(3)
        self.pos += len(d); return d
    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)


res = 1 / 3600.0
nx, ny = int(round((lon1 - lon0) / res)), int(round((lat1 - lat0) / res))
dem = np.full((ny, nx), np.nan, np.float32)
lons = lon0 + (np.arange(nx) + 0.5) * res
lats = lat1 - (np.arange(ny) + 0.5) * res          # north-up
for tl in range(math.floor(lat0), math.floor(lat1 - 1e-9) + 1):
    for tn in range(math.floor(lon0), math.floor(lon1 - 1e-9) + 1):
        name = f"{'N' if tl >= 0 else 'S'}{abs(tl):02d}_00_{'E' if tn >= 0 else 'W'}{abs(tn):03d}_00"
        url = BASE.format(n=name)
        try:
            fh = RangeFile(url)
        except Exception as e:
            print("tile missing", name, e); continue
        with tifffile.TiffFile(fh) as tf:
            pg = tf.pages[0]
            H, W = pg.shape[:2]; tw, th = pg.tilewidth, pg.tilelength
            pxres = 1.0 / W
            # tile covers lon tn..tn+1, lat tl..tl+1 (north-up, origin upper-left = (tn, tl+1))
            c0 = max(int(math.floor((lon0 - tn) * W)), 0); c1 = min(int(math.ceil((lon1 - tn) * W)), W)
            r0 = max(int(math.floor((tl + 1 - lat1) * H)), 0); r1 = min(int(math.ceil((tl + 1 - lat0) * H)), H)
            print(name, "size", fh.size, "shape", pg.shape, "window rows", r0, r1, "cols", c0, c1, flush=True)
            nTx = (W + tw - 1) // tw
            win = np.full((r1 - r0, c1 - c0), np.nan, np.float32)
            for ty in range(r0 // th, (r1 - 1) // th + 1):
                for tx in range(c0 // tw, (c1 - 1) // tw + 1):
                    idx = ty * nTx + tx
                    fh.seek(pg.dataoffsets[idx]); data = fh.read(pg.databytecounts[idx])
                    seg, ind, shp = pg.decode(data, idx, jpegtables=pg.jpegtables)
                    y0_, x0_ = ind[-3], ind[-2]; shp = (1,) + tuple(shp[-3:-1])  # (_, h, w)
                    seg = np.asarray(seg).reshape(shp[1], shp[2])
                    ya, yb = max(y0_, r0), min(y0_ + shp[1], r1); xa, xb = max(x0_, c0), min(x0_ + shp[2], c1)
                    win[ya - r0:yb - r0, xa - c0:xb - c0] = seg[ya - y0_:yb - y0_, xa - x0_:xb - x0_]
        # place window in output grid (same 1/3600 deg lattice)
        oy = int(round((lat1 - (tl + 1 - r0 * pxres)) / res)); ox = int(round((tn + c0 * pxres - lon0) / res))
        ya, xa = max(oy, 0), max(ox, 0)
        yb, xb = min(oy + win.shape[0], ny), min(ox + win.shape[1], nx)
        dem[ya:yb, xa:xb] = win[ya - oy:yb - oy, xa - ox:xb - ox]
print("DEM min/max/nan frac", np.nanmin(dem), np.nanmax(dem), float(np.isnan(dem).mean()))
np.savez_compressed(out, dem=dem, lon=lons, lat=lats, source="Copernicus GLO-30 DSM COG (AWS open data)")
