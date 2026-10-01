// Tor Mitologicznych Stworów — przyciski to wyłącznie legal_actions (koszt po zniżkach liczy silnik).

import { CREATURES, PLAYER_COLORS, TRACK_COSTS, creatureName } from '../data/labels'
import { CreatureIcon } from './icons'

export default function CreaturePanel({ cards, legal, onAction, disabled }) {
  if (!cards || !cards.track) return null
  const figures = Object.entries(cards.figures ?? {})
  return (
    <div className="panel">
      <h3>Mitologiczne Stwory</h3>
      <div className="track">
        {cards.track.map((c, slot) => {
          const buy = legal.find((a) => a.type === 'buy_creature' && a.slot === slot)
          const swap = legal.find((a) => a.type === 'replace_creature' && a.slot === slot)
          return (
            <div key={slot} className={`track-slot ${c ? '' : 'empty'}`}>
              <div className="track-cost">{TRACK_COSTS[slot]} GP</div>
              {c ? <>
                <CreatureIcon id={c} size={46} title={creatureName(c)} />
                <b>{creatureName(c)}</b>
                <span className="muted small-text">{CREATURES[c]?.desc}</span>
                {buy && <button className="btn small" disabled={disabled} onClick={() => onAction(buy)}>Wezwij</button>}
                {swap && <button className="btn small ghost" disabled={disabled} onClick={() => onAction(swap)}
                  title="Zeus: za 1 GP odrzuć i dociągnij nowego">Wymień (1 GP)</button>}
              </> : <span className="muted small-text">puste</span>}
            </div>
          )
        })}
      </div>
      <div className="muted small-text">
        stos: {cards.deck?.length ?? 0} · odrzucone: {cards.discard?.length ?? 0}
        {figures.length > 0 && <> · figurki: {figures.map(([n, f]) => (
          <span key={n} className="chip" style={{ background: PLAYER_COLORS[f.owner] ?? '#ccc' }}>{creatureName(n)} {f.field}</span>
        ))}</>}
      </div>
    </div>
  )
}
