"""OPTIONAL, modest random-forest 'drivers' analysis: sinking rate vs elevation, distance to valley axis,
distance to the valley edge (mountain front), local slope and building density.

Heavily caveated: correlative, not causal; 4 months of NISAR; building footprints are a PROXY for urban
pumping demand; features are spatially autocorrelated, so we use latitude-block spatial cross-validation.
"""
import os, json
import numpy as np
from scipy import ndimage as ndi


def run(c):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mask = c["mask"]
    H, W = mask.shape
    lat = c["LAT"]
    lon = c["LON"]
    res = abs(c["lons"][1] - c["lons"][0])
    kx = 111.32 * np.cos(np.radians(30.2)) * res
    ky = 110.57 * res
    elev = c["elev"]
    sink = -c["rate"]
    ok = mask & np.isfinite(sink) & np.isfinite(elev)
    # valley axis: per row, lon of lowest smoothed elevation in mask -> polyline; distance to nearest axis pixel
    es = ndi.gaussian_filter(np.where(mask, np.nan_to_num(elev, nan=np.nanmedian(elev[mask])), np.nan_to_num(elev, nan=3000)), 3)
    axis = np.zeros((H, W), bool)
    for i in range(H):
        if mask[i].any():
            j = np.where(mask[i], es[i], np.inf).argmin()
            axis[i, j] = True
    d_axis = ndi.distance_transform_edt(~axis, sampling=(ky, kx))
    d_edge = ndi.distance_transform_edt(mask, sampling=(ky, kx))
    bdens = ndi.gaussian_filter(c["bcount"], 6) / (res * 111.32 * np.cos(np.radians(30.2)) * res * 110.57)  # per km2 smoothed
    feats = {"elevation_m": elev, "dist_to_valley_axis_km": d_axis, "dist_to_valley_edge_km": d_edge,
             "slope_deg": c["slope"], "building_density_per_km2": bdens}
    names = list(feats)
    X = np.column_stack([feats[n][ok] for n in names])
    y = sink[ok]
    blk = np.digitize(lat[ok], np.linspace(lat[ok].min(), lat[ok].max(), 6)[1:-1])   # 5 latitude blocks
    rng = np.random.default_rng(0)
    sub = rng.choice(len(y), min(len(y), 20000), replace=False)
    X, y, blk = X[sub], y[sub], blk[sub]
    pred = np.zeros_like(y)
    imps = []
    for b in np.unique(blk):
        tr, te = blk != b, blk == b
        rf = RandomForestRegressor(n_estimators=150, min_samples_leaf=20, n_jobs=-1, random_state=0).fit(X[tr], y[tr])
        pred[te] = rf.predict(X[te])
        pi = permutation_importance(rf, X[te], y[te], n_repeats=3, random_state=0, n_jobs=-1)
        imps.append(pi.importances_mean)
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    imp = np.mean(imps, 0)
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=20, n_jobs=-1, random_state=0).fit(X, y)
    res_d = dict(label=c["label"] or "FINAL", n_samples=int(len(y)), spatial_block_cv_r2=float(r2),
                 permutation_importance_heldout={n: float(v) for n, v in zip(names, imp)},
                 impurity_importance_fullfit={n: float(v) for n, v in zip(names, rf.feature_importances_)},
                 caveat="Correlative only; short NISAR record; spatially autocorrelated; building density is a proxy; block-CV R2 can be negative, which means no transferable skill.")
    with open(os.path.join(c["out"], "drivers_rf.json"), "w") as f:
        json.dump(res_d, f, indent=1)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=200)
    o = np.argsort(imp)
    ax.barh(np.array(names)[o], imp[o], color="#4c78a8")
    ax.set_xlabel("Permutation importance (drop in R2, held-out latitude blocks)")
    ax.set_title(f"Random-forest drivers of sinking rate (exploratory; block-CV R2 = {r2:.2f})" + (f" [{c['label']}]" if c["label"] else ""), fontsize=10)
    fig.text(0.5, 0.005, "Correlative, not causal. Scenario/analysis aid, not a forecast.", ha="center", fontsize=8, style="italic")
    fig.subplots_adjust(left=0.33, bottom=0.2)
    sfx = f"_{c['label']}" if c["label"] else ""
    fig.savefig(os.path.join(c["out"], "figures", f"chart_rf_drivers{sfx}.png")); plt.close(fig)
    print("RF block-CV R2", r2, dict(zip(names, np.round(imp, 3))))
