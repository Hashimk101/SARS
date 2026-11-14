# Scientific & Software Engineering Best Practices

## 1. SAR Scientific Computing Standards

### A. Memory Efficiency with Large Arrays
NISAR HDF5 files can be 1 GB to 5 GB. Never load an entire multi-frequency granule into RAM unwindowed.
- **Chunked Reading with `h5py`:** Always slice the specific 2D sub-array corresponding to your bounding box:
  ```python
  with h5py.File(filepath, 'r') as h5:
      # Slice specific pixel rows and cols rather than dataset[:]
      ds = h5['/science/LSAR/GCOV/grids/frequencyA/HHHH']
      subset = ds[row_start:row_end, col_start:col_end]
  ```
- **Avoid Repeated Decibel Recomputations:** Compute $\text{dB}$ once, apply masking, and save intermediate rasters as compressed COG (`TIFFTAG_COMPRESSION=DEFLATE` or `LZW`).

### B. Masking & No-Data Handling
- Raw NISAR arrays use fill values (commonly `NaN` or `-9999.0`).
- Always apply the dataset mask located at `/science/LSAR/GCOV/grids/frequencyA/mask`.
- Avoid $\log_{10}(0)$ or $\log_{10}(\text{negative})$ runtime warnings:
  ```python
  # Safe linear-to-dB conversion
  valid_mask = (linear_power > 0) & np.isfinite(linear_power)
  db_array = np.full_like(linear_power, np.nan, dtype=np.float32)
  db_array[valid_mask] = 10.0 * np.log10(linear_power[valid_mask])
  ```

### C. Coordinate Systems & Projection Hygiene
- NISAR L2 GCOV is already geocoded, but it is projected in a local UTM zone (e.g., `EPSG:32642`).
- Web map libraries (MapLibre GL, Leaflet) require **WGS84 (`EPSG:4326`)** for geo-coordinates and **Web Mercator (`EPSG:3857`)** for raster tiles.
- Use `rasterio.warp.reproject` or `rioxarray` with bilinear or cubic resampling to project rasters before feeding them to web tiles or bounding-box overlays.

---

## 2. Frontend & UX Best Practices

### A. Instant Load Times (Sub-Second First Paint)
- Do not let the web browser parse GeoTIFFs dynamically on the main thread if it causes frame drops.
- Pre-render high-impact visual layers as optimized PNG/WebP overlays with precise `[north, south, east, west]` bounds for instant rendering.
- Keep the bundled demo dataset lightweight (< 15 MB total) so anyone judging from a laptop or mobile phone gets an instant, 60fps experience.

### B. Scientific Tooltips & Self-Explaining UI
- Every acronym must have a tooltip:
  - `HH`: "Horizontal Transmit, Horizontal Receive — sensitive to structure and surface roughness"
  - `HV`: "Horizontal Transmit, Vertical Receive — sensitive to volume scattering from vegetation"
  - `dB`: "Decibels — logarithmic scale of radar backscatter power"
- Include an interactive legend that clearly connects color to physical surface properties (Green = Forest, Dark = Water, Pink = Urban / Double-Bounce).

### C. Responsive & Demo-Ready
- Make sure the UI layout fits both widescreen 1080p/4K monitors and laptop screens without horizontal scrollbars or clipping controls.
- Provide a 1-click **"Guided Tour"** or **"Demo Mode"** that automatically steps judges through the narrative points without them needing to guess what buttons to click.

---

## 3. Code Quality & Modularity Rules
- **No Monolithic Files:** Keep data processing, API handlers, math algorithms, and UI components cleanly separated.
- **Type Safety & Documentation:** Use TypeScript for frontend components and Python type hints (`np.ndarray`, `Path`, `Tuple[float, float]`).
- **Reproducibility:** Maintain clean `requirements.txt` / `pyproject.toml` for Python and clean `package.json` with lockfiles for frontend dependencies.
