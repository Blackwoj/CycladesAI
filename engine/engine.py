"""GameEngine — fasada reguł gry.

Czyste API dla wszystkich konsumentów (pygame, batch, MCTS, FastAPI):

    engine = GameEngine(rng=Rng(42))
    state = engine.new_game(num_players=3)
    legal = engine.legal_actions(state)
    state, info = engine.step(state, action)

Silnik nie trzyma stanu gry w sobie — stan jest jawny i przekazywany.
"""
from __future__ import annotations

from .actions import Action, EndTurn
from .cards import CardRegistry, CARDS
from .rng import Rng
from .rules.board import apply_board_action, legal_board_actions, start_player_turn
from .rules.roll import apply_roll_bid, apply_apollon_bid, legal_roll_actions
from .rules.scoring import end_board_phase, is_game_over, start_cycle
from .rules.setup import build_initial_state
from .state import GameOptions, GameState, Player, Stage


class GameEngine:
    def __init__(
        self,
        rng: Rng | None = None,
        cards: CardRegistry | None = None,
        options: GameOptions | None = None,
    ):
        self._rng = rng or Rng()
        self._cards = cards or CARDS
        self._options = options or GameOptions()

    # ---- tworzenie gry -------------------------------------------------

    def new_game(
        self, num_players: int, rng: Rng | None = None, options: GameOptions | None = None,
    ) -> GameState:
        """Zbuduj stan początkowy i rozpocznij cykl 1 (tor Stworów, bogowie, dochód)."""
        r = rng or self._rng.spawn()
        state = build_initial_state(num_players, r, options or self._options)
        return start_cycle(state, r)

    # ---- rdzeń API -------------------------------------------------------

    def legal_actions(self, state: GameState) -> list[Action]:
        """Lista legalnych akcji dla act_player w bieżącym etapie."""
        if state.stage == Stage.ROLL:
            return legal_roll_actions(state)
        if state.stage == Stage.BOARD:
            if state.act_player is None:
                # Między turami — silnik powinien wywołać start_player_turn
                return []
            return legal_board_actions(state)
        return []

    def step(self, state: GameState, action: Action) -> tuple[GameState, dict]:
        """Zastosuj akcję. Zwraca (nowy_stan, info). Nie mutuje wejścia."""
        if is_game_over(state):
            return state, {"error": "gra skończona"}

        if state.stage == Stage.ROLL:
            return self._step_roll(state, action)
        if state.stage == Stage.BOARD:
            return self._step_board(state, action)
        return state, {"error": f"nieznany etap: {state.stage}"}

    # ---- etap ROLL -------------------------------------------------------

    def _step_roll(self, state: GameState, action: Action) -> tuple[GameState, dict]:
        from .actions import RollBid, ApollonBid
        if isinstance(action, RollBid):
            new_state = apply_roll_bid(state, action)
            if new_state.stage == Stage.BOARD:
                new_state = self._begin_board_phase(new_state)
            return new_state, {"valid": True}
        if isinstance(action, ApollonBid):
            new_state = apply_apollon_bid(state, action)
            if new_state.stage == Stage.BOARD:
                new_state = self._begin_board_phase(new_state)
            return new_state, {"valid": True}
        return state, {"valid": False, "error": f"niedozwolona akcja w fazie ROLL: {type(action).__name__}"}

    def _begin_board_phase(self, state: GameState) -> GameState:
        """Po zakończeniu ROLL startuj turę pierwszego gracza z play_order."""
        return start_player_turn(state)

    # ---- etap BOARD ------------------------------------------------------

    def _step_board(self, state: GameState, action: Action) -> tuple[GameState, dict]:
        new_state, info = apply_board_action(state, action, self._rng)

        if not info.get("valid", False):
            return state, info   # nielegalny ruch — zwracamy STARY stan

        if isinstance(action, EndTurn):
            if new_state.play_order:
                new_state = start_player_turn(new_state)
            else:
                # Koniec cyklu — tu (i tylko tu) rozstrzyga się zwycięstwo
                new_state = end_board_phase(new_state, self._rng)
                if new_state.winners:
                    info["winners"] = list(new_state.winners)

        return new_state, info

    # ---- zakończenie / wynik ---------------------------------------------

    def is_terminal(self, state: GameState) -> bool:
        return is_game_over(state)

    def winner(self, state: GameState) -> list[str]:
        """Zwycięzcy ustaleni na koniec cyklu ([] dopóki gra trwa)."""
        return list(state.winners)

    # ---- projekcja dla agenta --------------------------------------------

    def state_view(self, state: GameState, player: str) -> dict:
        """Widok stanu z perspektywy gracza — to dostaje Agent.

        Dla LLMAgent ten dict jest podstawą promptu.
        Gdy dojdzie ukryta informacja (karty), tu ją zamaskujemy.

        Klucze z podkreśleniem (_state, _engine) są wewnętrzne:
        MCTSAgent używa ich do symulacji; FastAPI/JSON ich nie serializuje.
        """
        view = state.to_dict()
        view["me"] = player
        view["legal_actions"] = [a.to_dict() for a in self.legal_actions(state)]
        view["_state"] = state      # GameState object — dla MCTSAgent
        view["_engine"] = self      # GameEngine object — dla MCTSAgent
        return view

    # ---- pomocnicze dla headless / eksperymentów -----------------------

    @staticmethod
    def new_game_static(num_players: int, rng: Rng | None = None) -> GameState:
        """Statyczna wersja new_game — do użycia bez instancji silnika."""
        engine = GameEngine(rng)
        return engine.new_game(num_players, rng)
