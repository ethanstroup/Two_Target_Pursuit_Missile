"""
diag_m5_partition.py -- report-only diagnostics for M5 checks 6 and 8 and for the
contested set, on the fine grid against the coarse one.

  overlap     where W_1 & W_2 and W_1 & D sit, and how close |V| is to zero there
  far flips   the check-8 disagreements more than 3 coarse cells from the barrier
  contested   what C is made of: which single-target guarantees hold on it, how it
              relates to M3's old "win-alone" set, where it sits, how thick it is

Usage:  python3 diag_m5_partition.py [T]
"""

import sys

import numpy as np
from scipy import ndimage

import test_m5 as TM
import sim_m5 as SIM


def load(tag, T):
    V_ra, diag = TM.load_ra('%s_T%g' % (tag, T))
    V1, _, _ = TM.load_single(tag, T)
    geom = SIM.Geom(V_ra.shape)
    return V_ra, V1, diag['cell'], geom


def deg(a):
    return np.degrees(a)


def overlap_report(V_ra, V1, cell, geom):
    Rg, P1, P2, l1, l2 = TM.node_ells(geom)
    om = (Rg >= TM.R_MARGIN) & (l1 > 0) & (l2 > 0)
    W1, W2, D, C = TM.partition(V_ra, V1, om)
    o = W1 & W2 & om
    gap = np.abs(np.abs(P1) - np.abs(P2)) / geom.dphi
    print('W_1 & W_2: %d nodes' % o.sum())
    if o.any():
        print('   ||phi_1| - |phi_2|| in cells: max %.2f;  on the diagonal exactly: %d'
              % (gap[o].max(), int(np.count_nonzero(gap[o] < 1e-9))))
        print('   |V_RA|/delta there: median %.2e  max %.2e' % (np.median(np.abs(V_ra[o])) / cell,
                                                             np.abs(V_ra[o]).max() / cell))
        print('   |phi_1| range %.1f-%.1f deg, R range %.2f-%.2f'
              % (deg(np.abs(P1[o])).min(), deg(np.abs(P1[o])).max(), Rg[o].min(), Rg[o].max()))
    o = W1 & D & om
    print('W_1 & D: %d nodes;  |V_RA|/delta max %.2e, V_1/delta max %.2e'
          % (o.sum(), (np.abs(V_ra[o]).max() / cell) if o.any() else 0, (V1[o].max() / cell) if o.any() else 0))
    return W1, W2, D, C, om, Rg, P1, P2, l1, l2


def far_flip_report(Vc, Vf, geom_c):
    Rg, P1, P2, _, _ = TM.node_ells(geom_c)
    sub = Vf[::2, ::2, ::2]
    ok = Rg >= TM.R_MARGIN
    inc, inf_ = (Vc <= 0) & ok, (sub <= 0) & ok
    near = ndimage.binary_dilation(TM.surface_mask(inc), iterations=3)
    far = (inc != inf_) & ~near
    print('check-8 flips beyond 3 coarse cells: %d' % far.sum())
    for ix in zip(*np.nonzero(far)):
        print('   R=%6.3f p1=%8.2f p2=%8.2f  V_coarse=%+.4f  V_fine=%+.4f'
              % (Rg[ix], deg(P1[ix]), deg(P2[ix]), Vc[ix], sub[ix]))


def contested_report(V_ra, V1, cell, geom, W1, C, om, Rg, P1, P2):
    V2 = TM.swap(V1)
    tot = om.sum()
    a = C & (V1 <= 0) & (V2 > 0)
    b = C & (V1 > 0) & (V2 <= 0)
    c = C & (V1 <= 0) & (V2 <= 0)
    print('contested C: %d nodes (%.4f%% of Omega)' % (C.sum(), 100 * C.sum() / tot))
    print('   player 1 alone can force a kill (V_1<=0<V_2): %.1f%%' % (100 * a.sum() / C.sum()))
    print('   player 2 alone can force a kill (V_2<=0<V_1): %.1f%%' % (100 * b.sum() / C.sum()))
    print('   both can force a kill:                         %.1f%%' % (100 * c.sum() / C.sum()))
    old = (V1 <= 0) & (V2 > 0) & om
    old_minus_new = old & ~W1
    print('   C & (old win-alone set minus W_1): %.1f%% of C;  that difference is %.1f%% inside C'
          % (100 * (C & old_minus_new).sum() / C.sum(), 100 * (C & old_minus_new).sum() / max(old_minus_new.sum(), 1)))
    print('   R distribution of C: 10th %.2f, median %.2f, 90th %.2f;  share at R < 0.8: %.1f%%'
          % (np.percentile(Rg[C], 10), np.median(Rg[C]), np.percentile(Rg[C], 90),
             100 * np.mean(Rg[C] < 0.8)))
    print('   V_RA/delta on C: median %.2f, 90th %.2f, max %.2f'
          % (np.median(V_ra[C]) / cell, np.percentile(V_ra[C], 90) / cell, V_ra[C].max() / cell))
    lab, n = TM.label_periodic(C & a, False)
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    print('   components of the player-1 half (a): %d; largest %s' % (n, sizes[:6].tolist()))
    # thickness: how many erosion layers before the player-1 half disappears
    m, layers = (C & a).copy(), 0
    while m.any() and layers < 40:
        m = ndimage.binary_erosion(m)
        layers += 1
    print('   erosions (6-neighbour, non-periodic) to empty the player-1 half: %d' % layers)


def main():
    T = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print('=' * 100)
    print('M5 partition diagnostics, T = %g' % T)
    print('=' * 100)
    for tag in ('201x204', '101x102'):
        V_ra, V1, cell, geom = load(tag, T)
        print('-' * 100)
        print('%s   delta %.4f' % (tag, cell))
        print('-' * 100)
        W1, W2, D, C, om, Rg, P1, P2, l1, l2 = overlap_report(V_ra, V1, cell, geom)
        contested_report(V_ra, V1, cell, geom, W1, C, om, Rg, P1, P2)
    print('-' * 100)
    Vc, _, _, geom_c = load('101x102', T)
    Vf, _, _, _ = load('201x204', T)
    far_flip_report(Vc, Vf, geom_c)


if __name__ == '__main__':
    main()
