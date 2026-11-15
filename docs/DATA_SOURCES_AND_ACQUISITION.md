# Data Sources & Acquisition Playbook

## 1. Primary NISAR Repositories

### A. Alaska Satellite Facility (ASF) DAAC
The primary NASA distribution hub for NISAR L-band and S-band products.
- **Web Portal:** [ASF Vertex](https://search.asf.alaska.edu/)
- **Python Client:** `asf_search` (`pip install asf_search`)
- **Authentication:** NASA Earthdata Login account.
  Configure in `~/.netrc`:
  ```
  machine urs.earthdata.nasa.gov
      login <YOUR_EARTHDATA_USERNAME>
      password <YOUR_EARTHDATA_PASSWORD>
  ```
- **NISAR Search Parameters:**
  - `platform`: `asf.PLATFORM.NISAR`
  - `processingLevel`: `'GCOV'` (Geocoded Polarimetric Covariance) or `'GUNW'` (Geocoded Unwrapped Interferograms)
  - `beamMode`: Dual-pol (`DHDH`, `DVDV`) or Quad-pol (`FP`)
  - `flightDirection`: `'ASCENDING'` or `'DESCENDING'` (keep consistent for change detection!)

### B. ISRO Bhoonidhi Portal
The Indian Space Research Organisation (ISRO) data dissemination portal for NISAR S-band and L-band joint observations.
- **Web Portal:** [Bhoonidhi Open Data](https://bhoonidhi.nrsc.gov.in/)
- **Usage:** Ideal for secondary S-band validation or South Asia specific acquisitions.

---

## 2. Ancillary & Fusion Datasets (NASA Scoring Criterion: "Deep Integration")
To score 5/5 on the **Relevance** and **Impact** rubric, fuse NISAR radar observations with at least one complementary data layer:

| Dataset | Provider | Purpose in Project | Access Link |
| :--- | :--- | :--- | :--- |
| **Sentinel-2 L2A** | ESA / Copernicus | Cloud-free optical comparison (shows NISAR piercing clouds) | [Copernicus Browser](https://browser.dataspace.copernicus.eu/) |
| **Copernicus DEM (GLO-30) / SRTM** | ESA / NASA | Topography, slope & flood accumulation modeling | [OpenTopography](https://portal.opentopography.org/) |
| **NASA GPM IMERG** | NASA GES DISC | Extreme rainfall timeline triggering surface water surge | [NASA Earthdata GES DISC](https://disc.gsfc.nasa.gov/) |
| **WorldPop / GHSL** | WorldPop / JRC | Population density layer showing human flood exposure | [WorldPop Hub](https://www.worldpop.org/) |
| **HydroSHEDS** | WWF / USGS | River networks, basins & flow direction | [HydroSHEDS](https://www.hydrosheds.org/) |

---

## 3. High-Impact Study Regions & Bounding Boxes

Selecting an area with dramatic dynamic change guarantees high visual and scientific impact:

### Option 1: Indus River Basin Monsoon Floods & Agricultural Pulse (Pakistan)
- **Bounding Box (WGS84):** `[67.5, 24.5, 70.0, 28.5]` (Sindh / Punjab corridor)
- **Physical Phenomenon:** Massive seasonal flood inundation, dynamic wetland expansion, crop cycles (rice paddies to bare soil).
- **Why it Wins:**
  - Clear double-bounce response over flooded agricultural vegetation.
  - Huge societal impact for disaster resilience and food security.
  - Both L-band and S-band frequent coverage.

### Option 2: Brahmaputra River Basin & Kaziranga Wetlands (India / Assam)
- **Bounding Box (WGS84):** `[92.5, 26.0, 94.5, 27.5]`
- **Physical Phenomenon:** Annual monsoon inundation of endangered wildlife habitats, braided river migration, wetland dynamics.
- **Why it Wins:** Strong environmental conservation angle, high contrast between open water, dense riparian canopy, and flooded grass.

### Option 3: Lake Mead & Colorado River Reservoir Fluctuations (USA)
- **Bounding Box (WGS84):** `[-114.9, 35.8, -114.2, 36.5]`
- **Physical Phenomenon:** Water level retreat exposing bathtub rings of dry mineral soil; local surface subsidence measured by `GUNW`.
- **Why it Wins:** High public familiarity, clear dielectric change between deep water and exposed dry land.

### Option 4: Pantanal / Amazon Wetland & Deforestation Pulse (Brazil)
- **Bounding Box (WGS84):** `[-58.0, -18.0, -55.0, -15.5]`
- **Physical Phenomenon:** Largest tropical wetland in the world; seasonal floodpulse beneath dense forest canopy.
- **Why it Wins:** Demonstrates L-band's unique 24 cm wavelength penetration through dense forest canopies where optical satellites see only green leaves.

---

## 4. Real Satellite Data & Proxy Archives (Where to Get Imagery Now)

Since NISAR is NASA's newest flagship, the NASA challenge explicitly encourages teams to utilize proven operational satellites as proxies and complementary verification sources:

### A. Sentinel-1 SAR (C-Band Synthetic Aperture Radar — 10 Years of Data!)
The closest operational sibling to NISAR. Free, open, and covers Pakistan every 6 to 12 days since 2014.
- **Provider:** European Space Agency (ESA) & NASA ASF DAAC.
- **Product Type:** `GRD` (Ground Range Detected, High Resolution).
- **Polarizations:** Dual-pol `VV + VH` (or `HH + HV`).
- **How to Download via Python:**
  ```python
  import asf_search as asf
  results = asf.search(
      platform=asf.PLATFORM.SENTINEL1,
      processingLevel='GRD_HD',
      intersectsWith='POLYGON((67.5 25.5, 69.8 25.5, 69.8 28.5, 67.5 28.5, 67.5 25.5))',
      start='2022-08-15T00:00:00Z',
      end='2022-09-05T23:59:59Z'
  )
  print(f"Found {len(results)} real SAR scenes for Pakistan floods!")
  # results.download(path='./data/sar_granules')
  ```

### B. Sentinel-2 (High-Resolution 10m Optical Satellite Imagery)
- **Use in App:** Provides the "Cloudy Optical" side of the split-screen swipe slider to prove how clouds blind optical sensors while radar pierces through.
- **Access Portal:** [Copernicus Data Space Browser](https://browser.dataspace.copernicus.eu/)
- **Direct GeoTIFF Downloads:** AWS Open Data `s3://sentinel-s2-l2a/`.

### C. NASA GIBS (Global Imagery Browse Services — 100% Free Live Tile Streaming!)
NASA operates a free, public tile API that delivers real daily satellite imagery across the globe. You can plug these directly into Leaflet or MapLibre:
- **MODIS Terra True-Color Imagery (August 2022 Pakistan Floods):**
  `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2022-08-30/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`
- **VIIRS Nighttime Day/Night Band (Nighttime Surface Lights):**
  `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_DayNightBand_AtSensor_M15/default/2022-08-30/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg`

---

## 5. Free Satellite Basemap APIs for the Web Frontend (Zero API Key Needed)

Claude and the frontend developer can use these URLs directly inside Leaflet or MapLibre:

| Map Style | Tile URL Template | Attribution |
| :--- | :--- | :--- |
| **ESRI High-Res Satellite** | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | Esri, Maxar, Earthstar Geographics |
| **CartoDB Dark Matter** | `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png` | CartoDB & OpenStreetMap |
| **OpenStreetMap Standard** | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` | OpenStreetMap contributors |
| **NASA GIBS TrueColor** | `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2022-08-30/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg` | NASA Earthdata GIBS |
