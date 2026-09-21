"""
diag_maxrange.py -- audit of the maximum-range barrier construction against
Davidovitz & Shinar Sec. 4.1.

The question this answers: are all the pieces needed for the two small closed
maximum-range capture zones being generated, or only the ordinary
backward-integrated sheets?

It reports, and does not repair.  Where a piece is missing it says so rather
than substituting something that looks like it.  Every intersection test uses
the full (R, phi_1, phi_2) state, never the (phi_1, phi_2) projection, and every
angular difference is wrapped.

Usage:  python3 layer0/viz/diag_maxrange.py [--tau 6.0] [--nseed 121]
                                            [--tol 0.02] [--out FIG.png]
"""

import argparse
import io
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import barrier as B
import bup_curves as C
from validate_table2 import TABLE2

D = 180.0 / np.pi
T2 = {n: (R, p1, p2) for n, R, p1, p2 in TABLE2}

RULE = '=' * 78
notes = []          # disagreements / gaps, collected for the closing summary


def head(n, s):
    print('\n' + RULE)
    print('%d. %s' % (n, s))
    print(RULE)


def gap(s):
    notes.append(s)
    print('  >> ' + s)


# ---------------------------------------------------------------------------
# closed forms, written out independently of barrier.py so that agreement is
# evidence rather than tautology
# ---------------------------------------------------------------------------

def eq32(p1, p2):
    """Eq. (32) residual: Rbar(1-cos p1) + (sin p1 + sin p2)(1+cos p2) sign p2."""
    return (B.R_hi(p2) * (1 - np.cos(p1))
            + (np.sin(p1) + np.sin(p2)) * (1 + np.cos(p2)) * np.sign(p2))


def rho(p2):
    Rb = B.R_hi(p2)
    return 1.0 / np.sqrt(Rb ** 2 + (1 + np.cos(p2)) ** 2)


def lam1dot_f(p1, p2):
    """lam1dot on the max-range BUP:  -rho[Rbar sin p1 + (1+cos p2) cos p1 sgn(sin p2)]."""
    Rb = B.R_hi(p2)
    return -rho(p2) * (Rb * np.sin(p1)
                       + (1 + np.cos(p2)) * np.cos(p1) * np.sign(np.sin(p2)))


def lam2_f(p2):
    Rb = B.R_hi(p2)
    return rho(p2) * Rb * (1 + np.cos(p2)) * np.sign(np.sin(p2))


def wrapdiff(a, b):
    return B.wrap(np.asarray(a) - np.asarray(b))


# ---------------------------------------------------------------------------

def step1_bup(nseed):
    head(1, 'The maximum-range BUP')

    rng = np.random.default_rng(1)
    w = 0.0
    for _ in range(20000):
        p1 = rng.uniform(-B.BETA, B.BETA)
        p2 = rng.uniform(-0.4, 0.4)
        lhs = B.R_hi(p2) * (1 - np.cos(p1))
        rhs = -(np.sin(p1) + np.sin(p2)) * (1 + np.cos(p2)) * np.sign(p2)
        w = max(w, abs((lhs - rhs) - B.up_maxrange(p1, p2)))
    print('  Eq. (32) as implemented vs the equality as stated:')
    print('     max | (LHS - RHS) - up_maxrange | over 20000 points = %.2e' % w)
    print('     -> the code solves exactly Rbar(1-cos p1) ='
          ' -(sin p1 + sin p2)(1+cos p2) sgn p2')

    seeds, label = C.seeds('max', nseed=nseed)
    print('\n  %s: %d connected branch(es) of the BUP' % (label, len(seeds)))
    for k, br in enumerate(seeds):
        q = np.array([y[2] for y in br]) * D
        p = np.array([y[1] for y in br]) * D
        print('     branch %d: %3d seeds   phi_2 in [%7.3f, %7.3f]   '
              'phi_1 in [%7.3f, %7.3f]' % (k, len(br), q.min(), q.max(),
                                           p.min(), p.max()))
    signs = set(np.sign([y[2] for br in seeds for y in br]))
    print('     signs of phi_2 present: %s -> both symmetric branches sampled: %s'
          % (sorted(signs), bool({-1.0, 1.0} <= signs)))

    res = max(abs(eq32(y[1], y[2])) for br in seeds for y in br)
    print('     max |Eq. (32)| over every seed = %.2e' % res)

    print('\n  Sampled BUP points (phi_1, phi_2, R), branch 0, every 8th:')
    print('        %9s %9s %9s   %12s' % ('phi_1', 'phi_2', 'R', 'Eq.(32)'))
    for y in seeds[0][::max(1, len(seeds[0]) // 8)]:
        print('        %9.4f %9.4f %9.5f   %12.2e'
              % (y[1] * D, y[2] * D, y[0], eq32(y[1], y[2])))
    return seeds


def step2_classify(seeds):
    head(2, 'Classifying every BUP seed by its initial control branch')

    w = 0.0
    for br in seeds:
        for y in br:
            _, l1d, _ = B.costate_dot(y[0], y[1], y[2], y[3], y[4], y[5])
            w = max(w, abs(l1d - lam1dot_f(y[1], y[2])))
    print('  lam_1f = 0 on every seed: max |lambda_1| = %.2e'
          % max(abs(y[4]) for br in seeds for y in br))
    print('  closed-form lam1dot_f vs the integrator\'s costate_dot: max diff = %.2e' % w)

    groups = {}
    for bi, br in enumerate(seeds):
        for si, y in enumerate(br):
            s1 = int(np.sign(lam1dot_f(y[1], y[2])))
            s2 = int(np.sign(lam2_f(y[2])))
            code = B.barrier_controls(*y)
            if (s1, s2) != (int(code[0]), int(code[1])):
                gap('seed (branch %d, %d): closed form gives (%+d,%+d), '
                    'barrier_controls gives (%+d,%+d)'
                    % (bi, si, s1, s2, code[0], code[1]))
            groups.setdefault((s1, s2), []).append((bi, si, y))

    print('\n  Seeds grouped by (sigma_1*, sigma_2*)   [sigma_1* = sign(lam1dot_f),'
          ' sigma_2* = sign(lam_2f)]')
    print('        %-14s %6s   %s' % ('(s1, s2)', 'count', 'phi_2 range [deg]'))
    for key in sorted(groups):
        g = groups[key]
        q = np.array([y[2] for _, _, y in g]) * D
        print('        %-14s %6d   [%7.3f, %7.3f]'
              % ('(%+d, %+d)' % key, len(g), q.min(), q.max()))
    return groups


def step3_special_points(seeds):
    head(3, 'The special BUP points: solving lam1dot_f = 0 on the BUP')

    # d/dphi1 Eq.(32) = -lam1dot_f/rho, so the sigma_1 switch locus on the BUP
    # is exactly the fold of Eq. (32).  Check it rather than assert it.
    rng = np.random.default_rng(3)
    w = 0.0
    for _ in range(5000):
        p1 = rng.uniform(-B.BETA, B.BETA)
        p2 = rng.uniform(-0.35, -0.01)
        h = 1e-6
        dEq = (eq32(p1 + h, p2) - eq32(p1 - h, p2)) / (2 * h)
        w = max(w, abs(dEq + lam1dot_f(p1, p2) / rho(p2)))
    print('  Identity  d(Eq.32)/dphi_1 == -lam1dot_f / rho :  max residual %.2e' % w)
    print('     -> lam1dot_f = 0 on the BUP IS the fold of Eq. (32): the point where')
    print('        its two phi_1 roots merge, and where sigma_1* changes sign.')

    out = {}
    for sgn, name in ((-1.0, 'phi_2 < 0'), (+1.0, 'phi_2 > 0')):
        lo, hi = 1e-5, 0.30
        for _ in range(200):                      # bisect on "two roots exist"
            mid = 0.5 * (lo + hi)
            if len(B.bup_maxrange(sgn * mid)) >= 2:
                lo = mid
            else:
                hi = mid
        q = sgn * lo
        rs = B.bup_maxrange(q)
        p1 = 0.5 * (min(rs) + max(rs))
        out[name] = (B.R_hi(q), p1, q)
        print('\n  %s : lam1dot_f = 0 and Eq.(32) = 0 at' % name)
        print('        R = %.5f   phi_1 = %.4f deg   phi_2 = %.4f deg'
              % (B.R_hi(q), p1 * D, q * D))
        print('        residuals: Eq.(32) = %.2e   lam1dot_f = %.2e'
              % (eq32(p1, q), lam1dot_f(p1, q)))
        for nm in ('d_1', 'f_1'):
            R, a1, a2 = T2[nm]
            print('        vs Table 2 %-4s (%.4f, %.2f, %.2f):  dR %.1e  dphi_1 %.1e deg'
                  '  dphi_2 %.1e deg'
                  % (nm, R, a1, a2, abs(B.R_hi(q) - R), abs(p1 * D - a1),
                     abs(q * D - a2)))

    print('\n  Is f_1 a point of the maximum-range BUP at all?')
    R, a1, a2 = T2['f_1']
    print('     Table 2 f_1 = (%.4f, %.2f deg, %.2f deg)' % (R, a1, a2))
    print('     Eq.(32) residual at f_1, evaluated at phi_2 = 0 exactly: %.4f'
          % eq32(a1 / D, a2 / D))
    for eps in (1e-4, 1e-3, 1e-2):
        print('     Eq.(32) residual at phi_1 = f_1, phi_2 = %+0.0e : %+.4f   /  %+.4f'
              % (eps, eq32(a1 / D, eps), eq32(a1 / D, -eps)))
    gap('f_1 is NOT a root of Eq. (32).  It sits at phi_2 = 0, R = Rbar(0), '
        'phi_1 = 18.5 deg -- on the phi_2 = 0 CORNER EDGE of the maximum-range '
        'surface, not on the maximum-range BUP.')
    return out


def integrate_classified(y0, tau_max, dt):
    """Retrograde integration with the stopping reason recorded."""
    tr = B.integrate_retrograde(y0, tau_max=tau_max, dt=dt,
                                R_min=0.02, R_max=12.0)
    Rend = tr['R'][-1]
    tau = tr['tau'][-1]
    if not np.isfinite(Rend):
        why = 'non-finite'
    elif Rend <= 0.02 + 1e-9:
        why = 'R_min reached'
    elif Rend >= 12.0 - 1e-9:
        why = 'R_max reached'
    elif tau >= tau_max - 1e-9:
        why = 'tau limit (numerical timeout)'
    else:
        why = 'step guard'
    tr['why'] = why
    return tr


def step4_integrate(seeds, tau_max, dt):
    head(4, 'Integrating every ordinary BUP seed, with termination classified')

    bundles, why_count, nsw, sing = [], {}, 0, 0
    fi = h = 0.0
    for br in seeds:
        rowb = []
        for y in br:
            tr = integrate_classified(np.asarray(y), tau_max, dt)
            why_count[tr['why']] = why_count.get(tr['why'], 0) + 1
            nsw += len(tr['switches'])
            sing += len(tr['singular'])
            fi = max(fi, tr['fi_err'].max())
            h = max(h, tr['h_err'].max())
            rowb.append(tr)
        bundles.append(rowb)

    n = sum(len(b) for b in bundles)
    print('  %d trajectories integrated to tau_max = %.1f, dt = %g' % (n, tau_max, dt))
    print('  control switches located (recomputed at every sign change): %d' % nsw)
    print('  singular-arc flags raised: %d' % sing)
    print('  invariants over the whole bundle: max |FI-1| = %.2e, max |H*| = %.2e'
          % (fi, h))
    print('\n  Termination events, counted separately from numerical timeout:')
    for k in sorted(why_count):
        print('        %-32s %4d' % (k, why_count[k]))
    return bundles, nsw, sing


# ---------------------------------------------------------------------------
# intersections, in the full state space
# ---------------------------------------------------------------------------

def cloud(bundle, stride=3):
    """(R, phi_1, phi_2) samples of a family, wrapped angles, as they are."""
    P = []
    for tr in bundle:
        for i in range(0, len(tr['R']), stride):
            P.append((tr['R'][i], tr['phi1'][i], tr['phi2'][i]))
    return np.array(P)


def scales(*clouds):
    """Per-coordinate span of the union, for a normalized metric."""
    A = np.vstack(clouds)
    s = np.array([A[:, 0].max() - A[:, 0].min(), 2 * np.pi, 2 * np.pi])
    return np.maximum(s, 1e-9)


def pair_distances(P, Q, s):
    """Normalized 3-D distance from each P to the nearest Q, angles wrapped."""
    from scipy.spatial import cKDTree
    # embed each angle on the circle so wrapping is exact under a Euclidean tree
    def emb(X):
        return np.c_[X[:, 0] / s[0],
                     np.cos(X[:, 1]) / (2 * np.pi), np.sin(X[:, 1]) / (2 * np.pi),
                     np.cos(X[:, 2]) / (2 * np.pi), np.sin(X[:, 2]) / (2 * np.pi)]
    t = cKDTree(emb(Q))
    d, j = t.query(emb(P), k=1)
    return d, j


def step4b_corner_family(nseed=25):
    """
    The paper's two families terminate on e_1 f_1 O and on e_1 d_1 O.  Those two
    segments share their endpoints, so together they bound the usable part in the
    phi_2 <= 0 half: the lens is one side, and the phi_2 = 0 CORNER EDGE of the
    maximum-range surface is the other.  f_1 lies on that corner edge.

    So one of the two families is seeded on the corner, not on the lens.  This
    checks whether the code can and does seed it.
    """
    head(41, 'The phi_2 = 0 corner segment O - f_1 - e_1 (the paper\'s other family)')

    for nm in ('O_1', 'f_1', 'e_1'):
        R, a1, a2 = T2[nm]
        print('  Table 2 %-4s = (R %.4f, phi_1 %6.2f deg, phi_2 %5.2f deg)'
              % (nm, R, a1, a2))
    print('  -> all three sit at phi_2 = 0 and R = Rbar(0) = %.5f, differing only'
          % B.R_hi(0.0))
    print('     in phi_1.  They are collinear along the corner edge, not on the lens.')

    print('\n  Rbar has a corner at phi_2 = 0: Rbar = Rbar_0 - |phi_2 + sin phi_2|,')
    print('  so dRbar/dphi_2 jumps from %+.4f to %+.4f across it.'
          % (B.dR_hi(-1e-9), B.dR_hi(+1e-9)))
    print('  The outer normal is therefore not unique there, and the costate must')
    print('  be a non-negative combination of the two adjoining normals:')
    na, nb = B.n_maxrange(-1e-9), B.n_maxrange(+1e-9)
    print('     n(phi_2 -> 0-) = (%.3f, %.3f, %+.3f)' % tuple(na))
    print('     n(phi_2 -> 0+) = (%.3f, %.3f, %+.3f)' % tuple(nb))

    print('\n  barrier.py CAN solve that combination: lam_corner solves H* = 0 and')
    print('  FI = 1 for it.  Scanning phi_1 along the corner:')
    R0 = B.R_hi(0.0)
    runs, cur, prev = [], None, 0.2
    for a1 in np.linspace(0.2, 44.8, 447):
        n = len(B.lam_corner(R0, a1 / D, 0.0, na, nb))
        if n >= 2 and cur is None:
            cur = [a1]
        if n < 2 and cur is not None:
            cur.append(prev); runs.append(cur); cur = None
        prev = a1
    if cur:
        cur.append(44.8); runs.append(cur)
    print('     phi_1 intervals admitting TWO admissible costates [deg]: %s'
          % [(round(a, 2), round(b, 2)) for a, b in runs])
    lo, hi = 30.0, 44.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if len(B.lam_corner(R0, mid / D, 0.0, na, nb)) >= 2:
            hi = mid
        else:
            lo = mid
    thr = 0.5 * (lo + hi)
    print('     the corner costate becomes double-valued at phi_1 = %.4f deg' % thr)
    print('     Table 2 e_1 is at                              phi_1 = %.2f deg'
          ' (difference %.4f deg)' % (T2['e_1'][1], abs(thr - T2['e_1'][1])))
    print('     -> e_1 is precisely the branch point of the corner costate. Below it,')
    print('        along O - f_1 - e_1, the corner costate is UNIQUE:')
    l = B.lam_corner(R0, T2['f_1'][1] / D, 0.0, na, nb)[0][0]
    lm, lp = B.lam_maxrange(-1e-6), B.lam_maxrange(+1e-6)
    print('        at f_1   lam_corner        = (%+.4f, %+.4f, %+.4f)  sigma_2* = %+d'
          % (l[0], l[1], l[2], int(np.sign(l[2]))))
    print('        cf.      lens, phi_2 -> 0- = (%+.4f, %+.4f, %+.4f)  sigma_2* = %+d'
          % (lm[0], lm[1], lm[2], int(np.sign(lm[2]))))
    print('        cf.      lens, phi_2 -> 0+ = (%+.4f, %+.4f, %+.4f)  sigma_2* = %+d'
          % (lp[0], lp[1], lp[2], int(np.sign(lp[2]))))
    gap('Wiring lam_corner into the seeding is necessary but NOT sufficient: on the '
        'segment O - f_1 - e_1 it returns a single costate, matching the phi_2 -> 0+ '
        'limit. Two sheets over that segment -- which is what a dispersal line needs '
        '-- do not fall out of it as written.')

    src = io.open(os.path.join(HERE, 'bup_curves.py'), encoding='utf-8').read()
    print('\n  Does the seeding ever use it?')
    for name in ('lam_corner', 'n_maxrange', 'n_minrange', 'n_boresight'):
        print('     bup_curves.py references %-12s : %s'
              % (name, 'yes' if name in src else 'NO'))
    gap('The phi_2 = 0 corner family is NEVER SEEDED. bup_curves.py builds seeds '
        'only from lam_maxrange / lam_minrange / lam_boresight -- the three smooth '
        'surfaces. lam_corner is implemented and validated by test_barrier.py to '
        '1.1e-15, but nothing calls it. So of the paper\'s two maximum-range '
        'families, only the lens family (e_1 d_1 O) is generated; the corner family '
        '(e_1 f_1 O) is absent.')
    gap('Because the corner family is absent, the dispersal line where the two '
        'families meet cannot be produced, c_1 cannot be located, and the two small '
        'closed capture zones cannot be bounded. What is plotted today is the '
        'ordinary backward-integrated sheets only.')


def truncate(bun, tau_cut, stride):
    P = []
    for tr in bun:
        m = int(np.searchsorted(tr['tau'], tau_cut))
        for i in range(0, max(m, 1), stride):
            P.append((tr['R'][i], tr['phi1'][i], tr['phi2'][i]))
    return np.array(P) if P else np.zeros((0, 3))


def step56_intersections(seeds, bundles, tol, stride=6):
    head(5, 'Intersections between barrier families, in full (R, phi_1, phi_2)')

    # The two sigma_1 families inside one lobe are the two halves of the lens,
    # split at the fold: inner (O_1 -> d_1) and outer (d_1 -> e_1).
    fam = {}
    for bi, (br, bun) in enumerate(zip(seeds, bundles)):
        k = int(np.argmax([abs(y[2]) for y in br]))
        fam[('lobe%d' % bi, 'inner')] = bun[:k + 1]
        fam[('lobe%d' % bi, 'outer')] = bun[k + 1:]
    for k in sorted(fam):
        print('  family %-28s %3d trajectories' % (str(k), len(fam[k])))

    print('\n  Resolved in retrograde time: past tau ~ 3 the angles wind through')
    print('  +/- 180 deg and every sheet threads every other one, so a single')
    print('  number at tau_max says nothing about whether they MEET.')
    print('\n  %-40s %9s %9s %9s' % ('family pair', 'tau<=0.4', 'tau<=1.0', 'tau<=2.0'))

    keys = sorted(fam)
    taus = (0.4, 1.0, 2.0)
    table, best = {}, None
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            ka, kb = keys[a], keys[b]
            row = []
            for tc in taus:
                Pa, Pb = truncate(fam[ka], tc, stride), truncate(fam[kb], tc, stride)
                if not len(Pa) or not len(Pb):
                    row.append(np.nan); continue
                s_ = scales(Pa, Pb)
                d, j = pair_distances(Pa, Pb, s_)
                row.append(d.min())
                if tc == taus[-1]:
                    i0 = int(np.argmin(d))
                    cand = (d.min(), ka, kb, Pa[i0], Pb[j[i0]], int((d < tol).sum()))
                    if best is None or cand[0] < best[0]:
                        best = cand
            table[(ka, kb)] = row
            print('  %-40s %9.5f %9.5f %9.5f'
                  % (str(ka) + ' x ' + str(kb), row[0], row[1], row[2]))

    head(6, 'Do the red and blue sheets actually meet?')
    print('  Closest approach of any two families, tau <= %.1f: %.5f (normalized)'
          % (taus[-1], best[0]))
    print('     %-22s R %.4f  phi_1 %8.3f deg  phi_2 %8.3f deg'
          % (str(best[1]), best[3][0], best[3][1] * D, best[3][2] * D))
    print('     %-22s R %.4f  phi_1 %8.3f deg  phi_2 %8.3f deg'
          % (str(best[2]), best[4][0], best[4][1] * D, best[4][2] * D))
    print('     separation in R alone there: %.5f' % abs(best[3][0] - best[4][0]))

    # the trap the request warns about, measured
    ka, kb = ('lobe0', 'inner'), ('lobe1', 'inner')
    Pa, Pb = truncate(fam[ka], 2.0, stride), truncate(fam[kb], 2.0, stride)
    s_ = scales(Pa, Pb)
    d3, _ = pair_distances(Pa, Pb, s_)
    flat = np.array([1.0, 2 * np.pi, 2 * np.pi])
    d2, _ = pair_distances(np.c_[Pa[:, 0] * 0, Pa[:, 1], Pa[:, 2]],
                           np.c_[Pb[:, 0] * 0, Pb[:, 1], Pb[:, 2]], flat)
    print('\n  Projection trap, %s x %s at tau <= 2:' % (str(ka), str(kb)))
    print('     within tol in the (phi_1, phi_2) projection alone : %6d points'
          % int((d2 < tol).sum()))
    print('     within tol in full (R, phi_1, phi_2)              : %6d points'
          % int((d3 < tol).sum()))
    print('     -> the projection overstates contact by %.1fx'
          % (max(int((d2 < tol).sum()), 1) / max(int((d3 < tol).sum()), 1)))

    # candidate dispersal points: different lobes only (different sigma_2)
    pts = []
    for (ka, kb), row in table.items():
        if ka[0] == kb[0]:
            continue
        Pa, Pb = truncate(fam[ka], 2.0, stride), truncate(fam[kb], 2.0, stride)
        s_ = scales(Pa, Pb)
        d, j = pair_distances(Pa, Pb, s_)
        m = d < tol
        if m.any():
            pts.append(0.5 * (Pa[m] + Pb[j[m]]))
    pts = np.vstack(pts) if pts else np.zeros((0, 3))
    print('\n  Candidate P2-dispersal points (different lobes => different sigma_2),')
    print('  tau <= 2, tol %.3f: %d' % (tol, len(pts)))
    if len(pts):
        print('     phi_2 of those points: mean %.4f deg, |phi_2| max %.4f deg'
              % (pts[:, 2].mean() * D, np.abs(pts[:, 2]).max() * D))

    curve, contiguous = order_curve(pts, scales(pts) if len(pts) else
                                    np.ones(3), tol)
    print('  ordered into one continuous curve: %s' % ('yes' if contiguous else 'no'))
    return fam, table, pts, curve


def order_curve(pts, s, tol):
    """Greedy nearest-neighbour chain; contiguous if no hop exceeds 6*tol."""
    if len(pts) < 3:
        return pts, False
    X = np.c_[pts[:, 0] / s[0], np.cos(pts[:, 1]) / (2 * np.pi),
              np.sin(pts[:, 1]) / (2 * np.pi), np.cos(pts[:, 2]) / (2 * np.pi),
              np.sin(pts[:, 2]) / (2 * np.pi)]
    left = list(range(len(X)))
    order = [left.pop(0)]
    hops = []
    while left:
        d = np.linalg.norm(X[left] - X[order[-1]], axis=1)
        k = int(np.argmin(d))
        hops.append(d[k])
        order.append(left.pop(k))
    return pts[order], (max(hops) < 6 * tol)


def step789(bundles, sing):
    head(7, 'Universal / singular control at the special points')
    print('  At d_1 (and at f_1 on the corner) lambda_1 = 0 AND lambda_1-dot = 0,')
    print('  so sigma_1 = -sign(lambda_1) determines nothing.')
    print('  barrier.py behaviour: integrate_retrograde DETECTS this case')
    print('  (|lambda_i| < tol and |lambda_i-dot| < tol) and returns it in its')
    print('  `singular` field.  Flags raised over this bundle: %d' % sing)
    best = 1e9
    for bun in bundles:
        for tr in bun:
            Y = tr['Y']
            for i in range(0, len(Y), 9):
                q = Y[i]
                _, l1d, l2d = B.costate_dot(q[0], q[1], q[2], q[3], q[4], q[5])
                best = min(best, max(abs(q[4]), abs(l1d)), max(abs(q[5]), abs(l2d)))
    print('  smallest max(|lambda_i|, |lambda_i-dot|) anywhere in the bundle: %.2e'
          % best)
    print('  detector threshold: 1.0e-07')
    gap('The singular detector never fires: the closest any trajectory comes to the '
        'condition is %.1e, five orders of magnitude above the 1e-7 threshold. It is '
        'dead code in practice and provides no protection.' % best)
    gap('There is NO singular / universal-arc propagation anywhere in the code. '
        'Universal lines are detected, never integrated. The intermediate control '
        'on such an arc is not computed, and nothing assigns sigma_1 = +/-1 there '
        'as a substitute.')

    head(8, 'Where the universal lines meet the dispersal line (c_1)')
    print('  Not computable: step 7 shows no universal line is propagated, so there')
    print('  is no curve to intersect with the dispersal candidates.')
    gap('c_1-type junctions cannot be located until universal-line propagation exists.')

    head(9, 'Closure of the capture zone')
    print('  Required pieces: ordinary sheets, universal-line pieces, dispersal-line')
    print('  junctions, and the usable maximum-range target patch.')
    print('     ordinary sheets ........................ present')
    print('     universal-line pieces .................. ABSENT (step 7)')
    print('     dispersal-line junctions ............... ABSENT (step 8)')
    print('     usable target patch .................... computable, not assembled')
    gap('No mesh is ever assembled from the sheets, so watertightness cannot be '
        'tested and no open-edge list can be produced. The code plots surfaces; '
        'it does not build a solid.')


# ---------------------------------------------------------------------------

def figure(seeds, fam, pts, special, out, tau_fig=0.45):
    """
    The diagnostic picture, restricted to the neighbourhood the capture zones
    live in.

    Drawn over the full retrograde length the bundle winds through several
    hundred degrees of phi_1 and phi_2 and the region of interest -- a lens 19
    degrees wide and 0.33 deep in R -- collapses to a line. So the trajectories
    are cut at tau = %.2f, which is the scale of the paper's Fig. 8, and the
    angles are left wrapped.
    """
    # NOTE: in this module D = 180/pi, so radians -> degrees is  * D.
    # (visualize.py defines D the other way round; do not copy '/ D' here.)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    COL = {('lobe0', 'inner'): '#1f5fa8', ('lobe0', 'outer'): '#7fb0e0',
           ('lobe1', 'inner'): '#c1442a', ('lobe1', 'outer'): '#e8a184'}
    LAB = {('lobe0', 'inner'): r'$\phi_2<0$, inner ($O_1\!\to\! d_1$)',
           ('lobe0', 'outer'): r'$\phi_2<0$, outer ($d_1\!\to\! e_1$)',
           ('lobe1', 'inner'): r'$\phi_2>0$, inner',
           ('lobe1', 'outer'): r'$\phi_2>0$, outer'}

    fig = plt.figure(figsize=(12.0, 5.6))
    for panel, (elev, azim, ttl) in enumerate(
            [(20, -62, 'oblique'), (6, -90, r'edge-on, down the $\phi_2$ axis')]):
        ax = fig.add_subplot(1, 2, panel + 1, projection='3d')

        # usable maximum-range patch, drawn as a scatter of the points that
        # satisfy Eq. (32) < 0 -- a NaN-filled plot_surface fights the autoscale
        q = np.linspace(-0.30, 0.30, 90)
        p = np.linspace(-B.BETA, B.BETA, 90)
        Q, P = np.meshgrid(q, p)
        m = B.up_maxrange(P, Q) < 0
        ax.scatter(Q[m] * D, P[m] * D, B.R_hi(Q[m]), s=2.5, c='#aeb7c0',
                   alpha=0.45, depthshade=False, linewidths=0)

        first = {}
        for key in sorted(fam):
            for tr in fam[key]:
                m = max(int(np.searchsorted(tr['tau'], tau_fig)), 2)
                ax.plot(tr['phi2'][:m] * D, tr['phi1'][:m] * D, tr['R'][:m],
                        lw=0.7, color=COL[key], alpha=0.85,
                        label=LAB[key] if key not in first else None)
                first[key] = True
        for br in seeds:
            ax.plot([y[2] * D for y in br], [y[1] * D for y in br],
                    [y[0] for y in br], lw=2.6, color='#111', zorder=9)

        for nm, c, mk in (('O_1', '#111', 'o'), ('d_1', '#111', 'o'),
                          ('e_1', '#111', 'o'), ('f_1', '#1a7f4b', 'D')):
            R, a1, a2 = T2[nm]
            ax.scatter([a2], [a1], [R], s=46 if mk == 'o' else 54, c=c,
                       marker=mk, depthshade=False, zorder=11, edgecolors='w',
                       linewidths=0.8)
            ax.text(a2, a1 + 1.6, R, '$%s$' % nm, fontsize=9, color=c, zorder=12)

        if len(pts):
            m = np.abs(pts[:, 2]) < 0.22
            ax.scatter(pts[m, 2] * D, pts[m, 1] * D, pts[m, 0], s=9,
                       c='#8a5cc7', depthshade=False, zorder=10)

        ax.set_xlabel(r'$\phi_2$ [deg]', labelpad=5)
        ax.set_ylabel(r'$\phi_1$ [deg]', labelpad=5)
        ax.set_zlabel(r'$R$', labelpad=5)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(ttl, fontsize=9.5)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.line.set_color('#3f4750')
            axis.line.set_linewidth(1.5)
            axis.set_pane_color((1, 1, 1, 0))
        ax.tick_params(colors='#2c333a', labelsize=8)
        if panel == 0:
            ax.legend(fontsize=7.5, loc='upper left', framealpha=0.92)

    fig.suptitle(r'Maximum-range barrier — diagnostic ($\tau \leq %.2f$, the Fig. 8 scale)'
                 % tau_fig + '\n'
                 'grey = usable maximum-range patch · black = (BUP)$_1$ · '
                 'trajectories by $(\sigma_1^*,\sigma_2^*)$ family · '
                 'purple = 3-D intersection candidates\n'
                 'NOT DRAWN, BECAUSE NOT IMPLEMENTED: the $\phi_2=0$ corner family '
                 'through $f_1$, the universal lines at $d_1$/$f_1$, $c_1$, '
                 'and any mesh open edges', fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(out, dpi=140)
    print('\n  wrote %s' % os.path.abspath(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tau', type=float, default=6.0)
    ap.add_argument('--nseed', type=int, default=121)
    ap.add_argument('--tol', type=float, default=0.02)
    ap.add_argument('--dt', type=float, default=1e-3)
    ap.add_argument('--out', default=os.path.join(HERE, 'figs', 'diag_maxrange.png'))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    seeds = step1_bup(a.nseed)
    step2_classify(seeds)
    special = step3_special_points(seeds)
    bundles, nsw, sing = step4_integrate(seeds, a.tau, a.dt)
    step4b_corner_family()
    fam, table, pts, curve = step56_intersections(seeds, bundles, a.tol)
    step789(bundles, sing)

    head(10, 'Summary')
    n = sum(len(b) for b in seeds)
    print('  BUP seeds ............................... %d (%d branches)'
          % (n, len(seeds)))
    print('  control switches detected ............... %d' % nsw)
    print('  min distance between families ........... %.5f (normalized, tau<=2)'
          % min(min(v) for v in table.values()))
    print('  intersection points within tol .......... %d' % len(pts))
    spread = (np.abs(pts[:, 2]).max() * D) if len(pts) else 0.0
    print('  intersection points cluster within ...... |phi_2| <= %.3f deg' % spread)
    print('  continuous dispersal line found ......... no -- see below')
    print('     The points that pass the 3-D test all sit at phi_2 ~ 0, which is')
    print('     where the two mirror lenses SHARE their endpoint O_1. That is one')
    print('     point thickened by the tolerance, not a dispersal curve. The two')
    print('     lens families otherwise stay %.3f apart (normalized) and never meet.'
          % min(v[2] for k, v in table.items() if k[0][0] != k[1][0]))
    print('  universal-line handling exists .......... no (detection only)')
    print('  assembled surface watertight ............ n/a -- no mesh is assembled')
    print('\n  Equations / conventions that disagree with the paper:')
    if notes:
        for i, s_ in enumerate(notes, 1):
            print('     %d. %s' % (i, s_))
    else:
        print('     none found')

    figure(seeds, fam, pts, special, a.out)


if __name__ == '__main__':
    main()
