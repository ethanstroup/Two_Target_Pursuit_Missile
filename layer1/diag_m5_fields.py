"""
diag_m5_fields.py -- report-only diagnostics for M5 field checks 5, 6 and 9.

  ordering   where V_RA < V_1 (exact in the continuum: V_RA >= V_1), how deep, and
             what is near those nodes (inner face, target-set kinks, the obstacle)
  topology   where each component of W_1 & Omega sits, and whether the components
             join when the R >= 0.45 mask or the target-set exclusion is relaxed

Usage:  python3 diag_m5_fields.py <grid tag, e.g. 101x102> [T]
"""

import sys

import numpy as np

import test_m5 as TM
import sim_m5 as SIM


def load(tag, T):
    V_ra, diag = TM.load_ra('%s_T%g' % (tag, T))
    V1, _, _ = TM.load_single(tag, T)
    return V_ra, V1, diag['cell'], SIM.Geom(V_ra.shape)


def ordering_report(V_ra, V1, cell, geom):
    Rg, P1, P2, l1, l2 = TM.node_ells(geom)
    d = V1 - V_ra
    m = Rg >= TM.R_MARGIN
    print('ORDERING  V_RA >= V_1 (continuum identity), masked nodes:')
    for thr in (0.0, 1e-6, 0.01 * cell, 0.1 * cell):
        print('   nodes with V_1 - V_RA > %.2e : %d' % (thr, int(np.count_nonzero((d > thr) & m))))
    flip = (V_ra <= 0) & (V1 > 0) & m
    worst = np.argsort(-(d * m).ravel())[:12]
    print('   worst 12 nodes (R, phi1 deg, phi2 deg, V_1, V_RA, ell_1, ell_2, -ell_2 - V_RA):')
    for i in worst:
        ix = np.unravel_index(i, d.shape)
        print('     R=%6.3f p1=%8.2f p2=%8.2f  V1=%+.4f VRA=%+.4f  l1=%+.4f l2=%+.4f  obst-VRA=%+.4f'
              % (Rg[ix], np.degrees(P1[ix]), np.degrees(P2[ix]), V1[ix], V_ra[ix], l1[ix], l2[ix],
                 -l2[ix] - V_ra[ix]))
    print('   sign flips (W_1 but V_1 > 0): %d' % int(flip.sum()))
    for ix in zip(*np.nonzero(flip)):
        print('     R=%6.3f p1=%8.2f p2=%8.2f  V1=%+.4f VRA=%+.4f  l1=%+.4f l2=%+.4f'
              % (Rg[ix], np.degrees(P1[ix]), np.degrees(P2[ix]), V1[ix], V_ra[ix], l1[ix], l2[ix]))


def describe(mask, Rg, P1, P2):
    R, a, b = Rg[mask], np.degrees(P1[mask]), np.degrees(P2[mask])
    return ('n=%6d  R [%.2f, %.2f]  phi1 [%+.0f, %+.0f]  phi2 [%+.0f, %+.0f]  mean (%.2f, %+.0f, %+.0f)'
            % (mask.sum(), R.min(), R.max(), a.min(), a.max(), b.min(), b.max(), R.mean(), a.mean(), b.mean()))


def topology_report(V_ra, cell, geom):
    Rg, P1, P2, l1, l2 = TM.node_ells(geom)
    W1 = V_ra <= 0
    variants = [
        ('Omega (as scored)', W1 & (Rg >= TM.R_MARGIN) & (l1 > 0) & (l2 > 0)),
        ('no R mask, targets excluded', W1 & (l1 > 0) & (l2 > 0)),
        ('R mask, T_1\' included', W1 & (Rg >= TM.R_MARGIN) & (l2 > 0)),
        ('no R mask, T_1\' included', W1 & (l2 > 0)),
    ]
    tot = int(((Rg >= TM.R_MARGIN) & (l1 > 0) & (l2 > 0)).sum())
    for name, mask in variants:
        lab, n = TM.label_periodic(mask, False)
        keep, sizes = TM.significant_components(lab, n, tot)
        sym = TM.symmetry_classes(lab, keep)
        print('TOPOLOGY  %-30s %d significant components' % (name, len(keep)))
        for c in keep:
            print('     comp %d  Rf-> %-9s %s' % (c, sym[c], describe(lab == c, Rg, P1, P2)))


def main():
    tag = sys.argv[1]
    T = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    V_ra, V1, cell, geom = load(tag, T)
    print('=' * 100)
    print('M5 field diagnostics  %s  T=%g  delta=%.4f' % (tag, T, cell))
    print('=' * 100)
    ordering_report(V_ra, V1, cell, geom)
    print()
    topology_report(V_ra, cell, geom)


if __name__ == '__main__':
    main()
