# Backend API Specification for Frontend & Claude

> **Project:** SAR-Pulse (NASA Space Apps 2026)  
> **Backend Framework:** FastAPI (Python 3.10+)  
> **Deployment Target:** Vercel Serverless (`/api`)  
> **Audience:** Frontend Developer & Claude Code Assistant

---

## 1. Quick Overview & Architecture

To keep the hackathon prototype **fast, lightweight, and 100% crash-proof on Vercel**, the backend is built using **FastAPI** running as a Vercel Serverless Function inside `/api/index.py`.

Both the frontend (React/Next.js/Vite) and backend live in the **same repository**:
* **Frontend:** Renders the interactive map of Pakistan with **4 clickable glowing dots**.
* **Backend:** Delivers structured JSON for the 4 hotspots upon user click, containing:
  1. **Region Coordinates & Metadata**
  2. **The 5-Step Presentation Dossier** (*Timeline $\rightarrow$ Human Pain Points $\rightarrow$ Physical Drivers $\rightarrow$ 2030 Tipping Point $\rightarrow$ Precautionary Action Plan*)
  3. **Radar Telemetry Metrics** ($HH$, $HV$, Ratio, Dielectric $\varepsilon$, Scattering regime)
  4. **Audio Sonification Parameters** (Web Audio frequencies and waveforms)

---

## 2. The 4 Hotspots (IDs & Names)

The frontend should plot these 4 points on the Pakistan map using their latitude and longitude:

| Hotspot ID | Display Name | Coordinates (Lat, Lon) | Primary Phenomenon | Theme Color |
| :--- | :--- | :--- | :--- | :--- |
| `indus` | **Indus River Basin** | `26.85, 68.12` (Dadu / Manchar) | Sub-Canopy Crop Flooding | `#00F0FF` (Cyan) |
| `quetta` | **Quetta Valley** | `30.18, 67.01` (Sariab / Chiltan) | 15 cm/yr Groundwater Subsidence | `#F59E0B` (Amber) |
| `islamabad` | **Islamabad & Margalla** | `33.72, 73.06` (E-11 / Nullah Lai) | Mountain Canopy Loss & Flash Flood | `#10B981` (Emerald) |
| `siachen` | **Siachen Glaciers** | `35.42, 77.10` (Karakoram) | Cryosphere Melt & GLOF | `#38BDF8` (Sky Blue) |

---

## 3. Endpoints Reference

### Base URL:
* **Local Development:** `http://localhost:8000` (FastAPI direct) or `http://localhost:3000/api` (via Next/Vite proxy)
* **Vercel Production:** `https://your-app.vercel.app/api`

---

### Endpoint 1: `GET /api/hotspots`
Returns the summary list of all 4 hotspots to render the dots on the Pakistan map.

#### Response Example:
```json
[
  {
    "id": "indus",
    "name": "Indus River Basin",
    "location": "Sindh (Dadu / Manchar Lake)",
    "lat": 26.85,
    "lon": 68.12,
    "badge": "SUB-CANOPY DOUBLE-BOUNCE DELUGE",
    "color": "#00F0FF",
    "severity": "CRITICAL",
    "short_desc": "Submerged staple crops and 33M citizens impacted by monsoon deluge."
  },
  {
    "id": "quetta",
    "name": "Quetta Valley",
    "location": "Balochistan (Sariab / Chiltan)",
    "lat": 30.18,
    "lon": 67.01,
    "badge": "15 CM/YR SINKING VOID",
    "color": "#F59E0B",
    "severity": "CRITICAL",
    "short_desc": "Catastrophic aquifer over-extraction causing active ground fissures."
  },
  {
    "id": "islamabad",
    "name": "Islamabad & Margalla Hills",
    "location": "Federal Territory (E-11 / Nullah Lai)",
    "lat": 33.72,
    "lon": 73.06,
    "badge": "CANOPY LOSS & FLASH CHOKE",
    "color": "#10B981",
    "severity": "HIGH",
    "short_desc": "Mountain forest clearing and ravine encroachment causing urban flash floods."
  },
  {
    "id": "siachen",
    "name": "Siachen & Karakoram Glaciers",
    "location": "Gilgit-Baltistan (Third Pole)",
    "lat": 35.42,
    "lon": 77.10,
    "badge": "CRYOSPHERE SURGE & GLOF",
    "color": "#38BDF8",
    "severity": "CRITICAL",
    "short_desc": "Accelerated glacial retreat threatening 75% of national river inflow."
  }
]
```

---

### Endpoint 2: `GET /api/hotspots/{id}`
**Trigger:** Called when the user clicks **any of the 4 dots** on the map.  
**Returns:** The complete presentation-mode dataset for that region.

#### Path Parameter:
* `id` (string): `"indus"`, `"quetta"`, `"islamabad"`, or `"siachen"`.

#### Response Example (`GET /api/hotspots/quetta`):
```json
{
  "id": "quetta",
  "name": "Quetta Valley",
  "location": "Balochistan (Sariab / Chiltan)",
  "badge": "15 CM/YR SINKING VOID",
  "coordinates": {
    "lat": 30.18,
    "lon": 67.01,
    "zoom": 11.5
  },
  "radar_telemetry": {
    "hh_backscatter": "-2.1 dB (WALL REFLECTION)",
    "hv_backscatter": "-24.6 dB (BARE ROCK)",
    "ratio_hh_hv": "+22.5 dB (FISSURE ANOMALY)",
    "dielectric_constant": "3.2 (DESICCATED CLAY)",
    "scattering_regime": "INSAR PHASE INTERFEROGRAM (15 CM/YR SUBSIDENCE)",
    "gpm_rain_30d": "12 mm (SEVERE METEOROLOGICAL DROUGHT)",
    "oco_carbon_flux": "NEUTRAL / BIOMASS COLLAPSE"
  },
  "sonification": {
    "base_freq_hz": 180,
    "waveform": "sawtooth",
    "pitch_slide": "DOWNWARD_SLIDE",
    "description": "Subterranean groaning sub-bass slide sonifying land collapse."
  },
  "story_chapters": [
    {
      "step": 1,
      "tag": "TIMELINE",
      "title": "1. The InSAR Fringe Timeline (2016 – 2026)",
      "milestones": [
        {"period": "2016 - 2018", "event": "Tubewell boom; groundwater table drops 2m/year. Early InSAR shows 4 cm/yr subsidence."},
        {"period": "2020 - 2023", "event": "Cumulative deficit collapses fine clay matrix. Sinking accelerates to 12 cm/year."},
        {"period": "2026 (NISAR Baseline)", "event": "Concentric InSAR fringes confirm peak subsidence of 16.6 cm/year; earth fissures split Sariab Road."}
      ]
    },
    {
      "step": 2,
      "tag": "HUMAN_PAIN",
      "title": "2. The Human Tragedy & Pain Points",
      "headline": "Homes Tearing in Half & The Race for Water",
      "emotional_summary": "Families in Killi Gul Muhammad wake up to earth fissures tearing through living room floors. Over 1,200 homes are structurally condemned. Wells drilled past 1,200 feet strike dry bedrock, forcing families to spend 40% of their income on private water tankers.",
      "stats": [
        {"label": "Condemned Homes", "value": "1,200+"},
        {"label": "Water Table Drop", "value": "-6m / year"},
        {"label": "Affected Population", "value": "3.2 Million"}
      ]
    },
    {
      "step": 3,
      "tag": "DRIVERS",
      "title": "3. What Caused It (Physical & Human Drivers)",
      "drivers": [
        {
          "type": "PHYSICAL",
          "title": "Aquifer Pore Depressurization",
          "desc": "Pumping out deep water removes the buoyant hydraulic pressure holding clay silt grains apart, causing permanent compaction."
        },
        {
          "type": "HUMAN",
          "title": "8,000+ Unregulated Solar Tubewells",
          "desc": "Subsidized electricity and cheap solar pumps created continuous 16-hour/day uncontrolled extraction with zero metering."
        }
      ]
    },
    {
      "step": 4,
      "tag": "TIPPING_POINT",
      "title": "4. The 2030 Tipping Point (Day Zero)",
      "warning": "DAY ZERO: Aquifer Bedrock Strike (2028-2030)",
      "consequences": [
        "Complete drinking water collapse for 3.2M residents.",
        "Runway shear and structural closure of Quetta International Airport.",
        "Differential subsidence severing the critical Quetta-Rohri rail lifeline."
      ],
      "economic_impact": "$1.4 Billion in structural infrastructure destruction."
    },
    {
      "step": 5,
      "tag": "ACTION_PLAN",
      "title": "5. Precautionary Action & Survival Blueprint",
      "measures": [
        {
          "priority": "IMMEDIATE",
          "title": "Mandatory Tubewell Moratorium & Smart Metering",
          "desc": "Enforce immediate bans on new agricultural tube wells in the central cone of depression."
        },
        {
          "priority": "HIGH",
          "title": "InSAR-Guided Infiltration Check Dams",
          "desc": "Construct 40+ percolation delay check dams across Chiltan mountain streams to force flash rainwater into deep aquifers."
        },
        {
          "priority": "LONG_TERM",
          "title": "Mangi Dam & Indus Bulk Water Pipeline",
          "desc": "Accelerate surface water piped supply from Mangi Dam to replace groundwater dependency before 2028."
        }
      ]
    }
  ]
}
```

---

## 4. TypeScript Interfaces for Claude & Frontend

Claude and the frontend teammate can copy-paste these types directly into their codebase (`web/src/types/hotspot.ts`):

```typescript
export type HotspotId = 'indus' | 'quetta' | 'islamabad' | 'siachen';

export interface HotspotSummary {
  id: HotspotId;
  name: string;
  location: string;
  lat: number;
  lon: number;
  badge: string;
  color: string;
  severity: 'CRITICAL' | 'HIGH';
  short_desc: string;
}

export interface RadarTelemetry {
  hh_backscatter: string;
  hv_backscatter: string;
  ratio_hh_hv: string;
  dielectric_constant: string;
  scattering_regime: string;
  gpm_rain_30d: string;
  oco_carbon_flux: string;
}

export interface SonificationParams {
  base_freq_hz: number;
  waveform: 'sine' | 'triangle' | 'sawtooth';
  pitch_slide?: string;
  description: string;
}

export interface StoryChapter {
  step: number;
  tag: 'TIMELINE' | 'HUMAN_PAIN' | 'DRIVERS' | 'TIPPING_POINT' | 'ACTION_PLAN';
  title: string;
  headline?: string;
  emotional_summary?: string;
  stats?: Array<{ label: string; value: string }>;
  milestones?: Array<{ period: string; event: string }>;
  drivers?: Array<{ type: 'PHYSICAL' | 'HUMAN'; title: string; desc: string }>;
  warning?: string;
  consequences?: string[];
  economic_impact?: string;
  measures?: Array<{ priority: string; title: string; desc: string }>;
}

export interface HotspotDetail {
  id: HotspotId;
  name: string;
  location: string;
  badge: string;
  coordinates: {
    lat: number;
    lon: number;
    zoom: number;
  };
  radar_telemetry: RadarTelemetry;
  sonification: SonificationParams;
  story_chapters: StoryChapter[];
}
```

---

## 5. Frontend Integration Snippet (Ready for Claude)

```typescript
// Fetch the 4 map dots on page load
export async function getHotspots(): Promise<HotspotSummary[]> {
  const res = await fetch('/api/hotspots');
  if (!res.ok) throw new Error('Failed to load hotspots');
  return res.json();
}

// Fetch complete presentation data when user clicks a dot
export async function getHotspotDetail(id: HotspotId): Promise<HotspotDetail> {
  const res = await fetch(`/api/hotspots/${id}`);
  if (!res.ok) throw new Error(`Failed to load hotspot ${id}`);
  return res.json();
}
```

---

## 6. How the Frontend Presentation Flow Works (No Popups!)

1. **Page Load:**
   - Map displays Pakistan with the **4 glowing pulse dots** (Siachen, Islamabad, Quetta, Indus).
2. **User Clicks a Dot (e.g. Quetta):**
   - The map camera zooms smoothly to Quetta (`map.flyTo({ center: [67.01, 30.18], zoom: 11.5 })`).
   - The frontend calls `getHotspotDetail('quetta')`.
   - The UI transitions into **Presentation Mode** (a clean side drawer or dedicated full-width presentation overlay).
   - The user steps through the 5 chapters:
     1. Timeline
     2. Human Pain Points
     3. Physical Drivers
     4. 2030 Tipping Point
     5. Action Plan
3. **Audio Button ("Hear Radar"):**
   - Synthesizes the tone using `hotspot.sonification.base_freq_hz` via the Web Audio API.
4. **"Back to Pakistan Map" Button:**
   - Resets camera zoom back to the full country (`zoom: 5.5, center: [69.3, 30.3]`) to let judges click another hotspot.
