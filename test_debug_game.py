import subprocess
import sys


def test_debug_game_runs_and_reports_seed():
    p = subprocess.run(
        [sys.executable, 'debug_game.py', '--seed', '1', '--min-score', '5', '--max-turns', '5'],
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'SEED=1 MIN_SCORE=5' in p.stdout
    assert 'P1 START' in p.stdout
    assert 'TURN 1 P1 DRAW' in p.stdout
    assert ('ACTION DISCARD' in p.stdout) or ('WIN TSUMO' in p.stdout)
