import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import Board from '../components/Board'
import RollPanel from '../components/RollPanel'
import ActionPanel, { fieldActions } from '../components/ActionPanel'
import PlayersPanel from '../components/PlayersPanel'
import CreaturePanel from '../components/CreaturePanel'
import PendingPanel, { actionFields } from '../components/PendingPanel'
import GameLog from '../components/GameLog'
import { HeroPortrait } from '../components/icons'
import { PLAYER_COLORS, heroName } from '../data/labels'

const STAGES = { roll: 'Licytacja', board: 'Plansza', game_over: 'Koniec gry', setup: 'Przygotowanie' }

export default function BoardView({ game, setGame, onExit }) {
  const [islands, setIslands] = useState(null)
  const [selected, setSelected] = useState(null)
  const [moveFrom, setMoveFrom] = useState(null)
  const [pendingMove, setPendingMove] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [paused, setPaused] = useState(false)
  const [delay, setDelay] = useState(500)

  useEffect(() => { api.layout().then((l) => setIslands(l.islands)).catch((e) => setError(e.message)) }, [])

  const { state, legal_actions: legal, act_player: act, terminal } = game
  const human = game.act_player_is_human && !terminal
  const hero = state.act_hero
  const pending = state.board?.pending

  const clearSelection = () => { setSelected(null); setMoveFrom(null); setPendingMove(null) }

  const apply = async (fn) => {
    setBusy(true); setError(null)
    try {
      setGame(await fn())
      clearSelection()
    } catch (e) {
      setError(e.message)
      if (e.status === 409) api.getGame(game.game_id).then(setGame).catch(() => {})
      if (e.status === 404) onExit()
    } finally {
      setBusy(false)
    }
  }
  const doAction = (a) => apply(() => api.step(game.game_id, a))

  // pętla AI żyje w kliencie: po każdym stanie, jeśli rusza się AI — poproś o jej krok
  useEffect(() => {
    if (terminal || human || !act || paused || busy || error) return
    const t = setTimeout(() => apply(() => api.aiStep(game.game_id)), delay)
    return () => clearTimeout(t)
  }, [game, paused, busy, delay, error]) // eslint-disable-line react-hooks/exhaustive-deps

  // podświetlenia pól = rzut legal_actions (bez żadnej reguły gry po stronie klienta)
  const { highlight, targets } = useMemo(() => {
    if (!human || game.stage !== 'board') return { highlight: new Set(), targets: new Set() }
    if (pending) {
      return { highlight: new Set(legal.flatMap(actionFields).filter((f) => state.fields[f])), targets: new Set() }
    }
    if (moveFrom) {
      return {
        highlight: new Set(),
        targets: new Set(legal.filter((a) => a.type === 'move_entity' && a.from_field === moveFrom).map((a) => a.to_field)),
      }
    }
    return {
      highlight: new Set(legal.flatMap((a) => a.type === 'move_entity' ? [a.from_field] : a.field_id ? [a.field_id] : [])),
      targets: new Set(),
    }
  }, [legal, moveFrom, human, game.stage, pending, state.fields])

  const onFieldClick = (id) => {
    if (busy) return
    if (pending) { setSelected(highlight.has(id) ? id : null); return }
    if (moveFrom) {
      if (targets.has(id)) {
        const options = legal.filter((a) => a.type === 'move_entity' && a.from_field === moveFrom && a.to_field === id)
        if (options.length === 1) doAction(options[0])
        else setPendingMove({ from: moveFrom, to: id, options })
      } else clearSelection()
      return
    }
    if (!highlight.has(id)) { clearSelection(); return }
    const acts = fieldActions(legal, id)
    const moves = acts.filter((a) => a.type === 'move_entity' && a.from_field === id)
    // jedyna możliwość = ruch stąd -> od razu tryb wyboru celu
    if (moves.length && moves.length === acts.length) { setSelected(id); setMoveFrom(id); return }
    setSelected(id); setMoveFrom(null); setPendingMove(null)
  }

  const stuck = human && !legal.length

  return (
    <div className="game">
      <header className="topbar">
        <b className="brand">Cyklady</b>
        <span>Runda <b>{state.round_no}</b></span>
        <span>{STAGES[game.stage] ?? game.stage}</span>
        <span className="muted">do wygranej: {state.options?.metros_to_win ?? 2} metropolie{state.options?.combat_dice ? ' · kości' : ''}</span>
        <span className="muted">seed {game.seed} · krok {game.step}</span>
        <span className="spacer" />
        <label className="inline muted">tempo AI
          <input type="range" min="0" max="1500" step="100" value={1500 - delay}
            onChange={(e) => setDelay(1500 - Number(e.target.value))} />
        </label>
        <button className="btn small" onClick={() => setPaused((p) => !p)}>{paused ? 'Wznów AI' : 'Pauza AI'}</button>
        <button className="btn small ghost" onClick={onExit}>Nowa gra</button>
      </header>

      <main className="layout">
        <section className="board-wrap">
          {islands
            ? <Board fields={state.fields} islands={islands} figures={state.cards?.figures} highlight={highlight} targets={targets}
                selected={selected} onFieldClick={onFieldClick} />
            : <div className="muted">Ładowanie planszy…</div>}
        </section>

        <aside className="sidebar">
          <div className="turn" style={{ '--pc': PLAYER_COLORS[act] ?? '#888' }}>
            {hero && hero !== 'None' && game.stage === 'board' && <HeroPortrait hero={hero} size={40} />}
            <div>
              {terminal ? <b>Koniec gry</b>
                : act ? <><b style={{ color: PLAYER_COLORS[act] }}>{act}</b> · {game.players[act]}
                  {game.stage === 'board' && hero && <> · {heroName(hero)}</>}</>
                  : 'Czekanie…'}
              {!terminal && !human && act && <div className="muted small-text">{paused ? 'AI wstrzymane' : busy ? 'AI myśli…' : 'AI zaraz się ruszy'}</div>}
            </div>
            {busy && <span className="spinner" />}
          </div>

          {error && <div className="error" onClick={() => setError(null)}>{error} <span className="muted">(kliknij, by ukryć i wznowić)</span></div>}
          {stuck && <div className="error">Brak legalnych akcji — silnik czeka.</div>}

          {human && game.stage === 'roll' && <RollPanel state={state} legal={legal} onAction={doAction} disabled={busy} />}
          {human && game.stage === 'board' && pending && (
            <PendingPanel pending={pending} legal={legal} selected={selected} onAction={doAction}
              onClear={() => setSelected(null)} disabled={busy} />
          )}
          {human && game.stage === 'board' && !pending && (
            <ActionPanel legal={legal} selected={selected} moveFrom={moveFrom} pendingMove={pendingMove}
              onAction={doAction} onStartMove={(id) => { setMoveFrom(id); setPendingMove(null) }}
              onCancel={clearSelection} disabled={busy} />
          )}
          {!human && game.stage === 'roll' && <RollPanel state={state} legal={[]} onAction={() => {}} disabled />}

          {state.options?.creatures !== false && (
            <CreaturePanel cards={state.cards} legal={human && !pending ? legal : []} onAction={doAction} disabled={busy} />
          )}
          <PlayersPanel state={state} labels={game.players} actPlayer={act} />
          <GameLog log={game.log} />
        </aside>
      </main>

      {terminal && (
        <div className="overlay">
          <div className="panel overlay-card">
            <h2>{game.winners.length ? 'Zwycięstwo!' : 'Koniec gry'}</h2>
            {game.winners.map((w) => (
              <p key={w}><b style={{ color: PLAYER_COLORS[w] }}>{w}</b> ({game.players[w]}) ma {state.options?.metros_to_win ?? 2} metropolie.</p>
            ))}
            <p className="muted">Partia: seed {game.seed}, {game.step} kroków, {state.round_no} rund.</p>
            <button className="btn primary" onClick={onExit}>Nowa gra</button>
          </div>
        </div>
      )}
    </div>
  )
}
