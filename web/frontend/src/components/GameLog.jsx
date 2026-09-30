import { PLAYER_COLORS, describeAction, heroName } from '../data/labels'

export default function GameLog({ log }) {
  return (
    <div className="panel log">
      <h3>Przebieg</h3>
      <ol reversed>
        {[...log].reverse().map((e) => (
          <li key={e.step}>
            <span className="muted">r{e.round_no}</span>{' '}
            <b style={{ color: PLAYER_COLORS[e.player] }}>{e.player}</b>{' '}
            {e.hero && e.hero !== 'None' && <span className="muted">({heroName(e.hero)}) </span>}
            {describeAction(e.action)}
            {e.info?.combat && <span className="combat"> · walka → {e.info.winner}</span>}
            {e.decision_ms != null && <span className="muted"> · {Math.round(e.decision_ms)} ms</span>}
            {e.detail?.input_tokens > 0 && (
              <span className="muted"> · {e.detail.input_tokens}+{e.detail.output_tokens} tok</span>
            )}
            {e.detail?.fallback_used && <span className="combat"> · fallback (losowa akcja)</span>}
            {e.detail?.illegal_attempts > 0 && <span className="combat"> · {e.detail.illegal_attempts}× nietrafione</span>}
            {e.detail?.reasoning && <div className="reasoning">„{e.detail.reasoning}”</div>}
          </li>
        ))}
      </ol>
    </div>
  )
}
