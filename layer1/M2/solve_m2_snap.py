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

TWO INNER FACES.  LAYER1_POLE selects which one, as in M5/reach_avoid.py and
M4/test_m4.py:

    unset or 0   hji.make_grid: R_min = 0.2 with linear extrapolation, the
                 grid M2 and M3 were solved on.
    1            M5/pole.py: real rows at (i + 1/2) dR, 3 mirror rows below
                 R = 0 refilled after every step from
                 (-R, phi_1, phi_2) == (R, phi_1 + pi, phi_2 + pi).
                 The grid of record since 2026-10-15.  n_phi must be even.
                 Outputs get the suffix '_pole' and hold the real rows only.

TWO THINGS TO KNOW BEFORE READING THE SNAPSHOTS.

1. The outer face.  Against a frozen evader the winning zone is range-limited
   and its outer edge advances at the maximum closing speed 2 (test_m2.py
   Sec. 2).  It starts at R_hi(0) = 6.14, so it reaches the domain's outer face
   R = 12 near tau = 2.9.  After that the values next to R = 12 come from the
   face's linear-extrapolation condition (hji.make_grid, trap 2), an outflow
   approximation that M2 never validated.  Written to the json as tau_sat.
   Both grids extrapolate at R = 12, so this holds for the pole run too.

2. The inner face R = 0.2 (default grid only).  V is a minimum of ell along a
   trajectory, so V >= min ell = -beta at every node and every tau.  On the
   R_min = 0.2 grid the frozen-evader solve breaks that bound from tau ~ 0.75
   on, starting at the inner face near phi_1 = phi_2 = 0 (nose-on, closing at
   speed 2, i.e. leaving the domain through that face) and growing without
   limit: min V is -11 at tau = 1, about -7e3 at tau = 3 and about -8e8 at
   tau = 6, and the region below the bound spreads outward in R at about the
   closing speed.  M2's own configuration (test_m2.py, 101^3, T = 3) does the
   same -- min V = -1.45e4 at T = 3, 3.3 % of nodes more than 0.05 below
   -beta, out to R = 5.3 -- and none of test_m2.py's checks can see it.
   The pole removes it (M5/diag/diag_m2_pole.py, Layer 1 close-out Sec. 5).
   This script on 101 x 102^2 with LAYER1_POLE=1 (2026-11-02): min V = -0.825
   from tau = 0.75 to 6, 0 nodes below the bound, all checks pass.  The bound
   is reported as a check on either grid, and the count of offending nodes per
   tau goes to the json; the explorer greys those nodes out.

THE COMPARISON CHECK.  A frozen evader can only help player 1, so
V_frozen <= V_two-player node for node.  On the default grid the two-player
field is M3's Vsnap; on the pole grid it is M5's single-target V_1 on the same
pole grid (Vsnap_RA_<grid>_T<T>_single_pole.npz), the field of record that
replaced M3's.  The check is skipped if that file is not on disk.

Usage (from layer1/M2):
    python solve_m2_snap.py [n_R] [n_phi] [T_max]       (defaults 101 102 6)
    cmd:         set "LAYER1_POLE=1" && python solve_m2_snap.py
    PowerShell:  $env:LAYER1_POLE = "1"; python solve_m2_snap.py

Writes, to m2_out/ (<tag> = <n_R>x<n_phi>_T<T>, plus '_pole' on the pole grid):
    Vsnap_frozen_<tag>.npz  V(., tau) as float32, keys '0.000', '0.500', ...
                            (as M3's Vsnap), plus the node arrays R, phi1, phi2
    m2_frozen_<tag>.json    zone share per 0.25, outer edge per 0.25, front
                            speed, tau_sat, the checks below; on the pole grid
                            also R_nodes.  Every statistic is over the real rows.
"""

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'common'))

import hji
import hj_reachability as hj
import jax.numpy as jnp
import ell as E

POLE = os.environ.get('LAYER1_POLE', '0') == '1'
if POLE:
    sys.path.insert(0, os.path.join(HERE, '..', 'M5'))
    import pole

N_R = int(sys.argv[1]) if len(sys.argv) > 1 else 101
N_PHI = int(sys.argv[2]) if len(sys.argv) > 2 else 102
T_MAX = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0

DTAU = 0.25                 # reporting interval, as solve_m3.py
SNAP_EVERY = 0.5            # as M3's Vsnap
OUT = os.path.join(HERE, 'm2_out')
M3_SNAP = os.path.join(HERE, '..', 'M3', 'm3_out', 'Vsnap_%dx%d_T%g.npz' % (N_R, N_PHI, T_MAX))
M5_SNAP = os.path.join(HERE, '..', 'M5', 'm5_out', 'm5_out_V1_pole',
                       'Vsnap_RA_%dx%d_T%g_single_pole.npz' % (N_R, N_PHI, T_MAX))

FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------------------------
# The two grids
# ---------------------------------------------------------------------------

def build_grid(n_R, n_phi):
    """The R_min = 0.2 extrapolation grid, or the pole grid when LAYER1_POLE=1."""
    return pole.make_grid(n_R, n_phi) if POLE else hji.make_grid(n_R=n_R, n_phi=n_phi)


def solver_settings():
    """M3's update (min over time); on the pole grid, followed by the mirror fill."""
    return pole.single_target_settings('very_high') if POLE else hji.make_solver_settings('very_high')


def initial_value(grid):
    """V(x, 0) = ell, with the mirror rows filled on the pole grid."""
    V0 = jnp.asarray(E.ell_on_grid(grid))
    return pole.fill(V0) if POLE else V0


def real_rows(v):
    """The rows at R > 0: all of them, or the pole grid's without its mirror rows."""
    return pole.strip(v) if POLE else np.asarray(v)


def tag_for(n_R, n_phi, T_max):
    return '%dx%d_T%g%s' % (n_R, n_phi, T_max, '_pole' if POLE else '')


# ---------------------------------------------------------------------------
# The march
# ---------------------------------------------------------------------------

def outer_edge(inside, Rg):
    """Largest R node with any node of the zone on it."""
    rows = np.where(inside.any(axis=(1, 2)))[0]
    return float(Rg[rows.max()]) if rows.size else float('nan')


def march(grid, ss, V0, T_max, floor):
    """`floor`: nodes with V below it are counted (the lower-bound check).
    Statistics and snapshots are over the real rows."""
    dyn = hji.FrozenEvader()
    V = V0
    Rg = real_rows(grid.coordinate_vectors[0])

    Vr = real_rows(V)
    taus, frac, edge = [0.0], [float(np.mean(Vr <= 0))], [outer_edge(Vr <= 0, Rg)]
    minV, below, below_R = [float(Vr.min())], [int(np.sum(Vr < floor))], [float('nan')]
    snaps = {'0.000': Vr.astype(np.float32)}
    max_rise = 0.0                  # V must not increase with the horizon
    prev = Vr
    tau = 0.0
    t0 = time.time()
    while tau < T_max - 1e-12:
        nxt = min(tau + DTAU, T_max)
        V = hj.step(ss, dyn, grid, -tau, V, -nxt, progress_bar=False)
        V.block_until_ready()
        tau = nxt
        Vn = real_rows(V)
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
              'below bound: %d nodes, out to R = %.2f   (%.0f s)'
              % (tau, 100 * frac[-1], edge[-1], Vn.min(), below[-1], below_R[-1], time.time() - t0),
              flush=True)
    diag = dict(min_V=minV, below_bound=below, below_bound_R=below_R)
    return V, snaps, np.array(taus), np.array(frac), np.array(edge), max_rise, diag


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_ghost_rows(V):
    """Pole grid only: the mirror rows hold the flipped real rows after the last step."""
    res = pole.ghost_residual(V)
    report('mirror rows equal the flipped real rows after the last step', res == 0.0,
           'max |ghost - mirror| = %.1e' % res)


def reference_field(Rg):
    """(path, npz) of the two-player field to compare with, or (path, None) if it is not
    usable: M3's Vsnap on the default grid, M5's single-target V_1 on the pole grid."""
    path = M5_SNAP if POLE else M3_SNAP
    if not os.path.exists(path):
        return path, None
    z = np.load(path)
    if 'R' in z.files and (z['R'].shape != Rg.shape or np.max(np.abs(z['R'] - Rg)) > 1e-9):
        print('        (%s has other R rows: the comparison is skipped)' % os.path.relpath(path, HERE))
        return path, None
    return path, z


def check_against_two_player(snaps, Rg, cell):
    """V_frozen <= V_two-player at every common snapshot (test_m2.py Sec. 5)."""
    path, ref = reference_field(Rg)
    name = os.path.relpath(path, HERE)
    if ref is None:
        print('        (%s not usable: the comparison with the two-player field is skipped)' % name)
        return None, name
    common = [k for k in snaps if k in ref.files]
    worst = max(float(np.max(snaps[k] - ref[k])) for k in common)
    report('V(frozen) <= V(two-player, %s) at all %d common snapshots' % ('M5 single-target' if POLE else 'M3',
                                                                          len(common)),
           worst <= 2 * cell, 'max V_frozen - V_two-player = %+.2e  (one cell = %.4f)' % (worst, cell))
    return worst, name


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save(tag, grid, snaps, record):
    os.makedirs(OUT, exist_ok=True)
    npz = os.path.join(OUT, 'Vsnap_frozen_%s.npz' % tag)
    np.savez_compressed(npz, R=real_rows(grid.coordinate_vectors[0]),
                        phi1=np.asarray(grid.coordinate_vectors[1]),
                        phi2=np.asarray(grid.coordinate_vectors[2]), **snaps)
    js = os.path.join(OUT, 'm2_frozen_%s.json' % tag)
    json.dump(record, open(js, 'w'), indent=1)
    return npz, js


def main():
    if POLE and N_PHI % 2:
        sys.exit('the pole grid needs an even n_phi')
    grid = build_grid(N_R, N_PHI)
    tag = tag_for(N_R, N_PHI, T_MAX)
    Rg = real_rows(grid.coordinate_vectors[0])
    dR = float(grid.spacings[0])
    V0 = initial_value(grid)
    L0 = real_rows(V0)
    cell = E.value_scale(grid, values=L0)
    face = 'pole at R = 0 (M5/pole.py)' if POLE else 'extrapolation at R_min = %.1f' % Rg[0]
    print('=' * 92)
    print('M2 frozen evader, snapshotted   grid %d x %d x %d   T_max %.1f   ell scaling %s'
          % (N_R, N_PHI, N_PHI, T_MAX, E.SCALING))
    print('   inner face: %s;   real rows R = %.4f .. %.4f' % (face, Rg[0], Rg[-1]))
    print('=' * 92)
    print('   dR = %.5f   dphi = %.5f   one-cell value change = %.5f'
          % (dR, grid.spacings[1], cell))
    if N_PHI % 8 == 0:
        print('   WARNING: n_phi is a multiple of 8, so nodes sit on |phi_1| = beta (M3 grid rule).')

    # The lower bound: V = min_t ell(x(t)) >= min ell, and min ell = -beta on this
    # grid (phi_1 = 0 is a node).  A node more than one cell below it is not a value.
    ell_min = float(L0.min())
    floor = ell_min - cell
    print('   lower bound: min ell = %+.4f; nodes below %+.4f (one cell under it) are counted'
          % (ell_min, floor))

    t0 = time.time()
    V, snaps, taus, frac, edge, max_rise, diag = march(grid, solver_settings(), V0, T_MAX, floor)
    wall = time.time() - t0
    print('   march complete in %.0f s' % wall)
    print()

    print('-' * 92)
    print('Checks')
    print('-' * 92)
    report('V(., 0) is ell on the grid', np.array_equal(snaps['0.000'], L0.astype(np.float32)))
    if POLE:
        check_ghost_rows(V)
    report('V is non-increasing in the horizon (min over a longer time)', max_rise <= 1e-9,
           'largest rise between steps %.2e' % max_rise)
    below = np.array(diag['below_bound'])
    first_bad = float(taus[np.argmax(below > 0)]) if (below > 0).any() else None
    report('V >= min ell - one cell everywhere (V is a minimum of ell)', first_bad is None,
           'min V %.3g; first broken at tau = %s; at tau = %g, %d nodes (%.2f%%) out to R = %.2f'
           % (min(diag['min_V']), first_bad, taus[-1], below[-1], 100.0 * below[-1] / L0.size,
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

    worst, ref_name = check_against_two_player(snaps, Rg, cell)

    record = dict(game='frozen evader (sigma_2 = 0)', n_R=N_R, n_phi=N_PHI, T_max=T_MAX,
                  pole=POLE, inner_face=face,
                  dtau=DTAU, snap_every=SNAP_EVERY, scaling=E.SCALING, wall_s=wall,
                  taus=taus.tolist(), frac=frac.tolist(), outer_edge=edge.tolist(),
                  front_speed=sp, tau_sat=tau_sat, max_rise=max_rise,
                  max_frozen_minus_m3=worst, two_player_reference=ref_name, cell=float(cell),
                  ell_min=ell_min, floor=floor, first_below_floor_tau=first_bad,
                  min_V=diag['min_V'], below_floor=diag['below_bound'],
                  below_floor_outer_R=diag['below_bound_R'], fails=FAILS)
    if POLE:
        record['R_nodes'] = Rg.tolist()
    npz, js = save(tag, grid, snaps, record)
    print()
    print('   wrote %s' % os.path.relpath(npz, HERE))
    print('   wrote %s' % os.path.relpath(js, HERE))
    print('=' * 92)
    print(('M2 snapshots %s: all checks passed' % tag) if not FAILS else
          '%d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS)))
    print('=' * 92)


if __name__ == '__main__':
    main()
