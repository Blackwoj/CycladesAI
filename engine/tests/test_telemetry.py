"""Testy telemetrii decyzji — surowca pod analizę i wykresy w pracy mgr."""
import json

from engine.agents import MCTSAgent, RandomAgent
from engine.experiment import ExperimentConfig, ExperimentRunner
from engine.experiment.telemetry import (
    DecisionRecord,
    DecisionTrace,
    agent_kind,
    player_snapshot,
    read_last_decision,
)
from engine.rng import Rng
from engine.rules.setup import build_initial_state


def test_trace_writes_one_json_line_per_record(tmp_path):
    path = tmp_path / "t.jsonl"
    with DecisionTrace(path) as trace:
        trace.add(DecisionRecord(matchup="m", game_id=0, step=0, decision_ms=1.5))
        trace.add(DecisionRecord(matchup="m", game_id=0, step=1, decision_ms=2.5))
    lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    assert lines[1]["step"] == 1
    assert lines[0]["decision_ms"] == 1.5


def test_trace_without_path_keeps_records_in_memory():
    """trace_path=None nie może wysypać runnera — telemetria jest opcjonalna."""
    with DecisionTrace(None) as trace:
        trace.add(DecisionRecord(step=7))
    assert len(trace.records) == 1


def test_agent_kind_recognises_agents():
    assert agent_kind(RandomAgent(Rng(1))) == "random"
    assert agent_kind(MCTSAgent(n_simulations=1)) == "mcts"


def test_read_last_decision_tolerates_agent_without_telemetry():
    """RandomAgent nie wystawia last_decision — ma wyjść pusty dict, nie błąd."""
    assert read_last_decision(RandomAgent(Rng(1))) == {}


def test_player_snapshot_counts_resources():
    s = build_initial_state(2, Rng(42))
    snap = player_snapshot(s, "p1")
    assert snap["coins"] == s.players["p1"].coins
    # p1 startuje z 2 wyspami i 2 polami wody (po naprawie graczy-widm)
    assert snap["islands_owned"] >= 1
    assert snap["warriors"] >= 1
    assert snap["metropolis"] == 0


def test_runner_logs_one_record_per_step(tmp_path):
    path = tmp_path / "trace.jsonl"
    cfg = ExperimentConfig(
        num_games=1, num_players=2,
        agents={"p1": RandomAgent(Rng(1)), "p2": RandomAgent(Rng(2))},
        seed=42, max_steps=30, matchup="test_matchup", trace_path=str(path),
    )
    results = ExperimentRunner(cfg).run()
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]

    assert len(rows) == results.games[0].steps
    assert {r["matchup"] for r in rows} == {"test_matchup"}
    assert [r["step"] for r in rows] == list(range(len(rows)))
    assert all(r["n_legal"] > 0 for r in rows)
    assert all(r["action_type"] for r in rows)


def test_mcts_reports_simulations_and_depth(tmp_path):
    """Metryki pracy MCTS (punkt C planu) muszą trafiać do rekordu decyzji."""
    path = tmp_path / "trace.jsonl"
    cfg = ExperimentConfig(
        num_games=1, num_players=2,
        agents={"p1": MCTSAgent(n_simulations=3, rollout_rng=Rng(9)),
                "p2": RandomAgent(Rng(2))},
        seed=42, max_steps=6, matchup="mcts", trace_path=str(path),
    )
    ExperimentRunner(cfg).run()
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    mcts_rows = [r for r in rows if r["agent_kind"] == "mcts"]

    assert mcts_rows, "brak decyzji MCTS w telemetrii"
    assert all(r["decision_ms"] >= 0 for r in mcts_rows)
    # Przy jednej legalnej akcji MCTS świadomie pomija symulacje
    # (_run_mcts zwraca od razu) — realny wybór jest dopiero od n_legal > 1.
    real_choices = [r for r in mcts_rows if r["n_legal"] > 1]
    assert real_choices, "brak decyzji MCTS z faktycznym wyborem"
    assert all(r["simulations"] > 0 for r in real_choices)
    assert all(r["tree_depth"] > 0 for r in real_choices)
    # RandomAgent nie raportuje pracy drzewa — pola zostają zerowe
    assert all(r["simulations"] == 0 for r in rows if r["agent_kind"] == "random")
