import { useEffect, useRef, useState, type ReactNode } from 'react'
import { animate, stagger } from 'animejs'
import type { Metric } from '../api'

const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches

/** Fades and lifts its direct children into place the first time it scrolls into view. */
export function Reveal({ children, className = '', as: Tag = 'div' }: { children: ReactNode; className?: string; as?: 'div' | 'section' | 'ul' }) {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const kids = [...el.children] as HTMLElement[]
    if (still()) return void el.classList.add('in')
    const io = new IntersectionObserver(
      ([e]) => {
        if (!e.isIntersecting) return
        io.disconnect()
        animate(kids, { opacity: [0, 1], y: [22, 0], duration: 1000, delay: stagger(70), ease: 'outExpo', onComplete: () => el.classList.add('in') })
      },
      { threshold: 0.12 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return <Tag ref={ref as any} className={`reveal ${className}`}>{children}</Tag>
}

export function Metrics({ items }: { items: Metric[] }) {
  return (
    <dl className="metrics">
      {items.map((m) => (
        <div key={m.label}>
          <dt>{m.label}</dt>
          <dd>
            {m.value} <small>{m.unit}</small>
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function ApiDown() {
  return (
    <p className="notice" role="status">
      Can't reach the data API. Start it from the repo root: <code>python -m uvicorn api.index:app --port 8000</code>
    </p>
  )
}

/** Pixel width of an element, so SVG charts can lay out at true size instead of scaling their text. */
export function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [w, setW] = useState(0)
  useEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setW(Math.round(e.contentRect.width)))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])
  return [ref, w] as const
}

const UNITS: [string, string][] = [
  ['_billion_usd', 'B USD'],
  ['_cm_day', 'cm/day'],
  ['_per_km2', '/km²'],
  ['_m3m3', 'm³/m³'],
  ['_m3s', 'm³/s'],
  ['_km2', 'km²'],
  ['_hectares', 'ha'],
  ['_pct', '%'],
  ['_mm', 'mm'],
  ['_cm', 'cm'],
  ['_km', 'km'],
  ['_deg', '°'],
  ['_m', 'm'],
  ['_c', '°C'],
]
const ACRONYMS = /\b(gpm|glof|twi|pdd|hh|hv|sar|insar)\b/gi

/** `ten_year_flood_probability_pct` -> { label: "Ten year flood probability", unit: "%" } */
export function humanize(key: string) {
  let unit = ''
  for (const [suffix, u] of UNITS)
    if (key.endsWith(suffix)) {
      key = key.slice(0, -suffix.length)
      unit = u
      break
    }
  const words = key.replace(/_/g, ' ').replace(ACRONYMS, (m) => m.toUpperCase())
  return { label: words.charAt(0).toUpperCase() + words.slice(1), unit }
}

export function fmt(n: number) {
  if (Math.abs(n) >= 1e6) return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n)
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: Math.abs(n) < 10 ? 2 : 1 }).format(n)
}
