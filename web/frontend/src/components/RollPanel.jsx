// Faza ROLL — aukcja herosów. Przyciski licytacji to wyłącznie legal_actions.

import { PLAYER_COLORS, heroName } from '../data/labels'
import { HeroPortrait } from './icons'

function PlayerChip({ pid }) {
  return <span className="chip" style={{ background: PLAYER_COLORS[pid] }}>{pid}</span>
}

export default function RollPanel({ state, legal, onAction, disabled }) {
  const rows = Object.entries(state.roll.heros_per_row).sort(([a], [b]) => a.localeCompare(b))
  const apollo = legal.find((a) => a.type === 'apollon_bid')

  return (
    <div className="panel">
      <h3>Licytacja bogów · runda {state.round_no}</h3>
      <div className="roll-rows">
        {rows.map(([row, hero]) => {
          if (!hero) return null
          if (row === 'row_5') {
            const joined = state.roll.bids.row_5 ?? []
            return (
              <div key={row} className="roll-row">
                <HeroPortrait hero="apollon" size={44} />
                <div className="roll-info">
                  <b>Apollon</b>
                  <div className="muted">{joined.length ? joined.map((p) => <PlayerChip key={p} pid={p} />) : 'nikt'}</div>
                </div>
                {apollo && <button className="btn" disabled={disabled} onClick={() => onAction(apollo)}>Wybierz</button>}
              </div>
            )
          }
          const bid = state.roll.bids[row] ?? {}
          const bids = legal.filter((a) => a.type === 'roll_bid' && a.row === row)
          return (
            <div key={row} className="roll-row">
              <HeroPortrait hero={hero} size={44} />
              <div className="roll-info">
                <b>{heroName(hero)}</b>
                <div className="muted">
                  {bid.player ? <>oferta <b>{bid.bid}</b> · <PlayerChip pid={bid.player} /></> : 'brak ofert'}
                </div>
              </div>
              <div className="bid-buttons">
                {bids.map((a) => (
                  <button key={a.amount} className="btn small" disabled={disabled}
                    onClick={() => onAction(a)} title={`licytuj ${a.amount}`}>{a.amount}</button>
                ))}
              </div>
            </div>
          )
        })}
      </div>
      {state.roll.bid_order.length > 0 && (
        <div className="muted small-text">Dalej licytują: {state.roll.bid_order.map((p) => <PlayerChip key={p} pid={p} />)}</div>
      )}
    </div>
  )
}
