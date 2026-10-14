"""
verify_pole.py -- the verification tests of claude/Layer1_M5_InnerFace_2026-10-13.md Sec. 4.

  v1   pole grid vs exact inertial truth, both controls frozen at (0,0) and (+1,-1),
       61 x 62^2, T = 4; the R_min = 0.1 extrapolation grid as the "before"
  v2   check 3's 500 rollouts integrated two ways: reduced + pole.stepper, and exact inertial
  v3   coarse pole-grid fields vs the R_min = 0.2 fields, away from the face; near-face W_1
  v4   near-face guarantee, check 11 and check 13 on the coarse pole grid; the near-face test
       on the R_min = 0.2 grid as the "before"

Usage:  python verify_pole.py v1|v2|v3|v4 [n_R n_phi]   (grid sizes for v3/v4; default 101 102)
"""

import json
import os
import sys

import numpy as np

import hji
import ell as E
import pole
import inertial as IN
import reach_avoid as RA
import sim_m5 as SIM
import smoke_m5 as SM

OUT = 'm5_out/pole'
N_R, N_PHI = 61, 62
R_MASK = 0.45
RESULTS = {}


def report(name, ok, msg):
    state = {True: 'PASS', False: 'FAIL'}.get(ok, ok)
    print('  %-14s %s   %s' % (state, name, msg))
    RESULTS[name] = dict(state=state, msg=msg)


def header(s):
    print('-' * 96)
    print(s)
    print('-' * 96)


def save(tag):
    os.makedirs(OUT, exist_ok=True)
    json.dump(RESULTS, open('%s/verify_%s.json' % (OUT, tag), 'w'), indent=1, default=str)


# ---------------------------------------------------------------------------
# V1
# ---------------------------------------------------------------------------

def frozen_solve(grid, c1, c2, T, use_pole):
    ell1, ell2 = RA.ell1_on_grid(grid), RA.ell2_on_grid(grid)
    if use_pole:
        ss, V0 = pole.reach_avoid_settings(ell2), pole.fill(RA.initial_value(ell1, ell2))
    else:
        ss, V0 = RA.solver_settings(ell1, ell2, 'library'), RA.initial_value(ell1, ell2)
    V = RA.march(grid, SM.FixedControls(c1, c2), ss, V0, T, snap_every=0.0, log=lambda s: None)[0]
    return pole.strip(V) if use_pole else V


def real_geom(grid, use_pole):
    R = np.asarray(grid.coordinate_vectors[0])
    if use_pole:
        R = R[pole.N_GHOST:]
    return SIM.Geom((len(R), N_PHI, N_PHI), R_min=float(R[0]), R_max=float(R[-1]))


def v1_case(c1, c2, T, use_pole, label):
    grid = pole.make_grid(N_R, N_PHI) if use_pole else hji.make_grid(N_R, N_PHI, R_min=0.1)
    V = frozen_solve(grid, c1, c2, T, use_pole)
    geom = real_geom(grid, use_pole)
    x0 = geom.node_states(np.arange(V.size))
    J, left, r_min = IN.exact_outcome(x0, c1, c2, T)
    J, left, r_min = (a.reshape(V.shape) for a in (J, left, r_min))
    far, tot = SM.far_disagreements(V <= 0, J <= 0, 2, ~left)
    near_pole = int(np.count_nonzero(r_min < 0.25))
    inner = int(np.count_nonzero(r_min < geom.R_min))
    far_inner = 0
    if not use_pole:
        near = SM.dilate(RA.surface_mask(V <= 0), 2) | SM.dilate(RA.surface_mask(J <= 0), 2)
        far_inner = int(np.count_nonzero(((V <= 0) != (J <= 0)) & ~left & (r_min < geom.R_min) & ~near))
    err = np.abs(V - J)[~left]
    print('   %s (%+g,%+g): far flips %d of %d;  paths inside R<0.25: %d;  paths below the grid edge: %d;'
          '  excluded (left through R=12): %d;  |V-J| median %.4f 95th %.4f'
          % (label, c1, c2, far, tot, near_pole, inner, int(left.sum()), np.median(err), np.percentile(err, 95)))
    if not use_pole:
        print('      of the far flips, %d have exact paths that pass below the grid edge' % far_inner)
    return far, tot, near_pole, inner, int(left.sum())


def v1(T=4.0):
    header('V1  pole grid vs exact inertial truth, %d x %d^2, T = %g' % (N_R, N_PHI, T))
    print('   conventions: round trip %.1e, one-step reduced vs exact %.1e' % IN.check_conventions())
    print('   dynamics equivariance under the flip: %.1e' % pole.dynamics_equivariance())
    for c1, c2 in ((0.0, 0.0), (1.0, -1.0)):
        far, tot, near_pole, _, n_left = v1_case(c1, c2, T, True, 'pole        ')
        report('V1 (%+g,%+g)' % (c1, c2), far == 0 and near_pole >= 1000,
               '%d far flips of %d; %d paths inside R<0.25 (informative if >= 1000); %d excluded at R=12'
               % (far, tot, near_pole, n_left))
        v1_case(c1, c2, T, False, 'R_min=0.1 ext')
    save('v1')


# ---------------------------------------------------------------------------
# V2
# ---------------------------------------------------------------------------

def frozen_p2_pole(T):
    grid = pole.make_grid(N_R, N_PHI)
    ell1, ell2 = RA.ell1_on_grid(grid), RA.ell2_on_grid(grid)
    V, _, _, _, _, snaps, _ = RA.march(grid, hji.FrozenEvader(), pole.reach_avoid_settings(ell2),
                                       pole.fill(RA.initial_value(ell1, ell2)), T, log=lambda s: None)
    return grid, V, snaps


def check3_starts(grid, V, n=500, seed=0):
    cell = E.value_scale(grid)
    R = np.asarray(grid.states[..., 0])
    om = (R >= R_MASK) & (np.asarray(RA.ell1_on_grid(grid)) > 0) & (np.asarray(RA.ell2_on_grid(grid)) > 0)
    cand = np.nonzero(((V <= -cell) & om).ravel())[0]
    return np.random.default_rng(seed).choice(cand, size=min(n, cand.size), replace=False), cand.size


def v2(T=4.0):
    header('V2  check 3 rollouts: reduced + pole.stepper vs exact inertial, T = %g' % T)
    grid, V, snaps = frozen_p2_pole(T)
    geom = pole.geom(grid)
    pick, n_pool = check3_starts(grid, V)
    x0 = geom.node_states(pick)
    stack = SIM.SnapshotStack(geom, snaps, keep=(1,))
    law1, law2 = SIM.law_value_p1(stack, T), SIM.law_zero()
    a = SIM.rollout(x0, law1, law2, T, stepper=pole.stepper, exit_lo=-np.inf)
    b = IN.rollout(x0, law1, law2, T)
    same = a['outcome'] == b['outcome']
    both = (a['outcome'] == SIM.WIN) & (b['outcome'] == SIM.WIN)
    dt = np.abs(a['t_end'] - b['t_end'])[both]
    print('   pool %d, 500 drawn (seed 0)' % n_pool)
    print('   (a) reduced + pole stepper: %s' % SIM.summarize(a['outcome']))
    print('   (b) exact inertial:         %s' % SIM.summarize(b['outcome']))
    print('   (b) runs passing inside R < 0.25: %d;  inside R < 0.1: %d'
          % (int(np.sum(b['r_min'] < 0.25)), int(np.sum(b['r_min'] < 0.1))))
    print('   kill-time |(a)-(b)| over runs both won: median %.2e, 99th %.2e, max %.2e'
          % (np.median(dt), np.percentile(dt, 99), dt.max()))
    for i in np.nonzero(~same | (b['outcome'] != SIM.WIN))[0]:
        print('   start %s  (a) %s t=%.3f  (b) %s t=%.3f'
              % (np.round(x0[i], 3).tolist(), SIM.OUTCOME_NAMES[a['outcome'][i]], a['t_end'][i],
                 SIM.OUTCOME_NAMES[b['outcome'][i]], b['t_end'][i]))
    report('V2', bool(np.all(b['outcome'] == SIM.WIN) and np.all(same)),
           '(b) wins %d / %d; outcomes identical in %d / %d'
           % (int(np.sum(b['outcome'] == SIM.WIN)), len(pick), int(same.sum()), len(pick)))
    save('v2')


# ---------------------------------------------------------------------------
# V3 / V4 helpers: loading the coarse fields
# ---------------------------------------------------------------------------

T_RA = 6.0
M5, M3 = 'm5_out', 'm3_out'


def load_pole(n_R, n_phi, kind='game'):
    """Full pole-grid field (ghost rows included), its snapshots, the arrival field and the grid."""
    tag = '%dx%d_T%g%s_pole' % (n_R, n_phi, T_RA, '' if kind == 'game' else '_' + kind)
    V = np.load('%s/VRA_%s.npy' % (M5, tag))
    t = np.load('%s/tRA_%s.npy' % (M5, tag)).astype(float)
    z = np.load('%s/VRAsnap_%s.npz' % (M5, tag))
    return V, {k: z[k] for k in z.files}, t, pole.make_grid(n_R, n_phi)


def load_old(kind='game'):
    """The R_min = 0.2 coarse fields: M5's V_RA, or M3's V_1 and t_1*."""
    if kind == 'game':
        z = np.load('%s/VRAsnap_101x102_T6.npz' % M5)
        return np.load('%s/VRA_101x102_T6.npy' % M5), {k: z[k] for k in z.files}, None
    z = np.load('%s/Vsnap_101x102_T6.npz' % M3)
    return (np.load('%s/V_101x102_T6.npy' % M3), {k: z[k] for k in z.files},
            np.load('%s/t1_101x102_T6.npy' % M3))


def old_R(n_R=101):
    return np.linspace(0.2, 12.0, n_R)


def interp_R(V_old, R_old, R_new):
    """Linear interpolation along R only (the angle nodes coincide); NaN outside R_old."""
    pos = (R_new - R_old[0]) / (R_old[1] - R_old[0])
    i0 = np.clip(np.floor(pos).astype(int), 0, len(R_old) - 2)
    w = (pos - i0)[:, None, None]
    out = (1 - w) * V_old[i0] + w * V_old[i0 + 1]
    out[(R_new < R_old[0]) | (R_new > R_old[-1])] = np.nan
    return out


def omega_on(R, P1, P2):
    l1, l2 = E.ell(R, P1, P2), E.ell(R, P2, P1)
    return (R >= R_MASK) & (l1 > 0) & (l2 > 0)


def mesh(R, n_phi):
    P = -np.pi + np.arange(n_phi) * 2 * np.pi / n_phi
    return np.meshgrid(R, P, P, indexing='ij')


def sign_compare(Va, Vb, Rg, valid, bands=((0.45, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, 12.01))):
    """Sign disagreements, total and more than 2 cells from either zero set, overall and by R band."""
    a, b = Va <= 0, Vb <= 0
    near = SM.dilate(RA.surface_mask(a), 2) | SM.dilate(RA.surface_mask(b), 2)
    diff = (a != b) & valid
    far = diff & ~near
    rows = []
    for lo, hi in bands:
        m = (Rg >= lo) & (Rg < hi)
        rows.append((lo, hi, int((diff & m).sum()), int((far & m).sum()), int((valid & m).sum())))
    return far, rows


# ---------------------------------------------------------------------------
# V3
# ---------------------------------------------------------------------------

def v3_field(name, V_pole_full, V_old):
    Vp = pole.strip(V_pole_full)
    Rp = np.asarray(pole.make_grid(Vp.shape[0], Vp.shape[1]).coordinate_vectors[0])[pole.N_GHOST:]
    Vo = interp_R(V_old, old_R(V_old.shape[0]), Rp)
    Rg, P1, P2 = mesh(Rp, Vp.shape[1])
    valid = omega_on(Rg, P1, P2) & np.isfinite(Vo)
    far, rows = sign_compare(Vp, np.nan_to_num(Vo, nan=1.0), Rg, valid)
    far_R1 = int((far & (Rg >= 1.0)).sum())
    print('   %s: sign disagreements (total / more than 2 cells from either zero set / nodes compared)' % name)
    for lo, hi, n_d, n_f, n_v in rows:
        print('      R in [%.2f, %5.2f): %6d / %4d / %8d' % (lo, hi, n_d, n_f, n_v))
    report('V3 %s' % name, far_R1 == 0, '%d far disagreements at R >= 1' % far_R1)
    return Vp, Rp, Rg, P1, P2


def w1_near_face(V_real, Rg, P1, P2, lo=R_MASK, hi=1.0):
    m = omega_on(Rg, P1, P2) & (Rg >= lo) & (Rg < hi)
    return float(np.mean(V_real[m] <= 0)), int(m.sum())


def v3(n_R=101, n_phi=102):
    header('V3  coarse pole grid vs the R_min = 0.2 fields (T = %g)' % T_RA)
    Vra_p, _, _, _ = load_pole(n_R, n_phi, 'game')
    V1_p, _, _, _ = load_pole(n_R, n_phi, 'single')
    Vra_o, _, _ = load_old('game')
    V1_o, _, _ = load_old('single')
    Vp, Rp, Rg, P1, P2 = v3_field('V_RA', Vra_p, Vra_o)
    V1p, _, _, _, _ = v3_field('V_1 ', V1_p, V1_o)

    print('   partition over Omega (R >= 0.45), old grid vs pole grid:')
    Ro = old_R()
    Rgo, P1o, P2o = mesh(Ro, 102)
    for label, Vr, V1, R_, A, B in (('old ', Vra_o, V1_o, Rgo, P1o, P2o), ('pole', Vp, V1p, Rg, P1, P2)):
        om = omega_on(R_, A, B)
        W1 = (Vr <= 0) & om
        D = (V1 > 0) & (np.swapaxes(V1, 1, 2) > 0) & om
        W2 = np.swapaxes(Vr <= 0, 1, 2) & om
        C = om & ~(W1 | W2 | D)
        print('      %s  W_1 %.4f%%  D %.4f%%  C %.4f%%   (Omega %d nodes)'
              % (label, 100 * W1.sum() / om.sum(), 100 * D.sum() / om.sum(), 100 * C.sum() / om.sum(), om.sum()))

    print('   W_1 share of Omega at 0.45 <= R < 1 (near the face):')
    f, n = w1_near_face(Vra_o, Rgo, P1o, P2o)
    print('      old  (R_min = 0.2, 101 rows): %.4f%% of %d nodes' % (100 * f, n))
    for nr, nphi in ((51, 52), (101, 102)):
        try:
            Vx = pole.strip(load_pole(nr, nphi, 'game')[0])
        except FileNotFoundError:
            print('      pole %dx%d: not solved' % (nr, nphi))
            continue
        Rx = np.asarray(pole.make_grid(nr, nphi).coordinate_vectors[0])[pole.N_GHOST:]
        f, n = w1_near_face(Vx, *mesh(Rx, nphi))
        print('      pole %3d rows x %d^2:          %.4f%% of %d nodes' % (nr, nphi, 100 * f, n))
    save('v3')


# ---------------------------------------------------------------------------
# V4
# ---------------------------------------------------------------------------

import test_m5 as TM
import converse_m5 as CV

POLE_KW = dict(stepper=pole.stepper, exit_lo=-np.inf)


N_NEAR = 1000


def near_face_starts(V, om, Rg, cell, n=None, seed=0):
    n = N_NEAR if n is None else n
    cand = np.nonzero(((V <= -cell) & om & (Rg < 1.0)).ravel())[0]
    return np.random.default_rng(seed).choice(cand, size=min(n, cand.size), replace=False), cand.size


def run_near_face(label, geom, V, om, Rg, cell, snaps_ra, snaps_v1, t1, kw):
    starts, n_pool = near_face_starts(V, om, Rg, cell)
    x0 = geom.node_states(starts)
    s_ra, s_v1 = SIM.SnapshotStack(geom, snaps_ra), SIM.SnapshotStack(geom, snaps_v1)
    laws = TM.player2_laws(s_ra, s_v1, t1, T_RA, len(starts) * 5)
    print('   %s: near-face pool %d (0.45 <= R < 1, V_RA <= -delta, Omega), %d drawn' % (label, n_pool, len(starts)))
    oc, fail, _ = TM.run_guarantee(label, x0, SIM.law_value_p1(s_ra, T_RA), laws, T_RA, kw)
    return int((oc != SIM.WIN).sum()), oc.size


def v4(n_R=101, n_phi=102):
    header('V4  guarantees near the face, coarse pole grid (T = %g)' % T_RA)
    Vra, snaps_ra, _, grid = load_pole(n_R, n_phi, 'game')
    V1, snaps_v1, t1, _ = load_pole(n_R, n_phi, 'single')
    geom = pole.geom(grid)
    cell = E.value_scale(grid)
    om = TM.omega(geom)
    Rg = np.asarray(grid.states[..., 0])

    n_fail, n_runs = run_near_face('(a) pole grid', geom, Vra, om, Rg, cell, snaps_ra, snaps_v1, t1, POLE_KW)
    report('V4a near-face guarantee', n_fail == 0, '%d failed runs of %d' % (n_fail, n_runs))

    Vo, so_ra, _ = load_old('game')
    V1o, so_v1, t1o = load_old('single')
    geom_o = SIM.Geom(Vo.shape)
    nf_o, nr_o = run_near_face('(a, before) R_min = 0.2 grid', geom_o, Vo, TM.omega(geom_o),
                               geom_o.node_states(np.arange(Vo.size))[:, 0].reshape(Vo.shape),
                               E.value_scale(hji.make_grid(101, 102)), so_ra, so_v1, t1o, None)
    print('   before (report only): %d failed runs of %d on the R_min = 0.2 grid' % (nf_o, nr_o))

    lab, _ = TM.label_periodic((Vra <= 0) & om, False)
    starts, n_cand = TM.pick_starts(Vra, om, cell, lab)
    x0 = geom.node_states(starts)
    s_ra, s_v1 = SIM.SnapshotStack(geom, snaps_ra), SIM.SnapshotStack(geom, snaps_v1)
    laws = TM.player2_laws(s_ra, s_v1, t1, T_RA, len(starts) * 5)
    print('   (b) check 11: %d candidates, %d drawn' % (n_cand, len(starts)))
    oc, _, _ = TM.run_guarantee('(b) check 11, pole grid', x0, SIM.law_value_p1(s_ra, T_RA), laws, T_RA, POLE_KW)
    report('V4b check 11', int((oc != SIM.WIN).sum()) == 0, '%d failed runs of %d' % (int((oc != SIM.WIN).sum()), oc.size))

    pool = CV.converse_pool(Vra, V1, om, cell)
    cs = CV.draw_starts(pool)
    xc = geom.node_states(cs)
    n_tot = len(cs) * 5
    p2 = TM.player2_laws(s_ra, s_v1, t1, T_RA, n_tot)
    p1 = CV.player1_laws(s_ra, s_v1, t1, T_RA, n_tot)
    wins, informative = 0, 0
    print('   (c) check 13: pool %d, %d drawn' % (pool.size, len(cs)))
    for name, law1 in zip(CV.P1_NAMES, p1):
        tab = CV.outcome_table(xc, law1, p2, T_RA, POLE_KW)
        CV.print_table(name, tab)
        wins += int(np.sum(tab[:, 0] == SIM.WIN))
        if name == 'single-target law':
            informative = int(np.sum(tab[:, 1] == SIM.WIN))
    report('V4c check 13', wins == 0 and informative >= 20,
           '%d wins alone against the adversary in %d runs; informative %d' % (wins, len(cs) * 5, informative))
    save('v4')


def main():
    which = sys.argv[1]
    print('=' * 96)
    print('Pole-condition verification: %s' % which)
    print('=' * 96)
    sizes = [int(a) for a in sys.argv[2:4]] if which in ('v3', 'v4') else []
    {'v1': v1, 'v2': v2, 'v3': v3, 'v4': v4}[which](*sizes)


if __name__ == '__main__':
    main()
