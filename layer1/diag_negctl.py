"""
diag_negctl.py -- report-only: can the check-11 harness register a loss at all?

Check 12's heuristic player 1 won every coarse-grid run, so before reading that as
"the heuristic is good" the harness is run with player-1 laws that should lose:
coasting (sigma_1 = 0), turning away (+sign(phi_1)), and random bang-bang, against
the reach-avoid adversary and the trading player 2.  Also reports how deep the
starts sit (V_RA in delta units) and how the heuristic fares from shallow starts
(-delta < V_RA <= 0), which check 11 does not score.

Usage:  python3 diag_negctl.py [grid tag] [T]
"""

import sys

import numpy as np

import test_m5 as TM
import sim_m5 as SIM


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else '101x102'
    T = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    V_ra, diag = TM.load_ra('%s_T%g' % (tag, T))
    V1, t1, _ = TM.load_single(tag, T)
    geom, cell = SIM.Geom(V_ra.shape), diag['cell']
    om = TM.omega(geom)
    snaps_ra = TM.load_snaps('%s/VRAsnap_%s_T%g.npz' % (TM.OUT, tag, T))
    snaps_v1 = TM.load_snaps('%s/Vsnap_%s_T6.npz' % (TM.M3, tag))
    s_ra, s_v1 = SIM.SnapshotStack(geom, snaps_ra), SIM.SnapshotStack(geom, snaps_v1)
    rng = np.random.default_rng(7)

    deep = np.nonzero(((V_ra <= -cell) & om).ravel())[0]
    shallow = np.nonzero(((V_ra > -cell) & (V_ra <= 0) & om).ravel())[0]
    v = V_ra.ravel()[deep] / cell
    print('start depth V_RA/delta over the check-11 pool: median %.2f, 10th pct %.2f, 90th %.2f'
          % (np.median(v), np.percentile(v, 10), np.percentile(v, 90)))

    x_deep = geom.node_states(rng.choice(deep, 400, replace=False))
    x_shal = geom.node_states(rng.choice(shallow, min(400, shallow.size), replace=False))
    p2 = {'reach-avoid adversary': SIM.law_value_p2(s_ra, T),
          'trade (t_2*)': SIM.law_trade_p2(s_v1, t1)}
    p1 = {'coast (sigma_1=0)': SIM.law_zero(),
          'turn away (+sign phi_1)': lambda x, t, ids: np.sign(x[:, 1]),
          'random bang-bang': SIM.law_random(400, T, seed=99),
          'heuristic (-sign phi_1)': SIM.law_heuristic(1),
          'reach-avoid (grid law)': SIM.law_value_p1(s_ra, T)}
    for pool, x0 in (('deep starts (V_RA <= -delta)', x_deep), ('shallow starts (-delta < V_RA <= 0)', x_shal)):
        print('-' * 96)
        print(pool, len(x0))
        for n1, l1 in p1.items():
            for n2, l2 in p2.items():
                s = SIM.summarize(SIM.rollout(x0, l1, l2, T)['outcome'])
                print('   P1 %-26s vs %-22s win %4d  lose %4d  mutual %3d  none %3d  exit %3d'
                      % (n1, n2, s['win alone'], s['player-2 kill'], s['mutual kill'],
                         s['no kill'], s['exited domain']))


if __name__ == '__main__':
    main()
