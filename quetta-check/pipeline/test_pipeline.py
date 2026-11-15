"""Unit tests on synthetic data (no login, no network). Run: python -I -m pytest scripts/test_pipeline.py -q
(-I isolates sys.path, so the tests add scripts/ themselves)."""
import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nisar_quetta as nq  # noqa: E402


def cfg(**kw):
    d = dict(coh_min=0.3, iono=False, plane=False, use_mask=True, ref_center=nq.REF_CENTER, ref_half=0.02,
             min_ref_pixels=20, phase_sign=1.0, win_px=1)
    d.update(kw)
    return argparse.Namespace(**d)


def test_units_and_sign():
    wl = 0.2384
    # one full fringe (2 pi) of +phase = lambda/2 range increase = 11.92 cm AWAY -> -11.92 cm
    assert abs(nq.phase_to_los_cm(2 * np.pi, wl) + wl / 2 * 100) < 1e-9
    assert abs(nq.phase_to_los_cm(2 * np.pi, wl, -1.0) - wl / 2 * 100) < 1e-9


def test_cumulate_telescopes():
    rng = np.random.default_rng(0)
    truth = np.cumsum(rng.normal(size=(5, 4, 4)), axis=0)  # epoch phases
    pairs = [truth[0]] + [truth[i] - truth[i - 1] for i in range(1, 5)]
    cum = nq.cumulate(pairs)
    assert cum.shape == (6, 4, 4)
    assert np.allclose(cum[0], 0) and np.allclose(cum[1:], truth)
    pairs[2] = pairs[2].copy(); pairs[2][0, 0] = np.nan  # NaN propagates to later epochs only
    cum = nq.cumulate(pairs)
    assert np.isfinite(cum[2, 0, 0]) and np.isnan(cum[3:, 0, 0]).all()


def test_utm_roundtrip_and_pyproj():
    lon, lat = np.array([66.75, 66.99, 67.25]), np.array([29.95, 30.18, 30.45])
    x, y = nq.lonlat_to_xy(lon, lat, 32642)
    lo, la = nq.xy_to_lonlat(x, y, 32642)
    assert np.abs(lo - lon).max() < 1e-8 and np.abs(la - lat).max() < 1e-8
    try:
        from pyproj import Transformer
    except ImportError:
        return
    px, py = Transformer.from_crs(4326, 32642, always_xy=True).transform(lon, lat)
    assert np.abs(px - x).max() < 0.05 and np.abs(py - y).max() < 0.05  # < 5 cm


def test_referencing_and_plane_removal():
    chain, subs, truth = nq.synthetic_chain(n_pairs=1, plane=True, noise_rad=0.0)
    s = subs[0]
    X, Y = np.meshgrid(s["x"], s["y"])
    LON, LAT = nq.xy_to_lonlat(X, Y, 32642)
    rb = nq.box_mask(LON, LAT, nq.ref_box_from_center(nq.REF_CENTER, 0.02))
    # without plane: reference box median is 0 after referencing
    ph, _ = nq.prepare_pair(s, X, Y, LON, LAT, cfg(plane=False), rb, nq.VALLEY, lambda *a: None)
    assert abs(np.nanmedian(ph[rb])) < 1e-6
    # with plane removal, residual vs. truth is small (bowl tail is ~0 at the plane-fit area)
    ph2, _ = nq.prepare_pair(s, X, Y, LON, LAT, cfg(plane=True), rb, nq.VALLEY, lambda *a: None)
    cm = nq.phase_to_los_cm(ph2)
    err = np.nanmedian(np.abs(cm - truth))
    assert err < 0.15, err
    ph_np = nq.phase_to_los_cm(ph)
    assert np.nanmedian(np.abs(ph_np - truth)) > 3 * err  # the ramp really was there and plane removal helps


def test_gaussian_bowl_chain_recovered():
    chain, subs, truth = nq.synthetic_chain(n_pairs=9, rate_cm_yr=14.0, plane=True, noise_rad=0.02)
    res = nq.process_chain(chain, subs, cfg(plane=True), log=lambda *a: None)
    d = res["disp_cm"]
    ok = np.isfinite(d) & np.isfinite(truth)
    assert ok.mean() > 0.9
    assert np.nanmedian(np.abs(d[ok] - truth[ok])) < 0.15
    s = res["summary"]
    expected = -14.0 * res["days"] / 365.25
    assert abs(s["max_sink_cm"] - expected) < 0.25, (s, expected)
    assert abs(s["rate_cm_yr"] + 14.0) < 1.0
    assert abs(s["lon"] - 66.99) < 0.03 and abs(s["lat"] - 30.19) < 0.03
    assert abs(res["series"]["reference"][-1]) < 0.1
    assert res["series"]["city_center"][-1] < -3.0 and res["series"]["city_center"][0] == 0


def test_coherence_and_component_masking():
    chain, subs, _ = nq.synthetic_chain(n_pairs=1, plane=False, noise_rad=0.0)
    s = subs[0]
    s["coh"][100:120, 100:120] = 0.1
    s["cc"][200:220, 200:220] = 2  # a second component, not the reference one
    X, Y = np.meshgrid(s["x"], s["y"])
    LON, LAT = nq.xy_to_lonlat(X, Y, 32642)
    rb = nq.box_mask(LON, LAT, nq.ref_box_from_center(nq.REF_CENTER, 0.02))
    ph, _ = nq.prepare_pair(s, X, Y, LON, LAT, cfg(), rb, nq.VALLEY, lambda *a: None)
    assert np.isnan(ph[100:120, 100:120]).all() and np.isnan(ph[200:220, 200:220]).all()


def test_iono_subtraction():
    chain, subs, _ = nq.synthetic_chain(n_pairs=1, plane=False, noise_rad=0.0)
    s = subs[0]
    X, Y = np.meshgrid(s["x"], s["y"])
    LON, LAT = nq.xy_to_lonlat(X, Y, 32642)
    rb = nq.box_mask(LON, LAT, nq.ref_box_from_center(nq.REF_CENTER, 0.02))
    s["iono"] = np.full_like(s["unw"], 1.0)
    s["iono"] += (X > X.mean()) * 1.0  # step iono; subtracting it must change the result
    a, _ = nq.prepare_pair(s, X, Y, LON, LAT, cfg(iono=False), rb, nq.VALLEY, lambda *a: None)
    b, _ = nq.prepare_pair(s, X, Y, LON, LAT, cfg(iono=True), rb, nq.VALLEY, lambda *a: None)
    east = (LON > 67.1) & np.isfinite(a) & np.isfinite(b)
    assert np.nanmedian((a - b)[east]) > 0.9


def test_selection_dedupe_and_chain():
    gj = nq.json.loads(Path(nq.DATA_DIR / "asf" / "quetta_gunw.geojson").read_text(encoding="utf-8"))
    prods = nq.products_from_geojson(gj)
    dup = dict(prods[0]); prods = prods + [dup, dict(dup)]  # repeated entries
    for tr, fr, n in ((41, 17, 9), (92, 73, 9)):
        chain, info = nq.select_chain(prods, tr, fr)
        assert len(chain) == n and info["n_unique"] == 9
        assert all(chain[i]["sec_start"].date() == chain[i + 1]["ref_start"].date() for i in range(len(chain) - 1))
    c41, _ = nq.select_chain(prods, 41, 17)
    assert [f"{p['ref_start']:%m%d}-{p['sec_start']:%m%d}" for p in c41] == \
        "0617-0629 0629-0711 0711-0723 0723-0816 0816-0828 0828-0909 0909-0921 0921-1003 1003-1015".split()


def test_dedupe_keeps_highest_version():
    gj = nq.json.loads(Path(nq.DATA_DIR / "asf" / "quetta_gunw.geojson").read_text(encoding="utf-8"))
    prods = nq.products_from_geojson(gj)
    p = next(q for q in prods if q["track"] == 41 and q["ref_start"] == datetime(2026, 6, 29, 0, 46, 30))
    q = dict(p, version=2, name=p["name"][:-3] + "002")
    chain, _ = nq.select_chain(prods + [q], 41, 17)
    assert len(chain) == 9 and chain[1]["version"] == 2


def test_geotiff_and_outputs():
    import tifffile

    chain, subs, _ = nq.synthetic_chain(n_pairs=3, plane=False)
    c = cfg()
    res = nq.process_chain(chain, subs, c, log=lambda *a: None)
    with tempfile.TemporaryDirectory() as td:
        nq.write_outputs(res, td, "t", "test", c)
        for suf in ("_map.png", "_timeseries.csv", "_cumulative_disp.npz", "_cumulative_disp_cm.tif"):
            assert (Path(td) / f"t{suf}").stat().st_size > 0
        with tifffile.TiffFile(Path(td) / "t_cumulative_disp_cm.tif") as tf:
            pg = tf.pages[0]
            assert pg.shape == res["disp_cm"].shape
            assert pg.tags[33550].value[0] == 80.0
            assert 32642 in pg.tags[34735].value
            assert np.allclose(pg.asarray(), res["disp_cm"], equal_nan=True)


def _fake_gunw(path, group=None, big=True):
    """Write a fake GUNW .h5 following the spec layout (or `group` to test the name-search fallback)."""
    import h5py

    chain, subs, _ = nq.synthetic_chain(n_pairs=1, plane=False, noise_rad=0.05)
    s = subs[0]
    base = group or nq.SPEC_IFG + "/HH"
    with h5py.File(path, "w") as h:
        h[nq.SPEC_GRID + "/listOfPolarizations"] = np.array([b"HH"])
        h[nq.SPEC_GRID + "/centerFrequency"] = 1.2575e9
        # embed the AOI grid inside a bigger frame so slicing is exercised
        pad = 50
        xs = np.concatenate([s["x"][0] - 80.0 * np.arange(pad, 0, -1), s["x"], s["x"][-1] + 80.0 * np.arange(1, pad + 1)])
        ys = np.concatenate([s["y"][0] + 80.0 * np.arange(pad, 0, -1), s["y"], s["y"][-1] - 80.0 * np.arange(1, pad + 1)])
        h[base + "/xCoordinates"] = xs
        h[base + "/yCoordinates"] = ys
        h[base + "/projection"] = np.uint32(32642)
        for k, n, fill, dt in (("unw", "unwrappedPhase", np.nan, "f4"), ("coh", "coherenceMagnitude", np.nan, "f4"),
                               ("cc", "connectedComponents", 65535, "u2"), ("iono", "ionospherePhaseScreen", np.nan, "f4")):
            arr = np.full((ys.size, xs.size), fill, dtype=dt)
            arr[pad:-pad, pad:-pad] = s[k]
            h[f"{base}/{n}"] = arr
    return s, pad


def test_extract_subset_spec_layout_and_fallback(tmp_path):
    import h5py

    for group in (None, "/science/LSAR/GUNW/grids/frequencyB/someOtherName/VV"):
        s, pad = _fake_gunw(tmp_path / "f.h5", group)
        with h5py.File(tmp_path / "f.h5", "r") as h:
            rows = nq.h5_listing(h)
            assert any("unwrappedPhase" in r for r in rows)
            sub = nq.extract_subset(h, nq.AOI, log=lambda *a: None)
        assert int(sub["epsg"]) == 32642 and abs(float(sub["wavelength"]) - 0.2384) < 2e-4
        assert sub["unw"].shape == sub["coh"].shape == sub["cc"].shape == (sub["y"].size, sub["x"].size)
        # subset must cover the AOI and be much smaller than the padded frame
        lon, lat = nq.xy_to_lonlat(*np.meshgrid(sub["x"], sub["y"]), 32642)
        assert lon.min() <= nq.AOI["lon0"] and lon.max() >= nq.AOI["lon1"]
        assert lat.min() <= nq.AOI["lat0"] and lat.max() >= nq.AOI["lat1"]
        assert sub["x"].size < s["x"].size + 2 * pad


def test_run_from_cache_without_login(tmp_path, monkeypatch):
    """Full `run` flow with cached subsets standing in for the 9 downloads: no login must be attempted."""
    monkeypatch.setattr(nq, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(nq, "OUT_DIR", tmp_path / "out")
    (tmp_path / "data" / "asf").mkdir(parents=True)
    src = Path(__file__).resolve().parent.parent / "data" / "asf" / "quetta_gunw.geojson"
    (tmp_path / "data" / "asf" / "quetta_gunw.geojson").write_bytes(src.read_bytes())
    monkeypatch.setattr(nq, "earthdata_login", lambda: (_ for _ in ()).throw(AssertionError("login attempted")))
    gj = nq.json.loads(src.read_text(encoding="utf-8"))
    chain, _ = nq.select_chain(nq.products_from_geojson(gj), 41, 17)
    _, subs, _ = nq.synthetic_chain(n_pairs=9, noise_rad=0.02)
    for p, s in zip(chain, subs):
        cp = nq.cache_path(p, None, nq.AOI)
        cp.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cp, **s)
    rc = nq.main(["run", "--offline", "--plane", "--geojson", str(tmp_path / "data" / "asf" / "quetta_gunw.geojson")])
    assert rc == 0
    assert (tmp_path / "out" / "track041_frame017" / "track041_frame017_map.png").exists()
