"""
diag_table3_misses.py -- report only (added 2026-10-28, after test_e_table3.py was scored; not
pre-registered).

Looks at test E's misses on the fine pole grid:
  * the S_1 U_1 samples one by one: on the barrier?  on Z_1?  how far from Z_1 & barrier?
  * for each missed (point, player): the offset to the nearest Z_p & barrier node, in cells
  * hits and nulls at hit radii 1-4 (the scored radius is 2)

Usage (from layer1/M4):  python diag/diag_table3_misses.py [pole output dir]
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..')))

import test_e_table3 as TE          # noqa: E402

DEG = TE.DEG


def nearest_offset(ZB, node, rmax=12):
    """(di, dj, dk) to a nearest Z & barrier node in Chebyshev distance, or None."""
    i, j, k = node
    n0, n1, n2 = ZB.shape
    for r in range(rmax + 1):
        best = None
        for di in range(-r, r + 1):
            ii = i + di
            if ii < 0 or ii >= n0:
                continue
            for dj in range(-r, r + 1):
                for dk in range(-r, r + 1):
                    if max(abs(di), abs(dj), abs(dk)) != r:
                        continue
                    if ZB[ii, (j + dj) % n1, (k + dk) % n2]:
                        cand = (di, dj, dk)
                        if best is None or sum(map(abs, cand)) < sum(map(abs, best)):
                            best = cand
        if best is not None:
            return best
    return None


def line_report(g, X, sc):
    TE.header('S_1 U_1, sample by sample (fine grid; scored samples only)')
    print('   t-index   R      phi1    phi2      V/delta   on Z_1   cells to Z_1 & barrier')
    for n, x in enumerate(X):
        if not sc[n]:
            continue
        node = TE.nearest_node(g['R'], g['phi'], x)
        v = TE.interp_value(g['V'], g['R'], g['phi'], x)
        print('   %3d    %6.3f  %7.2f  %7.2f   %+6.2f    %-5s    %d'
              % (n, x[0], x[1] * DEG, x[2] * DEG, v / g['delta'], bool(g['D'][1][node]),
                 TE.cells_to(g['ZB'][1], node)))


def miss_report(g, pts, pairs):
    TE.header('Offsets of the missed pairs to their nearest Z_p & barrier node (cells: dR, dphi1, dphi2)')
    for n, p in sorted(pairs, key=lambda t: pts[t[0]][0]):
        node = TE.nearest_node(g['R'], g['phi'], pts[n])
        if g['D'][p][node]:
            continue
        off = nearest_offset(g['ZB'][p], node)
        print('   %-5s %-8s offset %s   (%.3f in R, %.1f deg, %.1f deg)'
              % (n, 'pursuer' if p == 1 else 'evader', off,
                 off[0] * (g['R'][1] - g['R'][0]), off[1] * 360 / len(g['phi']), off[2] * 360 / len(g['phi'])))


def radius_report(g, pts, pairs):
    TE.header('Hits and nulls at hit radius 1-4 (scored radius 2)')
    for r in (1, 2, 3, 4):
        D = {p: TE.dilate(g['ZB'][p], r) for p in (1, 2)}
        p0 = {p: TE.null_rate(D[p], g['V'], g['Rg'], g['l1'], g['delta'])[0] for p in (1, 2)}
        hits = [bool(D[p][TE.nearest_node(g['R'], g['phi'], pts[n])]) for n, p in pairs]
        tail = TE.poisson_binomial_tail([p0[p] for _, p in pairs], int(sum(hits)))
        print('   r = %d:  %d of %d hits;  null p0 pursuer %.3f, evader %.3f;  P(>= hits | null) = %.1e'
              % (r, sum(hits), len(hits), p0[1], p0[2], tail))


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'M5', 'm5_out', 'm5_out_V1_pole')
    pts = TE.T3.points()
    g = TE.build(d, '201x204_T6_single_pole')
    pairs = sorted(TE.PRE_REGISTERED)
    X, _, _ = TE.s1u1_samples()
    sc = TE.E.ell(X[:, 0], X[:, 1], X[:, 2]) >= TE.OFF_TARGET * g['delta']
    print('=' * 100)
    print('Test E against Table 3: report-only look at the misses (not pre-registered)')
    print('=' * 100)
    line_report(g, X, sc)
    miss_report(g, pts, pairs)
    radius_report(g, pts, pairs)
    print('=' * 100)


if __name__ == '__main__':
    main()
