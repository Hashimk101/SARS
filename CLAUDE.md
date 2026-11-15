# CLAUDE.md — AI Coding Assistant Guidelines for "Dancing with the SARs"

## 1. Project Mission & Identity
You are assisting in building the award-winning entry for **NASA Space Apps 2026 — "Dancing with the SARs"**.
The application is an interactive radar remote sensing platform utilizing **NASA-ISRO Synthetic Aperture Radar (NISAR)** data to track, visualize, and explain Earth surface changes (floods, agriculture, wetlands, subsidence) over time.

---

## 2. Mandatory Scientific & Technical Ground Truths
Any code, visualization, or mathematical formula you generate MUST adhere strictly to these rules:

1. **Exact NISAR L2 GCOV HDF5 Paths (Zero Hallucination):**
   - Projection EPSG: `/science/LSAR/GCOV/grids/frequencyA/projection`
   - X coordinates: `/science/LSAR/GCOV/grids/frequencyA/xCoordinates`
   - Y coordinates: `/science/LSAR/GCOV/grids/frequencyA/yCoordinates`
   - Co-pol backscatter: `/science/LSAR/GCOV/grids/frequencyA/HHHH`
   - Cross-pol backscatter: `/science/LSAR/GCOV/grids/frequencyA/HVHV`
   - Data mask: `/science/LSAR/GCOV/grids/frequencyA/mask`
   *(Replace `LSAR` with `SSAR` for ISRO S-band).*

2. **Mandatory 3-Step Preprocessing Pipeline:**
   - Raw linear power $\gamma^0$ ($0.0001$ to $1.0$) must be filtered for speckle (Lee filter) **before** dB conversion.
   - Decibel formula: $\gamma^0_{dB} = 10 \cdot \log_{10}(\gamma^0_{linear})$.
   - Dynamic range clipping: `-25 dB` to `0 dB` for `HH`, `-30 dB` to `-5 dB` for `HV`.
   - Never mix `PROVISIONAL` and `VALIDATED` maturity files in a single temporal series.

3. **Physics of SAR Scattering:**
   - **Calm Water:** Specular reflection away from sensor $\rightarrow$ very low backscatter ($< -20\text{ dB}$).
   - **Flooded Forest / Stems:** Double-bounce reflection $\rightarrow$ dramatic spike in `HH` ($> -5\text{ dB}$).
   - **Vegetation Canopy:** Depolarizing volume scattering $\rightarrow$ high `HV`.
   - **Dielectric Constant:** Water presence ($\varepsilon \approx 80$) increases reflectivity by $3\text{--}6\text{ dB}$ over dry soil ($\varepsilon \approx 3\text{--}5$).

4. **Architecture Philosophy:**
   - Pre-compute heavy HDF5 array science on the Python backend into lightweight COGs / PNG overlays / GeoJSON metrics.
   - Stream instantaneous 60fps visuals on the React / MapLibre / Leaflet frontend. Never parse gigabyte HDF5 files inside the browser client.

---

## 3. Project Documentation Index
Consult these documentation files in `docs/` before generating code:
- [`docs/BACKEND_API_SPECIFICATION.md`](file:///home/hashim/Data/Projects/SARS/docs/BACKEND_API_SPECIFICATION.md): **FRONTEND DEVELOPER & CLAUDE GUIDE:** Complete FastAPI endpoints, JSON contracts, and TypeScript interfaces for the 4 Pakistan map dots.
- [`docs/PROJECT_BLUEPRINT_AND_SYSTEM_ARCHITECTURE.md`](file:///home/hashim/Data/Projects/SARS/docs/PROJECT_BLUEPRINT_AND_SYSTEM_ARCHITECTURE.md): Complete project blueprint, Pakistan study area, and 3-act workflow.
- [`docs/CHALLENGE_BRIEF_AND_RUBRIC.md`](file:///home/hashim/Data/Projects/SARS/docs/CHALLENGE_BRIEF_AND_RUBRIC.md): NASA scoring rubric & 5 evaluation criteria.
- [`docs/NISAR_DATA_ARCHITECTURE_2026.md`](file:///home/hashim/Data/Projects/SARS/docs/NISAR_DATA_ARCHITECTURE_2026.md): Complete 2026 data specs, HDF5 hierarchy, and search parameters.
- [`docs/SAR_PHYSICS_AND_ALGORITHMS.md`](file:///home/hashim/Data/Projects/SARS/docs/SAR_PHYSICS_AND_ALGORITHMS.md): False-color RGB composite recipes, speckle math, and physical drivers.
- [`docs/RECOMMENDED_TECH_STACK.md`](file:///home/hashim/Data/Projects/SARS/docs/RECOMMENDED_TECH_STACK.md): System architecture and folder structure.
- [`docs/DATA_SOURCES_AND_ACQUISITION.md`](file:///home/hashim/Data/Projects/SARS/docs/DATA_SOURCES_AND_ACQUISITION.md): ASF download scripts, satellite imagery tile APIs, and bounding boxes.
- [`docs/BEST_CODING_PRACTICES.md`](file:///home/hashim/Data/Projects/SARS/docs/BEST_CODING_PRACTICES.md): Python chunking, coordinate transformations, and frontend design standards.
- [`docs/AI_AGENT_HACKATHON_PLAYBOOK.md`](file:///home/hashim/Data/Projects/SARS/docs/AI_AGENT_HACKATHON_PLAYBOOK.md): AI agent hackathon rules (zero placeholders, fail-safe fallbacks, 60fps HUD).
- [`docs/PROMPT_TEMPLATES_FOR_AGENTS.md`](file:///home/hashim/Data/Projects/SARS/docs/PROMPT_TEMPLATES_FOR_AGENTS.md): Ready-to-copy prompts to scaffold components & scripts in 1 shot.
- [`.cursorrules`](file:///home/hashim/Data/Projects/SARS/.cursorrules) & [`.github/copilot-instructions.md`](file:///home/hashim/Data/Projects/SARS/.github/copilot-instructions.md): IDE & GitHub Copilot agent directives.

---

## 4. Backend Endpoints for Frontend (FastAPI at `/api`)
- `GET /api/health`: Health status, version (`2.1.0`), and supported satellite missions.
- `GET /api/hotspots`: Returns the 4 Pakistan dots to plot on the map:
  - `indus` (Lat: 26.85, Lon: 68.10) — Sky `#38BDF8`
  - `quetta` (Lat: 30.175, Lon: 66.984) — Orange `#F97316`
  - `islamabad` (Lat: 33.729, Lon: 73.093) — Emerald `#10B981`
  - `siachen` (Lat: 35.421, Lon: 77.109) — Purple `#A855F7`
- `GET /api/hotspots/{id}`: Returns the complete 5-chapter presentation dossier (`timeline`, `pain_points`, `drivers`, `tipping_point_2030`, `precautionary_measures`), radar telemetry metrics ($HH, HV, \varepsilon$), live soil moisture, live NASA ASF SAR granules, and Web Audio sonification parameters.
- `GET /api/hotspots/{id}/timeline`: Multi-date sensor time series for plotting interactive graphs (Recharts / Chart.js).
- `GET /api/hotspots/{id}/future-simulation?year=...&scenario=...`: Dynamic 2026–2050 scenario engine (`current_trend`, `accelerated`, `controlled`) with Monte-Carlo 500-draw data for Quetta.
- `GET /api/hotspots/{id}/figures`: Catalog of pre-rendered high-res NISAR interferograms, damage zones, and flood maps.
- `GET /api/figures/{figure_path}`: Direct PNG/JPEG image streamer from repository assets.
- `GET /api/satellites/query?lat=...&lon=...`: Universal coordinate query for any location on Earth.
- `GET /api/satellites/layers`: Free tile layers for map basemaps (ESRI, CartoDB, NASA GIBS).

---

## 5. Free Satellite Tile APIs for the Map
Use these free tile URLs directly in Leaflet / MapLibre (no API key needed):
- **Satellite Basemap (ESRI World Imagery):**  
  `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`
- **Dark Mode Tactical Basemap (CartoDB Dark Matter):**  
  `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
- **NASA GIBS True-Color Satellite Imagery (Daily Terra/MODIS):**  
  `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2022-08-30/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`

---

## 4. Key Deliverable Pillars for Maximum Score
- **Interactive Split Slider:** Swipe between pre- and post-event dates or NISAR SAR vs cloudy optical imagery.
- **Polarization Switcher:** Toggle `HH`, `HV`, `Dual-Pol RGB`, and `Change Detection`.
- **Pixel Time-Series & Sonification:** Click on any location to view the dB temporal graph and hear its radar acoustic signature ("Dancing with the SARs").
- **Guided Story Mode:** 4-5 narrative stops explaining what happened on Earth's surface and the radar physics behind it.
