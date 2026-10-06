"""
l0_traj.py -- regenerate Layer 0's 122 barrier trajectories for M4.

The seed families are exactly test_barrier.py's seeds_maxrange / seeds_minrange /
seeds_boresight; this module calls those rather than re-deriving them, so M4 is
tested against the same bundle Layer 0 verified and not a look-alike.
"""
import sys, os
import numpy as np
_L0 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'layer0')
sys.path.insert(0, _L0)
import barrier as B


def seeds():
    """The three BUP families, as test_barrier.py builds them."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('_tb', os.path.join(_L0, 'test_barrier.py'))
    # test_barrier.py runs its suite at import, so lift the seed functions by exec of
    # just their definitions rather than importing the module.
    src = open(os.path.join(_L0, 'test_barrier.py')).read()
    head = src.split("print('=' * 90)")[0]
    ns = {'np': np, 'B': B, 'D': np.pi / 180.0, 'FAILS': []}
    exec(compile(head, 'test_barrier_head', 'exec'), ns)
    return ns['seeds_maxrange']() + ns['seeds_minrange']() + ns['seeds_boresight']()


def trajectories(tau_max=6.0, dt=1e-3):
    """Integrate every seed retrograde.  Returns list of (family, dict)."""
    out = []
    for fam, y0 in seeds():
        tr = B.integrate_retrograde(y0, tau_max=tau_max, dt=dt)
        tr['family'] = fam
        out.append((fam, tr))
    return out


if __name__ == '__main__':
    s = seeds()
    from collections import Counter
    print('%d seeds: %s' % (len(s), dict(Counter(f for f, _ in s))))
    trs = trajectories()
    fi = max(t['fi_err'].max() for _, t in trs)
    hs = max(t['h_err'].max() for _, t in trs)
    nsw = sum(len(t['switches']) for _, t in trs)
    print('%d trajectories   max |FI-1| = %.2e   max |H*| = %.2e   %d switches'
          % (len(trs), fi, hs, nsw))
    print('retrograde lengths: min %.2f  mean %.2f  max %.2f'
          % (min(t['tau'][-1] for _, t in trs), np.mean([t['tau'][-1] for _, t in trs]),
             max(t['tau'][-1] for _, t in trs)))
