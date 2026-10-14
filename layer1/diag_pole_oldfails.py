"""
diag_pole_oldfails.py -- report only (added after V1-V4 ran; not pre-registered).

Every inner-face failure of smoke check 3 seen so far, re-flown on the 61 x 62^2 pole grid:
    R_min = 0.2, T = 4  (m5_out/diag_check3.log)                         2 starts
    R_min = 0.1, T = 4  (m5_out/rmin0.1/diag_check3_rmin0.1_T4_T6.log)   6 starts
    R_min = 0.1, T = 6  (same log, inner-face exits only)                 4 starts
For each: the pole grid's value at the start, and the outcome with player 1 on the pole grid's
law (sigma_2 == 0) integrated two ways, (a) reduced + pole.stepper and (b) exact inertial arcs.

Usage:  python diag_pole_oldfails.py
"""

import numpy as np

import ell as E
import pole
import inertial as IN
import sim_m5 as SIM
import verify_pole as VP

D = np.pi / 180
OLD_FAILS = {
    4.0: [('R_min 0.2', 0.5933, 1.5201 / D, -1.1148 / D),
          ('R_min 0.2', 0.5933, -0.1013 / D, 0.3040 / D),
          ('R_min 0.1', 0.695, -69.68, 63.87),
          ('R_min 0.1', 0.497, 23.23, -34.84),
          ('R_min 0.1', 0.695, -75.48, 58.06),
          ('R_min 0.1', 0.497, -69.68, 69.68),
          ('R_min 0.1', 0.497, -5.81, 17.42),
          ('R_min 0.1', 1.092, -46.45, 63.87)],
    6.0: [('R_min 0.1', 0.497, 11.61, -29.03),
          ('R_min 0.1', 1.092, -58.06, 69.68),
          ('R_min 0.1', 1.092, -75.48, 75.48),
          ('R_min 0.1', 2.678, -46.45, 58.06)],
}


def snap_angle(deg, n_phi):
    """The grid angle nearest to deg (the logged angles are node angles rounded to 0.01 deg)."""
    d = 2 * np.pi / n_phi
    return -np.pi + np.rint((deg * D + np.pi) / d) * d


def run(T):
    grid, V, snaps = VP.frozen_p2_pole(T)
    geom = pole.geom(grid)
    cell = E.value_scale(grid)
    rows = OLD_FAILS[T]
    x0 = np.array([[R, snap_angle(a, VP.N_PHI), snap_angle(b, VP.N_PHI)] for _, R, a, b in rows])
    v = SIM.interp(geom, V, x0)
    stack = SIM.SnapshotStack(geom, snaps, keep=(1,))
    law1, law2 = SIM.law_value_p1(stack, T), SIM.law_zero()
    a = SIM.rollout(x0, law1, law2, T, stepper=pole.stepper, exit_lo=-np.inf)
    b = IN.rollout(x0, law1, law2, T)
    print('-' * 96)
    print('T = %g   (pole delta %.4f)' % (T, cell))
    print('   failed on    R      phi1     phi2    pole V    (a) reduced+pole        (b) exact inertial     min R (b)')
    for i, (src, R, _, _) in enumerate(rows):
        print('   %-9s  %6.3f  %+7.2f  %+7.2f   %+7.3f   %-13s t=%5.3f   %-13s t=%5.3f   %6.3f'
              % (src, R, x0[i, 1] / D, x0[i, 2] / D, v[i],
                 SIM.OUTCOME_NAMES[a['outcome'][i]], a['t_end'][i],
                 SIM.OUTCOME_NAMES[b['outcome'][i]], b['t_end'][i], b['r_min'][i]))
    return int(np.sum(b['outcome'] == SIM.WIN)), len(rows)


def main():
    print('=' * 96)
    print('Old inner-face check 3 failures, re-flown on the 61 x 62^2 pole grid (sigma_2 == 0)')
    print('=' * 96)
    tot = [run(T) for T in (4.0, 6.0)]
    print('=' * 96)
    print('exact-frame wins: %d of %d' % (sum(w for w, _ in tot), sum(n for _, n in tot)))


if __name__ == '__main__':
    main()
