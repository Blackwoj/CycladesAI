// Grafiki gry — ręcznie narysowane SVG (viewBox 64×64), kolorowane propsami.
// Działają zarówno w HTML (<Icon .../>), jak i zagnieżdżone w SVG planszy (x/y/size).

import { HEROES } from '../data/labels'

const INK = '#1a1410'

function Frame({ x, y, size = 32, children, title }) {
  return (
    <svg x={x} y={y} width={size} height={size} viewBox="0 0 64 64" style={{ overflow: 'visible' }}>
      {title && <title>{title}</title>}
      {children}
    </svg>
  )
}

// ---- symbole herosów --------------------------------------------------------

const HeroGlyphs = {
  ares: (c) => (
    <g fill={c}>
      <path d="M13 24 Q32 -4 51 24 Q32 12 13 24 Z" />
      <path d="M16 48 V31 A16 16 0 0 1 48 31 V48 H41 V36 H35 V54 H29 V36 H23 V48 Z" />
    </g>
  ),
  atena: (c) => (
    <g>
      <path d="M14 12 L22 20 H42 L50 12 L50 40 Q50 58 32 58 Q14 58 14 40 Z" fill={c} />
      <circle cx="24" cy="30" r="8" fill="#fff" /><circle cx="40" cy="30" r="8" fill="#fff" />
      <circle cx="24" cy="30" r="3.5" fill={INK} /><circle cx="40" cy="30" r="3.5" fill={INK} />
      <path d="M29 38 L35 38 L32 45 Z" fill="#f0c330" />
    </g>
  ),
  posejdon: (c) => (
    <g stroke={c} strokeWidth="5" fill="none" strokeLinecap="round" strokeLinejoin="round">
      <path d="M32 60 V14" />
      <path d="M16 10 V24 Q16 34 32 34 Q48 34 48 24 V10" />
      <path d="M12 16 L16 8 L20 16 M28 12 L32 4 L36 12 M44 16 L48 8 L52 16" />
    </g>
  ),
  zeus: (c) => (
    <polygon points="38,3 13,36 29,36 22,61 51,25 35,25 44,3" fill={c} stroke={INK} strokeWidth="1.5" strokeLinejoin="round" />
  ),
  apollon: (c) => (
    <g fill={c} stroke={c}>
      <circle cx="32" cy="32" r="12" />
      {Array.from({ length: 12 }, (_, i) => {
        const a = (i * Math.PI) / 6
        return <line key={i} strokeWidth="4" strokeLinecap="round"
          x1={32 + 17 * Math.cos(a)} y1={32 + 17 * Math.sin(a)}
          x2={32 + (i % 2 ? 24 : 28) * Math.cos(a)} y2={32 + (i % 2 ? 24 : 28) * Math.sin(a)} />
      })}
    </g>
  ),
}
HeroGlyphs.ap_s = HeroGlyphs.apollon

// Portret herosa: medalion w kolorze boga z białym symbolem
export function HeroPortrait({ hero, size = 56, dim = false }) {
  const h = HEROES[hero]
  const glyph = HeroGlyphs[hero]
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" style={{ opacity: dim ? 0.35 : 1, flex: 'none' }}>
      <title>{h?.name ?? 'brak'}</title>
      <circle cx="32" cy="32" r="31" fill={h?.color ?? '#3a4658'} />
      <circle cx="32" cy="32" r="27" fill="none" stroke="#f0e6c8" strokeOpacity=".5" strokeWidth="1.5" />
      {glyph && <g transform="translate(12 12) scale(.625)">{glyph('#fff')}</g>}
    </svg>
  )
}

// ---- jednostki --------------------------------------------------------------

export function Warrior({ x, y, size, color }) {
  return (
    <Frame x={x} y={y} size={size} title="wojownik">
      <path d="M13 24 Q32 -4 51 24 Q32 12 13 24 Z" fill={color} stroke={INK} strokeWidth="3" />
      <path d="M16 50 V31 A16 16 0 0 1 48 31 V50 H41 V37 H35 V56 H29 V37 H23 V50 Z"
        fill={color} stroke={INK} strokeWidth="3" strokeLinejoin="round" />
    </Frame>
  )
}

export function Ship({ x, y, size, color }) {
  return (
    <Frame x={x} y={y} size={size} title="statek">
      <path d="M32 8 V40" stroke={INK} strokeWidth="3" />
      <path d="M34 10 Q52 22 34 36 Z" fill="#f0e6c8" stroke={INK} strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M30 12 Q16 24 30 36 Z" fill="#f0e6c8" stroke={INK} strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M4 40 H60 L50 54 H14 Z" fill={color} stroke={INK} strokeWidth="3" strokeLinejoin="round" />
      <path d="M60 40 Q64 34 60 30" stroke={INK} strokeWidth="3" fill="none" />
    </Frame>
  )
}

// ---- budynki ----------------------------------------------------------------

const BuildingGlyphs = {
  ares: <path d="M14 56 V22 H22 V28 H28 V22 H36 V28 H42 V22 H50 V56 H38 V44 A6 6 0 0 0 26 44 V56 Z" />,
  posejdon: (
    <g fill="none" strokeWidth="5" strokeLinecap="round">
      <circle cx="32" cy="14" r="5" />
      <path d="M32 19 V56 M20 28 H44 M12 40 Q14 56 32 56 Q50 56 52 40" />
    </g>
  ),
  atena: (
    <g>
      <path d="M8 16 Q20 10 31 16 V54 Q20 48 8 54 Z" />
      <path d="M56 16 Q44 10 33 16 V54 Q44 48 56 54 Z" />
    </g>
  ),
  zeus: <path d="M32 6 L60 22 H4 Z M8 26 H16 V50 H8 Z M22 26 H30 V50 H22 Z M34 26 H42 V50 H34 Z M48 26 H56 V50 H48 Z M4 52 H60 V58 H4 Z" />,
}

export function Building({ x, y, size, hero, owner }) {
  const glyph = BuildingGlyphs[hero]
  const c = HEROES[hero]?.color ?? '#777'
  return (
    <Frame x={x} y={y} size={size} title={`budynek: ${HEROES[hero]?.name ?? hero}`}>
      <rect x="2" y="2" width="60" height="60" rx="12" fill={c} stroke={owner ?? INK} strokeWidth="6" />
      <g transform="translate(12 12) scale(.625)" fill="#fff" stroke="#fff">{glyph}</g>
    </Frame>
  )
}

export function EmptySlot({ x, y, size }) {
  return (
    <Frame x={x} y={y} size={size} title="wolne miejsce na budynek">
      <rect x="6" y="6" width="52" height="52" rx="10" fill="#000" fillOpacity=".08"
        stroke="#6b5a3a" strokeOpacity=".55" strokeWidth="4" strokeDasharray="8 6" />
    </Frame>
  )
}

export function Metropolis({ x, y, size, owner }) {
  return (
    <Frame x={x} y={y} size={size} title="metropolia">
      <circle cx="32" cy="32" r="30" fill="#c9a84c" stroke={owner ?? INK} strokeWidth="5" />
      <path d="M12 50 V30 H20 V20 H26 V12 H38 V20 H44 V30 H52 V50 Z" fill="#fff" />
      <path d="M28 50 V40 H36 V50 M16 36 H18 M46 36 H48 M30 20 H34" stroke="#c9a84c" strokeWidth="3" />
    </Frame>
  )
}

// Znacznik dochodu Apollona — róg obfitości z liczbą znaczników
export function Prosperity({ x, y, size = 18, n = 1 }) {
  return (
    <Frame x={x} y={y} size={size} title={`znacznik dochodu +${n}`}>
      <circle cx="32" cy="32" r="30" fill="#e57a1f" stroke="#1a1410" strokeWidth="3" />
      <path d="M14 20 Q20 50 46 48 L50 36 Q30 38 24 16 Z" fill="#f6d27a" stroke="#1a1410" strokeWidth="3" strokeLinejoin="round" />
      <circle cx="50" cy="42" r="5" fill="#b83227" /><circle cx="44" cy="50" r="4" fill="#3fbf6f" />
      {n > 1 && <text x="20" y="54" fontSize="22" fontWeight="800" fill="#fff" stroke="#1a1410" strokeWidth="1">{n}</text>}
    </Frame>
  )
}

// ---- zasoby -----------------------------------------------------------------

export function Coin({ x, y, size = 14 }) {
  return (
    <Frame x={x} y={y} size={size} title="dochód">
      <circle cx="32" cy="32" r="28" fill="#e8c96c" stroke="#8a6414" strokeWidth="6" />
      <circle cx="32" cy="32" r="15" fill="none" stroke="#8a6414" strokeWidth="4" />
    </Frame>
  )
}

export function ResourceIcon({ kind, size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" style={{ flex: 'none', verticalAlign: 'middle' }}>
      {kind === 'coins' && <>
        <circle cx="32" cy="32" r="28" fill="#e8c96c" stroke="#8a6414" strokeWidth="6" />
        <circle cx="32" cy="32" r="15" fill="none" stroke="#8a6414" strokeWidth="4" />
      </>}
      {kind === 'philosophers' && <g fill="#9fb9d9">
        <rect x="14" y="10" width="36" height="44" rx="4" />
        <rect x="8" y="6" width="48" height="10" rx="5" fill="#d8e4f2" />
        <rect x="8" y="48" width="48" height="10" rx="5" fill="#d8e4f2" />
        <path d="M22 26 H42 M22 34 H42 M22 42 H36" stroke="#2b3f57" strokeWidth="3" />
      </g>}
      {kind === 'priests' && <g>
        <path d="M32 6 Q48 24 40 36 Q44 26 32 20 Q34 30 26 36 Q16 24 32 6 Z" fill="#f08a24" />
        <path d="M16 40 H48 L44 58 H20 Z" fill="#e8c96c" stroke="#8a6414" strokeWidth="3" />
      </g>}
      {kind === 'metro' && <path d="M8 56 V30 H18 V18 H26 V8 H38 V18 H46 V30 H56 V56 Z" fill="#c9a84c" />}
      {kind === 'island' && <polygon points="32,4 58,18 58,46 32,60 6,46 6,18" fill="#d9c48c" stroke="#8a6414" strokeWidth="4" />}
    </svg>
  )
}
