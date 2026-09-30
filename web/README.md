# Cyklady — wersja webowa

Przeglądarkowa nakładka na silnik headless z [`engine/`](../engine).
Stary kod (`game/`, pygame) zostaje nietknięty.

```
web/
  backend/   FastAPI — cienki adapter: HTTP -> GameEngine (zero reguł gry)
  frontend/  React + Vite — plansza SVG, licytacja, akcje, log
```

Zasada: **cała logika gry siedzi w `engine/`**. Backend trzyma `GameState` i woła
`legal_actions` / `step`; frontend rysuje stan i wysyła akcję wybraną z `legal_actions`.

## Uruchomienie (dev)

```bash
# 1. backend (z katalogu głównego repo)
python3 -m venv web/backend/.venv
web/backend/.venv/bin/pip install -r web/backend/requirements.txt
web/backend/.venv/bin/python -m uvicorn web.backend.main:app --reload --port 8000

# 2. frontend (drugi terminal)
cd web/frontend && npm install && npm run dev
# -> http://localhost:5173  (Vite proxuje /api na :8000)
```

Wersja „jeden port”: `cd web/frontend && npm run build`, potem sam backend
serwuje `web/frontend/dist` pod http://localhost:8000.

## Gra przeciw LLM

Na ekranie startowym gracz typu **LLM** ma wybór dostawcy, modelu i trybu
(`guided` — model wybiera numer z listy legalnych akcji; `free_form` — sam proponuje akcję).
Kropka ● przy dostawcy = gotowy, ○ = brak pakietu albo klucza (powód pod listą).

```bash
cp .env.example .env                                   # wpisz klucze
web/backend/.venv/bin/pip install anthropic            # i/lub: openai, google-generativeai
```

| Dostawca | Pakiet | Klucz w `.env` |
|---|---|---|
| anthropic | `anthropic` | `ANTHROPIC_API_KEY` |
| openai | `openai` | `OPENAI_API_KEY` |
| gemini | `google-generativeai` | `GOOGLE_API_KEY` |
| ollama | `openai` | brak — działający `ollama serve` (`OLLAMA_HOST`) |

W logu partii przy ruchach LLM widać tokeny, nietrafione odpowiedzi, fallback
i **uzasadnienie modelu** — to samo trafia do `runs/{game_id}.jsonl` (pole `detail`).
Błąd API dostawcy (limit, sieć) zwraca 502 i pauzuje pętlę AI — kliknięcie błędu wznawia.

## API

| Metoda | Ścieżka | Opis |
|---|---|---|
| POST | `/api/game/new` | `{num_players, seed?, agents: {p2: {kind: "mcts", n_simulations: 50}}}` — brak wpisu = człowiek |
| GET | `/api/game/{id}` | aktualny `GameView` |
| POST | `/api/game/{id}/step` | `{action: <dict z legal_actions>}` — ruch człowieka, 409 gdy akcja nieaktualna |
| POST | `/api/game/{id}/ai-step` | jeden ruch AI dla aktywnego gracza |
| GET | `/api/llm/providers` | którzy dostawcy LLM są gotowi (bez płatnych wywołań) |
| GET | `/api/board/layout` | komórki siatki zajmowane przez wyspy (prezentacja) |

Każdy krok dopisywany jest do `web/backend/runs/{game_id}.jsonl` (replay partii).

## Testy

```bash
web/backend/.venv/bin/pip install pytest httpx
web/backend/.venv/bin/python -m pytest web/backend/tests
```

`test_http_matches_engine` gra całą partię random-vs-random przez HTTP i porównuje
wynik z grą bezpośrednio na silniku (ten sam seed) — dowód, że adapter nie zmienia zasad.

## Grafiki

Wszystkie grafiki są nowe, rysowane w SVG (`frontend/src/components/icons.jsx`):
medaliony bogów (Ares, Posejdon, Atena, Zeus, Apollon), wojownik, statek, budynki
każdego boga, metropolia, monety/zasoby. Plansza to siatka 91 heksów
(`frontend/src/data/geometry.js`) — pola wodne z silnika + wyspy z layoutu,
obrys wyspy w kolorze właściciela.
