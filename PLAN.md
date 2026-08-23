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
| 6.1 | Naprawa 4 błędów silnika wykrytych przy analizie punktu A (niżej) | ✅ | `engine/rules/board.py`, `engine/rules/setup.py`, `engine/tests/test_regressions.py` |

**Testy**: 74 passed (65 poprzednich + 9 regresyjnych) przy `python3 -m pytest engine/tests/`.

### Faza 6.1 — naprawione błędy

Wykryte przy pomiarach do punktu A. Każdy ma test regresyjny w
`engine/tests/test_regressions.py` (sprawdzone: 8 z 9 testów pada na kodzie sprzed napraw).

1. **Gubienie `entity.kind` przy opróżnieniu pola** — `_apply_move_entity()` czytało
   rodzaj jednostki z `from_f.entity` już PO wyzerowaniu pola, więc ruch wszystkich
   statków dawał na polu docelowym `kind=None`. Kolejny ruch tych statków szedł
   ścieżką kosztu wojownika i bywał odrzucany.
2. **Wojownicy na otwartym morzu** — generator Aresa iterował po wszystkich polach,
   a `can_warrior_reach()` dopuszczał dowolne pole sąsiednie. W 10 partiach 127 ruchów
   wojowników na wodę, do 16 zajętych pól wodnych naraz. Teraz cel musi być wyspą;
   ścieżka DFS przez własną wodę (most ze statków) pozostaje dozwolona.
3. **Brak reprodukowalności między procesami** — kolejność `legal_actions()` zależała
   od iteracji po `set`, czyli od `PYTHONHASHSEED`. Ten sam seed dawał w dwóch procesach
   różne przebiegi gry. Po dodaniu `sorted()` wynik jest identyczny także dla
   `PYTHONHASHSEED=random`.
4. **Gracze-widma przy 2–4 graczach** — patrz punkt A niżej.

**Efekt łączny**: `step()` nie odrzuca już ani jednej akcji zwróconej przez
`legal_actions()` (wcześniej 6,0% kroków). To ważne dla punktu C: metryka
`illegal_count` mierzy teraz wyłącznie agenta, a nie szum silnika.

---

## Co jeszcze do zrobienia

### Priorytet wysoki (potrzebne do eksperymentów w pracy mgr)

#### A. Plansza dla 2–4 graczy — ZAMKNIĘTE (osobne plansze niepotrzebne)

**Sprostowanie do pierwotnego opisu**: liczba „~70% truncated przy max_steps=800" była
błędna — zapisane wyniki w `engine/experiments/results/random_vs_random.jsonl` mają
`"steps": 400`, więc 70% pochodzi z **max_steps=400**. Przy 800 truncation wynosiło 17%.

**Zrobione — gracze-widma (główna przyczyna)**: pliki JSON opisują rozstawienie dla
5 graczy i wczytywano je w całości niezależnie od `num_players`. W partii 2-osobowej
**15 z 22 zajętych pól (18 z 26 jednostek) należało do `p3`/`p4`/`p5`** — właścicieli
bez agenta, którzy nigdy się nie ruszali ani nie tracili jednostek, za to blokowali
ekspansję. `_parse_owner_entity()` przyjmuje teraz zbiór aktywnych graczy i zostawia
pozycje pozostałych neutralne. Układ pól i rozstawienie dla 5 graczy bez zmian.

Truncation dla 2 graczy, RandomAgent, `max_steps=400`, 30 partii:

| Wersja | truncated |
|---|---|
| zapisane wyniki (przed naprawami) | 70% |
| po naprawach błędów z Fazy 6.1 | 50% |
| po neutralizacji graczy-widm | **43%** |

**Rozstrzygnięte pomiarem: osobne plansze 2–4 NIE są potrzebne.** Truncation przy
`max_steps=800`, 2 graczy, po naprawach:

| Konfiguracja | truncated (przed, `max_steps=400`) | truncated (po, `max_steps=800`) |
|---|---|---|
| random vs random | 70% | **10%** (2/20) |
| MCTS vs random   | 60% | **10%** (1/10, sims=20) |
| MCTS vs MCTS     | 35% | **0%** (0/10, sims=20) |

Zbyt duża plansza nie była przyczyną — były nią gracze-widma i rozjazd
`legal_actions()`/`step()`. Im lepszy agent, tym mniej truncation: przy dwóch MCTS
partie kończą się w komplecie, średnio po 339 krokach. Przycinanie geometrii jest
więc zbędne i byłoby kosztowne — każda nowa plansza to komplet plików
`buildings_centers/`, `water_centers/`, `income_points/`, `warriors_points/`
plus współrzędne GUI.

Do rozważenia zamiast tego: `max_steps=800` jako standard w `compare.py` (już jest)
i raportowanie truncation jako metryki jakości agenta, nie wady planszy.

Koszt czasowy MCTS (sims=20, 2 gracze, do wykorzystania przy planowaniu przebiegów):
~500 ms/decyzję vs random, ~1260 ms/decyzję gdy obaj gracze to MCTS; partia MCTS vs
MCTS to ok. 7 minut.

- **Pliki**: `engine/rules/setup.py` → `load_board_data()`, `_parse_owner_entity()`, `_BOARDS_DIR`

#### B. Uruchomienie eksperymentów porównawczych z prawdziwymi LLM
- Uzupełnić klucze w `.env` (skopiować z `.env.example`)
- Odkomentować sekcję LLM w `engine/experiments/compare.py`
- Uruchomić: `python3 engine/experiments/compare.py`
- Przeanalizować wyniki z `engine/experiments/results/`
- **Uwaga: pliki w `results/` są nieaktualne** — powstały przed naprawami z Fazy 6.1,
  na silniku, który odrzucał 6% własnych legalnych akcji i stawiał na planszy graczy-widm.
  Trzeba je wygenerować od nowa, zanim posłużą za punkt odniesienia dla LLM
- **Modele do przetestowania**: `claude-haiku-4-5` (Anthropic), `gpt-4o-mini` (OpenAI), lokalny Llama przez Ollama, Gemini Flash

#### C. Metryki rozszerzone dla pracy mgr — ZROBIONE (czeka na dane z LLM)

Telemetria **per decyzja**, nie zbiorcza: `LLMStats`/`MCTSStats` trzymają tylko sumy,
z których nie da się zrobić wykresu (gubią rozkład w czasie).

- `engine/experiment/telemetry.py` — `DecisionRecord` (26 pól) + `DecisionTrace` (zapis
  strumieniowy do JSONL). Rekord łączy kontekst gry (runda, etap, heros), decyzję
  (`n_legal`, typ akcji, `decision_ms`), koszt LLM (tokeny wejścia/wyjścia,
  `illegal_attempts`, `fallback_used`), pracę MCTS (`simulations`, `tree_depth`)
  i stan gracza (monety, wyspy, metropolie, wojownicy, statki).
- Agenci wystawiają `last_decision`; agent bez telemetrii (`RandomAgent`) po prostu
  go nie ma i telemetria zwraca pusty dict — **żaden agent nie musi nic wiedzieć o zapisie**.
- `ExperimentConfig` ma `matchup` i `trace_path`; `compare.py` pisze do `results/traces/`.
- `engine/experiments/analyze.py` — CSV (`decisions.csv`, `per_matchup.csv`,
  `per_agent.csv`) + wykresy PNG. Bez `matplotlib` generuje same CSV.

Wykresy: rozstrzygalność partii, rozkład długości partii, koszt decyzji wg rodzaju
agenta (skala log), GUIDED vs FREE_FORM (nietrafione odpowiedzi + fallbacki), zużycie
tokenów wg rundy, wielkość przestrzeni decyzyjnej, struktura wybieranych akcji,
ekspansja terytorialna.

```bash
python3 engine/experiments/compare.py     # zapisuje results/*.jsonl + results/traces/*.jsonl
python3 engine/experiments/analyze.py     # CSV + PNG w results/analysis/
```

Katalog `results/analysis/` jest w `.gitignore` — w całości odtwarzalny z `traces/`.
Wykresy dotyczące LLM będą puste, dopóki nie ruszy punkt B (brak kluczy API).

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
- **5-player board dla wszystkich**: layout wspólny, ale rozstawienie startowe ograniczone
  do aktywnych graczy (Faza 6.1). Osobne plansze 2–4 — dopiero po pomiarze MCTS, patrz punkt A
- **Kolejność `legal_actions()` musi być deterministyczna**: bez tego seed nie wystarcza do
  reprodukcji. Nie iterować po `set` przy generowaniu akcji — zawsze `sorted()`
