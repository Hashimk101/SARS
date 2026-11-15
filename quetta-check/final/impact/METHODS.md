# Quetta impact module: methods, assumptions, limitations

**What this is:** risk *scenarios* for land subsidence in the Quetta valley to 2030 / 2040 / 2050, screening-level building-damage zones, and exposure counts. It is **not a forecast**. Future sinking depends on future pumping, which nobody can know. Every number below is conditional on the stated scenario assumptions.

**PROVISIONAL warning.** All results currently in `results_PROVISIONAL/` (files suffixed `_PROVISIONAL`) were computed from a *development stand-in* rate map built from only ~120 days of NISAR data on each of two tracks (t92 descending, t41 ascending, Jun-Oct 2026), LOS divided by cos(38 deg). Its bowl maximum (~22 cm/yr vertical, p99 ~17 cm/yr) is higher than published rates (11-16 cm/yr) and than our Sentinel-1 estimate (~14 cm/yr vertical), so provisional cumulative numbers are probably biased high. Re-run on the final NISAR map (command at the bottom). Results scale roughly linearly with the rate map, so a bowl-max rate of 14 cm/yr would give S1 ~3.3 m by 2050.

## 1. Pipeline overview

`scripts/impact_pipeline.py --rate R.tif --rate-unc U.tif --out DIR [--label PROVISIONAL]`

1. Read vertical-velocity (cm/yr, negative = sinking) and 1-sigma uncertainty rasters (EPSG:4326). All outputs are on the rate raster's grid (provisional: 0.00075 deg, ~80 m, 533 x 533, AOI 66.80-67.20 E, 30.00-30.40 N).
2. Valley mask (Copernicus DEM).
3. Monte Carlo scenario simulation (500 draws) per pixel, S1/S2/S3, years 2026-2050.
4. Damage screening from the median field's gradient.
5. Exposure (buildings, population) per class and scenario.
6. GeoTIFFs, maps, charts, `summary.json`, `exposure.csv`, pixel table, optional random-forest drivers.

Downloads (cached in `--data`, default `<out>/../_impact_data`) happen automatically from public URLs, no login.

## 2. Data and licences

| Dataset | Used for | Source | Licence / attribution |
|---|---|---|---|
| NISAR vertical velocity + uncertainty | main input | project (final map pending); provisional built by `scripts/make_provisional_rate.py` from the project's NISAR GUNW-derived cumulative displacement | NASA/ISRO NISAR data are open |
| Copernicus DEM GLO-30 (tiles N30_E066, N30_E067) | valley mask, slope, hillshade, driver features | `https://copernicus-dem-30m.s3.amazonaws.com/` (AWS Open Data) | Copernicus DEM licence: free of charge, attribution "Produced using Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved" |
| Microsoft Global ML Building Footprints, release 2026-02-03, Pakistan, quadkeys 123031131 and 123031133 (195,213 footprints inside the AOI) | building exposure (footprint vertex-mean centroid) | `https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv`, repo `microsoft/globalmlbuildingfootprints` | ODbL 1.0 (check repo README before redistribution; attribution "Microsoft Global ML Building Footprints") |
| WorldPop Global 2015-2030 R2025A, Pakistan, 2025, 100 m, constrained (`pak_pop_2025_CN_100m_R2025A_v1.tif`) | population exposure | `https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2025/PAK/v1/100m/constrained/` | CC BY 4.0, attribution "WorldPop (www.worldpop.org), University of Southampton". Licence taken from WorldPop's standard terms; confirm on the dataset page before publication |

Google Open Buildings and OSM were not needed. Note WorldPop "constrained" population is distributed over building footprints from a different source, so building and population counts are consistent in pattern but not identical sources. Population total inside the AOI: 2.68 M; inside the valley mask: 1.77 M. Valley mask contains 117,151 building centroids. Microsoft footprints may miss or merge buildings, and include non-residential structures; they are counted as "buildings" without type.

## 3. Valley mask (task 1)

Mask = valid rate pixel AND inside bbox lon 66.88-67.10, lat 30.04-30.30 AND mean elevation <= 1,750 m AND mean slope <= 4 deg (30 m DEM averaged to the analysis grid), followed by one binary opening, removal of components < 200 pixels, and hole-filling.

Justification: Quetta city centre is at ~1,675 m; valley-floor elevations in the bowl region are ~1,620-1,750 m. Of provisional pixels sinking >= 3 cm/yr inside the bowl region, 99% lie below 1,750 m (median 1,682 m); mountains rise above 2,000 m within a few km. The NISAR maps contain weather/terrain artifacts on the surrounding mountains, which this mask removes. Holes inside the mask where the input has no data (decorrelated core; 8% of mask pixels in the provisional run) are filled from the nearest valid pixel and their uncertainty is inflated by 1.5x. The bbox excludes the valley north of 30.30 N and east of 67.10 E, so exposure there is not counted (the bowl lies at 30.08-30.25 N).

## 4. Scenarios (task 3)

Cumulative subsidence is counted from 1 Jan 2026 (T0 = 2026.0); the measured rate is treated as the rate at T0.

**Rate uncertainty (all scenarios).** Each draw k and pixel p: `sinking_rate = max(-(rate_p + sigma_p * z_pk), 0)` (cm/yr). `z` is a unit-variance Gaussian field: sqrt(0.7) x one value shared by the whole map per draw (systematic error: reference, LOS-to-vertical, track mix) + sqrt(0.3) x a spatially correlated field (Gaussian-smoothed noise, correlation length ~12 px = ~1 km; atmosphere). Independent per-pixel noise was deliberately not used because it inflates the bowl maximum by picking the luckiest pixel. Uplift/noise is floored at zero sinking, which gives a small positive bias on stable pixels.

Provisional `sigma` = sqrt(SE_reg^2 + (0.25 rate)^2 + 1.0^2) cm/yr (regression standard error of the 120-day slope, a 25% systematic allowance, 1 cm/yr atmospheric floor); median 4.4 cm/yr in the valley. The final map's uncertainty raster replaces it.

| Scenario | Rate law | Parameters sampled per draw |
|---|---|---|
| **S1 Current trend** | `r(t) = r0` | rate uncertainty only |
| **S2 Keeps accelerating** | `r(t) = r0 * min(exp(g t), cap)` | g ~ triangular(0.5, 2.6, 4.0) %/yr; cap ~ uniform(1.3, 1.8) x r0 |
| **S3 Pumping controlled** | `r(t) = r0` until Ti, then `r0 * exp(-(t-Ti)/tau)` | Ti ~ uniform integer 2027-2030; tau ~ log-uniform 5-15 yr |

*S2 calibration.* Published rates rise from ~11.4 cm/yr (2003-2010, midpoint ~2006.5) to ~16 cm/yr (after 2016; period midpoint ~2019.5): ratio 1.40 over ~13 yr = **2.6 %/yr** (mode). Range 0.5-4 %/yr: low end because our 2024-26 measurements (~14 cm/yr vertical at Sentinel-1 max) show no clear further growth beyond 16; high end allows continued acceleration. Cap: rate cannot exceed 1.3-1.8x today's local rate (bowl max ~14-16 cm/yr -> ~20-29 cm/yr). Rationale: the highest published single-station value is ~16.6 cm/yr, aquifer drawdown and well failure (experts warn many wells may run dry within 5-10 years) limit further growth, and pumping cannot grow without bound in an arid basin. This cap is a judgement, not a measured limit.

*S3.* Intervention year 2027-2030 (assumed, e.g. 2028 median); e-folding time 5-15 yr. Compaction of clay is largely irreversible, so there is **no rebound**: the field only stops growing. Delayed consolidation of thick clays after head recovery is represented by the slow decay (tau up to 15 yr). It does not model a collapse of pumping because wells run dry, nor any recharge; S3 is a "what if policy works" case, with no claim it will happen.

Outputs per scenario/year (2030, 2040, 2050): median, p10, p90 cumulative subsidence (cm, positive = down) and, for 2026-2050 every year, the percentiles of the bowl-maximum (max over pixels per draw). The bowl-max band includes rate-map error plus scenario parameters; it does not include structural surprises, spatial changes of the pumping centre, or new fissures.

### Headline numbers (PROVISIONAL input; median [p10-p90])

Bowl maximum cumulative subsidence since Jan 2026 (m):

| | 2030 | 2040 | 2050 |
|---|---|---|---|
| S1 Current trend | 0.86 [0.53-1.37] | 3.01 [1.87-4.80] | 5.17 [3.20-8.23] |
| S2 Keeps accelerating | 0.91 [0.55-1.44] | 3.61 [2.14-5.69] | 6.90 [3.97-10.71] |
| S3 Pumping controlled | 0.83 [0.50-1.30] | 1.86 [1.13-3.01] | 2.21 [1.24-3.72] |

Area (km2) subsiding more than 1 m / 2 m by 2050 (valley mask = 142 km2):

| | > 1 m | > 2 m |
|---|---|---|
| S1 | 56 [19-91] | 27 [4-62] |
| S2 | 62 [24-101] | 39 [8-75] |
| S3 | 17 [1-52] | 0.3 [0-7] |

## 5. Damage risk (task 4)

**Angular distortion proxy** beta = |grad of median cumulative subsidence| in m/m, computed on the analysis grid after Gaussian smoothing (sigma = 1 px, ~80 m), with metre spacing from latitude. Outside-mask pixels are filled by nearest value before differencing so that the mask edge is not read as a cliff.

**Classes** (thresholds verified against the literature as far as sources could be found; see caveats):

| Class | beta | Basis |
|---|---|---|
| 0 negligible | < 1/1000 | below Bjerrum's tightest limit for settlement-sensitive structures / machinery (1/750 to ~1/1000 in tabulations) |
| 1 low | 1/1000 - 1/500 | 1/500 is Bjerrum's (1963) "safe limit" for buildings where cracking is not permissible; 1/500 also appears as onset of wall/partition cracking in Poulos et al. (2001) tabulations |
| 2 slight (cracking onset) | 1/500 - 1/300 | 1/300 = first cracking in panel/brick walls (Skempton & MacDonald 1956, Bjerrum 1963); 1/300 is also cited as the cracking limit for gypsum wallboard (ASCE J. Perform. Constr. Facil. 1990) |
| 3 moderate (wall cracking) | 1/300 - 1/150 | considerable cracking in panel and brick walls |
| 4 severe (structural-damage risk) | >= 1/150 | Skempton & MacDonald (1956) / Bjerrum (1963): structural damage to beams and columns expected at ~1/150 |

References: Skempton, A.W. & MacDonald, D.H. (1956), The allowable settlements of buildings, Proc. ICE Part 3, 5, 727-768. Bjerrum, L. (1963), Discussion, Proc. European Conf. Soil Mech. Found. Eng., Wiesbaden, vol. 2, 135-137. Boscardin, M.D. & Cording, E.J. (1989), Building response to excavation-induced settlement, J. Geotech. Eng. ASCE 115(1), 1-21. Burland, J.B. (1995), Assessment of risk of damage to buildings due to tunnelling and excavation, Proc. 1st Int. Conf. Earthquake Geotech. Eng., Tokyo. Poulos, H.G., Carter, J.P. & Small, J.C. (2001), Foundations and retaining structures: research and practice, Proc. 15th ICSMGE.

**Verification status (be honest with judges).** In this session the 1/150 (structural damage; Bjerrum, Skempton & MacDonald), 1/300 (cracking) and 1/500 (cracking onset in Poulos et al. 2001) values were confirmed against secondary sources found by web search. The 1/1000 "negligible" boundary and Bjerrum's 1/500 "safe limit" wording come from standard textbook tabulations and were **not re-checked against the original 1963 paper**. Boscardin & Cording (1989) and Burland's categories classify damage by combined angular distortion **and horizontal tensile strain** (negligible / very slight / slight / moderate / severe); their numeric category limits were **not verified** here and are not used. Our classes are therefore a beta-only simplification of the Skempton-Bjerrum framework, with the B&C/Burland damage vocabulary used only loosely as labels. Limits are for framed/masonry buildings on spread foundations, not for pipelines, roads, rail, or tube wells.

**Key limitation: resolution.** An 80 m grid smooths subsidence over distances much larger than a building (~10-20 m). Building-scale angular distortion is **larger** than the grid-scale beta (differential movement concentrates at fissures, pumping wells and fault-like discontinuities). The classes are **zone-level screening classes**, probably underestimating true building-scale distortion, and must not be used for assessing individual buildings. Also, beta from a *cumulative* field integrates over decades. Damage depends on when and how fast differential movement accumulates, building age, material, foundation, and maintenance; none of these is known.

**Classification is applied to the median field.** For an uncertainty-aware view, `exposure.csv` also includes the same classification on the p10 and p90 fields (`field` column). This is not the same as the percentile of beta over draws.

**Fissure-risk flank zone (heuristic).** Pixels on the bowl flanks (cumulative subsidence between 10% and 70% of the scenario bowl maximum and at least 20 cm) whose beta is in the top decile of flank pixels (and at least 1/1000). It flags where gradients concentrate, consistent with earth fissures forming at bowl margins/basement-step edges. Caveats: relative, not absolute (by construction ~6-7 km2 in every year with subsidence); not validated against mapped fissures (no fissure inventory was obtained); fissures depend on buried bedrock topography and sediment contrast not available here.

### Damage-class exposure, median field, valley mask (PROVISIONAL input)

Buildings (footprint centroids), class 1 / 2 / 3 / 4 (class 0 = remainder of the 117,151):

| | 2030 | 2040 | 2050 |
|---|---|---|---|
| S1 | ~0 in all classes | 18,034 / 3,302 / 4 / 0 | 30,307 / 11,658 / 3,668 / 0 |
| S2 | ~0 | 23,206 / 5,068 / 314 / 0 | 30,331 / 18,352 / 7,311 / 128 |
| S3 | ~0 | 5,933 / 11 / 0 / 0 | 9,004 / 396 / 0 / 0 |

People (rounded to 10), class 1 / 2 / 3 / 4 (class 0 = remainder of 1.77 M):

| | 2040 | 2050 |
|---|---|---|
| S1 | 322,800 / 61,080 / 80 / 0 | 490,350 / 204,340 / 68,000 / 0 |
| S2 | 408,790 / 89,110 / 6,510 / 0 | 455,410 / 334,080 / 124,500 / 2,510 |
| S3 | 103,030 / 210 / 0 / 0 | 151,590 / 8,180 / 0 / 0 |

(Using the p90 field, 2050 class 3+4 buildings are 7,784 for S1, 16,459 for S2, 36 for S3.) Full tables for all years/fields in `exposure.csv`.

Today's measured rate: valley area sinking faster than 5 cm/yr = 53.8 km2 with 54,618 buildings and ~934,000 people; faster than 10 cm/yr = 13.5 km2, 15,053 buildings, ~317,000 people.

People/buildings are assigned to the grid pixel containing the footprint centroid / WorldPop cell centre; WorldPop 100 m cells are re-binned, not area-weighted, so very local counts are noisy. Totals are conserved.

## 6. Optional random-forest drivers (task 7)

`scripts/drivers_rf.py`. Random forest (150 trees, min leaf 20; 20,000 sampled valley pixels) of sinking rate on five features: elevation, distance to the valley axis (row-wise minimum smoothed elevation), distance to the valley edge, slope, and smoothed building density. Validation by 5 latitude-block spatial cross-validation: block-CV R2 = 0.41 (provisional). Permutation importance on held-out blocks: elevation 0.48, building density 0.27, distance to valley axis 0.26, distance to valley edge 0.23, slope 0.03. **Interpretation is limited:** correlative, not causal; elevation mostly encodes position in the bowl (the bowl sits in the lowest part of the valley); building density is a proxy for urban pumping demand, but also sits where the bowl is, so the features are collinear; the provisional rate has only 4 months of data; and spatial autocorrelation remains. Do not present this as proof of drivers. Output: `drivers_rf.json`, `figures/chart_rf_drivers_*.png`.

## 7. Limitations summary

1. Scenarios, not forecasts. The probability of each scenario is not estimated; the p10-p90 bands are conditional on that scenario's assumed parameter ranges and the rate-map error model, which are subjective.
2. Provisional input: 4 months of NISAR, LOS/cos(38 deg) with a single constant incidence angle and no asc/desc decomposition (horizontal motion ignored), no atmospheric correction, no ionosphere correction. Strongly overestimates the bowl maximum relative to literature (see above).
3. The linear-in-time extrapolation of a 2026 rate over 24 years ignores feedbacks: compaction slows as clay consolidates and aquifer storage is exhausted; the pumping centre may migrate; wells may dry out. 
4. Spatial resolution 80 m; zone-level only. No building type, age, foundation, or well location data.
5. Beta is derived from cumulative subsidence of a median field; MC percentile fields are used only for the p10/p90 sensitivity.
6. Valley mask excludes slopes; subsidence near mountain fronts (where fissures and many buildings are) may be partly masked.
7. Exposure counts use footprint centroids (any building) and WorldPop 2025 (not projected to 2030-2050). Population and building growth are ignored, so future exposure is probably underestimated.
8. No infrastructure (pipes, roads, rail, canals), no flood or groundwater modelling.

## 8. Re-running on the final NISAR map

```
python -I scripts/impact_pipeline.py \
  --rate  D:/SARS/quetta-check/final/nisar/<final_vertical_velocity>.tif \
  --rate-unc D:/SARS/quetta-check/final/nisar/<final_uncertainty>.tif \
  --out D:/SARS/quetta-check/final/impact/results_FINAL \
  --data <download cache dir>
```
(requires numpy, scipy, matplotlib, rasterio, pandas, scikit-learn; see `scripts/requirements.txt`). Omit `--label` for final outputs; add `--label PROVISIONAL` for provisional ones. Both rasters must be EPSG:4326 in cm/yr, negative = sinking. The uncertainty raster may be on a different grid (it is resampled bilinearly). Options: `--draws 500`, `--seed`, `--no-rf`, `--no-figures`. Runtime ~2 min plus one-off ~200 MB downloads.

## 9. Output files

- `results_PROVISIONAL/geotiffs/`: `cum_subsidence_{S1,S2,S3}_{2030,2040,2050}_{median,p10,p90}_cm`, `damage_class_*` (0-4, 255 nodata), `angular_distortion_*` (m/m), `fissure_risk_*`, `rate_used`, `rate_unc_used`, `valley_mask`, `buildings_per_pixel`, `population_per_pixel`, `elevation_m`. All EPSG:4326, ~80 m.
- `results_PROVISIONAL/figures/`: rate map today; 2050 cumulative scenario maps; damage zones 2050 and 3x3 grid; bowl-max time-series chart with p10-p90 bands; exposure bars; RF drivers.
- `results_PROVISIONAL/summary.json`, `exposure.csv` (long format: scenario, year, field, zone, area_km2, buildings, people), `pixel_table_PROVISIONAL.csv.gz` (one row per valley pixel: rate, per-scenario median/p10/p90, class, fissure flag, buildings, people), `drivers_rf.json`.
- `inputs/`: the provisional rate and uncertainty GeoTIFFs.

## 10. FINAL runs (2026-11-15) — use these, not `results_PROVISIONAL/`

The provisional results above (sections 4–5 headline tables) came from a rate map built before the final NISAR products existed and are biased high. The final runs use the final NISAR vertical-velocity map (`../nisar/geotiff/vertical_velocity_cm_yr.tif`: tracks 41 + 92, terrain-corrected, vertical/east solve; bowl median −8.7 cm/yr, r = 0.89 vs Sentinel-1):

| Folder | Input | Why |
|---|---|---|
| `results_FINAL_annualized/` (**recommended headline**) | NISAR vertical rate × 0.75 (`inputs/*ANNUALIZED_x0.75.tif`) | NISAR covers only Jun–Oct 2026 (summer pumping). Sentinel-1 full-year rates over Quetta are ≈ 0.75 × its Mar–Sep rates (bowl max −10.8 vs −14.6 cm/yr LOS; city centre −9.3 vs ≈ −12.3), so the scaled map approximates an annual rate. |
| `results_FINAL_as_measured/` | NISAR vertical rate as measured | Upper-bound sensitivity. |

Scale script: `scripts/scale_rate.py`. Same scenario parameters, mask, thresholds, 500 draws, seed 20260.

### 2050 headline (median field; valley mask 124 km², ~112k buildings, ~1.71 M people)

| Scenario | Area sunk ≥ 1 m | Buildings / people in ≥ 1 m zone | Area sunk ≥ 2 m | Buildings in moderate + severe damage-risk zones | People in those zones |
|---|---|---|---|---|---|
| **Annualized ×0.75** | | | | | |
| S1 Current trend | 46 km² | 49,285 / 0.86 M | 12.7 km² | 5,476 + 51 | ≈ 92,000 |
| S2 Keeps accelerating | 52 km² | 55,769 / 0.96 M | 24.4 km² | 12,254 + 543 | ≈ 210,000 |
| S3 Pumping controlled | 6.2 km² | 7,317 / 0.14 M | 0.05 km² | 0 + 0 | ≈ 0 |
| **As measured** | | | | | |
| S1 Current trend | 53 km² | 56,473 / 0.96 M | 26.2 km² | 13,142 + 627 | ≈ 226,000 |
| S2 Keeps accelerating | 57 km² | 60,569 / 1.01 M | 39.8 km² | 21,134 + 2,749 | ≈ 409,000 |
| S3 Pumping controlled | 17 km² | 18,355 / 0.37 M | 0.9 km² | 210 + 0 | ≈ 4,300 |

Rates today (vertical): annualized p99 14.2 cm/yr, city centre −14.8 cm/yr; as measured p99 18.9 cm/yr, city centre −19.8 cm/yr. A robust "fastest-sinking 1 % of the valley" figure is p99 × 24 yr ≈ **3.4 m (annualized) to 4.5 m (as measured) more by 2050 if current rates continue**. The `bowl_max` values in `summary.json` (e.g. 5.1 m S1 annualized) come from the single fastest pixel and are noise-sensitive; prefer the p99 and area/exposure figures.
