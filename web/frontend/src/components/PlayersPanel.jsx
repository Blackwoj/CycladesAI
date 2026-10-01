import { PLAYER_COLORS, heroName } from '../data/labels'
import { HeroPortrait, ResourceIcon } from './icons'

export default function PlayersPanel({ state, labels, actPlayer }) {
  const count = (pid, pred) => Object.values(state.fields).filter((f) => f.owner === pid && pred(f)).length
  return (
    <div className="panel players">
      {Object.values(state.players).map((p) => {
        const heroes = state.round_heroes?.[p.player_id]?.length ? state.round_heroes[p.player_id]
          : [state.hero_players[p.player_id]].filter((h) => h && h !== 'None')
        const hero = heroes[0]
        const active = p.player_id === actPlayer
        return (
          <div key={p.player_id} className={`player-row ${active ? 'active' : ''}`}
            style={{ '--pc': PLAYER_COLORS[p.player_id] }}>
            <div className="portraits">
              {heroes.length ? heroes.map((h, i) => <HeroPortrait key={i} hero={h} size={heroes.length > 1 ? 26 : 34} />)
                : <HeroPortrait hero={null} size={34} dim />}
            </div>
            <div className="player-main">
              <div><b style={{ color: PLAYER_COLORS[p.player_id] }}>{p.player_id}</b> <span className="muted">{labels[p.player_id]}</span></div>
              <div className="muted small-text">{heroes.length ? heroes.map(heroName).join(' + ') : 'bez boga'}</div>
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
