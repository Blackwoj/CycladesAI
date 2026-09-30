import { useEffect, useState } from 'react'
import { api } from './api'
import SetupView from './views/SetupView'
import BoardView from './views/BoardView'

const SAVED = 'cyklady.game_id'

export default function App() {
  const [game, setGame] = useState(null)   // GameView — jedyne źródło prawdy
  const [booting, setBooting] = useState(true)

  // po odświeżeniu strony wróć do trwającej partii (jeśli serwer jej nie zgubił)
  useEffect(() => {
    let id = null
    try { id = localStorage.getItem(SAVED) } catch { /* brak storage */ }
    if (!id) { setBooting(false); return }
    api.getGame(id).then(setGame).catch(() => forget()).finally(() => setBooting(false))
  }, [])

  const start = (view) => {
    try { localStorage.setItem(SAVED, view.game_id) } catch { /* ignore */ }
    setGame(view)
  }
  const forget = () => {
    try { localStorage.removeItem(SAVED) } catch { /* ignore */ }
    setGame(null)
  }

  if (booting) return null
  return game
    ? <BoardView game={game} setGame={setGame} onExit={forget} />
    : <SetupView onStart={start} />
}
