# AI Agent Hackathon Playbook — Speed, Precision & Victory

This playbook instructs any AI agent (Claude, Gemini, ChatGPT, Cursor, Copilot, Windsurf) on the exact engineering strategies, coding patterns, and speed tactics required to build an award-winning hackathon submission.

---

## 1. The Hackathon Engineering Mindset vs. Traditional Enterprise

| Enterprise Development (Avoid) | Hackathon Winning Development (Enforce) |
| :--- | :--- |
| Multi-week architectural planning | Working interactive skeleton in 1 hour |
| Complex database schemas & OAuth | Bundled static JSON + local state for instant demos |
| Brittle live external API calls | Local mock fallbacks so the demo never fails on stage |
| Abstract microservice architectures | Flat, modular, high-cohesion single-responsibility modules |
| Generic grayscale/unstyled wireframes | Polished, dark scientific HUD with animated 60fps transitions |
| Fragmented code snippets (`// TODO...`) | Complete, copy-pasteable, zero-placeholder implementations |

---

## 2. The 5 Cardinal Rules for AI Coding Agents

### Rule 1: The Single-Turn Deliverable Rule
When asked to build a component or script, the AI agent must output the **entire working file** or a complete drop-in edit. 
- Never leave placeholders like `// Add remaining routes here`.
- Never truncate types or styling classes.
- The user must be able to paste the code, run it, and immediately see results without missing reference errors.

### Rule 2: The Fail-Safe Fallback Pattern (Zero-Crash Guarantee)
Every network request or data loader must follow this exact defensive structure:
```typescript
export async function fetchRadarDataset(regionId: string): Promise<RadarDataset> {
  try {
    const response = await fetch(`/api/radar/${regionId}`);
    if (!response.ok) throw new Error("API returned non-200");
    return await response.json();
  } catch (err) {
    console.warn(`[WARN] Live fetch failed for ${regionId}, loading bundled fallback data.`, err);
    // Bulletproof fallback ensures judges NEVER see a blank screen or error toast
    return BUNDLED_FALLBACK_DATA[regionId] ?? DEFAULT_FALLBACK_DATA;
  }
}
```

### Rule 3: Visual Polish & Instant Gratification
Judges judge with their eyes in the first 10 seconds:
- Use **Tailwind CSS** with a consistent Aerospace/NASA theme (Deep Space background `#070b14`, Radar Cyan `#00F0FF`, NASA Blue `#0B3D91`, Crisp White `#F8FAFC`).
- Ensure all map controls, buttons, and sliders have active visual states, smooth hover transitions (`transition-all duration-200`), and readable labels.
- Provide interactive tooltips for all radar concepts ($HH, HV, \gamma^0, dB$) so non-technical judges instantly understand the science.

### Rule 4: Radar Physics Integrity
Never make up physics formulas or SAR paths.
- Linear power $\gamma^0$ to Decibel conversion: $\gamma^0_{dB} = 10 \cdot \log_{10}(\gamma^0_{linear})$.
- Double-bounce scattering (flooded forests) yields high $HH$ backscatter ($> -5\text{ dB}$).
- Calm open water yields very low backscatter ($< -20\text{ dB}$) due to specular reflection.
- Always apply speckle filtering (Lee filter) on linear power *before* decibel conversion.

### Rule 5: Demo Mode / Guided Storyline Control
Build a 1-click **"Guided Tour"** or **"Story Mode"** into the frontend:
- Stepping through the tour automatically centers the map on key coordinates (e.g., Indus River Breach, Flooded Croplands, Urban Refuge).
- Changes the active layer (e.g., switches from Sentinel-2 cloudy optical to NISAR dual-pol composite).
- Shows an annotated explanation card describing the physical driver and societal impact.
- This guarantees judges see the full value proposition even if they only spend 60 seconds on the page!

---

## 3. High-Speed Scaffolding Sequence
When building out the project, execute in this order:
1. **Offline Preprocessing Script (`scripts/`):** A clean Python CLI that slices NISAR `.h5` files, applies Lee filter, computes dB rasters, and outputs PNG/GeoJSON assets.
2. **Bundled Asset Package (`web/src/data/`):** Store the processed demo assets and fallback JSON directly in the frontend project so the app is 100% self-contained.
3. **Core Map Viewer (`web/src/components/MapViewer.tsx`):** MapLibre GL or Leaflet canvas rendering the base map and SAR raster overlays.
4. **Before/After Split Slider (`web/src/components/SwipeSlider.tsx`):** Let users drag to compare pre- vs post-event or SAR vs optical.
5. **Polarization Switcher (`web/src/components/LayerControls.tsx`):** Instant toggle between $HH$, $HV$, False-Color RGB, and Change Detection.
6. **SAR Sonification Hook (`web/src/hooks/useRadarSonification.ts`):** Web Audio synthesizer translating radar pixel values into acoustic melodies ("Dancing with the SARs").
7. **Guided Story Mode Carousel (`web/src/components/StoryGuide.tsx`):** Multi-stop interactive narrative.
