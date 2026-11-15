# Overnight Plan: Quetta Sinking (NASA Space Apps 2026)

*Written 2026-11-15 02:45 local. Target: everything ready by about 09:00. Hard deadline: **Sunday Nov 15, 11:59 PM** (Local Event time zone, or the Team Owner's local time if registered for the Universal Event).*

Project brief: [`quetta-subsidence.md`](quetta-subsidence.md)

---

## What the judges need (official 2026 submission guide)

| Field | What we provide |
|---|---|
| Project Name | Placeholder: **"Sinking City: Quetta"**. The team decides the final name. |
| High-Level Summary | Short paragraph (in `SUBMISSION.md`) |
| **Link to Project Demo** | **7-slide deck** (title and intro count toward the 7), English, public link. Optional silent captioned video of 30 s or less. |
| **Link to Final Project** | Public website (interactive app plus method) and code repo; no login, password or permission needed |
| Detailed Description | What it does, how it works, tools used (in `SUBMISSION.md`) |
| Use of SI (AI) | Must state where and how AI was used. AI images/videos need a visible watermark; code/data need acknowledgement in text and metadata. Note the rule that AI "should not be used to come up with your idea"; the team should describe the idea's origin honestly. |
| NASA Data | NISAR (required: at least one NASA data source) |
| Partner data and references | ESA Sentinel-1 via COMET LiCSAR, ISRO (NISAR partner), building footprints, population, all code and tools |
| Images | The project page accepts JPG/PNG/GIF images up to 10 MB |

Judging criteria: **Impact, Creativity, Validity, Relevance, Presentation.** No NASA logos or branding in generated content.

---

## Overnight blocks (Claude works; times are targets)

### Block 1: Make the NISAR result solid (02:45–04:00), MUST
- [ ] Finish track 92 (descending, running now); also run tracks 142 and 20.
- [ ] Remove weather noise: fit phase against elevation (Copernicus DEM, public) outside the valley, per date, so the "sinking" blobs on the mountains disappear.
- [ ] Time-box the ionosphere-correction question (20 min); otherwise document it.
- [ ] Per-pixel rate **with uncertainty**; combine tracks.
- [ ] If the viewing-angle data is readable: ascending plus descending gives **vertical vs east–west** motion. Otherwise, label results as line-of-sight.
- **Output:** final rate GeoTIFF/PNG and JSON for the app; updated NISAR vs Sentinel-1 validation figure.

### Block 2: The money shot (04:00–04:45), SHOULD
- [ ] 11-month NISAR interferogram from two GSLCs (track 41, 2025-11-25 → 2026-10-27), streaming only Quetta.
- Fallback if it fails or takes too long: NISAR rate map plus the Sentinel-1 1-year rings image.

### Block 3: Impact and 2050 scenarios (04:45–05:45), MUST (lite)
- [ ] Building outlines for Quetta (Microsoft/Google open data) and a population grid (WorldPop).
- [ ] Three scenarios to 2030/2040/2050 (trend continues / keeps accelerating / pumping controlled), Monte-Carlo uncertainty bands.
- [ ] Damage-risk zones from uneven sinking (angular distortion); counts of buildings and people per risk class per decade.
- Stretch: random-forest "why is it sinking" drivers.

### Block 4: Interactive web app (05:45–07:45), MUST
- [ ] Static site: map with NISAR rate layer, Sentinel-1 comparison toggle, 2026→2050 scenario slider, damage zones.
- [ ] Click a neighbourhood: rate ± uncertainty, NISAR time series, Sentinel-1 value, 2050 scenarios, plain-language explanation (pre-written, labelled as AI-assisted).
- [ ] Story sections: problem → how NISAR sees it → proof → impact → limitations → credits and SI disclosure.
- [ ] Test in the browser pane (desktop and phone width).
- Hosting: GitHub Pages (needs the user's OK to publish under their account) or another public host.

### Block 5: Submission package (07:45–08:45), MUST
- [ ] **7-slide deck** (PDF + PPTX): title · problem · how NISAR sees it · result · validation · impact and 2050 · future.
- [ ] Optional 30-second captioned video built from the slides (ffmpeg is installed).
- [ ] `SUBMISSION.md`: every form field ready to paste.
- [ ] Repo `README.md`: reproduction steps, data licences and attributions.

### Block 6: QA and buffer (08:45–09:00)
- [ ] Numbers consistent across app, slides and text; links work without login; mobile view OK.

---

## What only the user can do (morning)
1. Choose the **project name** (and team details for the title slide).
2. **Approve publishing**: public GitHub repo plus website under your account (or push it yourself).
3. **Submit on the Space Apps site** (your login): paste the text, add links and images, press submit.
4. Confirm the **deadline time zone** (Local Event vs Universal Event).
5. Decide how to word the **SI disclosure**, including how the idea was chosen.

## Fallbacks
- NISAR improvements fail → ship the current confirmed result (r = 0.67 vs Sentinel-1) with honest caveats.
- 2050 damage data too slow → scenarios on the rate map only, without building counts.
- No hosting approval → zip the site plus the deck as a shareable folder; the user uploads to Drive/GitHub.

## Status log
- 02:45 Plan written. Track 92 NISAR run in progress.
- 02:55 Track 92 done: bowl centred on the city (−5.4 cm in 120 days), r = 0.80 vs Sentinel-1. Saved to `quetta-check/nisar/`.
- 03:05 **Scope set by user: everything EXCEPT the interactive website, slide deck and video.** Three Sonnet agents launched: Block 1 (final NISAR maps → `quetta-check/final/nisar/`), Block 2 (money shot → `quetta-check/final/moneyshot/`), Block 3 (impact and 2050 → `quetta-check/final/impact/`). Claude writes `SUBMISSION.md` and `README.md` and reruns impact on the final maps.
- 03:55 Block 2 (money shot) done, partial: the 336-day GSLC pair is decorrelated (coherence 0.11; BETA vs V1 files). The 132-day pair (Jun 17 → Oct 27) is coherent (0.47) and shows a ~2–3 cm LOS local anomaly at the city centre, consistent with sinking but noisy. Headline visual stays the track 92 cumulative map. Files in `quetta-check/final/moneyshot/`.
- 04:30 Block 3 (impact) built and run on a PROVISIONAL rate map (biased high: ~22 cm/yr vertical bowl max vs ~14 expected). Data: Microsoft building footprints (195k in the AOI), WorldPop 2025 100 m, Copernicus DEM. Rerun pending the final NISAR vertical map (Block 1). Files in `quetta-check/final/impact/`.
- 04:45 Block 1 (final NISAR) done: DEM correction raised track 41 to r = 0.88 and track 92 to r = 0.82; vertical map (41 + 92) bowl median −8.7 cm/yr, r = 0.89 vs Sentinel-1, east–west ≈ 0. Tracks 142 and 20 too noisy (excluded). Ionosphere explained (screen uncertainty > signal).
- 05:05 Impact rerun on the final map, both as measured and annualized ×0.75 (Sentinel-1 full-year/summer ratio). 2050 current trend: 46 km² sinks ≥ 1 m (≈ 49k buildings); pumping controlled: 6 km². Fixed a stale "replace with final" subtitle in the figures.
- 05:15 SUBMISSION.md finalized (demo/link fields still TODO; SI wording is a TEAM decision), README.md written, brief updated (§4.5). **Overnight scope complete.** Remaining: website, slides, public link, submission.
