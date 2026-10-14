"""
zone_structure.py -- structural read of the converged winning zone.

D&S Sec. 4 report that at these parameters each player's winning zone is
FIVE disconnected closed subregions (ProblemStatement Sec. 3.3).  Layer 0 could
not check that: it produced barrier trajectories, not an assembled surface, and
ProblemStatement Sec. 3.4 records the assembly as deliberately not done.  A
converged V makes the count a two-line measurement.

Connectivity must be computed with phi_1 and phi_2 PERIODIC.  Labelling the array
as a plain box would split any component that wraps the seam and inflate the count
-- which is exactly the sort of number that would look like agreement with the
paper for the wrong reason.

Usage:  python3 zone_structure.py [V.npy]
"""

import sys
import numpy as np
from scipy import ndimage

path = sys.argv[1] if len(sys.argv) > 1 else 'm3_out/V_101x100_T6.npy'
def _load(p):
    """Accept either V_<tag>.npy or the transferred m3_<tag>_fields.npz."""
    if p.endswith('.npz'):
        return np.load(p)['V'].astype(np.float64)
    return np.load(p)


V = _load(path)
inside = V <= 0

st = np.ones((3, 3, 3), bool)      # 26-connectivity


def label_periodic(mask):
    """Label with axes 1 and 2 periodic (R is not)."""
    lab, n = ndimage.label(mask, structure=st)
    # stitch components that meet across each periodic seam
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
        # a node on the low face touches the 8 neighbours around it on the high face
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


print('=' * 92)
print('Winning-zone structure   %s   %s' % (path, V.shape))
print('=' * 92)

lab_box, n_box = ndimage.label(inside, structure=st)
lab, n = label_periodic(inside)
print('   components ignoring periodicity : %d   <- the wrong number' % n_box)
print('   components with phi_1, phi_2 periodic : %d' % n)
print()

sizes = np.bincount(lab.ravel())[1:]
order = np.argsort(-sizes)
Rg = np.linspace(0.2, 12.0, V.shape[0])
n_phi = V.shape[1]
pg = -np.pi + np.arange(n_phi) * 2 * np.pi / n_phi
D = 180 / np.pi
print('   component   nodes    %% of zone    R range        phi_1 range (deg)   phi_2 range (deg)')
for k in order:
    c = k + 1
    m = lab == c
    idx = np.where(m)
    print('   %6d %9d %9.3f%%   [%.2f, %.2f]   [%7.1f, %6.1f]   [%7.1f, %6.1f]'
          % (c, sizes[k], 100 * sizes[k] / sizes.sum(),
             Rg[idx[0].min()], Rg[idx[0].max()],
             D * pg[idx[1].min()], D * pg[idx[1].max()],
             D * pg[idx[2].min()], D * pg[idx[2].max()]))
print()
big = int((sizes > 0.001 * sizes.sum()).sum())
print('   components holding > 0.1%% of the zone: %d' % big)
print('   D&S Sec. 4 report five disconnected subregions at these parameters.')

# ---------------------------------------------------------------------------
# Per-R sections.  D&S Fig. 13 is a section, not a solid, so the "five
# subregions" count is most likely a statement about a 2D slice.  Count them.
# ---------------------------------------------------------------------------
st2 = np.ones((3, 3), bool)


def label_periodic_2d(mask):
    lab, n = ndimage.label(mask, structure=st2)
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

    for ax in (0, 1):
        lo = np.take(lab, 0, axis=ax)
        hi = np.take(lab, lab.shape[ax] - 1, axis=ax)
        for d in (-1, 0, 1):
            other = np.roll(hi, d)
            m = (lo > 0) & (other > 0)
            for a, b in set(zip(lo[m].tolist(), other[m].tolist())):
                union(a, b)
    roots = sorted({find(i) for i in range(1, n + 1)})
    return len(roots)


print()
print('=' * 92)
print('Components of {V<=0} in the (phi_1, phi_2) plane, section by section in R')
print('=' * 92)
print('   R      area %%    components (periodic)   components (ignoring periodicity)')
for i in range(0, V.shape[0], 4):
    m = inside[i]
    if not m.any():
        continue
    npd = label_periodic_2d(m)
    nbx = ndimage.label(m, structure=st2)[1]
    print('   %5.2f  %7.3f%%          %3d                      %3d'
          % (Rg[i], 100 * m.mean(), npd, nbx))
