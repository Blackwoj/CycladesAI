// Faza BOARD — akcje człowieka. Wszystko wynika z filtrowania legal_actions.

import { heroName } from '../data/labels'

export function fieldActions(legal, id) {
  return legal.filter((a) => a.field_id === id || a.from_field === id)
}

function fieldActionLabel(a) {
  if (a.type === 'place_entity') return a.kind === 'warrior' ? 'Rekrutuj wojownika' : 'Zbuduj statek'
  if (a.type === 'place_income') return 'Połóż znacznik dochodu (+1)'
  if (a.type === 'build') return a.hero === 'metro' ? 'Zbuduj metropolię' : `Zbuduj budynek (${heroName(a.hero)})`
  return a.type
}

export default function ActionPanel({ legal, selected, moveFrom, pendingMove, onAction, onStartMove, onCancel, disabled }) {
  const global = legal.filter((a) => a.type === 'buy_card' || a.type === 'end_turn')
  const endTurn = global.find((a) => a.type === 'end_turn')
  const cards = global.filter((a) => a.type === 'buy_card')

  let body
  if (pendingMove) {
    body = <>
      <p>Ile jednostek z <b>{pendingMove.from}</b> na <b>{pendingMove.to}</b>?</p>
      <div className="bid-buttons">
        {pendingMove.options.map((a) => (
          <button key={a.quantity} className="btn" disabled={disabled} onClick={() => onAction(a)}>{a.quantity}</button>
        ))}
      </div>
      <button className="btn ghost" onClick={onCancel}>Anuluj</button>
    </>
  } else if (moveFrom) {
    body = <>
      <p>Wybierz cel ruchu z <b>{moveFrom}</b> (podświetlone pola).</p>
      <button className="btn ghost" onClick={onCancel}>Anuluj</button>
    </>
  } else if (selected) {
    const acts = fieldActions(legal, selected)
    const direct = acts.filter((a) => a.type !== 'move_entity')
    const canMove = acts.some((a) => a.type === 'move_entity' && a.from_field === selected)
    body = <>
      <p>Pole <b>{selected}</b></p>
      <div className="action-list">
        {direct.map((a, i) => (
          <button key={i} className="btn" disabled={disabled} onClick={() => onAction(a)}>{fieldActionLabel(a)}</button>
        ))}
        {canMove && <button className="btn" disabled={disabled} onClick={() => onStartMove(selected)}>Przesuń jednostki stąd…</button>}
      </div>
      <button className="btn ghost" onClick={onCancel}>Zamknij</button>
    </>
  } else if (legal.some((a) => a.type === 'place_income')) {
    body = <p>Apollon: kliknij swoją wyspę, żeby położyć <b>znacznik dochodu (+1)</b>.</p>
  } else {
    body = <p className="muted">
      {legal.some((a) => a.field_id || a.from_field)
        ? 'Kliknij podświetlone pole na planszy.'
        : 'Brak akcji na planszy w tej turze.'}
    </p>
  }

  return (
    <div className="panel">
      <h3>Twoja tura</h3>
      {body}
      <div className="action-list global">
        {cards.map((a) => (
          <button key={a.hero} className="btn" disabled={disabled} onClick={() => onAction(a)}>
            Kup kartę {a.hero === 'atena' ? 'filozofa' : 'kapłana'}
          </button>
        ))}
        {endTurn && <button className="btn primary" disabled={disabled} onClick={() => onAction(endTurn)}>Zakończ turę</button>}
      </div>
    </div>
  )
}
