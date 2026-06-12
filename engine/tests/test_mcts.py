"""Testy integracyjne MCTSAgent."""
import pytest
from engine.agents import MCTSAgent, RandomAgent
from engine.engine import GameEngine
from engine.rng import Rng


def _setup(seed=42, num_players=2):
    rng = Rng(seed)
    engine = GameEngine(rng=rng)
    state = engine.new_game(num_players=num_players, rng=rng.spawn())
    return engine, state


def test_mcts_returns_legal_action():
    engine, state = _setup()
    agent = MCTSAgent(n_simulations=20, rollout_rng=Rng(1))
    legal = engine.legal_actions(state)
    view = engine.state_view(state, state.act_player)
    action = agent.choose(view, legal)
    assert action in legal


def test_mcts_requires_state_in_view():
    engine, state = _setup()
    agent = MCTSAgent(n_simulations=5)
    legal = engine.legal_actions(state)
    with pytest.raises(ValueError, match="_state"):
        agent.choose({"me": state.act_player}, legal)


def test_mcts_single_action_returns_immediately():
    engine, state = _setup()
    agent = MCTSAgent(n_simulations=50)
    legal = engine.legal_actions(state)[:1]  # force single option
    view = engine.state_view(state, state.act_player)
    action = agent.choose(view, legal)
    assert action == legal[0]
    assert agent.stats.total_simulations == 0


def test_mcts_stats_recorded():
    engine, state = _setup()
    agent = MCTSAgent(n_simulations=30, rollout_rng=Rng(7))
    legal = engine.legal_actions(state)
    view = engine.state_view(state, state.act_player)
    agent.choose(view, legal)
    assert agent.stats.total_decisions == 1
    s = agent.stats.to_dict()
    assert "avg_simulations_per_move" in s
    assert "avg_decision_ms" in s


def test_mcts_completes_full_game():
    """MCTS vs Random — gra dochodzi do końca (lub max_steps)."""
    rng = Rng(99)
    engine = GameEngine(rng=rng)
    state = engine.new_game(num_players=2, rng=rng.spawn())

    agents = {
        "p1": MCTSAgent(n_simulations=15, rollout_rng=Rng(1)),
        "p2": RandomAgent(Rng(2)),
    }
    steps = 0
    max_steps = 300
    while not engine.is_terminal(state) and steps < max_steps:
        if state.act_player is None:
            break
        agent = agents.get(state.act_player)
        if agent is None:
            break
        legal = engine.legal_actions(state)
        if not legal:
            break
        view = engine.state_view(state, state.act_player)
        action = agent.choose(view, legal)
        state, _ = engine.step(state, action)
        steps += 1

    assert steps > 0


def test_mcts_time_budget():
    """time_budget_ms przerywa symulacje po zadanym czasie."""
    engine, state = _setup()
    agent = MCTSAgent(
        n_simulations=10_000,   # bez budżetu zajęłoby wieczność
        time_budget_ms=100.0,
        rollout_rng=Rng(5),
    )
    legal = engine.legal_actions(state)
    view = engine.state_view(state, state.act_player)
    action = agent.choose(view, legal)
    assert action in legal
    # Na pewno skończyło przed n_simulations
    assert agent.stats.total_simulations < 10_000
