"""
universal_d1.py -- the universal line of player 1 that terminates at d_1.

D&S Sec. 4.1 / Table 3: two universal lines of the pursuer, c_1 d_1 with
strategies (0,-1) and f_1 c_1 with (0,+1). This file propagates the first one
backward from d_1 with a genuine singular control -- nothing bang-bang, nothing
assigned -- and reports where it goes.

THE SINGULAR CONTROL (derived symbolically, see singular_control_coeffs):
with lambda_1 = 0, the second time derivative of lambda_1 is

    lambda_1-ddot = A * sigma_1,      A = -lambda_R cos phi_1 + lambda_2 sin phi_1 / R

with no sigma-free term at all. So keeping lambda_1 = lambda_1-dot = 0 requires
sigma_1 = 0 exactly -- Table 3's "0" -- and {lambda_1 = lambda_1-dot = 0} is then
invariant. sigma_2 = sign(lambda_2) as usual.

CLOSED FORM ON THE LINE: lambda_1-dot = 0 and FI = 1 give
    lambda = (cos phi_1, 0, -R sin phi_1),   A = -1,
held by the integrator to 5e-13. A never vanishes, so the arc never degenerates.

Usage:  python3 layer0/viz/universal_d1.py [out.png] [--tau 0.6]
"""

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import barrier as B

DEG = 180.0 / np.pi                        # radians -> degrees is  * DEG
R0 = B.RBAR0
F1 = 2.0 * np.arctan(1.0 / R0)             # Table 2 f_1 = 18.5 deg
C1_TABLE = (5.925, 18.7, 4.78)             # Table 2, as printed

plt.rcParams.update({'font.size': 9, 'figure.dpi': 140, 'savefig.dpi': 140,
                     'axes.grid': True, 'grid.alpha': 0.30, 'grid.color': '0.74',
                     'axes.edgecolor': '0.22', 'axes.linewidth': 1.2,
                     'axes.labelcolor': '0.06', 'axes.labelweight': 'semibold'})


def singular_control_coeffs():
    """lambda_1-ddot at lambda_1 = 0, split as A*sigma_1 + Bc. Returns (A, Bc)."""
    import sympy as sp
    R, p1, p2, lR, l1, l2, s1, s2 = sp.symbols('R p1 p2 lR l1 l2 s1 s2', real=True)
    L, S = sp.sin(p1) + sp.sin(p2), l1 + l2
    f = [-(sp.cos(p1) + sp.cos(p2)), L / R + s1, L / R + s2]
    g = [L * S / R**2, -(lR * sp.sin(p1) + sp.cos(p1) * S / R),
         -(lR * sp.sin(p2) + sp.cos(p2) * S / R)]
    X = [R, p1, p2, lR, l1, l2]
    l1dd = sum(sp.diff(g[1], x) * fx for x, fx in zip(X, f + g))
    l1dd = sp.simplify(sp.expand(l1dd).subs(l1, 0))
    return sp.simplify(sp.diff(l1dd, s1)), sp.simplify(l1dd.subs(s1, 0))


def l1dot_on_bup(p1, p2):
    """lambda_1-dot on the maximum-range BUP, from the transversality costate."""
    lR, l1, l2 = B.lam_maxrange(p2)
    return B.costate_dot(B.R_hi(p2), p1, p2, lR, l1, l2)[1]


def d1_seed():
    """d_1: Eq. (32) = 0 and lambda_1-dot = 0, phi_2 < 0 lobe. Full 6-vector."""
    p1, p2 = fsolve(lambda v: [B.up_maxrange(*v), l1dot_on_bup(*v)],
                    [18.88 / DEG, -9.57 / DEG], xtol=1e-13)
    return np.array([B.R_hi(p2), p1, p2, *B.lam_maxrange(p2)])


def universal_costate(R, p1):
    """lambda_1 = lambda_1-dot = 0 with FI = 1, lambda_R > 0."""
    return np.array([np.cos(p1), 0.0, -R * np.sin(p1)])


def integrate_universal(y0, tau_max, dt=2e-5):
    """Retrograde RK4 with sigma = (0, sign lambda_2) held; stops if lambda_2 flips."""
    s2 = float(np.sign(y0[5]))
    y = np.array(y0, float)
    T, Y = [0.0], [y.copy()]
    for i in range(int(round(tau_max / dt))):
        y = B._rk4_retro(y, dt, (0.0, s2))
        if np.sign(y[5]) != s2:
            break
        T.append((i + 1) * dt)
        Y.append(y.copy())
    return np.array(T), np.array(Y)


def invariants(Y):
    """max |lambda_1|, |lambda_1-dot|, |FI-1|, |H*|, and |lambda - closed form|."""
    l1d = np.array([B.costate_dot(*y)[1] for y in Y])
    fi = B.first_integral(Y[:, 0], Y[:, 3], Y[:, 4], Y[:, 5]) - 1
    hs = B.hamiltonian_star(*Y.T)
    cf = np.abs(Y[:, 3:] - np.array([universal_costate(y[0], y[1]) for y in Y]))
    return dict(l1=np.abs(Y[:, 4]).max(), l1dot=np.abs(l1d).max(),
                fi=np.abs(fi).max(), h=np.abs(hs).max(), closed=cf.max())


def at_phi2(T, Y, val_deg):
    """Linear interpolation of the line where phi_2 crosses val_deg. (tau, y) or None."""
    f = Y[:, 2] - val_deg / DEG
    i = np.where(np.diff(np.sign(f)) != 0)[0]
    if not len(i):
        return None
    i = i[0]
    w = f[i] / (f[i] - f[i + 1])
    return T[i] + w * (T[i + 1] - T[i]), Y[i] + w * (Y[i + 1] - Y[i])


def corner_H_universal(p1):
    """H* of the universal costate placed on the corner (R0, p1, 0). Closed form."""
    return R0 * np.sin(p1) - 1.0 - np.cos(p1)


def report(Td, Yd, Tf, Yf):
    y0 = Yd[0]
    print('d_1 = (R %.5f, phi_1 %.4f, phi_2 %.4f)   Table 2: (5.808, 18.88, -9.56)'
          % (y0[0], y0[1] * DEG, y0[2] * DEG))
    A, Bc = singular_control_coeffs()
    print('lambda_1-ddot | lambda_1=0  =  (%s) * sigma_1  +  (%s)' % (A, Bc))
    print('  -> sigma_1 = 0 on the universal line (Table 3: "0")')

    inv = invariants(Yd)
    print('\nd_1 universal line, sigma = (0,-1), tau <= %.2f' % Td[-1])
    print('  max |lambda_1| %.1e  |lambda_1-dot| %.1e  |FI-1| %.1e  |H*| %.1e'
          % (inv['l1'], inv['l1dot'], inv['fi'], inv['h']))
    print('  max |lambda - (cos phi_1, 0, -R sin phi_1)| = %.1e' % inv['closed'])
    gap = Yd[:, 0] - B.R_hi(Yd[:, 2])
    print('  stays outside T: min (R - Rbar) over tau > 0 = %.1e'
          % gap[1:].min())

    print('\n  where it goes (retrograde from d_1):')
    for v in (-4.78, 0.0, 4.78):
        t, y = at_phi2(Td, Yd, v)
        print('    phi_2 = %+5.2f :  tau %.4f   R %.4f   phi_1 %.3f   R - Rbar %+.4f'
              % (v, t, y[0], y[1] * DEG, y[0] - B.R_hi(y[2])))
    f1 = np.array([R0, F1, 0.0])
    d = np.linalg.norm(Yd[:, :3] - f1, axis=1)
    i = np.argmin(d)
    print('  closest approach to f_1 = (%.4f, %.4f, 0): %.1e  at (%.5f, %.4f, %+.3f)'
          % (R0, F1 * DEG, d[i], *Yd[i, :3] * [1, DEG, DEG]))

    print('\nTable 2 c_1 = (%.3f, %.1f, %+.2f) as printed' % C1_TABLE)
    R, a1, a2 = C1_TABLE
    print('  in T? %s  (Rbar(4.78 deg) = %.4f > 5.925: it is INSIDE the target set)'
          % (bool(B.in_target(a1 / DEG, a2 / DEG, R)), B.R_hi(a2 / DEG)))
    t, y = at_phi2(Td, Yd, -a2)
    print('  line at phi_2 = %+.2f matches phi_1 = %.3f (table %.1f), R = %.4f'
          % (-a2, y[1] * DEG, a1, y[0]))

    print('\nf_1 on the corner, with the universal costate:')
    lu = universal_costate(R0, F1)
    print('  H* = Rbar_0 sin phi_1 - 1 - cos phi_1 = 0  <=>  Rbar_0 tan(phi_1/2) = 1')
    print('  at f_1: H* %.1e  FI-1 %.1e  lambda_1-dot %.1e   cone ratio %.4f (> 1)'
          % (B.hamiltonian_star(R0, F1, 0.0, *lu), B.first_integral(R0, *lu) - 1,
             B.costate_dot(R0, F1, 0.0, *lu)[1], abs(lu[2]) / (2 * lu[0])))
    inv = invariants(Yf)
    print('  f_1 universal line (0,-1): max |H*| %.1e  |lambda_1| %.1e  |closed| %.1e'
          % (inv['h'], inv['l1'], inv['closed']))
    from scipy.spatial import cKDTree
    dd, _ = cKDTree(Yf[:, :3]).query(Yd[:, :3])
    k = Td > 0.2
    print('  distance d_1 line <-> f_1 line for tau > 0.2: %.2e .. %.2e'
          % (dd[k].min(), dd[k].max()))
    print('  -> same controls, same autonomous state ODE: parallel, never meeting.')
    lp = -lu
    print('  a (0,+1) universal costate at f_1 would be %s: lambda_R < 0, H* = %.3f'
          % (np.round(lp, 4), B.hamiltonian_star(R0, F1, 0.0, *lp)))


def figure(Td, Yd, Tf, Yf, out):
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.4))
    q = np.linspace(-0.2, 0.2, 801)
    for ax, mode in zip(axes, ('face', 'range')):
        for T, Y, col, nm in ((Td, Yd, '#8a1c7c', r'universal line from $d_1$, $(0,-1)$'),
                              (Tf, Yf, '#e08a00', r'universal line from $f_1$, $(0,-1)$')):
            x = Y[:, 2] * DEG
            yv = Y[:, 1] * DEG if mode == 'face' else Y[:, 0]
            ax.plot(x, yv, lw=2.2, color=col, label=nm, zorder=5)
        if mode == 'face':
            for sgn in (-1, 1):
                xs, lo, hi = [], [], []
                for v in np.linspace(1e-4, 0.1675, 300) * sgn:
                    r = B.bup_maxrange(v)
                    if len(r) >= 2:
                        xs.append(v * DEG); lo.append(min(r) * DEG); hi.append(max(r) * DEG)
                ax.plot(xs + xs[::-1], lo + hi[::-1], color='#111', lw=1.6, zorder=3)
            ax.plot([0, 0], [0, 36.08], color='#1a7f4b', lw=2.4, ls=(0, (6, 3)), zorder=4)
            pts = (('$d_1$', Yd[0, 2] * DEG, Yd[0, 1] * DEG), ('$f_1$', 0.0, F1 * DEG),
                   ('$e_1$', 0.0, 36.08), ('$O$', 0.0, 0.0),
                   ('$c_1$ (Table 2)', C1_TABLE[2], C1_TABLE[1]))
            ax.set_ylabel(r'$\phi_1$  [deg]')
            ax.set_ylim(-4, 40)
            ax.set_title(r'Fig. 8 face $(\phi_2,\phi_1)$', fontsize=10)
        else:
            ax.plot(q * DEG, B.R_hi(q), color='#111', lw=1.6,
                    label=r'$\bar R(\phi_2)$, max-range surface')
            pts = (('$d_1$', Yd[0, 2] * DEG, Yd[0, 0]), ('$f_1$', 0.0, R0),
                   ('$c_1$ (Table 2)', C1_TABLE[2], C1_TABLE[0]))
            ax.set_ylabel(r'$R$')
            ax.set_ylim(5.7, 6.5)
            ax.set_title(r'$(\phi_2, R)$: the line skims the surface and passes $f_1$',
                         fontsize=10)
        for nm, x, yv in pts:
            ax.plot(x, yv, 'o', ms=6, mfc='#111' if 'Table' not in nm else '#c1442a',
                    mec='w', zorder=9)
            ax.annotate(nm, (x, yv), textcoords='offset points', xytext=(6, 5), fontsize=9)
        ax.set_xlim(12, -12)
        ax.set_xlabel(r'$\phi_2$  [deg]   (increasing to the left, as in Fig. 8)')
        ax.legend(fontsize=7.5, loc='lower left', framealpha=0.94)
    fig.tight_layout()
    fig.savefig(out)
    print('\nwrote %s' % os.path.abspath(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out', nargs='?', default=os.path.join(HERE, 'figs', 'universal_d1.png'))
    ap.add_argument('--tau', type=float, default=0.6)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    yd = d1_seed()
    Td, Yd = integrate_universal(yd, a.tau)
    Tf, Yf = integrate_universal(np.r_[R0, F1, 0.0, universal_costate(R0, F1)], a.tau)
    report(Td, Yd, Tf, Yf)
    figure(Td, Yd, Tf, Yf, a.out)


if __name__ == '__main__':
    main()
