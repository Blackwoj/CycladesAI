# CycladesAI — Plan pracy magisterskiej

## Co zostało zrobione

| Faza | Zakres | Status | Pliki |
|------|--------|--------|-------|
| 1 | `GameState` + `clone()` + `to_dict/from_dict`, typy `Action`, interfejs `Agent`, szkielet `GameEngine`, `CardRegistry` | ✅ | `engine/state/`, `engine/actions/`, `engine/cards/`, `engine/engine.py` |
| 2 | Port reguł (ROLL/BOARD), `legal_actions()`, `step()`, plansza JSON, scoring, graf ruchu | ✅ | `engine/rules/`, `engine/engine.py` |
| 3 | `ExperimentRunner` — headless batch, metryki (win rate, illegal moves, truncation) | ✅ | `engine/experiment/runner.py`, `engine/tests/test_experiment.py` |
| 4 | `LLMAgent` multi-provider + Pydantic schematy per-bóg + system prompt z zasadami gry | ✅ | `engine/agents/llm_agent.py`, `engine/agents/llm_schemas.py` |
| 5 | `MCTSAgent` — UCB1, losowe rollouty, determinizacja walki, `time_budget_ms` | ✅ | `engine/agents/mcts_agent.py`, `engine/tests/test_mcts.py` |
| 6 | `ConsoleHumanAgent` + interaktywna gra człowiek vs AI | ✅ | `engine/agents/human_agent.py`, `engine/experiments/play.py` |

**Testy**: 65 passed (59 bez MCTS + 6 MCTS) przy `python3 -m pytest engine/tests/`.

---

## Co jeszcze do zrobienia

### Priorytet wysoki (potrzebne do eksperymentów w pracy mgr)

#### A. Plansza dla 2–4 graczy
- **Problem**: silnik używa planszy 5-osobowej dla wszystkich konfiguracji (brak plansz 2–4 w `game/gui/common/config_section/boards/`). W grach 2-osobowych ~70% gier jest truncated przy max_steps=800 bo plansza jest za duża i gra trwa zbyt długo.
- **Do zrobienia**: stworzyć lub zaimportować mniejsze plansze JSON dla 2, 3, 4 graczy albo przyciąć istniejącą planszę 5-osobową do podzbioru wysp/wód odpowiedniego dla mniejszej liczby graczy.
- **Pliki**: `engine/rules/setup.py` → `load_board_data()`, `_BOARDS_DIR`

#### B. Uruchomienie eksperymentów porównawczych z prawdziwymi LLM
- Uzupełnić klucze w `.env` (skopiować z `.env.example`)
- Odkomentować sekcję LLM w `engine/experiments/compare.py`
- Uruchomić: `python3 engine/experiments/compare.py`
- Przeanalizować wyniki z `engine/experiments/results/`
- **Modele do przetestowania**: `claude-haiku-4-5` (Anthropic), `gpt-4o-mini` (OpenAI), lokalny Llama przez Ollama, Gemini Flash

#### C. Metryki rozszerzone dla pracy mgr
- W `LLMStats` zbierane są `tokens_used`, `decision_ms`, `illegal_count` — dodać eksport do CSV/JSON
- Porównanie trybu GUIDED vs FREE_FORM (ile nielegalnych akcji generuje FREE_FORM?)
- W `MCTSAgent` zbierać: średnia głębokość drzewa, współczynnik eksploracji, czas rolloutów
- Skrypt analizy wyników: `engine/experiments/analyze.py`

### Priorytet średni (opcjonalne rozszerzenia)

#### D. Walka z prawdziwymi kośćmi (losowość)
- Obecna implementacja: `attacker vs defender = N vs M → deterministyczny wynik` (więcej jednostek wygrywa, remis → obrońca)
- Oryginalna gra: rzuty kośćmi — każda jednostka rzuca k6, ile wyrzuci >3 = ile trafia
- MCTS już obsługuje losowość przez `determinizację` (Rng w `rollout_rng`)
- Do zrobienia: dodać opcję `combat_dice=True` w `GameEngine.__init__` i obsłużyć w `engine/rules/board.py → _apply_move_entity()`

#### E. Faza 7 — Karty specjalne
- Szew już w miejscu: `engine/cards/card.py` (`CardRegistry`), akcja `PlayCard` zdefiniowana
- Do zrobienia: zaimplementować kilka przykładowych kart (np. Posejdon daje darmowy ruch statku)
- Wartość dla pracy mgr: sprawdzić czy LLM radzi sobie z nowym typem akcji bez przetrening

#### F. Faza 8 — FastAPI serwer (opcjonalne)
- Stan jest serializowalny (`to_dict/from_dict`), brak globali → gotowe do opakowania
- Prosty serwer: `POST /game/new`, `GET /game/{id}/state`, `POST /game/{id}/step`
- Umożliwia grę przez przeglądarkę lub zewnętrznych agentów przez HTTP

#### G. Podpięcie pygame GUI
- `HumanAgent` działa przez konsolę; pygame GUI wymaga adaptacji
- `DataCache` w starym kodzie = odpowiednik `GameState` — można stworzyć adapter `DataCacheBridge`
- Niski priorytet dla pracy mgr (GUI nie jest mierzony)

---

## Szybki start na nowej maszynie

```bash
git clone <repo-url>
cd CycladesAI

# Zależności
pip install pydantic python-dotenv pytest

# Opcjonalnie — agenci LLM:
pip install anthropic          # Claude
pip install openai             # GPT / Qwen / MiniMax / Ollama
pip install google-generativeai  # Gemini

# Klucze API
cp .env.example .env
# edytuj .env i wpisz klucze

# Testy
python3 -m pytest engine/tests/ -v

# Eksperymenty porównawcze (Random vs MCTS)
python3 engine/experiments/compare.py

# Gra interaktywna (człowiek vs MCTS)
python3 engine/experiments/play.py

# Gra interaktywna (człowiek vs Claude)
python3 engine/experiments/play.py --llm
```

---

## Architektura silnika

```
engine/
  engine.py          GameEngine — legal_actions / step / state_view
  rng.py             Seedowalny RNG (reprodukcja wyników)
  state/             GameState + typy (Field, Player, Entity, ...)
  actions/           Typy akcji (RollBid, PlaceEntity, MoveEntity, ...)
  rules/             Mechanika gry (roll.py, board.py, scoring.py, graph.py)
  cards/             CardRegistry — szew pod karty specjalne
  agents/
    random_agent.py  Baseline losowy
    mcts_agent.py    MCTS (UCB1, determinizacja)
    llm_agent.py     LLMAgent — Anthropic / OpenAI / Gemini / Ollama
    llm_schemas.py   Pydantic per-hero schemas
    human_agent.py   ConsoleHumanAgent
  experiment/
    runner.py        ExperimentRunner — batch headless
  experiments/
    compare.py       Skrypt porównawczy agentów → JSONL
    play.py          Interaktywna gra człowiek vs AI
  tests/             65 testów
```

---

## Kluczowe decyzje architektoniczne

- **Strangler fig**: nowy `engine/` obok `game/` (pygame) — stary kod nienaruszony
- **FastAPI odrzucone** tymczasowo — eksperymenty batch lokalnie wystarczą
- **LLM providers**: każdy w osobnej podklasie; OpenAI SDK pokrywa też Qwen/MiniMax/Ollama
- **MCTS + losowość**: determinizacja — Rng losuje wyniki walki w każdym rolloucie
- **Pydantic schematy**: per-bóg discriminated unions → zero ręcznego parsowania JSON z LLM
- **5-player board dla wszystkich**: znany dług techniczny — naprawić w punkcie A powyżej
