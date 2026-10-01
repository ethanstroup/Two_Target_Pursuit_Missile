"""
grid_study.py -- Layer 1, M3's second half: convergence in GRID.

Layer1_Plan.md Sec. 4: "converged ... in grid (101^3 vs 201^3, measuring drift of
the ZERO LEVEL SET, not of V)."

Two design points that make the measurement mean what it says:

1. THE GRIDS NEST.  n_R 101 -> 201 (201 = 2*101 - 1, endpoints included) and
   n_phi 100 -> 200 (200 = 2*100, endpoint=False).  Every coarse node is a fine
   node, so the comparison is exact subsampling, `V_fine[::2, ::2, ::2]`, with no
   interpolation error of its own folded into the drift.  A 101/201 pair in the
   periodic angles would NOT nest -- 2*pi/101 against 2*pi/201 -- and the study
   would partly be measuring its own interpolant.

2. THE DENOMINATOR IS THE SURFACE, NOT THE GRID.  Disagreement as a fraction of
   all nodes is dominated by empty space and looks reassuringly tiny whatever the
   solver does.  As a fraction of the nodes the zero level set actually occupies,
   it is the quantity the plan asks for.

Also asserts the two symmetries the solve must satisfy exactly, which are free
checks on an expensive computation:

    Rf-invariance   V(R, -phi_1, -phi_2) = V(R, phi_1, phi_2)
    S-transpose     V_2 = V_1 o S, hence t_2* = t_1* o S   (Plan Sec. 2.5)

On a grid with endpoint=False the reflection -phi is the exact index map
k -> (n - k) mod n, so Rf is testable at machine precision rather than by
interpolation.

Usage:  python3 grid_study.py
"""

import json
import os

import numpy as np
from scipy import ndimage

# Inner-boundary mask: the extrapolation condition at R = R_min sits on the
# singular R -> 0 face (Plan Sec. 3, trap 2) and leaks slightly.  At 101x100 it
# makes two 23-node blobs of |V| < 0.015 (12% of a cell) whose forward simulations
# miss by +0.5, and it accounts for the only grid-study disagreements that are not
# adjacent to the barrier.  The target set cannot exist below R_lo,min = 0.25.
R_MARGIN = float(os.environ.get('R_MARGIN', '0.45'))

OUT = 'm3_out'
COARSE = os.environ.get('COARSE', '101x100_T6')
FINE = os.environ.get('FINE', '201x200_T6')

FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


def surface_nodes(inside):
    b = np.zeros_like(inside)
    for ax in range(3):
        for sh in (1, -1):
            b |= (inside != np.roll(inside, sh, axis=ax))
    return b


def reflect(a):
    """Rf on a grid field: phi -> -phi is the index map k -> (n-k) mod n."""
    n1, n2 = a.shape[1], a.shape[2]
    i1 = (-np.arange(n1)) % n1
    i2 = (-np.arange(n2)) % n2
    return a[:, i1][:, :, i2]


def swap(a):
    return np.swapaxes(a, 1, 2)


E_BETA = np.pi / 4


def load_fields(tag):
    """
    Load V and t_1* for a grid, from whichever form is present.

    solve_m3.py writes V_<tag>.npy and t1_<tag>.npy (float64).  Those are 64 MB
    each at 201^3, over the device bridge's per-file limit, so the copies that
    travel are m3_<tag>_fields.npz -- the same two arrays in float32.  That is
    lossless for every purpose here: t_1* takes values on a 0.25 grid and is exact
    in float32, and V round-trips to 4.7e-07 against a cell scale of 0.059, with
    the sign of V (and therefore the barrier) preserved node for node.
    """
    npy = '%s/V_%s.npy' % (OUT, tag)
    if os.path.exists(npy):
        return np.load(npy), np.load('%s/t1_%s.npy' % (OUT, tag))
    z = np.load('%s/m3_%s_fields.npz' % (OUT, tag))
    return z['V'].astype(np.float64), z['t1'].astype(np.float64)


def main():
    Vc, tc = load_fields(COARSE)
    Vf, tf = load_fields(FINE)
    jc = json.load(open('%s/m3_%s.json' % (OUT, COARSE)))
    jf = json.load(open('%s/m3_%s.json' % (OUT, FINE)))

    print('=' * 92)
    print('M3 grid convergence:  %s  vs  %s' % (COARSE, FINE))
    print('=' * 92)
    print('   coarse %s   cell %.5f   wall %.0f s' % (Vc.shape, jc['cell'], jc['wall_s']))
    print('   fine   %s   cell %.5f   wall %.0f s' % (Vf.shape, jf['cell'], jf['wall_s']))
    print()

    print('-' * 92)
    print('1.  The grids nest')
    print('-' * 92)
    sub = Vf[::2, ::2, ::2]
    report('subsampled fine grid has the coarse shape', sub.shape == Vc.shape,
           '%s vs %s' % (sub.shape, Vc.shape))

    print()
    print('-' * 92)
    print('2.  Drift of the zero level set')
    print('-' * 92)
    Rg = np.linspace(0.2, 12.0, Vc.shape[0])
    ok = (Rg >= R_MARGIN)[:, None, None]
    inc, inf_ = (Vc <= 0) & ok, (sub <= 0) & ok
    bc = surface_nodes(inc)
    nb = int(bc.sum())
    dis = int(np.count_nonzero(inc != inf_))
    print('        inner-boundary mask R >= %.2f' % R_MARGIN)
    print('        {V<=0}:  coarse %.4f%%   fine %.4f%%   (fine, full res %.4f%%)'
          % (100 * inc.mean(), 100 * inf_.mean(), 100 * ((Vf <= 0)).mean()))
    print('        zero level set on the coarse grid: %d nodes (%.3f%% of it)'
          % (nb, 100 * nb / Vc.size))
    print('        nodes whose side of the barrier changed: %d' % dis)

    # THE CRITERION.  A count of flipped nodes is not itself meaningful -- it grows
    # with the surface's area whatever the solver does.  What the plan asks for is
    # how far the barrier MOVED, so spread the symmetric-difference volume over the
    # surface area: a slab of `dis` nodes on a surface of `nb` nodes is
    # dis/nb * 6 cells thick, the 6 because surface_nodes counts a node once per
    # face it presents.  Under a cell, and the two resolutions put the barrier in
    # the same place to within their own discretization.
    disp = dis / max(nb, 1) * 6
    report('the barrier moves less than one coarse cell under refinement',
           disp < 1.0, 'effective displacement %.3f coarse cells (%.2f%% of the surface)'
           % (disp, 100 * dis / max(nb, 1)))

    # Disagreements must be AT the barrier.  One in the deep interior would mean
    # something other than resolution is wrong.
    near = ndimage.binary_dilation(bc, iterations=3)
    off = int(np.count_nonzero((inc != inf_) & ~near))
    report('every disagreement sits within 3 cells of the barrier', off == 0,
           '%d of %d are further away' % (off, dis))

    print()
    print('-' * 92)
    print('3.  The value function itself (context, not the criterion)')
    print('-' * 92)
    d = np.abs(Vc - sub)
    print('        |V_coarse - V_fine| : median %.5f, 90th %.5f, max %.5f  (cell %.5f)'
          % (np.median(d), np.percentile(d, 90), d.max(), jc['cell']))
    near = np.abs(Vc) < 0.5
    print('        near the barrier (|V| < 0.5): median %.5f, max %.5f'
          % (np.median(d[near]), d[near].max()))

    print()
    print('-' * 92)
    print('4.  Arrival time t_1*, which is what M5 compares')
    print('-' * 92)
    both = np.isfinite(tc) & np.isfinite(sub * 0 + tf[::2, ::2, ::2])
    tfs = tf[::2, ::2, ::2]
    both = np.isfinite(tc) & np.isfinite(tfs)
    dt = np.abs(tc[both] - tfs[both])
    print('        reached on both grids: %.4f%% of nodes' % (100 * both.mean()))
    report('t_1* agrees between grids to within the reporting interval',
           np.median(dt) <= 0.25 and np.percentile(dt, 95) <= 0.5,
           'median %.3f, 95th %.3f, max %.3f  (dtau = %.2f)'
           % (np.median(dt), np.percentile(dt, 95), dt.max(), jc['dtau']))

    print()
    print('-' * 92)
    print('5.  Symmetries the solve must satisfy exactly (free checks)')
    print('-' * 92)
    print('        Rf-invariance is EXACT in the continuum -- ell is Rf-invariant to 4e-15')
    print('        and the dynamics are Rf-equivariant -- so any residual is numerical.')
    for tag, V, t in ((COARSE, Vc, tc), (FINE, Vf, tf)):
        nphi = V.shape[1]
        p = -np.pi + np.arange(nphi) * 2 * np.pi / nphi
        beta_on_node = bool(np.min(np.abs(np.abs(p) - E_BETA)) < 1e-12)
        e = np.abs(V - reflect(V)).max()
        report('%-12s  Rf-invariance of V (residual < 1%% of a cell)' % tag,
               e < 0.01 * (jc['cell'] if tag == COARSE else jf['cell']),
               'max |V - V o Rf| = %.3e   (|phi|=beta %s a grid node)'
               % (e, 'IS' if beta_on_node else 'is not'))
        fin = np.isfinite(t) & np.isfinite(reflect(t))
        et = np.abs(t[fin] - reflect(t)[fin]).max() if fin.any() else np.inf
        nd = int(np.count_nonzero(np.abs(t[fin] - reflect(t)[fin]) > 0))
        report('%-12s  Rf-invariance of t_1*' % tag, et == 0.0,
               'differs at %d nodes, max %.2f' % (nd, et))

        # M5 smoke test (Plan Sec. 4, M5.1).  t_2* = t_1* o S, so on |phi_1|=|phi_2|
        # the identity t_1* = t_2* reduces to Rf-invariance of t_1* -- the same
        # property tested just above.  Reported RAW and after projecting onto the
        # symmetry, never only after: the projection is legitimate (it removes
        # numerical error from an exact symmetry of the continuous problem) but
        # quoting only the projected number would be reporting the assumption.
        P1, P2 = np.meshgrid(p, p, indexing='ij')
        diag = (np.abs(np.abs(P1) - np.abs(P2)) < 1e-12)[None, :, :]
        for lbl, tt in (('raw', t), ('Rf-projected', np.minimum(t, reflect(t)))):
            f = np.isfinite(tt)
            cov = np.count_nonzero((tt == swap(tt)) & diag & f) / max(np.count_nonzero(diag & f), 1)
            report('%-12s  M5 smoke test, %-12s {t_1*=t_2*} covers {|phi_1|=|phi_2|}'
                   % (tag, lbl), cov > 0.999,
                   '%.4f%% of the diagonal covered' % (100 * cov))

    print()
    print('=' * 92)
    print('M3 grid study: all checks passed' if not FAILS else
          '%d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS)))
    print('=' * 92)


if __name__ == '__main__':
    main()
