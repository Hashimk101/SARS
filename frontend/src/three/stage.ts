import * as THREE from 'three'
import { geoEquirectangular, geoPath } from 'd3-geo'
import { feature } from 'topojson-client'
import { COORDS, HOTSPOT_IDS, type HotspotId } from '../api'
import { HUE, NEUTRAL, toThree } from '../theme'
import * as S from './shaders'

export interface StageState {
  /** 0–1 visibility of the globe rig. */
  globe: number
  /** 0–1 cloud cover (what an optical sensor sees). */
  cloud: number
  /** 0–1 radar on: beam + footprint cutting through cloud. */
  radar: number
  /** 0–1 turn and zoom the globe onto Pakistan. */
  focus: number
  /** 0–1 visibility of the terrain field. */
  terrain: number
  /** Which hotspot's physics the terrain shows. */
  mode: HotspotId
  /** 0–1 how far that process has run. */
  progress: number
  highlight: HotspotId | null
}

export const IDLE: StageState = {
  globe: 1,
  cloud: 0,
  radar: 0,
  focus: 0,
  terrain: 0,
  mode: 'indus',
  progress: 0,
  highlight: null,
}

export interface Label {
  id: HotspotId
  x: number
  y: number
  alpha: number
}

interface Options {
  /** Centre the subject instead of holding it to the right of the text column. */
  centered?: boolean
  onLabels?: (labels: Label[]) => void
}

const DEG = Math.PI / 180
const FOCUS = { lat: 31 * DEG, lon: 71.5 * DEG }
const ORBIT_R = 1.5
const mix = (a: number, b: number, t: number) => a + (b - a) * t
const sstep = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}

function latLon(lat: number, lon: number, r = 1) {
  const la = lat * DEG
  const lo = lon * DEG
  return new THREE.Vector3(r * Math.cos(la) * Math.sin(lo), r * Math.sin(la), r * Math.cos(la) * Math.cos(lo))
}

/** Evenly spaced points on a sphere, kept only where they fall on land (Natural Earth, rasterised once). */
async function landPoints(count: number): Promise<Float32Array> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const topo = (await import('world-atlas/land-50m.json')).default as any
  const land = feature(topo, topo.objects.land)
  const W = 2048
  const H = 1024
  const cv = document.createElement('canvas')
  cv.width = W
  cv.height = H
  const ctx = cv.getContext('2d', { willReadFrequently: true })!
  const proj = geoEquirectangular()
    .scale(W / (2 * Math.PI))
    .translate([W / 2, H / 2])
  ctx.beginPath()
  geoPath(proj, ctx)(land)
  ctx.fill()
  const px = ctx.getImageData(0, 0, W, H).data
  const out: number[] = []
  const golden = Math.PI * (3 - Math.sqrt(5))
  for (let i = 0; i < count; i++) {
    const y = 1 - (2 * (i + 0.5)) / count
    const r = Math.sqrt(1 - y * y)
    const th = i * golden
    const x = Math.sin(th) * r
    const z = Math.cos(th) * r
    const u = Math.floor(((Math.atan2(x, z) + Math.PI) / (2 * Math.PI)) * W) % W
    const v = Math.min(H - 1, Math.floor(((Math.PI / 2 - Math.asin(y)) / Math.PI) * H))
    if (px[(v * W + u) * 4 + 3] > 127) out.push(x, y, z)
  }
  return new Float32Array(out)
}

function discTexture(ring: boolean) {
  const cv = document.createElement('canvas')
  cv.width = cv.height = 128
  const c = cv.getContext('2d')!
  c.strokeStyle = c.fillStyle = '#fff'
  c.beginPath()
  if (ring) {
    c.lineWidth = 5
    c.arc(64, 64, 58, 0, Math.PI * 2)
    c.stroke()
  } else {
    c.arc(64, 64, 44, 0, Math.PI * 2)
    c.fill()
  }
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

export class Stage {
  target: StageState = { ...IDLE }
  private cur: StageState = { ...IDLE }
  private renderer: THREE.WebGLRenderer
  private scene = new THREE.Scene()
  private camera = new THREE.PerspectiveCamera(35, 1, 0.1, 50)
  private rig = new THREE.Group()
  private earth = new THREE.Group()
  private clouds: THREE.Mesh
  private sat = new THREE.Group()
  private field: THREE.Points
  private fieldRig = new THREE.Group()
  private markers = new Map<HotspotId, { dot: THREE.Sprite; ring: THREE.Sprite; pos: THREE.Vector3 }>()
  private u = {
    globe: {
      uAlpha: { value: 1 },
      uCloud: { value: 0 },
      uRadar: { value: 0 },
      uTime: { value: 0 },
      uBeam: { value: new THREE.Vector3(0, 0, 1) },
    },
    cloudBeam: { value: new THREE.Vector3(0, 0, 1) },
    landSize: { value: 6 },
    field: {
      uTime: { value: 0 },
      uProgress: { value: 0 },
      uAlpha: { value: 0 },
      uSize: { value: 8 },
      uMode: { value: 0 },
      uHue: { value: toThree(HUE.indus) },
      uInk: { value: toThree(NEUTRAL.ink) },
    },
  }
  private shownMode: HotspotId = 'indus'
  private modeFade = 1
  private spin = -38 * DEG
  private time = 0
  private last = 0
  private raf = 0
  private wide = true
  private disposables: { dispose(): void }[] = []
  private still = matchMedia('(prefers-reduced-motion: reduce)').matches
  private canvas: HTMLCanvasElement
  private opts: Options

  constructor(canvas: HTMLCanvasElement, opts: Options = {}) {
    this.canvas = canvas
    this.opts = opts
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' })
    this.renderer.setClearColor(0x000000, 0)
    this.camera.position.set(0, 0, 4.6)

    const ink = toThree(NEUTRAL.ink)
    const g = this.u.globe
    const track = <T extends { dispose(): void }>(x: T) => (this.disposables.push(x), x)

    // --- Earth: occluding ocean sphere + dot-matrix land ---
    const ocean = new THREE.Mesh(
      track(new THREE.SphereGeometry(0.994, 96, 64)),
      track(
        new THREE.ShaderMaterial({
          vertexShader: S.OCEAN_VERT,
          fragmentShader: S.OCEAN_FRAG,
          transparent: true,
          uniforms: { uBase: { value: toThree([0.175, 0.016, 255]) }, uRim: { value: toThree([0.42, 0.03, 250]) }, uAlpha: g.uAlpha },
        }),
      ),
    )
    const landGeo = track(new THREE.BufferGeometry())
    landGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(0), 3))
    const land = new THREE.Points(
      landGeo,
      track(
        new THREE.ShaderMaterial({
          vertexShader: S.LAND_VERT,
          fragmentShader: S.LAND_FRAG,
          transparent: true,
          depthWrite: false,
          uniforms: { uSize: this.u.landSize, uCloud: g.uCloud, uRadar: g.uRadar, uAlpha: g.uAlpha, uBeam: g.uBeam, uColor: { value: ink } },
        }),
      ),
    )
    land.frustumCulled = false
    landPoints(90000).then((pts) => {
      landGeo.setAttribute('position', new THREE.BufferAttribute(pts, 3))
    })
    this.earth.rotation.order = 'XYZ'
    this.earth.add(ocean, land)

    // --- Hotspot markers ---
    const dotTex = track(discTexture(false))
    const ringTex = track(discTexture(true))
    for (const id of HOTSPOT_IDS) {
      const color = toThree(HUE[id])
      const pos = latLon(COORDS[id].lat, COORDS[id].lon, 1.012)
      const dot = new THREE.Sprite(track(new THREE.SpriteMaterial({ map: dotTex, color, transparent: true, depthWrite: false })))
      const ring = new THREE.Sprite(track(new THREE.SpriteMaterial({ map: ringTex, color, transparent: true, depthWrite: false })))
      dot.position.copy(pos)
      ring.position.copy(pos)
      this.earth.add(dot, ring)
      this.markers.set(id, { dot, ring, pos })
    }

    // --- Cloud deck ---
    this.clouds = new THREE.Mesh(
      track(new THREE.SphereGeometry(1.035, 96, 64)),
      track(
        new THREE.ShaderMaterial({
          vertexShader: S.CLOUD_VERT,
          fragmentShader: S.CLOUD_FRAG,
          transparent: true,
          depthWrite: false,
          uniforms: {
            uTime: g.uTime,
            uCloud: g.uCloud,
            uRadar: g.uRadar,
            uAlpha: g.uAlpha,
            uBeam: this.u.cloudBeam,
            uColor: { value: toThree([0.8, 0.008, 255]) },
          },
        }),
      ),
    )
    this.clouds.renderOrder = 2

    // --- Satellite: bus, solar array, boom and the 12 m mesh reflector, drawn as an instrument outline ---
    const lineMat = track(new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.9 }))
    const edges = (w: number, h: number, d: number) => new THREE.LineSegments(track(new THREE.EdgesGeometry(new THREE.BoxGeometry(w, h, d))), lineMat)
    const bus = edges(0.034, 0.034, 0.05)
    const panel = edges(0.17, 0.002, 0.036)
    const dish = new THREE.LineLoop(
      track(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 40 }, (_, i) => new THREE.Vector3(Math.cos((i / 40) * 6.2832) * 0.05, Math.sin((i / 40) * 6.2832) * 0.05, 0)))),
      lineMat,
    )
    dish.position.set(0, 0.075, -0.02)
    const boom = new THREE.Line(track(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0.017, 0), new THREE.Vector3(0, 0.075, -0.02)])), lineMat)
    const beamLen = ORBIT_R - 1
    const beamGeo = track(new THREE.ConeGeometry(0.2, beamLen, 48, 1, true))
    beamGeo.translate(0, -beamLen / 2, 0)
    beamGeo.rotateX(-Math.PI / 2)
    const beam = new THREE.Mesh(
      beamGeo,
      track(
        new THREE.ShaderMaterial({
          vertexShader: S.BEAM_VERT,
          fragmentShader: S.BEAM_FRAG,
          transparent: true,
          depthWrite: false,
          side: THREE.DoubleSide,
          blending: THREE.AdditiveBlending,
          uniforms: { uRadar: g.uRadar, uAlpha: g.uAlpha, uTime: g.uTime, uColor: { value: ink } },
        }),
      ),
    )
    beam.renderOrder = 3
    this.sat.add(bus, panel, boom, dish, beam)
    const orbitLine = new THREE.LineLoop(
      track(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 180 }, (_, i) => new THREE.Vector3(0, Math.cos((i / 180) * 6.2832) * ORBIT_R, Math.sin((i / 180) * 6.2832) * ORBIT_R)))),
      track(new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.14 })),
    )
    const orbit = new THREE.Group()
    orbit.rotation.set(0, 0.42, 0.12)
    orbit.add(this.sat, orbitLine)
    this.lineMats = [lineMat, orbitLine.material as THREE.LineBasicMaterial]

    this.rig.add(this.earth, this.clouds, orbit)
    this.scene.add(this.rig)

    // --- Terrain field ---
    const N = 210
    const pos = new Float32Array(N * N * 3)
    const rand = new Float32Array(N * N)
    for (let j = 0, k = 0; j < N; j++)
      for (let i = 0; i < N; i++, k++) {
        pos[k * 3] = (i / (N - 1)) * 2 - 1
        pos[k * 3 + 2] = (j / (N - 1)) * 2 - 1
        rand[k] = Math.random()
      }
    const fieldGeo = track(new THREE.BufferGeometry())
    fieldGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    fieldGeo.setAttribute('aRand', new THREE.BufferAttribute(rand, 1))
    this.field = new THREE.Points(
      fieldGeo,
      track(new THREE.ShaderMaterial({ vertexShader: S.FIELD_VERT, fragmentShader: S.FIELD_FRAG, transparent: true, depthWrite: false, uniforms: this.u.field })),
    )
    this.field.frustumCulled = false
    this.fieldRig.add(this.field)
    this.scene.add(this.fieldRig)

    this.resize()
    addEventListener('resize', this.resize)
    this.raf = requestAnimationFrame(this.frame)
  }

  private lineMats: THREE.LineBasicMaterial[] = []

  /** Skip easing — use when a page mounts already in its final state. */
  snap(state: StageState) {
    this.target = { ...state }
    this.cur = { ...state }
    this.shownMode = state.mode
  }

  resize = () => {
    const w = this.canvas.clientWidth
    const h = this.canvas.clientHeight
    if (!w || !h) return
    const dpr = Math.min(devicePixelRatio, 2)
    this.renderer.setPixelRatio(dpr)
    this.renderer.setSize(w, h, false)
    this.camera.aspect = w / h
    this.camera.updateProjectionMatrix()
    this.wide = w / h > 1.05 && !this.opts.centered
    // Point sizes are in device pixels at unit distance; scale with viewport so density reads the same everywhere.
    const k = (h / 900) * dpr
    this.u.landSize.value = 6.2 * k
    this.u.field.uSize.value = 8.2 * k
  }

  private frame = (now: number) => {
    this.raf = requestAnimationFrame(this.frame)
    const dt = Math.min(0.05, (now - this.last) / 1000 || 0)
    this.last = now
    if (!this.still) this.time += dt
    const t = this.still ? 14 : this.time
    const ease = this.still ? 1 : 1 - Math.exp(-dt * 5)
    const c = this.cur
    const tg = this.target
    for (const k of ['globe', 'cloud', 'radar', 'focus', 'terrain', 'progress'] as const) c[k] = mix(c[k], tg[k], ease)

    // Cross-fade the terrain through zero when the phenomenon changes.
    if (tg.mode !== this.shownMode) {
      this.modeFade = mix(this.modeFade, 0, Math.min(1, ease * 2.4))
      if (this.modeFade < 0.03 || c.terrain < 0.03) {
        this.shownMode = tg.mode
        c.progress = tg.progress
      }
    } else this.modeFade = mix(this.modeFade, 1, ease)

    const g = this.u.globe
    const f = this.u.field
    const wide = this.wide
    const centered = this.opts.centered

    // ---- Globe rig ----
    this.rig.visible = c.globe > 0.01
    if (this.rig.visible) {
      const fo = c.focus
      const s = mix(wide ? 1 : centered ? 1 : 0.7, wide || centered ? 2.2 : 1.6, fo)
      this.rig.scale.setScalar(s * mix(0.94, 1, c.globe))
      this.rig.position.set(wide ? mix(1.0, 0.72, fo) : 0, wide || centered ? mix(0, -0.05, fo) : mix(0.62, 0.5, fo), 0)
      this.spin += dt * 0.045 * (1 - sstep(0, 0.2, fo)) * (this.still ? 0 : 1)
      const aim = -FOCUS.lon + Math.round((this.spin + FOCUS.lon) / (2 * Math.PI)) * 2 * Math.PI
      this.earth.rotation.y = mix(this.spin, aim, fo)
      this.earth.rotation.x = mix(0.3, FOCUS.lat, fo)
      this.clouds.rotation.y = this.earth.rotation.y * 0.6 + t * 0.006
      this.clouds.rotation.x = this.earth.rotation.x

      const a = -t * 0.32 + 1.2
      this.sat.position.set(0, Math.cos(a) * ORBIT_R, Math.sin(a) * ORBIT_R)
      this.rig.updateMatrixWorld(true)
      this.sat.lookAt(this.rig.getWorldPosition(v1))
      this.sat.getWorldPosition(v2)
      g.uBeam.value.copy(this.earth.worldToLocal(v1.copy(v2))).normalize()
      this.u.cloudBeam.value.copy(this.clouds.worldToLocal(v1.copy(v2))).normalize()

      g.uAlpha.value = c.globe
      g.uCloud.value = c.cloud
      g.uRadar.value = c.radar
      g.uTime.value = t
      this.lineMats[0].opacity = 0.9 * c.globe
      this.lineMats[1].opacity = 0.14 * c.globe * (1 - fo)

      let i = 0
      for (const [id, m] of this.markers) {
        const on = tg.highlight ? (tg.highlight === id ? 1 : 0.35) : 1
        const presence = c.globe * mix(0.55, 1, fo) * (1 - 0.85 * c.cloud * (1 - c.radar)) * on
        const base = 0.013 * (tg.highlight === id ? 1.5 : 1)
        m.dot.scale.setScalar(base)
        m.dot.material.opacity = presence
        const ph = (t * 0.45 + i++ * 0.25) % 1
        m.ring.scale.setScalar(base * (1 + ph * 3.2))
        m.ring.material.opacity = presence * (1 - ph) * 0.8
      }
    }

    // ---- Terrain rig ----
    const fa = c.terrain * this.modeFade
    this.fieldRig.visible = fa > 0.01
    if (this.fieldRig.visible) {
      f.uAlpha.value = fa
      f.uTime.value = t
      f.uProgress.value = c.progress
      f.uMode.value = HOTSPOT_IDS.indexOf(this.shownMode)
      f.uHue.value = toThree(HUE[this.shownMode])
      this.fieldRig.position.set(wide ? 1.02 : 0, wide ? -0.12 : centered ? -0.1 : 0.62, 0)
      this.fieldRig.scale.setScalar((wide ? 1.3 : centered ? 1.45 : 0.82) * mix(0.9, 1, fa))
      this.fieldRig.rotation.set(0.62, -0.5 + Math.sin(t * 0.1) * 0.22, 0)
    }

    this.renderer.render(this.scene, this.camera)

    if (this.opts.onLabels) {
      const w = this.canvas.clientWidth
      const h = this.canvas.clientHeight
      this.rig.getWorldPosition(v2)
      const labels: Label[] = []
      for (const [id, m] of this.markers) {
        v1.copy(m.pos).applyMatrix4(this.earth.matrixWorld)
        const facing = v3.copy(v1).sub(v2).normalize().dot(v4.copy(this.camera.position).sub(v1).normalize())
        v1.project(this.camera)
        labels.push({ id, x: (v1.x * 0.5 + 0.5) * w, y: (-v1.y * 0.5 + 0.5) * h, alpha: sstep(0.15, 0.4, facing) * sstep(0.6, 0.95, c.focus) * c.globe })
      }
      this.opts.onLabels(labels)
    }
  }

  dispose() {
    cancelAnimationFrame(this.raf)
    removeEventListener('resize', this.resize)
    for (const d of this.disposables) d.dispose()
    this.renderer.dispose()
  }
}

const v1 = new THREE.Vector3()
const v2 = new THREE.Vector3()
const v3 = new THREE.Vector3()
const v4 = new THREE.Vector3()
