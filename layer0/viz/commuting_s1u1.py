"""
commuting_s1u1.py -- the commuting line S_1 U_1 of player 1 (D&S Sec. 4.3, Table 3).

RESULT (run 2026-10-07):
  * Table 2's S_1 is a (-1,-1) stagnation point to table precision (R - 2 sin phi_1 = -4e-4).
  * The (0,-1) line from S_1 passes Table 2's U_1 at 3.6e-4 (dR +0.0003, dphi_1 -0.007 deg,
    dphi_2 +0.009 deg); invariants hold to 1e-13.  Shooting from U_1 recovers phi_1(S_1) =
    47.238 deg (Table 2: 47.24).  S_1 U_1 is reconstructed.
  * Layer 0's lambda_1 switches (off-boresight family) all lie on phi_2 = +/-135.00 deg, 0.04-0.11
    from the line, as transversal crossings (lambda_1-dot +0.07 to +0.72).  They are NOT on
    S_1 U_1.  lambda_1-dot changes sign along that plane near phi_1 = 90 deg, i.e. at U_1, the one
    point the switch locus and the commuting line share.

WHAT D&S SAY (p. 152).  The hole inside the closed barrier trajectory J_1 E_1 J_1 is filled
with closed barrier trajectories of sigma* = (-1,-1), centered on the stagnation point S_1
(Rdot = phi_1-dot = phi_2-dot = 0).  "The barrier strategy pair (sigma_1* = 0,
sigma_2* = -1) generates from point S_1 a trajectory segment S_1 U_1 connecting all closed
barrier trajectories" -- Table 3: S_1 U_1, commuting line, (0,-1), pursuer.

WHAT IS DERIVED HERE
  1. Stagnation under (-1,-1).  Rdot = -(cos phi_1 + cos phi_2) = 0 and
     phi_i-dot = L/R - 1 = 0 give phi_2 = pi - phi_1 and R = 2 sin phi_1: a CURVE of
     stagnation points, not one point.  Table 2's S_1 = (1.468, 47.24, 132.76) is checked
     against it.
  2. Costate.  sigma_1 = 0 needs lambda_1 = lambda_1-dot = 0.  universal_d1.py derives
     lambda_1-ddot = A sigma_1 with no sigma-free term, so that set is invariant under
     sigma_1 = 0; with FI = 1 and lambda_R > 0 the costate is the same closed form as the
     d_1 universal line, lambda = (cos phi_1, 0, -R sin phi_1), A = -1.  On it
         H* = R sin phi_1 - 1 - cos(phi_1 - phi_2),
     which vanishes at EVERY stagnation point (R sin phi_1 = 2 sin^2 phi_1 = 1 - cos 2 phi_1).
     So the start is admissible anywhere on the curve; step 4 tests what picks S_1.
  3. The line, in FORWARD time from S_1 under (0,-1).  At S_1, phi_1-dot = L/R = 1, so
     phi_1 grows toward U_1's 91.14 deg.  A short backward extension behind S_1 is also
     flown, only so that switch points below phi_1(S_1) can be measured against it.
  4. Acceptance: closest approach to Table 2's U_1 = (1.721, 91.14, 134.99).  Then a
     one-parameter shoot along the stagnation curve: which start sends the (0,-1) line
     closest to U_1, compared with Table 2's S_1.
  5. M4's switch "anomaly".  Every lambda_1 switch of Layer 0's 66 off-boresight
     trajectories (the M4 bundle), with its distance to the line and its lambda_1-dot.
     A closed (-1,-1) barrier orbit should TOUCH lambda_1 = 0 on this line: there
     lambda_1-dot = 0 and lambda_1-ddot = A sigma_1 = +1 > 0.  Layer 0's integrator
     instead records a transversal crossing (lambda_1-dot != 0) and flips sigma_1 to +1.
     How close the switch points sit to the line, and how large lambda_1-dot is there,
     says how near those trajectories are to D&S's closed orbits.

Usage:  python3 layer0/viz/commuting_s1u1.py [out.png] [--no-switches]
"""

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import barrier as B                                                   # noqa: E402
import validate_table2 as VT                                          # noqa: E402
from universal_d1 import universal_costate, singular_control_coeffs, invariants  # noqa: E402

DEG = 180.0 / np.pi
SIGMA = (0.0, -1.0)          # Table 3, S_1 U_1
DT = 2e-4
T_FWD = 1.5                  # well past U_1 (about 0.8 by the phi_1 rate at S_1)
T_BACK = 0.3


# ---------------------------------------------------------------------------
# Points and the stagnation curve
# ---------------------------------------------------------------------------

def table2_point(name):
    """(R, phi_1, phi_2), angles in radians, for a Table 2 point."""
    for n, R, a1, a2 in VT.TABLE2:
        if n == name:
            return np.array([R, a1 / DEG, a2 / DEG])
    raise KeyError(name)


def stagnation_state(p1):
    """The sigma = (-1,-1) stagnation point with phi_1 = p1."""
    return np.array([2.0 * np.sin(p1), p1, np.pi - p1])


def stagnation_residuals(x):
    """(R - 2 sin phi_1, phi_1 + phi_2 - pi, max |state_dot| under (-1,-1))."""
    sd = np.array(B.state_dot(x[0], x[1], x[2], -1.0, -1.0))
    return x[0] - 2.0 * np.sin(x[1]), x[1] + x[2] - np.pi, float(np.abs(sd).max())


def start_vector(x):
    """State x with the closed-form singular costate appended."""
    return np.r_[x, universal_costate(x[0], x[1])]


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

def rk4_step(y, h, sigma):
    """One RK4 step of the state-costate system with the control held; h < 0 runs backward."""
    k1 = B.field(y, sigma)
    k2 = B.field(y + 0.5 * h * k1, sigma)
    k3 = B.field(y + 0.5 * h * k2, sigma)
    k4 = B.field(y + h * k3, sigma)
    z = y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    z[1] = B.wrap(z[1])
    z[2] = B.wrap(z[2])
    return z


def integrate(y0, t_span, dt=DT, sigma=SIGMA):
    """
    Fly y0 under sigma for |t_span| (dt < 0 flies backward).  Stops early if lambda_2
    leaves sign(sigma_2) -- the evader's half of the strategy would no longer hold -- or
    if R leaves (0.02, 12).  Returns times (signed) and the 6-vector history.
    """
    y = np.array(y0, float)
    T, Y = [0.0], [y.copy()]
    for i in range(int(round(t_span / abs(dt)))):
        y = rk4_step(y, dt, sigma)
        if np.sign(y[5]) != np.sign(sigma[1]) or not (0.02 < y[0] < 12.0):
            break
        T.append((i + 1) * dt)
        Y.append(y.copy())
    return np.array(T), np.array(Y)


def full_line(x0, dt=DT):
    """Backward extension (t < 0) and the line proper (t >= 0), joined in time order."""
    y0 = start_vector(x0)
    Tb, Yb = integrate(y0, T_BACK, -dt)
    Tf, Yf = integrate(y0, T_FWD, dt)
    return np.r_[Tb[:0:-1], Tf], np.vstack([Yb[:0:-1], Yf])


# ---------------------------------------------------------------------------
# Distances
# ---------------------------------------------------------------------------

def state_gap(Y, x):
    """(dR, dphi_1, dphi_2) of every row of Y from x, angles wrapped, and its norm."""
    d = Y[:, :3] - np.asarray(x)[:3]
    d[:, 1:] = B.wrap(d[:, 1:])
    return d, np.linalg.norm(d, axis=1)


def closest_approach(Y, x):
    """Index, distance and (dR, dphi_1, dphi_2) of the point of Y nearest x."""
    d, n = state_gap(Y, x)
    i = int(np.argmin(n))
    return i, float(n[i]), d[i]


def miss_from_start(p1, target, dt=1e-3):
    """Closest approach to target of the forward (0,-1) line from the stagnation point at p1."""
    _, Y = integrate(start_vector(stagnation_state(p1)), T_FWD, dt)
    return closest_approach(Y, target)[1]


def shoot(target, lo_deg=40.0, hi_deg=55.0, n=61):
    """Stagnation start (phi_1, deg) whose line passes closest to target: (phi_1, miss)."""
    from scipy.optimize import minimize_scalar
    grid = np.linspace(lo_deg, hi_deg, n)
    miss = np.array([miss_from_start(g / DEG, target) for g in grid])
    k = int(np.argmin(miss))
    a, b = grid[max(k - 1, 0)], grid[min(k + 1, n - 1)]
    res = minimize_scalar(lambda g: miss_from_start(g / DEG, target),
                          bounds=(a, b), method='bounded', options={'xatol': 1e-6})
    return float(res.x), float(res.fun)


# ---------------------------------------------------------------------------
# Layer 0's lambda_1 switches on the off-boresight family (the M4 bundle)
# ---------------------------------------------------------------------------

def boresight_seeds():
    """test_barrier.py's own seeds_boresight(), lifted the way layer1/l0_traj.py does."""
    src = open(os.path.join(os.path.dirname(HERE), 'test_barrier.py')).read()
    head = src.split("print('=' * 90)")[0]
    ns = {'np': np, 'B': B, 'D': np.pi / 180.0, 'FAILS': []}
    exec(compile(head, 'test_barrier_head', 'exec'), ns)
    return [y0 for _, y0 in ns['seeds_boresight']()]


def lambda1_switches(tau_max=6.0, dt=1e-3):
    """Every located lambda_1 switch, with the state, lambda_1-dot and the seed."""
    out = []
    for y0 in boresight_seeds():
        tr = B.integrate_retrograde(y0, tau_max=tau_max, dt=dt)
        for tsw, which in tr['switches']:
            if which != 1:
                continue
            i = int(np.argmin(np.abs(tr['tau'] - tsw)))
            y = tr['Y'][i].copy()
            out.append(dict(seed=np.array(y0[:3]), tsw=float(tsw), y=y,
                            l1dot=float(B.costate_dot(*y)[1])))
    return out


# ---------------------------------------------------------------------------
# Report and figure
# ---------------------------------------------------------------------------

def report_start(S_tab, x0):
    r1, r2, sd = stagnation_residuals(S_tab)
    print('Table 2 S_1 = (%.3f, %.2f, %.2f)' % (S_tab[0], S_tab[1] * DEG, S_tab[2] * DEG))
    print('  on the (-1,-1) stagnation curve?  R - 2 sin phi_1 = %+.1e   phi_1 + phi_2 - pi = %+.1e'
          '   max |xdot| = %.1e' % (r1, r2, sd))
    y0 = start_vector(x0)
    print('  start used: (%.5f, %.4f, %.4f) on the curve at Table 2\'s phi_1;'
          '  H* = %.1e  FI-1 = %.1e  lambda_1-dot = %.1e'
          % (x0[0], x0[1] * DEG, x0[2] * DEG, B.hamiltonian_star(*y0),
             B.first_integral(y0[0], y0[3], y0[4], y0[5]) - 1, B.costate_dot(*y0)[1]))
    try:
        A, Bc = singular_control_coeffs()
        print('  lambda_1-ddot | lambda_1 = 0  =  (%s) * sigma_1 + (%s)' % (A, Bc))
    except ImportError:
        print('  (sympy not available; singular-control derivation skipped)')


def report_line(T, Y, U_tab):
    fwd = T >= 0
    inv = invariants(Y[fwd])
    print('\nS_1 U_1 line, sigma = (0,-1), forward t <= %.3f' % T[fwd][-1])
    print('  max |lambda_1| %.1e  |lambda_1-dot| %.1e  |FI-1| %.1e  |H*| %.1e  '
          '|lambda - closed form| %.1e  max lambda_2 %+.3f'
          % (inv['l1'], inv['l1dot'], inv['fi'], inv['h'], inv['closed'], Y[fwd][:, 5].max()))
    i, dist, d = closest_approach(Y[fwd], U_tab)
    y = Y[fwd][i]
    print('  closest approach to Table 2 U_1 = (%.3f, %.2f, %.2f): %.2e at t = %.4f'
          % (U_tab[0], U_tab[1] * DEG, U_tab[2] * DEG, dist, T[fwd][i]))
    print('    line there (%.4f, %.3f, %.3f);  dR %+.4f  dphi_1 %+.3f deg  dphi_2 %+.3f deg'
          % (y[0], y[1] * DEG, y[2] * DEG, d[0], d[1] * DEG, d[2] * DEG))


def report_shoot(S_tab, U_tab):
    p1, miss = shoot(U_tab)
    x = stagnation_state(p1 / DEG)
    print('\nshoot along the stagnation curve for the line through U_1:')
    print('  best start phi_1 = %.4f deg -> (%.5f, %.4f, %.4f), miss %.2e;  Table 2 S_1 phi_1 = %.2f'
          % (p1, x[0], x[1] * DEG, x[2] * DEG, miss, S_tab[1] * DEG))


def report_switches(sw, T, Y):
    if not sw:
        return
    rows = []
    for s in sw:
        i, dist, d = closest_approach(Y, s['y'])
        rows.append((dist, T[i], d, s))
    rows.sort(key=lambda r: r[0])
    print('\nLayer 0 lambda_1 switches, off-boresight family (%d), nearest the line first:' % len(rows))
    print('  %-9s %-28s %-8s %-11s %-9s %-8s %s' % ('dist', 'switch (R, phi_1, phi_2)', 'tau_sw',
                                                     'lambda1dot', 'line t', 'R >= .45',
                                                     'seed phi_2'))
    for dist, t, d, s in rows:
        y = s['y']
        print('  %.2e  (%.3f, %7.2f, %7.2f)   %6.3f  %+9.3e  %+7.3f   %-8s %7.2f'
              % (dist, y[0], y[1] * DEG, y[2] * DEG, s['tsw'], s['l1dot'], t,
                 'yes' if y[0] >= 0.45 else '-', s['seed'][2] * DEG))
    print('  (line t < 0: nearest point is on the extension behind S_1, not on S_1 U_1 itself)')


def figure(T, Y, S_tab, U_tab, sw, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fwd = T >= 0
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0))
    swy = np.array([s['y'] for s in sw]) if sw else np.zeros((0, 6))
    panels = ((2, 1, r'$\phi_2$  [deg]', r'$\phi_1$  [deg]'), (1, 0, r'$\phi_1$  [deg]', r'$R$'))
    for ax, (ix, iy, lx, ly) in zip(axes, panels):
        sx, sy = (DEG if ix else 1.0), (DEG if iy else 1.0)
        ax.plot(Y[~fwd][:, ix] * sx, Y[~fwd][:, iy] * sy, lw=1.2, ls='--', color='#8a1c7c',
                label=r'extension behind $S_1$')
        ax.plot(Y[fwd][:, ix] * sx, Y[fwd][:, iy] * sy, lw=2.2, color='#8a1c7c',
                label=r'$(0,-1)$ line from $S_1$')
        if len(swy):
            ax.plot(swy[:, ix] * sx, swy[:, iy] * sy, 'o', ms=4, color='#1f5fa8',
                    label=r'Layer 0 $\lambda_1$ switches')
        for nm, p in (('$S_1$', S_tab), ('$U_1$', U_tab)):
            ax.plot(p[ix] * sx, p[iy] * sy, 's', ms=7, mfc='#c1442a', mec='w', zorder=9)
            ax.annotate(nm + ' (Table 2)', (p[ix] * sx, p[iy] * sy), textcoords='offset points',
                        xytext=(6, 5), fontsize=9)
        xs, ys = Y[:, ix] * sx, Y[:, iy] * sy
        px, py = 0.15 * np.ptp(xs) + (2.0 if ix else 0.05), 0.15 * np.ptp(ys) + (2.0 if iy else 0.05)
        ax.set_xlim(xs.min() - px, xs.max() + px)
        ax.set_ylim(ys.min() - py, ys.max() + py)
        ax.set_xlabel(lx)
        ax.set_ylabel(ly)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7.5, loc='best')
    fig.suptitle(r'Commuting line $S_1U_1$, $(\sigma_1,\sigma_2) = (0,-1)$', fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    print('\nwrote %s' % os.path.abspath(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out', nargs='?', default=os.path.join(HERE, 'figs', 'commuting_s1u1.png'))
    ap.add_argument('--no-switches', action='store_true',
                    help='skip regenerating the 66 off-boresight trajectories')
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    S_tab, U_tab = table2_point('S_1'), table2_point('U_1')
    x0 = stagnation_state(S_tab[1])          # exactly on the curve; Table 2's R is rounded
    T, Y = full_line(x0)
    sw = [] if a.no_switches else lambda1_switches()

    report_start(S_tab, x0)
    report_line(T, Y, U_tab)
    report_shoot(S_tab, U_tab)
    report_switches(sw, T, Y)
    figure(T, Y, S_tab, U_tab, sw, a.out)


if __name__ == '__main__':
    main()
