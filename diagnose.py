from __future__ import annotations

import argparse
import json
import random
from collections import Counter

import simulator


def natural_win_audit(games: int, seed: int):
    rng = random.Random(seed)
    rows = [simulator.play(0, rng) for _ in range(games)]
    wins = [r for r in rows if r["method"] != "draw"]
    score_hist = Counter(r["score"] for r in wins)
    method_hist = Counter(r["method"] for r in wins)
    call_hist = Counter(r["calls"] for r in rows)
    kan_hist = Counter(r["kans"] for r in rows)
    return {
        "games": games,
        "natural_win_rate": len(wins) / games,
        "natural_draw_rate": (games - len(wins)) / games,
        "natural_score_histogram": dict(sorted(score_hist.items())),
        "natural_method_histogram": dict(method_hist),
        "zero_call_rate": call_hist[0] / games,
        "one_or_more_call_rate": 1 - call_hist[0] / games,
        "one_or_more_kan_rate": 1 - kan_hist[0] / games,
        "avg_calls": sum(k * v for k, v in call_hist.items()) / games,
        "avg_kans": sum(k * v for k, v in kan_hist.items()) / games,
    }


def threshold_comparison(games: int, seed: int):
    out = []
    for minimum in (4, 5):
        summary, rows = simulator.run(games, minimum, seed)
        # These are wins after the threshold, so this is intentionally compared
        # against the natural-score audit rather than treated as a direct causal test.
        out.append(summary)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261017)
    args = ap.parse_args()

    audit = natural_win_audit(args.games, args.seed)
    thresholds = threshold_comparison(args.games, args.seed)
    report = {"natural_win_audit": audit, "thresholds": thresholds}
    print(json.dumps(report, ensure_ascii=False, indent=2))

    with open("diagnostic.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
