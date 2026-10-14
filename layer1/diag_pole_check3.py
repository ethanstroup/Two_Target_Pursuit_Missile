"""
diag_pole_check3.py -- smoke check 3 with the pole condition at the inner face.

Same test as smoke_m5.check_3 (61 x 62^2, sigma_2 == 0, 500 starts from V <= -delta in
Omega, seed 0, player 1 on the grid law at the remaining horizon), but on pole.make_grid:
the extrapolation condition at R_min is replaced by the mirror identity through R = 0, and
rollouts pass through R = 0 instead of exiting.

At 61 rows the innermost real row sits at R = 0.0992, almost exactly where the R_min = 0.1
grid's edge is, so against `diag_check3_rmin.py 0.1 T` this changes only the inner-face
treatment.

Also reports the construction checks: the dynamics' equivariance under the flip, the ghost
rows after the solve, and reflection symmetry on the real rows.

Usage:  python diag_pole_check3.py [T]        (default 4)
"""

import sys

import numpy as np

import hji
import ell as E
import pole
import reach_avoid as RA
import sim_m5 as SIM

T = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
N_R, N_PHI = 61, 62
R_MASK = 0.45


def reflect(a):
    n = a.shape[1]
    i = (-np.arange(n)) % n
    return a[:, i][:, :, i]


def solve(grid):
    ell1, ell2 = RA.ell1_on_grid(grid), RA.ell2_on_grid(grid)
    ss = pole.reach_avoid_settings(ell2)
    V0 = pole.fill(RA.initial_value(ell1, ell2))
    V, _, taus, _, _, snaps, wall = RA.march(grid, hji.FrozenEvader(), ss, V0, T, log=lambda s: None)
    return V, snaps, wall


def omega(grid):
    R = np.asarray(grid.states[..., 0])
    return (R >= R_MASK) & (np.asarray(RA.ell1_on_grid(grid)) > 0) & (np.asarray(RA.ell2_on_grid(grid)) > 0)


def main():
    grid = pole.make_grid(N_R, N_PHI)
    Rv = np.asarray(grid.coordinate_vectors[0])
    cell = E.value_scale(grid)
    print('=' * 96)
    print('Smoke check 3 with the pole condition   %d real rows x %d^2   T = %g' % (N_R, N_PHI, T))
    print('   dR = %.4f; ghost rows at R = %s; innermost real row R = %.4f; delta = %.4f'
          % (Rv[1] - Rv[0], np.round(Rv[:pole.N_GHOST], 4).tolist(), Rv[pole.N_GHOST], cell))
    print('=' * 96)
    print('   dynamics equivariance under the flip: max rel. residual %.2e' % pole.dynamics_equivariance())

    V, snaps, wall = solve(grid)
    real = pole.strip(V)
    print('   solve %.0f s;  ghost residual after solve %.2e;  max |V - V o Rf| on real rows %.2e'
          % (wall, pole.ghost_residual(V), np.abs(real - reflect(real)).max()))

    geom = pole.geom(grid)
    cand = np.nonzero(((V <= -cell) & omega(grid)).ravel())[0]
    pick = np.random.default_rng(0).choice(cand, size=min(500, cand.size), replace=False)
    x0 = geom.node_states(pick)
    stack = SIM.SnapshotStack(geom, snaps, keep=(1,))
    res = SIM.rollout(x0, SIM.law_value_p1(stack, T), SIM.law_zero(), T,
                      stepper=pole.stepper, exit_lo=-np.inf)
    oc = res['outcome']
    print('-' * 96)
    print('   pool %d (V <= -delta in Omega, R >= %.2f); 500 drawn' % (cand.size, R_MASK))
    print('   outcomes: %s' % SIM.summarize(oc))
    near = res['r_min'] < 0.25
    print('   runs that came inside R = 0.25 at some step end: %d (of which won: %d)'
          % (near.sum(), int(np.sum(near & (oc == SIM.WIN)))))
    for b in np.nonzero(oc != SIM.WIN)[0]:
        xe = res['x_end'][b]
        print('   start (R %.3f, p1 %+7.2f, p2 %+7.2f)  V %+.3f  -> %-14s t=%.3f  end R %.3f  min R %.3f'
              % (x0[b, 0], np.degrees(x0[b, 1]), np.degrees(x0[b, 2]), V.ravel()[pick[b]],
                 SIM.OUTCOME_NAMES[oc[b]], res['t_end'][b], xe[0], res['r_min'][b]))
    print('=' * 96)


if __name__ == '__main__':
    main()
