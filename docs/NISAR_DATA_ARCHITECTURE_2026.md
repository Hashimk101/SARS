# NISAR 2026 Mission & Data Technical Reference

## 1. Mission Status & 2026 Release Context
- **Launch Date:** July 30, 2025.
- **Operational Data Availability (2026):**
  - **L-Band SAR (NASA - 24 cm wavelength, 1.257 GHz):** Provisional calibrated collections (`NISAR_L2_GCOV_PROVISIONAL_V1`) released starting July 2026 covering acquisitions from June 17, 2026 onward, alongside Validated collections (`NISAR_L2_GCOV_V1`). Penetrates forest canopies and dry soil.
  - **S-Band SAR (ISRO - 10 cm wavelength, 3.2 GHz):** Released July 24, 2026 (Baseline v1.4.0) via ISRO's Bhoonidhi portal and NASA ASF. Sensitive to crops, surface roughness, and snow/ice.
- **CRITICAL DATA HYGIENE RULE:** Never mix `PROVISIONAL` and `VALIDATED` maturity products in the same time-series change detection, as calibration algorithm updates between versions can create false change artifacts.

## 2. Product Levels Breakdown
- **DO NOT USE Level 0 (`RRSD`) or Level 1 (`RSLC`, `RIFG`, `RUNW`, `ROFF`):**
  - These are in unprojected Range-Doppler slant geometry.
  - They will not align on web maps (Leaflet/Mapbox/Deck.gl) without heavy orbital terrain-correction pipelines.
- **USE Level 2 Geocoded Products (Projected onto UTM / Polar Stereographic grids):**
  1. **`GCOV` (Geocoded Polarimetric Covariance) — PRIMARY CHOICE:** Radiometrically terrain-corrected (RTC) backscatter in $\gamma^0$ (gamma-naught) linear power. Ready for flood mapping, deforestation, agriculture, and urban change.
  2. **`GUNW` (Geocoded Unwrapped Interferogram) — FOR DEFORMATION:** 80m posting differential phase. Measures centimeter-scale vertical/line-of-sight ground displacement (earthquakes, subsidence, volcanoes).
  3. **`SME2` (Level 3 Soil Moisture):** 200m gridded volumetric soil moisture over non-urban/non-ice land.

## 3. Exact HDF5 (`.h5`) Internal Structure for `NISAR L2 GCOV`
NISAR products are distributed as HDF5 files. When reading with Python (`h5py`, `rioxarray`, or `GDAL`), access layers using these exact paths:

- **Coordinate Reference System (CRS) & Grid:**
  - `/science/LSAR/GCOV/grids/frequencyA/projection` (EPSG code, e.g., UTM zone)
  - `/science/LSAR/GCOV/grids/frequencyA/xCoordinates` (1D array, meters)
  - `/science/LSAR/GCOV/grids/frequencyA/yCoordinates` (1D array, meters)

- **Backscatter Covariance Terms (Linear $\gamma^0$ power):**
  - `/science/LSAR/GCOV/grids/frequencyA/HHHH` (Co-pol Horizontal backscatter: $S_{hh} \cdot S_{hh}^*$)
  - `/science/LSAR/GCOV/grids/frequencyA/HVHV` (Cross-pol backscatter: $S_{hv} \cdot S_{hv}^*$)
  - `/science/LSAR/GCOV/grids/frequencyA/VVVV` (Co-pol Vertical backscatter — if acquired in dual/quad-pol mode: $S_{vv} \cdot S_{vv}^*$)
  - `/science/LSAR/GCOV/grids/frequencyA/mask` (Valid data & water/layover shadow mask)

*(Note: For S-band products, replace `LSAR` with `SSAR`.)*

## 4. Programmatic Search & Download (`asf_search`)
```python
import asf_search as asf

# Search for NISAR L2 GCOV products over an Area of Interest (AOI)
results = asf.search(
    platform=[asf.PLATFORM.NISAR],
    processingLevel='GCOV',
    intersectsWith='POLYGON((72.8 33.4, 73.3 33.4, 73.3 33.9, 72.8 33.9, 72.8 33.4))',
    start='2026-06-17T00:00:00Z',
    end='2026-11-10T23:59:59Z'
)

print(f"Found {len(results)} scenes.")
# Download requires ~/.netrc configured with NASA Earthdata credentials
# results.download(path='./data/nisar_gcov')
```

## 5. File Naming Convention
A standard NISAR L2 GCOV file adheres to:
`NISAR_L2_PR_GCOV_001_005_A_045_2000_DHDH_A_20260715T120000_20260715T120035_P01101_F_N_J_001.h5`
- `NISAR`: Mission identifier
- `L2`: Product processing level
- `PR` / `VA`: Provisional vs Validated data maturity
- `GCOV`: Product type (Geocoded Covariance)
- `DHDH`: Dual-pol (Horizontal transmit, Dual receive)
- Timestamp strings: Start and end acquisition times in UTC
