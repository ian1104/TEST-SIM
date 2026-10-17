from __future__ import annotations
import argparse, csv, os, random, statistics
from collections import Counter

T = tuple(range(18))
RED = {0, 2, 4, 5, 6, 8, 9, 13, 15, 17}
GREEN = {10, 11, 12, 14, 16}
TERMS = {0, 8, 9, 17}


def num(t): return t % 9 + 1

def suit(t): return t // 9


def all_decompositions(tiles, melds_needed):
    if len(tiles) != melds_needed * 3 + 2:
        return []
    c = Counter(tiles)
    out = []
    def rec(m_left, pair_left, dec):
        if m_left == 0 and pair_left == 0:
            out.append(tuple(dec)); return
        t = next((x for x in range(18) if c[x]), None)
        if t is None: return
        if pair_left and c[t] >= 2:
            c[t] -= 2; rec(m_left, 0, dec + [('pair',(t,t))]); c[t] += 2
        if m_left and c[t] >= 3:
            c[t] -= 3; rec(m_left-1, pair_left, dec + [('trip',(t,t,t))]); c[t] += 3
        n = num(t)
        if m_left and n <= 7:
            a,b=t+1,t+2
            if suit(a)==suit(t)==suit(b) and c[a] and c[b]:
                c[t]-=1; c[a]-=1; c[b]-=1
                rec(m_left-1, pair_left, dec+[('seq',(t,a,b))])
                c[t]+=1; c[a]+=1; c[b]+=1
    rec(melds_needed, 1, [])
    return out


def parts(tiles, need):
    ds=all_decompositions(tiles,need)
    return list(ds[0]) if ds else None


class P:
    def __init__(self):
        self.h=[]
        self.m=[]
        self.d=[]
        self.f=set()
        self.closed=True

    def all(self):
        return self.h + [x for _,ts in self.m for x in ts]


def winparts(p):
    needed=2-len(p.m)
    if needed < 0: return []
    return all_decompositions(p.h, needed)


def _base_score(ms):
    return sum(1 if k=='seq' else 2 if k in ('trip','pon') else 3 if k=='kan' else 0 for k,_ in ms)


def _special_name(allx):
    if all(x in TERMS for x in allx): return 'chin_yao',20
    if all(x in GREEN for x in allx): return 'all_green',15
    if all(x in RED for x in allx): return 'super_red',10
    return None,0


def _ordinary_score(p,dec,dora,tsumo,rinshan):
    ms=list(dec)+list(p.m); allx=p.all(); base=_base_score(ms); bonus=0; y=[]
    if all(2<=num(x)<=8 for x in allx): y.append('tanyao'); bonus+=1
    if all(any(num(x) in (1,9) for x in ts) for _,ts in ms): y.append('chanta'); bonus+=2
    if p.closed and tsumo: y.append('menzen_tsumo'); bonus+=1
    if len({suit(x) for x in allx})==1: y.append('chinitsu'); bonus+=2
    seqs=[ts for k,ts in dec if k=='seq']
    if p.closed and len(seqs)>=2 and any(seqs[i]==seqs[j] for i in range(len(seqs)) for j in range(i+1,len(seqs))):
        y.append('iipeikou'); bonus+=1
    bonus += sum(x in RED for x in allx)
    bonus += sum(x==dora for x in allx)
    if rinshan: y.append('rinshan'); bonus+=2
    return base+bonus,y


def score(p,dora,tsumo=False,rinshan=False):
    decs=winparts(p)
    if not decs: return None
    special,sb=_special_name(p.all()); results=[]
    for dec in decs:
        ms=list(dec)+list(p.m); base=_base_score(ms)
        if special: results.append((base+sb,special,[]))
        else:
            s,y=_ordinary_score(p,dec,dora,tsumo,rinshan); results.append((s,None,y))
    return max(results,key=lambda x:x[0])


def tile_value(p,t):
    c=Counter(p.h); n=num(t); v=(c[t]-1)*2.0
    if 2<=n<=8: v+=0.35
    for d in (-2,-1,1,2):
        u=t+d
        if 0<=u<18 and suit(u)==suit(t) and u in c:
            v += 0.9 if abs(d)==1 else 0.25
    if n in (1,9): v-=0.15
    return v


def discard(p,r):
    vals=[(tile_value(p,t)+r.random()*0.08,t) for t in sorted(set(p.h))]
    return min(vals)[1]


def can_pon(p,t): return Counter(p.h)[t]>=2 and len(p.m)<2


def chi_options(p,t):
    if len(p.m)>=2: return []
    c=Counter(p.h); s,n=suit(t),num(t); out=[]
    for start in range(max(1,n-2),min(n,7)+1):
        q=[s*9+start-1+i for i in range(3)]
        if t not in q: continue
        need=Counter(q); need[t]-=1
        if all(c[x]>=v for x,v in need.items()): out.append(tuple(q))
    return out


def _remove(hand,tiles):
    for t in tiles: hand.remove(t)


def can_ankan(p):
    if len(p.m)>=2: return []
    return [t for t,v in Counter(p.h).items() if v==4]


def result(draws,method,e,calls,kans):
    return {'draws':draws,'method':method,'score':e[0] if e else 0,'yakuman':e[1] or '' if e else '','yaku':','.join(e[2]) if e else '','calls':calls,'kans':kans}


def play(minscore,r):
    deck=[t for t in T for _ in range(4)]; r.shuffle(deck)
    dora=deck.pop(); rinshan=[deck.pop() for _ in range(4)]; live=deck
    ps=[P() for _ in range(4)]
    for _ in range(7):
        for p in ps: p.h.append(live.pop())
    turn=0; rin_i=0; calls=kans=0

    for draw_no in range(1,40):
        if not live: break
        p=ps[turn]; p.h.append(live.pop())

        e=score(p,dora,tsumo=True)
        if e and e[0]>=minscore: return result(draw_no,'tsumo',e,calls,kans)

        # Ankan: remove four, expose as a kan, draw rinshan, then either win or discard.
        aks=can_ankan(p)
        if aks and rin_i<4:
            kt=aks[0]
            _remove(p.h,[kt]*4); p.m.append(('kan',(kt,kt,kt,kt))); kans+=1
            p.h.append(rinshan[rin_i]); rin_i+=1
            e=score(p,dora,tsumo=True,rinshan=True)
            if e and e[0]>=minscore: return result(draw_no,'tsumo',e,calls,kans)

        q=discard(p,r); p.h.remove(q); p.d.append(q); p.f.add(q)

        # Ron priority. A discarded tile never remains in the winner's hand.
        rons=[]
        for j,o in enumerate(ps):
            if j==turn or q in o.f: continue
            o.h.append(q); e=score(o,dora,tsumo=False); o.h.pop()
            if e and e[0]>=minscore: rons.append((j,e))
        if rons:
            return result(draw_no,'ron',rons[0][1],calls,kans)

        # Pon priority over chi. A call always consumes the discard and immediately discards one tile.
        pon=[j for j,o in enumerate(ps) if j!=turn and can_pon(o,q)]
        if pon and r.random()<0.16:
            caller=r.choice(pon); o=ps[caller]
            _remove(o.h,[q,q]); o.m.append(('pon',(q,q,q))); o.closed=False; calls+=1
            q2=discard(o,r); o.h.remove(q2); o.d.append(q2); o.f.add(q2); turn=caller; continue

        left=(turn+1)%4; opts=chi_options(ps[left],q)
        if opts and r.random()<0.10:
            o=ps[left]; seq=r.choice(opts); need=list(seq); need.remove(q)
            _remove(o.h,need); o.m.append(('seq',seq)); o.closed=False; calls+=1
            q2=discard(o,r); o.h.remove(q2); o.d.append(q2); o.f.add(q2); turn=left; continue

        turn=(turn+1)%4

    return result(39,'draw',None,calls,kans)


def run(n,minscore,seed):
    r=random.Random(seed); rows=[play(minscore,r) for _ in range(n)]; wins=[x for x in rows if x['method']!='draw']
    return {'games':n,'min_score':minscore,'win_rate':len(wins)/n,'draw_rate':sum(x['method']=='draw' for x in rows)/n,'ron_rate':sum(x['method']=='ron' for x in wins)/len(wins) if wins else 0,'tsumo_rate':sum(x['method']=='tsumo' for x in wins)/len(wins) if wins else 0,'avg_score':statistics.mean(x['score'] for x in wins) if wins else 0,'avg_end_draw':statistics.mean(x['draws'] for x in rows),'call_rate':sum(x['calls']>0 for x in rows)/n,'kan_rate':sum(x['kans']>0 for x in rows)/n,'super_red':sum(x['yakuman']=='super_red' for x in rows)/n,'all_green':sum(x['yakuman']=='all_green' for x in rows)/n,'chin_yao':sum(x['yakuman']=='chin_yao' for x in rows)/n},rows


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--games',type=int,default=10000); ap.add_argument('--seed',type=int,default=20261017); ap.add_argument('--out',default='results'); a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
    summaries=[]
    for minimum in (4,5):
        summary,rows=run(a.games,minimum,a.seed); summaries.append(summary)
        with open(f'{a.out}/hands_min{minimum}.csv','w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
    with open(f'{a.out}/summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=summaries[0]); w.writeheader(); w.writerows(summaries)
    for s in summaries: print(s)
