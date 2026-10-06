"""
solve_m2_snap.py -- Layer 1, M2's frozen-evader value function, snapshotted for
the explorer (viz/ell_explorer.html) beside M3's.

M2 (test_m2.py) verified the frozen-evader solve -- sigma_2 == 0, a
non-maneuvering target -- at 61^3 and 101^3 to T = 3.  This script re-solves the
same game on M3's grid and horizon, 101 x 102 x 102 to tau = 6, and writes it in
the layout of m3_out/Vsnap_101x102_T6.npz, so the two fields can be compared
node for node at the same tau.  Nothing here changes hji.py or ell.py.

The march copies solve_m3.march: hj.step every DTAU = 0.25 of retrograde time
(the solver substeps at its own CFL inside each step), snapshots every 0.5.
Identical stepping matters, because the snapshot values depend slightly on
where the steps stop.

TWO THINGS TO KNOW BEFORE READING THE SNAPSHOTS.

1. The outer face.  Against a frozen evader the winning zone is range-limited
   and its outer edge advances at the maximum closing speed 2 (test_m2.py
   Sec. 2).  It starts at R_hi(0) = 6.14, so it reaches the domain's outer face
   R = 12 near tau = 2.9.  After that the values next to R = 12 come from the
   face's linear-extrapolation condition (hji.make_grid, trap 2), an outflow
   approximation that M2 never validated.  Written to the json as tau_sat.

2. The inner face: THIS SOLVE IS NOT VALID EVERYWHERE, AND NEITHER IS M2'S.
   V is a minimum of ell along a trajectory, so V >= min ell = -beta at every
   node and every tau.  The frozen-evader solve breaks that bound from
   tau ~ 0.75 on, starting at the inner face R = 0.2 near phi_1 = phi_2 = 0
   (nose-on, closing at speed 2, i.e. leaving the domain through that face)
   and growing without limit: min V is -11 at tau = 1, about -7e3 at tau = 3
   and about -8e8 at tau = 6, and the region below the bound spreads outward
   in R at about the closing speed.  M2's own configuration (test_m2.py,
   101^3, T = 3) does the same -- min V = -1.45e4 at T = 3, 3.3 % of nodes more
   than 0.05 below -beta, out to R = 5.3 -- and none of test_m2.py's checks
   can see it: none bounds V from below, and the trajectory tests drop every
   sample that leaves the R domain, which is exactly where these states go.
   The two-player solve (M3) does not do this: its min V is -0.802, within
   0.017 of the bound.  This script therefore reports the bound as a check
   (it FAILS) and writes the count of offending nodes per tau to the json;
   the explorer greys those nodes out.  Changing the inner-face condition is
   a method decision and is not made here.

Usage:  python solve_m2_snap.py [n_R] [n_phi] [T_max]       (defaults 101 102 6)

Writes, to m2_out/:
    Vsnap_frozen_<n_R>x<n_phi>_T<T>.npz  V(., tau) as float32, keys '0.000', '0.500', ...
                                         (as M3's Vsnap), plus the node arrays R, phi1, phi2
    m2_frozen_<n_R>x<n_phi>_T<T>.json    zone share per 0.25, outer edge per 0.25, front
                                         speed, tau_sat, the checks below
"""

import json
import os
import sys
import time

import numpy as np

import hji
import hj_reachability as hj
import jax.numpy as jnp
import ell as E

N_R = int(sys.argv[1]) if len(sys.argv) > 1 else 101
N_PHI = int(sys.argv[2]) if len(sys.argv) > 2 else 102
T_MAX = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0

DTAU = 0.25                 # reporting interval, as solve_m3.py
SNAP_EVERY = 0.5            # as M3's Vsnap
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'm2_out')
M3_SNAP = os.path.join(HERE, 'm3_out', 'Vsnap_%dx%d_T%g.npz' % (N_R, N_PHI, T_MAX))

FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


def outer_edge(inside, Rg):
    """Largest R node with any node of the zone on it."""
    rows = np.where(inside.any(axis=(1, 2)))[0]
    return float(Rg[rows.max()]) if rows.size else float('nan')


def march(grid, T_max, floor):
    """`floor`: nodes with V below it are counted (the lower-bound check)."""
    dyn = hji.FrozenEvader()
    ss = hji.make_solver_settings('very_high')
    V = jnp.asarray(E.ell_on_grid(grid))
    Rg = np.asarray(grid.coordinate_vectors[0])

    V0 = np.asarray(V)
    taus, frac, edge = [0.0], [float(np.mean(V0 <= 0))], [outer_edge(V0 <= 0, Rg)]
    minV, below, below_R = [float(V0.min())], [int(np.sum(V0 < floor))], [float('nan')]
    snaps = {'0.000': V0.astype(np.float32)}
    max_rise = 0.0                  # V must not increase with the horizon
    prev = V0
    tau = 0.0
    while tau < T_max - 1e-12:
        nxt = min(tau + DTAU, T_max)
        V = hj.step(ss, dyn, grid, -tau, V, -nxt, progress_bar=False)
        V.block_until_ready()
        tau = nxt
        Vn = np.asarray(V)
        max_rise = max(max_rise, float(np.max(Vn - prev)))
        prev = Vn
        inside = Vn <= 0
        taus.append(tau)
        frac.append(float(inside.mean()))
        edge.append(outer_edge(inside, Rg))
        bad = Vn < floor
        minV.append(float(Vn.min()))
        below.append(int(bad.sum()))
        below_R.append(outer_edge(bad, Rg))
        if abs(tau / SNAP_EVERY - round(tau / SNAP_EVERY)) < 1e-9:
            snaps['%.3f' % tau] = Vn.astype(np.float32)
        print('   tau = %5.2f   {V<=0} = %7.4f%%   outer edge R = %6.3f   min V = %+.4g   '
              'below bound: %d nodes, out to R = %.2f'
              % (tau, 100 * frac[-1], edge[-1], Vn.min(), below[-1], below_R[-1]), flush=True)
    diag = dict(min_V=minV, below_bound=below, below_bound_R=below_R)
    return snaps, np.array(taus), np.array(frac), np.array(edge), max_rise, diag


def main():
    os.makedirs(OUT, exist_ok=True)
    grid = hji.make_grid(n_R=N_R, n_phi=N_PHI)
    tag = '%dx%d_T%g' % (N_R, N_PHI, T_MAX)
    Rg = np.asarray(grid.coordinate_vectors[0])
    dR = float(grid.spacings[0])
    cell = E.value_scale(grid)
    print('=' * 92)
    print('M2 frozen evader, snapshotted   grid %d x %d x %d   T_max %.1f   ell scaling %s'
          % (N_R, N_PHI, N_PHI, T_MAX, E.SCALING))
    print('=' * 92)
    print('   dR = %.5f   dphi = %.5f   one-cell value change = %.5f'
          % (dR, grid.spacings[1], cell))
    if N_PHI % 8 == 0:
        print('   WARNING: n_phi is a multiple of 8, so nodes sit on |phi_1| = beta (M3 grid rule).')

    # The lower bound: V = min_t ell(x(t)) >= min ell, and min ell = -beta on this
    # grid (phi_1 = 0 is a node).  A node more than one cell below it is not a value.
    ell_min = float(np.asarray(E.ell_on_grid(grid)).min())
    floor = ell_min - cell
    print('   lower bound: min ell = %+.4f; nodes below %+.4f (one cell under it) are counted'
          % (ell_min, floor))

    t0 = time.time()
    snaps, taus, frac, edge, max_rise, diag = march(grid, T_MAX, floor)
    wall = time.time() - t0
    print('   march complete in %.0f s' % wall)
    print()

    print('-' * 92)
    print('Checks')
    print('-' * 92)
    L0 = np.asarray(E.ell_on_grid(grid)).astype(np.float32)
    report('V(., 0) is ell on the grid', np.array_equal(snaps['0.000'], L0))
    report('V is non-increasing in the horizon (min over a longer time)', max_rise <= 1e-9,
           'largest rise between steps %.2e' % max_rise)
    below = np.array(diag['below_bound'])
    first_bad = float(taus[np.argmax(below > 0)]) if (below > 0).any() else None
    report('V >= min ell - one cell everywhere (V is a minimum of ell)', first_bad is None,
           'min V %.3g; first broken at tau = %s; at tau = %g, %d nodes (%.2f%%) out to R = %.2f'
           % (min(diag['min_V']), first_bad, taus[-1], below[-1], 100.0 * below[-1] / snaps['0.000'].size,
              diag['below_bound_R'][-1]))

    # The front: advances at the maximum closing speed 2 until it meets R = R_max.
    sat = edge >= Rg[-1] - 2 * dR
    tau_sat = float(taus[np.argmax(sat)]) if sat.any() else None
    free = ~sat
    sp = float(np.polyfit(taus[free], edge[free], 1)[0]) if free.sum() >= 5 else float('nan')
    report('front speed == max closing speed 2 (before it meets R = %.0f)' % Rg[-1],
           abs(sp - 2.0) < 0.10, 'measured %.3f over tau in [0, %.2f]' % (sp, taus[free].max()))
    print('        the front reaches the outer face near tau = %s; later snapshots depend on'
          % ('%.2f' % tau_sat if tau_sat is not None else 'never'))
    print('        the face\'s extrapolation condition there.')

    # A frozen evader can only help player 1: V_frozen <= V_two-player (test_m2.py Sec. 5).
    worst = None
    if os.path.exists(M3_SNAP):
        m3 = np.load(M3_SNAP)
        common = [k for k in snaps if k in m3.files]
        worst = max(float(np.max(snaps[k] - m3[k])) for k in common)
        report('V(frozen) <= V(two-player, M3) at all %d common snapshots' % len(common),
               worst <= 2 * cell, 'max V_frozen - V_M3 = %+.2e  (one cell = %.4f)' % (worst, cell))
    else:
        print('        (%s not found: the comparison with M3 is skipped)' % os.path.relpath(M3_SNAP, HERE))

    npz = os.path.join(OUT, 'Vsnap_frozen_%s.npz' % tag)
    np.savez_compressed(npz, R=Rg, phi1=np.asarray(grid.coordinate_vectors[1]),
                        phi2=np.asarray(grid.coordinate_vectors[2]), **snaps)
    js = os.path.join(OUT, 'm2_frozen_%s.json' % tag)
    json.dump(dict(game='frozen evader (sigma_2 = 0)', n_R=N_R, n_phi=N_PHI, T_max=T_MAX,
                   dtau=DTAU, snap_every=SNAP_EVERY, scaling=E.SCALING, wall_s=wall,
                   taus=taus.tolist(), frac=frac.tolist(), outer_edge=edge.tolist(),
                   front_speed=sp, tau_sat=tau_sat, max_rise=max_rise,
                   max_frozen_minus_m3=worst, cell=float(cell),
                   ell_min=ell_min, floor=floor, first_below_floor_tau=first_bad,
                   min_V=diag['min_V'], below_floor=diag['below_bound'],
                   below_floor_outer_R=diag['below_bound_R'], fails=FAILS),
              open(js, 'w'), indent=1)
    print()
    print('   wrote %s' % os.path.relpath(npz, HERE))
    print('   wrote %s' % os.path.relpath(js, HERE))
    print('=' * 92)
    print(('M2 snapshots %s: all checks passed' % tag) if not FAILS else
          '%d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS)))
    print('=' * 92)


if __name__ == '__main__':
    main()
