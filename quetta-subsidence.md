# Quetta Is Sinking — NISAR Space Apps 2026 Project Brief

*Status as of 2026-11-15. Challenge: **"Dancing with the SARs"**, NASA Space Apps Challenge 2026.*

> **Bottom line:** Quetta's ground is subsiding in a north–south bowl centred on the city. We have seen it in **three independent ways**: published research, Sentinel-1 radar (2024–25, both viewing directions), and **NISAR itself** (June–October 2026, ascending and descending). The final NISAR vertical map shows a bowl median of **−8.7 cm/yr** moving straight down (east–west ≈ 0), matching Sentinel-1 (≈ −8.3 cm/yr vertical-equivalent; **r = 0.89**). 2050 scenarios: under the current trend ~46 km² of the valley sinks ≥ 1 m more, affecting ~49,000 buildings; controlling pumping cuts that to ~6 km². **Final products: [`quetta-check/final/`](quetta-check/final/) — see §4.5.** Remaining work: interactive website, slide deck, submission.

---

## Contents
1. [The challenge](#1-the-challenge)
2. [The problem: why Quetta is sinking](#2-the-problem-why-quetta-is-sinking)
3. [How Quetta answers the challenge](#3-how-quetta-answers-the-challenge)
4. [Evidence we gathered](#4-evidence-we-gathered)
5. [NISAR data available over Quetta](#5-nisar-data-available-over-quetta)
6. [Pipeline: how to reproduce](#6-pipeline-how-to-reproduce)
7. [Viability: pros and cons](#7-viability-pros-and-cons)
8. [2050 sinking and damage scenarios (AI-assisted)](#8-2050-sinking-and-damage-scenarios-ai-assisted)
9. [20-hour team plan (3 people + Claude)](#9-20-hour-team-plan-3-people--claude)
10. [Presentation outline](#10-presentation-outline)
11. [Open issues and next steps](#11-open-issues-and-next-steps)
12. [File index](#12-file-index)
13. [Sources](#13-sources)

---

## 1. The challenge

**Task:** build an **interactive application** that uses radar data from **NISAR** (the NASA–ISRO L-band SAR mission) to **track and visualize one or more types of surface change** at locations around the world.

**Desired outcome:** an **open-source, user-friendly** tool that turns complex radar observations into **actionable insights** for scientists, resource managers, educators, decision-makers and the public, showing the patterns and rhythms of surface change over time.

**Suggested steps:** pick a study area → download NISAR data (plus supporting data) → present findings interactively (maps, sliders, dashboards, story maps) → **hypothesize the physical drivers** → discuss polarizations and **future NISAR applications**.

**Explicitly named:** *"SAR can also measure fine surface movement on the centimeter scale, such as for earthquakes and land subsidence."*

Official page: <https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/> · Full summary: [`challenge-statement.md`](challenge-statement.md)

---

## 2. The problem: why Quetta is sinking

| Fact | Value | Source |
|---|---|---|
| Subsidence rate (recent maximum) | **12–16 cm/yr**; >15 cm/yr in urban centres (2014–2024) | Remote Sensing 2024; Natural Hazards 2025; EGU25 |
| Acceleration | ~11.4 cm/yr (2003–2010) → ~16 cm/yr after 2016; one GNSS station 12 → 16.6 cm/yr | Natural Hazards 2025; Remote Sensing 2024 |
| Cumulative sinking | up to **2.7 m** (2003–2023) | Natural Hazards 2025 |
| Cause | Groundwater over-pumping → dewatering and compaction of clay-rich valley sediments | Remote Sensing 2024 |
| Water table decline | ~1 m/yr (1989–2007 reports); **2–5 m/yr** cited in Jan 2026 (one official: 1–1.5 m/yr) | WAPDA via literature; Dawn Jan 2026 |
| Outlook | Experts warn many valley wells may **run dry within 5–10 years** without action | Dawn, Apr 2026 |
| Ground cracking | Earth fissures documented in the valley | AGU 2015 abstract |
| Population pressure | Balochistan projected at 18.6 M by 2030, >35 M by 2050 | Official projections cited in news |

**Physical chain (the story):** arid valley + growing city → more tube wells → water table drops metres per year → clay layers lose water and compact (mostly irreversibly) → ground sinks unevenly → buildings, pipes, roads and rail crack; fissures open at the bowl edges.

---

## 3. How Quetta answers the challenge

| Challenge asks for | Quetta |
|---|---|
| Surface change tracked with NISAR | ✅ Land subsidence via InSAR (NISAR's signature capability) |
| Change over time / rhythms | ✅ 12-day NISAR revisit → time series and rates; possible seasonal (summer pumping) signal |
| Physical drivers | ✅ Groundwater depletion, clay compaction |
| Human drivers | ✅ Directly human-caused (wells, urban growth) |
| Actionable insight | ✅ Which neighbourhoods sink fastest; risk zones for water/urban planners |
| Interactive app | ✅ Rate map, click-a-neighbourhood time series, before/after, 2050 scenarios |
| Future NISAR applications | ✅ Same pipeline → Lahore, Karachi, Multan; nationwide subsidence monitor |
| Polarizations | ⚠️ Weak fit for InSAR — can be addressed with a GCOV backscatter layer showing urban growth (more buildings → more wells → more sinking) |

---

## 4. Evidence we gathered

### 4.1 Sentinel-1 (ESA, via COMET LiCSAR — public, no login)

Frames: **ascending `042A_05933_131313`** (incidence ≈ 39°) and **descending `151D_06038_131313`**. Data: unwrapped/wrapped interferograms, ~100 m.

**Ascending results** (line-of-sight, LOS; negative = away from satellite = sinking; reference on bedrock at 66.80E 30.25N):

| Pair | Days | Max rate (cm/yr LOS) | City centre (cm/yr LOS) |
|---|---|---|---|
| **2024-09-09 → 2025-09-04** (best) | 360 | **−10.8** (≈ −14 vertical if purely vertical) | −9.3 |
| 2025-03-08 → 2025-09-28 | 204 | −14.6 (summer-only, extrapolated) | −12.2 |
| 2025-03-20 → 2025-09-28 | 192 | −14.6 (summer-only, extrapolated) | −12.4 |
| 2024-03-01 → 2025-03-08 | 372 | −5.1 (under-reports; core decorrelated/unwrapping) | −4.5 |

- The bowl is centred on the city, running north–south from ~30.08 to 30.25°N, mostly between 66.96 and 67.02°E.
- Second reference point (67.15E 30.20N) agrees within 0.3 cm in the best pair.

**Descending:** the *unwrapped* products showed nothing, but the **wrapped phase shows dense concentric fringes over the valley** (roughly 4–5 rings per year at 2.8 cm each) in the same shape as ascending. The unwrapping failed because the fringes were too dense. → **The sinking is seen from both viewing directions, so the motion is predominantly vertical.**

Figures: [`quetta-check/sentinel1/`](quetta-check/sentinel1/)

### 4.2 NISAR full data — track 41 ascending (confirmed)

- **Data:** 9 consecutive GUNW interferograms (12-day, one 24-day), **2026-06-17 → 2026-10-15** (120 days), streamed for the Quetta area only. Usable pixels per pair: 78–96%.
- **Method:** mask coherence < 0.3 and invalid connected components; reference to bedrock box (66.80E 30.25N); remove best-fit plane outside the valley; sum consecutive pairs → cumulative LOS; fit a per-pixel linear rate through all 10 dates; smooth 5×5; compare pixel-by-pixel with the Sentinel-1 360-day rate map (resampled to the NISAR grid).
- Wavelength 0.2420 m (from the file's centre frequency). Sign: negative = away from satellite (sinking). The positive correlation with Sentinel-1 effectively **confirms the sign convention**.

| | NISAR (no iono correction) | NISAR (iono corrected) | Sentinel-1 2024–25 |
|---|---|---|---|
| **Inside the S1 bowl** (S1 < −5 cm/yr; 3,564 px), median | **−6.3 cm/yr** | −2.9 cm/yr | **−6.5 cm/yr** |
| Valley outside bowl (S1 > −1.5; 18,024 px), median | +1.1 cm/yr | +2.8 cm/yr | −0.2 cm/yr |
| Bowl minus outside | −7.4 cm/yr | −5.6 cm/yr | — |
| Pixel correlation with S1 (26,573 valley px) | **r = 0.67** | r = 0.36 | — |
| City-centre cumulative, 120 days | −2.8 cm | −1.5 cm | — |
| Bedrock reference, 120 days | +0.8 cm | +0.7 cm | — |

Interpretation:
- **Same bowl, same place, nearly the same rate** — two satellites, two wavelengths (C-band vs L-band), two different years. The sinking continued through 2026.
- **Atmospheric artifacts:** large "sinking" blobs on the mountains SW and E of the city are weather/terrain-correlated delay (Sentinel-1 shows nothing there). Mask or correct them in the app.
- **The ionosphere correction made it worse** (r 0.67 → 0.36). Unexplained — possibly noisy provisional ionosphere layers or a sign/units issue. Use the uncorrected version until investigated.
- **Single dates are noisy** (city-centre series jumps ±3 cm between dates) → present fitted rates, not date-to-date values.
- Note: pixel-level confidence intervals are over-optimistic because neighbouring pixels are correlated; the agreement is nonetheless large relative to the noise.

Figures and data: [`quetta-check/nisar/`](quetta-check/nisar/)

### 4.3 NISAR track 92 descending — confirmed (cleanest result)

Independent second viewing geometry: 9 consecutive pairs, **2026-06-20 → 2026-10-18** (120 days), 86–94% usable pixels per pair, no ionosphere correction, plane removed.

| | NISAR track 92 | Sentinel-1 2024–25 |
|---|---|---|
| **Inside the S1 bowl** (3,658 px), median | **−7.0 cm/yr** | −6.5 cm/yr |
| Valley outside bowl (18,394 px), median | +3.3 cm/yr | −0.2 cm/yr |
| Pixel correlation with S1 (27,131 valley px) | **r = 0.80** | — |
| Deepest point (5×5 smoothed) | −8.0 cm at **66.984E 30.175N** (city centre) | bowl centre ~66.99E 30.18–30.20N |
| City-centre cumulative, 120 days | **−5.4 cm** (steady decline) | — |
| Bedrock reference, 120 days | −0.2 cm (flat) | — |

- A sharp north–south bowl centred on the city, matching the Sentinel-1 shape; the city-centre time series declines steadily.
- Remaining artifact: a red patch on the mountains east of the city (~67.2E), weather-related (absent in Sentinel-1).
- **Two NISAR viewing directions (ascending track 41 and descending track 92) both show the bowl**, consistent with mainly vertical sinking.

Figures: `quetta-check/nisar/track92_cumulative_map.png`, `quetta-check/nisar/nisar_track92_vs_sentinel1_rates.png`

### 4.4 NISAR public preview images — inconclusive (superseded)

Before the login worked, we decoded NISAR's public quick-look PNGs (colormap `twilight_shifted`, phase rewrapped to 7π per the `nisarqa` source code) and summed the track 41 and 142 chains. Noise (6–8 cm) swamped the expected 2–5 cm and the tracks disagreed. The previews lack coherence, connected-component and ionosphere layers. Superseded by 4.2. Files: [`quetta-check/preview-stack/`](quetta-check/preview-stack/)

### 4.5 FINAL results (overnight 2026-11-15) — use these

**Final NISAR maps** ([`quetta-check/final/nisar/`](quetta-check/final/nisar/)): all four tracks processed; DEM-based correction for terrain-correlated atmosphere; per-pixel velocity ± error; vertical/east solve using the LOS geometry from the GUNW radarGrid cubes (incidence 45.1° track 41, 35.6° track 92).

| Track | r vs S1 | Bowl median (LOS, cm/yr) | Corrections | Used in vertical? |
|---|---|---|---|---|
| 41 asc | **0.88** (was 0.67) | −6.6 | DEM | ✅ |
| 92 desc | **0.82** (was 0.80) | −7.3 | DEM | ✅ |
| 142 asc | 0.49 | −15.2 | iono subtracted | ❌ too noisy (frame edge) |
| 20 desc | 0.24 | −24.1 | DEM + iono | ❌ too noisy |

- **Vertical (41 + 92):** bowl median **−8.7 cm/yr**; city centre −18 ± 4 cm/yr; max −26 cm/yr at 66.984E 30.175N; east–west ≈ 0 (−0.4 cm/yr); **r = 0.89** vs Sentinel-1. Valley area faster than 2 / 5 / 10 cm/yr: 82 / 59 / 18 km².
- **DEM correction** cut the fake mountain "sinking" pixels from 31 % to 11 % (track 41) and 19 % to 9 % (track 92).
- **Ionosphere:** the screen has the right sign (subtracting is correct) but its own uncertainty (~0.9 rad mean) exceeds a 12-day bowl signal, so it hurts the clean tracks and only helps noisy ones. Applied to tracks 142/20 only.
- **Caveat:** peak values (city centre, max) exceed the annual Sentinel-1 peak (~−14 vertical) — summer-only window plus noise; outside-bowl areas carry a +2 to +4 cm/yr bias (not real uplift).

**Money shot** ([`quetta-check/final/moneyshot/`](quetta-check/final/moneyshot/)): the 336-day GSLC pair (2025-11-25 → 2026-10-27) is decorrelated (coherence 0.11; BETA vs V1 files). The 132-day pair (2026-06-17 → 10-27) is coherent (0.47) and shows a ~2–3 cm LOS anomaly centred on the city — consistent with sinking but not a clean fringe image. The headline visual remains the NISAR vertical-velocity map.

**Impact and 2050 scenarios** ([`quetta-check/final/impact/`](quetta-check/final/impact/), METHODS §10): valley floor 124 km², ~112,000 buildings (Microsoft footprints), ~1.71 M people (WorldPop 2025). Recommended run uses NISAR rates annualized ×0.75 (Sentinel-1 full-year/summer ratio); an "as measured" run is the upper bound.

| 2050 (annualized, median) | Area sunk ≥ 1 m | Buildings / people there | Buildings in moderate–severe damage zones |
|---|---|---|---|
| Current trend | 46 km² | 49,285 / 0.86 M | ~5,500 |
| Keeps accelerating | 52 km² | 55,769 / 0.96 M | ~12,800 |
| Pumping controlled | 6.2 km² | 7,317 / 0.14 M | ~0 |

Fastest-sinking 1 % of the valley: ~3.4 m (annualized) to ~4.5 m (as measured) further sinking by 2050 if current rates continue. A random-forest drivers analysis (spatial CV R² ≈ 0.32; elevation most important) is correlative only.

---

## 5. NISAR data available over Quetta

| Product | What it is | Quetta inventory | Size |
|---|---|---|---|
| **GUNW** (L2) | Geocoded unwrapped interferogram; unwrapped phase + coherence at **80 m**, UTM grid (EPSG:32642); includes an ionosphere phase screen (not applied by default) | 42 products, 4 tracks (41A, 142A, 92D, 20D); 12-day pairs (some 24-day); Nov 2025–Jan 2026 (beta) and Jun–Oct 2026 | ~2.3 GB each |
| **GSLC** (L2) | Geocoded single-look complex; two GSLCs on the same track can be multiplied into a custom interferogram (e.g., 11 months) | t41A: 16 dates (2025-11-25 → 2026-10-27); t142A: 14; t92D: 11; t20D: 11 | ~22 GB each (stream subsets only) |
| **GCOV** (L2) | Radiometrically corrected backscatter (HH/HV) — for urban growth/land use context | ~50 per location | ~7 GB each |

- **Data gap:** no public NISAR data from February to mid-June 2026 (backlog expected by end of 2026).
- **Versions:** BETA (Nov 2025–Jan 2026, not fully calibrated) → PROVISIONAL (from 2026-06-17) → V1 (from ~2026-10-22).
- HDF5 layers used: `/science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram/HH/{unwrappedPhase, coherenceMagnitude, connectedComponents, ionospherePhaseScreen}`.
- **Access:** search via the ASF API (no login); preview PNGs are public; `.h5`, KML and QA files need a free NASA Earthdata login.
- **Tools:** `earthaccess` + `h5py` streaming works; MintPy (`prep_nisar`) can read GUNW for full time-series work.
- NASA's ready-made displacement product (OPERA DISP-NI) is **not released** and is planned for North America.

---

## 6. Pipeline: how to reproduce

Code: [`quetta-check/pipeline/nisar_quetta.py`](quetta-check/pipeline/nisar_quetta.py) (+ `test_pipeline.py`, `README.md`). It writes `data/` (cache) and `out/` next to the `pipeline/` folder.

### Earthdata login (Windows) — lessons learned
- `earthaccess` on Windows reads **`%USERPROFILE%\_netrc`** (underscore), not `.netrc`.
- The file must be **plain ASCII/UTF-8 without BOM**. PowerShell's `>` writes UTF-16, which fails to parse.
- Each person creates their own file (never share passwords in chat):

```powershell
Set-Content -Path "$env:USERPROFILE\_netrc" -Value "machine urs.earthdata.nasa.gov login YOUR_USERNAME password YOUR_PASSWORD" -Encoding ascii
```

- Log in once at <https://search.asf.alaska.edu> so ASF data access is approved for the account.

### Run

```bash
cd /d/SARS/quetta-check/pipeline
python -m venv venv
./venv/Scripts/python -m pip install earthaccess h5py numpy matplotlib tifffile pyproj pytest
./venv/Scripts/python -I -m pytest -q test_pipeline.py
./venv/Scripts/python -I nisar_quetta.py auth-check
./venv/Scripts/python -I nisar_quetta.py run --track 41 --frame 17 --plane
./venv/Scripts/python -I nisar_quetta.py run --track 92 --frame 73 --plane
```

Useful flags: `--iono` (apply ionosphere screen), `--coh-min 0.3`, `--phase-sign ±1`, `--ref-lon/--ref-lat`. Subsets are cached, so re-runs with different flags need no new downloads.

Comparison with Sentinel-1: [`quetta-check/nisar/compare_nisar_s1.py`](quetta-check/nisar/compare_nisar_s1.py) (needs `imagecodecs` to read the LiCSAR GeoTIFFs).

---

## 7. Viability: pros and cons

**Verdict:** viable, and the most distinctive option we evaluated. The key risk (does NISAR show it?) is now resolved.

### Pros
1. **Exactly on-brief:** subsidence is named in the challenge; InSAR is NISAR's headline capability.
2. **Big, real, current:** one of the world's fastest-sinking cities; confirmed in 2024–25 (Sentinel-1) and 2026 (NISAR).
3. **Triple validation:** literature + Sentinel-1 + NISAR agree → strong "Validity" score.
4. **Clear cause and effect, human-driven** — matches the challenge's emphasis on physical and human drivers.
5. **Differentiated:** most teams will choose floods, forests or glaciers; few will attempt InSAR.
6. **Strong story:** "A city of millions sinking over half a centimetre to a centimetre every month."
7. **Groundwork done:** data located, pipeline built and tested, first NISAR result in hand.

### Cons / risks
1. **Short NISAR record** (4 clean months on track 41) → rates are noisier than Sentinel-1's 1-year pairs.
2. **Atmospheric artifacts** on surrounding mountains; ionosphere correction currently counter-productive.
3. **Technical complexity:** unwrapping errors, reference choice, LOS-to-vertical conversion.
4. **Harder to explain:** InSAR is abstract; the app must translate to "cm per year" and maps.
5. **Large files:** GSLC (~22 GB) must be streamed; untested for the 11-month interferogram.
6. **Polarization question** is a weak fit (mitigate with a GCOV urban-growth layer).

### Compared with the Punjab floods idea
Floods were verified with NISAR preview images and are more intuitive, but crowded and complicated by rice-paddy flooding. Quetta wins on fit, validation and originality; floods remain a fallback.

---

## 8. 2050 sinking and damage scenarios (AI-assisted)

**Framing:** "AI-assisted risk scenarios to 2050", **not** "AI predicts 2050". Future sinking depends on future pumping, which no model can know; judges will attack an overconfident 24-year forecast.

| Layer | What it does | Data |
|---|---|---|
| 1. Measured now | Sinking rate per neighbourhood | NISAR (+ Sentinel-1 cross-check) |
| 2. Scenarios to 2030/2040/2050 | **Trend continues**; **keeps accelerating** (history: ~11 → 16 cm/yr, 2003–2016); **pumping controlled** (rate decays). Monte-Carlo uncertainty bands. | Measured rates + published history |
| 3. Damage risk | Uneven sinking → **angular distortion** under buildings → damage classes using standard geotechnical criteria (commonly cited: ~1/500 onset of cracking, ~1/150 serious damage — verify against Boscardin & Cording / Burland before use). Buildings and people per class per decade; **fissure-risk zones** at steep bowl edges. | Microsoft / Google Open Buildings footprints (both cover Pakistan), population grids |
| 4. AI — drivers | Random-forest model linking sinking to drivers (urban growth from radar backscatter, sediment/valley position, elevation); feature importance; fills gaps where radar lost coherence. RF performs best for spatial subsidence in published studies. | Rate map + driver layers |
| 5. AI — explainer | "Ask about your neighbourhood": Claude explains the local rate and 2050 risk in plain English/Urdu, grounded only in computed numbers. Pre-generate answers so no API key ships in the app. | Outputs above |

**Indicative headline (scenario arithmetic, not a measurement):** if today's 14–16 cm/yr continued, the fastest-sinking area would drop a further **~3.4–3.8 m by 2050**, on top of up to 2.7 m since 2003.

**Limits:** 80–100 m resolution → damage **zones**, not individual buildings; well locations, clay thickness and building types are not public; label as **risk screening**, not engineering assessment.

**Effort:** scenarios + damage ≈ 5–6 h; random forest ≈ 2–3 h; explainer ≈ 2 h. Cut the explainer first, the random forest second if time runs short.

---

## 9. 20-hour team plan (3 people + Claude)

Set up one GitHub repo with a `CLAUDE.md` holding this plan and an agreed **data contract** (file names/formats for rate maps, time series, scenario outputs) so all three Claude sessions share context and the app can start on dummy data.

| Hours | A — Data / InSAR | B — App | C — Story, validation, scenarios |
|---|---|---|---|
| 0–1 | Everyone: own Earthdata login (`_netrc`); repo + `CLAUDE.md`; re-run pipeline | App skeleton (map, slider, chart) | Gather facts/sources (Section 2) |
| 1–4 | Track 92 + 142 + 20 runs; atmospheric mask/elevation correction; investigate iono | App on dummy data | Slide outline; Sentinel-1 comparison figures |
| 4–10 | 11-month GSLC interferogram (money shot); final rate map + uncertainty; vertical conversion | Wire real data: swipe map, neighbourhood time series | Scenarios + damage model (Section 8) |
| 10–14 | Optional: asc/desc decomposition (vertical vs east-west); random-forest drivers | Polish, scenario slider to 2050, mobile layout | Draft slides; explainer text |
| 14–20 | Final data, credits | Deploy (e.g., GitHub Pages) | Video, rehearsal, submission page, buffer |

---

## 10. Presentation outline

1. **Hook:** "Quetta is sinking — over half a centimetre to a centimetre every month."
2. **Why:** groundwater pumping in an arid valley; compaction (one simple diagram).
3. **How NISAR sees it:** L-band InSAR, every 12 days, day/night, through clouds (one diagram).
4. **Money shot:** NISAR rate map over the city (and 11-month fringes if ready).
5. **Proof:** NISAR vs Sentinel-1 vs published studies — same bowl, same rate.
6. **Impact:** buildings/people in risk zones; fissures; infrastructure.
7. **2050 scenarios:** three futures with uncertainty; what changes if pumping is controlled.
8. **Live demo:** click a neighbourhood → rate, time series, 2050 scenario, plain-language explanation.
9. **Scale-up:** same pipeline for Lahore, Karachi, Multan — a national subsidence monitor refreshed every 12 days.

---

## 11. Open issues and next steps

- [x] Track 92 (descending) NISAR run — done: r = 0.80 vs Sentinel-1, bowl centred on the city.
- [x] Runs for tracks 142 and 20 — done; too noisy, excluded from the vertical map.
- [x] Ionosphere — explained: correct sign, but the screen's own uncertainty exceeds the 12-day signal.
- [x] Atmospheric correction — DEM phase–elevation fit; improved track 41 to r = 0.88.
- [x] 11-month GSLC interferogram — decorrelated; 132-day pair coherent (partial result).
- [x] Vertical/east decomposition using the files' LOS geometry — done.
- [x] Building footprints (Microsoft) and WorldPop population — done.
- [ ] Verify damage thresholds against the original geotechnical papers (1/150, 1/300, 1/500 checked against secondary sources only).
- [ ] Interactive website, slide deck (out of scope overnight).
- [ ] Public link (repo/website) and Space Apps submission — team.

---

## 12. File index

| Path | Contents |
|---|---|
| [`challenge-statement.md`](challenge-statement.md) | Challenge summary and resources |
| [`explainer.md`](explainer.md) / [`SUBMISSION.md`](SUBMISSION.md) / [`quetta-check/README.md`](quetta-check/README.md) / [`PLAN.md`](PLAN.md) | Plain-language explainer, project-page text, Quetta README, overnight plan and log |
| [`quetta-check/final/nisar/`](quetta-check/final/nisar/) | **FINAL** NISAR vertical/east/LOS velocity GeoTIFFs, maps, validation, `summary.json` |
| [`quetta-check/final/impact/`](quetta-check/final/impact/) | **FINAL** 2050 scenarios, damage-risk zones, exposure (`results_FINAL_annualized/`, `results_FINAL_as_measured/`), METHODS |
| [`quetta-check/final/moneyshot/`](quetta-check/final/moneyshot/) | Long-span GSLC interferograms (132-day coherent; 336-day decorrelated) |
| [`quetta-check/nisar/`](quetta-check/nisar/) | NISAR vs Sentinel-1 figure, track 41 map, time series CSVs, cumulative GeoTIFF, comparison script |
| [`quetta-check/sentinel1/`](quetta-check/sentinel1/) | Sentinel-1 maps (ascending, asc vs desc, wrapped phase) and scripts |
| [`quetta-check/pipeline/`](quetta-check/pipeline/) | NISAR pipeline, tests, README |
| [`quetta-check/preview-stack/`](quetta-check/preview-stack/) | Preview-image decoding attempt (inconclusive) |
| [`nisar-check/`](nisar-check/) | Earlier Punjab floods check (fallback project) |

---

## 13. Sources

**Quetta subsidence and groundwater**
- Remote Sensing 2024, Quetta Sentinel-1 study — <https://doaj.org/article/19dde210f0d642b1b4151146882ce457>
- Natural Hazards 2025, Quetta 2003–2023 — <https://www.link.springer.com/article/10.1007/s11069-025-07226-y>
- EGU25 abstract (2014–2024) — <https://meetingorganizer.copernicus.org/EGU25/EGU25-16369.html>
- AGU 2015 abstract (fissures, GPS) — <https://agu.confex.com/agu/fm15/webprogram/Paper69839.html>
- Dawn, "Quetta valley wells may run dry soon" — <https://www.dawn.com/news/1994905>
- Dawn, Quetta groundwater depletion — <https://www.dawn.com/news/1964668>
- Balochistan water crisis report — <https://www.newkerala.com/news/a/balochistan-edge-as-water-crisis-deepens-report-491.htm>

**Data and tools**
- ASF NISAR documentation — <https://nisar-docs.asf.alaska.edu/> (GUNW: <https://nisar-docs.asf.alaska.edu/gunw/>, availability: <https://nisar-docs.asf.alaska.edu/availability-overview/>)
- NASA: NISAR L-band data released — <https://www.earthdata.nasa.gov/news/nisar-l-band-data-released-expanding-record-surface-changes>
- earthaccess guide — <https://nisar-docs.asf.alaska.edu/earthaccess/>
- MintPy releases (`prep_nisar`) — <https://github.com/insarlab/MintPy/releases/latest>
- nisarqa (browse image code) — <https://github.com/isce-framework/nisarqa>
- OPERA products (DISP-NI status) — <https://nasa-opera.github.io/docs/products>
- COMET LiCSAR portal — <https://comet.nerc.ac.uk/comet-lics-portal>; Quetta frames: <https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products.public/42/042A_05933_131313/>, <https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products.public/151/151D_06038_131313/>

**Damage and prediction methods**
- Peduto et al. 2017, InSAR building damage — <https://www.iris.unisa.it/bitstream/11386/4679709/3/POST-PEER_PREPRINT_PEDUTO_ET_AL_2017_ENGEO.pdf>
- Sanabria et al. 2014, NHESS — <https://nhess.copernicus.org/articles/14/1341/2014/nhess-14-1341-2014.pdf>
- Frontiers 2025, InSAR + machine learning — <https://www.frontiersin.org/articles/10.3389/feart.2024.1503634/full>
- IEEE JSTARS 2025, Xi'an RF subsidence — <https://doaj.org/article/ba306953d1c84f5098804ff9af7a892b>
- EGU26 physics-informed LSTM abstract — <https://meetingorganizer.copernicus.org/EGU26/EGU26-16451.html>
- Google Open Buildings — <https://sites.research.google/open-buildings/>
- Microsoft building footprints — <https://github.com/microsoft/globalmlbuildingfootprints>
