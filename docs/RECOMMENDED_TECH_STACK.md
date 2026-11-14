# Recommended Hackathon Architecture ("Dancing with the SARs")

## 1. Architecture Philosophy: Pre-Compute Heavy Science, Stream Fast Visuals
**Do NOT** attempt to download and process 2–5 GB NISAR `.h5` files dynamically inside a user's web browser during a live demo. Live demo failures kill hackathon scores.

### Offline / Backend Pipeline (Python)
- **Tools:** `asf_search`, `h5py`, `numpy`, `scipy.ndimage`, `rasterio`, `shapely`, `geopandas`
- **Workflow:**
  1. Fetch targeted NISAR `GCOV`/`GUNW` scenes via `asf_search` over the selected Area of Interest (AOI).
  2. Slice spatial bounds and target polarizations (`HHHH`, `HVHV`).
  3. Apply speckle filter (Lee filter) and convert linear power to decibels ($dB$).
  4. Generate dual-pol False-Color RGB composites and Before/After difference rasters.
  5. Calculate summary metrics (e.g., inundated area in $\text{km}^2$, percent change, soil moisture shift).
  6. Export web-optimized outputs:
     - Lightweight **Cloud-Optimized GeoTIFFs (COGs)** or high-res PNG/WebP overlays with geo-coordinates.
     - Fast **GeoJSON** change masks and time-series summaries.

### Interactive Frontend (React / Vite / Next.js + MapLibre GL / Leaflet)
- **Core Visual Features:**
  1. **Before/After Split-Screen Swipe Slider:** Real-time side-by-side comparison between dates (e.g., pre-flood vs post-flood) or sensor comparison (NISAR L-band vs cloudy Sentinel-2 optical imagery).
  2. **Polarization Switcher:** Instant toggling between `HH`, `HV`, `Dual-Pol RGB`, and `Temporal Change` masks without re-rendering delays.
  3. **Point Inspector & Audio Sonification ("Dancing with the SARs"):**
     - Clicking any pixel plots its temporal backscatter curve ($dB$ vs time).
     - Sonification module: maps radar backscatter amplitude ($dB$) and change frequency to musical pitch and rhythm, embodying the "Dancing with the SARs" theme.
  4. **Guided Narrative / Story Mode:** Step-by-step interactive carousel or chapter walk-through that pans the camera across significant points of interest, presenting scientific explanations with layman clarity.

---

## 2. Directory Structure Blueprint
```
SARS/
├── docs/                               # AI Knowledge Base & Technical Docs
│   ├── CHALLENGE_BRIEF_AND_RUBRIC.md   # NASA prompt, rubric & objectives
│   ├── NISAR_DATA_ARCHITECTURE_2026.md # HDF5 paths & 2026 data rules
│   ├── SAR_PHYSICS_AND_ALGORITHMS.md   # Radar physics & FCC formulas
│   ├── DATA_SOURCES_AND_ACQUISITION.md # NASA ASF & external datasets
│   ├── BEST_CODING_PRACTICES.md        # Pipeline & frontend coding standards
│   └── RECOMMENDED_TECH_STACK.md       # Architecture blueprint
├── scripts/                            # Data acquisition & SAR preprocessing
│   ├── download_nisar.py               # asf_search automated downloader
│   ├── process_gcov.py                 # HDF5 slicer, Lee filter & dB converter
│   └── generate_composites.py          # Dual-pol RGB & difference map generator
├── data/                               # Raw & processed geospatial assets (.gitignored)
│   ├── raw/                            # Input .h5 NISAR granules
│   └── processed/                      # Output COGs, GeoJSON, and JSON metrics
├── web/                                # Interactive Map Dashboard (Frontend)
│   ├── src/
│   │   ├── components/                 # Map, SwipeSlider, AudioPlayer, StoryGuide
│   │   ├── hooks/                      # Audio synth & time-series hooks
│   │   └── data/                       # Bundled demo geo-assets & metrics
│   ├── package.json
│   └── vite.config.ts
├── CLAUDE.md                           # AI system instructions for Claude
├── GEMINI.md                           # AI system instructions for Gemini
├── README.md                           # Open-source showcase & setup guide
└── .gitignore                          # Ignores data, caches & local secrets
```

---

## 3. Recommended Frontend Packages
- **Map Engine:** `maplibre-gl` or `leaflet` with `leaflet-side-by-side` (clean, lightweight swipe slider).
- **Charts / Time Series:** `chart.js` or `recharts` for fast backscatter curve plotting.
- **Audio Synthesizer (Sonification):** `tone.js` or native Web Audio API for translating $dB$ values into harmonic tones.
- **Styling:** `tailwindcss` with dark scientific HUD aesthetics (NASA blue `#0B3D91`, radar cyan `#00F0FF`, deep space slate `#0b0f19`).
