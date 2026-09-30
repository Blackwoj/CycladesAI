import { PLAYER_COLORS, heroName } from '../data/labels'
import { HeroPortrait, ResourceIcon } from './icons'

export default function PlayersPanel({ state, labels, actPlayer }) {
  const count = (pid, pred) => Object.values(state.fields).filter((f) => f.owner === pid && pred(f)).length
  return (
    <div className="panel players">
      {Object.values(state.players).map((p) => {
        const hero = state.hero_players[p.player_id]
        const active = p.player_id === actPlayer
        return (
          <div key={p.player_id} className={`player-row ${active ? 'active' : ''}`}
            style={{ '--pc': PLAYER_COLORS[p.player_id] }}>
            <HeroPortrait hero={hero} size={34} dim={!hero || hero === 'None'} />
            <div className="player-main">
              <div><b style={{ color: PLAYER_COLORS[p.player_id] }}>{p.player_id}</b> <span className="muted">{labels[p.player_id]}</span></div>
              <div className="muted small-text">{hero && hero !== 'None' ? heroName(hero) : 'bez boga'}</div>
            </div>
            <div className="res" title="monety"><ResourceIcon kind="coins" />{p.coins}</div>
            <div className="res" title="filozofowie"><ResourceIcon kind="philosophers" />{p.philosophers}</div>
            <div className="res" title="kapłani"><ResourceIcon kind="priests" />{p.priests}</div>
            <div className="res" title="wyspy"><ResourceIcon kind="island" />{count(p.player_id, (f) => f.type === 'island')}</div>
            <div className="res" title="metropolie"><ResourceIcon kind="metro" />{count(p.player_id, (f) => f.is_metropolis)}</div>
          </div>
        )
      })}
    </div>
  )
}
