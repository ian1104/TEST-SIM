from __future__ import annotations
import argparse, csv, os, random, statistics
from collections import Counter

# Tile id: 0..8 = pinzu 1..9, 9..17 = souzu 1..9.
T = tuple(range(18))
RED = {0, 2, 4, 5, 6, 8, 9, 13, 15, 17}
GREEN = {10, 11, 12, 14, 16}  # 2,3,4,6,8 souzu only
TERMS = {0, 8, 9, 17}         # 1/9 of either suit


def num(t: int) -> int:
    return t % 9 + 1


def suit(t: int) -> int:
    return t // 9


def tile_counts(tiles):
    return Counter(tiles)


def all_decompositions(tiles, melds_needed):
    """Enumerate every valid (melds_needed x 3) + pair decomposition."""
    if len(tiles) != melds_needed * 3 + 2:
        return []
    c = Counter(tiles)
    out = []

    def rec(c, m_left, pair_left, dec):
        if m_left == 0 and pair_left == 0:
            out.append(tuple(dec))
            return
        t = next((x for x in range(18) if c[x]), None)
        if t is None:
            return

        if pair_left and c[t] >= 2:
            c[t] -= 2
            rec(c, m_left, 0, dec + [('pair', (t, t))])
            c[t] += 2

        if m_left and c[t] >= 3:
            c[t] -= 3
            rec(c, m_left - 1, pair_left, dec + [('trip', (t, t, t))])
            c[t] += 3

        n = num(t)
        if m_left and n <= 7:
            a, b = t + 1, t + 2
            if suit(a) == suit(t) == suit(b) and c[a] > 0 and c[b] > 0:
                c[t] -= 1; c[a] -= 1; c[b] -= 1
                rec(c, m_left - 1, pair_left,
                    dec + [('seq', (t, a, b))])
                c[t] += 1; c[a] += 1; c[b] += 1

    rec(c, melds_needed, 1, [])
    return out


def parts(tiles, need):
    """Backward-compatible first decomposition, if one exists."""
    ds = all_decompositions(tiles, need)
    return list(ds[0]) if ds else None


class P:
    def __init__(self):
        self.h = []          # concealed tiles only
        self.m = []          # [('seq'|'pon'|'kan', tuple(tiles))]
        self.d = []
        self.f = set()       # simplified permanent furiten set
        self.closed = True

    def all(self):
        return self.h + [x for _, ts in self.m for x in ts]


def winparts(p):
    needed = 2 - len(p.m)
    if needed < 0:
        return []
    return all_decompositions(p.h, needed)


def _base_score(ms):
    return sum(
        1 if k == 'seq' else
        2 if k in ('trip', 'pon') else
        3 if k == 'kan' else 0
        for k, _ in ms
    )


def _special_name(allx):
    if all(x in TERMS for x in allx):
        return 'chin_yao', 20
    if all(x in GREEN for x in allx):
        return 'all_green', 15
    if all(x in RED for x in allx):
        return 'super_red', 10
    return None, 0


def _ordinary_score(p, dec, dora, tsumo, rinshan):
    ms = list(dec) + list(p.m)
    allx = p.all()
    base = _base_score(ms)
    y = []
    bonus = 0

    if all(2 <= num(x) <= 8 for x in allx):
        y.append('tanyao')
        bonus += 1

    chanta = True
    for kind, ts in ms:
        if not any(num(x) in (1, 9) for x in ts):
            chanta = False
            break
    if chanta:
        y.append('chanta')
        bonus += 2

    if p.closed and tsumo:
        y.append('menzen_tsumo')
        bonus += 1

    if len({suit(x) for x in allx}) == 1:
        y.append('chinitsu')
        bonus += 2

    seqs = [ts for k, ts in dec if k == 'seq']
    if p.closed and len(seqs) >= 2:
        if any(seqs[i] == seqs[j]
               for i in range(len(seqs))
               for j in range(i + 1, len(seqs))):
            y.append('iipeikou')
            bonus += 1

    bonus += sum(x in RED for x in allx)
    bonus += sum(x == dora for x in allx)

    if rinshan:
        y.append('rinshan')
        bonus += 2

    return base + bonus, y


def score(p, dora, tsumo=False, rinshan=False):
    """Return best scoring interpretation: (score, special, yaku)."""
    decs = winparts(p)
    if not decs:
        return None

    special, special_bonus = _special_name(p.all())
    results = []
    for dec in decs:
        ms = list(dec) + list(p.m)
        base = _base_score(ms)
        if special:
            results.append((base + special_bonus, special, []))
        else:
            s, y = _ordinary_score(p, dec, dora, tsumo, rinshan)
            results.append((s, None, y))
    return max(results, key=lambda x: x[0])


def discard(p, r):
    """Simple heuristic AI. Higher value means more desirable to discard."""
    c = Counter(p.h)
    best = None
    best_value = -10**9
    for t in sorted(c):
        value = (c[t] - 1) * 1.8
        n = num(t)
        if 2 <= n <= 8:
            value += 0.5
        for d in (-2, -1, 1, 2):
            u = t + d
            if 0 <= u < 18 and suit(u) == suit(t) and u in c:
                value += 0.65 if abs(d) == 1 else 0.2
        if n in (1, 9):
            value -= 0.2
        value += r.random() * 0.12
        if value > best_value:
            best_value = value
            best = t
    return best


def can_pon(p, t):
    return Counter(p.h)[t] >= 2 and len(p.m) < 2


def chi_options(p, t):
    """Return every legal chi using the discarded tile."""
    if len(p.m) >= 2:
        return []
    s, n = suit(t), num(t)
    result = []
    for start in range(max(1, n - 2), min(n, 7) + 1):
        q = [s * 9 + start - 1 + i for i in range(3)]
        if t not in q:
            continue
        need = Counter(q)
        need[t] -= 1
        if all(Counter(p.h)[x] >= count for x, count in need.items()):
            result.append(tuple(q))
    return result


def _remove_tiles(hand, tiles):
    for t in tiles:
        hand.remove(t)


def result(draws, method, e, calls, kans):
    return {
        'draws': draws,
        'method': method,
        'score': e[0] if e else 0,
        'yakuman': e[1] or '' if e else '',
        'yaku': ','.join(e[2]) if e else '',
        'calls': calls,
        'kans': kans,
    }


def play(minscore, r):
    """One hand simulation.

    This version keeps the physical tile count correct and implements the
    simplified call rules without corrupting concealed hands. The AI remains
    intentionally simple; this phase is for validating the rule engine.
    """
    deck = [t for t in T for _ in range(4)]
    r.shuffle(deck)

    dora = deck.pop()
    rinshan = [deck.pop() for _ in range(4)]
    live = deck

    ps = [P() for _ in range(4)]
    for _ in range(7):
        for p in ps:
            p.h.append(live.pop())

    turn = 0
    rin_i = 0
    calls = 0
    kans = 0

    # 39 normal live draws remain after the 28 initial tiles.
    for draw_no in range(1, 40):
        if not live:
            break
        p = ps[turn]
        p.h.append(live.pop())

        e = score(p, dora, tsumo=True)
        if e and e[0] >= minscore:
            return result(draw_no, 'tsumo', e, calls, kans)

        # Ankan: preserve menzen, draw one rinshan tile, then check tsumo.
        counts = Counter(p.h)
        kt = next((t for t, v in counts.items()
                   if v == 4 and len(p.m) < 2 and rin_i < 4), None)
        if kt is not None:
            _remove_tiles(p.h, [kt] * 4)
            p.m.append(('kan', (kt, kt, kt, kt)))
            kans += 1
            p.h.append(rinshan[rin_i])
            rin_i += 1
            e = score(p, dora, tsumo=True, rinshan=True)
            if e and e[0] >= minscore:
                return result(draw_no, 'tsumo', e, calls, kans)

        q = discard(p, r)
        p.h.remove(q)
        p.d.append(q)
        p.f.add(q)

        # Ron has priority over all calls. Multiple ron is possible in the
        # real rules; for a single-hand win-rate simulation, any ron ends it.
        for j, o in enumerate(ps):
            if j == turn or q in o.f:
                continue
            o.h.append(q)
            e = score(o, dora, tsumo=False)
            o.h.pop()
            if e and e[0] >= minscore:
                return result(draw_no, 'ron', e, calls, kans)

        # Randomized but legal call policy for the placeholder AI.
        caller = None
        meld = None

        # Pon may come from any opponent.
        pon_candidates = [j for j, o in enumerate(ps)
                          if j != turn and can_pon(o, q)]
        if pon_candidates and r.random() < 0.16:
            caller = r.choice(pon_candidates)
            o = ps[caller]
            _remove_tiles(o.h, [q, q])
            meld = ('pon', (q, q, q))

        # Chi only from the player on the left of the discarder, and only if
        # no pon was selected.
        if caller is None:
            j = (turn + 1) % 4
            options = chi_options(ps[j], q)
            if options and r.random() < 0.10:
                caller = j
                seq = r.choice(options)
                need = list(seq)
                need.remove(q)
                _remove_tiles(ps[j].h, need)
                meld = ('seq', tuple(seq))

        if caller is not None:
            o = ps[caller]
            o.m.append(meld)
            o.closed = False
            calls += 1

            # A call is followed immediately by a discard; no draw occurs.
            q2 = discard(o, r)
            o.h.remove(q2)
            o.d.append(q2)
            o.f.add(q2)
            turn = caller
        else:
            turn = (turn + 1) % 4

    return result(39, 'draw', None, calls, kans)


def run(n, minscore, seed):
    r = random.Random(seed)
    rows = [play(minscore, r) for _ in range(n)]
    wins = [x for x in rows if x['method'] != 'draw']
    return {
        'games': n,
        'min_score': minscore,
        'win_rate': len(wins) / n,
        'draw_rate': sum(x['method'] == 'draw' for x in rows) / n,
        'ron_rate': sum(x['method'] == 'ron' for x in wins) / len(wins) if wins else 0,
        'tsumo_rate': sum(x['method'] == 'tsumo' for x in wins) / len(wins) if wins else 0,
        'avg_score': statistics.mean(x['score'] for x in wins) if wins else 0,
        'avg_end_draw': statistics.mean(x['draws'] for x in rows),
        'call_rate': sum(x['calls'] > 0 for x in rows) / n,
        'kan_rate': sum(x['kans'] > 0 for x in rows) / n,
        'super_red': sum(x['yakuman'] == 'super_red' for x in rows) / n,
        'all_green': sum(x['yakuman'] == 'all_green' for x in rows) / n,
        'chin_yao': sum(x['yakuman'] == 'chin_yao' for x in rows) / n,
    }, rows


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=10000)
    ap.add_argument('--seed', type=int, default=20261017)
    ap.add_argument('--out', default='results')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    summaries = []
    for minimum in (4, 5):
        summary, rows = run(a.games, minimum, a.seed)
        summaries.append(summary)
        with open(f'{a.out}/hands_min{minimum}.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)

    with open(f'{a.out}/summary.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=summaries[0])
        writer.writeheader()
        writer.writerows(summaries)

    for summary in summaries:
        print(summary)
