"""
test_e_table3.py -- Layer 1, test E against D&S Table 3.

Pre-registered in Overview/Layer1/Layer1_TestE_Table3_2026-10-28.md Sec. 1-5 before it ran.

Every scored Table 3 line is where one player's barrier control is singular or switches, so it
lies on the barrier {V = 0} and on Z_p, the set where V_p = dV/dphi_p changes sign
(p = 1 pursuer, 2 evader).  V is the single-target value (M5's V_1) on the pole grids.

  T3-1  level: the 8 scored Table 2 points have |V| <= delta (at most 1 miss)
  T3-2  locus: the 9 (point, player) pairs are within 2 cells of Z_p & barrier
        (>= 7 hits, and P(hits >= observed) < 0.01 under the null)
  T3-3  the S_1 U_1 commuting line: >= 80 % of its scored samples on the barrier and on Z_1

Usage (from layer1/M4):
    python test_e_table3.py [pole output dir]       default ../M5/m5_out/m5_out_V1_pole
"""

import json
import os
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
for p in (os.path.join(ROOT, 'layer1', 'common'), os.path.join(ROOT, 'layer0', 'common'),
          os.path.join(ROOT, 'layer0', 'singular_lines'), os.path.join(ROOT, 'layer1', 'M5')):
    sys.path.insert(0, p)

import ell as E                      # noqa: E402
import table3 as T3                  # noqa: E402
import validate_table2 as VT         # noqa: E402
import commuting_s1u1 as CL          # noqa: E402

R_MASK = 0.45
OFF_TARGET = 2.0          # points must sit at ell_1 >= OFF_TARGET * delta
RADIUS = 2                # hit radius, Chebyshev, in index units
NULL_R = (0.45, 4.5)
N_LINE = 41
SCORED_KINDS = ('universal', 'dispersal', 'semidispersal', 'switch', 'commuting')
EXCLUDED_ROWS = {('f_1', 'c_1'), ('c_1', 'O_1'), ('M_1', 'n_1'), ('I_1', 'P_1')}   # contradicted or inconsistent
PLAYER_AXIS = {'pursuer': 1, 'evader': 2}
PRE_REGISTERED = {('E_1', 2), ('b_1', 2), ('G_1', 2), ('D_1', 2), ('C_1', 2), ('H_1', 2),
                  ('H_1', 1), ('I_1', 2), ('U_1', 1)}
BARS = dict(level_misses=1, locus_hits=7, locus_p=0.01, line_frac=0.80, null_max=0.5)
DEG = 180.0 / np.pi
RESULTS = {}


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------

def load_field(d, tag):
    """Real rows (R > 0) of a pole fields file: V, R, phi, and the file's full arrays."""
    z = np.load(os.path.join(d, 'm5_%s_fields.npz' % tag))
    R = z['R']
    i0 = int(np.searchsorted(R, 0.0))
    return z['V'][i0:].astype(np.float64), R[i0:], z['phi1'], z['V'].astype(np.float64)


def cell_of(d, tag):
    return json.load(open(os.path.join(d, 'm5_%s.json' % tag)))['cell']


def mesh_ell(R, phi):
    Rg, P1, P2 = np.meshgrid(R, phi, phi, indexing='ij')
    return Rg, E.ell(Rg, P1, P2)


# ---------------------------------------------------------------------------
# The switch locus Z_p and hits
# ---------------------------------------------------------------------------

def central_partial(V, axis, dphi):
    """dV/dphi along a periodic angle axis (1 or 2)."""
    return (np.roll(V, -1, axis) - np.roll(V, 1, axis)) / (2 * dphi)


def sign_change_to_neighbor(s):
    """Nodes whose sign differs from any face neighbor's; angles periodic, R not."""
    out = np.zeros(s.shape, bool)
    out[1:] |= s[1:] != s[:-1]
    out[:-1] |= s[:-1] != s[1:]
    for ax in (1, 2):
        for sh in (1, -1):
            out |= s != np.roll(s, sh, ax)
    return out


def switch_locus(V, p, dphi):
    """Z_p: V_p changes sign to a face neighbor, or the one-sided differences along phi_p disagree."""
    s = np.sign(central_partial(V, p, dphi))
    dm = V - np.roll(V, 1, p)
    dp = np.roll(V, -1, p) - V
    return sign_change_to_neighbor(s) | (dm * dp <= 0)


def dilate(mask, r=RADIUS):
    """Chebyshev dilation by r cells; periodic in the angles, clipped in R."""
    return ndimage.maximum_filter(mask.astype(np.uint8), size=2 * r + 1,
                                  mode=('nearest', 'wrap', 'wrap')).astype(bool)


def nearest_node(R, phi, x):
    dR = R[1] - R[0]
    i = int(np.clip(np.rint((x[0] - R[0]) / dR), 0, len(R) - 1))
    n = len(phi)
    dphi = 2 * np.pi / n
    j = int(np.rint((x[1] + np.pi) / dphi)) % n
    k = int(np.rint((x[2] + np.pi) / dphi)) % n
    return i, j, k


def interp_value(V, R, phi, x):
    """Trilinear value at x (angles periodic, R clamped)."""
    dR = R[1] - R[0]
    n = len(phi)
    dphi = 2 * np.pi / n
    fr = np.clip((x[0] - R[0]) / dR, 0, len(R) - 1 - 1e-9)
    f1 = ((x[1] + np.pi) / dphi) % n
    f2 = ((x[2] + np.pi) / dphi) % n
    i0, j0, k0 = int(fr), int(f1), int(f2)
    wr, w1, w2 = fr - i0, f1 - j0, f2 - k0
    out = 0.0
    for ii, a in ((i0, 1 - wr), (min(i0 + 1, len(R) - 1), wr)):
        for jj, b in ((j0, 1 - w1), ((j0 + 1) % n, w1)):
            for kk, c in ((k0, 1 - w2), ((k0 + 1) % n, w2)):
                out += a * b * c * V[ii, jj, kk]
    return float(out)


def cells_to(ZB, node, rmax=12):
    """Chebyshev distance in cells from node to the nearest ZB node (rmax + 1 if none)."""
    i, j, k = node
    n0, n1, n2 = ZB.shape
    for r in range(rmax + 1):
        ii = np.arange(max(i - r, 0), min(i + r, n0 - 1) + 1)
        jj = np.arange(j - r, j + r + 1) % n1
        kk = np.arange(k - r, k + r + 1) % n2
        if ZB[np.ix_(ii, jj, kk)].any():
            return r
    return rmax + 1


# ---------------------------------------------------------------------------
# What is scored
# ---------------------------------------------------------------------------

def scored_pairs(delta, pts):
    """(point, axis) pairs by the Sec. 2 rule."""
    out = set()
    for a, b, kind, _, player, flag in T3.TABLE3:
        if (a, b) in EXCLUDED_ROWS or kind not in SCORED_KINDS:
            continue
        for n in (a, b):
            R, p1, p2 = pts[n]
            if R >= R_MASK and float(E.ell(np.array(R), np.array(p1), np.array(p2))) >= OFF_TARGET * delta:
                out.add((n, PLAYER_AXIS[player]))
    return out


def s1u1_samples():
    """N_LINE samples, equal in t, of the forward (0,-1) arc from S_1 to its closest approach to U_1."""
    S, U = CL.table2_point('S_1'), CL.table2_point('U_1')
    T, Y = CL.integrate(CL.start_vector(CL.stagnation_state(S[1])), CL.T_FWD, CL.DT)
    i, miss, _ = CL.closest_approach(Y, U)
    idx = np.rint(np.linspace(0, i, N_LINE)).astype(int)
    return Y[idx, :3], float(T[i]), miss


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def poisson_binomial_tail(ps, h):
    """P(X >= h) for X a sum of independent Bernoulli(p_i)."""
    dist = np.zeros(len(ps) + 1)
    dist[0] = 1.0
    for p in ps:
        dist[1:] = dist[1:] * (1 - p) + dist[:-1] * p
        dist[0] *= (1 - p)
    return float(dist[h:].sum())


def null_rate(D, V, Rg, l1, delta):
    m = (np.abs(V) <= delta) & (l1 >= OFF_TARGET * delta) & (Rg >= NULL_R[0]) & (Rg <= NULL_R[1])
    return float(D[m].mean()), int(m.sum())


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(name, state, msg):
    print('  %-14s %s   %s' % (state, name, msg))
    RESULTS[name] = dict(state=state, msg=msg)


def header(s):
    print('-' * 100)
    print(s)
    print('-' * 100)


# ---------------------------------------------------------------------------
# One grid
# ---------------------------------------------------------------------------

def build(d, tag):
    V, R, phi, Vfull = load_field(d, tag)
    delta = cell_of(d, tag)
    dphi = 2 * np.pi / len(phi)
    Rg, l1 = mesh_ell(R, phi)
    B = np.abs(V) <= delta
    Z = {p: switch_locus(V, p, dphi) for p in (1, 2)}
    ZB = {p: Z[p] & B for p in (1, 2)}
    Dl = {p: dilate(ZB[p]) for p in (1, 2)}
    p0 = {p: null_rate(Dl[p], V, Rg, l1, delta) for p in (1, 2)}
    return dict(V=V, R=R, phi=phi, Vfull=Vfull, delta=delta, Rg=Rg, l1=l1, B=B, ZB=ZB, D=Dl, p0=p0)


def run_grid(g, tag, pts, scored, line, scored_run):
    delta = g['delta']
    header('%s   delta %.5f   null p0: pursuer %.3f (%d barrier nodes), evader %.3f'
           % (tag, delta, g['p0'][1][0], g['p0'][1][1], g['p0'][2][0]))
    out = dict(tag=tag, delta=delta, p0={p: g['p0'][p][0] for p in (1, 2)})
    # T3-1
    names = sorted({n for n, _ in scored}, key=lambda n: pts[n][0])
    lv = {n: interp_value(g['V'], g['R'], g['phi'], pts[n]) for n in names}
    for n in names:
        print('        %-5s R=%6.3f phi1=%+7.1f phi2=%+7.1f   V = %+.4f = %+.2f delta  %s'
              % (n, pts[n][0], pts[n][1] * DEG, pts[n][2] * DEG, lv[n], lv[n] / delta,
                 'ok' if abs(lv[n]) <= delta else 'MISS'))
    miss1 = [n for n in names if abs(lv[n]) > delta]
    ok1 = len(miss1) <= BARS['level_misses']
    # T3-2
    pairs = sorted(scored, key=lambda t: (pts[t[0]][0], t[1]))
    hits, ps = [], []
    for n, p in pairs:
        node = nearest_node(g['R'], g['phi'], pts[n])
        h = bool(g['D'][p][node])
        dist = cells_to(g['ZB'][p], node)
        hits.append(h)
        ps.append(g['p0'][p][0])
        print('        %-5s %-8s hit %-5s  nearest Z_%d & barrier node %d cells away'
              % (n, 'pursuer' if p == 1 else 'evader', h, p, dist))
    nh = int(sum(hits))
    tail = poisson_binomial_tail(ps, nh)
    informative2 = all(g['p0'][p][0] <= BARS['null_max'] for _, p in pairs)
    ok2 = nh >= BARS['locus_hits'] and tail < BARS['locus_p']
    # T3-3
    X, sc = line
    vals = np.array([interp_value(g['V'], g['R'], g['phi'], x) for x in X[sc]])
    lh = np.array([bool(g['D'][1][nearest_node(g['R'], g['phi'], x)]) for x in X[sc]])
    on = np.abs(vals) <= delta
    informative3 = g['p0'][1][0] <= BARS['null_max']
    ok3 = on.mean() >= BARS['line_frac'] and lh.mean() >= BARS['line_frac']
    print('        S_1 U_1: %d scored samples;  |V| <= delta at %d (%.0f%%);  hits on Z_1 %d (%.0f%%);'
          '  V from %+.3f to %+.3f'
          % (sc.sum(), on.sum(), 100 * on.mean(), lh.sum(), 100 * lh.mean(), vals.min(), vals.max()))
    if scored_run:
        report('T3-1 level', 'PASS' if ok1 else 'FAIL',
               '%d of %d points off the barrier %s (allowed %d)' % (len(miss1), len(names), miss1, BARS['level_misses']))
        st2 = ('PASS' if ok2 else 'FAIL') if informative2 else 'UNINFORMATIVE'
        report('T3-2 locus', st2, '%d of %d pairs hit; P(>= %d | null) = %.2e (bar %.0e); max p0 %.3f'
               % (nh, len(pairs), nh, tail, BARS['locus_p'], max(ps), ))
        st3 = ('PASS' if ok3 else 'FAIL') if informative3 else 'UNINFORMATIVE'
        report('T3-3 S_1 U_1', st3, 'on the barrier %.0f%%, on Z_1 %.0f%% (bar %.0f%% each); p0 pursuer %.3f'
               % (100 * on.mean(), 100 * lh.mean(), 100 * BARS['line_frac'], g['p0'][1][0]))
    else:
        print('  report     level %d misses %s;  locus %d of %d, tail %.2e;  line %.0f%% / %.0f%%'
              % (len(miss1), miss1, nh, len(pairs), tail, 100 * on.mean(), 100 * lh.mean()))
    out.update(level=lv, hits={'%s/%d' % k: bool(h) for k, h in zip(pairs, hits)}, tail=tail,
               line_on=float(on.mean()), line_hit=float(lh.mean()))
    return out


# ---------------------------------------------------------------------------
# Report only: every row, M4's detector, placed points
# ---------------------------------------------------------------------------

def row_status(row, delta, pts):
    a, b, kind, _, player, flag = row
    if (a, b) in EXCLUDED_ROWS:
        return 'excluded (contradicted or inconsistent)'
    if kind not in SCORED_KINDS:
        return 'kind not scored'
    st = []
    for n in (a, b):
        R, p1, p2 = pts[n]
        l = float(E.ell(np.array(R), np.array(p1), np.array(p2)))
        st.append('below mask' if R < R_MASK else ('on/near target' if l < OFF_TARGET * delta else 'scored'))
    return '%s / %s' % tuple(st)


def every_row(g, pts):
    header('Report only: every Table 3 row on the fine grid')
    for row in T3.TABLE3:
        a, b = row[0], row[1]
        va = interp_value(g['V'], g['R'], g['phi'], pts[a]) if pts[a][0] >= g['R'][0] else float('nan')
        vb = interp_value(g['V'], g['R'], g['phi'], pts[b]) if pts[b][0] >= g['R'][0] else float('nan')
        h = []
        for n in (a, b):
            node = nearest_node(g['R'], g['phi'], pts[n])
            h.append('%d%d' % (int(g['D'][1][node]), int(g['D'][2][node])))
        print('   %-14s %-17s %-7s V %+7.3f %+7.3f   hits(p,e) %s %s   %s'
              % (a + ' ' + b, row[2], row[4][:7], va, vb, h[0], h[1], row_status(row, g['delta'], pts)))


def m4_detector_excess(g, tag, pts, scored):
    """M4's test E detector: WENO5 one-sided sign change along any axis, V minus ell."""
    try:
        import jax.numpy as jnp
        import hj_reachability as hj
        import pole
    except Exception as e:                      # report only; never blocks the scored checks
        print('   (M4 detector skipped: %s)' % e)
        return {}
    n_R = len(g['R'])
    grid = pole.make_grid(n_R, len(g['phi']))

    def locus(Vfull):
        gl, gr = grid.upwind_grad_values(hj.finite_differences.upwind_first.WENO5, jnp.asarray(Vfull))
        gl, gr = np.asarray(gl), np.asarray(gr)
        j = np.zeros(Vfull.shape, bool)
        for d in range(3):
            j |= gl[..., d] * gr[..., d] < 0
        return pole.strip(j)
    kv = locus(g['Vfull'])
    kl = locus(np.asarray(pole.fill(jnp.asarray(E.ell_on_grid(grid)))))
    ex = kv & ~kl & (g['Rg'] >= R_MASK)
    dil = dilate(ex)
    header('Report only: M4\'s detector (WENO5 sign change, V minus ell) near each scored point, %s' % tag)
    print('   excess locus: %.3f%% of nodes at R >= %.2f' % (100 * ex[g['Rg'] >= R_MASK].mean(), R_MASK))
    out = {}
    for n in sorted({n for n, _ in scored}, key=lambda n: pts[n][0]):
        node = nearest_node(g['R'], g['phi'], pts[n])
        out[n] = bool(dil[node])
        print('   %-5s within %d cells of the excess locus: %s' % (n, RADIUS, out[n]))
    return out


def unplaced_table2():
    out = []
    for name, R, d1, d2 in VT.TABLE2:
        res = VT.tests(R, d1 / DEG, d2 / DEG)
        if min(abs(v) for v in res.values()) > 2.5e-3:
            out.append(name)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'M5', 'm5_out', 'm5_out_V1_pole')
    pts = T3.points()
    print('=' * 100)
    print('Layer 1 test E against D&S Table 3   field: single-target V on the pole grids   %s' % d)
    print('=' * 100)
    fine_tag, coarse_tag = '201x204_T6_single_pole', '101x102_T6_single_pole'
    delta_f = cell_of(d, fine_tag)
    scored = scored_pairs(delta_f, pts)
    if scored != PRE_REGISTERED:
        raise SystemExit('scored pairs %s differ from the pre-registered set' % sorted(scored))
    X, t_u, miss = s1u1_samples()
    l1x = E.ell(X[:, 0], X[:, 1], X[:, 2])
    sc_f = l1x >= OFF_TARGET * delta_f
    print('   scored pairs: %s' % ', '.join('%s/%s' % (n, 'p' if p == 1 else 'e') for n, p in sorted(scored)))
    print('   S_1 U_1: %d samples to t = %.3f (miss %.1e at U_1); %d scored on the fine grid'
          % (len(X), t_u, miss, sc_f.sum()))
    out = {}
    gf = build(d, fine_tag)
    out['fine'] = run_grid(gf, fine_tag, pts, scored, (X, sc_f), True)
    every_row(gf, pts)
    out['m4_detector'] = m4_detector_excess(gf, fine_tag, pts, scored)
    unpl = set(unplaced_table2())
    names = {n for n, _ in scored}
    placed = sorted(n for n in names if n in unpl and abs(out['fine']['level'][n]) <= gf['delta']
                    and all(out['fine']['hits']['%s/%d' % (n, p)] for (m, p) in scored if m == n))
    header('Report only: Table 2 points placed by this test (unplaced by validate_table2, level and locus both pass)')
    print('   %s' % (', '.join(placed) if placed else 'none'))
    out['placed'] = placed
    del gf
    delta_c = cell_of(d, coarse_tag)
    sc_c = l1x >= OFF_TARGET * delta_c
    scored_c = scored_pairs(delta_c, pts)
    gc = build(d, coarse_tag)
    out['coarse'] = run_grid(gc, coarse_tag + ' (report only)', pts, scored_c, (X, sc_c), False)
    states = [RESULTS[k]['state'] for k in ('T3-1 level', 'T3-2 locus', 'T3-3 S_1 U_1')]
    verdict = 'PASS' if all(s == 'PASS' for s in states) else (
        'FAIL' if 'FAIL' in states else 'UNINFORMATIVE')
    print('=' * 100)
    print('Test E against Table 3: %s   (%s)' % (verdict, ', '.join(states)))
    print('=' * 100)
    out['verdict'], out['results'] = verdict, RESULTS
    json.dump(out, open(os.path.join(d, 'test_e_table3.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
