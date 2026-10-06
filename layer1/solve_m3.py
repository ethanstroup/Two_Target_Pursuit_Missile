"""
solve_m3.py -- Layer 1, Milestone M3.  The converged two-player solve.

Layer1_Plan.md Sec. 4:

    "M3 -- Full two-player solve.  Converged in horizon (zero level set stops
     moving) and in grid (101^3 vs 201^3, measuring drift of the ZERO LEVEL SET,
     not of V)."

and Sec. 10's opening move, both steps of which are run here as pre-flight before
any long march:

    1. use hji.make_policy, never a hand-rolled gradient read;
    2. assert the Sec. 2.5 transpose identity ON THE GRID before relying on
       t_2* = t_1* o S.

Outputs, written to m3_out/:
    V_<n>.npy        the converged value function
    t1_<n>.npy       the arrival-time field t_1*(x) = min{ T : V(x,T) <= 0 }
    Vsnap_<n>.npz    sparse V(.,tau) snapshots, for M4 test C1's remaining-horizon read
    m3_<n>.json      convergence diagnostics

Usage:  python3 solve_m3.py [n_R] [n_phi] [T_max]

GRID CHOICE.  n_R 101 -> 201 and n_phi 100 -> 200 are NESTED: every coarse node is
a fine node (201 = 2*101 - 1 with endpoints included; 200 = 2*100 with
endpoint=False).  The grid study therefore compares the two solutions by exact
subsampling, with no interpolation error of its own mixed into the drift it is
trying to measure.  A 101/201 pair in the periodic angles would NOT nest --
spacing 2*pi/101 against 2*pi/201 -- and the comparison would be measuring its own
interpolant as much as the solver.
"""

import json
import os
import sys
import time

import numpy as np
import jax.numpy as jnp

import hji
import hj_reachability as hj
import barrier as B
import ell as E

N_R = int(sys.argv[1]) if len(sys.argv) > 1 else 101
N_PHI = int(sys.argv[2]) if len(sys.argv) > 2 else 100
T_MAX = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0

DTAU = 0.25                 # reporting interval; the solver substeps at its own CFL
SNAP_EVERY = float(os.environ.get('M3_SNAP_EVERY', '0.5'))   # V(.,tau) snapshots, for M4 test C1
DO_PREFLIGHT = os.environ.get('M3_PREFLIGHT', '1') != '0'
OUT = 'm3_out'
os.makedirs(OUT, exist_ok=True)

FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------------------------
# Pre-flight: the Sec. 2.5 transpose identity, on the grid rather than in theory
# ---------------------------------------------------------------------------

def ell2_on_grid(grid):
    """
    ell for T_{2->1}: player 2 shooting player 1.  Index asymmetry (the easiest
    thing in the model to get wrong): the boresight bound is on the SHOOTER's own
    angle, here phi_2, and both range bounds are on the TARGET's aspect angle,
    here phi_1.  So ell_2(R, phi_1, phi_2) = ell_1(R, phi_2, phi_1) by inspection
    -- which is the identity being tested, so it is written out independently
    rather than by calling ell_1 with swapped arguments.
    """
    st = grid.states
    R, p1, p2 = st[..., 0], st[..., 1], st[..., 2]
    g_bore = jnp.abs(p2) - E.BETA
    R_lo = E.A1 + E.B1 * jnp.cos(p1)
    R_hi = E.RBAR0 - jnp.abs(p1 + jnp.sin(p1))
    w_b, w_n, w_x = E._weights(jnp, p1)      # weights keyed on the TARGET's angle
    return jnp.maximum(w_b * g_bore, jnp.maximum(w_n * (R_lo - R), w_x * (R - R_hi)))


class MirrorGame(hji.TwoTargetPursuit):
    """
    The second game: player 2 is the one driving the state into its own target
    set, so player 2 MINIMIZES and player 1 maximizes.  sigma_2 is the control and
    sigma_1 the disturbance -- the opposite assignment to TwoTargetPursuit.
    """

    def __init__(self):
        super().__init__(control_mode="min", disturbance_mode="max")

    def control_jacobian(self, state, time=0.0):
        return jnp.array([[0.0], [0.0], [1.0]])      # sigma_2 drives phi_2

    def disturbance_jacobian(self, state, time=0.0):
        return jnp.array([[0.0], [1.0], [0.0]])      # sigma_1 drives phi_1


def swap(a):
    """S: (R, phi_1, phi_2) -> (R, phi_2, phi_1), i.e. transpose the angle axes."""
    return np.swapaxes(a, 1, 2)


def preflight(grid, T=2.0):
    print('=' * 92)
    print('M3 pre-flight  (Plan Sec. 10)')
    print('=' * 92)

    p1 = np.asarray(grid.coordinate_vectors[1])
    p2 = np.asarray(grid.coordinate_vectors[2])
    report('phi_1 and phi_2 discretizations are identical (the transpose needs this)',
           p1.shape == p2.shape and np.array_equal(p1, p2),
           'max |phi_1 - phi_2| = %.2e' % (np.abs(p1 - p2).max() if p1.shape == p2.shape else np.inf))

    L1 = np.asarray(E.ell_on_grid(grid))
    L2 = np.asarray(ell2_on_grid(grid))
    e = np.abs(L2 - swap(L1)).max()
    report('ell_2 == ell_1 o S on the grid', e == 0.0, 'max |diff| = %.2e' % e)

    # The identity that actually matters, and the one Sec. 2.5 says to assert
    # rather than assume: solve the mirror game outright and compare.
    t0 = time.time()
    V1 = np.asarray(hji.solve_backward(hji.TwoTargetPursuit(), grid,
                                       jnp.asarray([0.0, -T]), jnp.asarray(L1)))[-1]
    V2 = np.asarray(hji.solve_backward(MirrorGame(), grid,
                                       jnp.asarray([0.0, -T]), jnp.asarray(L2)))[-1]
    e = np.abs(V2 - swap(V1)).max()
    scale = float(np.abs(V1).max())
    # TOLERANCE.  The residual is floating-point accumulation, growing as nodes^1.32
    # and T^2.36, so a fixed 1e-12*|V|max bar fails a healthy 201x204 T=6 run (~1.1e-10).
    # Bar is now 1e-6 of one cell: still 4 orders below M3's accepted 2.8e-4 reflection
    # residual, but it does not punish a bigger grid for doing more arithmetic.
    cell = E.value_scale(grid)
    bar = 1e-6 * cell
    report('V_2 == V_1 o S from an independent solve  (T = %.1f, %.0f s)' % (T, time.time() - t0),
           e < bar, 'max |diff| = %.3e  vs bar %.2e = 1e-6 of one cell (%.4f)'
           % (e, bar, cell))
    dis = np.mean((V2 <= 0) != (swap(V1) <= 0))
    report('the two winning zones are exact mirrors', dis == 0.0,
           '%.6f%% of nodes disagree' % (100 * dis))
    print('        So t_2* = t_1* o S is an axis transpose, not a second overnight solve.')
    print()


# ---------------------------------------------------------------------------
# The march
# ---------------------------------------------------------------------------

def surface_nodes(inside):
    """Nodes the zero level set passes through: those with a 6-neighbour of opposite sign."""
    b = np.zeros_like(inside)
    for ax in range(3):
        for sh in (1, -1):
            b |= (inside != np.roll(inside, sh, axis=ax))
    return int(b.sum())


def march(grid, T_max, dtau, snap_every):
    """
    Step the two-player solve backward, accumulating the arrival-time field and
    the zero-level-set motion as we go.

    hj.solve would return the whole stack; at 201^3 with 41 outputs that is 2.7 GB,
    so the march is done with hj.step and only what is needed is kept.
    """
    dyn = hji.TwoTargetPursuit()
    ss = hji.make_solver_settings('very_high')
    V = jnp.asarray(E.ell_on_grid(grid))

    t1 = np.full(np.asarray(V).shape, np.inf)      # arrival time
    t1[np.asarray(V) <= 0] = 0.0

    taus = [0.0]
    frac = [float(np.mean(np.asarray(V) <= 0))]
    moved = [np.nan]
    snaps = {'0.000': np.asarray(V).astype(np.float32)}

    tau = 0.0
    prev_in = np.asarray(V) <= 0
    while tau < T_max - 1e-12:
        nxt = min(tau + dtau, T_max)
        V = hj.step(ss, dyn, grid, -tau, V, -nxt, progress_bar=False)
        V.block_until_ready()
        tau = nxt
        Vn = np.asarray(V)
        inside = Vn <= 0
        t1[inside & (t1 == np.inf)] = tau
        taus.append(tau)
        frac.append(float(inside.mean()))
        moved.append(float(np.mean(inside != prev_in)))
        prev_in = inside
        if snap_every > 0 and abs(tau / snap_every - round(tau / snap_every)) < 1e-9:
            snaps['%.3f' % tau] = Vn.astype(np.float32)
        print('   tau = %5.2f   {V<=0} = %7.4f%%   moved this step = %.5f%%   '
              'min V = %+.4f' % (tau, 100 * frac[-1], 100 * moved[-1], Vn.min()), flush=True)

    return np.asarray(V), t1, np.array(taus), np.array(frac), np.array(moved), snaps


def main():
    grid = hji.make_grid(n_R=N_R, n_phi=N_PHI)
    tag = '%dx%d_T%g' % (N_R, N_PHI, T_MAX)
    print('=' * 92)
    print('M3  two-player solve   grid %d x %d x %d   T_max %.1f   ell scaling %s'
          % (N_R, N_PHI, N_PHI, T_MAX, E.SCALING))
    print('=' * 92)
    print('   dR = %.5f   dphi = %.5f   one-cell value change = %.5f'
          % (grid.spacings[0], grid.spacings[1], E.value_scale(grid)))
    print()

    if DO_PREFLIGHT:
        preflight(grid, T=2.0)
    else:
        print('   pre-flight SKIPPED (M3_PREFLIGHT=0).  The Sec. 2.5 transpose identity is')
        print('   algebraic and was verified from independent solves at 51x50 (1.8e-14) and')
        print('   101x100 (6.5e-13), both with zero disagreement in the winning zones.')
        print()

    print('=' * 92)
    print('Marching')
    print('=' * 92)
    t0 = time.time()
    V, t1, taus, frac, moved, snaps = march(grid, T_MAX, DTAU, SNAP_EVERY)
    wall = time.time() - t0
    print('   march complete in %.0f s' % wall)
    print()

    print('=' * 92)
    print('Horizon convergence')
    print('=' * 92)
    # "The zero level set stops moving" has to be normalized by the SIZE OF THE
    # ZERO LEVEL SET, not by the whole grid.  Against the grid, a converged surface
    # still reports motion simply because the grid is mostly empty space; against
    # its own node count, the number means what the criterion says it means.  At
    # 101x100 the first step moves 49% of the surface and the last moves 0.04%.
    nb = surface_nodes(V <= 0)
    surf = moved * V.size / max(nb, 1)
    print('        zero level set occupies %d nodes (%.3f%% of grid)' % (nb, 100 * nb / V.size))
    print('        motion per %.2f of retrograde time, as a fraction of the surface itself:' % DTAU)
    for i in range(1, len(taus)):
        if abs(taus[i] % 2.0) < 1e-9 or i == len(taus) - 1:
            print('          tau = %5.2f   %8.4f%% of the surface' % (taus[i], 100 * surf[i]))
    report('zero level set has stopped moving (< 0.5% of the surface per step)',
           surf[-1] < 5e-3, 'final step moves %.4f%% of the surface' % (100 * surf[-1]))

    # Where the horizon is actually heading: fit frac(tau) = L - A exp(-k tau) on
    # the tail and report the remaining drift, rather than asserting convergence
    # from the last number alone.
    m = taus >= max(4.0, 0.4 * T_MAX)
    L = np.nan
    if m.sum() >= 6:
        best = None
        for k in np.linspace(0.05, 2.0, 400):
            X = np.vstack([np.ones(int(m.sum())), -np.exp(-k * taus[m])]).T
            c, *_ = np.linalg.lstsq(X, frac[m], rcond=None)
            r = float(np.sum((X @ c - frac[m]) ** 2))
            if best is None or r < best[0]:
                best = (r, k, c)
        L = float(best[2][0])
        drift = L - frac[-1]
        print('        tail fit: infinite-horizon {V<=0} -> %.5f%% (k = %.2f);'
              % (100 * L, best[1]))
        print('        remaining drift past T_max = %+.5f%% of grid = %+.3f%% of the surface'
              % (100 * drift, 100 * drift * V.size / max(nb, 1)))
        report('remaining drift past T_max is under one node layer',
               abs(drift) * V.size < 0.05 * nb,
               '|drift| = %.1f nodes vs surface %d nodes' % (abs(drift) * V.size, nb))
    conv = float(taus[np.argmax(surf < 5e-3)]) if (surf < 5e-3).any() else None
    Rg = np.asarray(grid.coordinate_vectors[0])
    edge = Rg[np.where((V <= 0).any(axis=(1, 2)))[0].max()]
    report('winning zone stays inside R_hi(0) = %.4f' % B.R_hi(0.0),
           edge < B.R_hi(0.0) + 2 * float(grid.spacings[0]),
           'outer edge R = %.3f' % edge)
    report('winning zone is a nontrivial fraction of the grid',
           0.01 < frac[-1] < 0.5, 'final {V<=0} = %.4f%%' % (100 * frac[-1]))

    finite = np.isfinite(t1)
    print('        arrival time t_1*: %.3f%% of nodes reached, max t_1* = %.2f'
          % (100 * finite.mean(), t1[finite].max() if finite.any() else np.nan))

    np.save('%s/V_%s.npy' % (OUT, tag), V)
    np.save('%s/t1_%s.npy' % (OUT, tag), t1)
    np.savez_compressed('%s/Vsnap_%s.npz' % (OUT, tag), **snaps)
    json.dump(dict(n_R=N_R, n_phi=N_PHI, T_max=T_MAX, dtau=DTAU, scaling=E.SCALING,
                   wall_s=wall, taus=taus.tolist(), frac=frac.tolist(),
                   moved=moved.tolist(), conv_tau=conv, outer_edge=float(edge),
                   surface_nodes=nb, horizon_limit=L,
                   cell=float(E.value_scale(grid)), fails=FAILS),
              open('%s/m3_%s.json' % (OUT, tag), 'w'), indent=1)
    print()
    print('   wrote %s/{V,t1}_%s.npy, Vsnap_%s.npz, m3_%s.json' % (OUT, tag, tag, tag))
    print()
    print('=' * 92)
    print(('M3 grid %s: all checks passed' % tag) if not FAILS else
          '%d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS)))
    print('=' * 92)


if __name__ == '__main__':
    main()
