from __future__ import annotations
import csv
import random
import statistics
from collections import Counter
import simulator


def random_discard(p, r):
    return r.choice(p.h)


def basic_discard(p, r):
    # Simple human-like heuristic: keep pairs and adjacent tiles, but do not
    # perform the current simulator's extra scoring search.
    c = Counter(p.h)
    def value(t):
        n = simulator.num(t)
        v = (c[t] - 1) * 1.5
        for d in (-1, 1):
            u = t + d
            if 0 <= u < 18 and simulator.suit(u) == simulator.suit(t) and u in c:
                v += 1.0
        for d in (-2, 2):
            u = t + d
            if 0 <= u < 18 and simulator.suit(u) == simulator.suit(t) and u in c:
                v += 0.3
        if n in (1, 9):
            v -= 0.1
        return v
    return min(p.h, key=lambda t: (value(t), t))


def current_discard(p, r):
    return simulator.discard(p, r)


def strong_discard(p, r):
    # Stronger but still legal-information-only heuristic. Prefer discards
    # that leave more immediate sequence/triplet/pair potential and estimate
    # one-tile improvement by counting currently useful tile types.
    c = Counter(p.h)
    def potential(hand):
        cc = Counter(hand)
        score = 0.0
        for t, n in cc.items():
            score += max(0, n - 1) * 2.2
            num = simulator.num(t)
            for d in (-1, 1):
                u = t + d
                if 0 <= u < 18 and simulator.suit(u) == simulator.suit(t) and cc.get(u, 0):
                    score += 1.25 * min(n, cc[u])
            for d in (-2, 2):
                u = t + d
                if 0 <= u < 18 and simulator.suit(u) == simulator.suit(t) and cc.get(u, 0):
                    score += 0.35 * min(n, cc[u])
            if num in (1, 9):
                score -= 0.12
        # Count distinct tile faces that could complete a simple 3-tile meld
        # from the remaining hand. This is only a local shape estimate.
        for start in range(1, 8):
            for s in (0, 1):
                q = [s * 9 + start - 1 + i for i in range(3)]
                have = sum(bool(cc.get(x)) for x in q)
                if have == 2:
                    score += 1.5
                elif have == 3:
                    score += 2.5
        return score

    best = None
    for t in sorted(set(p.h)):
        h = list(p.h)
        h.remove(t)
        v = potential(h)
        if best is None or v > best[0] or (v == best[0] and t < best[1]):
            best = (v, t)
    return best[1]


POLICIES = {
    "random": random_discard,
    "basic": basic_discard,
    "current": current_discard,
    "strong": strong_discard,
}


def run_policy(name, games, minscore, seed):
    old = simulator.discard
    simulator.discard = POLICIES[name]
    try:
        summary, rows = simulator.run(games, minscore, seed)
    finally:
        simulator.discard = old
    summary = dict(summary)
    summary["ai"] = name
    return summary, rows


def main():
    games = 10000
    seed = 20261017
    rows = []
    for ai in POLICIES:
        for minimum in (4, 5):
            s, _ = run_policy(ai, games, minimum, seed)
            rows.append(s)
            print(s)
    with open("ai_benchmark.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ai", "games", "min_score", "win_rate", "draw_rate", "ron_rate", "tsumo_rate", "avg_score", "avg_end_draw", "call_rate", "kan_rate", "super_red", "all_green", "chin_yao"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
