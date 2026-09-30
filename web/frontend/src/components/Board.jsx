// Renderer planszy — rysuje state.fields na siatce heksów. Zero reguł gry:
// podświetlenia (`highlight`) liczy rodzic z legal_actions.

import { useMemo } from 'react'
import { ALL_CELLS, BOARD_H, BOARD_W, R, cellCenter, hexPoints, islandGeometry } from '../data/geometry'
import { PLAYER_COLORS } from '../data/labels'
import { Building, Coin, EmptySlot, Metropolis, Prosperity, Ship, Warrior } from './icons'

const LAND = '#e6d3a0'
const LAND_EDGE = '#a88b52'

function CountBadge({ x, y, n, color }) {
  if (n <= 1) return null
  return (
    <g className="no-hit">
      <circle cx={x} cy={y} r="7.5" fill="#fff" stroke={color} strokeWidth="2" />
      <text x={x} y={y + 3.4} textAnchor="middle" fontSize="10" fontWeight="700" fill="#1a1410">{n}</text>
    </g>
  )
}

function Coins({ x, y, n, size = 11 }) {
  return Array.from({ length: n }, (_, i) => (
    <Coin key={i} x={x + i * (size - 2)} y={y} size={size} />
  ))
}

function IslandContent({ id, field, geo }) {
  const { cx, cy } = geo
  const owner = PLAYER_COLORS[field.owner]
  const slots = Object.entries(field.buildings)
  const S = 15
  const rowW = slots.length * (S + 2) - 2
  const qty = field.entity?.quantity ?? 0
  return (
    <g className="no-hit">
      <text x={cx} y={cy - 25} textAnchor="middle" className="field-label">{id}</text>
      {qty > 0 && <>
        <Warrior x={cx - 24} y={cy - 20} size={19} color={owner ?? '#999'} />
        <CountBadge x={cx - 6} y={cy - 4} n={qty} color={owner ?? '#999'} />
      </>}
      <Coins x={qty > 0 ? cx + 2 : cx - (field.base_income * 9) / 2} y={cy - 18} n={field.base_income} />
      {field.income?.quantity > 0 && (
        <Prosperity x={cx + 12} y={cy - 9} size={17} n={field.income.quantity} />
      )}
      {field.is_metropolis
        ? <Metropolis x={cx - 15} y={cy + 1} size={30} owner={owner} />
        : slots.map(([slot, b], i) => {
          const x = cx - rowW / 2 + i * (S + 2)
          return b
            ? <Building key={slot} x={x} y={cy + 4} size={S} hero={b.hero} owner={owner} />
            : <EmptySlot key={slot} x={x} y={cy + 4} size={S} />
        })}
    </g>
  )
}

function WaterContent({ id, field }) {
  const { x, y } = cellCenter(id)
  const owner = PLAYER_COLORS[field.owner]
  const qty = field.entity?.quantity ?? 0
  return (
    <g className="no-hit">
      {field.base_income > 0 && <Coins x={x - (field.base_income * 9) / 2 - 1} y={y - 30} n={field.base_income} />}
      {qty > 0 && <>
        <Ship x={x - 14} y={y - 15} size={28} color={owner ?? '#999'} />
        <CountBadge x={x + 13} y={y + 10} n={qty} color={owner ?? '#999'} />
      </>}
      <text x={x} y={y + 25} textAnchor="middle" className="water-label">{id}</text>
    </g>
  )
}

export default function Board({ fields, islands, highlight, selected, targets, onFieldClick }) {
  const islandGeo = useMemo(() => Object.fromEntries(
    Object.entries(islands).map(([id, cfg]) => [id, islandGeometry(cfg.location)])), [islands])

  const waterIds = ALL_CELLS.filter((c) => fields[c]?.type === 'water')
  const islandIds = Object.keys(islandGeo).filter((id) => fields[id])

  // komórki siatki należące do pola (woda = 1, wyspa = kilka)
  const cellsOf = (id) => islandGeo[id] ? islandGeo[id].cells : [cellCenter(id)]

  const markState = (id) =>
    id === selected ? 'selected' : targets?.has(id) ? 'target' : highlight?.has(id) ? 'legal' : null

  return (
    <svg className="board" viewBox={`0 0 ${BOARD_W} ${BOARD_H}`} preserveAspectRatio="xMidYMid meet">
      <defs>
        <radialGradient id="sea" cx="50%" cy="45%" r="70%">
          <stop offset="0%" stopColor="#2a7fb0" />
          <stop offset="100%" stopColor="#0f3a5c" />
        </radialGradient>
        <linearGradient id="land" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#efe0b4" />
          <stop offset="100%" stopColor={LAND} />
        </linearGradient>
      </defs>

      <rect width={BOARD_W} height={BOARD_H} rx="18" fill="url(#sea)" />

      {/* morze */}
      {waterIds.map((id) => {
        const { x, y } = cellCenter(id)
        return <polygon key={id} points={hexPoints(x, y, R - 1)} className="water-hex" />
      })}

      {/* wyspy: najpierw obrys (kolor właściciela), potem ląd — szwy między heksami znikają */}
      {islandIds.map((id) => (
        <g key={id}>
          {islandGeo[id].cells.map((p, i) => (
            <polygon key={i} points={hexPoints(p.x, p.y, R + 4.5)}
              fill={PLAYER_COLORS[fields[id].owner] ?? LAND_EDGE} />
          ))}
        </g>
      ))}
      {islandIds.map((id) => (
        <g key={id}>
          {islandGeo[id].cells.map((p, i) => (
            <polygon key={i} points={hexPoints(p.x, p.y, R - 1)} fill="url(#land)" stroke={LAND} strokeWidth="3" />
          ))}
        </g>
      ))}

      {waterIds.map((id) => <WaterContent key={id} id={id} field={fields[id]} />)}
      {islandIds.map((id) => <IslandContent key={id} id={id} field={fields[id]} geo={islandGeo[id]} />)}

      {/* podświetlenia + obszary klikalne (na wierzchu) */}
      {[...waterIds, ...islandIds].map((id) => {
        const mark = markState(id)
        return (
          <g key={id} className={`hit ${mark ?? ''}`} onClick={() => onFieldClick?.(id)}>
            {cellsOf(id).map((p, i) => (
              <polygon key={i} points={hexPoints(p.x, p.y, R - 3)} />
            ))}
          </g>
        )
      })}
    </svg>
  )
}
