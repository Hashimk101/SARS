import { useEffect, useRef, useState } from 'react'
import type { HotspotDetail } from '../api'

const SECONDS = 7

/**
 * Plays the hotspot's signal as sound: the API's tension curve drives pitch and loudness of one oscillator,
 * with a slow tremolo at the given modulation rate.
 */
export function Sonify({ params }: { params: HotspotDetail['sonification'] }) {
  const [playing, setPlaying] = useState(false)
  const ctxRef = useRef<AudioContext | null>(null)
  const stop = () => {
    ctxRef.current?.close()
    ctxRef.current = null
    setPlaying(false)
  }
  useEffect(() => stop, [])

  const play = () => {
    if (playing) return stop()
    const ctx = new AudioContext()
    ctxRef.current = ctx
    const t0 = ctx.currentTime + 0.05
    const osc = new OscillatorNode(ctx, { type: params.waveform, frequency: params.base_frequency_hz })
    const filter = new BiquadFilterNode(ctx, { type: 'lowpass', frequency: 1400 })
    const amp = new GainNode(ctx, { gain: 0 })
    const tremolo = new GainNode(ctx, { gain: 1 })
    const lfo = new OscillatorNode(ctx, { frequency: params.mod_frequency_hz })
    const depth = new GainNode(ctx, { gain: 0.35 })
    lfo.connect(depth).connect(tremolo.gain)
    osc.connect(filter).connect(tremolo).connect(amp).connect(ctx.destination)

    const curve = params.tension_curve
    curve.forEach((v, i) => {
      const t = t0 + (i / (curve.length - 1)) * (SECONDS - 1) + 0.4
      amp.gain.linearRampToValueAtTime(0.03 + v * 0.14, t)
      osc.frequency.linearRampToValueAtTime(params.base_frequency_hz * (1 + v * 0.5), t)
    })
    amp.gain.linearRampToValueAtTime(0, t0 + SECONDS)
    osc.start(t0)
    lfo.start(t0)
    osc.stop(t0 + SECONDS)
    osc.onended = stop
    setPlaying(true)
  }

  const c = params.tension_curve
  const d = c.map((v, i) => `${i ? 'L' : 'M'}${(i / (c.length - 1)) * 120},${26 - v * 22}`).join('')

  return (
    <div className="sonify">
      <button onClick={play} aria-pressed={playing}>
        <svg width="10" height="12" viewBox="0 0 10 12" aria-hidden="true">
          {playing ? <path d="M0 0h3.5v12H0zM6.5 0H10v12H6.5z" /> : <path d="M0 0l10 6-10 6z" />}
        </svg>
        {playing ? 'Stop' : 'Listen'}
      </button>
      <svg className={playing ? 'curve on' : 'curve'} width="120" height="28" viewBox="0 0 120 28" aria-hidden="true">
        <path d={d} />
        <line y1="0" y2="28" style={{ animationDuration: `${SECONDS}s` }} />
      </svg>
      <span>
        {params.sound_theme}. {params.base_frequency_hz} Hz {params.waveform}
      </span>
    </div>
  )
}
