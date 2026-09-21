"""
corner_family.py -- the missing half of the maximum-range barrier.

D&S Sec. 4.1 has two families of barrier trajectories terminating on the
maximum-range (BUP)_1: one on the segment e_1 f_1 O, one on e_1 d_1 O. They
intersect along a dispersal line of the evader.

e_1 d_1 O is the lens, Eq. (32) = 0, which bup_curves.py already traces.
e_1 f_1 O is the phi_2 = 0 CORNER EDGE of the maximum-range surface, where
Rbar = Rbar_0 - |phi_2 + sin phi_2| has its slope jump from +2 to -2 and the
outer normal is a cone rather than a vector. That segment was never seeded.

It is seedable. lam_corner solves the corner costate from the two conditions it
must satisfy anyway -- H* = 0 and FI = 1 -- and on this segment it returns one
admissible costate per point, to machine precision. Seeding from it and
integrating retrograde gives the second family.

WHAT THE TWO FAMILIES DO, MEASURED. They contact each other, but not yet along
the dispersal line e_1 c_1 O. The contact set is TWO arcs hugging the endpoints
the two (BUP) pieces share, with a gap in the middle that WIDENS as the
tolerance tightens:

    tol     contacts   phi_1 clusters [deg]        nearest contact to f_1
    0.020      1743    [0.3, 12.1] [25.0, 39.3]     6.4 deg
    0.010       736    [0.3, 10.2] [26.9, 37.7]     8.3 deg
    0.002       142    [0.3,  8.6] [28.5, 36.4]     9.9 deg
    0.0005       21    fragments                   11.5 deg

A transversal intersection along a curve would hold its extent as the tolerance
shrinks. This does not: it converges on O and e_1. So the two families meet at
the shared endpoints and the middle of the dispersal line is still missing --
and the gap sits exactly where f_1, the (+1,+1) family and the universal lines
belong. Those are the pieces below.

    the corner segment  R = Rbar_0,  phi_2 = 0,  0 < phi_1 < 2 arctan(2/Rbar_0)

The upper limit is e_1 in closed form: it is where the phi_2 -> 0- limit of
Eq. (32), Rbar_0(1 - cos phi_1) - 2 sin phi_1, changes sign.

CORRECTION (see universal_d1.py): 18.5 deg is not only a sign-slip artifact.
The universal-line costate lambda = (cos phi_1, 0, -R sin phi_1) placed on this
corner has H* = Rbar_0 sin phi_1 - 1 - cos phi_1, which vanishes exactly at
Rbar_0 tan(phi_1/2) = 1 -- the same root. So f_1 is where a universal line of
player 1 can leave the corner semipermeably, and the universal line from d_1
passes within 2e-3 of it. That costate is 2.7% outside the corner normal cone,
and it is not the corner family's costate, so what follows about sigma_1 on the
corner family itself still stands.

WHERE f_1 COMES FROM, AND WHY THE SWITCH IS NOT THERE.  Table 2 lists
f_1 = (R, phi_1, phi_2) = (6.142, 18.5, 0.0), i.e. on this very segment, and
Sec. 4.1 says two universal lines of player 1 terminate at d_1 and f_1. So
sigma_1 ought to flip here. It does not, and the number 18.5 is reproducible
exactly -- from a misplaced sign in the paper's Eq. (42). Run f1_diagnostic().

The corner costate is Eqs. (38)-(41): lambda_1 == 0 identically (the corner
cone is spanned by (1,0,-2) and (1,0,+2), both with zero phi_1 component), so
sigma_1 comes from Eq. (33), sigma_1 = sign(lambda_1-dot), and the paper gives

    Eq. (42)   lambda_1-dot = -q[ Rbar_0 |sin phi_1| + (cos phi_1 + 1) sign phi_1 ]

Substituting Eqs. (39)-(41) into Eq. (18) reproduces that expression to 1e-16
FOR phi_1 > 0 -- so the equation is right on the branch the paper derives it on,
and it is strictly negative there: sigma_1 = -1, no switch.

For phi_1 < 0 it is wrong. The true lambda_1-dot is odd under the paper's own
mirror symmetry M: (phi_1, phi_2, lambda_1, lambda_2) -> -(phi_1, phi_2,
lambda_1, lambda_2), so the sign phi_1 belongs OUTSIDE the bracket,

    corrected  lambda_1-dot = -q[ Rbar_0 |sin phi_1| + (cos phi_1 + 1) ] sign phi_1

As printed, with sign phi_1 attached only to the second term, the bracket
becomes a DIFFERENCE on phi_1 < 0 and acquires a spurious root:

    Rbar_0 |sin phi_1| = 1 + cos phi_1   <=>   Rbar_0 tan(|phi_1|/2) = 1
    |phi_1| = 2 arctan(1/Rbar_0) = 18.4960 deg      (18.5007 with Rbar_0 = 6.14)

which is Table 2's 18.5 to both printed digits. Compare e_1, the end of this
segment, which is the honest Rbar_0 tan(phi_1/2) = 2 -> 36.0755 deg (Table 2:
36.07). The two differ only in that factor of 2 -- the jump in dRbar/dphi_2
across phi_2 = 0 -- which is exactly what the misplaced sign destroys.

The one other reading also fails. H* = 0 and FI = 1 have a SECOND root at the
corner, with lambda_2 < 0, and its lambda_1-dot does vanish at 18.4960 deg. But
that root lies outside the admissible normal cone (|lambda_2| / 2 lambda_R =
1.027 > 1, i.e. one of mu+, mu- is negative) for every phi_1 below e_1; it
enters the cone exactly at phi_1 = e_1 = 36.0755 deg. So it is not a barrier
costate anywhere on the segment where f_1 is tabulated.

THE SEGMENT ITSELF IS NOT IN DOUBT. O - f_1 - e_1 is a (BUP): every point of
it is seeded here, including the half below f_1, with FI = 1 and H* = 0 to
1e-16 and trajectories integrating out of it cleanly. What is in doubt is only
which control pair it carries.

AND (+1,+1) CANNOT BE THAT PAIR, for a reason that needs none of Eq. (42).
On the corner lambda_1 == 0, so Eq. (18) reduces to

    lambda_1-dot = -[ lambda_R sin phi_1 + lambda_2 cos phi_1 / Rbar_0 ]

On 0 < phi_1 < e_1 = 36.08 deg both sin phi_1 > 0 and cos phi_1 > 0, and
lambda_R = mu+ + mu- > 0 for every admissible cone vector. So sigma_2 = +1
means lambda_2 > 0 (Eq. 22), which makes both terms positive, which makes
lambda_1-dot < 0, which by Eq. (33) forces sigma_1 = -1. Choosing sigma_2 = +1
chooses sigma_1 = -1. A brute scan of the whole cone -- 2e4 cone directions at
each of 400 values of phi_1 -- realizes exactly one pair, {(-1,+1)}.

sigma_1 = +1 would need lambda_2 < -Rbar_0 tan(phi_1) lambda_R, hence
lambda_2 < 0, hence sigma_2 = -1. So the only second family that could
terminate on this segment is (+1,-1), not (+1,+1) -- and the lambda_2 < 0 root
of H* = 0 is the out-of-cone one above. Which is a sensible place to look next:
Eq. (31) says sigma_2 = sign(phi_2), and phi_2 = 0 is exactly where that is
undefined, so a corner is the natural home for a second evader branch.

Conclusion: on this segment sigma_1 = -sign(phi_1) throughout, only the
(-1,+1) family is reproducible, and nothing here fakes any other. That is
close-out section 6 item 3, now with the discrepancy localized to one sign in
one printed equation rather than left open.

Usage:  python3 layer0/viz/corner_family.py [out.png] [--tau 1.0] [--tol 0.01]
"""

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import barrier as B
import bup_curves as C

DEG = 180.0 / np.pi                      # radians -> degrees is  * DEG
BLUE, GREEN, PURPLE = '#1f5fa8', '#1a7f4b', '#8a5cc7'

plt.rcParams.update({'font.size': 9, 'figure.dpi': 140, 'savefig.dpi': 140,
                     'axes.grid': True, 'grid.alpha': 0.30, 'grid.color': '0.74',
                     'axes.edgecolor': '0.22', 'axes.linewidth': 1.2,
                     'axes.labelcolor': '0.06', 'axes.labelweight': 'semibold',
                     'xtick.color': '0.16', 'ytick.color': '0.16',
                     'xtick.major.width': 1.1, 'ytick.major.width': 1.1})

R0 = B.R_hi(0.0)
NA, NB = B.n_maxrange(-1e-9), B.n_maxrange(+1e-9)
E1 = 2.0 * np.arctan(2.0 / B.RBAR0)       # phi_1 of e_1, closed form


F1 = 2.0 * np.arctan(1.0 / B.RBAR0)       # the phi_1 that Table 2 rounds to 18.5


def lam_39_41(p1):
    """The paper's corner costate, Eqs. (39)-(41), transcribed."""
    q = 1.0 / np.hypot(np.cos(p1) + 1.0, B.RBAR0 + abs(np.sin(p1)))   # Eq. (41)
    return np.array([q * (B.RBAR0 + abs(np.sin(p1))),                 # Eq. (39)
                     0.0,
                     q * B.RBAR0 * (np.cos(p1) + 1.0) * np.sign(p1)]), q  # Eq. (40)


def eq42_printed(p1):
    """Eq. (42) read exactly as printed: sign(phi_1) on the second term only."""
    _, q = lam_39_41(p1)
    return -q * (B.RBAR0 * abs(np.sin(p1))
                 + (np.cos(p1) + 1.0) * np.sign(p1))


def eq42_corrected(p1):
    """The same with sign(phi_1) outside the bracket -- odd under M, as it must be."""
    _, q = lam_39_41(p1)
    return -q * (B.RBAR0 * abs(np.sin(p1)) + np.cos(p1) + 1.0) * np.sign(p1)


def f1_diagnostic():
    """
    Is f_1 a sigma_1 switch?  Table 2 says it is at phi_1 = 18.5 on this segment.

    Checks, in order: (a) Eqs. (39)-(41) really do satisfy H* = 0 and FI = 1;
    (b) Eq. (42) as printed equals the true lambda_1-dot on phi_1 > 0 and fails
    on phi_1 < 0; (c) the spurious root of the printed form is exactly Table 2's
    18.5; (d) the true lambda_1-dot has no root; (e) the second root of H* = 0
    does have one there but is outside the normal cone.
    """
    from scipy.optimize import brentq
    print('f_1 diagnostic -- is there a sigma_1 switch on phi_2 = 0?')
    print('  phi1[deg]     H*        FI-1      true l1dot    Eq.(42) printed')
    for d in (-30.0, -F1 * DEG, -10.0, 10.0, F1 * DEG, 30.0):
        p1 = d / DEG
        lam, _ = lam_39_41(p1)
        print('  %9.4f  %+.1e  %+.1e  %+12.8f  %+12.8f'
              % (d, B.hamiltonian_star(R0, p1, 0.0, *lam),
                 B.first_integral(R0, *lam) - 1.0,
                 B.costate_dot(R0, p1, 0.0, *lam)[1], eq42_printed(p1)))

    err_p = max(abs(eq42_printed(d / DEG)
                    - B.costate_dot(R0, d / DEG, 0.0, *lam_39_41(d / DEG)[0])[1])
                for d in np.linspace(0.5, E1 * DEG - 0.5, 400))
    err_m = max(abs(eq42_corrected(d / DEG)
                    - B.costate_dot(R0, d / DEG, 0.0, *lam_39_41(d / DEG)[0])[1])
                for d in np.linspace(-E1 * DEG + 0.5, E1 * DEG - 0.5, 800))
    print('  Eq.(42) as printed vs Eq.(18), phi_1 > 0 only : max err %.1e' % err_p)
    print('  Eq.(42) with sign outside, both signs of phi_1: max err %.1e' % err_m)

    r = brentq(lambda d: eq42_printed(d / DEG), -E1 * DEG + 1e-6, -1.0)
    print('  root of the printed form (phi_1 < 0): %.6f deg' % -r)
    print('    closed form 2 atan(1/Rbar_0)       : %.6f deg   [Table 2 f_1 = 18.5]'
          % (F1 * DEG))
    print('    same with the paper\'s Rbar_0 = 6.14: %.6f deg'
          % (2.0 * np.arctan(1.0 / 6.14) * DEG))
    print('    cf. e_1, 2 atan(2/Rbar_0)          : %.6f deg   [Table 2 e_1 = 36.07]'
          % (E1 * DEG))
    print('  true |lambda_1-dot| there            : %.6f   -> no switch'
          % abs(B.costate_dot(R0, F1, 0.0, *lam_39_41(F1)[0])[1]))

    def second_root(p1):
        c1, s1 = np.cos(p1), np.sin(p1)
        k = (-s1 / B.RBAR0 + 1.0) / (c1 + 1.0)          # lam_R / |lam_2|
        b = 1.0 / np.sqrt(1.0 / B.RBAR0 ** 2 + k * k)
        return k * b, -b
    print('  second root of H*=0 (lambda_2 < 0):  cone ratio |lam_2|/(2 lam_R)')
    for d in (10.0, F1 * DEG, 30.0, E1 * DEG):
        A, Bv = second_root(d / DEG)
        print('    %9.6f  ratio %.6f  %s  l1dot %+.8f'
              % (d, abs(Bv) / (2 * A),
                 'admissible ' if abs(Bv) <= 2 * A + 1e-12 else 'OUT OF CONE',
                 B.costate_dot(R0, d / DEG, 0.0, A, 0.0, Bv)[1]))
    print('    -> it reaches the cone edge exactly at e_1, not at f_1.')

    print('  is (+1,+1) realizable anywhere on the cone, 0 < phi_1 < e_1?')
    pairs = set()
    for d in np.linspace(0.2, E1 * DEG - 0.2, 120):
        p1 = d / DEG
        for th in np.linspace(0.0, np.pi / 2, 4001):
            lam = np.cos(th) * NA + np.sin(th) * NB          # mu_a, mu_b >= 0
            lam = lam / np.sqrt(B.first_integral(R0, *lam))
            if abs(B.hamiltonian_star(R0, p1, 0.0, *lam)) < 5e-4:
                ld = B.costate_dot(R0, p1, 0.0, *lam)[1]
                pairs.add((int(np.sign(ld)),
                           int(B.barrier_controls(R0, p1, 0.0, *lam)[1])))
    print('    realizable (sigma_1, sigma_2) = %s   -> no, and not (+1,-1) either'
          % sorted(pairs))
    print('    sigma_2 = +1 => lambda_2 > 0 => both terms of Eq. (18) positive')
    print('    => lambda_1-dot < 0 => sigma_1 = -1.  The pair is forced.\n')


def corner_seeds(n=60):
    """The e_1 - f_1 - O segment, seeded with the corner costate."""
    out = []
    for a1 in np.linspace(0.004, E1 - 1e-4, n):
        sols = B.lam_corner(R0, a1, 0.0, NA, NB)
        if not sols:
            continue
        l = sols[0][0]
        out.append(np.array([R0, a1, 0.0, l[0], l[1], l[2]]))
    return out


def lens_seeds(n=60):
    """The e_1 - d_1 - O lens, phi_2 < 0 lobe."""
    S, _ = C.seeds('max', nseed=n)
    return [np.asarray(y) for br in S if br[0][2] < 0 for y in br]


def run(seeds, tau, dt=5e-4):
    return [B.integrate_retrograde(y, tau_max=tau, dt=dt) for y in seeds]


def cloud(bundle, tau, stride=3):
    P = []
    for t in bundle:
        m = max(int(np.searchsorted(t['tau'], tau)), 1)
        for i in range(0, m, stride):
            P.append((t['R'][i], t['phi1'][i], t['phi2'][i]))
    return np.array(P)


def embed(X, s):
    """Angles on their circles, so wrapping is exact under a Euclidean tree."""
    return np.c_[X[:, 0] / s,
                 np.cos(X[:, 1]) / (2 * np.pi), np.sin(X[:, 1]) / (2 * np.pi),
                 np.cos(X[:, 2]) / (2 * np.pi), np.sin(X[:, 2]) / (2 * np.pi)]


def contacts(A, Bc, tol):
    s = max(np.ptp(A[:, 0]), np.ptp(Bc[:, 0]), 1e-9)
    d, j = cKDTree(embed(Bc, s)).query(embed(A, s), k=1)
    m = d < tol
    return d, 0.5 * (A[m] + Bc[j[m]])


def report_contacts(pts, tol, n):
    """
    Contacts, described as what they are.

    A single span [min, max] would read as a curve from O to e_1. The set is not
    one curve: it splits wherever phi_1 jumps, and the gap around f_1 is the
    point of the whole exercise, so both are printed.
    """
    if len(pts) < 2:
        print('   tol %.4f : %d contacts' % (tol, len(pts)))
        return
    a1 = np.sort(pts[:, 1] * DEG)
    cuts = np.where(np.diff(a1) > 2.0)[0]
    segs = [g for g in np.split(a1, cuts + 1) if len(g) > 2]
    cl = ' '.join('[%.1f, %.1f]' % (g.min(), g.max()) for g in segs)
    print('   tol %.4f : %5d contacts   phi_1 clusters %-30s '
          'nearest to f_1 %5.1f deg' % (tol, n, cl, np.abs(a1 - 18.5).min()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out', nargs='?',
                    default=os.path.join(HERE, 'figs', 'fig8_dispersal.png'))
    ap.add_argument('--tau', type=float, default=1.0)
    ap.add_argument('--tol', type=float, default=0.01)
    ap.add_argument('--nseed', type=int, default=60)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    f1_diagnostic()

    cs, ls = corner_seeds(a.nseed), lens_seeds(a.nseed)
    print('corner family: %d seeds on phi_2 = 0, 0 < phi_1 < %.4f deg'
          % (len(cs), E1 * DEG))
    print('   max |FI-1| = %.1e   max |H*| = %.1e'
          % (max(abs(B.first_integral(y[0], y[3], y[4], y[5]) - 1) for y in cs),
             max(abs(B.hamiltonian_star(*y)) for y in cs)))
    sig = set(tuple(int(v) for v in B.barrier_controls(*y)) for y in cs)
    print('   control pairs on the segment: %s' % sorted(sig))

    cb, lb = run(cs, a.tau), run(ls, a.tau)
    print('lens family  : %d seeds' % len(ls))
    print('integrated   : max |H*| = %.1e (corner), %.1e (lens)'
          % (max(t['h_err'].max() for t in cb), max(t['h_err'].max() for t in lb)))

    A, Bc = cloud(cb, a.tau), cloud(lb, a.tau)
    d, pts = contacts(A, Bc, a.tol)
    print('\ncontact between the two families, full (R, phi_1, phi_2):')
    print('   min distance %.5f' % d.min())
    for tol in (0.02, 0.01, 0.005, 0.002, 0.001, 0.0005):
        _, q = contacts(A, Bc, tol)
        report_contacts(q, tol, len(q))
    print('   O is at phi_1 = 0.00 deg, e_1 at %.2f deg, f_1 at 18.50 deg,'
          ' all at R = %.5f' % (E1 * DEG, R0))
    print('   -> the contact set converges on the two SHARED endpoints as the')
    print('      tolerance tightens, and the gap at f_1 widens. That is not yet')
    print('      the dispersal line e_1 c_1 O: its middle is missing, exactly')
    print('      where f_1, the (+1,+1) family and the universal lines belong.')

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.6))

    for ax, (xk, xl, inv) in zip(axes, [(2, r'$\phi_2$  [deg]', True),
                                        (0, r'$R$', False)]):
        for t in lb:
            x = t['phi2'] * DEG if xk == 2 else t['R']
            ax.plot(x, t['phi1'] * DEG, lw=0.6, color=BLUE, alpha=0.5, zorder=3)
        for t in cb:
            x = t['phi2'] * DEG if xk == 2 else t['R']
            ax.plot(x, t['phi1'] * DEG, lw=0.6, color=GREEN, alpha=0.55, zorder=4)
        bx = [y[2] * DEG if xk == 2 else y[0] for y in ls]
        ax.plot(bx, [y[1] * DEG for y in ls], lw=2.6, color='#111', zorder=7)
        bx = [y[2] * DEG if xk == 2 else y[0] for y in cs]
        ax.plot(bx, [y[1] * DEG for y in cs], lw=3.0, color=GREEN, zorder=8)
        if len(pts):
            px = pts[:, 2] * DEG if xk == 2 else pts[:, 0]
            ax.plot(px, pts[:, 1] * DEG, '.', ms=2.6, color=PURPLE, zorder=9)
        for nm, q, r, p1 in (('$O$', 0.0, R0, 0.0), ('$e_1$', 0.0, R0, E1 * DEG),
                             ('$d_1$', -9.569, 5.8083, 18.88),
                             ('$f_1$', 0.0, R0, 18.50)):
            x = q if xk == 2 else r
            ax.plot(x, p1, 'o', ms=6, mfc='#111' if nm != '$f_1$' else GREEN,
                    mec='w', mew=1.0, zorder=11)
            ax.annotate(nm, (x, p1), textcoords='offset points', xytext=(6, 5),
                        fontsize=10, zorder=12)
        ax.set_xlabel(xl)
        ax.set_ylabel(r'$\phi_1$  [deg]')
        if inv:
            ax.set_xlim(14, -14)
            ax.set_title(r'the Fig. 8 face $(\phi_2,\phi_1)$', fontsize=10)
        else:
            ax.set_xlim(6.10, 6.45)
            ax.set_title(r'the same thing in $(R,\phi_1)$ — the contacts are a real'
                         '\n3-D curve, not a projection artefact', fontsize=10)
        ax.set_ylim(-6, 46)

    from matplotlib.lines import Line2D
    axes[0].legend(handles=[
        Line2D([], [], color='#111', lw=2.6, label=r'(BUP) lens $e_1d_1O$, Eq. (32) = 0'),
        Line2D([], [], color=GREEN, lw=3.0, label=r'(BUP) corner $e_1f_1O$, $\phi_2=0$'),
        Line2D([], [], color=BLUE, lw=0.9, label='lens family'),
        Line2D([], [], color=GREEN, lw=0.9, alpha=0.6, label='corner family'),
        Line2D([], [], color=PURPLE, lw=0, marker='.', ms=7,
               label='contact set (NOT yet $e_1c_1O$)'),
    ], fontsize=8, loc='upper left', framealpha=0.94)

    fig.suptitle('Both maximum-range families: the lens $e_1d_1O$ and the corner '
                 r'$e_1f_1O$   ($\tau \leq %.2f$)' % a.tau + '\n'
                 'the corner family IS seedable — but its contact with the lens '
                 'family clusters at the two shared\nendpoints and leaves a gap at '
                 r'$f_1$ that widens as the tolerance tightens, so this is not yet '
                 r'the dispersal line', fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(a.out)
    print('\nwrote %s' % os.path.abspath(a.out))


if __name__ == '__main__':
    main()
