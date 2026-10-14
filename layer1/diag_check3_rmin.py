"""
diag_check3_rmin.py -- smoke check 3 at a chosen inner face, without editing any module.

Reproduces smoke_m5.check_3 exactly (61 x 62^2, T = 4, seed 0, 500 starts from
V <= -delta in Omega, player 1 on the grid law, sigma_2 == 0) at R_min = 0.1, two ways:

  consistent   grid, start geometry, interpolation and exit test all at R_min = 0.1
  hji only     the grid at 0.1, but sim_m5 left at its 0.2 default (start states,
               interpolation and the exit test still assume 0.2)

and lists every non-win: start state, V there, outcome, end state, exit face.

Usage:  python diag_check3_rmin.py [R_min] [T]        (defaults 0.1 and 4)
"""

import sys

import numpy as np

import hji
import ell as E
import sim_m5 as SIM
import smoke_m5 as SM

T = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
N_R, N_PHI = 61, 62


def solve_frozen_p2(R_min):
    grid = hji.make_grid(n_R=N_R, n_phi=N_PHI, R_min=R_min)
    V, snaps, _ = SM.solve(grid, hji.FrozenEvader(), T, snap_every=0.25)
    return grid, V, snaps


def run_check3(grid, V, snaps, geom_R_min, exit_R_min):
    cell = E.value_scale(grid)
    geom = SIM.Geom((N_R, N_PHI, N_PHI), R_min=geom_R_min)
    cand = np.nonzero(((V <= -cell) & SM.omega_mask(grid)).ravel())[0]
    pick = np.random.default_rng(0).choice(cand, size=min(500, cand.size), replace=False)
    x0 = geom.node_states(pick)
    stack = SIM.SnapshotStack(geom, snaps, keep=(1,))
    keep = SIM.R_LO_DOM
    SIM.R_LO_DOM = exit_R_min
    try:
        res = SIM.rollout(x0, SIM.law_value_p1(stack, T), SIM.law_zero(), T)
    finally:
        SIM.R_LO_DOM = keep
    return cell, cand, pick, x0, res


def report(label, grid, V, cell, cand, pick, x0, res):
    R_nodes = np.asarray(grid.coordinate_vectors[0])
    print('-' * 96)
    print('%s:  delta %.4f, pool %d, first masked R row %.3f'
          % (label, cell, cand.size, R_nodes[R_nodes >= 0.45][0]))
    print('   outcomes: %s' % SIM.summarize(res['outcome']))
    true_R = np.asarray(grid.states[..., 0]).ravel()[pick]
    print('   start R used vs true node R: max offset %.4f' % np.abs(x0[:, 0] - true_R).max())
    bad = np.nonzero(res['outcome'] != SIM.WIN)[0]
    for b in bad:
        xe = res['x_end'][b]
        face = 'R_min' if xe[0] < 1.0 else ('R_max' if xe[0] > 11 else '-')
        print('   start (R %.3f, p1 %+7.2f, p2 %+7.2f)  V %+.3f  -> %-14s t=%.3f  end R %.3f  %s'
              % (x0[b, 0], np.degrees(x0[b, 1]), np.degrees(x0[b, 2]), V.ravel()[pick[b]],
                 SIM.OUTCOME_NAMES[res['outcome'][b]], res['t_end'][b], xe[0],
                 face if res['outcome'][b] == SIM.EXIT else ''))


def main():
    R_min = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
    print('=' * 96)
    print('Smoke check 3 at R_min = %g, T = %g' % (R_min, T))
    print('=' * 96)
    grid, V, snaps = solve_frozen_p2(R_min)
    for label, g_R, e_R in (('consistent (everything at %g)' % R_min, R_min, R_min),
                            ('hji only (sim_m5 left at 0.2)', 0.2, 0.2)):
        report(label, grid, V, *run_check3(grid, V, snaps, g_R, e_R))


if __name__ == '__main__':
    main()
