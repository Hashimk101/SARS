# Final NISAR ground-motion products, Quetta (Jun-Oct 2026)

Sign convention everywhere: **negative = sinking** (vertical) / **moving away from the satellite** (LOS). Units cm/yr.
Rates are fitted over only ~108-120 days (Jun-Oct 2026) and expressed per year; seasonal pumping may bias the annual equivalent.

## Products
| File | Content |
|---|---|
| `vertical_velocity_map.png` | combined vertical velocity map (5x5 smoothed), Quetta labelled |
| `los_velocity_4tracks.png` | the 4 per-track LOS maps side by side |
| `validation_nisar_vs_sentinel1.png` | NISAR vs Sentinel-1: maps, N-S profile, per-track scatter with r |
| `summary.json` | all statistics, corrections, geometry, city-centre time series |
| `geotiff/los_velocity_trackNNN_cm_yr.tif`, `los_velocity_se_trackNNN_cm_yr.tif` | per-track LOS velocity and standard error (unsmoothed) |
| `geotiff/vertical_velocity_cm_yr.tif` (+ `_uncertainty_`), `east_velocity_cm_yr.tif` (+ `_uncertainty_`) | combined solution |
| `scripts/`, `work/` | code (runnable, paths as arguments) and intermediates (`work/` includes the per-track npz and the 4326 grid) |

GeoTIFFs: EPSG:4326, float32, NaN = no data, 667 x 667 px, 0.00075 deg (~80 m), lon 66.75-67.25, lat 29.95-30.45, deflate.

## Method
1. NISAR GUNW chains (tracks 41 A frame 17, 142 A/17, 92 D/73, 20 D/73) streamed for the AOI with `nisar_quetta.py` (coherence >= 0.3, connected-component and plane removal outside the valley, referenced to 66.80E 30.25N, pair phases summed to cumulative LOS). Chains checked contiguous (8-9 pairs each).
2. Per-pixel LOS velocity = least-squares line through all epochs (>= 8 valid epochs). Standard error = residual-based regression SE. It is formal and per pixel: atmospheric noise is spatially correlated, so it is optimistic; the empirical spread on stable ground is in `summary.json` (`stable_ground_empirical_sigma_cm_yr`) and is added in quadrature (excess over formal SE) to weight and propagate uncertainty in the inversion.
3. LOS geometry read from the GUNW `metadata/radarGrid` cubes (`losUnitVectorX/Y`, `incidenceAngle`, layer at ~1500 m height; files are LEFT-looking). Median incidence: t41 45.1 deg, t92 35.6 deg. Vectors point ground to satellite (checked against look direction). East/vertical solved per pixel by weighted least squares from the tracks used, assuming no north-south motion (the north component of the LOS vector, ~0.17-0.18, is therefore ignored; any N-S motion leaks into the result).
4. Vertical/east need one ascending and one descending track per pixel; the tracks entering the inversion are those with r >= 0.5 vs Sentinel-1: **41 and 92**. Tracks 142 and 20 are published as LOS products but flagged noisy and excluded (sensitivity using all four is in `summary.json`, `sensitivity_all_four_tracks`).

## Corrections (see summary.json `corrections`)
- **DEM-elevation atmosphere correction (Copernicus GLO-30, public AWS tiles, window fetched by HTTP range requests):** per epoch fit cum = a + b*h on stable ground (outside lon 66.90-67.08/lat 30.03-30.30 and outside S1-flagged sinking), subtract b*h. Kept per track only if r vs S1 does not fall and the spread of rates outside the valley falls. Result: t41 r 0.67->0.88, sigma outside valley 4.4->2.9 cm/yr, share of pixels below -3 cm/yr outside valley 31%->11%; t92 r 0.80->0.82, 3.5->3.1, 19%->9%; t20 helped (r 0.00->0.24) but is still unusable; t142 hurt (not applied).
- **Ionosphere (ionospherePhaseScreen):** file attributes: units radians, no sign convention stated; ASF docs say it is *not applied* to unwrappedPhase by default and give no sign/scaling. Regression of unwrappedPhase on the screen on stable ground gives slope ~ +1.1-1.3 (raw), so the screen has the same sign and roughly unit scale: **subtracting is the right operation**. Its per-pixel uncertainty layer is ~0.5-2.9 rad (mean ~0.9 rad = ~1.7 cm), larger than a 12-day bowl signal (~0.3-0.5 rad), and the non-planar part carries bowl-scale structure. Effect (after plane removal): t41 r 0.67 -> 0.36 (worse; adding the screen gives 0.82 but is unphysical and raises mountain noise), t92 0.80 -> 0.76 (calms mountains but weakens the bowl), t142 0.08 -> 0.49 and noise 13.9 -> 7.2 cm/yr (clearly better), t20 noise 21 -> 17 cm/yr. Applied only to 142 and 20. Likely cause of the track-41 degradation: the screen's bowl-scale noise/leakage, not a sign error. Not proven.
- **GUNW `mask` layer:** used for 41/92; disabled for 142/20 (different mask encoding removed most pixels; valid fraction 58% -> 74% on 142).

## Caveats
- NISAR (Jun-Oct 2026, L-band) vs Sentinel-1 (Sep 2024-Sep 2025, C-band) are different years/geometries; agreement is in shape and magnitude, not exact values.
- Residual weather/terrain blobs remain on the mountains (west and far east); the valley-outside-bowl median is biased by about +2 to +4 cm/yr on t41/t92 (referencing to a bedrock box). Treat the 5-10 cm/yr contours as reliable, ~2 cm/yr as noise level.
- Tracks 142 and 20 are noisy (stable-ground sigma 6.6 and 12 cm/yr per pixel); do not quote them quantitatively. Track 142 has a frame edge in the east (valid area ~60%).
- Strict masking: a pixel invalid in any pair is dropped from later epochs.
- Reproduce: `scripts/` (run with `python -I`): `dem_prep.py`, `fetch_subsets.py` + `nisar_quetta.py run ... --plane [--iono] [--no-mask-layer]`, `fetch_geometry.py`, `iono_test.py`, `iono_regress.py`, `make_products.py`, `make_figures.py` (usage in each docstring). `nisar_quetta.py` is a copy of the pipeline script.
