"""Endpointy gry — bez ani jednej reguły Cyclades (FRONTEND.md §2).

Każda mutacja: dict akcji -> action_from_dict -> engine.step -> GameView.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from engine.actions import action_from_dict
from engine.agents.llm_factory import PROVIDERS, provider_available
from engine.experiment.telemetry import read_last_decision
from engine.rules.setup import load_board_data
from engine.state import GameOptions

from ..schemas import GameView, NewGameRequest, StepRequest
from ..store import LOG_TAIL, Game, store

router = APIRouter(prefix="/api", tags=["game"])


def _view(game: Game, info: dict | None = None) -> GameView:
    state = game.state
    engine = game.engine
    terminal = engine.is_terminal(state)
    act = state.act_player
    viewer = act or next(iter(state.players))
    # state_view wstrzykuje obiekty Pythona (_state, _engine) — wycinamy je tutaj, tylko tutaj
    view = {k: v for k, v in engine.state_view(state, viewer).items() if not k.startswith("_")}
    human = game.is_human(act)
    return GameView(
        game_id=game.game_id,
        seed=game.seed,
        step=game.step,
        state=view,
        legal_actions=view["legal_actions"] if (human and not terminal) else [],
        act_player=act,
        act_player_is_human=human,
        players=game.labels,
        stage=state.stage.value,
        terminal=terminal,
        winners=engine.winner(state),
        info=info or {},
        log=game.log[-LOG_TAIL:],
    )


def _get(game_id: str) -> Game:
    game = store.get(game_id)
    if game is None:
        raise HTTPException(404, "gra nie istnieje (restart serwera?)")
    return game


@router.post("/game/new", response_model=GameView, status_code=201)
def new_game(body: NewGameRequest):
    try:
        options = GameOptions(combat_dice=body.combat_dice, creatures=body.creatures)
        game = store.create(body.num_players, body.seed, body.agents, options)
    except ImportError as e:
        raise HTTPException(400, f"brak zależności agenta: {e}") from e
    except (ValueError, OSError) as e:   # OSError obejmuje EnvironmentError "Brak ..._API_KEY"
        raise HTTPException(400, str(e)) from e
    return _view(game)


@router.get("/game/{game_id}", response_model=GameView)
def get_game(game_id: str):
    return _view(_get(game_id))


@router.post("/game/{game_id}/step", response_model=GameView)
def step(game_id: str, body: StepRequest):
    game = _get(game_id)
    with game.lock:
        if not game.is_human(game.state.act_player):
            raise HTTPException(409, "teraz ruch AI")
        try:
            action = action_from_dict(body.action)
        except (KeyError, TypeError) as e:
            raise HTTPException(422, f"zły format akcji: {e}") from e
        # walidacja przez przynależność — pytamy silnik, nie duplikujemy reguł
        if action not in game.engine.legal_actions(game.state):
            raise HTTPException(409, "akcja nieaktualna — odśwież stan")
        info = game.apply(action)
        if info.get("valid") is False:
            raise HTTPException(409, info.get("reason") or info.get("error") or "ruch odrzucony")
        return _view(game, info)


@router.post("/game/{game_id}/ai-step", response_model=GameView)
def ai_step(game_id: str):
    game = _get(game_id)
    with game.lock:
        state = game.state
        if game.engine.is_terminal(state):
            raise HTTPException(409, "gra skończona")
        act = state.act_player
        if act is None or game.is_human(act):
            raise HTTPException(409, "teraz ruch człowieka")
        legal = game.engine.legal_actions(state)
        if not legal:
            raise HTTPException(409, "brak legalnych akcji")
        agent = game.agents[act]
        t0 = time.monotonic()
        try:
            action = agent.choose(game.engine.state_view(state, act), legal)
        except Exception as e:  # noqa: BLE001 — błąd API dostawcy LLM nie może zabić partii
            raise HTTPException(502, f"agent {game.labels[act]} zawiódł: {type(e).__name__}: {e}") from e
        ms = (time.monotonic() - t0) * 1000
        detail = read_last_decision(agent)
        info = game.apply(action, decision_ms=ms, detail=detail)
        return _view(game, {**info, "chosen_action": action.to_dict(), "decision_ms": ms})


@router.get("/llm/providers")
def llm_providers():
    """Którzy dostawcy LLM są gotowi (pakiet + klucz / serwer) — bez płatnych wywołań."""
    out = {}
    for name, (model, env_key, _, _) in PROVIDERS.items():
        ok, reason = provider_available(name)
        out[name] = {"default_model": model, "env_key": env_key, "available": ok, "reason": reason}
    return out


@router.get("/board/layout")
def board_layout(num_players: int = 5):
    """Dane prezentacyjne planszy: komórki siatki zajmowane przez wyspy (silnik ich nie trzyma)."""
    _, islands = load_board_data(num_players)
    return {
        "islands": {
            fid: {"location": cfg["location"], "slots": cfg["buildings"]["small"]}
            for fid, cfg in islands.items()
        }
    }
