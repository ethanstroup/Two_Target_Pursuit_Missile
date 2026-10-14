"""
win_alone.py -- is D&S's "five disconnected subregions" the WIN-ALONE set?

The converged {V_1 <= 0} is connected (zone_structure.py).  D&S Sec. 4 report five
disconnected closed subregions.  The two are not the same object, and the
difference is the point rather than a discrepancy:

  * Layer 1 solves the UNCORRECTED single-target reach problem -- the same one
    Layer 0's barriers are seeded from, which Plan Sec. 6 records as "exactly right
    as ground truth for this layer".  {V_1 <= 0} is "player 1 can force a kill",
    said without reference to whether player 2 kills him too.
  * D&S's winning zone is the CORRECTED one, T_1' = T_1 \\ closure(T_2)
    (Appendix B), i.e. player 1 wins ALONE.

The nearest object Layer 1 can form without doing Layer 2's work is

    W_1 = {V_1 <= 0} \\ {V_2 <= 0},        V_2 = V_1 o S  (Plan Sec. 2.5, free)

"player 1 can guarantee a kill and player 2 cannot".  This is INDICATIVE, not the
Appendix B construction: the correction applies to the target set BEFORE solving,
so removing a set afterwards is not the same computation.  Reported as a structural
read of M3's output and a pointer for Layer 2, not as a reproduction of Fig. 13.
"""

import sys
import numpy as np
from scipy import ndimage

_p = sys.argv[1] if len(sys.argv) > 1 else 'm3_out/m3_201x204_T6_fields.npz'
# Accept either V_<tag>.npy as solve_m3.py writes it, or the m3_<tag>_fields.npz
# that travels over the device bridge (float32; sign of V preserved node for node).
V1 = np.load(_p)['V'].astype(np.float64) if _p.endswith('.npz') else np.load(_p)
V2 = np.swapaxes(V1, 1, 2)                      # V_2 = V_1 o S
st = np.ones((3, 3, 3), bool)


def label_periodic(mask):
    lab, n = ndimage.label(mask, structure=st)
    parent = np.arange(n + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for ax in (1, 2):
        lo = np.take(lab, 0, axis=ax)
        hi = np.take(lab, lab.shape[ax] - 1, axis=ax)
        for d0 in (-1, 0, 1):
            for d1 in (-1, 0, 1):
                other = np.roll(np.roll(hi, d0, axis=0), d1, axis=1)
                m = (lo > 0) & (other > 0)
                for a, b in set(zip(lo[m].tolist(), other[m].tolist())):
                    union(a, b)
    roots = np.array([find(i) for i in range(n + 1)])
    roots[0] = 0
    uniq = {r: i for i, r in enumerate(sorted(set(roots[1:].tolist())), start=1)}
    out = np.zeros_like(lab)
    for i in range(1, n + 1):
        out[lab == i] = uniq[roots[i]]
    return out, len(uniq)


# INNER-BOUNDARY MASK.  The extrapolation (outflow) condition at R = R_min sits
# right on the singular R -> 0 face (Plan Sec. 3, trap 2) and leaks a little: at
# 101x100 it produces two 23-node blobs of V just barely negative (|V| < 0.015,
# about 12% of one cell) at R = 0.200 and 0.318.  Forward simulation from them
# under the grid's own policy misses by min_ell = +0.41 to +0.54 -- they are not
# reachable states.  Left in, they would have made the win-alone component count
# come out at exactly D&S's five, which is the kind of agreement worth destroying
# on purpose.  R_MARGIN excludes the first few cells of the inner face; the target
# set cannot exist below R_lo,min = a - b = 0.25 in any case.
R_MARGIN = float(__import__('os').environ.get('R_MARGIN', '0.45'))
Rg = np.linspace(0.2, 12.0, V1.shape[0])
ok = (Rg >= R_MARGIN)[:, None, None]

w1 = (V1 <= 0) & (V2 > 0) & ok
both = (V1 <= 0) & (V2 <= 0) & ok
nphi = V1.shape[1]
pg = -np.pi + np.arange(nphi) * 2 * np.pi / nphi
D = 180 / np.pi

print('=' * 92)
print('Win-alone structure   %s' % (V1.shape,))
print('=' * 92)
print('   inner-boundary mask: R >= %.2f  (%d of %d R-planes kept)'
      % (R_MARGIN, int(ok.sum()), V1.shape[0]))
print('   {V_1 <= 0}            %8.4f%% of grid' % (100 * ((V1 <= 0) & ok).mean()))
print('   {V_2 <= 0}            %8.4f%% of grid  (transpose; equal by symmetry)'
      % (100 * ((V2 <= 0) & ok).mean()))
print('   both can kill         %8.4f%% of grid' % (100 * both.mean()))
print('   W_1 = win alone       %8.4f%% of grid' % (100 * w1.mean()))
print()

lab, n = label_periodic(w1)
sizes = np.bincount(lab.ravel())[1:]
order = np.argsort(-sizes)
print('   connected components of W_1 (phi periodic): %d' % n)
print('   comp     nodes    %% of W_1    R range        phi_1 (deg)         phi_2 (deg)')
for k in order[:12]:
    c = k + 1
    idx = np.where(lab == c)
    print('   %4d %9d %9.3f%%   [%.2f, %.2f]   [%7.1f, %6.1f]   [%7.1f, %6.1f]'
          % (c, sizes[k], 100 * sizes[k] / sizes.sum(),
             Rg[idx[0].min()], Rg[idx[0].max()],
             D * pg[idx[1].min()], D * pg[idx[1].max()],
             D * pg[idx[2].min()], D * pg[idx[2].max()]))
for thr in (0.01, 0.001, 0.0001):
    print('   components holding > %.3f%% of W_1: %d'
          % (100 * thr, int((sizes > thr * sizes.sum()).sum())))
print()
print('   D&S Sec. 4: five disconnected closed subregions, and mutual kill collapsing')
print('   to measure-zero surfaces |phi_1| = |phi_2| (their Eq. 87).')
mk = both.mean()
P1, P2 = np.meshgrid(pg, pg, indexing='ij')
diag = (np.abs(np.abs(P1) - np.abs(P2)) < 1.01 * (2 * np.pi / nphi))[None, :, :]
on_diag = np.count_nonzero(both & diag) / max(np.count_nonzero(both), 1)
print('   measured: "both can kill" is %.4f%% of grid, %.2f%% of it within one cell'
      % (100 * mk, 100 * on_diag))
print('   of |phi_1| = |phi_2|.')
