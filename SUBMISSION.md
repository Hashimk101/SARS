# Space Apps 2026 — Project Page Text

*Copy each section into the matching field on the team's Project tab. **[TODO]** = still to produce (demo, public link); **[TEAM]** = needs a team decision. Numbers are final as of 2026-11-15 (see `quetta-check/final/`).*

---

## Project Name
**SAR-Pulse: Dancing with the SARs** *(Flagship Validation Study: Sinking City Quetta)* **[TEAM: final name]**

## High-Level Project Summary
Across four critical Pakistani biomes—urban subsidence, mega-monsoon inundation, protected forest fragmentation, and Himalayan cryosphere surge—ground radar observations have historically been sparse. **SAR-Pulse** transforms NASA-ISRO NISAR L-band and ISRO S-band radar data into an open, real-time national radar observatory.

In our flagship deep-dive validation study, we focus on **Quetta**, home to over two million people in arid Balochistan where groundwater over-pumping is compacting the valley floor. Published studies estimate up to 2.7 m of subsidence since 2003. We used radar interferometry from the new NASA–ISRO NISAR satellite to measure this from orbit through 2026. Combining NISAR's ascending and descending views, we mapped a sinking bowl centred on the city: the ground inside it is moving straight down by a median of about 9 cm per year, and the core sinks fastest. Independent ESA Sentinel-1 data match the NISAR map (correlation r = 0.89). We then turned the measurements into 2050 risk scenarios. If today's rates continue, about 46 km² of the valley sinks at least a further metre by 2050, affecting about 49,000 buildings and 860,000 people. If pumping is brought under control, that falls to about 6 km² and 7,000 buildings. The platform gives water managers, planners, and residents across Pakistan an open, repeatable way to see where the ground and ecosystems are moving, how fast, and what is at stake.

## Link to Project Demo
**[TODO — 7-slide deck or ≤30-second video; public link, English]**

## Link to Final Project
https://sars-visualize.vercel.app/ *(Zero login required; interactive platform and API documentation)*

## Detailed Project Description

### What it does
- **Measures** how fast each part of Quetta is sinking, using NISAR L-band radar interferometry (InSAR) from June–October 2026, and separates vertical sinking from sideways motion by combining NISAR's ascending and descending views.
- **Validates** the result against independent ESA Sentinel-1 data (2024–2025) and published GNSS/InSAR studies.
- **Projects** three scenarios to 2030, 2040 and 2050 (current trend continues; keeps accelerating; pumping brought under control), with Monte-Carlo uncertainty.
- **Maps damage-risk zones** where uneven sinking could crack buildings, and counts the buildings and people exposed.

### How it works
1. **Data discovery and access:** NISAR Level-2 geocoded unwrapped interferograms (GUNW, 80 m) over Quetta are found with the ASF DAAC search API; only the Quetta area is streamed from each ~2.3 GB HDF5 file using `earthaccess` + `h5py`, so no full downloads are needed.
2. **Time series:** for each orbit track, nine consecutive 12-day interferograms are masked for low coherence and unwrapping errors, referenced to stable bedrock outside the valley, corrected for terrain-correlated atmospheric delay using the Copernicus DEM, and summed into cumulative motion; a per-pixel velocity and its uncertainty are fitted through all dates.
3. **Vertical vs sideways:** the ascending (track 41) and descending (track 92) line-of-sight velocities are combined using the viewing geometry stored in the NISAR files, giving vertical and east–west velocity. East–west motion in the bowl is about zero: the city is going straight down.
4. **Validation:** the NISAR map is compared pixel-by-pixel with an independent one-year Sentinel-1 interferogram processed by COMET LiCSAR.
5. **Scenarios and risk:** the vertical-velocity map drives 500 Monte-Carlo runs per scenario. NISAR covers only the summer pumping season, so we also scale rates to an annual equivalent using Sentinel-1's full-year/summer ratio (×0.75). The slope of the projected sinking surface (angular distortion) is compared with standard geotechnical damage thresholds (1/1000 to 1/150) and intersected with open building footprints (Microsoft, about 195,000 in the area) and population data (WorldPop 2025).

### Key results
| | NISAR ascending (track 41) | NISAR descending (track 92) | NISAR vertical (combined) | Sentinel-1 (2024–25) |
|---|---|---|---|---|
| Period | Jun 17 – Oct 15, 2026 | Jun 20 – Oct 18, 2026 | Jun – Oct 2026 | Sep 2024 – Sep 2025 |
| Correlation with Sentinel-1 across the valley | r = 0.88 | r = 0.82 | **r = 0.89** | — |
| Median rate inside the sinking bowl | −6.6 cm/yr (line of sight) | −7.3 cm/yr (line of sight) | **−8.7 cm/yr (vertical)** | −6.5 LOS ≈ −8.3 vertical |
| City centre | −2.9 cm in 120 days | −5.4 cm in 120 days | −18 ± 4 cm/yr (summer rate) | — |

- Valley area sinking faster than 5 cm/yr: **59 km²**; faster than 10 cm/yr: **18 km²**.
- The sinking bowl is centred at 66.984°E, 30.175°N, the city centre.

**2050 scenarios** (annualized rates; median; valley floor of 124 km², about 112,000 buildings and 1.7 million people):

| Scenario | Valley area sunk ≥ 1 m | Buildings / people in that area | Buildings in moderate–severe damage-risk zones |
|---|---|---|---|
| Current trend | 46 km² | ~49,000 / ~860,000 | ~5,500 |
| Keeps accelerating | 52 km² | ~56,000 / ~960,000 | ~12,800 |
| Pumping controlled | 6 km² | ~7,300 / ~140,000 | ~0 |

The fastest-sinking 1% of the valley would drop roughly a further 3.4–4.5 m by 2050 if current rates continued.

### Limitations (stated openly)
- NISAR rates come from about 120 days of 2026 data, extrapolated to a year; bowl medians agree with Sentinel-1, but peak values are higher, likely because of summer pumping and residual noise.
- Some weather/terrain artifacts remain on the surrounding mountains; areas outside the bowl carry a small positive bias, so they are not real uplift.
- NISAR products used are PROVISIONAL (not yet fully validated by the mission).
- 2050 figures are scenarios under stated assumptions, not forecasts; damage classes are zone-level screening on an 80 m grid, not building inspections. Buildings and population are held at 2025 levels.

### Benefits
- An open, repeatable, satellite-based subsidence monitor that works day and night and through clouds, refreshed every 12 days by NISAR.
- Turns abstract radar data into "how fast is my neighbourhood sinking, and what could that mean by 2050?", the actionable view planners, water authorities and residents need.
- Shows the value of action: controlling pumping cuts the area sinking a further metre by 2050 from about 46 km² to about 6 km².
- The same pipeline can be pointed at other sinking cities (e.g., Lahore, Karachi, Multan).

### What we hope to achieve
Make Quetta's slow-moving disaster visible early enough to support groundwater management, safer construction, and monitoring of fissure-prone zones at the edges of the sinking bowl.

### Tools, languages and software
Python (numpy, scipy, h5py, earthaccess, pyproj, rasterio, pandas, scikit-learn, matplotlib, tifffile); ASF DAAC search API and NASA Earthdata; COMET LiCSAR Sentinel-1 products; Copernicus DEM GLO-30; Microsoft Global ML Building Footprints; WorldPop.

## Use of Super Intelligence (SI)
**[TEAM: review and edit — this answer must be accurate.]**

Yes. We used Anthropic's Claude (an AI assistant, including Claude Code with sub-agents) to:
- search for and summarise literature and documentation (NISAR product specs, ASF documentation, published Quetta studies);
- locate datasets and write the data-access and processing code (NISAR streaming pipeline, time-series and velocity estimation, terrain correction, vertical/east decomposition, Sentinel-1 comparison, scenario and damage-risk models);
- run the analyses and produce the figures (all figures are plotted by code from the satellite and open datasets, not made by image-generation models);
- draft and edit project text, including this page.

All AI-assisted code is acknowledged in `quetta-check/README.md`; all numbers come from code run on the cited datasets.

> **[TEAM note — do not paste]** The rules say SI "should not be used to come up with your idea of how to solve the challenge." The Quetta direction emerged from AI-assisted research after the team asked for alternative directions, and the team chose it. Describe the idea's origin honestly in this field.

## NASA Data
- **NISAR** (NASA–ISRO Synthetic Aperture Radar) L-band data from the ASF DAAC:
  - Level-2 **GUNW** (geocoded unwrapped interferograms), PROVISIONAL, June–October 2026: ascending tracks 41 and 142 (frame 17), descending tracks 92 and 20 (frame 73). Tracks 41 and 92 form the final vertical map; 142 and 20 were processed and found too noisy.
  - Level-2 **GSLC** (geocoded single-look complex), track 41: a 132-day interferogram (2026-06-17 → 10-27) built directly from two GSLCs as an independent check.
- NASA Earthdata / ASF DAAC search API and `earthaccess` for discovery and access; ASF NISAR Data User Guide.

## Space Agency Partner Data and Other References
**Partner data**
- **ESA — Copernicus Sentinel-1**: interferograms processed by COMET LiCSAR (frames 042A_05933_131313 and 151D_06038_131313). Contains modified Copernicus Sentinel data (2024–2025). We acknowledge COMET and the Copernicus programme.
- **ESA / Copernicus DEM GLO-30**: © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA.
- **ISRO**: NISAR mission partner (L-band data used; S-band not used).

**Other data**
- Microsoft Global ML Building Footprints (release 2026-02-03), ODbL.
- WorldPop 2025, 100 m, Pakistan (constrained), CC BY 4.0.

**Published research and sources**
- Quetta subsidence, Sentinel-1/GNSS (Remote Sensing, 2024): https://doaj.org/article/19dde210f0d642b1b4151146882ce457
- Quetta subsidence 2003–2023 (Natural Hazards, 2025): https://www.link.springer.com/article/10.1007/s11069-025-07226-y
- EGU 2025 abstract, Pakistan subsidence 2014–2024: https://meetingorganizer.copernicus.org/EGU25/EGU25-16369.html
- AGU 2015 abstract, Quetta fissures/GPS: https://agu.confex.com/agu/fm15/webprogram/Paper69839.html
- Dawn (2026), Quetta groundwater: https://www.dawn.com/news/1994905 , https://www.dawn.com/news/1964668
- InSAR building-damage assessment: Peduto et al. 2017 (https://www.iris.unisa.it/bitstream/11386/4679709/3/POST-PEER_PREPRINT_PEDUTO_ET_AL_2017_ENGEO.pdf); Sanabria et al. 2014 (https://nhess.copernicus.org/articles/14/1341/2014/nhess-14-1341-2014.pdf)
- Geotechnical damage criteria: Skempton & MacDonald (1956); Bjerrum (1963); Burland (1995) — as cited in `quetta-check/final/impact/METHODS.md`
- ASF NISAR documentation: https://nisar-docs.asf.alaska.edu/ ; COMET LiCSAR portal: https://comet.nerc.ac.uk/comet-lics-portal

**Software and tools**
- earthaccess, h5py, numpy, scipy, pyproj, rasterio, pandas, scikit-learn, matplotlib, tifffile; MintPy (reference for NISAR GUNW handling).
