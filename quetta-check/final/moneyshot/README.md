# NISAR GSLC interferogram of Quetta ("money shot" attempt)

**Honest result:** the 336-day pair (2025-11-25 BETA -> 2026-10-27 V1) is decorrelated (mean coherence ~0.11, about the noise floor), so no fringes can be shown. The 132-day pair (2026-06-17 -> 2026-10-27, track 41 ascending, frame 17) is coherent (mean 0.47) but shows less than one fringe: a localized phase anomaly (~1-2 rad, ~2-4 cm LOS) at the city centre, sitting among atmospheric/topographic ramps of similar size. It is NOT a clean ring pattern.

## Files
- `B_132d_interferogram_filtered.png`, `..._unfiltered.png` - full AOI (66.80-67.20E, 30.00-30.40N), HSV cyclic colour, dimmed by coherence
- `B_132d_zoom.png`, `B_132d_zoom_highpass.png` - zoom on the basin; the high-pass version removes smooth ramps (12 km box) and is the most convincing view of the Quetta anomaly
- `B_132d_coherence.png`, `B_132d_transects.png` (E-W and N-S through 66.99E 30.18N)
- `A_336d_*` - same products for the decorrelated 336-day pair
- `side_by_side_336d_vs_132d.png`
- `*_phase_coh.tif` - GeoTIFF, EPSG:32642, 60 m; band 1 wrapped phase (rad, referenced), band 2 coherence
- `pairA.npz`, `pairB.npz` - multilooked complex ifg (raw and Goldstein-filtered), coherence, georeferencing
- `stats.json`, `*_stats.json`; `scripts/`

## Method
- Data: NISAR L2 GSLC, `/science/LSAR/GSLC/grids/frequencyA/HH`, 5 m x 5 m posting, UTM 42N (EPSG:32642), same grid for same track/frame. Per ASF docs the phase is flattened for the reference orbit, so cross-multiplication gives a flattened interferogram; there is no stated DEM/baseline correction, so residual topographic phase may remain (perpendicular baseline unknown to us). Only the AOI window (9728 x 8192 px) was streamed (earthaccess + h5py), ~0.6 GB each.
- ifg = s_early * conj(s_late) (earlier date = reference). Assuming SAR phase = -4*pi*R/lambda, positive phase = range increase = motion away from satellite (subsidence). The sign was not verified against the file spec; verify against the GUNW-based result before publishing.
- The two GSLCs of a pair are NOT perfectly co-registered (offsets ~0.3 px in rows, ~1.3 px in columns for the BETA-V1 pair; ~0.1-0.2 px for pair B). We estimated offsets from amplitude cross-correlation on 512 px patches, median-filled, interpolated and applied Fourier sub-pixel shifts to the later image before multiplying.
- 12 x 12 boxcar multilook = 60 m; coherence = |sum s1 s2*| / sqrt(sum|s1|^2 sum|s2|^2); Goldstein filter (alpha 0.6, 32 px windows) for the "filtered" display; reference phase = coherence-weighted mean in a 4 km box at 66.80E 30.25N (a coherent patch there, coh>0.4).
- Lambda = 0.2420 m (centre frequency 1239 MHz); one fringe = 12.1 cm LOS.

## Caveats
- The 336-day pair mixes BETA (v1.0.2) and V1 (v1.0.20) processing; decorrelation may be partly due to that (and to the large offsets) rather than purely temporal, we cannot separate them. Pair B mixes v1.0.11 and v1.0.20 as well but is coherent.
- Pair B's ramps (up to ~1 fringe over tens of km, correlated with relief) are most likely atmosphere, ionosphere and residual topographic phase; no corrections applied. Fringe counts are therefore an upper bound on subsidence only loosely.
- The Quetta anomaly is a few km wide and ~2-4 cm LOS, consistent with 7-14 cm/yr x 132 d x cos(inc) but not uniquely identifiable from one interferogram. Better: stack several 12-day pairs.
- Pair C (track 142) was not needed or processed. The optional velocity-contour overlay was skipped.
