"""
diag_pole_rerun.py -- report-only diagnostics for the M5 rerun on pole grids (2026-10-15).

Not pre-registered.  Reads the float32 field files only, so it runs in a minute or two.

  reflection   check 4: where |V - V o Rf| lives, row by row, and inside Omega / near the zero set
  ordering     check 5: where V_1 > V_RA, and whether any sign flips
  overlap      check 6: where W_1 & W_2 and W_1 & D sit
  contested    what C is made of, where it sits, erosion thickness (as diag_m5_partition.py)
  topology     check 9 with the R mask / target exclusion relaxed (as diag_m5_fields.py)
  check8       the six old far-flip states on the pole grids
  near face    W_1 share of Omega at 0.45 <= R < 1, every grid
  old vs pole  fine pole vs old fine (R_min = 0.2), sign disagreements by R band

Usage (from layer1/M5):
    python diag/diag_pole_rerun.py [pole_dir] [old_dir]
defaults: m5_out/m5_out_V1_pole  m5_out/m5_out_V0
"""

import os
import sys

import numpy as np
from scipy import ndimage

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', '..', 'common'))

import ell as E

R_MASK = 0.45
R_MAX = 12.0
R_MIN_OLD = 0.2


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def angles(n_phi):
    return -np.pi + np.arange(n_phi) * 2 * np.pi / n_phi


def load_pole(d, tag):
    """Real rows (R > 0) of a pole fields file: V, R, phi."""
    z = np.load(os.path.join(d, 'm5_%s_fields.npz' % tag))
    R = z['R']
    i0 = int(np.searchsorted(R, 0.0))
    return z['V'][i0:].astype(np.float64), R[i0:], z['phi1']


def load_old(d, tag):
    """An R_min = 0.2 fields file: rows at linspace(0.2, 12, n_R)."""
    V = np.load(os.path.join(d, 'm5_%s_fields.npz' % tag))['V'].astype(np.float64)
    return V, np.linspace(R_MIN_OLD, R_MAX, V.shape[0]), angles(V.shape[1])


def cell_of(d, tag):
    import json
    return json.load(open(os.path.join(d, 'm5_%s.json' % tag)))['cell']


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------

def mesh(R, phi):
    Rg, P1, P2 = np.meshgrid(R, phi, phi, indexing='ij')
    return Rg, P1, P2, E.ell(Rg, P1, P2), E.ell(Rg, P2, P1)


def omega(Rg, l1, l2):
    return (Rg >= R_MASK) & (l1 > 0) & (l2 > 0)


def swap(a):
    return np.swapaxes(a, 1, 2)


def reflect(a):
    n = a.shape[1]
    k = (-np.arange(n)) % n
    return a[:, k][:, :, k]


def surface(inside):
    b = np.zeros_like(inside)
    for ax in range(3):
        for sh in (1, -1):
            b |= inside != np.roll(inside, sh, axis=ax)
    return b


def interp_R(V, R_src, R_dst):
    """Linear in R, angles unchanged; R_dst clipped to the source range."""
    i = np.clip(np.searchsorted(R_src, R_dst, side='right') - 1, 0, len(R_src) - 2)
    w = np.clip((R_dst - R_src[i]) / (R_src[i + 1] - R_src[i]), 0.0, 1.0)[:, None, None]
    return (1 - w) * V[i] + w * V[i + 1]


def label_periodic(mask):
    """Face-connected components, periodic in both angles (as test_m5.label_periodic)."""
    lab, n = ndimage.label(mask)
    parent = np.arange(n + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for ax in (1, 2):
        lo, hi = np.take(lab, 0, axis=ax), np.take(lab, lab.shape[ax] - 1, axis=ax)
        m = (lo > 0) & (hi > 0)
        for a, b in set(zip(lo[m].tolist(), hi[m].tolist())):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    roots = np.array([find(i) for i in range(n + 1)])
    uniq = {r: i for i, r in enumerate(sorted(set(roots[1:].tolist())), start=1)}
    remap = np.zeros(n + 1, int)
    for i in range(1, n + 1):
        remap[i] = uniq[roots[i]]
    return remap[lab], len(uniq)


def deg(a):
    return np.degrees(a)


def rule(c='-'):
    print(c * 96)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def reflection_report(V, R, phi, cell, l1, l2, om, name):
    d = np.abs(V - reflect(V))
    rowmax = d.reshape(len(R), -1).max(1)
    print('%s: max |V - V o Rf| = %.3e = %.4f delta;  nodes above 0.01 delta: %d'
          % (name, d.max(), d.max() / cell, int((d > 0.01 * cell).sum())))
    print('   by row:  ' + '  '.join('R=%.3f %.1e' % (R[i], rowmax[i]) for i in range(6)))
    Rg = np.broadcast_to(R[:, None, None], V.shape)
    for label, m in (('R >= 0.45', Rg >= R_MASK), ('Omega', om),
                     ('|V| < 2 delta', np.abs(V) < 2 * cell)):
        print('   over %-14s max %.3e = %.4f delta;  above 0.01 delta: %d'
              % (label, d[m].max(), d[m].max() / cell, int((d[m] > 0.01 * cell).sum())))
    i, j, k = np.unravel_index(int(np.argmax(d)), d.shape)
    print('   worst node R=%.3f phi1=%+.2f phi2=%+.2f  V=%+.4f  ell_1=%+.3f ell_2=%+.3f'
          % (R[i], deg(phi[j]), deg(phi[k]), V[i, j, k], l1[i, j, k], l2[i, j, k]))
    big = (d > 0.01 * cell) & (Rg >= R_MASK)
    if big.any():
        ii = np.nonzero(big)
        print('   above 0.01 delta at R >= 0.45: R %s, |phi1| %.1f-%.1f, |phi2| <= %.1f, V %+.3f to %+.3f'
              % (sorted(set(np.round(R[ii[0]], 3).tolist())), deg(np.abs(phi[ii[1]])).min(),
                 deg(np.abs(phi[ii[1]])).max(), deg(np.abs(phi[ii[2]])).max(), V[big].min(), V[big].max()))
    print('   W_1 vs W_1 o Rf: %d nodes differ' % int(((V <= 0) != reflect(V <= 0)).sum()))


def ordering_report(V_ra, V1, R, phi, cell, l1, l2, name):
    d = V1 - V_ra
    Rg = np.broadcast_to(R[:, None, None], V_ra.shape)
    m = Rg >= R_MASK
    om = m & (l1 > 0) & (l2 > 0)
    print('%s: max (V_1 - V_RA) at R >= 0.45 = %.3e = %.3f delta;  in Omega %.3f delta'
          % (name, d[m].max(), d[m].max() / cell, d[om].max() / cell))
    for thr in (0.01 * cell, 0.1 * cell):
        print('   nodes with V_1 - V_RA > %.1e: %d (in Omega %d)'
              % (thr, int(((d > thr) & m).sum()), int(((d > thr) & om).sum())))
    i, j, k = np.unravel_index(int(np.argmax(np.where(m, d, -np.inf))), d.shape)
    print('   worst node R=%.3f phi1=%+.2f phi2=%+.2f  V_1=%+.4f V_RA=%+.4f  ell_1=%+.4f ell_2=%+.4f'
          % (R[i], deg(phi[j]), deg(phi[k]), V1[i, j, k], V_ra[i, j, k], l1[i, j, k], l2[i, j, k]))
    print('   inside T_2->1 (ell_2 <= 0): %s' % (l2[i, j, k] <= 0))
    print('   sign flips (W_1 but V_1 > 0), R >= 0.45: %d' % int(((V_ra <= 0) & (V1 > 0) & m).sum()))


def overlap_report(W1, W2, D, V_ra, V1, om, Rg, P1, P2, cell, dphi, name):
    o = W1 & W2 & om
    gap = np.abs(np.abs(P1) - np.abs(P2)) / dphi
    print('%s: W_1 & W_2: %d nodes' % (name, int(o.sum())))
    if o.any():
        print('   exactly on |phi_1| = |phi_2|: %d;  |V_RA|/delta median %.2e max %.2e;  '
              '|phi_1| %.1f-%.1f deg, R %.2f-%.2f'
              % (int((gap[o] < 1e-9).sum()), np.median(np.abs(V_ra[o])) / cell, np.abs(V_ra[o]).max() / cell,
                 deg(np.abs(P1[o])).min(), deg(np.abs(P1[o])).max(), Rg[o].min(), Rg[o].max()))
    o = W1 & D & om
    print('   W_1 & D: %d nodes' % int(o.sum()))


def contested_report(V_ra, V1, W1, C, om, Rg, P1, P2, cell, name):
    V2 = swap(V1)
    a = C & (V1 <= 0) & (V2 > 0)
    b = C & (V1 > 0) & (V2 <= 0)
    c = C & (V1 <= 0) & (V2 <= 0)
    n = max(int(C.sum()), 1)
    print('%s: C %d nodes (%.4f%% of Omega);  player-1 half %.1f%%, player-2 half %.1f%%, both %.1f%%'
          % (name, n, 100 * n / om.sum(), 100 * a.sum() / n, 100 * b.sum() / n, 100 * c.sum() / n))
    old_minus_new = (V1 <= 0) & (V2 > 0) & om & ~W1
    print('   old win-alone set minus W_1: %.1f%% of it inside C' % (100 * (C & old_minus_new).sum()
                                                                     / max(old_minus_new.sum(), 1)))
    print('   R of C: 10th %.2f median %.2f 90th %.2f;  V_RA/delta on C: median %.2f 90th %.2f'
          % (np.percentile(Rg[C], 10), np.median(Rg[C]), np.percentile(Rg[C], 90),
             np.median(V_ra[C]) / cell, np.percentile(V_ra[C], 90) / cell))
    lab, nl = label_periodic(a)
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    m, layers = a.copy(), 0
    while m.any() and layers < 40:
        m = ndimage.binary_erosion(m)
        layers += 1
    print('   player-1 half: %d components, largest %s;  erosions (6-neighbour, non-periodic) to empty: %d'
          % (nl, sizes[:4].tolist(), layers))


def topology_report(W1, Rg, l1, l2, P1, total, name):
    variants = (('Omega (as scored)', W1 & (Rg >= R_MASK) & (l1 > 0) & (l2 > 0)),
                ('no R mask, targets excluded', W1 & (l1 > 0) & (l2 > 0)),
                ("R mask, T_1' included", W1 & (Rg >= R_MASK) & (l2 > 0)))
    for label, mask in variants:
        lab, n = label_periodic(mask)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)[1:]
        keep = [i + 1 for i in np.argsort(-sizes) if sizes[i] > 1e-4 * total]
        rl = reflect(lab)
        desc = []
        for c in keep:
            img = rl[lab == c]
            img = img[img > 0]
            t = int(np.bincount(img).argmax()) if img.size else -1
            desc.append('%d%s' % (sizes[c - 1], ' inv' if t == c else ''))
        print('%s %-30s %d components: %s' % (name, label, len(keep), ', '.join(desc)))


def check8_states(Vc, Rc, Vf, Rf, phic, phif):
    """The six far flips of the original check 8 (Layer1_M5_2026-10-11.md Sec. 4.4)."""
    pts = ((-24.71, 28.24), (24.71, -28.24), (-21.18, 24.71), (21.18, -24.71),
           (-17.65, 21.18), (17.65, -21.18))
    old = {24.71: (0.1828, -0.0363), 21.18: (0.2240, -0.0196), 17.65: (0.2741, -0.0066)}

    def at(V, R, phi, a1, a2):
        j = int(np.argmin(np.abs(np.angle(np.exp(1j * (phi - np.radians(a1)))))))
        k = int(np.argmin(np.abs(np.angle(np.exp(1j * (phi - np.radians(a2)))))))
        return float(interp_R(V[:, j:j + 1, k:k + 1], R, np.array([0.554]))[0, 0, 0])

    print('   R=0.554    phi1     phi2    old coarse  old fine   pole coarse  pole fine')
    for a1, a2 in pts:
        oc, of = old[abs(a1)]
        print('            %+7.2f  %+7.2f    %+.4f    %+.4f     %+.4f      %+.4f'
              % (a1, a2, oc, of, at(Vc, Rc, phic, a1, a2), at(Vf, Rf, phif, a1, a2)))


def near_face_share(V, R, phi):
    Rg, P1, P2, l1, l2 = mesh(R, phi)
    m = omega(Rg, l1, l2) & (Rg < 1.0)
    return 100 * float(np.mean(V[m] <= 0)), int(m.sum())


def old_vs_pole(Vo, Ro, Vp, Rp, phi, cell):
    """Old fine interpolated in R onto the pole rows (angles coincide), as V3 did on the coarse grid."""
    m = Rp >= R_MASK
    A = interp_R(Vo, Ro, Rp[m]) <= 0
    B = Vp[m] <= 0
    near = ndimage.binary_dilation(surface(A), iterations=2) | ndimage.binary_dilation(surface(B), iterations=2)
    dis = A != B
    Rr = Rp[m]
    print('   R band          nodes     disagree   far (>2 cells from either zero set)')
    for lo, hi in ((0.45, 1), (1, 2), (2, 4), (4, 12.01)):
        b = ((Rr >= lo) & (Rr < hi))[:, None, None]
        bb = np.broadcast_to(b, A.shape)
        print('   [%5.2f, %5.2f)  %9d   %7d    %d' % (lo, hi, int(bb.sum()), int((dis & bb).sum()),
                                                     int((dis & ~near & bb).sum())))
    far = dis & ~near
    if far.any():
        ii = np.nonzero(far)
        print('   far disagreements at R %s' % sorted(set(np.round(Rr[ii[0]], 3).tolist())))
        Bv = Vp[m]
        Av = interp_R(Vo, Ro, Rp[m])
        for i, j, k in list(zip(*ii))[:12]:
            print('      R=%.3f phi1=%+.2f phi2=%+.2f  old %+.4f  pole %+.4f'
                  % (Rr[i], deg(phi[j]), deg(phi[k]), Av[i, j, k], Bv[i, j, k]))
    Rg, P1, P2, l1, l2 = mesh(Rr, phi)
    om = omega(Rg, l1, l2)
    print('   W_1 share of Omega: old %.4f%%  pole %.4f%%  (both on the pole rows)'
          % (100 * (A & om).sum() / om.sum(), 100 * (B & om).sum() / om.sum()))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def field_reports(pdir, tag, name):
    V_ra, R, phi = load_pole(pdir, '%s_T6_pole' % tag)
    V1, _, _ = load_pole(pdir, '%s_T6_single_pole' % tag)
    cell = cell_of(pdir, '%s_T6_pole' % tag)
    Rg, P1, P2, l1, l2 = mesh(R, phi)
    om = omega(Rg, l1, l2)
    W1 = V_ra <= 0
    W2 = swap(W1)
    D = (V1 > 0) & (swap(V1) > 0)
    C = om & ~(W1 | W2 | D)
    rule()
    print('%s  %s   delta %.5f   Omega %d nodes' % (name, tag, cell, int(om.sum())))
    rule()
    reflection_report(V_ra, R, phi, cell, l1, l2, om, 'check 4  V_RA')
    reflection_report(V1, R, phi, cell, l1, l2, om, 'check 4  V_1 ')
    ordering_report(V_ra, V1, R, phi, cell, l1, l2, 'check 5')
    overlap_report(W1, W2, D, V_ra, V1, om, Rg, P1, P2, cell, 2 * np.pi / len(phi), 'check 6')
    contested_report(V_ra, V1, W1, C, om, Rg, P1, P2, cell, 'contested')
    topology_report(W1, Rg, l1, l2, P1, int(om.sum()), 'check 9')
    return V_ra, R, phi


def main():
    pdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join('m5_out', 'm5_out_V1_pole')
    odir = sys.argv[2] if len(sys.argv) > 2 else os.path.join('m5_out', 'm5_out_V0')
    rule('=')
    print('M5 pole rerun: report-only field diagnostics   pole %s   old %s' % (pdir, odir))
    rule('=')
    Vf, Rf, phif = field_reports(pdir, '201x204', 'fine')
    Vc, Rc, phic = field_reports(pdir, '101x102', 'coarse')
    V51, R51, phi51 = load_pole(pdir, '51x52_T6_pole')
    rule()
    print('Check 8: the six old far-flip states')
    check8_states(Vc, Rc, Vf, Rf, phic, phif)
    rule()
    print('W_1 share of Omega at 0.45 <= R < 1')
    rows = [('pole 51x52', V51, R51, phi51), ('pole 101x102', Vc, Rc, phic), ('pole 201x204', Vf, Rf, phif)]
    have_old = os.path.exists(os.path.join(odir, 'm5_201x204_T6_fields.npz'))
    if have_old:
        Voc, Roc, phioc = load_old(odir, '101x102_T6')
        Vof, Rof, phiof = load_old(odir, '201x204_T6')
        rows += [('old 101x102', Voc, Roc, phioc), ('old 201x204', Vof, Rof, phiof)]
    for label, V, R, phi in rows:
        s, n = near_face_share(V, R, phi)
        print('   %-14s %7.3f%% of %d nodes' % (label, s, n))
    if have_old:
        rule()
        print('Old fine (R_min = 0.2) vs pole fine, V_RA, interpolated onto the pole rows')
        old_vs_pole(Vof, Rof, Vf, Rf, phif, cell_of(pdir, '201x204_T6_pole'))
    rule('=')


if __name__ == '__main__':
    main()
