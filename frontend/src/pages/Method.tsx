import type { ReactNode } from 'react'
import { HOTSPOT_IDS, useApi, type Health, type HotspotDetail, type HotspotId } from '../api'
import { useStage } from '../stage-context'
import { ApiDown, Reveal } from '../components/ui'

/** Ray diagrams: the pulse arrives from the upper left; what comes back decides how bright a pixel is. */
const MECHANISMS: { name: string; reading: string; text: string; art: ReactNode }[] = [
  {
    name: 'Specular reflection',
    reading: 'below −20 dB',
    text: 'Calm water is a mirror. The pulse leaves at the opposite angle and almost nothing returns, so open floodwater reads dark.',
    art: (
      <>
        <path className="ground" d="M10 82H150" />
        <path className="ray in" d="M28 18L80 82" />
        <path className="ray out" d="M80 82L132 18" />
      </>
    ),
  },
  {
    name: 'Double bounce',
    reading: 'above −5 dB in HH',
    text: 'Water under standing stems or beside walls makes a corner. The pulse bounces twice and comes straight back: flooded forest and built-up blocks read very bright.',
    art: (
      <>
        <path className="ground" d="M10 82H150M104 82V24" />
        <path className="ray in" d="M30 20L72 82L104 44" />
        <path className="ray back" d="M104 44L48 14" />
      </>
    ),
  },
  {
    name: 'Volume scattering',
    reading: 'strong HV',
    text: 'Leaves and branches scatter the pulse many times and rotate its polarisation. A high cross-polarised return means canopy.',
    art: (
      <>
        <path className="ground" d="M10 82H150" />
        <ellipse className="canopy" cx="92" cy="46" rx="42" ry="26" />
        <path className="ray in" d="M22 14L74 40L96 30L86 54L108 50" />
        <path className="ray back" d="M74 40L40 10M96 30L78 8" />
      </>
    ),
  },
  {
    name: 'Dielectric constant',
    reading: '+3 to 6 dB when wet',
    text: 'Water has a dielectric constant near 80; dry soil sits between 3 and 5. Wet ground reflects more of the pulse than the same ground dry.',
    art: (
      <>
        <path className="ground" d="M10 82H150" />
        <path className="wet" d="M80 82H150V96H80Z" />
        <path className="ray in" d="M20 16L50 82M92 16L122 82" />
        <path className="ray back thin" d="M50 82L30 38" />
        <path className="ray back" d="M122 82L102 38" />
      </>
    ),
  },
]

const STEPS = [
  { title: 'Filter speckle', text: 'A Lee filter is applied to the raw linear backscatter γ⁰. It must run before any log conversion, or the noise statistics are wrong.' },
  { title: 'Convert to decibels', text: 'γ⁰(dB) = 10 · log₁₀(γ⁰). Backscatter spans four orders of magnitude; the log scale makes it comparable.' },
  { title: 'Clip the range', text: 'HH is kept between −25 and 0 dB, HV between −30 and −5 dB. Provisional and validated products are never mixed in one time series.' },
  { title: 'Precompute, then serve', text: 'The heavy HDF5 work runs once in Python. The browser only ever receives small JSON, so every page loads instantly.' },
]

function Paths({ id }: { id: HotspotId }) {
  const { data } = useApi<HotspotDetail>(`/api/hotspots/${id}?include_live_sar=false`)
  if (!data) return null
  return (
    <div style={{ '--hue': `var(--h-${id})` } as React.CSSProperties}>
      <dt>
        <i className="swatch" />
        {data.name}
      </dt>
      <dd>
        {Object.values(data.scientific_context.hdf5_datasets).map((p) => (
          <code key={p}>{p}</code>
        ))}
      </dd>
    </div>
  )
}

export default function Method() {
  const { data, error } = useApi<Health>('/api/health')
  useStage({ cloud: 0.9, radar: 1 })

  return (
    <main className="page">
      <svg width="0" height="0" aria-hidden="true" style={{ position: 'absolute' }}>
        <marker id="arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" orient="auto">
          <path d="M0 0L6 3L0 6z" fill="context-stroke" />
        </marker>
      </svg>
      <div className="col">
        <Reveal as="section" className="page-head">
          <p className="eyebrow">Method</p>
          <h1>How the radar reads the ground.</h1>
          <p className="lede">A SAR image is a map of how much of each pulse came back. Four mechanisms explain almost every bright and dark pixel.</p>
        </Reveal>

        <Reveal as="section" className="block mechanisms">
          {MECHANISMS.map((m) => (
            <article key={m.name}>
              <svg viewBox="0 0 160 100" aria-hidden="true">
                {m.art}
              </svg>
              <h2>{m.name}</h2>
              <p className="reading">{m.reading}</p>
              <p>{m.text}</p>
            </article>
          ))}
        </Reveal>

        <Reveal as="section" className="block">
          <p className="eyebrow">From echo to evidence</p>
          <ol className="steps-list">
            {STEPS.map((s) => (
              <li key={s.title}>
                <h2>{s.title}</h2>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
        </Reveal>

        <Reveal as="section" className="block">
          <p className="eyebrow">NISAR datasets read per site</p>
          <dl className="paths">
            {HOTSPOT_IDS.map((id) => (
              <Paths key={id} id={id} />
            ))}
          </dl>
        </Reveal>

        {error && <ApiDown />}
        {data && (
          <Reveal as="section" className="block">
            <p className="eyebrow">Data sources · API v{data.version}</p>
            <ul className="sources">
              {data.supported_missions.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </Reveal>
        )}
      </div>
    </main>
  )
}
