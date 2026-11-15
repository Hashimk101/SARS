import { createContext, useCallback, useContext, useEffect, useRef, type ReactNode, type RefObject } from 'react'
import { Link } from 'react-router-dom'
import { COORDS, HOTSPOT_IDS } from './api'
import { IDLE, Stage, type StageState } from './three/stage'

const Ctx = createContext<RefObject<Stage | null>>({ current: null })

/**
 * One WebGL scene lives behind every page. Pages never own a canvas — they describe the state they want and the
 * scene eases into it, so moving between pages is a continuous camera move rather than a reload.
 */
export function StageProvider({ children }: { children: ReactNode }) {
  const stage = useRef<Stage | null>(null)
  const labels = useRef<(HTMLAnchorElement | null)[]>([])

  // Created in a ref callback (layout phase) so the scene exists before any page's effects ask for a state.
  const mount = useCallback((canvas: HTMLCanvasElement | null) => {
    if (!canvas) return
    const s = new Stage(canvas, {
      onLabels: (pts) =>
        pts.forEach((p, i) => {
          const el = labels.current[i]
          if (!el) return
          el.style.transform = `translate(${p.x}px, ${p.y}px)`
          el.style.opacity = String(p.alpha)
          el.style.visibility = p.alpha > 0.05 ? 'visible' : 'hidden'
        }),
    })
    stage.current = s
    return () => {
      s.dispose()
      stage.current = null
    }
  }, [])

  return (
    <Ctx.Provider value={stage}>
      <canvas ref={mount} className="stage" aria-hidden="true" />
      <div className="stage-labels">
        {HOTSPOT_IDS.map((id, i) => (
          <Link
            key={id}
            to={`/hotspot/${id}`}
            className="stage-label"
            style={{ '--hue': `var(--h-${id})` } as React.CSSProperties}
            ref={(el) => {
              labels.current[i] = el
            }}
          >
            {COORDS[id].short}
          </Link>
        ))}
      </div>
      {children}
    </Ctx.Provider>
  )
}

export const useStageRef = () => useContext(Ctx)

/** Declaratively point the shared scene at a state for as long as the calling page is mounted. */
export function useStage(state: Partial<StageState>) {
  const ref = useStageRef()
  const key = JSON.stringify(state)
  useEffect(() => {
    if (ref.current) ref.current.target = { ...IDLE, ...(JSON.parse(key) as Partial<StageState>) }
  }, [ref, key])
}
