"""Analiza wyników eksperymentów — CSV i wykresy do pracy magisterskiej.

Czyta dwa źródła z `engine/experiments/results/`:
  *.jsonl        — jeden rekord na GRĘ  (z ExperimentRunner.to_jsonl)
  traces/*.jsonl — jeden rekord na DECYZJĘ (z engine/experiment/telemetry.py)

Produkuje w `results/analysis/`:
  decisions.csv        — pełna tabela decyzji (import do Excela / R / pandas)
  per_matchup.csv      — agregaty na konfigurację (win rate, truncation, koszt)
  per_agent.csv        — agregaty na rodzaj agenta
  fig_*.png            — wykresy

Użycie:
    python3 engine/experiments/analyze.py
    python3 engine/experiments/analyze.py --results-dir inna/sciezka --no-charts

Wykresy wymagają matplotlib (`pip install matplotlib`); bez niego skrypt i tak
wygeneruje wszystkie pliki CSV.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RESULTS_DIR = Path(__file__).parent / "results"

# Paleta stała dla wszystkich wykresów — ten sam agent ma zawsze ten sam kolor.
COLORS = {
    "random": "#94a3b8",
    "mcts": "#2563eb",
    "llm": "#f59e0b",
    "human": "#10b981",
}
FALLBACK_COLORS = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#94a3b8"]


# ---------------------------------------------------------------------------
# Wczytywanie
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_games(results_dir: Path) -> dict[str, list[dict]]:
    """matchup -> lista rekordów gier (pliki *.jsonl w results/, bez traces/)."""
    games = {}
    for path in sorted(results_dir.glob("*.jsonl")):
        rows = load_jsonl(path)
        if rows:
            games[path.stem] = rows
    return games


def load_decisions(results_dir: Path) -> list[dict]:
    """Wszystkie decyzje ze wszystkich przebiegów (results/traces/*.jsonl)."""
    decisions = []
    for path in sorted((results_dir / "traces").glob("*.jsonl")):
        decisions += load_jsonl(path)
    return decisions


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def write_decisions_csv(decisions: list[dict], out: Path) -> None:
    if not decisions:
        return
    # `action` to zagnieżdżony dict — spłaszczamy do JSON-a w jednej kolumnie,
    # żeby CSV dało się wczytać dowolnym narzędziem bez parsowania kolumn.
    cols = [c for c in decisions[0] if c != "action"] + ["action_json"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d in decisions:
            row = {k: v for k, v in d.items() if k != "action"}
            row["action_json"] = json.dumps(d.get("action", {}), ensure_ascii=False)
            w.writerow(row)


def _mean(xs, digits=2):
    return round(statistics.mean(xs), digits) if xs else 0.0


def summarize_matchups(games: dict[str, list[dict]],
                       decisions: list[dict]) -> list[dict]:
    by_matchup = defaultdict(list)
    for d in decisions:
        by_matchup[d["matchup"]].append(d)

    out = []
    for name, rows in games.items():
        n = len(rows)
        decided = [r for r in rows if r.get("winner")]
        wins = Counter(w for r in rows for w in r.get("winner", []))
        dec = by_matchup.get(name, [])
        llm = [d for d in dec if d["agent_kind"] == "llm"]
        out.append({
            "matchup": name,
            "games": n,
            "decided": len(decided),
            "truncated": sum(1 for r in rows if r.get("truncated")),
            "truncated_pct": round(100 * sum(1 for r in rows if r.get("truncated")) / n, 1),
            "avg_steps": _mean([r["steps"] for r in rows], 1),
            "winner_p1": wins.get("p1", 0),
            "winner_p2": wins.get("p2", 0),
            "decisions_logged": len(dec),
            "avg_decision_ms": _mean([d["decision_ms"] for d in dec]),
            "avg_branching": _mean([d["n_legal"] for d in dec], 1),
            "llm_decisions": len(llm),
            "llm_illegal_attempts": sum(d["illegal_attempts"] for d in llm),
            "llm_fallbacks": sum(1 for d in llm if d["fallback_used"]),
            "llm_input_tokens": sum(d["input_tokens"] for d in llm),
            "llm_output_tokens": sum(d["output_tokens"] for d in llm),
        })
    return out


def summarize_agents(decisions: list[dict]) -> list[dict]:
    by_agent = defaultdict(list)
    for d in decisions:
        key = (d["agent_kind"], d["agent_label"], d.get("model", ""), d.get("mode", ""))
        by_agent[key].append(d)

    out = []
    for (kind, label, model, mode), rows in sorted(by_agent.items()):
        illegal = sum(r["illegal_attempts"] for r in rows)
        out.append({
            "agent_kind": kind,
            "agent_label": label,
            "model": model,
            "mode": mode,
            "decisions": len(rows),
            "avg_decision_ms": _mean([r["decision_ms"] for r in rows]),
            "median_decision_ms": round(statistics.median(
                [r["decision_ms"] for r in rows]), 2) if rows else 0,
            "avg_branching": _mean([r["n_legal"] for r in rows], 1),
            "illegal_attempts": illegal,
            "illegal_per_decision": round(illegal / len(rows), 3) if rows else 0,
            "fallbacks": sum(1 for r in rows if r["fallback_used"]),
            "avg_input_tokens": _mean([r["input_tokens"] for r in rows], 1),
            "avg_output_tokens": _mean([r["output_tokens"] for r in rows], 1),
            "avg_simulations": _mean([r["simulations"] for r in rows], 1),
            "avg_tree_depth": _mean([r["tree_depth"] for r in rows]),
        })
    return out


def write_csv(rows: list[dict], out: Path) -> None:
    if not rows:
        return
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Wykresy
# ---------------------------------------------------------------------------

def make_charts(games: dict[str, list[dict]], decisions: list[dict],
                out_dir: Path) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")            # bez GUI — zapis do pliku
        import matplotlib.pyplot as plt
    except ImportError:
        print("[analyze] matplotlib niedostępny — pomijam wykresy "
              "(pip install matplotlib)")
        return []

    plt.rcParams.update({
        "figure.dpi": 130,
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    made = []

    def save(fig, name):
        path = out_dir / name
        fig.tight_layout()
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        made.append(name)

    # --- 1. Rozstrzygnięcia i truncation na konfigurację -------------------
    if games:
        names = list(games)
        decided = [100 * sum(1 for r in games[n] if r.get("winner")) / len(games[n])
                   for n in names]
        trunc = [100 * sum(1 for r in games[n] if r.get("truncated")) / len(games[n])
                 for n in names]
        fig, ax = plt.subplots(figsize=(7, 3.6))
        y = range(len(names))
        h = 0.38
        ax.barh([i + h / 2 for i in y], decided, height=h,
                color="#2563eb", label="rozstrzygnięte")
        ax.barh([i - h / 2 for i in y], trunc, height=h,
                color="#ef4444", label="truncated")
        ax.set_yticks(list(y))
        ax.set_yticklabels(names)
        ax.set_xlabel("% partii")
        ax.set_xlim(0, 100)
        ax.set_title("Rozstrzygalność partii wg konfiguracji agentów")
        ax.legend(loc="lower right")
        save(fig, "fig_rozstrzygalnosc.png")

    # --- 2. Długość partii -------------------------------------------------
    if games:
        fig, ax = plt.subplots(figsize=(7, 3.6))
        data = [[r["steps"] for r in games[n]] for n in games]
        ax.boxplot(data, tick_labels=list(games))
        ax.set_ylabel("kroków w partii")
        ax.set_title("Rozkład długości partii")
        ax.tick_params(axis="x", rotation=15)
        save(fig, "fig_dlugosc_partii.png")

    if not decisions:
        return made

    by_kind = defaultdict(list)
    for d in decisions:
        by_kind[d["agent_kind"]].append(d)

    # --- 3. Koszt decyzji (skala log — rzędy wielkości się różnią) ---------
    fig, ax = plt.subplots(figsize=(6, 3.6))
    kinds = sorted(by_kind)
    vals = [[max(d["decision_ms"], 0.001) for d in by_kind[k]] for k in kinds]
    bp = ax.boxplot(vals, tick_labels=kinds, patch_artist=True)
    for patch, k in zip(bp["boxes"], kinds):
        patch.set_facecolor(COLORS.get(k, "#94a3b8"))
        patch.set_alpha(0.75)
    ax.set_yscale("log")
    ax.set_ylabel("czas decyzji [ms, skala log]")
    ax.set_title("Koszt pojedynczej decyzji wg rodzaju agenta")
    save(fig, "fig_czas_decyzji.png")

    # --- 4. Nielegalne odpowiedzi: GUIDED vs FREE_FORM --------------------
    llm = [d for d in decisions if d["agent_kind"] == "llm"]
    if llm:
        by_mode = defaultdict(list)
        for d in llm:
            by_mode[d.get("mode") or "?"].append(d)
        modes = sorted(by_mode)
        rate = [sum(d["illegal_attempts"] for d in by_mode[m]) / len(by_mode[m])
                for m in modes]
        fb = [100 * sum(1 for d in by_mode[m] if d["fallback_used"]) / len(by_mode[m])
              for m in modes]
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(8, 3.4))
        a1.bar(modes, rate, color="#f59e0b")
        a1.set_ylabel("odrzuconych odpowiedzi / decyzję")
        a1.set_title("Nietrafione odpowiedzi LLM")
        a2.bar(modes, fb, color="#ef4444")
        a2.set_ylabel("% decyzji")
        a2.set_title("Decyzje zakończone losowaniem (fallback)")
        save(fig, "fig_llm_tryby.png")

        # --- 5. Zużycie tokenów w trakcie partii --------------------------
        buckets = defaultdict(list)
        for d in llm:
            buckets[d["round_no"]].append(d["input_tokens"] + d["output_tokens"])
        if buckets:
            rounds = sorted(buckets)
            fig, ax = plt.subplots(figsize=(7, 3.4))
            ax.plot(rounds, [_mean(buckets[r], 1) for r in rounds],
                    marker="o", color="#f59e0b")
            ax.set_xlabel("runda")
            ax.set_ylabel("tokenów na decyzję (średnio)")
            ax.set_title("Koszt promptu rośnie wraz ze stanem gry")
            save(fig, "fig_tokeny_w_czasie.png")

    # --- 6. Współczynnik rozgałęzienia w czasie ---------------------------
    branch = defaultdict(list)
    for d in decisions:
        branch[d["round_no"]].append(d["n_legal"])
    if branch:
        rounds = sorted(branch)
        fig, ax = plt.subplots(figsize=(7, 3.4))
        ax.plot(rounds, [_mean(branch[r], 1) for r in rounds],
                marker="o", color="#2563eb")
        ax.set_xlabel("runda")
        ax.set_ylabel("liczba legalnych akcji (średnio)")
        ax.set_title("Wielkość przestrzeni decyzyjnej w trakcie partii")
        save(fig, "fig_rozgalezienie.png")

    # --- 7. Co agenci właściwie robią -------------------------------------
    kinds = sorted(by_kind)
    types = sorted({d["action_type"] for d in decisions})
    if types:
        fig, ax = plt.subplots(figsize=(7.5, 3.8))
        bottom = [0.0] * len(kinds)
        # Paleta skalowana do liczby typów akcji — stała lista kolorów
        # powodowała, że przy >6 typach dwa segmenty dostawały ten sam kolor.
        cmap = plt.get_cmap("tab20")
        for i, t in enumerate(types):
            share = []
            for k in kinds:
                rows = by_kind[k]
                share.append(100 * sum(1 for d in rows if d["action_type"] == t)
                             / len(rows))
            ax.bar(kinds, share, bottom=bottom,
                   color=cmap(i / max(1, len(types) - 1) * 0.95), label=t)
            bottom = [b + s for b, s in zip(bottom, share)]
        ax.set_ylabel("% decyzji")
        ax.set_title("Struktura wybieranych akcji wg rodzaju agenta")
        ax.legend(fontsize=7, ncol=2, loc="upper right")
        save(fig, "fig_typy_akcji.png")

    # --- 8. Postęp gry: metropolie i wyspy --------------------------------
    prog = defaultdict(lambda: defaultdict(list))
    for d in decisions:
        prog[d["agent_kind"]][d["round_no"]].append(d["islands_owned"])
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for k in sorted(prog):
        rounds = sorted(prog[k])
        ax.plot(rounds, [_mean(prog[k][r], 2) for r in rounds],
                marker="o", label=k, color=COLORS.get(k, None))
    ax.set_xlabel("runda")
    ax.set_ylabel("posiadanych wysp (średnio)")
    ax.set_title("Ekspansja terytorialna wg rodzaju agenta")
    ax.legend()
    save(fig, "fig_ekspansja.png")

    return made


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Analiza wyników CycladesAI")
    ap.add_argument("--results-dir", default=str(RESULTS_DIR))
    ap.add_argument("--no-charts", action="store_true", help="tylko CSV")
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    out_dir = results_dir / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    games = load_games(results_dir)
    decisions = load_decisions(results_dir)

    print(f"[analyze] konfiguracji: {len(games)}  "
          f"partii: {sum(len(v) for v in games.values())}  "
          f"decyzji: {len(decisions)}")
    if not games and not decisions:
        print(f"[analyze] brak danych w {results_dir} — uruchom najpierw compare.py")
        return

    write_decisions_csv(decisions, out_dir / "decisions.csv")
    matchups = summarize_matchups(games, decisions)
    write_csv(matchups, out_dir / "per_matchup.csv")
    write_csv(summarize_agents(decisions), out_dir / "per_agent.csv")

    for m in matchups:
        print(f"   {m['matchup']:32} partii={m['games']:3}  "
              f"truncated={m['truncated_pct']:5}%  "
              f"avg_steps={m['avg_steps']:6}  "
              f"avg_decyzja={m['avg_decision_ms']:8} ms")

    made = [] if args.no_charts else make_charts(games, decisions, out_dir)
    print(f"[analyze] zapisano w {out_dir}: "
          f"decisions.csv, per_matchup.csv, per_agent.csv"
          + (f", {len(made)} wykresów" if made else ""))


if __name__ == "__main__":
    main()
