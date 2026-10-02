"""Fuzz przez prawdziwy serwer HTTP: losowe legalne ruchy człowieka + niezmienniki."""
import json, random, sys, urllib.request, urllib.error
from collections import Counter

BASE = "http://127.0.0.1:8000/api"
ISSUES = []
SEEN = set()
TYPES = Counter()
LAST = {}

def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

def check(v, ctx):
    s = v["state"]
    def bad(msg):
        key = (ctx, msg.split(" ")[0] + msg.split(" ")[-1][:12])
        if key in SEEN: return
        SEEN.add(key)
        ISSUES.append(f"{ctx} step={v['step']}: {msg} | last={LAST.get(ctx)}")
    for pid, p in s["players"].items():
        if p["coins"] < 0: bad(f"{pid} coins<0")
        if p["philosophers"] < 0 or p["priests"] < 0: bad(f"{pid} cards<0")
        if p["philosophers"] >= 4 and not s["board"].get("pending") and s["stage"] == "board" and s["act_player"] == pid:
            bad(f"{pid} ma {p['philosophers']} filozofów bez metropolii")
    units = Counter()
    for fid, f in s["fields"].items():
        q, k, o = f["entity"]["quantity"], f["entity"]["kind"], f["owner"]
        if q < 0: bad(f"{fid} qty<0")
        if f["type"] == "water":
            if (q > 0) != (o is not None): bad(f"{fid} water owner/qty mismatch owner={o} q={q}")
            if q > 0 and k != "ship": bad(f"{fid} water kind={k}")
        else:
            if q > 0 and k != "warrior": bad(f"{fid} island kind={k}")
            if q > 0 and o is None: bad(f"{fid} troops without owner")
        if q and o: units[(o, f["type"])] += q
        if f["is_metropolis"] and f["type"] != "island": bad(f"{fid} metro on water")
    for (o, t), n in units.items():
        if n > 8: bad(f"{o} {t} units={n} > 8")
    kr = s["cards"]["figures"].get("kraken")
    if kr and s["fields"][kr["field"]]["entity"]["quantity"] > 0:
        bad(f"fleets on kraken field {kr['field']}")
    if v["terminal"] and not v["winners"]: bad("terminal without winners")
    if not v["terminal"] and v["act_player_is_human"] and not v["legal_actions"]: bad("human without legal actions")
    if v["terminal"]:
        target = s["options"]["metros_to_win"]
        mc = Counter(f["owner"] for f in s["fields"].values() if f["is_metropolis"])
        for w in v["winners"]:
            if mc[w] < target: bad(f"winner {w} has {mc[w]} < {target} metros")
    # deck accounting: 17 kart = talia + odrzucone + tor + figurki na wyspach + chimera w toku
    if s["options"]["creatures"]:
        c = s["cards"]
        pend = (s["board"].get("pending") or {})
        held = [x for x in c["track"] if x] + c["deck"] + c["discard"] + [
            n for n, f in c["figures"].items() if n != "kraken" and f.get("held", True)]
        if pend.get("card") and not pend.get("via_chimera") and pend["card"] not in held:
            held.append(pend["card"])           # karta w trakcie rozstrzygania
        cnt = Counter(held)
        dup = [k for k, n in cnt.items() if n > 1]
        if dup: bad(f"duplicated creature cards {dup}")
        if len(set(held)) != 17: bad(f"creature cards accounted {len(set(held))}/17 pend={pend}")

def play(n, seed, dice, creatures, max_steps=2500):
    ctx = f"n={n} seed={seed} dice={dice} cr={creatures}"
    st, v = call("POST", "/game/new", {"num_players": n, "seed": seed, "combat_dice": dice, "creatures": creatures})
    if st != 201: ISSUES.append(f"{ctx} new_game {st} {v}"); return None
    rng = random.Random(seed)
    check(v, ctx)
    for _ in range(max_steps):
        if v["terminal"]: break
        a = rng.choice(v["legal_actions"])
        TYPES[a["type"] if a["type"] != "play_card" else "play_card:" + a["card_id"]] += 1
        LAST[ctx] = a
        st, nv = call("POST", f"/game/{v['game_id']}/step", {"action": a})
        if st != 200:
            ISSUES.append(f"{ctx} step {st} {nv} action={a}"); return None
        v = nv
        check(v, ctx)
    st, g = call("GET", f"/game/{v['game_id']}")
    if st != 200 or g["step"] != v["step"]: ISSUES.append(f"{ctx} GET mismatch")
    return v

if __name__ == "__main__":
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    res = Counter()
    for n in (2, 3, 4, 5):
        for dice in (False, True):
            for cr in (True, False):
                for g in range(games):
                    v = play(n, 100 * n + g, dice, cr)
                    res["done" if v and v["terminal"] else "unfinished"] += 1
    print("games:", dict(res))
    print("issues:", len(ISSUES))
    for i in ISSUES[:40]: print("  ", i)
    creatures_used = sorted(k for k in TYPES if k.startswith("play_card:"))
    print("action types:", len(TYPES), dict(TYPES.most_common(12)))
    print("creatures exercised:", len(creatures_used), [c.split(":")[1] for c in creatures_used])
