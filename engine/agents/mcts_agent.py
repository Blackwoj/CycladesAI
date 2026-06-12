"""MCTSAgent — agent Monte Carlo Tree Search.

Używa clone() + step() + legal_actions() silnika do symulacji gier.
Losowość (combat, kolejność aukcji) obsługiwana przez determinizację —
przy każdym kroku symulacji silnik używa nowego Rng, co oznacza próbkowanie
losowego wyniku. MCTS uśrednia po wielu takich próbkach.

Metryki zbierane dla pracy magisterskiej:
  - avg_simulations_per_move   (ile symulacji na decyzję)
  - avg_decision_ms
  - avg_tree_depth             (średnia głębokość drzewa po selekcji)

Konfiguracja:
  n_simulations   — całkowita liczba iteracji MCTS na decyzję (domyślnie 200)
  time_budget_ms  — jeśli podane, symuluj tyle ms zamiast n_simulations
  max_rollout_depth — max głębokość rolloutu (ochrona przed nieskończoną grą)
  exploration_weight — stała C w UCB1 (domyślnie sqrt(2) ≈ 1.414)
  rollout_agent   — agent do rolloutów (domyślnie RandomAgent)
  player_id       — ID gracza; jeśli None, pobierane z state_view["me"]
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field as dc_field
from typing import TYPE_CHECKING

from ..actions import Action
from ..rng import Rng
from .base import Agent
from .random_agent import RandomAgent

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..state import GameState


# ---------------------------------------------------------------------------
# Metryki
# ---------------------------------------------------------------------------

@dataclass
class MCTSStats:
    total_decisions: int = 0
    total_simulations: int = 0
    total_decision_ms: float = 0.0
    total_tree_depth: float = 0.0

    def record(self, simulations: int, decision_ms: float, tree_depth: float) -> None:
        self.total_decisions += 1
        self.total_simulations += simulations
        self.total_decision_ms += decision_ms
        self.total_tree_depth += tree_depth

    def to_dict(self) -> dict:
        n = max(1, self.total_decisions)
        return {
            "total_decisions": self.total_decisions,
            "total_simulations": self.total_simulations,
            "avg_simulations_per_move": round(self.total_simulations / n, 1),
            "avg_decision_ms": round(self.total_decision_ms / n, 1),
            "avg_tree_depth": round(self.total_tree_depth / n, 2),
        }


# ---------------------------------------------------------------------------
# Węzeł drzewa
# ---------------------------------------------------------------------------

@dataclass
class MCTSNode:
    state: "GameState"
    action: Action | None                   # akcja która doprowadziła tu z rodzica
    parent: "MCTSNode | None"
    player: str                             # gracz podejmujący decyzję w tym węźle
    untried_actions: list[Action] = dc_field(default_factory=list)
    children: list["MCTSNode"] = dc_field(default_factory=list)
    visits: int = 0
    total_reward: float = 0.0

    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def ucb1(self, exploration: float) -> float:
        if self.visits == 0:
            return float("inf")
        exploitation = self.total_reward / self.visits
        parent_visits = self.parent.visits if self.parent else self.visits
        exploration_term = exploration * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration_term

    def best_child(self, exploration: float) -> "MCTSNode":
        return max(self.children, key=lambda c: c.ucb1(exploration))

    def best_action_child(self) -> "MCTSNode":
        """Wybierz dziecko z największą liczbą odwiedzin (po zakończeniu MCTS)."""
        return max(self.children, key=lambda c: c.visits)

    def depth(self) -> int:
        d = 0
        node = self
        while node.parent:
            d += 1
            node = node.parent
        return d


# ---------------------------------------------------------------------------
# Agent MCTS
# ---------------------------------------------------------------------------

class MCTSAgent(Agent):
    """Monte Carlo Tree Search agent.

    Wymaga, żeby state_view zawierał '_state' i '_engine' (ustawiane przez
    GameEngine.state_view). Jeśli brak — rzuca ValueError.
    """

    def __init__(
        self,
        n_simulations: int = 200,
        time_budget_ms: float | None = None,
        max_rollout_depth: int = 80,
        exploration_weight: float = math.sqrt(2),
        rollout_rng: Rng | None = None,
        player_id: str | None = None,
        verbose: bool = False,
    ) -> None:
        self.n_simulations = n_simulations
        self.time_budget_ms = time_budget_ms
        self.max_rollout_depth = max_rollout_depth
        self.exploration_weight = exploration_weight
        self._rollout_rng = rollout_rng or Rng()
        self._player_id = player_id
        self.verbose = verbose
        self.stats = MCTSStats()

    def choose(self, state_view: dict, legal_actions: list[Action]) -> Action:
        if not legal_actions:
            raise ValueError("MCTSAgent.choose: brak legalnych akcji")

        state: "GameState" = state_view.get("_state")
        engine: "GameEngine" = state_view.get("_engine")
        if state is None or engine is None:
            raise ValueError(
                "MCTSAgent wymaga '_state' i '_engine' w state_view. "
                "Sprawdź czy używasz GameEngine.state_view()."
            )

        player_id = self._player_id or state_view.get("me", state.act_player)
        t0 = time.monotonic()

        action, simulations, tree_depth = self._run_mcts(
            state, engine, legal_actions, player_id
        )

        elapsed_ms = (time.monotonic() - t0) * 1000
        self.stats.record(simulations, elapsed_ms, tree_depth)

        if self.verbose:
            print(
                f"[MCTSAgent] action={action} "
                f"sims={simulations} depth={tree_depth:.1f} time={elapsed_ms:.0f}ms"
            )
        return action

    def _run_mcts(
        self,
        root_state: "GameState",
        engine: "GameEngine",
        legal_actions: list[Action],
        player_id: str,
    ) -> tuple[Action, int, float]:
        """Uruchom MCTS. Zwróć (najlepsza_akcja, liczba_symulacji, średnia_głębokość)."""
        if len(legal_actions) == 1:
            return legal_actions[0], 0, 0.0

        root = MCTSNode(
            state=root_state,
            action=None,
            parent=None,
            player=player_id,
            untried_actions=list(legal_actions),
        )

        simulations = 0
        total_depth = 0.0
        deadline = (
            time.monotonic() + self.time_budget_ms / 1000.0
            if self.time_budget_ms
            else None
        )

        while simulations < self.n_simulations:
            if deadline and time.monotonic() >= deadline:
                break

            # 1. Selekcja
            node = self._select(root)

            # 2. Ekspansja
            if not engine.is_terminal(node.state) and node.untried_actions:
                node = self._expand(node, engine)

            # 3. Rollout
            reward = self._rollout(node.state, engine, player_id)

            # 4. Propagacja
            self._backpropagate(node, reward)

            total_depth += node.depth()
            simulations += 1

        if not root.children:
            return legal_actions[0], simulations, 0.0

        best = root.best_action_child()
        avg_depth = total_depth / max(1, simulations)
        return best.action, simulations, avg_depth

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Selekcja UCB1 — idź w dół aż do nierozwiniętego węzła lub liścia."""
        while node.is_fully_expanded and node.children:
            node = node.best_child(self.exploration_weight)
        return node

    def _expand(self, node: MCTSNode, engine: "GameEngine") -> MCTSNode:
        """Rozwiń jeden nieprzetestowany ruch."""
        action = node.untried_actions.pop(
            self._rollout_rng.randint(0, len(node.untried_actions) - 1)
        )
        new_state, _ = engine.step(node.state, action)
        new_state = self._advance_state(new_state, engine)

        child = MCTSNode(
            state=new_state,
            action=action,
            parent=node,
            player=new_state.act_player or node.player,
            untried_actions=list(engine.legal_actions(new_state)),
        )
        node.children.append(child)
        return child

    def _rollout(
        self, state: "GameState", engine: "GameEngine", player_id: str
    ) -> float:
        """Symuluj grę losowo do końca lub do max_rollout_depth."""
        rollout_agent = RandomAgent(self._rollout_rng)
        current = state.clone()
        depth = 0

        while not engine.is_terminal(current) and depth < self.max_rollout_depth:
            legal = engine.legal_actions(current)
            if not legal:
                current = self._advance_state(current, engine)
                legal = engine.legal_actions(current)
                if not legal:
                    break

            view = {"me": current.act_player or player_id}
            action = rollout_agent.choose(view, legal)
            current, _ = engine.step(current, action)
            current = self._advance_state(current, engine)
            depth += 1

        return self._reward(current, engine, player_id)

    def _advance_state(self, state: "GameState", engine: "GameEngine") -> "GameState":
        """Przepchnij stan przez puste przejścia (act_player=None między turami)."""
        from ..state import Stage
        max_iters = 10
        for _ in range(max_iters):
            if engine.is_terminal(state):
                break
            if state.stage == Stage.BOARD and state.act_player is None:
                if state.play_order:
                    from ..rules.board import start_player_turn
                    state = start_player_turn(state)
                else:
                    from ..rules.scoring import end_board_phase
                    state = end_board_phase(state, self._rollout_rng)
            else:
                break
        return state

    def _backpropagate(self, node: MCTSNode, reward: float) -> None:
        """Propaguj nagrodę w górę drzewa."""
        current: MCTSNode | None = node
        while current is not None:
            current.visits += 1
            current.total_reward += reward
            current = current.parent

    @staticmethod
    def _reward(state: "GameState", engine: "GameEngine", player_id: str) -> float:
        """Nagrada: 1.0 za wygraną, 0.0 za przegraną, 0.5 za remis/truncation."""
        winners = engine.winner(state)
        if not winners:
            return 0.5
        if player_id in winners:
            return 1.0 / len(winners)   # podziel nagrodę przy remisie
        return 0.0
