from __future__ import annotations

import argparse
import random
from collections import Counter

import simulator


def fmt(t):
    s = 'p' if simulator.suit(t) == 0 else 's'
    return f"{simulator.num(t)}{s}"


def fmt_hand(h):
    return ' '.join(fmt(t) for t in sorted(h))


def state(p):
    melds = []
    for k, ts in p.m:
        melds.append(f"{k}:[{','.join(fmt(t) for t in ts)}]")
    return f"hand=[{fmt_hand(p.h)}] open=[{' '.join(melds)}] closed={p.closed} discards=[{fmt_hand(p.d)}]"


def score_detail(p, dora, tsumo=False, rinshan=False):
    e = simulator.score(p, dora, tsumo=tsumo, rinshan=rinshan)
    if not e:
        return None
    return {"score": e[0], "yakuman": e[1], "yaku": e[2]}


def play_debug(seed=20261017, minscore=5, max_turns=39):
    r = random.Random(seed)
    deck = [t for t in simulator.T for _ in range(4)]
    r.shuffle(deck)
    dora = deck.pop()
    rinshan = [deck.pop() for _ in range(4)]
    live = deck
    ps = [simulator.P() for _ in range(4)]

    for _ in range(7):
        for p in ps:
            p.h.append(live.pop())

    print(f"SEED={seed} MIN_SCORE={minscore} DORA={fmt(dora)} LIVE={len(live)}")
    for i, p in enumerate(ps):
        print(f"P{i+1} START {state(p)}")

    turn = 0
    rin_i = 0
    calls = 0
    kans = 0

    for draw_no in range(1, min(max_turns, 39) + 1):
        if not live:
            break
        p = ps[turn]
        drawn = live.pop()
        p.h.append(drawn)
        print(f"\nTURN {draw_no} P{turn+1} DRAW {fmt(drawn)}")
        print(f"P{turn+1} BEFORE_ACTION {state(p)}")

        e = simulator.score(p, dora, tsumo=True)
        if e and e[0] >= minscore:
            print(f"WIN TSUMO P{turn+1} score={e[0]} yakuman={e[1]} yaku={e[2]} decomposition={simulator.winparts(p)}")
            print(f"FINAL {state(p)}")
            return

        aks = simulator.can_ankan(p)
        if aks and rin_i < 4:
            kt = aks[0]
            print(f"ACTION ANKAN P{turn+1} TILE {fmt(kt)}")
            simulator._remove(p.h, [kt] * 4)
            p.m.append(('kan', (kt, kt, kt, kt)))
            kans += 1
            p.h.append(rinshan[rin_i])
            rin_i += 1
            print(f"RINSHAN P{turn+1} DRAW {fmt(p.h[-1])} STATE {state(p)}")
            e = simulator.score(p, dora, tsumo=True, rinshan=True)
            if e and e[0] >= minscore:
                print(f"WIN RINSHAN P{turn+1} score={e[0]} yakuman={e[1]} yaku={e[2]} decomposition={simulator.winparts(p)}")
                print(f"FINAL {state(p)}")
                return

        q = simulator.discard(p, r)
        print(f"ACTION DISCARD P{turn+1} {fmt(q)}")
        p.h.remove(q)
        p.d.append(q)
        p.f.add(q)

        rons = []
        for j, o in enumerate(ps):
            if j == turn or q in o.f:
                continue
            o.h.append(q)
            e = simulator.score(o, dora, tsumo=False)
            o.h.pop()
            if e and e[0] >= minscore:
                rons.append((j, e))
        if rons:
            print(f"WIN RON discard=P{turn+1} tile={fmt(q)} winners=" + str([(j+1, e) for j, e in rons]))
            for j, e in rons:
                o = ps[j]
                o.h.append(q)
                print(f"P{j+1} RON score={e[0]} yakuman={e[1]} yaku={e[2]} decomposition={simulator.winparts(o)}")
                o.h.pop()
            return

        pon = [j for j, o in enumerate(ps) if j != turn and simulator.can_pon(o, q)]
        if pon and r.random() < 0.16:
            caller = r.choice(pon)
            o = ps[caller]
            print(f"ACTION PON P{caller+1} FROM_P{turn+1} TILE {fmt(q)}")
            simulator._remove(o.h, [q, q])
            o.m.append(('pon', (q, q, q)))
            o.closed = False
            calls += 1
            q2 = simulator.discard(o, r)
            print(f"ACTION DISCARD_AFTER_PON P{caller+1} {fmt(q2)}")
            o.h.remove(q2)
            o.d.append(q2)
            o.f.add(q2)
            turn = caller
            continue

        left = (turn + 1) % 4
        opts = simulator.chi_options(ps[left], q)
        if opts and r.random() < 0.10:
            o = ps[left]
            seq = r.choice(opts)
            need = list(seq)
            need.remove(q)
            print(f"ACTION CHI P{left+1} FROM_P{turn+1} SEQ {[fmt(x) for x in seq]}")
            simulator._remove(o.h, need)
            o.m.append(('seq', seq))
            o.closed = False
            calls += 1
            q2 = simulator.discard(o, r)
            print(f"ACTION DISCARD_AFTER_CHI P{left+1} {fmt(q2)}")
            o.h.remove(q2)
            o.d.append(q2)
            o.f.add(q2)
            turn = left
            continue

        turn = (turn + 1) % 4

    print(f"DRAW max_turns={max_turns} calls={calls} kans={kans}")
    for i, p in enumerate(ps):
        print(f"P{i+1} FINAL {state(p)}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=20261017)
    ap.add_argument('--min-score', type=int, default=5)
    ap.add_argument('--max-turns', type=int, default=39)
    args = ap.parse_args()
    play_debug(args.seed, args.min_score, args.max_turns)
