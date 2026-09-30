// Jedyne miejsce z adresem backendu. W dev Vite proxuje /api -> :8000.
const BASE = '/api'

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(data.detail ? String(data.detail) : `HTTP ${res.status}`)
    err.status = res.status
    throw err
  }
  return data
}

export const api = {
  newGame: (cfg) => request('POST', '/game/new', cfg),
  getGame: (id) => request('GET', `/game/${id}`),
  step: (id, action) => request('POST', `/game/${id}/step`, { action }),
  aiStep: (id) => request('POST', `/game/${id}/ai-step`),
  layout: () => request('GET', '/board/layout'),
  providers: () => request('GET', '/llm/providers'),
}
