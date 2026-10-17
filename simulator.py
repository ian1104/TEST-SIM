from __future__ import annotations
import argparse,csv,os,random,statistics
from collections import Counter

T=range(18)
RED={0,2,4,5,6,8,9,13,15,17}
GREEN={10,11,12,14,16}
TERMS={0,8,9,17}

def num(t): return t%9+1
def suit(t): return t//9

def parts(tiles,need):
    c=Counter(tiles)
    if len(tiles)!=need*3+2:return None
    def f(c,m,p,out):
        if m==0 and p==0:return out
        t=next((x for x,v in c.items() if v),None)
        if t is None:return None
        if p and c[t]>=2:
            c[t]-=2;r=f(c,m,0,out+[('pair',(t,t))]);c[t]+=2
            if r:return r
        if m and c[t]>=3:
            c[t]-=3;r=f(c,m-1,p,out+[('trip',(t,t,t))]);c[t]+=3
            if r:return r
        if m and num(t)<=7:
            a,b=t+1,t+2
            if suit(a)==suit(t)==suit(b) and c[a] and c[b]:
                c[t]-=1;c[a]-=1;c[b]-=1;r=f(c,m-1,p,out+[('seq',(t,a,b))]);c[t]+=1;c[a]+=1;c[b]+=1
                if r:return r
        return None
    return f(c,need,1,[])

class P:
    def __init__(self):self.h=[];self.m=[];self.d=[];self.f=set();self.closed=True
    def all(self):return self.h+[x for _,ts in self.m for x in ts]

def winparts(p):
    n=2-len(p.m)
    if n<0:return None
    return parts(p.h,n)

def score(p,dora,tsumo=False,rinshan=False):
    dec=winparts(p)
    if dec is None:return None
    ms=dec+[(k,ts) for k,ts in p.m]
    allx=p.all();base=sum(1 if k=='seq' else 2 if k in ('trip','pon') else 3 for k,ts in ms)
    # Special hands suppress ordinary bonuses.
    if all(x in RED for x in allx):return (base+10,'super_red',[])
    if all(x in GREEN for x in allx):return (base+15,'all_green',[])
    if all(x in TERMS for x in allx):return (base+20,'chin_yao',[])
    y=[];b=0
    if all(2<=num(x)<=8 for x in allx):y.append('tanyao');b+=1
    if all(num(x) in (1,9) for _,ts in ms for x in ts):y.append('chanta');b+=2
    if p.closed and tsumo:y.append('menzen_tsumo');b+=1
    if len({suit(x) for x in allx})==1:y.append('chinitsu');b+=2
    seq=[ts for k,ts in dec if k=='seq']
    if p.closed and len(seq)>=2 and seq[0]==seq[1]:y.append('iipeikou');b+=1
    red=sum(x in RED for x in allx);dr=sum(x==dora for x in allx)
    b+=red+dr
    if rinshan:y.append('rinshan');b+=2
    return base+b,None,y

def discard(p,r):
    c=Counter(p.h);best=None;bv=-99
    for t in set(p.h):
        v=(c[t]-1)*1.8
        n=num(t)
        if 2<=n<=8:v+=.5
        for d in (-2,-1,1,2):
            u=t+d
            if 0<=u<18 and suit(u)==suit(t) and u in c:v+=.65 if abs(d)==1 else .2
        if n in (1,9):v-=.2
        v+=r.random()*.12
        if v>bv:bv=v;best=t
    return best

def can_pon(p,t):return Counter(p.h)[t]>=2 and len(p.m)<2

def can_chi(p,t):
    if len(p.m)>=2:return False
    s=suit(t);n=num(t)
    for st in range(max(1,n-2),min(n,7)+1):
        q=[s*9+st-1+i for i in range(3)]
        if t in q and all(x==t or x in p.h for x in q):return q
    return None

def play(minscore,r):
    deck=[t for t in T for _ in range(4)];r.shuffle(deck)
    dora=deck.pop();rin=deck[-4:];live=deck[:-4]
    ps=[P() for _ in range(4)]
    for _ in range(7):
        for p in ps:p.h.append(live.pop())
    turn=0;ri=0;calls=kans=0
    for draws in range(1,80):
        if not live:break
        p=ps[turn];x=live.pop();p.h.append(x)
        e=score(p,dora,True,False)
        if e and e[0]>=minscore:return result(draws,'tsumo',e,calls,kans)
        # concealed kan
        c=Counter(p.h);kt=next((t for t,v in c.items() if v==4 and len(p.m)<2 and ri<4),None)
        if kt is not None:
            for _ in range(4):p.h.remove(kt)
            p.m.append(('kan',(kt,kt,kt,kt)));kans+=1
            x=rin[ri];ri+=1;p.h.append(x)
            e=score(p,dora,True,True)
            if e and e[0]>=minscore:return result(draws,'tsumo',e,calls,kans)
        q=discard(p,r);p.h.remove(q);p.d.append(q);p.f.add(q)
        # Ron has priority over calls.
        rons=[]
        for j,o in enumerate(ps):
            if j==turn or q in o.f:continue
            o.h.append(q);e=score(o,dora,False,False);o.h.pop()
            if e and e[0]>=minscore:rons.append(e)
        if rons:return result(draws,'ron',rons[0],calls,kans)
        # Simple stochastic calls. Pon is checked before chi.
        caller=None;meld=None
        for j,o in enumerate(ps):
            if j!=turn and can_pon(o,q) and r.random()<.16:caller=j;meld=('trip',(q,q,q));break
        if caller is None:
            j=(turn+1)%4;o=ps[j];seq=can_chi(o,q)
            if seq and r.random()<.10:
                for x2 in seq:
                    if x2!=q:o.h.remove(x2)
                caller=j;meld=('seq',tuple(seq))
        if caller is not None:
            o=ps[caller]
            if meld[0]=='trip':o.h.remove(q);o.h.remove(q)
            o.m.append(meld);o.closed=False;calls+=1
            e=score(o,dora,False,False)
            if e and e[0]>=minscore:return result(draws,'ron',e,calls,kans)
            q2=discard(o,r);o.h.remove(q2);o.d.append(q2);o.f.add(q2);turn=caller
        else:turn=(turn+1)%4
    return result(draws,'draw',None,calls,kans)

def result(draws,method,e,calls,kans):
    return {'draws':draws,'method':method,'score':e[0] if e else 0,'yakuman':e[1] if e else '', 'yaku':','.join(e[2]) if e else '', 'calls':calls,'kans':kans}

def run(n,m,seed):
    r=random.Random(seed);rows=[play(m,r) for _ in range(n)];w=[x for x in rows if x['method']!='draw']
    return {'games':n,'min_score':m,'win_rate':len(w)/n,'draw_rate':sum(x['method']=='draw' for x in rows)/n,'ron_rate':sum(x['method']=='ron' for x in w)/len(w) if w else 0,'tsumo_rate':sum(x['method']=='tsumo' for x in w)/len(w) if w else 0,'avg_score':statistics.mean(x['score'] for x in w) if w else 0,'avg_end_draw':statistics.mean(x['draws'] for x in rows),'call_rate':sum(x['calls']>0 for x in rows)/n,'kan_rate':sum(x['kans']>0 for x in rows)/n,'super_red':sum(x['yakuman']=='super_red' for x in rows)/n,'all_green':sum(x['yakuman']=='all_green' for x in rows)/n,'chin_yao':sum(x['yakuman']=='chin_yao' for x in rows)/n},rows

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--games',type=int,default=10000);ap.add_argument('--seed',type=int,default=20261017);ap.add_argument('--out',default='results');a=ap.parse_args();os.makedirs(a.out,exist_ok=True)
    ss=[]
    for m in (4,5):
        s,rows=run(a.games,m,a.seed);ss.append(s)
        with open(f'{a.out}/hands_min{m}.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    with open(f'{a.out}/summary.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=ss[0]);w.writeheader();w.writerows(ss)
    for s in ss:print(s)
