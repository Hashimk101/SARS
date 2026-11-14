# Dancing with the SARs — NASA Space Apps Challenge 2026

- **Official page:** https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/
- **Resources tab:** https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources
- **Subject:** Earth Science
- **Difficulty:** Intermediate, Advanced
- **Saved:** 2026-11-14 (summary in my own words; see the official page for exact wording, and check it for resources added later)

---

## The challenge in one sentence

Build an **interactive application** that uses radar data from the **NASA-ISRO Synthetic Aperture Radar (NISAR)** mission to **track and visualize one or more types of surface change** at locations around the world.

## Background

### Passive vs. active remote sensing
- Most Earth-observing instruments are **passive**: they measure sunlight reflected off the surface. Different materials (water, rock, vegetation) reflect different wavelengths, giving each a "spectral fingerprint".
- Radar is **active**: it emits its own energy, in the **microwave** band, and measures what bounces back.

### What SAR is
- **Synthetic Aperture Radar** combines many acquisitions from a short physical antenna as the satellite moves, "synthesizing" a much longer antenna and so getting higher spatial resolution.
- It works **day or night and through clouds**, which makes it valuable during disasters (oil spills, wildfires, hurricanes, floods).

### What radar is sensitive to
1. **Surface roughness**: drives backscatter. Together with **polarization**, it reveals structure, geometry and material properties.
2. **Dielectric constant**: water's is high, so SAR highlights **water bodies, flood inundation and soil moisture**.
3. SAR can also measure **centimeter-scale ground movement** (earthquakes, land subsidence) via interferometry.

Radar images are not like ordinary optical satellite photos. Bright and dark areas mean roughness and moisture, not color.

## Objectives

### Types of surface change to choose from
- Wetlands and floodplains expanding and retreating
- Forest loss from deforestation and wildfire
- Agricultural land changing crop type and crop health
- Soil moisture swelling and shrinking
- Glacier and sea-ice movement
- Land deformation from earthquakes and coastal subsidence

These changes affect ecosystems, water resources, agriculture, infrastructure and local communities.

### Desired outcome
An **open-source, user-friendly** tool that turns complex radar observations into **actionable insights**. The audience includes scientists, resource managers, educators, decision-makers and the public. It should show the patterns and rhythms of surface change across different time steps.

Suggested formats: **interactive change-detection maps, time-series animations, dashboards**.

### Suggested workflow
1. **Pick a study area.** Examples: your hometown, a tropical wetland, an ice sheet, a wildfire, a flooded neighborhood, a volcanic eruption.
2. **Download NISAR data** using the listed resources. Optionally add **optical imagery or GIS layers** for context.
3. **Present your findings** in an interactive digital medium: report, video, slides, story map, or something more creative (the statement jokingly suggests an interpretive dance).
4. **Hypothesize the physical drivers** behind what you see, or don't see. The statement's example questions:
   - Why might vegetation change over time (e.g. in the Amazon)?
   - Which polarizations highlight changes on land and on ice?
   - What future applications of NISAR are possible?

## Potential considerations (optional)
- Analyze NISAR data across **different polarizations** and/or **different frequencies** (from other sensors).
- Use **multiple dates** to build a **time series**.
- Add **ancillary datasets** (population, vegetation type, etc.) for context.
- Show how **human drivers** (agriculture, industry) affect natural resources.
- Focus on **compelling data storytelling**.
- If you know the study area personally, add **personal context and stories**.
- Make the summary **interactive** (image sliders, web maps).

---

## Resources (from the challenge's Resources tab)

> The page notes that NASA doesn't endorse non-U.S. Government sites and that participants must follow each site's data-use terms.

### NASA data and resources
| Resource | What it's for |
|---|---|
| [NASA Earthdata Search](https://search.earthdata.nasa.gov/search) | Discover, compare, visualize and download NASA Earth science data |
| [ASF Data Search (Vertex)](https://search.asf.alaska.edu/) | Alaska Satellite Facility, NASA's SAR data archive. **Main place to get NISAR data.** |
| [NISAR Data User Guide](https://nisar-docs.asf.alaska.edu/) | ASF's one-stop guide to accessing and working with NISAR data |
| [Intro to Remote Sensing](https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/remote-sensing) | Basics: instrument characteristics, types of resolution, processing |
| [Intro to SAR](https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/sar) | Basics: frequency/wavelength, polarization, scattering mechanisms |
| [NASA ARSET Trainings](https://appliedsciences.nasa.gov/get-involved/training) | Online trainings, including intro remote sensing, SAR and NISAR material (English and Spanish) |
| [NISAR StoryMaps](https://nisar.jpl.nasa.gov/applications/arcgis-storymaps/) | Interactive examples: floods, wildfires, subsidence, oil slicks, glacier motion |
| [NISAR Applications White Papers](https://nisar.jpl.nasa.gov/applications/societal-benefit/) | 2-page overviews of NISAR's societal-benefit applications |
| [UAVSAR Postcards](https://uavsar.jpl.nasa.gov/education/postcards.html) | False-color composites of airborne UAVSAR data showing Earth processes |

### Space agency partner resources

**Canadian Space Agency (CSA)**
| Resource | What it's for |
|---|---|
| [RADARSAT Constellation Mission (RCM) data](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm) | Three-satellite all-weather SAR constellation for maritime, disaster and ecosystem monitoring |
| [SAR Python Tutorial](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial) | Practical steps for accessing and visualizing SAR imagery with Python and QGIS |
| [RADARSAT-1 data](https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1) | Open-licensed archive from RADARSAT-1 (launched 1995). Useful for long historical baselines. |

**National Space Activities Commission of Argentina (CONAE)**
| Resource | What it's for |
|---|---|
| [SAOCOM Catalogue](https://catalogos.conae.gov.ar/catalogo/catalogoSatSaocomInfo.html) | CONAE's SAR mission catalogue, with download and processing tutorials |
| [SAOCOM Catalogue Registration](https://www.argentina.gob.ar/noticias/la-informacion-saocom-cada-vez-mas-accesible) | How to register a "ONE CLICK" login profile to access SAOCOM data |
