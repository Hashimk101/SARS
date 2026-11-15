import { useEffect, useState } from 'react'
import { get, type HotspotId, type Scenario, type Simulation as Sim } from '../api'
import { fmt, humanize, useWidth } from './ui'

export const SCENARIOS: { id: Scenario; label: string }[] = [
  { id: 'controlled', label: 'Controlled' },
  { id: 'current_trend', label: 'Current trend' },
  { id: 'accelerated', label: 'Accelerated' },
]
const YEARS = [2026, 2030, 2034, 2038, 2042, 2046, 2050]

interface Band {
  key: string
  p10: number
  median: number
  p90: number
}

/** The API names its percentile block differently per hotspot; find it structurally. */
function band(sim: Sim): Band | null {
  for (const v of Object.values(sim)) {
    if (!v || typeof v !== 'object') continue
    const e = Object.entries(v as Record<string, number>)
    const pick = (p: string) => e.find(([k]) => k.startsWith(p))
    const m = pick('median')
    const lo = pick('p10')
    const hi = pick('p90')
    if (m && lo && hi) return { key: m[0], p10: lo[1], median: m[1], p90: hi[1] }
  }
  return null
}

const HIDDEN = new Set(['year', 'monte_carlo_draws', 'damage_reduction_pct'])

type Curves = Record<Scenario, Band[]>

function Trajectory({ curves, scenario, year, unit }: { curves: Curves; scenario: Scenario; year: number; unit: string }) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const H = 220
  const M = { l: 52, r: 104, t: 12, b: 26 }
  const top = Math.max(...Object.values(curves).flatMap((c) => c.map((b) => b.p90)))
  const sx = (y: number) => M.l + ((y - 2026) / 24) * (width - M.l - M.r)
  const sy = (v: number) => M.t + (1 - v / (top * 1.05)) * (H - M.t - M.b)
  const line = (c: Band[], f: (b: Band) => number) => c.map((b, i) => `${i ? 'L' : 'M'}${sx(YEARS[i]).toFixed(1)},${sy(f(b)).toFixed(1)}`).join('')
  const act = curves[scenario]
  const area = line(act, (b) => b.p90) + [...act].map((b, i) => `L${sx(YEARS[i]).toFixed(1)},${sy(b.p10).toFixed(1)}`).reverse().join('') + 'Z'

  // Direct labels at the line ends, nudged apart so they never overlap.
  const ends = SCENARIOS.map((s) => ({ ...s, y: sy(curves[s.id][YEARS.length - 1].median) })).sort((a, b) => a.y - b.y)
  for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 14)

  return (
    <div ref={ref}>
      {width > 0 && (
        <svg width={width} height={H} role="img" aria-label={`Median projection 2026 to 2050 for three scenarios, in ${unit}. Shaded band is the 10th to 90th percentile of the selected scenario.`}>
          {[0, top / 2, top].map((t) => (
            <g key={t}>
              <line className="grid" x1={M.l} x2={width - M.r} y1={sy(t)} y2={sy(t)} />
              <text className="tick" x={M.l - 10} y={sy(t)} textAnchor="end" dominantBaseline="middle">
                {fmt(t)}
              </text>
            </g>
          ))}
          {[2026, 2030, 2040, 2050].map((y) => (
            <text key={y} className="tick" x={sx(y)} y={H - 6} textAnchor="middle">
              {y}
            </text>
          ))}
          <path className="band" d={area} />
          {SCENARIOS.map((s) => (
            <path key={s.id} className={s.id === scenario ? 'series' : 'series off'} d={line(curves[s.id], (b) => b.median)} />
          ))}
          <line className="cursor" x1={sx(year)} x2={sx(year)} y1={M.t} y2={H - M.b} />
          {ends.map((e) => (
            <text key={e.id} className={e.id === scenario ? 'end on' : 'end'} x={width - M.r + 10} y={e.y} dominantBaseline="middle">
              {e.label}
            </text>
          ))}
        </svg>
      )}
    </div>
  )
}

export function Simulation({ id, year, scenario, onChange }: { id: HotspotId; year: number; scenario: Scenario; onChange: (year: number, scenario: Scenario) => void }) {
  const [sim, setSim] = useState<Sim | null>(null)
  const [curves, setCurves] = useState<Curves | null>(null)

  // Selected point. The previous result stays on screen while the next one loads, so the panel never blanks.
  useEffect(() => {
    const ctl = new AbortController()
    const t = setTimeout(() => {
      get<Sim>(`/api/hotspots/${id}/future-simulation?year=${year}&scenario=${scenario}`, ctl.signal).then(setSim, () => {})
    }, 90)
    return () => {
      clearTimeout(t)
      ctl.abort()
    }
  }, [id, year, scenario])

  // Whole trajectories, once per hotspot.
  useEffect(() => {
    const ctl = new AbortController()
    Promise.all(
      SCENARIOS.map((s) => Promise.all(YEARS.map((y) => get<Sim>(`/api/hotspots/${id}/future-simulation?year=${y}&scenario=${s.id}`, ctl.signal).then(band)))),
    ).then(
      (rows) => {
        if (rows.flat().every(Boolean)) setCurves(Object.fromEntries(SCENARIOS.map((s, i) => [s.id, rows[i]])) as Curves)
      },
      () => {},
    )
    return () => ctl.abort()
  }, [id])

  if (!sim) return null
  const b = band(sim)
  const head = b ? humanize(b.key) : null
  const stats = Object.entries(sim).filter(([k, v]) => typeof v === 'number' && !HIDDEN.has(k) && !k.startsWith('median')) as [string, number][]

  return (
    <div className="sim">
      <div className="controls">
        <div className="seg" role="radiogroup" aria-label="Scenario">
          {SCENARIOS.map((s) => (
            <button key={s.id} role="radio" aria-checked={s.id === scenario} onClick={() => onChange(year, s.id)}>
              {s.label}
            </button>
          ))}
        </div>
        <label className="year">
          <span>Year</span>
          <input type="range" min={2026} max={2050} value={year} onChange={(e) => onChange(+e.target.value, scenario)} />
          <output>{year}</output>
        </label>
      </div>

      {b && head && (
        <p className="headline">
          <b>
            {fmt(b.median)} <small>{head.unit}</small>
          </b>
          <span>
            {sim.metric_projected}. Median of {sim.monte_carlo_draws ?? 500} draws; 10th–90th percentile {fmt(b.p10)}–{fmt(b.p90)} {head.unit}.
          </span>
        </p>
      )}

      {curves && head && <Trajectory curves={curves} scenario={scenario} year={year} unit={head.unit} />}

      <dl className="metrics">
        <div>
          <dt>Risk level</dt>
          <dd className="word">{sim.risk_level.toLowerCase()}</dd>
        </div>
        {stats.map(([k, v]) => {
          const h = humanize(k)
          return (
            <div key={k}>
              <dt>{h.label}</dt>
              <dd>
                {fmt(v)} <small>{h.unit}</small>
              </dd>
            </div>
          )
        })}
      </dl>

      {sim.damage_reduction_pct > 0 && (
        <p className="policy">
          <b>−{fmt(sim.damage_reduction_pct)}%</b> {sim.policy_summary}
        </p>
      )}
    </div>
  )
}
