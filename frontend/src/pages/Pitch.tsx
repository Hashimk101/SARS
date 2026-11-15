import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { animate, stagger } from 'animejs'
import { COORDS, HOTSPOT_IDS, useApi, type HotspotDetail, type HotspotId } from '../api'
import { useStageRef } from '../stage-context'
import { IDLE, type StageState } from '../three/stage'
import { ApiDown, Metrics, Reveal } from '../components/ui'

/** What the terrain is doing in each hotspot section — written to match the physics the scene animates. */
const STORY: Record<HotspotId, { title: string; body: string }> = {
  indus: {
    title: 'Water rises. The radar echo falls.',
    body: 'Open water reflects the pulse away from the sensor, so flooded land drops below −20 dB and reads dark against dry ground. The bright line is the shore.',
  },
  quetta: {
    title: 'A city sinking into its own aquifer.',
    body: 'Comparing the phase of two passes resolves centimetres of ground motion. Each colour band is one fringe of the deepening bowl.',
  },
  islamabad: {
    title: 'The forest edge moves uphill.',
    body: 'Tree canopy scatters the pulse in every direction and lights up the HV channel. Cleared slopes lose that signal; the street grid replaces it.',
  },
  siachen: {
    title: 'Ice that is speeding up.',
    body: 'The same phase comparison gives surface velocity along the glacier, fastest at the centreline and rising with every warm season.',
  },
}

const sstep = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}

/** Scroll position (in section units: 0 = hero centred, 1 = next section centred, …) -> scene state. */
function stateAt(s: number): StageState {
  const i = Math.min(7, Math.max(4, Math.round(s)))
  return {
    ...IDLE,
    cloud: sstep(0.35, 0.95, s) * (1 - sstep(2.45, 2.95, s)),
    radar: sstep(1.45, 1.95, s) * (1 - sstep(3.0, 3.4, s)),
    focus: sstep(2.4, 3.0, s),
    globe: 1 - sstep(3.45, 3.85, s) + sstep(7.55, 7.95, s),
    terrain: sstep(3.6, 3.95, s) * (1 - sstep(7.45, 7.8, s)),
    mode: HOTSPOT_IDS[i - 4],
    progress: sstep(i - 0.4, i + 0.3, s),
  }
}

function HotspotSection({ id, n }: { id: HotspotId; n: number }) {
  const { data, error } = useApi<HotspotDetail>(`/api/hotspots/${id}?include_live_sar=false`)
  return (
    <section className="beat" data-stage style={{ '--hue': `var(--h-${id})` } as React.CSSProperties}>
      <Reveal className="col">
        <p className="eyebrow">
          <i className="swatch" />0{n} · {data?.name ?? COORDS[id].short}
        </p>
        <h2>{STORY[id].title}</h2>
        <p className="lede">{STORY[id].body}</p>
        {data && <Metrics items={data.chapters[0].metrics} />}
        {error && <ApiDown />}
        <Link className="link" to={`/hotspot/${id}`}>
          Open the dossier
        </Link>
      </Reveal>
    </section>
  )
}

export default function Pitch() {
  const root = useRef<HTMLElement>(null)
  const stage = useStageRef()

  useEffect(() => {
    const sections = [...root.current!.querySelectorAll<HTMLElement>('[data-stage]')]
    const onScroll = () => {
      const mid = scrollY + innerHeight / 2
      let s = -0.5
      for (const el of sections) s += Math.min(1, Math.max(0, (mid - el.offsetTop) / el.offsetHeight))
      if (stage.current) stage.current.target = stateAt(s)
    }
    onScroll()
    addEventListener('scroll', onScroll, { passive: true })
    addEventListener('resize', onScroll)
    return () => {
      removeEventListener('scroll', onScroll)
      removeEventListener('resize', onScroll)
    }
  }, [stage])

  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    animate('.hero h1 span > span', { y: ['105%', '0%'], duration: 1300, delay: stagger(90, { start: 150 }), ease: 'outExpo' })
    animate('.hero .after', { opacity: [0, 1], y: [14, 0], duration: 1000, delay: stagger(110, { start: 750 }), ease: 'outExpo' })
  }, [])

  return (
    <main ref={root} className="pitch">
      <section className="beat hero" data-stage>
        <div className="col">
          <p className="eyebrow after">NISAR L-band radar · Pakistan</p>
          <h1 aria-label="Dancing with the SARs">
            {['Dancing', 'with the', 'SARs'].map((w, i) => (
              <span key={w} aria-hidden="true">
                <span className={i === 0 ? 'it' : ''}>{w}</span>
              </span>
            ))}
          </h1>
          <p className="lede after">A radar satellite that watches the ground move, through cloud, rain and night. We use it to track four hazards across Pakistan.</p>
          <p className="actions after">
            <Link className="btn" to="/explore">
              See the four hotspots
            </Link>
            <Link className="link" to="/method">
              How the radar reads the ground
            </Link>
          </p>
        </div>
      </section>

      <section className="beat" data-stage>
        <Reveal className="col">
          <h2>When the monsoon breaks, optical satellites go blind.</h2>
          <p className="lede">Floods arrive under the cloud that causes them. Landsat and Sentinel-2 record the cloud tops, not the water underneath.</p>
        </Reveal>
      </section>

      <section className="beat" data-stage>
        <Reveal className="col">
          <h2>Radar doesn't wait for clear sky.</h2>
          <p className="lede">NISAR sends its own 24 cm pulse and times the echo. Cloud, rain and darkness are transparent to it. Standing water, sinking ground and moving ice are not.</p>
        </Reveal>
      </section>

      <section className="beat" data-stage>
        <Reveal className="col">
          <h2>Four places where Pakistan's surface is changing.</h2>
          <ul className="index">
            {HOTSPOT_IDS.map((id) => (
              <li key={id} style={{ '--hue': `var(--h-${id})` } as React.CSSProperties}>
                <Link to={`/hotspot/${id}`}>
                  <i className="swatch" />
                  <span>{COORDS[id].short}</span>
                  <em>{{ indus: 'Flood', quetta: 'Subsidence', islamabad: 'Canopy loss', siachen: 'Glacier motion' }[id]}</em>
                </Link>
              </li>
            ))}
          </ul>
        </Reveal>
      </section>

      {HOTSPOT_IDS.map((id, i) => (
        <HotspotSection key={id} id={id} n={i + 1} />
      ))}

      <section className="beat" data-stage>
        <Reveal className="col">
          <h2>Pick a place. Read the ground.</h2>
          <p className="lede">Each dossier carries the radar record, what is driving the change, and where it leads by 2050 under three policies.</p>
          <p className="actions">
            <Link className="btn" to="/explore">
              Open the hotspots
            </Link>
          </p>
        </Reveal>
      </section>
    </main>
  )
}
