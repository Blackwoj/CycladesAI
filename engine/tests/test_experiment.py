"""Test integracyjny ExperimentRunner — headless batch."""
import pytest
from engine.experiment.runner import ExperimentRunner, ExperimentConfig
from engine.agents import RandomAgent
from engine.rng import Rng


def _make_config(n_games=3, n_players=2, seed=42):
    agents = {f"p{i}": RandomAgent(Rng(i)) for i in range(1, n_players + 1)}
    return ExperimentConfig(
        num_games=n_games,
        num_players=n_players,
        agents=agents,
        seed=seed,
        max_steps=200,
    )


def test_runner_completes_games():
    config = _make_config(n_games=3)
    results = ExperimentRunner(config).run()
    assert len(results.games) == 3


def test_runner_steps_positive():
    config = _make_config(n_games=2)
    results = ExperimentRunner(config).run()
    for g in results.games:
        assert g.steps > 0


def test_runner_illegal_moves_tracked():
    config = _make_config(n_games=2)
    results = ExperimentRunner(config).run()
    for g in results.games:
        assert all(isinstance(v, int) for v in g.illegal_moves.values())


def test_summary_returns_dict():
    config = _make_config(n_games=3)
    results = ExperimentRunner(config).run()
    summary = results.summary()
    assert "total_games" in summary
    assert summary["total_games"] == 3


def test_results_jsonl():
    """Wyniki muszą być JSON-serializowalne (potrzebne do logowania i FastAPI)."""
    import json
    config = _make_config(n_games=2)
    results = ExperimentRunner(config).run()
    jsonl = results.to_jsonl()
    lines = jsonl.strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # nie rzuca


def test_runner_deterministic_with_seed():
    """Ten sam seed → te same wyniki gier (reprodukcja do pracy mgr)."""
    cfg1 = _make_config(n_games=3, seed=7)
    cfg2 = _make_config(n_games=3, seed=7)
    r1 = ExperimentRunner(cfg1).run()
    r2 = ExperimentRunner(cfg2).run()
    for g1, g2 in zip(r1.games, r2.games):
        assert g1.steps == g2.steps
        assert g1.winner == g2.winner
