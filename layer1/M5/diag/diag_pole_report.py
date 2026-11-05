"""
diag_pole_report.py -- report-only: the M5 numbers the final report quotes that were
measured only on the R_min = 0.2 grids, recomputed on the pole grids of record.

  extents   where the sets sit: the off-boresight zones of W_1, the min-range share of
            W_1, the extent of the contested set C, and the size of its player-1 half
            against the naive "win-alone" set           (was diag_m5_fields / diag_m5_partition)
  harness   the simulator can record a loss: bad player-1 laws from the check-11 pool
            against the reach-avoid adversary and the trading player 2   (was diag_negctl)
  retreat   from the check-13 starts in the player-1 half of C, player 1 flies the
            evader law of the mirror game, +sign(dV_2/dphi_1)            (was diag_retreat)

Nothing here is pre-registered and nothing changes a score.  The laws, seeds, start pools
and sample sizes are the originals', so the numbers compare one for one.

Run from layer1/M5/ (cmd):
    python diag\\diag_pole_report.py all 201x204 > m5_out\\m5_out_V1_pole\\diag_pole_report_201x204.log
    python diag\\diag_pole_report.py extents 101x102 > m5_out\\m5_out_V1_pole\\diag_pole_report_101x102.log
Parts: extents | harness | retreat | all.  Grid tag default 201x204, horizon 6.
Inputs: m5_out/m5_out_V1_pole/ (set M5_POLE_DIR if the pole outputs moved).
"""

import os
import sys
import time

os.environ['LAYER1_POLE'] = '1'          # must be set before sim_m5 / test_m5 are imported

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', '..', 'common'))
sys.path.insert(0, os.path.join(_HERE, '..'))

import sim_m5 as SIM
import test_m5 as TM
import converse_m5 as CV

TM.OUT = os.environ.get('M5_POLE_DIR', os.path.join('m5_out', 'm5_out_V1_pole'))
T_DEFAULT = 6.0


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load(grid_tag, T):
    """The pole fields of record for one grid (R > 0 rows for sets, full grid for rollouts)."""
    s = TM.load_set(grid_tag, T)
    if s is None or s['V1'] is None:
        raise SystemExit('no pole solve for %s at T=%g in %s' % (grid_tag, T, TM.OUT))
    if not s['diag'].get('pole', False):
        raise SystemExit('%s is not a pole run' % s['tag'])
    return s


def stacks(s):
    """Snapshot stacks of V_RA and V_1 on the full pole grid (ghost rows included)."""
    ra = SIM.SnapshotStack(s['geom_sim'], TM.load_snaps(s['snaps_ra']))
    v1 = SIM.SnapshotStack(s['geom_sim'], TM.load_snaps(s['snaps_v1']))
    return ra, v1


# ---------------------------------------------------------------------------
# Extents
# ---------------------------------------------------------------------------

def spread(name, v):
    """min, 5th, median, 95th, max of one coordinate."""
    q = np.percentile(v, [0, 5, 50, 95, 100])
    return '%-8s min %7.2f  5th %7.2f  median %7.2f  95th %7.2f  max %7.2f' % ((name,) + tuple(q))


def describe(mask, Rg, P1, P2):
    """Size and bounding box of one set of nodes, angles in degrees."""
    R, a, b = Rg[mask], np.degrees(P1[mask]), np.degrees(P2[mask])
    return ('n=%7d  R [%.2f, %.2f]  phi1 [%+.0f, %+.0f]  phi2 [%+.0f, %+.0f]  |phi1| [%.0f, %.0f]  |phi2| <= %.0f'
            % (mask.sum(), R.min(), R.max(), a.min(), a.max(), b.min(), b.max(),
               np.abs(a).min(), np.abs(a).max(), np.abs(b).max()))


def components(mask, total):
    """Significant face-connected components (periodic in angle) with their mirror classes."""
    lab, n = TM.label_periodic(mask, False)
    keep, _ = TM.significant_components(lab, n, total)
    return lab, keep, TM.symmetry_classes(lab, keep)


def w1_report(V_ra, om, Rg, P1, P2, l1, l2):
    """Subregions of W_1: as scored on Omega, and with the R mask lifted."""
    W1 = V_ra <= 0
    total = int(om.sum())
    for name, mask in (('Omega (as scored)', W1 & om),
                       ('no R mask, targets excluded', W1 & (l1 > 0) & (l2 > 0))):
        lab, keep, sym = components(mask, total)
        print('W_1 subregions, %s: %d components' % (name, len(keep)))
        for c in keep:
            print('   comp %-4d Rf-> %-9s %s' % (c, sym[c], describe(lab == c, Rg, P1, P2)))
    lab, keep, _ = components(W1 & om, total)
    sizes = sorted((int((lab == c).sum()) for c in keep), reverse=True)
    small = [c for c in keep if (lab == c).sum() < sizes[1]]
    print('min-range share of W_1 & Omega (all but the two smallest components): %.1f%%'
          % (100 * sum(sizes[:-2]) / (W1 & om).sum()))
    for c in small:
        print('   off-boresight zone  %s' % describe(lab == c, Rg, P1, P2))


def contested_report(V_ra, V1, om, Rg, P1, P2):
    """Where C sits, and its player-1 half against the naive win-alone set."""
    W1, _, _, C = TM.partition(V_ra, V1, om)
    V2 = TM.swap(V1)
    half1 = C & (V1 <= 0) & (V2 > 0)
    both = C & (V1 <= 0) & (V2 <= 0)
    naive = (V1 <= 0) & (V2 > 0) & om
    total = om.sum()
    print('C: %d nodes, %.4f%% of Omega;  player-1 half %d;  both can force a kill %d (%.2f%% of C)'
          % (C.sum(), 100 * C.sum() / total, half1.sum(), both.sum(), 100 * both.sum() / C.sum()))
    print('naive set (V_1 <= 0 < V_2): %.4f%% of Omega;  player-1 half of C %.4f%% of Omega = %.1f%% of the naive set'
          % (100 * naive.sum() / total, 100 * half1.sum() / total, 100 * half1.sum() / naive.sum()))
    print('naive set minus W_1 inside C: %.1f%%' % (100 * (naive & ~W1 & C).sum() / max((naive & ~W1).sum(), 1)))
    print('player-1 half of C:')
    print('   ' + spread('R', Rg[half1]))
    print('   ' + spread('|phi1|', np.degrees(np.abs(P1[half1]))))
    print('   ' + spread('|phi2|', np.degrees(np.abs(P2[half1]))))
    lab, keep, sym = components(half1, total)
    print('   %d significant components' % len(keep))
    for c in keep:
        print('   comp %-4d Rf-> %-9s %s' % (c, sym[c], describe(lab == c, Rg, P1, P2)))


def run_extents(s):
    V_ra, V1, geom = s['V_ra'], s['V1'], s['geom']
    Rg, P1, P2, l1, l2 = TM.node_ells(geom)
    om = TM.omega(geom)
    TM.header('EXTENTS  %s   delta %.5f   Omega %d nodes' % (s['tag'], s['cell'], int(om.sum())))
    w1_report(V_ra, om, Rg, P1, P2, l1, l2)
    print()
    contested_report(V_ra, V1, om, Rg, P1, P2)


# ---------------------------------------------------------------------------
# Rollouts
# ---------------------------------------------------------------------------

def outcome_line(name1, name2, res):
    s = SIM.summarize(res['outcome'])
    return ('   P1 %-26s vs %-22s win %4d  lose %4d  mutual %3d  none %4d  exit %4d'
            % (name1, name2, s['win alone'], s['player-2 kill'], s['mutual kill'], s['no kill'],
               s['exited domain']))


def run_harness(s, T, n=400, seed=7):
    """Bad player-1 laws from deep and shallow W_1 starts should lose (diag_negctl's setup)."""
    V_ra, geom, cell = s['V_ra'], s['geom'], s['cell']
    om = TM.omega(geom)
    s_ra, s_v1 = stacks(s)
    rng = np.random.default_rng(seed)
    deep = np.nonzero(((V_ra <= -cell) & om).ravel())[0]
    shallow = np.nonzero(((V_ra > -cell) & (V_ra <= 0) & om).ravel())[0]
    TM.header('HARNESS  %s   %d deep and %d shallow candidate starts' % (s['tag'], deep.size, shallow.size))
    pools = (('deep starts (V_RA <= -delta)', geom.node_states(rng.choice(deep, n, replace=False))),
             ('shallow starts (-delta < V_RA <= 0)',
              geom.node_states(rng.choice(shallow, min(n, shallow.size), replace=False))))
    p2 = {'reach-avoid adversary': SIM.law_value_p2(s_ra, T),
          'trade (t_2*)': SIM.law_trade_p2(s_v1, s['t1'])}
    p1 = {'coast (sigma_1=0)': SIM.law_zero(),
          'turn away (+sign phi_1)': lambda x, t, ids: np.sign(x[:, 1]),
          'random bang-bang': SIM.law_random(n, T, seed=99),
          'heuristic (-sign phi_1)': SIM.law_heuristic(1),
          'reach-avoid (grid law)': SIM.law_value_p1(s_ra, T)}
    for pool, x0 in pools:
        print('%s: %d' % (pool, len(x0)))
        for n1, l1 in p1.items():
            for n2, l2 in p2.items():
                print(outcome_line(n1, n2, SIM.rollout(x0, l1, l2, T)))


def law_retreat_p1(stack_v1, T):
    """sigma_1 = +sign(dV_2/dphi_1), with dV_2/dphi_1 (x) = dV_1/dphi_2 (Sx), capped horizon."""
    def law(x, t, ids):
        r = min(T - t, stack_v1.taus[-1])
        g = SIM.interp(stack_v1.geom, stack_v1.d2[stack_v1.nearest(r)], SIM.swapped(x))
        return SIM.finite_or_zero(SIM.sign_max(g), g)
    return law


def run_retreat(s, T):
    """Player 1 retreats from the check-13 starts against all five player-2 laws (diag_retreat's setup)."""
    V_ra, V1, geom, cell = s['V_ra'], s['V1'], s['geom'], s['cell']
    starts = CV.draw_starts(CV.converse_pool(V_ra, V1, TM.omega(geom), cell))
    x0 = geom.node_states(starts)
    s_ra, s_v1 = stacks(s)
    p2 = TM.player2_laws(s_ra, s_v1, s['t1'], T, len(starts) * len(TM.P2_NAMES))
    TM.header('RETREAT  %s   %d check-13 starts, horizon %g' % (s['tag'], len(starts), T))
    law1 = law_retreat_p1(s_v1, T)
    killed = 0
    for name2, law2 in zip(TM.P2_NAMES, p2):
        res = SIM.rollout(x0, law1, law2, T)
        oc = res['outcome']
        killed += int(np.sum((oc == SIM.LOSS) | (oc == SIM.MUTUAL)))
        print(outcome_line('retreat +sign(dV_2/dphi_1)', name2, res))
        ex, nk = oc == SIM.EXIT, oc == SIM.NONE
        if ex.any():
            print('      exits %d (all through R = 12 on the pole grid): exit time median %.2f'
                  % (ex.sum(), np.median(res['t_end'][ex])))
        if nk.any():
            print('      no-kill runs: final R median %.2f, closest approach median %.2f'
                  % (np.median(res['x_end'][nk, 0]), np.median(res['r_min'][nk])))
    print('player 1 killed (alone or mutual) in %d of %d runs' % (killed, len(starts) * len(p2)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

PARTS = {'extents': lambda s, T: run_extents(s),
         'harness': run_harness,
         'retreat': run_retreat}


def main():
    part = sys.argv[1] if len(sys.argv) > 1 else 'all'
    grid = sys.argv[2] if len(sys.argv) > 2 else '201x204'
    T = float(sys.argv[3]) if len(sys.argv) > 3 else T_DEFAULT
    names = list(PARTS) if part == 'all' else [part]
    if any(n not in PARTS for n in names):
        raise SystemExit('part must be one of: %s, all' % ', '.join(PARTS))
    print('=' * 96)
    print('M5 report numbers on the pole grids   grid %s   T %g   inputs %s' % (grid, T, TM.OUT))
    print('=' * 96)
    s = load(grid, T)
    for n in names:
        t0 = time.time()
        PARTS[n](s, T)
        print('   (%s: %.1f min)' % (n, (time.time() - t0) / 60))


if __name__ == '__main__':
    main()
