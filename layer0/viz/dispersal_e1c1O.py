"""
dispersal_e1c1O.py -- the evader dispersal line e_1 c_1 O of D&S Fig. 8, solved.

Two barrier sheets meet along it (Table 3: e_1 c_1 with (-1,-1)(-1,+1)):

    corner sheet   (-1,+1)  trajectories from the phi_2 = 0 edge O - e_1
    (-1,-1) sheet            lens-outer trajectories from e_1 - d_1, CONTINUED by
                             trajectories that ride the d_1 universal line and peel
                             off it with sigma_1 = -1
    (+1,-1) sheet            lens-inner trajectories from d_1 - O, continued by
                             peel-offs with sigma_1 = +1

The peel-offs are the piece the earlier contact test did not have. On the
universal line lambda_1 = lambda_1-dot = 0 and lambda_1-ddot = A sigma_1 with
A = -1, so leaving it with sigma_1 = -1 makes lambda_1 > 0 and with sigma_1 = +1
makes lambda_1 < 0 -- both self-consistent with sigma_1* = -sign(lambda_1). Every
point of the universal line launches one trajectory into each side.

Intersections are solved EXACTLY, not by point-cloud proximity: for each member
of the (-/+1,-1) sheet, find (s, tau_C, tau_B) with

    X_corner(s, tau_C) = X_member(tau_B)          3 equations, 3 unknowns

State flows with fixed controls are all that is needed (controls are constant on
every member over this range -- checked: zero switches for tau <= 0.6).

Usage:  python3 layer0/viz/dispersal_e1c1O.py [out.png]
"""

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import barrier as B
import universal_d1 as U

DEG = 180.0 / np.pi
R0 = B.RBAR0
E1 = 2.0 * np.arctan(2.0 / R0)

plt.rcParams.update({'font.size': 9, 'figure.dpi': 140, 'savefig.dpi': 140,
                     'axes.grid': True, 'grid.alpha': 0.30, 'grid.color': '0.74',
                     'axes.edgecolor': '0.22', 'axes.linewidth': 1.2,
                     'axes.labelcolor': '0.06', 'axes.labelweight': 'semibold'})


def flow(x0, sig, tau):
    """Retrograde state flow with the control pair held fixed."""
    x0 = np.asarray(x0, float)
    if tau == 0:
        return x0
    f = lambda t, x: -np.array(B.state_dot(x[0], x[1], x[2], *sig))
    return solve_ivp(f, (0, tau), x0, rtol=1e-12, atol=1e-14).y[:, -1]


def corner_point(s, tau_c):
    """A point of the (-1,+1) corner sheet: seed phi_1 = s on the edge, time tau_c."""
    return flow([R0, s, 0.0], (-1.0, 1.0), tau_c)


def meet(x0, sig, guess):
    """Solve corner_point(s, tau_C) = flow(x0, sig, tau_B). Returns (v, residual, ok)."""
    F = lambda v: corner_point(v[0], v[1]) - flow(x0, sig, v[2])
    v, _, ier, _ = fsolve(F, guess, full_output=True, xtol=1e-13)
    res = np.abs(F(v)).max()
    ok = ier == 1 and res < 1e-10 and v[1] > 0 and v[2] >= 0 and 0 < v[0] < E1
    return v, res, ok


def lens_member(q, outer):
    """Seed state on the lens at phi_2 = q; outer root (e_1 side) or inner (O side)."""
    r = B.bup_maxrange(q)
    return np.array([B.R_hi(q), max(r) if outer else min(r), q])


def sweep(members, sig, guess):
    """Solve the meeting for an ordered list of (label, param, x0). Continuation guess."""
    out = []
    for lab, par, x0, tb_guess in members:
        g = [guess[0], guess[1], tb_guess if guess[2] is None else guess[2]]
        v, res, ok = meet(x0, sig, g)
        for frac in (None, 0.25, 0.5, 0.75, 1.0):     # retries: fresh guesses
            if ok:
                break
            s_g = guess[0] if frac is None else frac * x0[1] + (1 - frac) * guess[0]
            v, res, ok = meet(x0, sig, [s_g, max(guess[1], 1e-5), tb_guess])
        if ok:
            guess = [v[0], v[1], None]
        out.append(dict(member=lab, param=par, s=v[0], tau_c=v[1], tau_b=v[2],
                        res=res, ok=ok, x=corner_point(v[0], v[1])))
    return out


def dispersal_line(n_lens=40, n_peel=35):
    """Both halves, each ordered from the far end to c_1."""
    yd = U.d1_seed()
    Tu, Yu = U.integrate_universal(yd, 0.2, dt=2e-5)
    peel = [(t, Yu[np.argmin(abs(Tu - t)), :3]) for t in np.linspace(0, 0.1726, n_peel)]

    outer = [('lens', q * DEG, lens_member(q, True), abs(q) / 0.95)
             for q in np.linspace(-2e-4, yd[2] + 1e-5, n_lens)]
    outer += [('peel', t, x, max(0.1727 - t, 1e-4)) for t, x in peel]
    upper = sweep(outer, (-1.0, -1.0), [E1 - 1e-3, 1e-4, None])

    inner = [('lens', q * DEG, lens_member(q, False), abs(q))
             for q in np.linspace(-2e-4, yd[2] + 1e-5, n_lens)]
    lower = sweep(inner, (1.0, -1.0), [1e-5, 1e-6, None])
    lower += sweep([('peel', t, x, max(0.1727 - t, 1e-4)) for t, x in peel],
                   (1.0, -1.0), [8.8 / DEG, 9e-4, None])
    return yd, Tu, Yu, upper, lower


def c1_point(yd):
    """Where the d_1 universal line itself crosses the corner sheet."""
    v, res, ok = meet(yd[:3], (0.0, -1.0), [18.43 / DEG, 1.1e-3, 0.1727])
    return v, res, ok, corner_point(v[0], v[1])


def sheet_angle(p):
    """Angle between corner-sheet tangent plane and the member's flow line direction."""
    h = 1e-6
    a = (corner_point(p['s'] + h, p['tau_c']) - corner_point(p['s'] - h, p['tau_c'])) / (2 * h)
    b = (corner_point(p['s'], p['tau_c'] + h) - corner_point(p['s'], p['tau_c'] - h)) / (2 * h)
    n = np.cross(a, b)
    n /= np.linalg.norm(n)
    return n


def report(yd, upper, lower, c1):
    v, res, ok, x = c1
    print('c_1 = d_1 universal line  x  corner sheet   (residual %.0e, %s)'
          % (res, 'valid' if ok else 'INVALID'))
    print('   R %.5f   phi_1 %.4f deg   phi_2 %+.4f deg     R - Rbar %.2e'
          % (x[0], x[1] * DEG, x[2] * DEG, x[0] - B.R_hi(x[2])))
    print('   distance to f_1 (Table 2 / 2 atan(1/Rbar_0)): %.1e' % np.linalg.norm(
        x - [R0, U.F1, 0.0]))
    print('   Table 2 c_1 = (5.925, 18.7, +4.78)  -- inside T, see universal_d1.py')

    for name, part, sig in (('e_1 -> c_1', upper, '(-1,-1) x (-1,+1)'),
                            ('O -> c_1', lower, '(+1,-1) x (-1,+1)')):
        good = [p for p in part if p['ok']]
        X = np.array([p['x'] for p in good])
        print('\n%s   sheets %s   %d/%d members meet the corner sheet'
              % (name, sig, len(good), len(part)))
        print('   max residual %.0e' % max(p['res'] for p in good))
        print('   phi_1 from %.4f to %.4f deg' % (X[:, 1].min() * DEG, X[:, 1].max() * DEG))
        print('   R - Rbar_0 in [%.1e, %.1e]    phi_2 in [%.4f, %.4f] deg'
              % ((X[:, 0] - R0).min(), (X[:, 0] - R0).max(),
                 X[:, 2].min() * DEG, X[:, 2].max() * DEG))
        print('   tau on corner sheet <= %.4f   -- it hugs the phi_2 = 0 edge'
              % max(p['tau_c'] for p in good))
        bad = [p for p in part if not p['ok']]
        if bad:
            print('   %d members give no valid meeting: %s near %s' % (
                len(bad), bad[0]['member'],
                ', '.join('%.2f' % p['param'] for p in bad[:3])))


def figure(yd, Tu, Yu, upper, lower, c1, out):
    x_c1 = c1[3]
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2))
    DISP, UNIV, CORN = '#c1442a', '#8a1c7c', '#1a7f4b'

    ax = axes[0]
    xs, lo, hi = [], [], []
    for v in np.linspace(-0.1675, -1e-4, 300):
        r = B.bup_maxrange(v)
        if len(r) >= 2:
            xs.append(v * DEG); lo.append(min(r) * DEG); hi.append(max(r) * DEG)
    ax.plot(xs + xs[::-1], lo + hi[::-1], color='#111', lw=1.6, label='(BUP) lens')
    ax.plot([0, 0], [0, E1 * DEG], color=CORN, lw=2.2, ls=(0, (6, 3)),
            label=r'corner edge $O$–$e_1$')
    k = Tu <= 0.1727
    ax.plot(Yu[k, 2] * DEG, Yu[k, 1] * DEG, color=UNIV, lw=2.2, label=r'universal line $d_1c_1$')
    for part in (upper, lower):
        X = np.array([p['x'] for p in part if p['ok']])
        ax.plot(X[:, 2] * DEG, X[:, 1] * DEG, color=DISP, lw=2.6, ls='--')
    ax.plot([], [], color=DISP, lw=2.6, ls='--', label=r'dispersal line $e_1c_1O$')
    ax.set_xlim(2, -12)
    ax.set_ylim(-2, 40)
    ax.set_title(r'Fig. 8 face — the dispersal line lies on the $\phi_2=0$ axis', fontsize=10)

    ax = axes[1]
    for part in (upper, lower):
        X = np.array([p['x'] for p in part if p['ok']])
        ax.plot(X[:, 2] * DEG, X[:, 1] * DEG, color=DISP, lw=2.6, ls='--')
    ax.plot(Yu[:, 2] * DEG, Yu[:, 1] * DEG, color=UNIV, lw=2.2)
    ax.axvline(0, color=CORN, lw=2.2, ls=(0, (6, 3)))
    ax.set_xlim(0.03, -0.12)
    ax.set_ylim(-2, 40)
    ax.set_title(r'zoom: $\phi_2$ axis magnified $\times$100', fontsize=10)

    ax = axes[2]
    for part in (upper, lower):
        X = np.array([p['x'] for p in part if p['ok']])
        ax.plot((X[:, 0] - R0) * 1e3, X[:, 1] * DEG, color=DISP, lw=2.6, ls='--')
    ax.plot((Yu[:, 0] - R0) * 1e3, Yu[:, 1] * DEG, color=UNIV, lw=2.2)
    ax.axvline(0, color=CORN, lw=2.2, ls=(0, (6, 3)))
    ax.set_xlim(-6, 8)
    ax.set_ylim(-2, 40)
    ax.set_xlabel(r'$(R-\bar R_0)\times 10^3$')
    ax.set_title(r'range clearance above the corner edge', fontsize=10)

    for i, ax in enumerate(axes):
        pts = [('$e_1$', 0.0, R0, E1 * DEG), ('$O$', 0.0, R0, 0.0),
               ('$f_1$', 0.0, R0, U.F1 * DEG),
               ('$c_1$', x_c1[2] * DEG, x_c1[0], x_c1[1] * DEG),
               ('$d_1$', yd[2] * DEG, yd[0], yd[1] * DEG)]
        for nm, q, r, p1 in pts:
            xv = q if i < 2 else (r - R0) * 1e3
            if i == 2 and nm == '$d_1$':
                continue
            if i == 1 and nm == '$d_1$':
                continue
            ax.plot(xv, p1, 'o', ms=6, mfc='#111', mec='w', zorder=9)
            ax.annotate(nm, (xv, p1), textcoords='offset points',
                        xytext=(-16 if nm == '$c_1$' else 6, 5), fontsize=9.5)
        ax.set_ylabel(r'$\phi_1$  [deg]')
        if i < 2:
            ax.set_xlabel(r'$\phi_2$  [deg]   (increasing to the left)')
    axes[0].legend(fontsize=7.5, loc='lower left', framealpha=0.94)
    fig.tight_layout()
    fig.savefig(out)
    print('\nwrote %s' % os.path.abspath(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out', nargs='?', default=os.path.join(HERE, 'figs', 'dispersal_e1c1O.png'))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    yd, Tu, Yu, upper, lower = dispersal_line()
    c1 = c1_point(yd)
    report(yd, upper, lower, c1)
    figure(yd, Tu, Yu, upper, lower, c1, a.out)


if __name__ == '__main__':
    main()
