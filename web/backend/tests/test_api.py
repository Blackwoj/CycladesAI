"""Adapter HTTP nie zmienia zasad: partia przez API == ta sama partia bezpośrednio na silniku."""
from fastapi.testclient import TestClient

from engine.agents import RandomAgent
from engine.engine import GameEngine
from engine.rng import Rng
from web.backend.main import app

client = TestClient(app)
MAX_STEPS = 400


def _play_http(seed: int) -> dict:
    r = client.post("/api/game/new", json={
        "num_players": 2, "seed": seed,
        "agents": {"p1": {"kind": "random"}, "p2": {"kind": "random"}},
    })
    assert r.status_code == 201, r.text
    view = r.json()
    assert view["stage"] == "roll"
    assert len(view["state"]["fields"]) == 74
    for _ in range(MAX_STEPS):
        if view["terminal"]:
            break
        r = client.post(f"/api/game/{view['game_id']}/ai-step")
        assert r.status_code == 200, r.text
        view = r.json()
    return view


def _play_direct(seed: int) -> dict:
    # odtworzenie dokładnie tej samej sekwencji Rng co GameStore.create + agents_factory
    rng = Rng(seed)
    engine = GameEngine(rng=rng)
    state = engine.new_game(2, rng.spawn())
    agents = {"p1": RandomAgent(rng=rng.spawn()), "p2": RandomAgent(rng=rng.spawn())}
    for _ in range(MAX_STEPS):
        if engine.is_terminal(state):
            break
        act = state.act_player
        legal = engine.legal_actions(state)
        state, _ = engine.step(state, agents[act].choose(engine.state_view(state, act), legal))
    return state.to_dict()


def test_http_matches_engine():
    view = _play_http(7)
    assert view["state"]["fields"] == _play_direct(7)["fields"]


def test_human_step_and_validation():
    view = client.post("/api/game/new", json={"num_players": 2, "seed": 1}).json()
    gid = view["game_id"]
    assert view["act_player_is_human"]
    assert view["legal_actions"]
    # akcja spoza legal_actions -> 409
    bad = {"type": "roll_bid", "player": view["act_player"], "row": "row_1", "amount": 999}
    assert client.post(f"/api/game/{gid}/step", json={"action": bad}).status_code == 409
    # ai-step przy turze człowieka -> 409
    assert client.post(f"/api/game/{gid}/ai-step").status_code == 409
    ok = client.post(f"/api/game/{gid}/step", json={"action": view["legal_actions"][0]})
    assert ok.status_code == 200, ok.text
    assert ok.json()["step"] == 1


def test_layout():
    islands = client.get("/api/board/layout").json()["islands"]
    assert len(islands) == 13
    assert islands["IS1"]["location"] == ["B1", "B2", "C1", "C2"]


class _FakeLLM:
    """Udaje agenta LLM: wybiera pierwszą legalną akcję i raportuje telemetrię."""
    def __init__(self, fail=False):
        self.fail = fail
        self.last_decision = {}

    def choose(self, view, legal):
        if self.fail:
            raise RuntimeError("rate limit")
        self.last_decision = {"model": "fake", "input_tokens": 123, "reasoning": "bo tak"}
        return legal[0]


def test_llm_telemetry_in_log(monkeypatch):
    from web.backend import agents_factory
    monkeypatch.setattr(agents_factory, "make_llm_agent", lambda *a, **k: _FakeLLM())
    v = client.post("/api/game/new", json={"num_players": 2, "seed": 3,
                                           "agents": {"p1": {"kind": "llm"}, "p2": {"kind": "llm"}}}).json()
    assert v["players"]["p1"] == "LLM claude-haiku-4-5 (guided)"
    v = client.post(f"/api/game/{v['game_id']}/ai-step").json()
    assert v["log"][-1]["detail"]["reasoning"] == "bo tak"
    assert v["log"][-1]["detail"]["input_tokens"] == 123


def test_llm_api_error_is_502(monkeypatch):
    from web.backend import agents_factory
    monkeypatch.setattr(agents_factory, "make_llm_agent", lambda *a, **k: _FakeLLM(fail=True))
    v = client.post("/api/game/new", json={"num_players": 2, "seed": 3,
                                           "agents": {"p1": {"kind": "llm"}, "p2": {"kind": "llm"}}}).json()
    r = client.post(f"/api/game/{v['game_id']}/ai-step")
    assert r.status_code == 502 and "rate limit" in r.json()["detail"]


def test_llm_missing_key_is_400(monkeypatch):
    from web.backend import agents_factory

    def no_key(*a, **k):
        raise EnvironmentError("Brak ANTHROPIC_API_KEY")
    monkeypatch.setattr(agents_factory, "make_llm_agent", no_key)
    r = client.post("/api/game/new", json={"num_players": 2, "agents": {"p2": {"kind": "llm"}}})
    assert r.status_code == 400 and "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_llm_providers_endpoint():
    data = client.get("/api/llm/providers").json()
    assert set(data) == {"anthropic", "openai", "gemini", "ollama"}
    assert all("available" in v and "reason" in v for v in data.values())
