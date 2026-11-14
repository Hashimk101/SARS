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

## 4. Synthetic / Mock Data Strategy (Zero-Blocker Development)
If live NISAR 2026 granules are undergoing calibration reprocessing or ASF download speeds are constrained during the hackathon:
- **Use Sentinel-1 GRD or ALOS-2 PALSAR-2 as proxy:** Convert dual-pol SAR data into NISAR L2 GCOV-equivalent HDF5 structure using the provided preprocessing script.
- Ensure the frontend and scientific calculations remain 100% compliant with NISAR GCOV HDF5 layer specifications.
