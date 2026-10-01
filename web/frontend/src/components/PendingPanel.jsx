// Wybór w toku (obowiązkowa Metropolia albo cel Stwora) — tylko akcje z legal_actions.

import { CREATURES, creatureName, describeTargets } from '../data/labels'
import { CreatureIcon } from './icons'

export const actionFields = (a) =>
  a.type === 'play_card' ? (a.targets ?? []).filter((x) => typeof x === 'string') : a.field_id ? [a.field_id] : []

export default function PendingPanel({ pending, legal, selected, onAction, onClear, disabled }) {
  const shown = selected ? legal.filter((a) => actionFields(a).includes(selected) || a.targets?.[0] === 'done') : legal
  const metro = pending.kind === 'metropolis'
  return (
    <div className="panel pending">
      <h3>{metro ? 'Metropolia!' : `Stwór: ${creatureName(pending.card)}`}</h3>
      <div className="pending-head">
        {!metro && <CreatureIcon id={pending.card} size={44} />}
        <p>{metro
          ? `Masz ${pending.source === 'philosophers' ? '4 Filozofów' : 'komplet 4 budynków'} — wybierz wyspę na Metropolię.`
          : CREATURES[pending.card]?.desc}
          {pending.budget !== undefined && <> · zostało ruchów: <b>{pending.budget}</b></>}
        </p>
      </div>
      <p className="muted small-text">
        {selected ? <>Opcje dla <b>{selected}</b> · <a href="#" onClick={(e) => { e.preventDefault(); onClear() }}>pokaż wszystkie</a></>
          : 'Kliknij podświetlone pole albo wybierz z listy.'}
      </p>
      <div className="action-list scroll">
        {shown.map((a, i) => (
          <button key={i} className={`btn ${a.targets?.[0] === 'done' ? 'ghost' : ''}`} disabled={disabled} onClick={() => onAction(a)}>
            {a.type === 'build' ? `Metropolia na ${a.field_id}` : describeTargets(a)}
          </button>
        ))}
      </div>
    </div>
  )
}
