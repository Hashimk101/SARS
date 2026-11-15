import { useEffect, useRef, useState } from 'react'
import { animate, stagger, svg } from 'animejs'
import type { Drivers, Timeline } from '../api'
import { fmt, humanize, useWidth } from './ui'

const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches

/** Three round-ish ticks spanning the data. */
function ticks(lo: number, hi: number) {
  if (lo === hi) return [lo]
  return [lo, (lo + hi) / 2, hi]
}

interface Pt {
  x: number
  v: number
}

function Line({
  pts,
  width,
  height = 150,
  label,
  unit,
  active,
  onActive,
  xLabels,
}: {
  pts: Pt[]
  width: number
  height?: number
  label: string
  unit: string
  active: number
  onActive: (i: number) => void
  xLabels?: { x: number; text: string }[]
}) {
  const path = useRef<SVGPathElement>(null)
  const M = { l: 52, r: 12, t: 14, b: xLabels ? 26 : 10 }
  const vs = pts.map((p) => p.v)
  const lo = Math.min(...vs)
  const hi = Math.max(...vs)
  const pad = (hi - lo || 1) * 0.12
  const sx = (x: number) => M.l + x * (width - M.l - M.r)
  const sy = (v: number) => M.t + (1 - (v - (lo - pad)) / (hi - lo + 2 * pad)) * (height - M.t - M.b)
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x).toFixed(1)},${sy(p.v).toFixed(1)}`).join('')

  useEffect(() => {
    if (!path.current || still() || !width) return
    const a = animate(svg.createDrawable(path.current), { draw: ['0 0', '0 1'], duration: 1400, ease: 'inOutQuart' })
    return () => {
      a.revert()
    }
    // Draw once per dataset, not on every resize.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.length, width > 0])

  if (!width) return null
  return (
    <figure className="chart">
      <figcaption>
        {label} <span>{unit}</span>
      </figcaption>
      <svg
        width={width}
        height={height}
        role="img"
        aria-label={`${label}: ${pts.length} observations from ${fmt(vs[0])} to ${fmt(vs[vs.length - 1])} ${unit}`}
        onPointerMove={(e) => {
          const x = e.nativeEvent.offsetX
          let best = 0
          pts.forEach((p, i) => {
            if (Math.abs(sx(p.x) - x) < Math.abs(sx(pts[best].x) - x)) best = i
          })
          onActive(best)
        }}
      >
        {ticks(lo, hi).map((t) => (
          <g key={t}>
            <line className="grid" x1={M.l} x2={width - M.r} y1={sy(t)} y2={sy(t)} />
            <text className="tick" x={M.l - 10} y={sy(t)} textAnchor="end" dominantBaseline="middle">
              {fmt(t)}
            </text>
          </g>
        ))}
        <line className="cursor" x1={sx(pts[active].x)} x2={sx(pts[active].x)} y1={M.t} y2={height - M.b} />
        <path ref={path} className="series" d={d} />
        {pts.map((p, i) => (
          <circle key={i} className={i === active ? 'pt on' : 'pt'} cx={sx(p.x)} cy={sy(p.v)} r={i === active ? 4.5 : 2.5} />
        ))}
        {xLabels?.map((l) => (
          <text key={l.text} className="tick" x={sx(l.x)} y={height - 6} textAnchor="middle">
            {l.text}
          </text>
        ))}
      </svg>
    </figure>
  )
}

/** Two stacked small multiples on a shared time axis, with one readout for the selected observation. */
export function TimelineChart({ data }: { data: Timeline }) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const s = data.series
  const [active, setActive] = useState(s.length - 1)
  const i = Math.min(active, s.length - 1)
  const t = s.map((p) => +new Date(p.date))
  const t0 = t[0]
  const span = t[t.length - 1] - t0 || 1
  const xs = t.map((v) => (v - t0) / span)
  const hasSecond = s.every((p) => typeof p.secondary_val === 'number')

  const y0 = new Date(t0).getUTCFullYear()
  const y1 = new Date(t[t.length - 1]).getUTCFullYear()
  const years = [] as { x: number; text: string }[]
  for (let y = y0; y <= y1 + 1; y++) {
    const x = (Date.UTC(y, 0, 1) - t0) / span
    if (x >= 0 && x <= 1) years.push({ x, text: String(y) })
  }

  const p = s[i]
  const extras = Object.entries(p).filter(([k, v]) => typeof v === 'number' && !['primary_val', 'secondary_val'].includes(k)) as [string, number][]

  return (
    <div ref={ref} className="timeline">
      <Line pts={s.map((q, k) => ({ x: xs[k], v: q.primary_val }))} width={width} label={data.metric_primary.replace(/\s*\(.*\)$/, '')} unit={data.unit_primary} active={i} onActive={setActive} xLabels={hasSecond ? undefined : years} />
      {hasSecond && (
        <Line pts={s.map((q, k) => ({ x: xs[k], v: q.secondary_val as number }))} width={width} height={130} label={data.metric_secondary.replace(/\s*\(.*\)$/, '')} unit={data.unit_secondary} active={i} onActive={setActive} xLabels={years} />
      )}
      <div className="readout" aria-live="polite">
        <div className="steps" role="group" aria-label="Observation">
          {s.map((q, k) => (
            <button key={q.date} aria-label={`${q.date}: ${q.epoch}`} aria-pressed={k === i} onClick={() => setActive(k)} onFocus={() => setActive(k)} />
          ))}
        </div>
        <p>
          <time>{p.date}</time>
          <strong>{p.epoch}</strong>
        </p>
        <p className="note">{p.note}</p>
        <dl>
          {extras.map(([k, v]) => {
            const h = humanize(k)
            return (
              <div key={k}>
                <dt>{h.label}</dt>
                <dd>
                  {fmt(v)} {h.unit}
                </dd>
              </div>
            )
          })}
        </dl>
      </div>
    </div>
  )
}

export function DriverBars({ data }: { data: Drivers }) {
  const ref = useRef<HTMLOListElement>(null)
  const rows = Object.entries(data.feature_attribution_importance).sort((a, b) => b[1].importance_score - a[1].importance_score)
  const max = Math.max(...rows.map((r) => r[1].importance_score), 0.0001)

  useEffect(() => {
    const el = ref.current
    if (!el || still()) return
    const bars = el.querySelectorAll('.bar i')
    const io = new IntersectionObserver(
      ([e]) => {
        if (!e.isIntersecting) return
        io.disconnect()
        animate(bars, { scaleX: [0, 1], duration: 1100, delay: stagger(90), ease: 'outExpo' })
      },
      { threshold: 0.3 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [rows.length])

  return (
    <div className="drivers">
      <ol ref={ref}>
        {rows.map(([k, v]) => (
          <li key={k}>
            <div className="head">
              <span>{humanize(k).label}</span>
              <b>{v.importance_score.toFixed(3)}</b>
            </div>
            <div className="bar">
              <i style={{ width: `${Math.max(0, v.importance_score / max) * 100}%` }} />
            </div>
            <p>{v.description}</p>
          </li>
        ))}
      </ol>
      <p className="fine">
        Permutation importance. {data.model_type}
        {data.training_samples ? `, ${fmt(data.training_samples)} samples` : ''}. Spatial block cross-validation R² = {data.spatial_block_cv_r2}.
      </p>
    </div>
  )
}
