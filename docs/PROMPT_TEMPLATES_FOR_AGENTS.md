# Ready-to-Use AI Agent Prompt Templates for Hackathon Speedruns

Copy and paste these exact prompts into Claude, Gemini, ChatGPT, or Cursor to scaffold high-impact features instantly without back-and-forth debugging.

---

## Prompt 1: Python NISAR L2 GCOV Preprocessor (`process_gcov.py`)
```markdown
Read `docs/NISAR_DATA_ARCHITECTURE_2026.md` and `docs/SAR_PHYSICS_AND_ALGORITHMS.md`.
Write a complete, production-grade Python script `scripts/process_gcov.py` that:
1. Opens a NISAR L2 GCOV HDF5 file using `h5py`.
2. Extracts `/science/LSAR/GCOV/grids/frequencyA/HHHH` and `/science/LSAR/GCOV/grids/frequencyA/HVHV` along with the coordinate grids and valid mask.
3. Implements a spatial Lee Filter (3x3 or 5x5 window) on the raw linear power arrays before decibel conversion.
4. Safely converts filtered linear power to decibels using gamma0_dB = 10 * log10(gamma0_linear), clipping HH between -25 dB and 0 dB, and HV between -30 dB and -5 dB.
5. Computes a Dual-Pol False-Color Composite (R: HH, G: HV, B: HH-HV) normalized to 0-255 uint8.
6. Exports both high-resolution PNG overlays (with a JSON bounding box) and a Cloud-Optimized GeoTIFF (using rasterio).
7. Includes defensive error handling for missing frequencies, NaNs, and provides a CLI via `argparse`.
Do not truncate code. Write the entire file with all imports and mathematical helper functions.
```

---

## Prompt 2: Interactive Split-Screen Swipe Slider Component
```markdown
Read `docs/AI_AGENT_HACKATHON_PLAYBOOK.md` and `docs/BEST_CODING_PRACTICES.md`.
Write a React + TypeScript component `web/src/components/SwipeSlider.tsx` using Tailwind CSS and Lucide React icons.
Features required:
1. Split-screen visual comparison: Left pane shows Date 1 (Pre-Flood or Optical Sentinel-2), Right pane shows Date 2 (Post-Flood NISAR SAR).
2. Smooth, draggable vertical divider with 60fps responsiveness across mouse and touch events.
3. Interactive toggle buttons at the top of each pane to switch display modes (HH, HV, Dual-Pol RGB, Difference Mask).
4. Badges indicating satellite sensor, acquisition date, and polarization mode.
5. Dark-mode aerospace aesthetic (deep slate background, radar cyan `#00F0FF` accents, crisp typography).
6. Fail-safe props with sensible defaults so it renders immediately even without parent data.
Write the complete TypeScript file without placeholders or missing imports.
```

---

## Prompt 3: Radar Sonification Engine ("Dancing with the SARs")
```markdown
Read `docs/CHALLENGE_BRIEF_AND_RUBRIC.md` and `docs/SAR_PHYSICS_AND_ALGORITHMS.md`.
We are implementing the thematic "Dancing with the SARs" feature: translating SAR microwave backscatter and surface change rhythms into audio.
Write a React hook `web/src/hooks/useRadarSonification.ts` using the browser's native Web Audio API (zero external heavy audio dependencies):
1. Accepts pixel radar backscatter values: HH (dB), HV (dB), and temporal change magnitude (delta dB).
2. Maps decibels (-30 dB to 0 dB) to musical pitch (e.g., pentatonic or harmonic minor scale from 220 Hz to 880 Hz). Water (low dB) sounds deep and calm; urban/double-bounce (high dB) rings sharp and clear.
3. Maps polarization ratio (HH / HV) or temporal change delta to audio timbre (sine vs triangle wave) and rhythmic pulsing tempo (BPM).
4. Provides methods: `playPixelTone(hhDb, hvDb, deltaDb)`, `startDanceLoop(pixelSeries)`, and `stopAudio()`.
5. Includes mute/unmute state management and handles browser audio context autoplay restrictions gracefully.
Write the complete TypeScript file ready to import into our map point inspector.
```

---

## Prompt 4: Guided Narrative / Story Mode Carousel
```markdown
Read `docs/CHALLENGE_BRIEF_AND_RUBRIC.md`.
Judges need a guided walkthrough that demonstrates both technical depth and societal impact in under 90 seconds.
Write a React + TypeScript component `web/src/components/StoryGuide.tsx`:
1. Provides a step-by-step interactive card carousel (Chapter 1: "The Monsoons Hit & Clouds Blind Optical Sensors", Chapter 2: "NISAR Pierces the Storm", Chapter 3: "Double-Bounce Unveils Submerged Forests", Chapter 4: "Quantifying Damage for Emergency Relief").
2. When the user clicks "Next" or "Previous", triggers a callback `onSelectChapter(chapter)` that passes coordinates, zoom level, and target active layer (e.g., optical vs SAR) so the map camera pans smoothly.
3. Includes badges for Key Physical Metric (e.g., "Backscatter drop: -14.2 dB", "Double-bounce: +7.8 dB") and Societal Impact (e.g., "1,200 km² flooded, 45,000 residents alerted").
4. Styled with NASA blue, radar cyan highlights, and Lucide icons.
Write the full component with sample chapter data bundled so it runs out-of-the-box.
```

---

## Prompt 5: Self-Contained Fallback Demo Data Generator
```markdown
Read `docs/RECOMMENDED_TECH_STACK.md` and `docs/DATA_SOURCES_AND_ACQUISITION.md`.
Write a script or JSON generator `web/src/data/mockRadarData.ts` that exports:
1. Realistic geo-bounded metadata for a high-impact study region (e.g., Indus River Basin or Amazon Pantanal).
2. Array of temporal acquisition dates with simulated HH, HV, and delta dB statistics.
3. GeoJSON feature collections for inundation extent and high-risk zones.
4. Pre-configured story chapter stops with titles, descriptions, coordinates, and physical radar metrics.
This file ensures that even if local servers are disconnected during a live judging session, the web frontend runs 100% interactively without errors.
```
