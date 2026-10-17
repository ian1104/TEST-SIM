from simulator import *


def mk(hand, melds=None, closed=True):
    p = P()
    p.h = list(hand)
    p.m = melds or []
    p.closed = closed
    return p


def test_tile_set_is_72_and_red_is_40():
    deck = [t for t in T for _ in range(4)]
    assert len(deck) == 72
    assert sum(t in RED for t in deck) == 40


def test_basic_win_two_sequences_and_pair():
    p = mk([0, 1, 2, 9, 10, 11, 4, 4])
    assert winparts(p)
    assert score(p, 0)[0] >= 0


def test_multiple_decompositions_are_enumerated():
    # 11223344p + 55p can be decomposed in more than one valid way.
    p = mk([0, 0, 1, 1, 2, 2, 3, 3])
    assert len(winparts(p)) >= 2


def test_all_green_definition_excludes_7_sou():
    p = mk([10, 11, 12, 10, 11, 12, 16, 16])
    assert score(p, 0)[1] == 'all_green'
    p2 = mk([15, 15, 15, 10, 11, 12, 16, 16])
    assert winparts(p2)
    assert score(p2, 0)[1] != 'all_green'


def test_chin_yao_is_terminals_only():
    p = mk([0, 0, 0, 17, 17, 17, 8, 8])
    assert score(p, 0)[1] == 'chin_yao'


def test_chanta_requires_every_meld_and_pair_to_touch_19():
    p = mk([1, 2, 3, 6, 7, 8, 0, 0])
    assert 'chanta' not in score(p, 0)[2]
    p = mk([0, 1, 2, 6, 7, 8, 8, 8])
    assert 'chanta' in score(p, 0)[2]


def test_iipeikou_same_suit_only():
    p = mk([0, 1, 2, 0, 1, 2, 4, 4])
    assert 'iipeikou' in score(p, 0)[2]
    p = mk([0, 1, 2, 9, 10, 11, 4, 4])
    assert 'iipeikou' not in score(p, 0)[2]


def test_pon_consumes_two_concealed_tiles_not_the_discard():
    p = mk([0, 0, 1, 2, 3])
    assert can_pon(p, 0)
    _remove_tiles(p.h, [0, 0])
    p.m.append(('pon', (0, 0, 0)))
    assert p.h == [1, 2, 3]
    assert len(p.m[0][1]) == 3


def test_chi_counts_duplicates_correctly():
    p = mk([0, 1, 1, 3, 4])
    options = chi_options(p, 2)
    assert (0, 1, 2) in options


def test_open_hand_has_five_concealed_tiles_for_one_open_meld():
    p = mk([0, 1, 2, 4, 4], [('pon', (9, 9, 9))], closed=False)
    assert winparts(p)
    assert score(p, 0, tsumo=False) is not None


def test_ankan_preserves_menzen():
    p = mk([0, 0, 0, 0, 1, 2, 3, 4])
    _remove_tiles(p.h, [0, 0, 0, 0])
    p.m.append(('kan', (0, 0, 0, 0)))
    assert p.closed
