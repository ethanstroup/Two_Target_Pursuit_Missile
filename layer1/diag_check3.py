"""
diag_check3.py -- diagnosis of the two check-3 rollouts at 61 x 62^2 that left the
R domain instead of winning.  Reproduces smoke_m5.check_3 exactly (same solve, same
seed), then reports where those starts are, how they exit, and how the same starts
fare under a 101 x 102^2 solve.

Usage:  python3 diag_check3.py
"""

import numpy as np

import hji
import ell as E
import reach_avoid as RA
import sim_m5 as SIM
import smoke_m5 as SM

T = 4.0


def frozen_p2_solve(n_R, n_phi):
    grid = hji.make_grid(n_R=n_R, n_phi=n_phi)
    V, snaps, wall = SM.solve(grid, hji.FrozenEvader(), T, snap_every=0.25)
    return grid, SIM.Geom((n_R, n_phi, n_phi)), V, snaps


def trace(x0, stack, T, dt=2e-3):
    """Single-trajectory trace under the grid law, for printing."""
    law = SIM.law_value_p1(stack, T)
    x = np.array([x0], float)
    rows = []
    for n in range(int(round(T / dt))):
        t = n * dt
        s1 = law(x, t, None)
        if n % 100 == 0:
            rows.append((t, *x[0], s1[0], float(SIM.ell1(x)[0]), float(SIM.ell2(x)[0])))
        x = SIM.rk4(x, s1, np.zeros(1), dt)
        if not (SIM.R_LO_DOM < x[0, 0] < SIM.R_HI_DOM) or SIM.ell1(x)[0] <= 0:
            rows.append((t + dt, *x[0], s1[0], float(SIM.ell1(x)[0]), float(SIM.ell2(x)[0])))
            break
    return rows


def main():
    grid, geom, V, snaps = frozen_p2_solve(61, 62)
    cell = E.value_scale(grid)
    cand = np.nonzero(((V <= -cell) & SM.omega_mask(grid)).ravel())[0]
    pick = np.random.default_rng(0).choice(cand, size=500, replace=False)
    x0 = geom.node_states(pick)
    stack = SIM.SnapshotStack(geom, snaps, keep=(1,))
    res = SIM.rollout(x0, SIM.law_value_p1(stack, T), SIM.law_zero(), T)
    bad = np.nonzero(res['outcome'] != SIM.WIN)[0]
    print('61x62: delta %.4f, %d non-wins' % (cell, len(bad)))
    for b in bad:
        print('-' * 80)
        print('start %s  V_grid %.4f  outcome %s at t=%.3f, end state %s'
              % (np.round(x0[b], 4), V.ravel()[pick[b]], SIM.OUTCOME_NAMES[res['outcome'][b]],
                 res['t_end'][b], np.round(res['x_end'][b], 4)))
        for r in trace(x0[b], stack, T)[::2]:
            print('   t=%.2f  R=%.4f  p1=%+.4f  p2=%+.4f  s1=%+g  ell1=%+.4f  ell2=%+.4f' % r)

    print('=' * 80)
    print('Same starts, 101 x 102^2 solve')
    grid2, geom2, V2, snaps2 = frozen_p2_solve(101, 102)
    stack2 = SIM.SnapshotStack(geom2, snaps2, keep=(1,))
    v2 = SIM.interp(geom2, V2, x0[bad])
    res2 = SIM.rollout(x0[bad], SIM.law_value_p1(stack2, T), SIM.law_zero(), T)
    for i, b in enumerate(bad):
        print('start %s  V_101 %.4f (delta_101 %.4f)  outcome %s at t=%.3f'
              % (np.round(x0[b], 4), v2[i], E.value_scale(grid2),
                 SIM.OUTCOME_NAMES[res2['outcome'][i]], res2['t_end'][i]))


if __name__ == '__main__':
    main()
