import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { figureSrc, HOTSPOT_IDS, useApi, type Drivers, type Figure, type HotspotDetail, type HotspotId, type Scenario, type Timeline } from '../api'
import { useStage } from '../stage-context'
import { DriverBars, TimelineChart } from '../components/charts'
import { SCENARIOS, Simulation } from '../components/Simulation'
import { Sonify } from '../components/Sonify'
import { ApiDown, Metrics, Reveal } from '../components/ui'

const SHOWS: Record<HotspotId, string> = {
  indus: 'flood extent',
  quetta: 'subsidence bowl',
  islamabad: 'canopy clearing',
  siachen: 'ice velocity',
}
const SEVERITY: Record<Scenario, number> = { controlled: 0.5, current_trend: 0.8, accelerated: 1 }

function Figures({ id }: { id: HotspotId }) {
  const { data } = useApi<{ figures: Figure[] }>(`/api/hotspots/${id}/figures`)
  const [broken, setBroken] = useState<string[]>([])
  const figs = data?.figures.filter((f) => !broken.includes(f.id)) ?? []
  if (!figs.length) return null
  return (
    <Reveal as="section" className="block">
      <p className="eyebrow">Evidence</p>
      <div className="figures">
        {figs.map((f) => (
          <figure key={f.id}>
            <a href={figureSrc(f.api_url)} target="_blank" rel="noreferrer">
              <img src={figureSrc(f.api_url)} alt={f.title} loading="lazy" onError={() => setBroken((b) => [...b, f.id])} />
            </a>
            <figcaption>
              <strong>{f.title}</strong>
              {f.description}
            </figcaption>
          </figure>
        ))}
      </div>
    </Reveal>
  )
}

function Granules({ id }: { id: HotspotId }) {
  const { data } = useApi<HotspotDetail>(`/api/hotspots/${id}?include_live_sar=true`)
  const rows = data?.nasa_asf_granules?.slice(0, 5) ?? []
  if (!rows.length) return null
  return (
    <Reveal as="section" className="block">
      <p className="eyebrow">Latest radar passes · NASA ASF DAAC</p>
      <table className="table">
        <thead>
          <tr>
            <th>Scene</th>
            <th>Platform</th>
            <th>Pol.</th>
            <th>Acquired</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((g) => (
            <tr key={g.scene_name}>
              <td>
                <a href={g.download_url} target="_blank" rel="noreferrer" title={g.scene_name}>
                  {g.scene_name}
                </a>
              </td>
              <td>{g.platform}</td>
              <td>{g.polarization}</td>
              <td>{g.acquisition_time?.slice(0, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Reveal>
  )
}

function Dossier({ id }: { id: HotspotId }) {
  const detail = useApi<HotspotDetail>(`/api/hotspots/${id}?include_live_sar=false`)
  const timeline = useApi<Timeline>(`/api/hotspots/${id}/timeline`)
  const drivers = useApi<Drivers>(`/api/hotspots/${id}/drivers`)
  const [year, setYear] = useState(2030)
  const [scenario, setScenario] = useState<Scenario>('current_trend')

  // The terrain on the right is driven by the simulation controls further down the page.
  useStage({ globe: 0, terrain: 1, mode: id, progress: 0.1 + 0.9 * ((year - 2026) / 24) ** 0.8 * SEVERITY[scenario] })

  const d = detail.data
  const n = HOTSPOT_IDS.indexOf(id)
  const next = HOTSPOT_IDS[(n + 1) % HOTSPOT_IDS.length]
  const env = d?.live_environmental

  return (
    <main className="page dossier" style={{ '--hue': `var(--h-${id})` } as React.CSSProperties}>
      <div className="col">
        {detail.error && <ApiDown />}
        {d && (
          <Reveal as="section" className="page-head">
            <p className="eyebrow">
              <Link to="/explore">Hotspots</Link> / 0{n + 1}
            </p>
            <h1>{d.name}</h1>
            <p className="meta">
              <i className="swatch" />
              {d.location} · {d.severity.toLowerCase()} severity
            </p>
            <p className="lede">{d.short_desc}</p>
            <Sonify params={d.sonification} />
          </Reveal>
        )}

        {d?.chapters.map((ch) => (
          <Reveal as="section" className="block chapter" key={ch.step}>
            <p className="eyebrow">Chapter {ch.step} of {d.chapters.length}</p>
            <h2>{ch.title.replace(/^Historical Timeline:\s*/, '')}</h2>
            <p className="body">{ch.body}</p>
            <Metrics items={ch.metrics} />

            {ch.step === 1 && timeline.data && (
              <div className="panel">
                <p className="eyebrow">The radar record</p>
                <TimelineChart data={timeline.data} />
              </div>
            )}
            {ch.step === 3 && drivers.data && (
              <div className="panel">
                <p className="eyebrow">What the model says drives it</p>
                <DriverBars data={drivers.data} />
                <p className="body">{drivers.data.scientific_synthesis}</p>
              </div>
            )}
            {ch.step === 4 && (
              <div className="panel">
                <p className="eyebrow">Projection, 2026–2050</p>
                <Simulation
                  id={id}
                  year={year}
                  scenario={scenario}
                  onChange={(y, s) => {
                    setYear(y)
                    setScenario(s)
                  }}
                />
              </div>
            )}
          </Reveal>
        ))}

        <Figures id={id} />

        {d && (
          <Reveal as="section" className="block">
            <p className="eyebrow">How this site is measured</p>
            <dl className="spec">
              <div>
                <dt>Mission</dt>
                <dd>{d.scientific_context.satellite_mission}</dd>
              </div>
              <div>
                <dt>Channels</dt>
                <dd>{d.scientific_context.polarization_channels}</dd>
              </div>
              <div>
                <dt>Processing</dt>
                <dd>{d.scientific_context.preprocessing_rule}</dd>
              </div>
              <div>
                <dt>Physics</dt>
                <dd>{d.scientific_context.physical_phenomenon}</dd>
              </div>
              {env && (
                <div>
                  <dt>Ground now</dt>
                  <dd>
                    Soil moisture {env.soil_moisture_topsoil_m3m3} m³/m³ topsoil, {env.soil_moisture_subsurface_m3m3} m³/m³ subsurface. Precipitation {env.current_precipitation_mm} mm. Open-Meteo, {env.timestamp.replace('T', ' ')} UTC.
                  </dd>
                </div>
              )}
            </dl>
          </Reveal>
        )}

        <Granules id={id} />

        <Link className="next" to={`/hotspot/${next}`} style={{ '--hue': `var(--h-${next})` } as React.CSSProperties}>
          <span className="eyebrow">Next site</span>
          <span>
            <i className="swatch" />
            {{ indus: 'Indus River Basin', quetta: 'Quetta Valley', islamabad: 'Margalla Hills', siachen: 'Siachen Glacier' }[next]}
          </span>
        </Link>
      </div>

      <p className="stage-caption">
        Illustrative model, not to scale · {SHOWS[id]} · {year} · {SCENARIOS.find((s) => s.id === scenario)!.label.toLowerCase()}
      </p>
    </main>
  )
}

export default function Hotspot() {
  const { id } = useParams()
  if (!HOTSPOT_IDS.includes(id as HotspotId))
    return (
      <main className="page">
        <div className="col page-head">
          <h1>No such site.</h1>
          <Link className="link" to="/explore">
            Back to the hotspots
          </Link>
        </div>
      </main>
    )
  // Keyed so every piece of per-site state (year, scenario, audio) resets when the site changes.
  return <Dossier key={id} id={id as HotspotId} />
}
