from simulator import *

def mk(hand,melds=None,closed=True):
    p=P();p.h=list(hand);p.m=melds or [];p.closed=closed;return p

def test_tile_set_is_72_and_red_is_40():
    deck=[t for t in T for _ in range(4)]
    assert len(deck)==72
    assert sum(t in RED for t in deck)==40

def test_basic_win_two_sequences_and_pair():
    p=mk([0,1,2,9,10,11,4,4])
    assert winparts(p) is not None
    assert score(p,0)[0]>=0

def test_all_green_definition_excludes_7_sou():
    p=mk([10,11,12,10,11,12,16,16])
    assert score(p,0)[1]=='all_green'
    p2=mk([15,10,11,10,11,12,16,16])
    assert score(p2,0)[1]!='all_green'

def test_chin_yao_is_terminals_only():
    p=mk([0,0,0,17,17,17,8,8])
    assert score(p,0)[1]=='chin_yao'

def test_chanta_requires_every_meld_and_pair_to_touch_19():
    p=mk([1,2,3,6,7,8,0,0])
    assert 'chanta' not in score(p,0)[2]
    p=mk([0,1,2,6,7,8,8,8])
    assert 'chanta' in score(p,0)[2]

def test_iipeikou_same_suit_only():
    p=mk([0,1,2,0,1,2,4,4])
    assert 'iipeikou' in score(p,0)[2]
    p=mk([0,1,2,9,10,11,4,4])
    assert 'iipeikou' not in score(p,0)[2]
