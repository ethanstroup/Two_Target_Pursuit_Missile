"""
smoke_m5.py -- Layer 1, M5 smoke tests at 61 x 62^2 (criteria Sec. 4.1, checks 1b, 2, 3).

  1b  The library form of the update against Fisac's Algorithm 1 written out
      literally.  The two are the same dynamic-programming step (criteria Sec. 2);
      on a grid they should differ only next to the zero level set.
  2   Both controls frozen, at (0, 0) and at (+1, -1).  The game collapses to a
      single deterministic flow, so the exact reach-avoid outcome
          min_t max{ ell_1(x(t)), max_{s<=t} -ell_2(x(s)) }
      is computed by integrating forward from EVERY node.  This is where an
      obstacle-placement or Runge-Kutta-stage problem would show.
  3   sigma_2 == 0.  Rollouts of player 1's grid law from nodes with V <= -delta:
      every one must win alone.

n_phi = 62 keeps |phi_1| = beta off the nodes (index 38.75).

Usage:  python3 smoke_m5.py [T]        (default T = 4)
"""

import sys
import time

import numpy as np
import jax.numpy as jnp

import hji
import ell as E
import reach_avoid as RA
import sim_m5 as SIM

N_R, N_PHI = 61, 62
T = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FixedControls(hji.TwoTargetPursuit):
    """Both players' turn rates frozen at constants: a single deterministic flow."""

    def __init__(self, c1, c2):
        super().__init__()
        self.c1, self.c2 = float(c1), float(c2)

    def open_loop_dynamics(self, state, time=0.0):
        R, p1, p2 = state[0], state[1], state[2]
        L = jnp.sin(p1) + jnp.sin(p2)
        C = jnp.cos(p1) + jnp.cos(p2)
        return jnp.array([-C, L / R + self.c1, L / R + self.c2])

    def control_jacobian(self, state, time=0.0):
        return jnp.zeros((3, 1))

    def disturbance_jacobian(self, state, time=0.0):
        return jnp.zeros((3, 1))


def dilate(mask, iters):
    """Binary dilation, 6-neighbour, periodic in both angles, not in R."""
    m = mask.copy()
    for _ in range(iters):
        g = m.copy()
        g[1:] |= m[:-1]
        g[:-1] |= m[1:]
        for ax in (1, 2):
            g |= np.roll(m, 1, ax) | np.roll(m, -1, ax)
        m = g
    return m


def far_disagreements(a_in, b_in, band, valid=None):
    """Nodes where the two sign fields differ and neither surface is within `band` cells."""
    near = dilate(RA.surface_mask(a_in), band) | dilate(RA.surface_mask(b_in), band)
    diff = a_in != b_in
    if valid is not None:
        diff &= valid
    return int(np.count_nonzero(diff & ~near)), int(np.count_nonzero(diff))


def solve(grid, dyn, T_max, form='library', snap_every=0.0):
    ell1, ell2 = RA.ell1_on_grid(grid), RA.ell2_on_grid(grid)
    ss = RA.solver_settings(ell1, ell2, form)
    V0 = RA.initial_value(ell1, ell2)
    V, _, taus, frac, moved, snaps, wall = RA.march(grid, dyn, ss, V0, T_max,
                                                    snap_every=snap_every, log=lambda s: None)
    return V, snaps, wall


def exact_outcome(geom, c1, c2, T_max, dt=1e-3):
    """
    Integrate the frozen-control flow forward from every node and return the exact
    reach-avoid outcome, plus a mask of nodes whose path left 0.2 < R < 12 (where
    the grid solution is only an outflow approximation; excluded from the check).
    """
    x = geom.node_states(np.arange(geom.n_R * geom.n_phi ** 2))
    s1 = np.full(len(x), c1)
    s2 = np.full(len(x), c2)
    G = -SIM.ell2(x)
    J = np.maximum(SIM.ell1(x), G)
    exited = np.zeros(len(x), bool)
    for _ in range(int(round(T_max / dt))):
        x = SIM.rk4(x, s1, s2, dt)
        exited |= ~((x[:, 0] > SIM.R_LO_DOM) & (x[:, 0] < SIM.R_HI_DOM))
        G = np.maximum(G, -SIM.ell2(x))
        J = np.minimum(J, np.maximum(SIM.ell1(x), G))
    shape = (geom.n_R, geom.n_phi, geom.n_phi)
    return J.reshape(shape), exited.reshape(shape)


def omega_mask(grid):
    R = np.asarray(grid.states[..., 0])
    return (R >= RA.R_MARGIN) & (np.asarray(RA.ell1_on_grid(grid)) > 0) & \
           (np.asarray(RA.ell2_on_grid(grid)) > 0)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_1b(grid):
    print('-' * 92)
    print('1b.  Library form vs Fisac Algorithm 1   (T = %.1f)' % T)
    print('-' * 92)
    Va, _, wa = solve(grid, hji.TwoTargetPursuit(), T, 'library')
    Vb, _, wb = solve(grid, hji.TwoTargetPursuit(), T, 'fisac')
    far, tot = far_disagreements(Va <= 0, Vb <= 0, 2)
    d = np.abs(Va - Vb)
    print('        {V<=0}: library %.4f%%  fisac %.4f%%   (%.0f s, %.0f s)'
          % (100 * np.mean(Va <= 0), 100 * np.mean(Vb <= 0), wa, wb))
    print('        |V_lib - V_fisac|: median %.2e  max %.2e   sign flips %d'
          % (np.median(d), d.max(), tot))
    report('check 1b: no sign disagreement more than 2 cells from either zero set', far == 0,
           '%d of %d flips are further away' % (far, tot))
    return Va


def check_2(grid, geom, cell):
    for c1, c2 in ((0.0, 0.0), (1.0, -1.0)):
        print('-' * 92)
        print('2.  Both controls frozen at (%+g, %+g)   (T = %.1f)' % (c1, c2, T))
        print('-' * 92)
        Vg, _, wall = solve(grid, FixedControls(c1, c2), T)
        t0 = time.time()
        Vx, exited = exact_outcome(geom, c1, c2, T)
        valid = ~exited
        far, tot = far_disagreements(Vg <= 0, Vx <= 0, 2, valid)
        err = np.abs(Vg - Vx)[valid]
        print('        grid solve %.0f s, exact integration %.0f s;  %d nodes excluded (left the R domain)'
              % (wall, time.time() - t0, int(exited.sum())))
        print('        {V<=0}: grid %.4f%%  exact %.4f%%   |V_grid - V_exact| median %.4f  95th %.4f  (cell %.4f)'
              % (100 * np.mean((Vg <= 0)[valid]), 100 * np.mean((Vx <= 0)[valid]),
                 np.median(err), np.percentile(err, 95), cell))
        report('check 2 (%+g,%+g): no sign disagreement more than 2 cells from the zero set' % (c1, c2),
               far == 0, '%d of %d flips are further away' % (far, tot))


def check_3(grid, geom, cell, n_starts=500, seed=0):
    print('-' * 92)
    print('3.  sigma_2 == 0, rollouts of player 1\'s grid law   (T = %.1f)' % T)
    print('-' * 92)
    V, snaps, wall = solve(grid, hji.FrozenEvader(), T, snap_every=0.25)
    n, mm1, mm2, hard = SIM.assert_matches_make_policy(grid, snaps)
    report('vectorized law reproduces hji.make_policy', hard == 0,
           '%d states: %d / %d sigma_1 / sigma_2 mismatches, %d away from exact ties'
           % (n, mm1, mm2, hard))
    cand = np.nonzero(((V <= -cell) & omega_mask(grid)).ravel())[0]
    rng = np.random.default_rng(seed)
    pick = rng.choice(cand, size=min(n_starts, cand.size), replace=False)
    x0 = geom.node_states(pick)
    stack = SIM.SnapshotStack(geom, snaps, keep=(1,))
    res = SIM.rollout(x0, SIM.law_value_p1(stack, T), SIM.law_zero(), T)
    s = SIM.summarize(res['outcome'])
    print('        %d candidate starts with V <= -delta in Omega; %d rolled out (solve %.0f s)'
          % (cand.size, len(pick), wall))
    print('        outcomes: %s' % s)
    report('check 3: every rollout from V <= -delta wins alone', s['win alone'] == len(pick),
           '%d / %d' % (s['win alone'], len(pick)))
    return res, pick


def main():
    grid = hji.make_grid(n_R=N_R, n_phi=N_PHI)
    geom = SIM.Geom((N_R, N_PHI, N_PHI))
    cell = E.value_scale(grid)
    print('=' * 92)
    print('M5 smoke tests   grid %d x %d x %d   T = %.1f   delta = %.5f'
          % (N_R, N_PHI, N_PHI, T, cell))
    print('=' * 92)
    ok, e, _ = RA.check_ell2_transpose(grid, RA.ell1_on_grid(grid), RA.ell2_on_grid(grid))
    report('check 1: ell_2 (independent) == ell_1 o S', ok, 'max |diff| = %.2e' % e)
    check_1b(grid)
    check_2(grid, geom, cell)
    check_3(grid, geom, cell)
    print('=' * 92)
    print('M5 smoke tests: all passed' if not FAILS else
          '%d FAILED: %s' % (len(FAILS), '; '.join(FAILS)))
    print('=' * 92)


if __name__ == '__main__':
    main()
