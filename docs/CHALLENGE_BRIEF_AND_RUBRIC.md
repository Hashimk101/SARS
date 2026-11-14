# NASA Space Apps 2026 — "Dancing with the SARs" Master Brief

## 1. Core Objective
Build an open-source, user-friendly interactive application using **NASA-ISRO Synthetic Aperture Radar (NISAR)** data to track, visualize, and explain surface changes over time. The app must translate complex radar backscatter/phase observations into actionable insights for scientists, resource managers, educators, or the public.

## 2. Mandatory Deliverables & Judging Rubric (1–5 Scale per Category)
To advance from **Local Nominee -> Global Finalist -> Top 10 Global Winner**, every feature must serve these 5 criteria:

1. **Relevance (Deep NASA Data Integration):**
   - NISAR data cannot be a static screenshot or cosmetic backdrop.
   - Must show real data ingestion, multi-date temporal comparison, polarization switching (`HH`, `HV`, `VV`, `VH`), or ancillary data fusion (optical, rainfall, elevation, population).
2. **Validity (Scientific & Technical Accuracy):**
   - Ground insights in real radar physics: **surface roughness** and **dielectric constant**.
   - Explicitly state physical drivers behind observed changes (e.g., why flooded forests brighten due to double-bounce scattering rather than darkening like open water).
3. **Impact:**
   - Focus on a clear real-world problem (flood response, agricultural groundwater depletion, wildfire burn scars, coastal subsidence, glacial retreat) with measurable societal utility.
4. **Creativity:**
   - Go beyond a generic map viewer.
   - Dual-polarization RGB false-color composers, interactive split-screen swipe sliders, audio/sonification of SAR time-series ("dancing" rhythms), or automated change-detection alerts.
5. **Presentation (Storytelling):**
   - Structure the app as a guided narrative.
   - Judges evaluate both the **30-second / 3-minute demo video** and the **live interactive web app**.

## 3. Target Global Award Categories to Aim For
- **Best Use of Data:** Making complex NISAR HDF5 products accessible to non-experts.
- **Best Use of Science:** Rigorous multi-polarization or InSAR phase analysis with physical hypothesis testing.
- **Local Impact / Galactic Impact:** Solving a critical regional disaster or resource challenge (e.g., Indus Basin floods/irrigation, Himalayan glacial lake outburst floods, coastal subsidence).

## 4. Challenge Context & Background
Earth remote sensing helps us acquire information from a bird's eye view. Unlike passive sensors that rely on reflected solar energy and are blinded by darkness and clouds, active radar instruments emit microwave pulses and measure what bounces back:
- **Active microwave sensing:** Operates day and night, penetrates rain, smoke, and cloud cover.
- **Wavelength sensitivities:** L-band (NASA, 24 cm) penetrates deep into tree canopies and dry soils; S-band (ISRO, 10 cm) is sensitive to light vegetation, crop geometry, and surface roughness.
- **Key Radar Sensitivities:**
  - *Roughness:* Smooth surfaces (calm water, paved runways) bounce pulses away specularly (dark); rough surfaces (plowed fields, rocks) bounce energy back diffusely (moderate/bright).
  - *Dielectric Constant:* Water has a very high dielectric constant (~80 vs ~3-5 for dry soil), drastically amplifying radar reflectivity and backscatter.
