import * as THREE from 'three'
import type { HotspotId } from './api'

/**
 * Single source of truth for colour, defined in OKLCH.
 *
 * Rules the whole UI follows:
 *  - Neutrals are near-black / off-white, tinted (chroma ~0.012), never pure #000 / #fff.
 *  - Chroma is reserved for data: the only saturated colours are the four hotspot hues.
 *  - Hotspot hues share one chroma and sit in a narrow lightness band so none dominates;
 *    lightness is staggered slightly so sky/violet stay separable under red-green CVD.
 *  - Colour never carries meaning alone: every hue is paired with a text label.
 */
export type Oklch = [l: number, c: number, h: number]

export const NEUTRAL = {
  bg: [0.155, 0.012, 255] as Oklch,
  surface: [0.195, 0.014, 255] as Oklch,
  line: [0.3, 0.014, 255] as Oklch,
  faint: [0.62, 0.012, 255] as Oklch,
  muted: [0.74, 0.012, 255] as Oklch,
  ink: [0.94, 0.012, 85] as Oklch,
}

export const HUE: Record<HotspotId, Oklch> = {
  indus: [0.82, 0.13, 235],
  quetta: [0.76, 0.13, 55],
  islamabad: [0.8, 0.13, 165],
  siachen: [0.72, 0.13, 305],
}

export const css = ([l, c, h]: Oklch) => `oklch(${l} ${c} ${h})`

/** OKLCH -> linear sRGB (three.js working colour space). */
export function toThree([l, c, h]: Oklch): THREE.Color {
  const a = c * Math.cos((h * Math.PI) / 180)
  const b = c * Math.sin((h * Math.PI) / 180)
  const l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
  const m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
  const s_ = (l - 0.0894841775 * a - 1.291485548 * b) ** 3
  const clamp = (v: number) => Math.min(1, Math.max(0, v))
  return new THREE.Color().setRGB(
    clamp(4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_),
    clamp(-1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_),
    clamp(-0.0041960863 * l_ - 0.7034186147 * m_ + 1.707614701 * s_),
    THREE.LinearSRGBColorSpace,
  )
}

/** Writes the palette onto :root so CSS and WebGL can never drift apart. */
export function applyTheme() {
  const s = document.documentElement.style
  for (const [k, v] of Object.entries(NEUTRAL)) s.setProperty(`--${k}`, css(v))
  for (const [k, v] of Object.entries(HUE)) s.setProperty(`--h-${k}`, css(v))
}
