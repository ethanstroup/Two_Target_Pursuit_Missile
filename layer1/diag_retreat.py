"""
diag_retreat.py -- report-only, after check 13.

Check 13's starts have V_2 > 0: in the single-target game where player 2 pursues,
player 1 can keep out of T_{2->1}.  If player 1 retreats with that evader law,
player 2 should not be able to kill him (and there is no mutual kill, since that needs
player 1 inside T_{2->1}).  Together with check 13 (player 2 can always stop a win
alone), that makes these states a draw when both play their guarantees.

Player 1's retreat law is the maximizer's law of the mirror game,
    sigma_1 = +sign(dV_2/dphi_1),   dV_2/dphi_1 (x) = dV_1/dphi_2 (Sx),
read at the remaining horizon from M3's snapshots (capped at their last horizon).

Usage:  python3 diag_retreat.py [grid tag] [T]
"""

import sys

import numpy as np

import sim_m5 as SIM
import test_m5 as TM
import converse_m5 as CV


def law_retreat_p1(stack_v1, T):
    def law(x, t, ids):
        r = min(T - t, stack_v1.taus[-1])
        g = SIM.interp(stack_v1.geom, stack_v1.d2[stack_v1.nearest(r)], SIM.swapped(x))
        return SIM.finite_or_zero(SIM.sign_max(g), g)
    return law


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else '201x204'
    T = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    V_ra, d = TM.load_ra('%s_T%g' % (tag, T))
    V1, t1, _ = TM.load_single(tag, T)
    geom, cell = SIM.Geom(V_ra.shape), d['cell']
    starts = CV.draw_starts(CV.converse_pool(V_ra, V1, TM.omega(geom), cell))
    x0 = geom.node_states(starts)
    s_ra = SIM.SnapshotStack(geom, TM.load_snaps('%s/VRAsnap_%s_T%g.npz' % (TM.OUT, tag, T)))
    s_v1 = SIM.SnapshotStack(geom, TM.load_snaps('%s/Vsnap_%s_T6.npz' % (TM.M3, tag)))
    p2 = TM.player2_laws(s_ra, s_v1, t1, T, len(starts) * len(TM.P2_NAMES))
    oc = CV.outcome_table(x0, law_retreat_p1(s_v1, T), p2, T)
    print('Retreat diagnostic on %s, the %d check-13 starts, horizon %g' % (tag, len(starts), T))
    CV.print_table('retreat law +sign(dV_2/dphi_1)', oc)
    bad = int(np.sum((oc == SIM.LOSS) | (oc == SIM.MUTUAL)))
    print('player 1 killed (alone or mutual) in %d of %d runs' % (bad, oc.size))


if __name__ == '__main__':
    main()
