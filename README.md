# 🛰️ Dancing with the SARs — NISAR Earth Surface Dynamics Explorer

> **NASA International Space Apps Challenge 2026**  
> **Challenge:** [Dancing with the SARs](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/)  
> **Global Judging Categories:** *Best Use of Data* | *Best Use of Science* | *Galactic Impact*

[![NASA Space Apps](https://img.shields.io/badge/NASA-Space_Apps_2026-0B3D91?style=for-the-badge&logo=nasa&logoColor=white)](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/)
[![NISAR L2 GCOV](https://img.shields.io/badge/NISAR-L2__GCOV__RTC-00F0FF?style=for-the-badge)](https://nisar.jpl.nasa.gov/)
[![License: MIT](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](LICENSE)

---

## ⚡ Quick Links for NASA Judges
- 🚀 **Live Interactive Demo:** [Launch Dancing with the SARs](https://dancing-with-the-sars.vercel.app) *(Pre-computed for 60fps instant loading)*
- 🎬 **Project Demo Video (YouTube):** [Watch the 3-Minute Video Pitch](https://youtube.com)
- 📊 **Presentation Slides:** [View 7-Slide Deck (PDF)](docs/)
- 📜 **NASA Space Apps Project Page:** [Official Submission](https://www.spaceappschallenge.org)

---

## 🌍 The Mission & Problem
During catastrophic surface events—such as monsoons, river breaches, and wetland floods—traditional optical satellites (like Landsat and Sentinel-2) are frequently **blinded by thick cloud cover, torrential rain, and darkness**. 

**Dancing with the SARs** is an open-source radar remote sensing platform utilizing microwave data from the **NASA-ISRO Synthetic Aperture Radar (NISAR)** mission. Operating at L-band (24 cm wavelength), NISAR's radar pulses pierce through clouds and dense forest canopies day and night. 

Our application decodes raw microwave backscatter ($\gamma^0$) and polarimetric phase into clear, actionable surface intelligence—and maps the temporal rhythms of Earth into harmonic acoustic frequencies (*"Dancing with the SARs"*).

---

## 🏆 NASA Judging Rubric Alignment (How We Score 5/5)

| Evaluation Criterion | How Our Project Fulfills It | Deep-Dive Documentation |
| :--- | :--- | :--- |
| **1. Relevance** *(Deep NASA Data)* | Ingests real NISAR L2 GCOV (Geocoded Polarimetric Covariance) HDF5 data via the NASA Alaska Satellite Facility (ASF DAAC). Features multi-date comparison and polarization toggling ($HH, HV$). | [`docs/NISAR_DATA_ARCHITECTURE_2026.md`](file:///home/hashim/Data/Projects/SARS/docs/NISAR_DATA_ARCHITECTURE_2026.md) |
| **2. Validity** *(Scientific Accuracy)* | Strictly grounded in **surface roughness** and **dielectric constant** physics. Explicitly isolates **double-bounce scattering** ($> -5\text{ dB}$) in flooded canopies from **specular reflection** ($< -20\text{ dB}$) over open water. | [`docs/SAR_PHYSICS_AND_ALGORITHMS.md`](file:///home/hashim/Data/Projects/SARS/docs/SAR_PHYSICS_AND_ALGORITHMS.md) |
| **3. Impact** *(Societal Benefit)* | Quantifies submerged agricultural lands ($\text{km}^2$), detects compromised infrastructure, and outputs lightweight emergency GeoJSON for disaster response teams. | [`docs/DATA_SOURCES_AND_ACQUISITION.md`](file:///home/hashim/Data/Projects/SARS/docs/DATA_SOURCES_AND_ACQUISITION.md) |
| **4. Creativity** *(Innovation)* | Features an **interactive split-screen swipe slider** (NISAR SAR vs. cloudy optical) and an **audio sonification synthesizer** that translates radar backscatter curves into musical pitch and rhythm. | [`docs/SAR_PHYSICS_AND_ALGORITHMS.md`](file:///home/hashim/Data/Projects/SARS/docs/SAR_PHYSICS_AND_ALGORITHMS.md) |
| **5. Presentation** *(Storytelling)* | Guided 4-chapter narrative mode with automated camera panning, dark aerospace HUD styling, and sub-second load times on any device. | [`docs/BEST_CODING_PRACTICES.md`](file:///home/hashim/Data/Projects/SARS/docs/BEST_CODING_PRACTICES.md) |

---

## 🎯 Key Application Features

```
┌────────────────────────────────────────────────────────────────────────┐
│  🛰️  DANCING WITH THE SARS  |  NASA-ISRO SAR EXPLORER HUD               │
├────────────────────────────────┬───────────────────────────────────────┤
│  SPLIT SWIPE SLIDER            │  LAYER CONTROLS & PHYSICAL METRICS    │
│  [Date 1: Pre-Flood Optical]   │  [x] NISAR Dual-Pol FCC (HH/HV/Ratio) │
│              ◄──||──►          │  [ ] HH Backscatter (Double-Bounce)   │
│  [Date 2: Post-Flood NISAR SAR]│  [ ] HV Cross-Pol (Canopy Structure)  │
├────────────────────────────────┴───────────────────────────────────────┤
│  BACKSCATTER SONIFICATION SYNTH & GUIDED STORYLINE                     │
│  ♫ Tone: 440 Hz (Roughness) | Tempo: 120 BPM (Hydrologic Pulse)        │
│  [◀ Previous Chapter]  Stop 2: Double-Bounce Inundation  [Next Chapter ▶]
└────────────────────────────────────────────────────────────────────────┘
```

1. **Before/After Split-Screen Swipe:** Directly compare pre-disaster optical imagery with post-disaster NISAR L-band SAR, proving radar's cloud-piercing capability.
2. **Dual-Pol False-Color Compositing (FCC):**
   - **Red ($HH$):** Bare soil, urban structures, and double-bounce reflection.
   - **Green ($HV$):** Forest canopies and dense agricultural crops (volume scattering).
   - **Blue ($HH - HV$):** Calm open floodwaters and specular surfaces.
3. **Radar Acoustic Sonification:** Click any coordinate to inspect its multi-temporal $dB$ backscatter curve and hear its acoustic frequency mapped via the Web Audio API.
4. **Guided Story Mode:** 1-click narrative tour stepping judges through key surface anomalies with layman-friendly scientific explanations.

---

## 📡 NASA & Partner Data Sources Used
- **Primary Mission Data:** NASA-ISRO Synthetic Aperture Radar (NISAR) Level 2 Geocoded Polarimetric Covariance (`NISAR_L2_GCOV_V1` / `PROVISIONAL_V1`) via [NASA ASF DAAC](https://search.asf.alaska.edu/).
  - Co-pol backscatter: `/science/LSAR/GCOV/grids/frequencyA/HHHH`
  - Cross-pol backscatter: `/science/LSAR/GCOV/grids/frequencyA/HVHV`
- **Optical Comparison:** Copernicus Sentinel-2 L2A Cloud-Optimized GeoTIFFs (European Space Agency / AWS Open Data).
- **Digital Elevation Model:** NASA SRTM 30m / Copernicus GLO-30 DEM.

---

## 💻 Architecture & Engineering Philosophy
- **Offline Heavy Science (Python):** HDF5 array extraction, spatial Lee speckle filtering, linear-to-decibel conversion, and Cloud-Optimized GeoTIFF (COG) generation.
- **Fast Web Streaming (React + TypeScript):** Instantaneous 60fps map rendering (MapLibre GL / Leaflet), Web Audio synthesizer, and bundled offline demo fallbacks.

```mermaid
flowchart LR
    A["NISAR L2 GCOV<br/>(.h5 via ASF DAAC)"] --> B["Python Pipeline<br/>(h5py + Lee Filter)"]
    B --> C["Decibel Normalization<br/>(HH: -25 to 0 dB, HV: -30 to -5 dB)"]
    C --> D["Cloud-Optimized GeoTIFFs<br/>& GeoJSON Metrics"]
    D --> E["Interactive Web HUD<br/>(React + MapLibre + Web Audio)"]
```

---

## 🚀 Quickstart (Run Locally in 60 Seconds)

### 1. Interactive Web Dashboard
```bash
# Clone the repository
git clone https://github.com/your-username/dancing-with-the-sars.git
cd dancing-with-the-sars/web

# Install dependencies and start local dev server
npm install
npm run dev
# Open http://localhost:5173 in your browser
```

### 2. Python SAR Data Processing (Optional for Custom Scenes)
```bash
# Install Python scientific dependencies
pip install -r requirements.txt

# Run preprocessing on a NISAR granule
python scripts/process_gcov.py --input data/raw/sample_nisar.h5 --output data/processed/
```

---

## 📖 Complete Technical Documentation Index

For judges, researchers, and developers seeking deep technical specifications:

| Document | Description |
| :--- | :--- |
| [**Project Master Blueprint**](file:///home/hashim/Data/Projects/SARS/docs/PROJECT_BLUEPRINT_AND_SYSTEM_ARCHITECTURE.md) | Complete Pakistan case study, multi-sensor data fusion, and 3-act workflow |
| [**Challenge Brief & Rubric**](file:///home/hashim/Data/Projects/SARS/docs/CHALLENGE_BRIEF_AND_RUBRIC.md) | NASA challenge objectives, 5 scoring criteria, and target awards |
| [**NISAR 2026 Data Architecture**](file:///home/hashim/Data/Projects/SARS/docs/NISAR_DATA_ARCHITECTURE_2026.md) | Exact HDF5 internal paths, product levels (GCOV vs GUNW), and ASF queries |
| [**SAR Physics & Algorithms**](file:///home/hashim/Data/Projects/SARS/docs/SAR_PHYSICS_AND_ALGORITHMS.md) | Lee speckle filtering formulas, linear-to-dB math, and FCC color recipes |
| [**Recommended Tech Stack**](file:///home/hashim/Data/Projects/SARS/docs/RECOMMENDED_TECH_STACK.md) | System blueprint, directory structure, and frontend component roadmap |
| [**Data Sources & Acquisition**](file:///home/hashim/Data/Projects/SARS/docs/DATA_SOURCES_AND_ACQUISITION.md) | ASF Vertex setup, Earthdata `.netrc`, and high-impact study regions |
| [**Scientific & Code Best Practices**](file:///home/hashim/Data/Projects/SARS/docs/BEST_CODING_PRACTICES.md) | Memory-efficient HDF5 chunking, coordinate reprojection, and UI standards |
| [**AI Agent Hackathon Playbook**](file:///home/hashim/Data/Projects/SARS/docs/AI_AGENT_HACKATHON_PLAYBOOK.md) | Rapid delivery rules, fail-safe fallbacks, and zero-stub coding policy |
| [**Ready-to-Use Agent Prompts**](file:///home/hashim/Data/Projects/SARS/docs/PROMPT_TEMPLATES_FOR_AGENTS.md) | Scaffolding prompts for Python pipelines, swipe sliders, and audio synths |

---

## 👥 The Team
Built with passion for **NASA Space Apps Challenge 2026**.

## 📄 License
This project is open-source and released under the [MIT License](LICENSE).
