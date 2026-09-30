// Geometria planszy — czysta prezentacja. Plansza to 91 heksów w 11 rzędach
// (A–K, długości 6→11→6); pole wodne = 1 heks, wyspa = kilka heksów (layout z API).
// Topologia (sąsiedzi) NIE jest tu liczona — przychodzi ze stanu silnika.

export const R = 38                     // promień heksa (pointy-top)
export const HEX_W = Math.sqrt(3) * R
const ROW_H = 1.5 * R
const PAD = 14
const ROWS = 'ABCDEFGHIJK'

export const BOARD_W = 11 * HEX_W + 2 * PAD
export const BOARD_H = 10 * ROW_H + 2 * R + 2 * PAD

export const rowLength = (k) => 6 + Math.min(k, 10 - k)

export function cellCenter(cellId) {
  const k = ROWS.indexOf(cellId[0])
  const c = Number(cellId.slice(1)) - 1
  const len = rowLength(k)
  return {
    x: BOARD_W / 2 + (c - (len - 1) / 2) * HEX_W,
    y: PAD + R + k * ROW_H,
  }
}

export const ALL_CELLS = [...ROWS].flatMap((r, k) =>
  Array.from({ length: rowLength(k) }, (_, i) => `${r}${i + 1}`))

export function hexPoints(cx, cy, r = R) {
  return Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 90)
    return `${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`
  }).join(' ')
}

// środek ciężkości wyspy + kotwice na jednostki/budynki
export function islandGeometry(location) {
  const pts = location.map(cellCenter)
  const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length
  const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length
  // komórka najbliższa środkowi — tam rysujemy jednostki, żeby nie wypadły do wody
  const anchor = pts.reduce((best, p) =>
    Math.hypot(p.x - cx, p.y - cy) < Math.hypot(best.x - cx, best.y - cy) ? p : best)
  return { cells: pts, cx, cy, anchor }
}
