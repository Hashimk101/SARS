# SAR Signal Processing & Physical Interpretation Rules

## 1. Mandatory Preprocessing Pipeline (Raw $\gamma^0$ to Web-Ready Tiles)
Raw `GCOV` arrays (`HHHH`, `HVHV`) store linear backscatter power values (mostly between `0.0001` and `1.0`). Plotting raw linear values produces an almost pitch-black image with a few white speckles. Always execute these 3 steps:

### Step 1: Speckle Filtering (Noise Reduction)
- Radar interference causes salt-and-pepper granular speckle noise.
- Apply a spatial **Lee Filter**, **Refined Lee Filter**, or **Boxcar/Median Filter** (e.g., $3 \times 3$ or $5 \times 5$ window) on linear power *before* decibel conversion.
- Preserves radiometric boundaries while smoothing granular noise.

### Step 2: Decibel ($dB$) Conversion
$$\gamma^0_{dB} = 10 \cdot \log_{10}(\gamma^0_{linear})$$
- Typical dynamic range to clip and stretch for visualization:
  - **Co-polarization (`HH` / `VV`):** `-25 dB` (dark/smooth) to `0 dB` (bright/rough or double-bounce).
  - **Cross-polarization (`HV` / `VH`):** `-30 dB` to `-5 dB` (vegetation volume scattering).

### Step 3: Reprojection to Web Mercator (`EPSG:3857`) or WGS84 (`EPSG:4326`)
- Convert processed arrays to **Cloud-Optimized GeoTIFFs (COGs)** or lightweight PNG/WebP overlays with precise georeferenced bounding boxes for frontend map rendering (Leaflet, MapLibre GL, Deck.gl).

---

## 2. False-Color Composite (FCC) Recipes for Instant Storytelling
Never show judges plain grayscale radar when a false-color composite reveals physical scattering mechanisms immediately:

### A. Standard Dual-Pol Land/Water/Vegetation RGB (Static / Single Date)
- **Red:** `HH` (or `VV`) in dB — highlights bare soil, urban structures, double-bounce.
- **Green:** `HV` (or `VH`) in dB — highlights volume scattering (forests, dense crops).
- **Blue:** `HH - HV` in dB (which mathematically equals the ratio $HH/HV$ in linear power) — highlights open water and very smooth surfaces.

**Visual Legend for Users & Judges:**
- **Green:** Dense forest / healthy crops (high volume depolarizing backscatter)
- **Dark Blue / Black:** Calm open water / asphalt (smooth specular reflection away from sensor)
- **Bright Pink / White:** Urban buildings or flooded tree trunks (strong double-bounce)
- **Purple / Magenta:** Rough bare soil / rocky terrain

### B. Multi-Temporal Change Detection RGB (Before vs. After)
- **Red:** Date 1 (`Before` backscatter in dB)
- **Green:** Date 2 (`After` backscatter in dB)
- **Blue:** Date 2 (`After` backscatter in dB)

**Visual Legend for Users & Judges:**
- **Grayscale (Neutral):** No significant change between dates.
- **Bright Red:** Backscatter *dropped* (e.g., land submerged by open water flood, forest cleared/burned).
- **Bright Cyan (Green + Blue):** Backscatter *increased* (e.g., floodwaters receded exposing rough mud, new urban construction, flooded forest double-bounce, crop emergence).

---

## 3. Physical Drivers Cheat Sheet (For UI Tooltips & Judge Q&A)

### Open Water Floods (Specular Reflection)
- Smooth water acts like a mirror, reflecting radar pulses away from the antenna.
- Result: Sharp drop in `HH` and `VV` backscatter ($< -20\text{ dB}$).

### Flooded Forests / Wetlands / Rice Paddies (Double-Bounce Scattering)
- Radar bounces off flat, high-dielectric water, strikes vertical tree trunks or crop stems, and reflects straight back into the satellite antenna.
- Result: Dramatic *increase* in `HH` backscatter ($> -5\text{ dB}$), while cross-pol `HV` stays moderate.
- *Why NISAR L-Band wins:* 24 cm wavelength penetrates dense forest canopy to reach the water-trunk interface beneath the trees, where optical sensors (Sentinel-2, Landsat) see only leaves and clouds.

### Wildfire Burn Scars (Canopy Loss & Moisture Drop)
- Fire destroys the leafy canopy (volume scatterers) and dries out the topsoil.
- Result: Sharp drop in cross-pol `HV`, accompanied by an increase in the $HH/HV$ ratio.

### Soil Moisture Changes (Dielectric Constant Variation)
- Liquid water has a dielectric constant ($\varepsilon \approx 80$) compared to dry soil ($\varepsilon \approx 3 - 5$).
- As soil moisture increases, surface reflectivity rises, increasing co-pol backscatter ($HH$/$VV$) by $3\text{ to }6\text{ dB}$ even if surface roughness remains unchanged.

### Land Subsidence & Earthquakes (`GUNW` InSAR Phase)
- Unwrapped interferometric phase change $\Delta \phi$ converts to line-of-sight displacement $d$ via:
  $$d = \frac{\lambda \cdot \Delta \phi}{4\pi}$$
  where $\lambda = 0.24\text{ m}$ ($24\text{ cm}$) for NISAR L-band.
- Positive phase change indicates uplift / movement towards satellite; negative phase indicates subsidence / retreat.
