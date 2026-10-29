"""
c2_longrange.py -- Layer 1, test C2 at long range (the heuristic's inversion).

Pre-registered in Overview/Layer1/Layer1_C2LongRange_2026-10-15.md Sec. 1-5 before it ran.

  LR-1  field: Omega & {R >= 8} lies entirely in D, on both pole grids
  LR-2  player 1 on the avoid law +sign(dV_2/dphi_1) is never killed, against all five player-2 laws
  LR-3  (avoid, avoid): nobody is killed -- Decision 2's model outside the winning zones
  LR-4  negative control: player 1 on the heuristic is killed from >= 20 starts
  LR-5  harness control: heuristic vs heuristic reproduces the Layer 0 simulator's inversion

Usage (from layer1/M5):
    LAYER1_POLE=1 python c2_longrange.py [pole output dir]       default m5_out/m5_out_V1_pole
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))

import ell as E
import sim_m5 as SIM
import test_m5 as TM
import converse_m5 as CV

T = 6.0
R_LONG = 8.0
STARTS_R0 = (8.0, 10.0)
N_GRID = 73
BAR_NEG = 20
LR5_R0 = (2.0, 8.0, 12.0)
LR5_T = 30.0
LR5_SHORT_MIN, LR5_LONG_MAX = 0.80, 0.20
RBAR0 = 3.0 + np.pi


# ---------------------------------------------------------------------------
# Starts and laws
# ---------------------------------------------------------------------------

def start_grid(R0, n=N_GRID):
    """The Layer 0 simulator's acceptance grid: n x n (phi_1, phi_2) in [-pi, pi], endpoints included."""
    p = np.linspace(-np.pi, np.pi, n)
    P1, P2 = np.meshgrid(p, p, indexing='ij')
    return np.stack([np.full(P1.size, R0), P1.ravel(), P2.ravel()], -1)


def law_avoid_p1(stack_v1, T):
    """diag_retreat.py's law: sigma_1 = +sign(dV_2/dphi_1), dV_2/dphi_1 (x) = dV_1/dphi_2 (Sx)."""
    def law(x, t, ids):
        r = min(T - t, stack_v1.taus[-1])
        g = SIM.interp(stack_v1.geom, stack_v1.d2[stack_v1.nearest(r)], SIM.swapped(x))
        return SIM.finite_or_zero(SIM.sign_max(g), g)
    return law


# ---------------------------------------------------------------------------
# LR-1: the field
# ---------------------------------------------------------------------------

def long_range_field(d, grid_tag):
    """Omega & {R >= R_LONG}: W_1 | W_2 node count, nodes outside D, and the margins in delta."""
    def load(kind):
        z = np.load(os.path.join(d, 'm5_%s_T6%s_pole_fields.npz' % (grid_tag, kind)))
        R = z['R']
        i0 = int(np.searchsorted(R, 0.0))
        return z['V'][i0:].astype(float), R[i0:], z['phi1']
    V_ra, R, phi = load('')
    V1, _, _ = load('_single')
    cell = json.load(open(os.path.join(d, 'm5_%s_T6_pole.json' % grid_tag)))['cell']
    Rg, P1, P2 = np.meshgrid(R, phi, phi, indexing='ij')
    om = (Rg >= TM.R_MARGIN) & (E.ell(Rg, P1, P2) > 0) & (E.ell(Rg, P2, P1) > 0)
    m = om & (Rg >= R_LONG)
    W1 = V_ra <= 0
    W = W1 | TM.swap(W1)
    V2 = TM.swap(V1)
    D = (V1 > 0) & (V2 > 0)
    return dict(grid=grid_tag, nodes=int(m.sum()), W=int((W & m).sum()), notD=int((~D & m).sum()),
                minV1=float(V1[m].min() / cell), minV2=float(V2[m].min() / cell))


def score_lr1(rows):
    for r in rows:
        print('        %s: %d nodes in Omega & R >= %g;  W_1 | W_2: %d;  outside D: %d;  '
              'min V_1 = %.1f delta, min V_2 = %.1f delta'
              % (r['grid'], r['nodes'], R_LONG, r['W'], r['notD'], r['minV1'], r['minV2']))
    ok = all(r['W'] == 0 and r['notD'] == 0 and r['nodes'] > 0 for r in rows)
    TM.report('LR-1: long range is all D', ok,
              '; '.join('%s W %d, not D %d' % (r['grid'], r['W'], r['notD']) for r in rows))
    return ok


# ---------------------------------------------------------------------------
# LR-2 .. LR-4: the guarantee runs
# ---------------------------------------------------------------------------

def run_table(x0, law1, p2laws):
    """Outcome codes (starts x player-2 laws) and the smallest R each run reached."""
    n, k = len(x0), len(p2laws)
    X = np.repeat(x0, k, axis=0)
    lid = np.tile(np.arange(k), n)
    res = SIM.rollout(X, law1, TM.composite(p2laws, lid), T)
    return res['outcome'].reshape(n, k), res['r_min'].reshape(n, k)


def print_table(name, oc, rmin, R0s):
    print('        player 1: %s' % name)
    for R0 in sorted(set(R0s.tolist())):
        sel = R0s == R0
        print('          R0 = %g' % R0)
        for j, p2 in enumerate(TM.P2_NAMES):
            s = SIM.summarize(oc[sel, j])
            eng = 100 * np.mean(rmin[sel, j] < RBAR0)
            print('            vs %-24s win %5d  p2-kill %5d  mutual %4d  none %5d  exit %5d   engaged %5.1f%%'
                  % (p2, s['win alone'], s['player-2 kill'], s['mutual kill'], s['no kill'],
                     s['exited domain'], eng))


def killed_p1(oc):
    return (oc == SIM.LOSS) | (oc == SIM.MUTUAL)


def list_failures(x0, oc, mask, limit=40):
    rows = np.argwhere(mask)
    for i, j in rows[:limit]:
        print('            start R=%.0f phi1=%+7.2f phi2=%+7.2f  vs %-24s %s'
              % (x0[i, 0], np.degrees(x0[i, 1]), np.degrees(x0[i, 2]), TM.P2_NAMES[j],
                 SIM.OUTCOME_NAMES[int(oc[i, j])]))
    if len(rows) > limit:
        print('            ... %d more' % (len(rows) - limit))


def score_lr2_lr3(x0, oc):
    bad = killed_p1(oc)
    TM.report('LR-2: avoid guarantee', int(bad.sum()) == 0,
              'player 1 killed in %d of %d runs' % (int(bad.sum()), oc.size))
    if bad.any():
        list_failures(x0, oc, bad)
    j = TM.P2_NAMES.index('avoid (V_1)')
    col = oc[:, j]
    kills = int(np.sum((col == SIM.WIN) | (col == SIM.LOSS) | (col == SIM.MUTUAL)))
    TM.report('LR-3: (avoid, avoid) has no kill', kills == 0,
              '%d kills in %d runs' % (kills, col.size))
    return int(bad.sum()) == 0 and kills == 0


def score_lr4(oc):
    n = int(np.any(killed_p1(oc), axis=1).sum())
    TM.report('LR-4: negative control', n >= BAR_NEG,
              'heuristic player 1 killed by some law from %d of %d starts (bar %d)' % (n, len(oc), BAR_NEG))
    return n >= BAR_NEG


# ---------------------------------------------------------------------------
# LR-5: the inversion, heuristic vs heuristic
# ---------------------------------------------------------------------------

def heuristic_pair(R0):
    """Both players on -sign(phi_i), horizon LR5_T, no outer exit (no field is read)."""
    x0 = start_grid(R0)
    keep = SIM.R_HI_DOM
    SIM.R_HI_DOM = np.inf
    try:
        res = SIM.rollout(x0, SIM.law_heuristic(1), SIM.law_heuristic(2), LR5_T)
    finally:
        SIM.R_HI_DOM = keep
    return x0, res


def angular_agreement(x0, res):
    """Share of decisive, non-terminal outcomes with |phi_1| != |phi_2| won by the smaller |phi|."""
    oc, t = res['outcome'], res['t_end']
    a1, a2 = np.abs(x0[:, 1]), np.abs(x0[:, 2])
    neq = np.abs(a1 - a2) > 1e-9
    dec = ((oc == SIM.WIN) | (oc == SIM.LOSS)) & (t > 0) & neq
    agree = ((oc == SIM.WIN) & (a1 < a2)) | ((oc == SIM.LOSS) & (a2 < a1))
    return float(agree[dec].mean()) if dec.any() else float('nan'), int(dec.sum())


def run_lr5():
    out = {}
    for R0 in LR5_R0:
        x0, res = heuristic_pair(R0)
        oc, t = res['outcome'], res['t_end']
        n = len(oc)
        term = int(np.sum(t == 0))
        live = t > 0
        frac = {k: 100 * float(np.sum((oc == c) & live)) / n for k, c in
                (('p1', SIM.WIN), ('p2', SIM.LOSS), ('mutual', SIM.MUTUAL), ('draw', SIM.NONE))}
        agr, ndec = angular_agreement(x0, res)
        out[R0] = dict(agree=agr, decisive=ndec, terminal=term, **frac)
        print('        R0 = %4g: terminal at t=0 %5.1f%%  P1 %5.1f%%  P2 %5.1f%%  mutual %5.1f%%  draw %5.1f%%;'
              '  smaller |phi| wins %5.1f%% of %d decisive'
              % (R0, 100 * term / n, frac['p1'], frac['p2'], frac['mutual'], frac['draw'], 100 * agr, ndec))
    ok = out[2.0]['agree'] >= LR5_SHORT_MIN and out[8.0]['agree'] <= LR5_LONG_MAX
    TM.report('LR-5: harness reproduces the inversion', ok,
              'smaller |phi| wins %.1f%% at R0 = 2 (bar >= %.0f%%), %.1f%% at R0 = 8 (bar <= %.0f%%)'
              % (100 * out[2.0]['agree'], 100 * LR5_SHORT_MIN, 100 * out[8.0]['agree'], 100 * LR5_LONG_MAX))
    return ok, out


# ---------------------------------------------------------------------------
# Report only: the angular advantage inside W_1
# ---------------------------------------------------------------------------

def angular_share_in_w1(d, grid_tag='201x204', bands=((0.45, 1), (1, 2), (2, 4), (4, 6.2))):
    z = np.load(os.path.join(d, 'm5_%s_T6_pole_fields.npz' % grid_tag))
    R = z['R']
    i0 = int(np.searchsorted(R, 0.0))
    V, R, phi = z['V'][i0:], R[i0:], z['phi1']
    Rg, P1, P2 = np.meshgrid(R, phi, phi, indexing='ij')
    om = (Rg >= TM.R_MARGIN) & (E.ell(Rg, P1, P2) > 0) & (E.ell(Rg, P2, P1) > 0)
    W = (V <= 0) & om
    adv = np.abs(P1) < np.abs(P2) - 1e-12
    parts = []
    for lo, hi in bands:
        b = W & (Rg >= lo) & (Rg < hi)
        parts.append('[%g, %g) %.1f%% of %d' % (lo, hi, 100 * float(adv[b].mean()) if b.any() else float('nan'),
                                                int(b.sum())))
    print('        W_1 & Omega nodes with |phi_1| < |phi_2| (%s): %s' % (grid_tag, ';  '.join(parts)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join('m5_out', 'm5_out_V1_pole')
    if not TM.POLE:
        raise SystemExit('run with LAYER1_POLE=1')
    TM.OUT = d
    print('=' * 104)
    print('Layer 1 test C2 at long range   T = %g   starts R0 = %s, %dx%d   fields %s'
          % (T, STARTS_R0, N_GRID, N_GRID, d))
    print('=' * 104)

    TM.header('LR-1: the partition at R >= %g' % R_LONG)
    lr1 = score_lr1([long_range_field(d, g) for g in ('101x102', '201x204')])

    s = TM.load_set('101x102', T)
    stack_ra = SIM.SnapshotStack(s['geom_sim'], TM.load_snaps(s['snaps_ra']))
    stack_v1 = SIM.SnapshotStack(s['geom_sim'], TM.load_snaps(s['snaps_v1']))
    x0 = np.concatenate([start_grid(R0) for R0 in STARTS_R0])
    R0s = x0[:, 0]
    p2laws = TM.player2_laws(stack_ra, stack_v1, s['t1'], T, len(x0) * len(TM.P2_NAMES))

    TM.header('LR-2, LR-3: player 1 on the avoid law (%s), %d starts x %d laws'
              % (s['tag'], len(x0), len(p2laws)))
    oc2, rm2 = run_table(x0, law_avoid_p1(stack_v1, T), p2laws)
    print_table('avoid +sign(dV_2/dphi_1)', oc2, rm2, R0s)
    lr23 = score_lr2_lr3(x0, oc2)

    TM.header('LR-4: negative control, player 1 on the heuristic')
    oc4, rm4 = run_table(x0, SIM.law_heuristic(1), p2laws)
    print_table('heuristic -sign(phi_1)', oc4, rm4, R0s)
    lr4 = score_lr4(oc4)

    TM.header('LR-5: heuristic vs heuristic, horizon %g, no outer exit' % LR5_T)
    lr5, lr5_out = run_lr5()

    TM.header('Report only: the angular advantage inside W_1')
    angular_share_in_w1(d)

    state = ('PASS' if (lr1 and lr23) else 'FAIL') if (lr4 and lr5) else 'UNINFORMATIVE'
    if not (lr1 and lr23):
        state = 'FAIL'
    print('=' * 104)
    print('Test C2 at long range: %s' % state)
    print('=' * 104)
    json.dump(dict(state=state, results=TM.RESULTS, lr5=lr5_out,
                   lr2=SIM.summarize(oc2.ravel()), lr4=SIM.summarize(oc4.ravel())),
              open(os.path.join(d, 'c2_longrange.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
