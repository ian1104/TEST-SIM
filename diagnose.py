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
        out.append(summary)
    return out


def paired_threshold_audit(games: int, seed: int):
    """Run the same per-game RNG seed at min 4 and min 5.

    This isolates whether a rejected 4-point win is merely replaced by a later
    >=5-point win in the same game. A normal threshold can therefore have a
    small effect on final win rate even when 4-point wins exist naturally.
    """
    categories = Counter()
    examples = []
    score_pairs = Counter()

    for i in range(games):
        game_seed = seed + i
        r4 = simulator.play(4, random.Random(game_seed))
        r5 = simulator.play(5, random.Random(game_seed))
        s4 = r4["score"] if r4["method"] != "draw" else None
        s5 = r5["score"] if r5["method"] != "draw" else None
        score_pairs[(s4, s5)] += 1

        if r4["method"] == "draw":
            categories["both_draw"] += 1
        elif r4["score"] >= 5:
            if r5["method"] == "draw":
                categories["min4_high_win_to_min5_draw"] += 1
            else:
                categories["both_win"] += 1
        else:  # min4 accepted a 4-point win
            if r5["method"] == "draw":
                categories["four_point_win_becomes_draw"] += 1
                if len(examples) < 10:
                    examples.append({"game": i, "min4": r4, "min5": r5})
            elif r5["score"] >= 5:
                categories["four_point_win_replaced_by_high_win"] += 1
                if len(examples) < 10:
                    examples.append({"game": i, "min4": r4, "min5": r5})
            else:
                categories["unexpected"] += 1

    return {
        "games": games,
        "categories": dict(categories),
        "score_pairs_top": [
            {"min4": a, "min5": b, "count": n}
            for (a, b), n in score_pairs.most_common(20)
        ],
        "examples": examples,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261017)
    args = ap.parse_args()

    audit = natural_win_audit(args.games, args.seed)
    thresholds = threshold_comparison(args.games, args.seed)
    paired = paired_threshold_audit(args.games, args.seed)
    report = {
        "natural_win_audit": audit,
        "thresholds": thresholds,
        "paired_threshold_audit": paired,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    with open("diagnostic.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
