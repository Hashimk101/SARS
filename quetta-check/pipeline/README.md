# NISAR GUNW -> Quetta subsidence check

`nisar_quetta.py` selects a chain of consecutive NISAR L2 GUNW pairs over Quetta, streams only the AOI
(lon 66.75-67.25, lat 29.95-30.45) of the needed layers from each ~2.3 GB `.h5`, sums the unwrapped phase along
the chain, and writes a cumulative line-of-sight (LOS) displacement map, GeoTIFF, CSV time series and a summary.

## Setup (Windows Git Bash shown; venv already exists in `..\venv`)

```bash
cd <this folder>/..                       # the nisar_pipeline folder
python -m venv venv
./venv/Scripts/python -m pip install earthaccess h5py numpy matplotlib tifffile
# optional: pytest (tests), pyproj (only used by the tests as a cross-check)
```

Always run with `-I` (isolated mode): `./venv/Scripts/python -I scripts/nisar_quetta.py ...`

## Earthdata login (you do this yourself; the script never reads or prints credentials)

1. Create an account at https://urs.earthdata.nasa.gov (accept the ASF / NISAR data terms if asked).
2. Configure ONE of:
   - environment variable `EARTHDATA_TOKEN=<token from your URS profile>`; or
     `EARTHDATA_USERNAME` + `EARTHDATA_PASSWORD`
   - a netrc file (`%USERPROFILE%\_netrc` or `~/.netrc`) containing
     `machine urs.earthdata.nasa.gov login <user> password <password>`
3. Check: `./venv/Scripts/python -I scripts/nisar_quetta.py auth-check` (exit code 0 = OK, 2 = not configured;
   it prints setup instructions when not configured). Only the non-interactive earthaccess strategies
   `environment` then `netrc` are tried; there is never a prompt.

## Commands

```bash
PY="./venv/Scripts/python -I scripts/nisar_quetta.py"

$PY select --track 41 --frame 17          # search ASF (no login), print the 9-pair chain
$PY select --track 92 --frame 73
$PY list-h5 <https URL or local .h5>      # dump groups/datasets of one file (login needed for URL)

# the real check (ascending, primary):
$PY run --track 41 --frame 17 --plane
# secondary check (descending):
$PY run --track 92 --frame 73 --plane

$PY demo                                  # synthetic data, exercises processing + plotting, no login
./venv/Scripts/python -I -m pytest scripts/test_pipeline.py -q -p no:cacheprovider
```

Useful options for `run`: `--iono` (subtract ionospherePhaseScreen; off by default), `--plane` (remove best-fit
plane estimated outside the valley box), `--coh-min 0.3`, `--ref-lon 66.80 --ref-lat 30.25 --ref-half 0.02`
(reference box), `--phase-sign -1` (see sign check), `--pol HH`, `--start/--end` (reference-date window of the
chain, default 2026-06-01..2026-12-31), `--max-pairs N`, `--offline` (use the saved geojson instead of the live
ASF search; the script also falls back to it automatically if the API is unreachable).

Subsets are cached as `data/cache/<scene>__<pol>__<aoi>.npz`; re-runs (and any parameter change) need no login or
network once all subsets are cached. Select-only and the demo never need login.

## What happens

1. Chain: filter by track/frame/date window, dedupe on (reference date, secondary date) keeping the highest product
   version, take the longest contiguous run (secondary date == next reference date).
2. Per pair, from the AOI subset: valid = finite phase, coherence >= 0.3, connectedComponents > 0 (65535 = fill),
   GUNW `mask` layer valid and not water; optionally minus ionosphere screen; keep only the connected component that
   holds the reference box; subtract the median phase in the reference box; optional plane removal (fit outside the
   valley box 66.85-67.10E, 30.05-30.40N) and re-reference.
3. Sum pairs (telescoping) to cumulative phase per epoch. A pixel invalid in any pair is NaN afterwards (strict).
4. Convert: `displacement_cm = -phase_sign * phase * lambda/(4 pi) * 100`, lambda = c / centerFrequency from the file
   (0.2384 m fallback). Default `phase_sign=+1`: **negative = moving away from the satellite (sinking), positive =
   toward the satellite.** This is LOS, not vertical (vertical ~ LOS / cos(incidence), ~35-45 deg).

## Outputs (`out/track041_frame017/`)

- `..._map.png`   map (Quetta, airport, reference box, valley box labelled; colorbar in cm) + time-series panel
- `..._cumulative_disp_cm.tif`  north-up GeoTIFF (UTM 42N EPSG read from file), float32 cm, NaN nodata
- `..._cumulative_disp.npz`     disp_cm, per-epoch cum_cm stack, x/y, lon/lat, dates
- `..._timeseries.csv`          cumulative cm per epoch at city_center (66.99E 30.18N), airport (66.94E 30.25N),
  reference
- console summary: max LOS sinking (5x5-smoothed, inside valley box), its location, implied cm/yr over the span.

Expect (if the published ~12-16 cm/yr is seen): ~4-5 cm of LOS sinking over the 0617->1015 span (120 days) near
the city, ~0 at the reference. Noise and atmosphere are of order 1 cm per pair, so a 2-5 cm bowl is detectable
but check `--iono` and `--plane` variants and the descending track for consistency.

## Sign check (IMPORTANT, unverified)

The GUNW product spec (JPL D-102272 Rev E) gives `unwrappedPhase` in radians but does NOT state the sign convention.
The default assumes ISCE3's `reference * conj(secondary)` interferogram, for which a range increase gives positive
phase. If a known subsiding basin comes out as uplift (positive), re-run with `--phase-sign -1`. Quetta should
show the valley moving away from the satellite relative to the reference; the summary prints a note if not.

## Verified vs unverified

Verified: ASF search + chain selection (live and offline), auth failure path, UTM math (vs pyproj), referencing,
plane removal, masking, summing, unit conversion, synthetic Gaussian bowl recovery, GeoTIFF/PNG/CSV writing, h5
extraction against a *fake* file with the spec layout (and a fallback layout), cached `run` end to end.
Not verified (needs login/real files): the dataset paths against a real file (taken from the product spec:
`/science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram/<POL>/{unwrappedPhase,coherenceMagnitude,connectedComponents,ionospherePhaseScreen}`,
`.../xCoordinates|yCoordinates|projection`, `.../unwrappedInterferogram/mask`, `.../frequencyA/centerFrequency`);
streaming speed via `earthaccess.open` + h5py; the phase sign; whether x/y coordinates are pixel centers (assumed);
the grid is UTM, not geographic (per spec/docs), so the script converts the AOI to UTM using the file's EPSG. If a
path is wrong the script searches dataset names automatically; use `list-h5` to inspect a real file.
