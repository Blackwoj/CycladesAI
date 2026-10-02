import json, random, sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from fuzz_api import call
from collections import Counter
codes = Counter(); bad = []

def mutate(a, v, rng):
    m = dict(a)
    choice = rng.randrange(7)
    if choice == 0: m["player"] = "p9"
    elif choice == 1: m["type"] = "teleport"
    elif choice == 2: m = {k: v2 for k, v2 in m.items() if k != "player"}
    elif choice == 3:
        for k in ("amount", "quantity", "slot"):
            if k in m: m[k] = m[k] + 50
        m.setdefault("field_id", "ZZ9")
    elif choice == 4: m["field_id"] = "IS999"; m["to_field"] = "X"
    elif choice == 5: m = {"type": "end_turn", "player": "p1" if v["act_player"] != "p1" else "p2"}
    else: m = {"type": "play_card", "player": v["act_player"], "card_id": "kraken", "targets": ["A1"]}
    return m

for seed in range(12):
    rng = random.Random(seed)
    n = 2 + seed % 4
    st, v = call("POST", "/game/new", {"num_players": n, "seed": seed})
    for _ in range(300):
        if v["terminal"]: break
        if rng.random() < 0.4:
            m = mutate(rng.choice(v["legal_actions"]), v, rng)
            st, r = call("POST", f"/game/{v['game_id']}/step", {"action": m})
            codes[st] += 1
            if st == 200:
                if m not in v["legal_actions"]:
                    bad.append(("ACCEPTED NON-LEGAL", m, [x for x in v["legal_actions"] if x["type"] == m.get("type")][:3]))
                v = r                                     # stan się zmienił — idź dalej z nowym
                continue
            if st not in (409, 422): bad.append((st, m, r))
            st2, v2 = call("GET", f"/game/{v['game_id']}")
            if v2["step"] != v["step"]: bad.append(("state changed after rejected action", m))
        a = rng.choice(v["legal_actions"])
        st, nv = call("POST", f"/game/{v['game_id']}/step", {"action": a})
        if st != 200: bad.append(("legal action failed", st, nv, a, v["step"])); break
        v = nv
    # nieaktualna akcja (podwójny klik): ta sama akcja drugi raz
    if not v["terminal"]:
        a = v["legal_actions"][0]
        call("POST", f"/game/{v['game_id']}/step", {"action": a})
        st, r = call("POST", f"/game/{v['game_id']}/step", {"action": a})
        codes[f"replay:{st}"] += 1

# błędne wejścia
for body, expect in [({"num_players": 1}, 422), ({"num_players": 6}, 422), ({"num_players": 2, "agents": {"p2": {"kind": "alien"}}}, 422),
                     ({"num_players": 2, "agents": {"p2": {"kind": "mcts", "n_simulations": 0}}}, 422),
                     ({"num_players": 2, "agents": {"p2": {"kind": "llm", "provider": "anthropic"}}}, 400)]:
    st, r = call("POST", "/game/new", body); codes[f"new:{st}"] += 1
    if st != expect: bad.append(("new_game", body, st, r))
st, r = call("GET", "/game/nope"); codes[f"get404:{st}"] += 1
st, r = call("POST", "/game/nope/ai-step"); codes[f"ai404:{st}"] += 1
st, v = call("POST", "/game/new", {"num_players": 2}); st, r = call("POST", f"/game/{v['game_id']}/ai-step")
codes[f"ai_on_human:{st}"] += 1
if st != 409: bad.append(("ai-step on human", st))
print("codes:", dict(codes)); print("bad:", len(bad))
for b in bad[:10]: print("  ", b)

