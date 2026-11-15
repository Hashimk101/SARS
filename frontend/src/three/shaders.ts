const SNOISE = /* glsl */ `
vec3 permute(vec3 x){ return mod(((x*34.0)+1.0)*x, 289.0); }
float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
  m = m*m; m = m*m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}
float fbm(vec2 p){
  float a = 0.5, s = 0.0;
  for (int i = 0; i < 4; i++) { s += a * snoise(p); p *= 2.03; a *= 0.5; }
  return s;
}
`

const POINT_FRAG = /* glsl */ `
varying vec3 vColor;
varying float vA;
void main(){
  float d = length(gl_PointCoord - 0.5);
  if (d > 0.5) discard;
  gl_FragColor = vec4(vColor, vA * smoothstep(0.5, 0.15, d));
  #include <colorspace_fragment>
}
`

/* ---------- Globe ---------- */

export const LAND_VERT = /* glsl */ `
uniform float uSize, uCloud, uRadar, uAlpha;
uniform vec3 uBeam, uColor;
varying vec3 vColor;
varying float vA;
void main(){
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  vec3 n = normalize(normalMatrix * position);
  float facing = dot(n, normalize(-mv.xyz));
  // Under cloud the surface is hidden from optical sensors; only the radar footprint still resolves it.
  float inBeam = smoothstep(0.90, 0.975, dot(normalize(position), uBeam)) * uRadar;
  float seen = mix(1.0, 0.10 + 0.90 * inBeam, uCloud);
  vA = smoothstep(-0.05, 0.45, facing) * seen * uAlpha * 0.9;
  vColor = uColor;
  gl_PointSize = uSize / -mv.z;
  gl_Position = projectionMatrix * mv;
}
`
export const LAND_FRAG = POINT_FRAG

export const OCEAN_VERT = /* glsl */ `
varying vec3 vN, vV;
void main(){
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  vN = normalize(normalMatrix * normal);
  vV = normalize(-mv.xyz);
  gl_Position = projectionMatrix * mv;
}
`
export const OCEAN_FRAG = /* glsl */ `
uniform vec3 uBase, uRim;
uniform float uAlpha;
varying vec3 vN, vV;
void main(){
  float rim = pow(1.0 - max(dot(normalize(vN), normalize(vV)), 0.0), 3.5);
  gl_FragColor = vec4(mix(uBase, uRim, rim * 0.55), uAlpha);
  #include <colorspace_fragment>
}
`

export const CLOUD_VERT = /* glsl */ `
varying vec3 vP, vN, vV;
void main(){
  vP = normalize(position);
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  vN = normalize(normalMatrix * normal);
  vV = normalize(-mv.xyz);
  gl_Position = projectionMatrix * mv;
}
`
export const CLOUD_FRAG = /* glsl */ `
uniform float uTime, uCloud, uRadar, uAlpha;
uniform vec3 uBeam, uColor;
varying vec3 vP, vN, vV;
float hash(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float noise(vec3 x){
  vec3 i = floor(x), f = fract(x);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x), mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x), mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}
void main(){
  vec3 p = vP * 2.6 + vec3(uTime * 0.02, 0.0, uTime * 0.012);
  float n = 0.55 * noise(p) + 0.28 * noise(p * 2.1) + 0.17 * noise(p * 4.3);
  float cover = smoothstep(0.34, 0.62, n);
  float hole = smoothstep(0.90, 0.975, dot(vP, uBeam)) * uRadar;
  float facing = max(dot(normalize(vN), normalize(vV)), 0.0);
  float a = cover * uCloud * uAlpha * (1.0 - 0.92 * hole) * smoothstep(0.0, 0.35, facing) * 0.62;
  gl_FragColor = vec4(uColor, a);
  #include <colorspace_fragment>
}
`

export const BEAM_VERT = /* glsl */ `
varying vec2 vUv;
void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
`
export const BEAM_FRAG = /* glsl */ `
uniform float uRadar, uAlpha, uTime;
uniform vec3 uColor;
varying vec2 vUv;
void main(){
  // Pulses travel from the antenna (v = 1) down to the ground (v = 0).
  float pulse = 0.5 + 0.5 * sin((vUv.y * 9.0 + uTime * 2.2) * 6.2831);
  float a = uRadar * uAlpha * (0.05 + 0.10 * vUv.y + 0.06 * pulse * pulse);
  gl_FragColor = vec4(uColor, a);
  #include <colorspace_fragment>
}
`

/* ---------- Terrain field: one point grid, four physical behaviours ---------- */

export const FIELD_VERT = /* glsl */ `
uniform float uTime, uProgress, uAlpha, uSize;
uniform int uMode;
uniform vec3 uHue, uInk;
attribute float aRand;
varying vec3 vColor;
varying float vA;
${SNOISE}
void main(){
  vec2 q = position.xz;
  float h = 0.0, a = 0.5;
  vec3 col = uInk;

  if (uMode == 0) {
    // FLOOD — water level rises out of the river channel across the floodplain.
    // Open water reflects the pulse away from the sensor, so flooded ground goes dim; the shoreline stays bright.
    float c = abs(q.x + 0.28 * sin(q.y * 2.4));
    h = 0.05 * smoothstep(0.02, 0.10, c) + 0.20 * pow(c, 1.6) + fbm(q * 2.4) * 0.03;
    float level = mix(0.03, 0.20, uProgress);
    float wet = smoothstep(level + 0.004, level - 0.004, h);
    float shore = 1.0 - smoothstep(0.0, 0.016, abs(h - level));
    h = mix(h, level + 0.0025 * sin(uTime * 1.4 + q.y * 16.0 + q.x * 9.0), wet);
    col = mix(uInk, uHue, max(wet, shore));
    a = mix(0.42, 0.30, wet) + shore * 0.55;
  } else if (uMode == 1) {
    // SUBSIDENCE — a bowl deepens in the valley floor; colour bands are interferogram fringes of the displacement.
    h = fbm(q * 1.8) * 0.045 + smoothstep(0.5, 1.1, length(q)) * 0.26;
    vec2 o = q - vec2(0.06, -0.04);
    float d = uProgress * 0.34 * exp(-dot(o, o) / 0.11);
    h -= d;
    float fringe = 0.5 + 0.5 * cos(d * 90.0);
    float m = smoothstep(0.004, 0.03, d);
    col = mix(uInk, uHue, m * (0.3 + 0.7 * fringe));
    a = 0.38 + m * 0.5 * fringe;
  } else if (uMode == 2) {
    // CANOPY — forest gives volume scattering (points lifted off the ground); a clearing front climbs the hills
    // and leaves the regular bright grid of built-up land behind it.
    float ridge = smoothstep(-0.25, 0.75, q.y + 0.16 * snoise(q * 1.5));
    h = ridge * 0.30 + fbm(q * 3.0) * 0.035 * ridge;
    float forest = smoothstep(0.14, 0.30, ridge);
    float front = mix(0.14, 0.80, uProgress) + 0.07 * snoise(q * 4.0);
    float cleared = forest * smoothstep(front + 0.03, front - 0.03, ridge);
    float alive = forest * (1.0 - cleared);
    h += alive * aRand * 0.075;
    vec2 g = abs(fract(q * 13.0) - 0.5);
    float street = 1.0 - smoothstep(0.0, 0.10, min(g.x, g.y));
    col = mix(uInk, uHue, alive);
    a = mix(0.16 + 0.55 * street, 0.42 + 0.4 * aRand, alive);
  } else {
    // GLACIER — ice in the valley flows downstream, fastest at the centreline; velocity climbs with progress.
    float w = 0.27;
    float c = q.x - 0.30 * sin(q.y * 1.7 + 0.4);
    float lane = c / w;
    float inside = 1.0 - smoothstep(0.82, 1.0, abs(lane));
    if (abs(lane) < 1.0) {
      float speed = mix(0.025, 0.13, uProgress) * (1.0 - lane * lane);
      float z = mod(q.y - uTime * speed + 1.0, 2.0) - 1.0;
      q = vec2(lane * w + 0.30 * sin(z * 1.7 + 0.4), z);
    }
    h = (1.0 - inside) * (0.10 + 0.30 * smoothstep(1.0, 3.0, abs(lane)) + fbm(q * 3.0) * 0.05)
      + inside * (0.035 + 0.012 * snoise(vec2(lane * 3.0, q.y * 22.0)))
      - q.y * 0.07;
    col = mix(uInk, uHue, inside);
    a = mix(0.32, 0.35 + 0.5 * aRand, inside);
  }

  // Radar swath sweeping across the scene.
  float sweep = fract(uTime * 0.11) * 2.6 - 1.3;
  a += (1.0 - smoothstep(0.0, 0.05, abs(q.y - sweep))) * 0.3;

  a *= smoothstep(1.0, 0.72, length(q));
  vColor = col;
  vA = a * uAlpha;
  vec4 mv = modelViewMatrix * vec4(q.x, h, q.y, 1.0);
  gl_PointSize = uSize / -mv.z;
  gl_Position = projectionMatrix * mv;
}
`
export const FIELD_FRAG = POINT_FRAG
