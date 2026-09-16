"""
bup_curves.py -- ordered seed curves along the boundary of the usable part.

Integrating retrograde from the (BUP) needs more than a set of seed points: to
render the bundle as a *surface* rather than a pile of curves, the seeds must be
ordered along the boundary, so that neighbouring seeds are genuinely neighbours
on the barrier.  Sweeping phi_2 and taking whatever roots come back does not do
that.  Where Eq. (32) or Eq. (46) has several roots the naive order jumps
between sheets; where a family's admissible interval is disconnected in phi_2 it
jumps across the gap; and where two roots merge at a fold the two halves of one
smooth curve are handed back as separate unrelated lists.

This module fixes all three by continuation:

  1. march phi_2 on a fine grid and solve for the roots at each station;
  2. match each root to the branch it continues, by linear prediction from that
     branch's last two points -- so crossing branches do not swap identities;
  3. join the two branches that terminate together at a fold into one polyline;
  4. merge runs that meet across the phi_2 = +/- pi seam, which is not a boundary
     of the problem but of the coordinate.

The result is one ordered polyline per connected component of the (BUP), for
every family, which is what makes the swept sheet meaningful.

Cross-checked against the JavaScript implementation in bup_curves.js by
test_viz.py -- the two must agree to machine precision or the explorer and the
figures are showing different objects.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # layer0/
import barrier as B

TWO_PI = 2.0 * np.pi


# ---------------------------------------------------------------------------
# root finding on one phi_2 station
# ---------------------------------------------------------------------------

def _bisect(f, lo, hi, iters=80):
    flo = f(lo)
    if flo == 0.0:
        return lo
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if flo * f(mid) <= 0.0:
            hi = mid
        else:
            lo = mid
            flo = f(lo)
    return 0.5 * (lo + hi)


def roots_in(f, lo, hi, n=900):
    """Every sign change of f on [lo, hi], refined by bisection."""
    grid = np.linspace(lo, hi, n)
    vals = np.array([f(x) for x in grid])
    out = []
    for i in range(n - 1):
        if vals[i] == 0.0:
            out.append(grid[i])
        elif vals[i] * vals[i + 1] < 0.0:
            out.append(_bisect(f, grid[i], grid[i + 1]))
    return out


# ---------------------------------------------------------------------------
# continuation
# ---------------------------------------------------------------------------

def _predict(branch):
    """Linear extrapolation of phi_1 from a branch's last two points."""
    if len(branch) == 1:
        return branch[-1][1]
    (x0, y0), (x1, y1) = branch[-2], branch[-1]
    return y1 + (y1 - y0)


def trace_branches(root_fn, p2_grid, jump_tol):
    """
    Continuation of the root set of `root_fn` along `p2_grid`.

    Returns a list of branches, each an ordered list of (phi_2, phi_1).  A root
    continues the branch whose linear prediction it is nearest to, provided that
    distance is under `jump_tol`; otherwise it opens a new branch.  Matching is
    greedy on the closest pair, which keeps identities straight where two
    branches approach each other without merging.
    """
    active, done = [], []
    for q in p2_grid:
        rs = root_fn(q)
        if not rs:
            done.extend(active)
            active = []
            continue

        pairs = []
        for bi, br in enumerate(active):
            pred = _predict(br)
            for ri, r in enumerate(rs):
                pairs.append((abs(r - pred), bi, ri))
        pairs.sort()

        used_b, used_r = set(), set()
        for dist, bi, ri in pairs:
            if dist > jump_tol or bi in used_b or ri in used_r:
                continue
            active[bi].append((q, rs[ri]))
            used_b.add(bi)
            used_r.add(ri)

        still, dropped = [], []
        for bi, br in enumerate(active):
            (still if bi in used_b else dropped).append(br)
        done.extend(dropped)
        for ri, r in enumerate(rs):
            if ri not in used_r:
                still.append([(q, r)])
        active = still

    done.extend(active)
    return [b for b in done if len(b) > 2]


def refine_fold(root_fn, q_in, q_out, iters=200):
    """
    The exact point where two roots merge and the curve turns.

    Continuation can only follow a branch to the last phi_2 station where the
    grid still resolves two separate roots; past that the roots are closer
    together than the grid and the branch simply stops, leaving the two sheets a
    short distance apart at the tip.  Near a fold the roots separate like
    sqrt(phi_2* - phi_2), so that residual gap is much larger in phi_1 than the
    phi_2 step suggests -- on the maximum-range lens it leaves the tip about half
    a degree short of d_1.

    Bisecting on "do two roots still exist" closes it: `q_in` is a station that
    has them, `q_out` one that does not, and at the limit the merged root is the
    mean of the pair.  Returns (phi_2*, phi_1*).
    """
    lo, hi = q_in, q_out
    best = root_fn(q_in)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        rs = root_fn(mid)
        if len(rs) >= 2:
            lo, best = mid, rs
        else:
            hi = mid
    return lo, 0.5 * (min(best) + max(best))


def close_fold_tips(branches, root_fn, tol=6e-2):
    """
    Splice the refined fold point into every branch pair that dies together, so
    the tip of the curve is the fold itself rather than the last resolved
    station on either side.
    """
    out = []
    for br in branches:
        b = list(br)
        for end in (0, -1):
            q_in, p_in = b[end]
            step = b[1][0] - b[0][0] if end == 0 else b[-1][0] - b[-2][0]
            q_out = q_in + 12.0 * (-step if end == 0 else step)
            if len(root_fn(q_out)) >= 2:
                continue
            qf, pf = refine_fold(root_fn, q_in, q_out)
            if abs(pf - p_in) > tol:
                continue
            if end == 0:
                b.insert(0, (qf, pf))
            else:
                b.append((qf, pf))
        out.append(b)
    return out


def join_folds(branches, tol=2e-2):
    """
    Two branches that die at the same place died at a fold -- the two sheets of
    one smooth curve meeting where the roots merge.  Splice them into a single
    polyline that runs out along one sheet and back along the other, so the fold
    is an interior point rather than two loose ends.
    """
    out = list(branches)
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            for j in range(len(out)):
                if i == j:
                    continue
                a, b = out[i], out[j]
                for a_end, b_end in ((-1, -1), (-1, 0), (0, -1), (0, 0)):
                    pa, pb = a[a_end], b[b_end]
                    if abs(pa[0] - pb[0]) < tol and abs(pa[1] - pb[1]) < tol:
                        aa = a if a_end == -1 else a[::-1]
                        bb = b if b_end == 0 else b[::-1]
                        merged = aa + bb[1:]
                        out = [out[k] for k in range(len(out)) if k not in (i, j)]
                        out.append(merged)
                        changed = True
                        break
                if changed:
                    break
            if changed:
                break
    return out


def merge_seam(branches, tol=2e-2):
    """
    phi_2 = +pi and phi_2 = -pi are the same aspect angle.  A branch reaching one
    and another leaving the other are one curve cut by the coordinate, not two.

    The joined branch carries phi_2 UNWRAPPED across the seam -- the second run
    is shifted by 2*pi -- so that arclength resampling and the plotted polyline
    both stay continuous.  Wrap only when evaluating the equations, which is
    what seed_state does.
    """
    out = list(branches)
    for _ in range(len(branches)):
        joined = False
        for i in range(len(out)):
            for j in range(len(out)):
                if i == j:
                    continue
                a, b = out[i], out[j]
                if (abs(abs(a[-1][0]) - np.pi) < 0.05 and abs(abs(b[0][0]) - np.pi) < 0.05
                        and a[-1][0] * b[0][0] < 0
                        and abs(a[-1][1] - b[0][1]) < tol):
                    shift = TWO_PI * np.sign(a[-1][0] - b[0][0])
                    bb = [(q + shift, p) for q, p in b]
                    out = [out[k] for k in range(len(out)) if k not in (i, j)]
                    out.append(a + bb)
                    joined = True
                    break
            if joined:
                break
        if not joined:
            break
    return out


# ---------------------------------------------------------------------------
# the four families
# ---------------------------------------------------------------------------

def _grid(lo, hi, n):
    return np.linspace(lo, hi, n)


def branches_maxrange(n=900):
    """
    (BUP)_1 on the maximum-range surface, Eq. (32) with equality.

    sign(phi_2) in Eq. (32) makes phi_2 = 0 a genuine discontinuity of the root
    set, so the two lobes are traced separately; each is a closed lens folding
    at d_1.
    """
    eps = 2e-4
    out = []
    for sgn in (-1.0, +1.0):
        g = sgn * _grid(eps, 0.25, n)
        br = trace_branches(B.bup_maxrange, g, jump_tol=0.05)
        br = close_fold_tips(br, B.bup_maxrange)
        out.extend(join_folds(br))
    return out


def branches_minrange(n=1600):
    """(BUP)_1 on the minimum-range surface, Eq. (46) with equality."""
    g = _grid(-np.pi + 1e-3, np.pi - 1e-3, n)
    br = trace_branches(B.bup_minrange, g, jump_tol=0.05)
    br = close_fold_tips(br, B.bup_minrange)
    return merge_seam(join_folds(br))


def branches_boresight(sgn=+1, n=1600):
    """
    (BUP)_1 on the off-boresight limit surface phi_1 = sgn*beta, Eq. (62).

    phi_1 is fixed, so there is no root to trace: the curve is R(phi_2), defined
    exactly where that R lies inside the target set's range band.  The only
    ordering work is splitting into contiguous admissible runs and rejoining the
    two that meet at the phi_2 = +/- pi seam.
    """
    p1 = sgn * B.BETA
    g = _grid(-np.pi, np.pi, n)
    runs, cur = [], []
    for q in g:
        R = B.bup_boresight(q, sgn)
        if R is None:
            if len(cur) > 2:
                runs.append(cur)
            cur = []
        else:
            cur.append((q, p1))
    if len(cur) > 2:
        runs.append(cur)
    return merge_seam(runs)


FAMILIES = {
    'max': ('maximum range, Eq. (32)', branches_maxrange),
    'min': ('minimum range, Eq. (46)', branches_minrange),
    'bore+': (r'off-boresight $\phi_1=+\beta$, Eq. (62)',
              lambda n=1600: branches_boresight(+1, n)),
    'bore-': (r'off-boresight $\phi_1=-\beta$, Eq. (62)',
              lambda n=1600: branches_boresight(-1, n)),
}


# ---------------------------------------------------------------------------
# seeds
# ---------------------------------------------------------------------------

def seed_state(family, p1, p2):
    """
    State + transversality costate at one (BUP) point, Eq. (20).

    phi_2 arrives possibly unwrapped past +/- pi (see merge_seam) and is wrapped
    here, because Eq. (9)'s R_hi uses phi_2 + sin phi_2 unwrapped and is not
    periodic.
    """
    p2 = float(B.wrap(p2))
    if family == 'max':
        return np.array([B.R_hi(p2), p1, p2, *B.lam_maxrange(p2)])
    if family == 'min':
        return np.array([B.R_lo(p2), p1, p2, *B.lam_minrange(p2)])
    R = B.bup_boresight(p2, 1 if p1 > 0 else -1)
    return np.array([R, p1, p2, *B.lam_boresight(R, p1, p2)])


def resample_branch(branch, m):
    """
    Re-space a traced branch to m points at equal arclength in (phi_2, phi_1).

    Continuation produces points spaced by the phi_2 grid, which crowds near a
    fold, where the curve turns; equal arclength gives the sheet an even
    parametrization and keeps the quad strips well shaped.
    """
    P = np.asarray(branch, float)
    if len(P) < 2:
        return P
    d = np.r_[0.0, np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))]
    if d[-1] <= 0:
        return P[:1]
    t = np.linspace(0.0, d[-1], m)
    return np.c_[np.interp(t, d, P[:, 0]), np.interp(t, d, P[:, 1])]


ROOT_FN = {
    'max': lambda q: B.bup_maxrange(q),
    'min': lambda q: B.bup_minrange(q),
}


def snap_to_bup(family, pts):
    """
    Put resampled points back exactly on the (BUP).

    resample_branch interpolates (phi_2, phi_1) linearly, which lands slightly
    OFF the root of Eq. (32) / Eq. (46) -- enough to leave H* at 1e-5 at the seed
    instead of 1e-16, and a seed that is not semipermeable is not a barrier
    point.  So at each resampled phi_2 the root is solved again and the one
    nearest the interpolated phi_1 is taken.  The boresight families have no root
    to solve: R is given in closed form by Eq. (62), so they are already exact.
    """
    fn = ROOT_FN.get(family)
    if fn is None:
        return pts
    out = []
    for q, p1 in pts:
        rs = fn(float(B.wrap(q)))
        out.append((q, min(rs, key=lambda r: abs(r - p1)) if rs else p1))
    return out


def seeds(family, nseed=60, n=None):
    """Ordered seed states, one list per connected component of the (BUP)."""
    label, fn = FAMILIES[family]
    br = fn() if n is None else fn(n)
    out = []
    for b in br:
        pts = snap_to_bup(family, resample_branch(b, nseed))
        out.append([seed_state(family, p1, p2) for p2, p1 in pts])
    return out, label


if __name__ == '__main__':
    for key in ('max', 'min', 'bore+', 'bore-'):
        S, label = seeds(key, nseed=40)
        D = 180.0 / np.pi
        print('%-6s %-44s %d branch(es)' % (key, label, len(S)))
        for k, s in enumerate(S):
            a, b = s[0], s[-1]
            print('    %d: %3d seeds   phi_2 %8.2f -> %8.2f   phi_1 %8.2f -> %8.2f'
                  % (k, len(s), a[2] * D, b[2] * D, a[1] * D, b[1] * D))
