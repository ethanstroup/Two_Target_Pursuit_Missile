"""
converse_m5.py -- Layer 1, M5 check 13: the converse guarantee.

Pre-registered in claude/Layer1_M5_Criteria_2026-10-11.md Sec. 7 (addendum
2026-10-12) before it ran.

Check 11 showed W_1 is not too big: from inside it player 1 always wins alone.  This
tests that W_1 is not too small: where V_RA > 0, player 2's reach-avoid feedback law
+sign(dV_RA/dphi_2) must stop player 1 winning alone whatever player 1 flies.  The
starts are the states M3's old "win-alone" set claimed and W_1 denies, one cell in
from each edge:
    V_1 <= -delta,   V_2 > 0,   V_RA >= +delta,   in Omega.

Usage:  python3 converse_m5.py [T]
"""

import json
import sys

import numpy as np

import sim_m5 as SIM
import test_m5 as TM

N_STARTS = 2000
BAR_INFORMATIVE = 20
P1_NAMES = ['reach-avoid law', 'single-target law', 'time-optimal law', 'heuristic', 'random bang-bang']


def converse_pool(V_ra, V1, om, cell):
    """Flat node indices of the old set's over-claim, one cell in from its edges."""
    return np.nonzero((om & (V1 <= -cell) & (TM.swap(V1) > 0) & (V_ra >= cell)).ravel())[0]


def draw_starts(pool, n=N_STARTS, seed=0):
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(pool, size=min(n, pool.size), replace=False))


def player1_laws(stack_ra, stack_v1, t1star, T, n_total):
    return [SIM.law_value_p1(stack_ra, T),
            SIM.law_value_p1_capped(stack_v1, T),
            SIM.law_trade_p1(stack_v1, t1star),
            SIM.law_heuristic(1),
            SIM.law_random(n_total, T, seed=777)]


def outcome_table(x0, law1, p2laws, T):
    """Outcome codes, shape (starts, player-2 laws)."""
    n, k = len(x0), len(p2laws)
    X = np.repeat(x0, k, axis=0)
    lid = np.tile(np.arange(k), n)
    res = SIM.rollout(X, law1, TM.composite(p2laws, lid), T)
    return res['outcome'].reshape(n, k)


def print_table(name, oc):
    print('        player 1: %s' % name)
    for j, p2 in enumerate(TM.P2_NAMES):
        s = SIM.summarize(oc[:, j])
        print('          vs %-24s win %5d  p2-kill %5d  mutual %4d  none %4d  exit %4d'
              % (p2, s['win alone'], s['player-2 kill'], s['mutual kill'], s['no kill'],
                 s['exited domain']))


def run_grid(tag, T, scored):
    V_ra, diag = TM.load_ra('%s_T%g' % (tag, T))
    V1, t1, v1tag = TM.load_single(tag, T)
    geom, cell = SIM.Geom(V_ra.shape), diag['cell']
    om = TM.omega(geom)
    pool = converse_pool(V_ra, V1, om, cell)
    starts = draw_starts(pool)
    x0 = geom.node_states(starts)
    TM.header('Check 13 on %s (delta %.4f, V_1 from %s)%s' % (tag, cell, v1tag, '' if scored else ', report only'))
    print('        pool: %d nodes (V_1 <= -delta, V_2 > 0, V_RA >= +delta, in Omega); %d drawn'
          % (pool.size, len(starts)))
    print('        start R: 10th %.2f  median %.2f  90th %.2f'
          % tuple(np.percentile(x0[:, 0], [10, 50, 90])))
    stack_ra = SIM.SnapshotStack(geom, TM.load_snaps('%s/VRAsnap_%s_T%g.npz' % (TM.OUT, tag, T)))
    stack_v1 = SIM.SnapshotStack(geom, TM.load_snaps('%s/Vsnap_%s_T6.npz' % (TM.M3, tag)))
    n_total = len(starts) * len(TM.P2_NAMES)
    p2laws = TM.player2_laws(stack_ra, stack_v1, t1, T, n_total)
    p1laws = player1_laws(stack_ra, stack_v1, t1, T, n_total)
    tables = {}
    for name, law1 in zip(P1_NAMES, p1laws):
        tables[name] = outcome_table(x0, law1, p2laws, T)
        print_table(name, tables[name])
    wins_vs_adv = {n: int(np.sum(tables[n][:, 0] == SIM.WIN)) for n in P1_NAMES}
    informative = int(np.sum(tables['single-target law'][:, 1] == SIM.WIN))
    total_wins = sum(wins_vs_adv.values())
    print('        wins alone against the reach-avoid adversary: %s' % wins_vs_adv)
    print('        informativeness: single-target law vs avoiding player 2 wins alone from %d starts (bar %d)'
          % (informative, BAR_INFORMATIVE))
    if scored:
        state = (True if total_wins == 0 else False) if informative >= BAR_INFORMATIVE else 'UNINF'
        if state == 'UNINF':
            print('  %-10s check 13 %s: converse guarantee   uninformative (%d < %d)'
                  % ('UNINFORMATIVE', tag, informative, BAR_INFORMATIVE))
        else:
            TM.report('check 13 %s: converse guarantee' % tag, state,
                      '%d wins alone in %d runs against the adversary; informativeness %d starts'
                      % (total_wins, len(starts) * len(P1_NAMES), informative))
    return dict(tag=tag, pool=int(pool.size), starts=starts.tolist(), wins_vs_adversary=wins_vs_adv,
                informative=informative,
                tables={n: {p2: SIM.summarize(tables[n][:, j]) for j, p2 in enumerate(TM.P2_NAMES)}
                        for n in P1_NAMES})


def main():
    T = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print('=' * 96)
    print('M5 check 13: the converse guarantee   T_RA = %g' % T)
    print('=' * 96)
    out = {'fine': run_grid('201x204', T, True), 'coarse': run_grid('101x102', T, False)}
    out['results'], out['fails'] = TM.RESULTS, TM.FAILS
    json.dump(out, open('%s/converse_m5_T%g.json' % (TM.OUT, T), 'w'), indent=1)
    print('=' * 96)
    print('check 13: %s' % (TM.RESULTS.get('check 13 201x204: converse guarantee', {}).get('state', 'see above')))
    print('=' * 96)


if __name__ == '__main__':
    main()
