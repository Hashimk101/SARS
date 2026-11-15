"""Stream the small radarGrid geometry cubes (LOS unit vector, incidence, elevation angle, height layers, tropo/tide
phase screens) and layer attributes from the FIRST GUNW file of a track's chain, subset to the AOI. Needs Earthdata login
(earthaccess netrc/env, same as the pipeline).
usage: fetch_geometry.py <pipeline_scripts_dir> <outdir> <track> <frame> [<track> <frame> ...]"""
import json, sys
from pathlib import Path
pipe, outdir = sys.argv[1], Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, pipe)
import numpy as np, h5py, nisar_quetta as nq
import argparse
a = argparse.Namespace(offline=False, search_start="2025-10-01", search_end="2026-11-14", geojson=str(nq.DATA_DIR/"asf"/"quetta_gunw.geojson"))
prods = nq.load_products(a)
ea, _ = nq.earthdata_login()
RG = "/science/LSAR/GUNW/metadata/radarGrid"
IFG = "/science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram/HH"
args = sys.argv[3:]
for t, fr in zip(args[0::2], args[1::2]):
    t, fr = int(t), int(fr)
    chain, _ = nq.select_chain(prods, t, fr)
    p = chain[0]
    print("track", t, p["name"])
    f = nq.open_remote(ea, p["url"])
    with h5py.File(f, "r") as h:
        x, y = h[RG + "/xCoordinates"][()], h[RG + "/yCoordinates"][()]
        epsg = int(h[RG + "/projection"][()])
        sl = nq.aoi_slices(x, y, epsg, nq.AOI, margin=2)
        heights = h[RG + "/heightAboveEllipsoid"][()]
        li = int(np.argmin(np.abs(heights - 1700.0)))   # one layer near the valley floor (LOS vectors vary little with height)
        out = dict(x=x[sl[1]], y=y[sl[0]], epsg=np.int64(epsg), heights=heights, layer=np.int64(li), name=np.str_(p["name"]))
        for k in ("losUnitVectorX", "losUnitVectorY", "incidenceAngle"):
            out[k] = h[RG + "/" + k][(li,) + sl]
            print("   read", k, flush=True)
        np.savez_compressed(outdir / f"geom_track{t:03d}.npz", **out)
        att = {}
        for path in (IFG + "/unwrappedPhase", IFG + "/ionospherePhaseScreen", IFG + "/ionospherePhaseScreenUncertainty",
                     IFG + "/coherenceMagnitude", RG + "/losUnitVectorX", RG + "/wetTroposphericPhaseScreen",
                     RG + "/slantRangeSolidEarthTidesPhase", RG + "/hydrostaticTroposphericPhaseScreen"):
            if path in h:
                att[path] = {k: (v.decode() if isinstance(v, bytes) else (v.tolist() if hasattr(v, "tolist") else str(v)))
                             for k, v in h[path].attrs.items()}
        for gp in ("/science/LSAR/GUNW/metadata/processingInformation/parameters/ionosphere",
                   "/science/LSAR/GUNW/metadata/processingInformation/algorithms/ionosphereEstimation",
                   "/science/LSAR/GUNW/metadata/processingInformation/parameters/unwrappedInterferogram"):
            pass
        for gp in ():
            if gp in h:
                d = {}
                def v(n, o):
                    if isinstance(o, h5py.Dataset) and o.size < 50:
                        x_ = o[()]
                        d[n] = x_.decode() if isinstance(x_, bytes) else (x_.tolist() if hasattr(x_, "tolist") else str(x_))
                h[gp].visititems(v)
                att[gp] = d
        # wavelength / frequencies / look direction
        ident = {}
        for k in ("lookDirection", "orbitPassDirection", "trackNumber", "frameNumber"):
            pth = "/science/LSAR/identification/" + k
            if pth in h:
                x_ = h[pth][()]; ident[k] = x_.decode() if isinstance(x_, bytes) else str(x_)
        att["identification"] = ident
        (outdir / f"attrs_track{t:03d}.json").write_text(json.dumps(att, indent=1, default=str))
    print("  saved; incidence range", float(np.nanmin(out["incidenceAngle"])), float(np.nanmax(out["incidenceAngle"])))
