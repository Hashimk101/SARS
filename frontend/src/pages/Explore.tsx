import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useApi, type HotspotId, type HotspotSummary } from '../api'
import { useStage } from '../stage-context'
import { ApiDown, Reveal } from '../components/ui'

export default function Explore() {
  const { data, error } = useApi<HotspotSummary[]>('/api/hotspots')
  const [hover, setHover] = useState<HotspotId | null>(null)
  useStage({ focus: 1, highlight: hover })

  return (
    <main className="page">
      <div className="col">
        <Reveal as="section" className="page-head">
          <p className="eyebrow">Hotspots</p>
          <h1>Four sites, four kinds of change.</h1>
        </Reveal>
        {error && <ApiDown />}
        {data && (
          <Reveal as="ul" className="sites">
            {data.map((h, i) => (
              <li key={h.id} style={{ '--hue': `var(--h-${h.id})` } as React.CSSProperties}>
                <Link to={`/hotspot/${h.id}`} onPointerEnter={() => setHover(h.id)} onPointerLeave={() => setHover(null)} onFocus={() => setHover(h.id)} onBlur={() => setHover(null)}>
                  <span className="n">0{i + 1}</span>
                  <div>
                    <h2>{h.name}</h2>
                    <p>{h.badge}</p>
                    <p className="meta">
                      <i className="swatch" />
                      {h.location} · {h.lat.toFixed(2)}°N {h.lon.toFixed(2)}°E · {h.severity.toLowerCase()} severity
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </Reveal>
        )}
      </div>
    </main>
  )
}
