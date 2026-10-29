"""
diag_m2_pole.py -- report only (2026-10-15, Layer 1 close-out).  Not pre-registered.

README_LAYER1.md (2026-10-01) left one M2 item open: the frozen-evader value breaks the bound
V >= min ell from tau ~ 0.75, starting at the R = 0.2 inner face nose-on, and grows without
limit (min V = -1.45e4 at T = 3 on M2's 101^3 grid).  V is a minimum of ell along a
trajectory, so V >= min ell holds exactly in the continuum.

This solves the same frozen-evader problem (sigma_2 == 0, V(x,0) = ell, M3's update) twice at
the same resolution and reports min V against the bound every 0.25 in tau:
    old    R_min = 0.2 with linear extrapolation   (hji.make_grid, hji.make_solver_settings)
    pole   the pole condition, fill after every step (pole.make_grid, pole.single_target_settings)

Usage (from layer1/M5):  python diag/diag_m2_pole.py [n_R n_phi T [n_phi_old]]     default 61 62 3
n_phi_old (default n_phi) lets the old grid be M2's own odd 101; the pole needs an even n_phi.
"""

import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', '..', 'common'))
sys.path.insert(0, os.path.join(_HERE, '..'))

import hji
import pole
import ell as E
import hj_reachability as hj
import jax.numpy as jnp

DTAU = 0.25
SLACK = 0.05          # README's measure: nodes more than 0.05 below the bound


def global_min_ell(n=241):
    """min ell over (0, 12] x S^1 x S^1, sampled densely: the continuum lower bound on V."""
    R = np.linspace(0.01, 12.0, n)
    p = np.linspace(-np.pi, np.pi, 4 * n, endpoint=False)
    out = np.inf
    for r in R:
        P1, P2 = np.meshgrid(p, p, indexing='ij')
        out = min(out, float(E.ell(np.full_like(P1, r), P1, P2).min()))
    return out


def setups(n_R, n_phi, n_phi_old):
    """(name, grid, settings, V0, rows to score) for the old face and the pole."""
    g_old = hji.make_grid(n_R=n_R, n_phi=n_phi_old)
    g_pole = pole.make_grid(n_R, n_phi)
    return [('old  R_min = 0.2', g_old, hji.make_solver_settings('very_high'),
             jnp.asarray(E.ell_on_grid(g_old)), slice(None)),
            ('pole', g_pole, pole.single_target_settings(),
             pole.fill(jnp.asarray(E.ell_on_grid(g_pole))), slice(pole.N_GHOST, None))]


def march(name, grid, ss, V0, rows, T, bound):
    dyn = hji.FrozenEvader()
    V, tau, t0 = V0, 0.0, time.time()
    Rn = np.asarray(grid.coordinate_vectors[0])[rows]
    print('   %s   (real rows R = %.3f .. %.3f)' % (name, Rn[0], Rn[-1]))
    worst = []
    while tau < T - 1e-12:
        nxt = min(tau + DTAU, T)
        V = hj.step(ss, dyn, grid, -tau, V, -nxt, progress_bar=False)
        tau = nxt
        Vr = np.asarray(V)[rows]
        below = Vr < bound - SLACK
        i = np.unravel_index(int(np.argmin(Vr)), Vr.shape)
        worst.append(float(Vr.min()))
        print('      tau = %4.2f   min V = %+12.4f   at R = %.3f;   nodes below bound - %.2f: %.3f%%   (%.0f s)'
              % (tau, Vr.min(), Rn[i[0]], SLACK, 100 * below.mean(), time.time() - t0))
    return worst


def main():
    n_R = int(sys.argv[1]) if len(sys.argv) > 1 else 61
    n_phi = int(sys.argv[2]) if len(sys.argv) > 2 else 62
    T = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
    n_phi_old = int(sys.argv[4]) if len(sys.argv) > 4 else n_phi
    bound = global_min_ell()
    print('=' * 100)
    print('M2 frozen-evader value, old inner face vs pole   old %d x %d^2, pole %d x %d^2   T = %g   ell scaling %s'
          % (n_R, n_phi_old, n_R, n_phi, T, E.SCALING))
    print('   continuum bound: V >= min ell = %+.4f' % bound)
    print('=' * 100)
    res = {}
    for name, grid, ss, V0, rows in setups(n_R, n_phi, n_phi_old):
        res[name] = march(name, grid, ss, V0, rows, T, bound)
    print('-' * 100)
    for name, w in res.items():
        print('   %-18s min V at T = %g: %+.4f   (bound %+.4f)  -> %s'
              % (name, T, w[-1], bound, 'holds' if w[-1] >= bound - SLACK else 'BROKEN'))
    print('=' * 100)


if __name__ == '__main__':
    main()
