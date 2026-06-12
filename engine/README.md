# CycladesAI — silnik gry (headless)

Czysty, bezstanowy globalnie silnik gry Cyclades, **niezależny od pygame**.
Powstaje jako green-field obok istniejącego kodu w [`game/`](../game). Stary kod
(pygame + `DataCache`) zostaje nietknięty i działa, dopóki silnik nie będzie gotowy
do podpięcia.

## Po co osobny silnik?

Praca magisterska: testowanie **planowania strategii długoterminowej przez modele LLM**,
porównanie z MCTS i RandomAgent. To wymaga rzeczy, których stara architektura nie daje:

- **klonowalny stan** (`GameState.clone()`) — MCTS robi tysiące symulacji na kopiach;
- **brak globalnego stanu** — można grać wiele gier naraz (batch, eksperymenty headless);
- **jawne akcje + walidacja** — `legal_actions()` / `step()` zamiast drag&drop;
- **serializacja** (`to_dict`/`from_dict`) — logowanie przebiegów, reprodukcja, FastAPI;
- **czytelny stan dla LLM** — projekcja stanu + Pydantic schematy per-bóg.

## Architektura

```
KONSUMENCI:  pygame GUI  ·  ExperimentRunner (batch)  ·  [opcj.] FastAPI
                              │ tylko przez API silnika + Agent
Agent:       choose(state_view, legal_actions) -> Action
             RandomAgent · LLMAgent · MCTSAgent  [· HumanAgent — Faza 6]
                              │
GameEngine:  legal_actions(state)  /  step(state, action)  /  state_view(state, player)
             rules/   — mechanika (roll, board, combat, scoring)
             cards/   — CardRegistry (szew Fazy 7)
GameState:   dataclass · clone() · to_dict()/from_dict()
Action:      typy akcji (RollBid, PlaceEntity, MoveEntity, Build, BuyCard, PlayCard, EndTurn)
```

## Struktura folderów

```
engine/
  README.md
  rng.py               seedowalny RNG (reprodukcja + chance-nodes MCTS)
  engine.py            GameEngine — główne API
  state/               GameState + wszystkie typy stanu
  actions/             typy Action + action_from_dict
  rules/               mechanika: roll.py / board.py / scoring.py / setup.py / graph.py
  cards/               CardRegistry + protokół Card (szew)
  agents/
    base.py            interfejs Agent (ABC)
    random_agent.py    baseline losowy
    llm_agent.py       LLMAgent multi-provider:
                         AnthropicLLMAgent (claude-*)
                         OpenAILLMAgent    (gpt-*, qwen-*, minimax, ...)
                         OllamaLLMAgent    (llama3.2, mistral, ...)
                         GeminiLLMAgent    (gemini-*)
    llm_schemas.py     Pydantic schematy per-bóg (walidacja wyjścia LLM)
    mcts_agent.py      MCTSAgent (UCB1 + determinizacja)
  experiment/
    runner.py          ExperimentRunner (batch headless) + metryki
  tests/               59 testów (unit + integracyjne)
```

## Status faz

| Faza | Zakres | Status |
|------|--------|--------|
| 1 | GameState, typy Action, interfejs Agent, GameEngine szkielet | ✅ GOTOWE |
| 2 | Port reguł (ROLL/BOARD), legal_actions(), step(), planszaJSON, scoring | ✅ GOTOWE |
| 3 | ExperimentRunner (batch headless) + metryki + testy | ✅ GOTOWE |
| 4 | LLMAgent multi-provider + Pydantic schematy per-bóg + system prompt + .env | ✅ GOTOWE |
| 5 | MCTSAgent (UCB1, determinizacja, time budget) | ✅ GOTOWE |
| 6 | HumanAgent / podpięcie pygame jako wizualizera | TODO |
| 7 (opcj.) | Moduł kart specjalnych (CardRegistry szew już w miejscu) | TODO |
| 8 (opcj.) | FastAPI serwer | TODO |

## Szybki start

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom eksperymenty porównawcze (Random vs MCTS)
python3 engine/experiments/compare.py

# Testy
python3 -m pytest engine/tests/ -v
```

## Klucze API dla LLM

```bash
cp .env.example .env
# edytuj .env i wpisz klucze
```

Następnie w eksperymencie:
```python
from dotenv import load_dotenv; load_dotenv()
from engine.agents import AnthropicLLMAgent
agent = AnthropicLLMAgent(model="claude-haiku-4-5")
```

## Przykład — porównanie agentów

```python
from engine.experiment.runner import ExperimentRunner, ExperimentConfig
from engine.agents import RandomAgent, MCTSAgent
from engine.rng import Rng

config = ExperimentConfig(
    num_games=50,
    num_players=2,
    agents={
        "p1": MCTSAgent(n_simulations=200),
        "p2": RandomAgent(Rng(2)),
    },
    seed=42,
)
results = ExperimentRunner(config).run()
print(results.summary())
```
