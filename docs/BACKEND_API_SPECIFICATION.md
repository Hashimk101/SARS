# Backend API Specification for Frontend & Claude

> **Project:** SAR-Pulse (NASA Space Apps 2026 — "Dancing with the SARs")  
> **Backend Framework:** FastAPI (Python 3.10+)  
> **Deployment Target:** Vercel Serverless (`/api`)  
> **Audience:** Frontend Developer & Claude Code Assistant  
> **Status:** 100% Tested & Fully Operational (24/24 Pytest Suite Passed)

---

## 1. Quick Overview & Architecture

The SAR-Pulse backend is a lightweight, zero-dependency, crash-proof **FastAPI serverless application** located in [`api/index.py`](file:///home/hashim/Data/Projects/SARS/api/index.py).

Both the frontend and backend live in the **same repository**:
* **Frontend:** Renders the interactive map of Pakistan with **4 glowing clickable dots**.
* **Backend:** Delivers structured JSON for the 4 hotspots, multi-mission satellite fusion, time-series charts, and dynamic 2026–2050 future simulations:
  1. **Region Coordinates & Metadata**
  2. **The 5-Chapter Presentation Dossier** (*Timeline $\rightarrow$ Human Pain Points $\rightarrow$ Physical Drivers $\rightarrow$ 2030 Tipping Point $\rightarrow$ Precautionary Action Plan*)
  3. **Multi-Date Temporal Time Series** for interactive graphs (Recharts / Chart.js)
  4. **Dynamic 2026–2050 Policy Simulation Engine** (Monte-Carlo 500-draw backed for Quetta)
  5. **Live NASA ASF DAAC SAR Granules & Free Satellite Tile Layers**
  6. **High-Resolution InSAR Interferograms & Flood Maps Catalog**
  7. **Web Audio Sonification Parameters** (Web Audio frequencies and waveforms)

---

## 2. The 4 Hotspots (IDs & Names)

The frontend plots these 4 points on the Pakistan map:

| Hotspot ID | Display Name | Coordinates (Lat, Lon) | Primary Phenomenon | Theme Color | Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `indus` | **Indus River Basin** | `26.85, 68.10` (Sindh/Punjab) | Monsoon Deluge & Double-Bounce Flood | `#38BDF8` (Sky) | `CRITICAL` |
| `quetta` | **Quetta Valley** | `30.175, 66.984` (Balochistan) | -15 cm/yr Aquifer Depletion Subsidence | `#F97316` (Orange) | `CRITICAL` |
| `islamabad` | **Margalla Hills & Federal Capital** | `33.729, 73.093` (Capital Zone) | Canopy Loss & Urban Sprawl Contrast | `#10B981` (Emerald) | `MODERATE` |
| `siachen` | **Siachen Glaciers** | `35.421, 77.109` (Karakoram) | Glacial Slip Velocity & GLOF Hazard | `#A855F7` (Purple) | `HIGH` |

---

## 3. Endpoints Reference

### Base URL:
* **Local Development:** `http://localhost:8000` (FastAPI direct) or `http://localhost:3000/api` (via Next/Vite proxy)
* **Vercel Production:** `https://your-app.vercel.app/api`

---

### Endpoint 1: `GET /api/health`
Health check, version verification, and mission catalog.

#### Response:
```json
{
  "status": "healthy",
  "service": "SAR-Pulse Multi-Mission Satellite Fusion API",
  "version": "2.1.0",
  "environment": "Vercel / FastAPI Serverless",
  "supported_missions": [
    "NASA-ISRO NISAR L2 GCOV (L-band Backscatter)",
    "NASA-ISRO NISAR L2 GUNW (L-band InSAR)",
    "ESA Sentinel-1 GRD / SLC (C-band SAR)",
    "NASA Alaska Satellite Facility (ASF DAAC Search API)",
    "NASA GIBS (Terra/MODIS & SNPP/VIIRS)",
    "NASA GPM IMERG Precipitation",
    "Open-Meteo Soil Moisture Telemetry"
  ],
  "active_hotspots": ["indus", "quetta", "islamabad", "siachen"]
}
```

---

### Endpoint 2: `GET /api/hotspots`
Returns the summary list of all 4 hotspots to render the dots on the Pakistan map.

#### Response:
```json
[
  {
    "id": "indus",
    "name": "Indus River Basin & Sindh-Punjab Plains",
    "location": "Sindh & Southern Punjab, Pakistan",
    "lat": 26.85,
    "lon": 68.1,
    "badge": "Monsoon Deluge & Double-Bounce Flood Inundation",
    "color": "#38bdf8",
    "severity": "CRITICAL",
    "short_desc": "Catastrophic 2022 mega-flood zone where 33 million citizens were displaced..."
  },
  ...
]
```

---

### Endpoint 3: `GET /api/hotspots/{hotspot_id}`
Returns the complete 5-chapter presentation dossier, radar HDF5 schema, live soil moisture telemetry, and live NASA ASF SAR granules.

#### Query Parameters:
* `include_live_sar` (boolean, default: `true`): Whether to fetch real-time scenes from NASA ASF DAAC.

#### Response Structure:
```json
{
  "id": "quetta",
  "name": "Quetta Valley & Zarghoon Basin",
  "coordinates": {"lat": 30.175, "lon": 66.984},
  "badge": "Active Tectonic & Groundwater Land Subsidence",
  "color": "#f97316",
  "severity": "CRITICAL",
  "scientific_context": {
    "satellite_mission": "NISAR L2 GUNW (80m unwrapped InSAR) + ESA Sentinel-1 Cross-Validation",
    "polarization_channels": "HH / InSAR Phase & Coherence",
    "hdf5_group": "/science/LSAR/GUNW/grids/frequencyA",
    "hdf5_datasets": {
      "unwrapped_phase": "/science/LSAR/GUNW/grids/frequencyA/unwrappedPhase",
      "coherence": "/science/LSAR/GUNW/grids/frequencyA/coherenceMagnitude",
      "ionospheric_phase": "/science/LSAR/GUNW/grids/frequencyA/ionosphericPhaseScreen"
    },
    "preprocessing_rule": "Combine Ascending (Track 41) and Descending (Track 92) line-of-sight geometries...",
    "physical_phenomenon": "Pumping exceeding natural recharge drops water table..."
  },
  "chapters": [
    {
      "step": 1,
      "title": "Historical Timeline: 2.7 Meters of Ground Collapse Since 2003",
      "body": "...",
      "metrics": [
        {"label": "Cumulative Sinking (2003-26)", "value": "2.7", "unit": "meters"},
        {"label": "Active Sinking Bowl Area", "value": "59.0", "unit": "sq km"},
        {"label": "City Centre Sinking Rate", "value": "-14.8", "unit": "cm/yr"},
        {"label": "NISAR vs Sentinel-1 r", "value": "0.89", "unit": "correlation"}
      ]
    },
    ... (Steps 2 to 5)
  ],
  "sonification": {
    "sound_theme": "Low Sub-Bass Rumble & Creaking Earth Tensile Strain",
    "base_frequency_hz": 65,
    "mod_frequency_hz": 1.2,
    "waveform": "triangle",
    "tension_curve": [0.2, 0.45, 0.8, 0.98, 0.5]
  },
  "live_environmental": {
    "soil_moisture_topsoil_m3m3": 0.14,
    "soil_moisture_subsurface_m3m3": 0.18,
    "current_precipitation_mm": 0.0,
    "timestamp": "2026-11-15T08:00:00Z"
  },
  "nasa_asf_granules": [
    {
      "scene_name": "S1A_IW_GRDH_1SDV_20261102T012345_...",
      "platform": "Sentinel-1 / SAR",
      "polarization": "VV+VH",
      "browse_image_url": "https://datapool.asf.alaska.edu/BROWSE/...",
      "download_url": "https://datapool.asf.alaska.edu/...",
      "file_size_mb": 924.3
    }
  ]
}
```

---

### Endpoint 4: `GET /api/hotspots/{hotspot_id}/timeline`
Returns multi-date sensor observations and radar metrics for interactive charts (Recharts, Chart.js).

#### Response Example:
```json
{
  "hotspot_id": "quetta",
  "hotspot_name": "Quetta Valley & Zarghoon Basin",
  "metric_primary": "Cumulative Sinking (cm)",
  "metric_secondary": "Vertical Subsidence Rate (cm/yr)",
  "unit_primary": "cm",
  "unit_secondary": "cm/yr",
  "series": [
    {
      "date": "2024-09-09",
      "epoch": "Sentinel-1 Ascending Base",
      "primary_val": 0.0,
      "secondary_val": -8.3,
      "coherence": 0.68,
      "groundwater_depth_m": 88.5,
      "note": "COMET LiCSAR baseline interferogram"
    },
    {
      "date": "2026-06-17",
      "epoch": "NISAR Track 41 Ascending",
      "primary_val": -15.1,
      "secondary_val": -6.6,
      "coherence": 0.82,
      "groundwater_depth_m": 94.6,
      "note": "High L-band coherence across arid valley"
    },
    {
      "date": "2026-10-18",
      "epoch": "NISAR 4-Track Combined Final",
      "primary_val": -21.4,
      "secondary_val": -8.7,
      "coherence": 0.81,
      "groundwater_depth_m": 97.2,
      "note": "Annualized median rate resolved at -8.7 cm/yr (r=0.89)"
    }
  ]
}
```

---

### Endpoint 5: `GET /api/hotspots/{hotspot_id}/future-simulation`
Dynamic multi-scenario predictive engine for the 2026–2050 timeline slider.

#### Query Parameters:
* `year` (int, `2026` to `2050`, default: `2030`)
* `scenario` (string, `current_trend`, `accelerated`, or `controlled`)

#### Response Example (`/api/hotspots/quetta/future-simulation?year=2040&scenario=controlled`):
```json
{
  "hotspot_id": "quetta",
  "year": 2040,
  "scenario": "controlled",
  "metric_projected": "Cumulative Ground Sinking",
  "median_subsidence_cm": 46.2,
  "bowl_maximum_sinking_cm": 78.6,
  "area_exceeding_1m_km2": 4.49,
  "buildings_in_damage_zone": 4200,
  "population_at_risk": 81666,
  "risk_level": "CONTROLLED",
  "damage_reduction_pct": 85.3,
  "policy_summary": "Pumping regulation and 18 delay-action recharge dams reduce structural damage by over 85%."
}
```

---

### Endpoint 6: `GET /api/hotspots/{hotspot_id}/figures`
Returns the catalog of pre-rendered high-resolution NISAR interferograms, damage zone maps, and validation charts.

#### Response Example:
```json
{
  "hotspot_id": "quetta",
  "figures": [
    {
      "id": "quetta_ifg_side_by_side",
      "title": "NISAR L-band Interferograms: 336-Day vs 132-Day Baselines",
      "description": "Direct side-by-side comparison of active radar fringe deformation over Quetta Valley...",
      "api_url": "/api/figures/quetta-check/final/moneyshot/side_by_side_336d_vs_132d.png",
      "tags": ["NISAR", "InSAR", "Interferogram", "MoneyShot"]
    },
    {
      "id": "quetta_vertical_velocity_map",
      "title": "Combined Vertical Velocity Map (Ascending + Descending)",
      "description": "Pure vertical ground sinking resolved by combining NISAR Track 41 and Track 92...",
      "api_url": "/api/figures/quetta-check/final/nisar/vertical_velocity_map.png",
      "tags": ["NISAR", "VerticalVelocity", "Decomposition"]
    }
  ]
}
```

---

### Endpoint 7: `GET /api/figures/{figure_path:path}`
Streams the high-resolution PNG image directly from disk. Protected against directory traversal.

---

### Endpoint 8: `GET /api/satellites/query?lat=...&lon=...`
Universal live coordinate query for ANY location on Earth: returns live NASA ASF DAAC granules, live Open-Meteo soil moisture, and theoretical NISAR HDF5 structures.

---

### Endpoint 9: `GET /api/satellites/layers`
Returns free satellite and dark-mode tile URLs ready for MapLibre or Leaflet:
* ESRI World Imagery
* CartoDB Dark Matter
* NASA GIBS Terra/MODIS TrueColor

---

## 4. TypeScript Interfaces (Copy directly into Frontend `types/api.ts`)

```typescript
export type HotspotId = 'indus' | 'quetta' | 'islamabad' | 'siachen';
export type ScenarioType = 'current_trend' | 'accelerated' | 'controlled';

export interface HotspotSummary {
  id: HotspotId;
  name: string;
  location: string;
  lat: number;
  lon: number;
  badge: string;
  color: string;
  severity: 'CRITICAL' | 'HIGH' | 'MODERATE';
  short_desc: string;
}

export interface MetricItem {
  label: string;
  value: string;
  unit: string;
}

export interface Chapter {
  step: number;
  title: string;
  body: string;
  metrics: MetricItem[];
}

export interface ScientificContext {
  satellite_mission: string;
  polarization_channels: string;
  hdf5_group: string;
  hdf5_datasets: Record<string, string>;
  preprocessing_rule: string;
  physical_phenomenon: string;
}

export interface SonificationParams {
  sound_theme: string;
  base_frequency_hz: number;
  mod_frequency_hz: number;
  waveform: 'sine' | 'triangle' | 'sawtooth' | 'square';
  tension_curve: number[];
}

export interface LiveEnvironmental {
  soil_moisture_topsoil_m3m3: number;
  soil_moisture_subsurface_m3m3: number;
  current_precipitation_mm: number;
  timestamp: string;
}

export interface AsfGranule {
  scene_name: string;
  platform: string;
  polarization: string;
  flight_direction: string;
  acquisition_time: string;
  browse_image_url: string | null;
  download_url: string;
  file_size_mb: number;
  orbit?: number;
}

export interface HotspotDetail {
  id: HotspotId;
  name: string;
  location: string;
  coordinates: { lat: number; lon: number };
  badge: string;
  color: string;
  severity: string;
  short_desc: string;
  scientific_context: ScientificContext;
  chapters: Chapter[];
  sonification: SonificationParams;
  live_environmental: LiveEnvironmental;
  nasa_asf_granules?: AsfGranule[];
}

export interface TimelinePoint {
  date: string;
  epoch: string;
  primary_val: number;
  secondary_val?: number;
  rainfall_gpm_mm?: number;
  dielectric_constant?: number;
  coherence?: number;
  groundwater_depth_m?: number;
  canopy_cover_pct?: number;
  surface_temp_c?: number;
  meltwater_runoff_m3s?: number;
  terminus_retreat_m?: number;
  note: string;
}

export interface HotspotTimeline {
  hotspot_id: HotspotId;
  hotspot_name: string;
  metric_primary: string;
  metric_secondary: string;
  unit_primary: string;
  unit_secondary: string;
  series: TimelinePoint[];
}

export interface FutureSimulation {
  hotspot_id: HotspotId;
  year: number;
  scenario: ScenarioType;
  metric_projected: string;
  median_subsidence_cm?: number;
  bowl_maximum_sinking_cm?: number;
  area_exceeding_1m_km2?: number;
  buildings_in_damage_zone?: number;
  population_at_risk?: number;
  ten_year_flood_probability_pct?: number;
  projected_displaced_citizens?: number;
  cumulative_forest_depletion_pct?: number;
  temperature_heat_island_anomaly_c?: number;
  cumulative_ice_volume_loss_pct?: number;
  glof_hazard_index_pct?: number;
  risk_level: string;
  damage_reduction_pct: number;
  policy_summary: string;
}

export interface FigureItem {
  id: string;
  title: string;
  description: string;
  file_path: string | null;
  api_url: string;
  tags: string[];
}
```

---

## 5. Ready-to-Use Frontend API Client (`services/api.ts`)

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchAllHotspots(): Promise<HotspotSummary[]> {
  const res = await fetch(`${BASE_URL}/api/hotspots`);
  if (!res.ok) throw new Error('Failed to load hotspots summary');
  return res.json();
}

export async function fetchHotspotDetail(id: HotspotId): Promise<HotspotDetail> {
  const res = await fetch(`${BASE_URL}/api/hotspots/${id}`);
  if (!res.ok) throw new Error(`Failed to load details for ${id}`);
  return res.json();
}

export async function fetchHotspotTimeline(id: HotspotId): Promise<HotspotTimeline> {
  const res = await fetch(`${BASE_URL}/api/hotspots/${id}/timeline`);
  if (!res.ok) throw new Error(`Failed to load timeline for ${id}`);
  return res.json();
}

export async function fetchFutureSimulation(
  id: HotspotId, 
  year: number, 
  scenario: ScenarioType
): Promise<FutureSimulation> {
  const res = await fetch(`${BASE_URL}/api/hotspots/${id}/future-simulation?year=${year}&scenario=${scenario}`);
  if (!res.ok) throw new Error(`Failed to run simulation for ${id}`);
  return res.json();
}

export async function fetchHotspotFigures(id: HotspotId): Promise<{ hotspot_id: HotspotId; figures: FigureItem[] }> {
  const res = await fetch(`${BASE_URL}/api/hotspots/${id}/figures`);
  if (!res.ok) throw new Error(`Failed to load figures for ${id}`);
  return res.json();
}
```
