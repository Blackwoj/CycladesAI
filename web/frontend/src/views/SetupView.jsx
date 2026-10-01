import { useEffect, useState } from 'react'
import { api } from '../api'
import { HEROES, PLAYER_COLORS } from '../data/labels'
import { HeroPortrait } from '../components/icons'

const KINDS = [
  { id: 'human', label: 'Człowiek' },
  { id: 'mcts', label: 'MCTS' },
  { id: 'random', label: 'Random' },
  { id: 'llm', label: 'LLM' },
]

const PROVIDERS = [
  { id: 'anthropic', label: 'Anthropic (Claude)' },
  { id: 'openai', label: 'OpenAI (GPT)' },
  { id: 'gemini', label: 'Google (Gemini)' },
  { id: 'ollama', label: 'Ollama (lokalnie)' },
]

const defaultSpec = (i) => (i === 0 ? { kind: 'human' } : { kind: 'mcts', n_simulations: 50 })

export default function SetupView({ onStart }) {
  const [num, setNum] = useState(2)
  const [seed, setSeed] = useState('')
  const [dice, setDice] = useState(false)
  const [creatures, setCreatures] = useState(true)
  const [specs, setSpecs] = useState(() => Array.from({ length: 5 }, (_, i) => defaultSpec(i)))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [providers, setProviders] = useState({})

  useEffect(() => { api.providers().then(setProviders).catch(() => {}) }, [])

  const setSpec = (i, patch) => setSpecs((s) => s.map((x, j) => (j === i ? { ...x, ...patch } : x)))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    const agents = Object.fromEntries(specs.slice(0, num).map((s, i) => [`p${i + 1}`, s]))
    try {
      onStart(await api.newGame({ num_players: num, seed: seed === '' ? null : Number(seed), agents,
        combat_dice: dice, creatures }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="setup">
      <div className="setup-hero">
        {['ares', 'posejdon', 'atena', 'zeus', 'apollon'].map((h) => <HeroPortrait key={h} hero={h} size={52} />)}
      </div>
      <h1>Cyklady</h1>
      <p className="muted">Zbuduj dwie metropolie, zanim zrobią to bogowie… albo MCTS.</p>

      <form className="panel setup-form" onSubmit={submit}>
        <label className="field">
          <span>Liczba graczy</span>
          <div className="seg">
            {[2, 3, 4, 5].map((n) => (
              <button type="button" key={n} className={n === num ? 'on' : ''} onClick={() => setNum(n)}>{n}</button>
            ))}
          </div>
        </label>

        {specs.slice(0, num).map((s, i) => (
          <div className="setup-player" key={i}>
            <span className="dot" style={{ background: PLAYER_COLORS[`p${i + 1}`] }} />
            <b>p{i + 1}</b>
            <select value={s.kind} onChange={(e) => setSpec(i, { kind: e.target.value })}>
              {KINDS.map((k) => <option key={k.id} value={k.id}>{k.label}</option>)}
            </select>
            {s.kind === 'mcts' && (
              <label className="inline">symulacji
                <input type="number" min="1" max="5000" value={s.n_simulations ?? 50}
                  onChange={(e) => setSpec(i, { n_simulations: Number(e.target.value) })} />
              </label>
            )}
            {s.kind === 'llm' && (() => {
              const prov = s.provider ?? 'anthropic'
              const info = providers[prov]
              return <div className="llm-spec">
                <select value={prov} onChange={(e) => setSpec(i, { provider: e.target.value, model: null })}>
                  {PROVIDERS.map((p) => (
                    <option key={p.id} value={p.id}>{providers[p.id]?.available ? '● ' : '○ '}{p.label}</option>
                  ))}
                </select>
                <input className="model" value={s.model ?? ''} placeholder={info?.default_model ?? 'model'}
                  onChange={(e) => setSpec(i, { model: e.target.value || null })} />
                <select value={s.mode ?? 'guided'} onChange={(e) => setSpec(i, { mode: e.target.value })}
                  title="guided: model wybiera numer z listy legalnych akcji · free_form: model sam proponuje akcję">
                  <option value="guided">guided</option>
                  <option value="free_form">free_form</option>
                </select>
                {info && !info.available && <div className="warn small-text">niedostępny: {info.reason}</div>}
              </div>
            })()}
          </div>
        ))}

        <label className="field">
          <span>Seed <span className="muted">(puste = losowy)</span></span>
          <input type="number" value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="np. 42" />
        </label>

        <div className="options">
          <label className="check"><input type="checkbox" checked={creatures} onChange={(e) => setCreatures(e.target.checked)} />
            Mitologiczne Stwory</label>
          <label className="check"><input type="checkbox" checked={dice} onChange={(e) => setDice(e.target.checked)} />
            Bitwy z kośćmi <span className="muted">(oryginał; bez — deterministyczne)</span></label>
        </div>

        {error && <div className="error">{error}</div>}
        <button className="btn primary big" disabled={busy}>{busy ? 'Tworzenie…' : 'Rozpocznij grę'}</button>
      </form>

      <div className="legend muted small-text">
        {Object.entries(HEROES).filter(([k]) => !['ap_s', 'metro'].includes(k)).map(([k, h]) => (
          <span key={k}><b style={{ color: h.color }}>{h.name}</b> — {h.desc}</span>
        ))}
      </div>
    </div>
  )
}
