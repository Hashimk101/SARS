import { useEffect, useState } from 'react'

export type HotspotId = 'indus' | 'quetta' | 'islamabad' | 'siachen'
export type Scenario = 'current_trend' | 'accelerated' | 'controlled'

export const HOTSPOT_IDS: HotspotId[] = ['indus', 'quetta', 'islamabad', 'siachen']

/** Coordinates from docs/BACKEND_API_SPECIFICATION.md — lets the 3D scene place markers before the API answers. */
export const COORDS: Record<HotspotId, { lat: number; lon: number; short: string }> = {
  indus: { lat: 26.85, lon: 68.1, short: 'Indus Basin' },
  quetta: { lat: 30.175, lon: 66.984, short: 'Quetta Valley' },
  islamabad: { lat: 33.729, lon: 73.093, short: 'Margalla Hills' },
  siachen: { lat: 35.421, lon: 77.109, short: 'Siachen Glacier' },
}

export interface Metric {
  label: string
  value: string
  unit: string
}
export interface Chapter {
  step: number
  title: string
  body: string
  metrics: Metric[]
}
export interface HotspotSummary {
  id: HotspotId
  name: string
  location: string
  lat: number
  lon: number
  badge: string
  severity: string
  short_desc: string
}
export interface Granule {
  scene_name: string
  platform: string
  polarization: string
  flight_direction?: string
  acquisition_time?: string
  download_url: string
  file_size_mb: number
}
export interface HotspotDetail extends Omit<HotspotSummary, 'lat' | 'lon'> {
  coordinates: { lat: number; lon: number }
  scientific_context: {
    satellite_mission: string
    polarization_channels: string
    hdf5_group: string
    hdf5_datasets: Record<string, string>
    preprocessing_rule: string
    physical_phenomenon: string
  }
  chapters: Chapter[]
  sonification: {
    sound_theme: string
    base_frequency_hz: number
    mod_frequency_hz: number
    waveform: OscillatorType
    tension_curve: number[]
  }
  live_environmental?: {
    soil_moisture_topsoil_m3m3: number
    soil_moisture_subsurface_m3m3: number
    current_precipitation_mm: number
    timestamp: string
  }
  nasa_asf_granules?: Granule[]
}
export interface TimelinePoint {
  date: string
  epoch: string
  primary_val: number
  secondary_val?: number
  note: string
  [extra: string]: string | number | undefined
}
export interface Timeline {
  metric_primary: string
  metric_secondary: string
  unit_primary: string
  unit_secondary: string
  series: TimelinePoint[]
}
export interface Drivers {
  model_type: string
  training_samples?: number
  spatial_block_cv_r2: number
  feature_attribution_importance: Record<string, { importance_score: number; description: string }>
  scientific_synthesis: string
}
export interface Simulation {
  year: number
  scenario: Scenario
  metric_projected: string
  risk_level: string
  damage_reduction_pct: number
  policy_summary: string
  monte_carlo_draws?: number
  [k: string]: unknown
}
export interface Figure {
  id: string
  title: string
  description: string
  api_url: string
  tags: string[]
}
export interface Health {
  version: string
  supported_missions: string[]
}

const BASE = import.meta.env.VITE_API_URL ?? ''

export async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(BASE + path, { signal })
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json() as Promise<T>
}

export const figureSrc = (url: string) => (url.startsWith('http') ? url : BASE + url)

export interface ApiState<T> {
  data: T | null
  error: boolean
}

/** Fetch-on-mount with abort on path change. `null` path skips the request. */
export function useApi<T>(path: string | null): ApiState<T> {
  const [state, set] = useState<ApiState<T> & { path: string | null }>({ data: null, error: false, path })
  useEffect(() => {
    if (!path) return
    const ctl = new AbortController()
    get<T>(path, ctl.signal)
      .then((data) => set({ data, error: false, path }))
      .catch((e: Error) => {
        if (e.name !== 'AbortError') set({ data: null, error: true, path })
      })
    return () => ctl.abort()
  }, [path])
  // Never show a previous path's payload under a new path.
  return state.path === path ? state : { data: null, error: false }
}
