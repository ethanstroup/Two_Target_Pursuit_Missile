"""
reach_avoid.py -- Layer 1, Milestone M5.  The two-target reach-avoid solve.

Layer1_Plan.md Sec. 4 (M5, redefined 2026-10-01) and the pre-registered criteria
claude/Layer1_M5_Criteria_2026-10-11.md.

WHAT IS SOLVED
--------------
    V_RA(x,tau) = min_{sigma_1} max_{sigma_2} min_{t in [0,tau]}
                      max{ ell_1(x(t)),  max_{s in [0,t]} -ell_2(x(s)) }

Fisac et al. (arXiv:1410.6445) Eq. (4) with payoff l = ell_1 and discriminator
g = -ell_2: player 1 reaches T_{1->2} without having entered T_{2->1} on the way,
against every player-2 behavior.  W_1 = {V_RA <= 0}.

THE UPDATE (derived in the criteria file, Sec. 2)
-------------------------------------------------
    V(x,0) = max(ell_1, -ell_2)
    V <- max( V + dtau * min(0, H_hat),  -ell_2 )          per TVD-RK3 step

`backwards_reachable_tube` supplies min(0, H_hat) at every Runge-Kutta stage and
`static_obstacle(-ell_2)` supplies the max after the full step.  Fisac's
Algorithm 1 takes the min with ell_1 instead of with the previous V; the two are
the same dynamic-programming step because V is non-increasing in tau.
`solver_settings(form='fisac')` builds Algorithm 1 literally, for check 1b.

Usage:  python3 reach_avoid.py n_R n_phi T_max [kind]
        kind = game (default)   the reach-avoid value V_RA
             | single           M3's single-target V_1 at the same horizon, for D
             | frozen_p2        sigma_2 == 0 (the check-3 smoke test)
        python3 reach_avoid.py cut <src_tag> T     outputs at horizon T from a longer march
"""

import json
import os
import sys
import time

import numpy as np
import jax.numpy as jnp

import hji
import hj_reachability as hj
import ell as E

OUT = 'm5_out'
DTAU = 0.25
SNAP_EVERY = float(os.environ.get('M5_SNAP_EVERY', '0.25'))
R_MARGIN = 0.45


# ---------------------------------------------------------------------------
# Constraint functions
# ---------------------------------------------------------------------------

def ell1_on_grid(grid):
    """ell for T_{1->2}, as M1-M4 use it."""
    return jnp.asarray(E.ell_on_grid(grid))


def ell2_on_grid(grid):
    """
    ell for T_{2->1}, written out independently rather than as ell_1 o S (check 1
    compares the two).  Boresight bound on the SHOOTER's own angle (phi_2), both
    range bounds on the TARGET's aspect angle (phi_1), weights keyed on phi_1.
    """
    st = grid.states
    R, p1, p2 = st[..., 0], st[..., 1], st[..., 2]
    g_bore = jnp.abs(p2) - E.BETA
    R_lo = E.A1 + E.B1 * jnp.cos(p1)
    R_hi = E.RBAR0 - jnp.abs(p1 + jnp.sin(p1))
    w_b, w_n, w_x = E._weights(jnp, p1)
    return jnp.maximum(w_b * g_bore, jnp.maximum(w_n * (R_lo - R), w_x * (R - R_hi)))


def swap(a):
    """S: (R, phi_1, phi_2) -> (R, phi_2, phi_1), an axis transpose on the grid."""
    return np.swapaxes(np.asarray(a), 1, 2)


def initial_value(ell1, ell2):
    """Fisac Eq. (17b): V(x,0) = max{l, g} = max{ell_1, -ell_2}."""
    return jnp.maximum(ell1, -ell2)


# ---------------------------------------------------------------------------
# Solver settings
# ---------------------------------------------------------------------------

def solver_settings(ell1, ell2, form='library', accuracy='very_high'):
    """
    form='library'  min(0, H_hat) at every stage, then max(., -ell_2) per step.
    form='fisac'    Algorithm 1 literally: unclamped H_hat, then min(., ell_1),
                    then max(., -ell_2), per step.
    """
    obstacle = -ell2
    if form == 'library':
        return hj.SolverSettings.with_accuracy(
            accuracy,
            hamiltonian_postprocessor=hj.solver.backwards_reachable_tube,
            value_postprocessor=hj.solver.static_obstacle(obstacle))
    if form == 'fisac':
        return hj.SolverSettings.with_accuracy(
            accuracy,
            hamiltonian_postprocessor=hj.solver.identity,
            value_postprocessor=lambda t, v: jnp.maximum(jnp.minimum(v, ell1), obstacle))
    raise ValueError(form)


def make_dynamics(kind='game'):
    """game / single: the full two-player game.  frozen_p2: sigma_2 == 0 (check 3)."""
    if kind in ('game', 'single'):
        return hji.TwoTargetPursuit()
    if kind == 'frozen_p2':
        return hji.FrozenEvader()
    raise ValueError(kind)


def problem(kind, ell1, ell2):
    """
    (solver settings, initial value) for each kind of solve.
    single: M3's single-target reach value V_1 (no obstacle, V(x,0) = ell_1), so the
    draw set D can be formed at the same horizon and on the same grids as V_RA.
    """
    if kind == 'single':
        return hji.make_solver_settings('very_high'), ell1
    return solver_settings(ell1, ell2, 'library'), initial_value(ell1, ell2)


# ---------------------------------------------------------------------------
# The march
# ---------------------------------------------------------------------------

def surface_mask(inside):
    """Nodes the zero level set passes through: a 6-neighbour of opposite sign."""
    b = np.zeros_like(inside)
    for ax in range(3):
        for sh in (1, -1):
            b |= (inside != np.roll(inside, sh, axis=ax))
    return b


def is_snapshot_time(tau, every):
    return every > 0 and abs(tau / every - round(tau / every)) < 1e-9


def march(grid, dyn, ss, V0, T_max, dtau=DTAU, snap_every=SNAP_EVERY, log=print):
    """
    Step V backward from V0 to T_max with hj.step, keeping only what is needed:
    the current field, float32 snapshots, the arrival time, and the motion of
    the zero level set per dtau.
    """
    V = jnp.asarray(V0)
    Vn = np.asarray(V)
    t_arr = np.full(Vn.shape, np.inf, dtype=np.float32)
    t_arr[Vn <= 0] = 0.0
    taus, frac, moved = [0.0], [float(np.mean(Vn <= 0))], [np.nan]
    snaps = {'%.3f' % 0.0: Vn.astype(np.float32)}
    prev = Vn <= 0
    tau = 0.0
    t0 = time.time()
    while tau < T_max - 1e-12:
        nxt = min(tau + dtau, T_max)
        V = hj.step(ss, dyn, grid, -tau, V, -nxt, progress_bar=False)
        V.block_until_ready()
        tau = nxt
        Vn = np.asarray(V)
        inside = Vn <= 0
        t_arr[inside & np.isinf(t_arr)] = tau
        taus.append(tau)
        frac.append(float(inside.mean()))
        moved.append(float(np.mean(inside != prev)))
        prev = inside
        if is_snapshot_time(tau, snap_every):
            snaps['%.3f' % tau] = Vn.astype(np.float32)
        log('   tau = %5.2f   {V<=0} = %7.4f%%   moved = %.5f%%   min V = %+.4f   (%.0f s)'
            % (tau, 100 * frac[-1], 100 * moved[-1], Vn.min(), time.time() - t0))
    return Vn, t_arr, np.array(taus), np.array(frac), np.array(moved), snaps, time.time() - t0


def surface_motion(V, moved):
    """Per-step motion of the zero level set as a fraction of the surface's own node count."""
    nb = int(surface_mask(V <= 0).sum())
    return moved * V.size / max(nb, 1), nb


def choose_horizon(taus, surf, tol=5e-3, t_min=6.0):
    """
    Criteria Sec. 3.2: the smallest integer tau >= t_min such that every step from
    there to the end of the march moves less than `tol` of the surface.
    """
    for T in np.arange(np.ceil(t_min), taus[-1] + 1e-9, 1.0):
        tail = surf[taus > T + 1e-9]
        if tail.size and np.all(tail < tol):
            return float(T)
    return None


# ---------------------------------------------------------------------------
# Check 1 (pre-flight)
# ---------------------------------------------------------------------------

def check_ell2_transpose(grid, ell1, ell2):
    cell = E.value_scale(grid)
    e = float(np.abs(np.asarray(ell2) - swap(ell1)).max())
    return e <= 1e-6 * cell, e, cell


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def tag_for(n_R, n_phi, T_max, kind):
    return '%dx%d_T%g%s' % (n_R, n_phi, T_max, '' if kind == 'game' else '_' + kind)


def save_outputs(tag, V, t_arr, snaps, diag):
    os.makedirs(OUT, exist_ok=True)
    np.save('%s/VRA_%s.npy' % (OUT, tag), V)
    np.save('%s/tRA_%s.npy' % (OUT, tag), t_arr)
    np.savez('%s/VRAsnap_%s.npz' % (OUT, tag), **snaps)
    np.savez_compressed('%s/m5_%s_fields.npz' % (OUT, tag),
                        V=V.astype(np.float32), tRA=t_arr)
    json.dump(diag, open('%s/m5_%s.json' % (OUT, tag), 'w'), indent=1)


def cut_horizon(src_tag, T):
    """
    Outputs for horizon T taken from a longer march (the same march, stopped earlier):
    V(., T) is the float32 snapshot at T, diagnostics and snapshots are truncated to
    tau <= T, and arrival times beyond T become inf.
    """
    d = json.load(open('%s/m5_%s.json' % (OUT, src_tag)))
    z = np.load('%s/VRAsnap_%s.npz' % (OUT, src_tag))
    snaps = {k: z[k] for k in z.files if float(k) <= T + 1e-9}
    V = snaps['%.3f' % T].astype(np.float64)
    t_arr = np.load('%s/tRA_%s.npy' % (OUT, src_tag))
    t_arr = np.where(t_arr <= T + 1e-9, t_arr, np.inf).astype(np.float32)
    keep = np.array(d['taus']) <= T + 1e-9
    diag = dict(d)
    for key in ('taus', 'frac', 'moved'):
        diag[key] = list(np.array(d[key])[keep])
    surf, nb = surface_motion(V, np.array(diag['moved']))      # normalized by the tau = T surface
    diag.update(T_max=T, cut_from=src_tag, surf_motion=surf.tolist(), surface_nodes=nb)
    tag = src_tag.rsplit('_T', 1)[0] + '_T%g' % T
    save_outputs(tag, V, t_arr, snaps, diag)
    return tag


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'cut':
        print('wrote', cut_horizon(sys.argv[2], float(sys.argv[3])))
        return
    n_R = int(sys.argv[1]) if len(sys.argv) > 1 else 101
    n_phi = int(sys.argv[2]) if len(sys.argv) > 2 else 102
    T_max = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    kind = sys.argv[4] if len(sys.argv) > 4 else 'game'
    tag = tag_for(n_R, n_phi, T_max, kind)

    grid = hji.make_grid(n_R=n_R, n_phi=n_phi)
    ell1, ell2 = ell1_on_grid(grid), ell2_on_grid(grid)
    print('=' * 92)
    print('M5 reach-avoid solve   grid %d x %d x %d   T_max %.1f   dyn %s   ell %s'
          % (n_R, n_phi, n_phi, T_max, kind, E.SCALING))
    print('=' * 92)

    ok, e, cell = check_ell2_transpose(grid, ell1, ell2)
    print('   one-cell value change delta = %.5f' % cell)
    print('   %s  check 1: ell_2 (independent) == ell_1 o S   max |diff| = %.2e  (bar %.2e)'
          % ('PASS' if ok else 'FAIL', e, 1e-6 * cell))

    ss, V0 = problem(kind, ell1, ell2)
    V, t_arr, taus, frac, moved, snaps, wall = march(grid, make_dynamics(kind), ss, V0, T_max)
    surf, nb = surface_motion(V, moved)
    T_star = choose_horizon(taus, surf)
    print('   march complete in %.0f s;  surface %d nodes;  final step moves %.4f%% of it'
          % (wall, nb, 100 * surf[-1]))
    print('   horizon rule (criteria 3.2): T_RA = %s' % T_star)

    diag = dict(n_R=n_R, n_phi=n_phi, T_max=T_max, kind=kind, dtau=DTAU, scaling=E.SCALING,
                cell=cell, check1=dict(ok=bool(ok), max_diff=e), wall_s=wall,
                taus=taus.tolist(), frac=frac.tolist(), moved=moved.tolist(),
                surf_motion=surf.tolist(), surface_nodes=nb, T_RA=T_star,
                snap_every=SNAP_EVERY)
    save_outputs(tag, V, t_arr, snaps, diag)
    print('   wrote %s/{VRA,tRA}_%s.npy, VRAsnap_%s.npz, m5_%s.json' % (OUT, tag, tag, tag))


if __name__ == '__main__':
    main()
