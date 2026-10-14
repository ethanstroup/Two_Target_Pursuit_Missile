"""
test_m5.py -- Layer 1, M5.  Checks 4-12 and the report-only quantities of the
pre-registered criteria (claude/Layer1_M5_Criteria_2026-10-11.md, Sec. 4).

Reads the outputs of reach_avoid.py (m5_out/) for the reach-avoid value V_RA and
the single-target value V_1 at the same horizon, and M3's arrival-time field and
snapshots (m3_out/) where the criteria call for them.

Usage:  python3 test_m5.py T_RA [stage ...]
        stages: fields (4-10, reports), all (default: fields, then 11, 12 and C2)
Environment:
        COARSE, FINE, THIRD   grid tags without the horizon, default 101x102, 201x204, 51x51
                              (51x52 with the pole: its map needs an even n_phi)
        LAYER1_POLE=1         score the pole-grid runs (tags ending _pole), with V_1 from
                              reach_avoid.py's `single` pole solves (M3's fields are on the
                              other grid).  Field checks use the rows at R > 0; rollouts use the
                              full grid and pole.stepper.  Check 8 interpolates the fine field in
                              R, since pole rows don't nest (claude/Layer1_M5_InnerFace_2026-10-13.md
                              Sec. 8).  Results go to test_m5_T<T>_pole.json.
A grid whose V_1 is not solved yet gets the checks that need only V_RA (4, 7, 8, 9, 10).
"""

import json
import os
import sys

import numpy as np
from scipy import ndimage

import ell as E
import sim_m5 as SIM

OUT = 'm5_out'
M3 = 'm3_out'
R_MARGIN = 0.45
FAILS, RESULTS = [], {}
POLE = SIM.POLE
SUFFIX = '_pole' if POLE else ''


def report(name, ok, msg=''):
    state = {True: 'PASS', False: 'FAIL', None: 'UNRESOLVED'}[ok]
    print('  %-10s %s%s' % (state, name, ('   ' + msg) if msg else ''))
    RESULTS[name] = dict(state=state, msg=msg)
    if ok is False:
        FAILS.append(name)


def header(s):
    print('-' * 96)
    print(s)
    print('-' * 96)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_npy_or_fields(path_npy, path_npz, key):
    if os.path.exists(path_npy):
        return np.load(path_npy).astype(np.float64)
    return np.load(path_npz)[key].astype(np.float64)


def run_tag(grid_tag, T, kind='game'):
    """reach_avoid.py's tag: '101x102_T6', '101x102_T6_single', ... and '_pole' on pole runs."""
    return '%s_T%g%s%s' % (grid_tag, T, '' if kind == 'game' else '_' + kind, SUFFIX)


def load_ra(tag):
    V = load_npy_or_fields('%s/VRA_%s.npy' % (OUT, tag), '%s/m5_%s_fields.npz' % (OUT, tag), 'V')
    diag = json.load(open('%s/m5_%s.json' % (OUT, tag)))
    if bool(diag.get('pole', False)) != POLE:
        raise ValueError('%s: run pole=%s but LAYER1_POLE=%d' % (tag, diag.get('pole', False), POLE))
    return V, diag


def load_single(grid_tag, T):
    """V_1 and t_1* at horizon T: from m5_out (kind=single) if solved, else M3 (old grids only)."""
    tag = run_tag(grid_tag, T, 'single')
    if os.path.exists('%s/m5_%s.json' % (OUT, tag)):
        V = load_npy_or_fields('%s/VRA_%s.npy' % (OUT, tag), '%s/m5_%s_fields.npz' % (OUT, tag), 'V')
        t = load_npy_or_fields('%s/tRA_%s.npy' % (OUT, tag), '%s/m5_%s_fields.npz' % (OUT, tag), 'tRA')
        return V, t, tag
    if POLE:
        raise FileNotFoundError('no %s/m5_%s.json (LAYER1_POLE=1 reach_avoid.py %s %g single)'
                                % (OUT, tag, grid_tag.replace('x', ' '), T))
    tag3 = '%s_T6' % grid_tag
    return np.load('%s/V_%s.npy' % (M3, tag3)), np.load('%s/t1_%s.npy' % (M3, tag3)), 'M3 ' + tag3


def single_snap_path(grid_tag, T):
    """V_1 snapshots: the m5_out single solve if there is one, else M3's (old grids only)."""
    p = '%s/VRAsnap_%s.npz' % (OUT, run_tag(grid_tag, T, 'single'))
    return p if (os.path.exists(p) or POLE) else '%s/Vsnap_%s_T6.npz' % (M3, grid_tag)


def node_R(diag, n_R):
    """Every row's R: the json's R_nodes (pole rows, ghost rows included), else hji's default."""
    if 'R_nodes' in diag:
        return np.asarray(diag['R_nodes'], float)
    return np.linspace(SIM.R_LO_DOM, SIM.R_HI_DOM, n_R)


def load_set(grid_tag, T):
    """
    One grid's fields, or None if its reach-avoid solve is missing.  Field checks use the
    rows at R > 0 (V_ra, V1, geom); rollouts use the full grid (geom_sim, t1, the snapshot
    files), which on a pole grid includes the mirror rows below zero.  V1 is None if the
    single-target solve is missing.
    """
    tag = run_tag(grid_tag, T)
    if not os.path.exists('%s/m5_%s.json' % (OUT, tag)):
        return None
    V, diag = load_ra(tag)
    R = node_R(diag, V.shape[0])
    i0 = int(np.searchsorted(R, 0.0))
    n_phi = V.shape[1]
    s = dict(tag=tag, grid=grid_tag, diag=diag, cell=diag['cell'], V_ra=V[i0:], R=R[i0:],
             geom=SIM.Geom.from_R(R[i0:], n_phi), geom_sim=SIM.Geom.from_R(R, n_phi),
             snaps_ra='%s/VRAsnap_%s.npz' % (OUT, tag), V1=None, t1=None, v1tag=None, snaps_v1=None)
    try:
        V1, t1, v1tag = load_single(grid_tag, T)
    except FileNotFoundError as e:
        print('  (%s)' % e)
        return s
    if V1.shape != V.shape:
        raise ValueError('%s: V_1 shape %s vs V_RA %s' % (v1tag, V1.shape, V.shape))
    s.update(V1=V1[i0:], t1=t1, v1tag=v1tag, snaps_v1=single_snap_path(grid_tag, T))
    return s


def load_snaps(path):
    z = np.load(path)
    return {k: z[k] for k in z.files}


# ---------------------------------------------------------------------------
# Grid-set helpers
# ---------------------------------------------------------------------------

def swap(a):
    return np.swapaxes(a, 1, 2)


def reflect(a):
    """Rf: phi -> -phi is the index map k -> (n - k) mod n on an endpoint=False grid."""
    n1, n2 = a.shape[1], a.shape[2]
    return a[:, (-np.arange(n1)) % n1][:, :, (-np.arange(n2)) % n2]


def node_ells(geom):
    R, P = geom.coords()
    Rg, P1, P2 = np.meshgrid(R, P, P, indexing='ij')
    return Rg, P1, P2, E.ell(Rg, P1, P2), E.ell(Rg, P2, P1)


def omega(geom):
    """Live play: R >= 0.45 and outside both target sets."""
    Rg, _, _, l1, l2 = node_ells(geom)
    return (Rg >= R_MARGIN) & (l1 > 0) & (l2 > 0)


def partition(V_ra, V1, om):
    W1 = V_ra <= 0
    W2 = swap(W1)
    D = (V1 > 0) & (swap(V1) > 0)
    C = om & ~(W1 | W2 | D)
    return W1, W2, D, C


def surface_mask(inside):
    b = np.zeros_like(inside)
    for ax in range(3):
        for sh in (1, -1):
            b |= (inside != np.roll(inside, sh, axis=ax))
    return b


def label_periodic(mask, full=False):
    """Connected components, periodic in both angles (face-connected unless full)."""
    st = ndimage.generate_binary_structure(3, 3 if full else 1)
    lab, n = ndimage.label(mask, structure=st)
    parent = np.arange(n + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    shifts = [(0, 0)] if not full else [(d0, d1) for d0 in (-1, 0, 1) for d1 in (-1, 0, 1)]
    for ax in (1, 2):
        lo = np.take(lab, 0, axis=ax)
        hi = np.take(lab, lab.shape[ax] - 1, axis=ax)
        for d0, d1 in shifts:
            other = np.roll(np.roll(hi, d0, axis=0), d1, axis=1)
            m = (lo > 0) & (other > 0)
            for a, b in set(zip(lo[m].tolist(), other[m].tolist())):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
    roots = np.array([find(i) for i in range(n + 1)])
    uniq = {r: i for i, r in enumerate(sorted(set(roots[1:].tolist())), start=1)}
    remap = np.zeros(n + 1, int)
    for i in range(1, n + 1):
        remap[i] = uniq[roots[i]]
    return remap[lab], len(uniq)


def significant_components(lab, n, total, frac=1e-4):
    sizes = np.bincount(lab.ravel(), minlength=n + 1)[1:]
    keep = [i + 1 for i in np.argsort(-sizes) if sizes[i] > frac * total]
    return keep, sizes


def symmetry_classes(lab, keep):
    """For each kept component: 'invariant' if Rf maps it to itself, else the id of its mirror."""
    rl = reflect(lab)
    out = {}
    for c in keep:
        m = lab == c
        img = rl[m]
        img = img[img > 0]
        if img.size == 0:
            out[c] = None
            continue
        target = int(np.bincount(img).argmax())
        out[c] = 'invariant' if target == c else target
    return out


# ---------------------------------------------------------------------------
# Checks on the fields
# ---------------------------------------------------------------------------

def check_reflection(name, V, cell):
    e = float(np.abs(V - reflect(V)).max())
    report('check 4 %s: reflection' % name, e < 0.01 * cell,
           'max |V_RA - V_RA o Rf| = %.3e vs 0.01 delta = %.3e' % (e, 0.01 * cell))


def check_ordering(name, V_ra, V1, cell, Rg):
    m = Rg >= R_MARGIN
    viol = float(np.max((V1 - V_ra)[m]))
    sub = bool(np.all(~((V_ra <= 0) & (V1 > 0))[m]))
    n_bad = int(np.count_nonzero(((V_ra <= 0) & (V1 > 0))[m]))
    report('check 5 %s: ordering' % name, viol <= 0.01 * cell and sub,
           'max (V_1 - V_RA) = %+.3e vs 0.01 delta = %.3e;  W_1 outside {V_1<=0}: %d nodes'
           % (viol, 0.01 * cell, n_bad))


def check_disjoint(name, W1, W2, D, om):
    a = int(np.count_nonzero(W1 & W2 & om))
    b = int(np.count_nonzero(W1 & D & om))
    report('check 6 %s: disjointness' % name, a == 0 and b == 0,
           'W_1 & W_2: %d nodes, W_1 & D: %d nodes (in Omega)' % (a, b))


def check_horizon(name, diag):
    surf = np.array(diag['surf_motion'])
    report('check 7 %s: horizon' % name, surf[-1] < 5e-3,
           'final 0.25-step moves %.4f%% of {V_RA=0}' % (100 * surf[-1]))


def fine_at_coarse(Vf, Rf, Rc):
    """
    The fine field at the coarse nodes.  The angles nest (fine node 2k is coarse node k).  R is
    subsampled where the rows nest (R_min = 0.2 grids, exactly as M5 scored it) and linearly
    interpolated where they don't (pole grids; claude/Layer1_M5_InnerFace_2026-10-13.md Sec. 8).
    """
    A = Vf[:, ::2, ::2]
    if len(Rf) == 2 * len(Rc) - 1 and np.allclose(Rf[::2], Rc, atol=1e-9):
        return A[::2], 'R subsampled'
    i = np.clip(np.searchsorted(Rf, Rc, side='right') - 1, 0, len(Rf) - 2)
    w = np.clip((Rc - Rf[i]) / (Rf[i + 1] - Rf[i]), 0.0, 1.0)[:, None, None]
    return (1 - w) * A[i] + w * A[i + 1], 'R interpolated'


def check_grid(Vc, Rc, Vf, Rf):
    """M3's metric (grid_study.py), applied to {V_RA <= 0}."""
    if Vf.shape[1] != 2 * Vc.shape[1]:
        raise ValueError('check 8 needs the fine angles to nest: %d vs %d' % (Vf.shape[1], Vc.shape[1]))
    sub, how = fine_at_coarse(Vf, Rf, Rc)
    ok = np.broadcast_to((Rc >= R_MARGIN)[:, None, None], Vc.shape)
    inc, inf_ = (Vc <= 0) & ok, (sub <= 0) & ok
    bc = surface_mask(inc)
    nb = int(bc.sum())
    dis = int(np.count_nonzero(inc != inf_))
    disp = dis / max(nb, 1) * 6
    near = ndimage.binary_dilation(bc, iterations=3)
    off = int(np.count_nonzero((inc != inf_) & ~near))
    report('check 8: grid convergence of dW_1', disp <= 0.5 and off == 0,
           'displacement %.3f coarse cells; %d of %d flips beyond 3 cells (fine field %s)'
           % (disp, off, dis, how))
    return disp, off


def near_intersection_lines(geom, cell, P1, l1, l2, band=2):
    """Nodes within `band` cells of the target-intersection lines at |phi_1| = beta (through beta, delta)."""
    core = (np.abs(l1) <= cell) & (np.abs(l2) <= cell) & \
           (np.abs(np.abs(P1) - E.BETA) <= geom.dphi)
    return ndimage.binary_dilation(core, iterations=band)


def check_topology(name, W1, om, geom, cell, scored=True):
    _, P1, _, l1, l2 = node_ells(geom)
    tot = int(om.sum())
    out = {}
    for full in (False, True):
        lab, n = label_periodic(W1 & om, full)
        keep, sizes = significant_components(lab, n, tot)
        sym = symmetry_classes(lab, keep)
        out['26' if full else '6'] = dict(n=len(keep), sizes=[int(sizes[c - 1]) for c in keep],
                                          sym=[str(sym[c]) for c in keep])
    r6 = out['6']
    inv = sum(s == 'invariant' for s in r6['sym'])
    good = r6['n'] == 3 and inv == 1
    state = good
    msg = '6-conn: %d components %s %s;  26-conn: %d' % (
        r6['n'], r6['sizes'], r6['sym'], out['26']['n'])
    if not good and r6['n'] < 3:
        cut = W1 & om & ~near_intersection_lines(geom, cell, P1, l1, l2)
        lab, n = label_periodic(cut, False)
        keep, sizes = significant_components(lab, n, tot)
        sym = symmetry_classes(lab, keep)
        msg += ';  with nodes near the beta/delta lines removed: %d %s' % (
            len(keep), [str(sym[c]) for c in keep])
        if len(keep) == 3 and sum(sym[c] == 'invariant' for c in keep) == 1:
            state = None
    if scored:
        report('check 9 %s: topology' % name, state, msg)
    else:
        print('  report     check 9 %s: %s' % (name, msg))
    return out


def check_table2(V_ra, geom, cell):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'layer0'))
    from validate_table2 import TABLE2
    pts = {n: (R, a * np.pi / 180, b * np.pi / 180) for n, R, a, b in TABLE2}
    off = ['alpha', 'eps', 'zeta_1', 'rho_1', 'tau', 'E_1', 'F_1', 'H_1', 'S_1', 'U_1', 'a_1', 'b_1']
    on = ['A_1', 'B_1', 'K_1', 'Qt_1', 'h_1']
    rows = []
    miss_off, miss_on = [], []
    for grp, names in (('off', off), ('on', on)):
        for nme in names:
            x = np.array([pts[nme]])
            v = float(SIM.interp(geom, V_ra, x)[0])
            hit = abs(v) <= cell if grp == 'off' else v >= -cell
            rows.append((grp, nme, v, hit))
            if not hit:
                (miss_off if grp == 'off' else miss_on).append(nme)
    for grp, nme, v, hit in rows:
        print('        %-3s %-7s V_RA = %+.4f   %s' % (grp, nme, v, 'ok' if hit else 'MISS'))
    report('check 10: Table 2 points on dW_1', len(miss_off) <= 2 and len(miss_on) <= 1,
           'off-target misses %d/12 %s (allowed 2);  on-target misses %d/5 %s (allowed 1)'
           % (len(miss_off), miss_off, len(miss_on), miss_on))
    return rows


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def fractions(W1, W2, D, C, om, geom):
    Rg, _, _, l1, l2 = node_ells(geom)
    m = Rg >= R_MARGIN
    tot = om.sum()
    return dict(W1=float((W1 & om).sum() / tot), W2=float((W2 & om).sum() / tot),
                D=float((D & om).sum() / tot), C=float(C.sum() / tot),
                T1p=float(((l1 <= 0) & (l2 > 0) & m).sum() / m.sum()),
                T2p=float(((l2 <= 0) & (l1 > 0) & m).sum() / m.sum()),
                T12=float(((l1 <= 0) & (l2 <= 0) & m).sum() / m.sum()),
                omega_nodes=int(tot))


def report_old_vs_new(W1, V1, C, om):
    old = (V1 <= 0) & ~(swap(V1) <= 0) & om
    both = (V1 <= 0) & (swap(V1) <= 0) & om
    new = W1 & om
    tot = om.sum()
    r = dict(old=float(old.sum() / tot), new=float(new.sum() / tot),
             new_minus_old=float((new & ~old).sum() / tot), old_minus_new=float((old & ~new).sum() / tot),
             both_force=float(both.sum() / tot), C=float(C.sum() / tot),
             C_in_both=float((C & both).sum() / max(C.sum(), 1)))
    print('        old {V1<=0}\\{V2<=0}: %.4f%%   new W_1: %.4f%%   new\\old %.4f%%   old\\new %.4f%%'
          % (100 * r['old'], 100 * r['new'], 100 * r['new_minus_old'], 100 * r['old_minus_new']))
    print('        {V1<=0}&{V2<=0}: %.4f%%   contested C: %.4f%%   share of C inside it: %.2f%%'
          % (100 * r['both_force'], 100 * r['C'], 100 * r['C_in_both']))
    return r


def report_diagonal_share(C, geom, coarse_dphi):
    _, P1, P2, _, _ = node_ells(geom)
    d = np.abs(np.abs(P1) - np.abs(P2))
    near = d <= coarse_dphi
    s = float((C & near).sum() / max(C.sum(), 1))
    print('        contested nodes within one coarse cell of |phi_1| = |phi_2|: %.2f%%' % (100 * s))
    return s


def thin_or_fat(v51, v101, v201):
    """Criteria Sec. 4.3."""
    out = dict(v=[v51, v101, v201])
    r = v201 / v101 if v101 > 0 else np.nan
    out['r'] = r
    out['r_class'] = 'thin' if r <= 0.6 else ('fat' if r >= 0.85 else 'inconclusive')
    d1, d2 = v51 - v101, v101 - v201
    fit_ok = False
    if d1 != 0 and d2 != 0 and np.sign(d1) == np.sign(d2):
        p = float(np.log2(d1 / d2))
        c_h = d2 / (2 ** p - 1)            # c * h_201^p
        v0 = v201 - c_h
        fit_ok = 0.25 <= p <= 2.0
        out.update(p=p, v0=v0, ratio=v0 / v201 if v201 else np.nan)
        out['fit_class'] = ('thin' if out['ratio'] <= 0.2 else
                            'fat' if out['ratio'] >= 0.6 else 'inconclusive')
    out['fit_valid'] = fit_ok
    out['decision'] = out['fit_class'] if fit_ok else out['r_class']
    out['rule'] = 'three-grid fit' if fit_ok else 'two-grid ratio fallback'
    return out


# ---------------------------------------------------------------------------
# Simulations (checks 11, 12; C2)
# ---------------------------------------------------------------------------

def pick_starts(V_ra, om, cell, lab_comp, n=2000, per_comp=200, seed=0):
    cand = np.nonzero(((V_ra <= -cell) & om).ravel())[0]
    rng = np.random.default_rng(seed)
    pick = list(rng.choice(cand, size=min(n, cand.size), replace=False))
    lab_flat = lab_comp.ravel()
    for c in np.unique(lab_flat[cand]):
        if c == 0:
            continue
        have = int(np.sum(lab_flat[pick] == c))
        if have < per_comp:
            pool = np.setdiff1d(cand[lab_flat[cand] == c], pick)
            extra = rng.choice(pool, size=min(per_comp - have, pool.size), replace=False)
            pick.extend(extra.tolist())
    return np.array(pick), cand.size


def composite(laws, law_id):
    def law(x, t, ids):
        out = np.empty(len(x))
        lid = law_id[ids]
        for j, f in enumerate(laws):
            m = lid == j
            if m.any():
                out[m] = f(x[m], t, ids[m])
        return out
    return law


P2_NAMES = ['reach-avoid adversary', 'avoid (V_1)', 'trade (t_2*)', 'heuristic', 'random bang-bang']


def player2_laws(stack_ra, stack_v1, t1star, T, n_total):
    return [SIM.law_value_p2(stack_ra, T),
            SIM.law_value_p2_capped(stack_v1, T),
            SIM.law_trade_p2(stack_v1, t1star),
            SIM.law_heuristic(2),
            SIM.law_random(n_total, T, seed=12345)]


def run_guarantee(name, x0, law1, p2laws, T, rollout_kw=None):
    """rollout_kw: extra arguments for sim_m5.rollout (the pole stepper, for pole grids)."""
    n = len(x0)
    k = len(p2laws)
    X = np.repeat(x0, k, axis=0)
    lid = np.tile(np.arange(k), n)
    res = SIM.rollout(X, law1, composite(p2laws, lid), T, **(rollout_kw or {}))
    oc = res['outcome'].reshape(n, k)
    print('        %s: %d starts x %d laws' % (name, n, k))
    for j in range(k):
        print('          %-24s %s' % (P2_NAMES[j], SIM.summarize(oc[:, j])))
    fail_start = np.any(oc != SIM.WIN, axis=1)
    failure_breakdown(x0, oc)
    return oc, fail_start, res


def failure_breakdown(x0, oc, edges=(0.45, 0.8, 1.5, 3.0, 7.0)):
    """Report only: where the failing starts sit in R, and how they failed."""
    bad = np.any(oc != SIM.WIN, axis=1)
    if not bad.any():
        return
    R = x0[:, 0]
    print('          failing starts by start R (failed / all):')
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (R >= lo) & (R < hi)
        if m.any():
            kinds = SIM.summarize(oc[m & bad][oc[m & bad] != SIM.WIN]) if (m & bad).any() else {}
            kinds = {k: v for k, v in kinds.items() if v}
            print('            R in [%.2f, %.2f): %4d / %4d   %s' % (lo, hi, int((m & bad).sum()),
                                                                 int(m.sum()), kinds))


def run_checks_11_12(tag, V_ra, om, cell, geom, geom_sim, snaps_ra, snaps_v1, t1star, T, comp_lab, scored):
    """Starts are nodes of V_ra (geom); laws read the full-grid snapshots and t1star (geom_sim)."""
    stack_ra = SIM.SnapshotStack(geom_sim, snaps_ra)
    stack_v1 = SIM.SnapshotStack(geom_sim, snaps_v1)
    starts, n_cand = pick_starts(V_ra, om, cell, comp_lab)
    x0 = geom.node_states(starts)
    print('        %d candidate starts (V_RA <= -delta in Omega), %d drawn' % (n_cand, len(starts)))
    laws = player2_laws(stack_ra, stack_v1, t1star, T, len(starts) * 5)
    oc, fail, _ = run_guarantee('check 11 (reach-avoid player 1)', x0,
                                SIM.law_value_p1(stack_ra, T), laws, T)
    nf = int(fail.sum())
    oc_h, fail_h, _ = run_guarantee('check 12 (heuristic player 1)', x0, SIM.law_heuristic(1), laws, T)
    nh = int(fail_h.sum())
    if scored:
        report('check 11 %s: W_1 guarantee' % tag, int((oc != SIM.WIN).sum()) == 0,
               '%d failed runs of %d; %d of %d starts failed against some law'
               % (int((oc != SIM.WIN).sum()), oc.size, nf, len(starts)))
        report('check 12 %s: negative control' % tag, nh >= 20,
               '%d of %d starts (%.1f%%) beaten by some law; bar 20'
               % (nh, len(starts), 100 * nh / len(starts)))
    else:
        print('  report     check 11 %s: %d failed runs of %d;  check 12: %d of %d starts beaten'
              % (tag, int((oc != SIM.WIN).sum()), oc.size, nh, len(starts)))
    return dict(starts=starts.tolist(), oc=oc.tolist(), oc_h=oc_h.tolist())


def run_c2(C, geom, geom_sim, snaps_v1, t1star, T, n=1000, seed=3):
    cand = np.nonzero(C.ravel())[0]
    if cand.size == 0:
        print('        contested set is empty; C2 not run')
        return {}
    rng = np.random.default_rng(seed)
    pick = rng.choice(cand, size=min(n, cand.size), replace=False)
    stack = SIM.SnapshotStack(geom_sim, snaps_v1)
    res = SIM.rollout(geom.node_states(pick), SIM.law_trade_p1(stack, t1star),
                      SIM.law_trade_p2(stack, t1star), T)
    s = SIM.summarize(res['outcome'])
    print('        C2 race from %d contested starts (assumption-dependent): %s' % (len(pick), s))
    return s


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def field_stage(T, coarse, fine, third):
    out = {}
    sets = {}
    for name, g in (('coarse', coarse), ('fine', fine), ('third', third)):
        s = load_set(g, T)
        if s is None:
            print('  (no reach-avoid solve for %s yet)' % run_tag(g, T))
            continue
        V_ra, V1, geom, cell, diag = s['V_ra'], s['V1'], s['geom'], s['cell'], s['diag']
        Rg = np.broadcast_to(s['R'][:, None, None], V_ra.shape)
        om = omega(geom)
        header('%s  %s   delta %.4f   V_1 from %s' % (name, s['tag'], cell, s['v1tag'] or '(not solved yet)'))
        scored = name in ('coarse', 'fine')
        W1, C, fr, ovn, dshare = V_ra <= 0, None, None, None, None
        if scored:
            check_reflection(name, V_ra, cell)
        if V1 is not None:
            W1, W2, D, C = partition(V_ra, V1, om)
            if scored:
                check_ordering(name, V_ra, V1, cell, Rg)
                check_disjoint(name, W1, W2, D, om)
        if scored:
            check_horizon(name, diag)
        if V1 is not None:
            fr = fractions(W1, W2, D, C, om, geom)
            print('        over Omega (%d nodes): W_1 %.4f%%  W_2 %.4f%%  D %.4f%%  C %.4f%%'
                  % (fr['omega_nodes'], 100 * fr['W1'], 100 * fr['W2'], 100 * fr['D'], 100 * fr['C']))
            print('        terminal (of R>=0.45): T_1\' %.4f%%  T_2\' %.4f%%  T_1&T_2 %.4f%%'
                  % (100 * fr['T1p'], 100 * fr['T2p'], 100 * fr['T12']))
        else:
            print('        V_1 not solved yet: checks 5 and 6, the partition and the sims wait for it')
        topo = check_topology(name, W1, om, geom, cell, scored=(name == 'fine'))
        if V1 is not None:
            ovn = report_old_vs_new(W1, V1, C, om)
            dshare = report_diagonal_share(C, geom, 2 * np.pi / 102)
        out[name] = dict(tag=s['tag'], v1=s['v1tag'], cell=cell, fractions=fr, topology=topo,
                         old_vs_new=ovn, diag_share=dshare)
        s.update(om=om, C=C, W1=W1)
        sets[name] = s
    if 'coarse' in sets and 'fine' in sets:
        header('Grid convergence (check 8) and thin / fat (Sec. 4.3)')
        out['check8'] = check_grid(sets['coarse']['V_ra'], sets['coarse']['R'],
                                   sets['fine']['V_ra'], sets['fine']['R'])
        if all(n in out and out[n]['fractions'] for n in ('third', 'coarse', 'fine')):
            tf = thin_or_fat(out['third']['fractions']['C'], out['coarse']['fractions']['C'],
                             out['fine']['fractions']['C'])
            out['thin_fat'] = tf
            print('        contested fraction: 51 %.4f%%  101 %.4f%%  201 %.4f%%'
                  % tuple(100 * v for v in tf['v']))
            if 'p' in tf:
                print('        fit v = v0 + c h^p:  p = %.3f  v0 = %.4f%%  v0/v_201 = %.3f  (valid %s) -> %s'
                      % (tf['p'], 100 * tf['v0'], tf['ratio'], tf['fit_valid'], tf.get('fit_class')))
            print('        ratio r = v_201/v_101 = %.3f -> %s' % (tf['r'], tf['r_class']))
            print('        DECISION (%s): %s' % (tf['rule'], tf['decision'].upper()))
        else:
            print('        thin / fat waits for V_1 on all three grids')
    if 'fine' in sets:
        header('Check 10: Table 2 points (fine grid)')
        out['table2'] = [list(r) for r in check_table2(sets['fine']['V_ra'], sets['fine']['geom'],
                                                       sets['fine']['cell'])]
    return out, sets


def sim_stage(T, sets, which):
    out = {}
    for name in which:
        if name not in sets:
            continue
        s = sets[name]
        if s['V1'] is None:
            print('  (checks 11, 12 and C2 on the %s grid wait for its V_1)' % name)
            continue
        header('Checks 11 and 12 on the %s grid (%s)%s' % (name, s['tag'], '' if name == 'fine' else ', report only'))
        snaps_ra = load_snaps(s['snaps_ra'])
        snaps_v1 = load_snaps(s['snaps_v1'])
        print('        V_1 snapshots from %s' % s['snaps_v1'])
        lab, _ = label_periodic(s['W1'] & s['om'], False)
        out[name] = run_checks_11_12(name, s['V_ra'], s['om'], s['cell'], s['geom'], s['geom_sim'],
                                     snaps_ra, snaps_v1, s['t1'], T, lab, scored=(name == 'fine'))
        header('C2 in the contested set, %s grid (report only, assumption-dependent)' % name)
        out[name]['c2'] = run_c2(s['C'], s['geom'], s['geom_sim'], snaps_v1, s['t1'], T)
        del snaps_ra, snaps_v1
    return out


def main():
    T = float(sys.argv[1])
    stages = sys.argv[2:] or ['all']
    coarse = os.environ.get('COARSE', '101x102')
    fine = os.environ.get('FINE', '201x204')
    third = os.environ.get('THIRD', '51x52' if POLE else '51x51')
    print('=' * 96)
    print('M5 acceptance   T_RA = %g   grids %s / %s / %s   ell %s   inner face: %s'
          % (T, third, coarse, fine, E.SCALING, 'pole' if POLE else 'extrapolate at R_min'))
    print('=' * 96)
    out, sets = field_stage(T, coarse, fine, third)
    if 'all' in stages or 'sims' in stages:
        out['sims'] = sim_stage(T, sets, ['fine', 'coarse'])
    out['stages'] = stages
    out['results'] = RESULTS
    out['fails'] = FAILS
    json.dump(out, open('%s/test_m5_T%g%s%s.json' % (OUT, T, SUFFIX, '' if 'all' in stages else '_' + '_'.join(stages)),
                        'w'), indent=1, default=str)
    print('=' * 96)
    print('M5: all scored checks passed' if not FAILS else
          'M5: %d check(s) FAILED: %s' % (len(FAILS), '; '.join(FAILS)))
    print('=' * 96)


if __name__ == '__main__':
    main()
