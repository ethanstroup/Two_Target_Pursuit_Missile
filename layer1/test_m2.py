"""
test_m2.py -- Layer 1, Milestone M2.  One-player smoke test.

Layer1_Plan.md Sec. 4:

    "Freeze sigma_2 = 0 (non-maneuvering target).  The problem collapses to
     single-player reachability, checkable against direct forward simulation from
     sampled states.  Get this exactly right before turning player 2 on."

The check is TWO-SIDED, which is the point.  With player 2 frozen,

    V(x_0, T) = min_{sigma_1(.)} min_{t in [0,T]} ell(x(t))

so for any admissible control the forward-simulated min_t ell must be

    (a) ACHIEVED    by the value function's own feedback law -- V is not too low;
    (b) NOT BEATEN  by any other control                    -- V is not too high.

(b) is the half that catches a value function that is merely plausible: a solve
with the wrong sign convention, the wrong player minimizing, or a missing
periodic boundary generally produces a V that some dumb control beats.

Usage:  python3 test_m2.py [n_grid] [T]
"""

import sys
import time
import numpy as np

import hji
import jax.numpy as jnp
import barrier as B
import ell as E

N = int(sys.argv[1]) if len(sys.argv) > 1 else 101
T = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
K = 61

FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


print('=' * 92)
print('M2  one-player smoke test:  sigma_2 frozen at 0,  grid %d^3,  horizon T = %.1f' % (N, T))
print('=' * 92)

grid = hji.make_grid(n_R=N, n_phi=N)
V0 = E.ell_on_grid(grid)
taus = np.linspace(0.0, T, K)

t0 = time.time()
Vs = np.asarray(hji.solve_backward(hji.FrozenEvader(), grid, jnp.asarray(-taus), V0))
print('   solve: %.1f s,  %d nodes x %d output times' % (time.time() - t0, np.asarray(V0).size, K))
V = Vs[-1]
dR = float(grid.spacings[0]); dP = float(grid.spacings[1])
# Tolerances are in ELL units, so the unit is the change in ell across one grid
# cell, not dR.  Those coincided only while ell was unscaled.
cell = E.value_scale(grid, V0)
print('   grid spacing: dR = %.4f,  dphi = %.4f' % (dR, dP))
print('   ell scaling: %-6s  one-cell value change: %.5f' % (E.SCALING, cell))

print()
print('-' * 92)
print('1.  Structure of the solution')
print('-' * 92)
report('V is finite everywhere', np.all(np.isfinite(V)))
report('V <= ell everywhere (waiting is always an option)',
       np.all(V <= np.asarray(V0) + 1e-9), 'max V - ell = %.2e' % np.max(V - np.asarray(V0)))
report('V is monotone non-increasing in the horizon',
       np.all(np.diff(Vs, axis=0) <= 1e-9), 'max increase = %.2e' % np.max(np.diff(Vs, axis=0)))
report('the winning zone grows monotonically with the horizon',
       all(np.count_nonzero(Vs[i] <= 0) <= np.count_nonzero(Vs[i + 1] <= 0) for i in range(K - 1)))

print()
print('-' * 92)
print('2.  The reach front travels at the maximum closing speed')
print('-' * 92)
# Against a non-maneuvering target the winning zone is RANGE-LIMITED: its outer
# edge in R can advance no faster than max |Rdot| = max (cos phi_1 + cos phi_2)
# = 2, and with both aircraft nose-on it advances at exactly that.  This is a
# physical check the solver cannot pass by accident, and it is sharper here than
# "has the zero level set stopped moving" -- against a frozen evader it never
# stops, it just runs out of domain.  (Horizon convergence is an M3 question,
# where player 2 maneuvers and the zone is genuinely bounded.)
Rg = np.asarray(grid.coordinate_vectors[0])
edge = np.array([Rg[np.where((v <= 0).any(axis=(1, 2)))[0].max()] for v in Vs])
unsat = edge < Rg[-1] - 2 * dR
if unsat.sum() >= 5:
    sp = np.polyfit(taus[unsat], edge[unsat], 1)[0]
else:
    sp = np.nan
print('        outer edge of {V<=0}:  tau=0  R=%.2f  ->  tau=%.1f  R=%.2f' % (edge[0], T, edge[-1]))
report('front speed == max closing speed 2', abs(sp - 2.0) < 0.10, 'measured %.3f' % sp)
report('front never exceeds the max closing speed',
       np.all(np.diff(edge) <= 2.0 * (taus[1] - taus[0]) + 1.01 * dR))

print()
print('-' * 92)
print('3.  (a) the value function\'s own feedback law ACHIEVES V')
print('-' * 92)
policy = hji.make_policy(grid, Vs, taus, freeze_p2=True)
V_at = hji.make_interp(grid, jnp.asarray(V))

rng = np.random.default_rng(31415)
samples = []
while len(samples) < 240:
    R0 = rng.uniform(1.0, 8.0)
    p1, p2 = rng.uniform(-np.pi, np.pi, 2)
    if E.ell(R0, p1, p2) <= 0:
        continue
    samples.append(np.array([R0, p1, p2]))

gap, vv, mm = [], [], []
for x0 in samples:
    tr = hji.forward_sim(x0, policy, T, dt=4e-3)
    if tr['exited']:
        continue
    v = float(V_at(x0))
    gap.append(tr['min_ell'] - v); vv.append(v); mm.append(tr['min_ell'])
gap = np.array(gap); vv = np.array(vv); mm = np.array(mm)
print('        %d of %d sampled trajectories stayed inside the R domain' % (len(gap), len(samples)))
report('feedback law achieves V  (min_t ell - V within a grid cell)',
       np.median(np.abs(gap)) < 0.1 * cell and np.percentile(np.abs(gap), 90) < cell
       and np.abs(gap).max() < 3 * cell,
       'median %+.5f, 90th pct %+.5f, max %+.5f  (one cell = %.5f)'
       % (np.median(gap), np.percentile(np.abs(gap), 90), np.abs(gap).max(), cell))
nd = np.count_nonzero((vv <= 0) != (mm <= 0))
report('sign of V agrees with the simulated outcome', nd / len(vv) < 0.02,
       '%d of %d disagree' % (nd, len(vv)))

# The finite-horizon read, stated as a test rather than a comment.  Reading the
# TERMINAL-horizon V throughout is the natural mistake and it is a large one.
stale = hji.make_static_policy(grid, V, freeze_p2=True)
gap_stale = []
for x0 in samples:
    tr = hji.forward_sim(x0, stale, T, dt=4e-3)
    if not tr['exited']:
        gap_stale.append(tr['min_ell'] - float(V_at(x0)))
gap_stale = np.array(gap_stale)
report('reading V(.,T) instead of V(.,T-t) is measurably WORSE (control, not V)',
       gap_stale.max() > 5 * np.abs(gap).max(),
       'stale max shortfall %+.4f vs correct %+.4f' % (gap_stale.max(), np.abs(gap).max()))
print('        Same V, same grid, same trajectories -- only the horizon at which')
print('        grad V is read changed.  The value function is not at fault here, and')
print('        an acceptance suite that only tested the stale read would blame it.')

print()
print('-' * 92)
print('4.  (b) NO other control beats V  --  the sharp half')
print('-' * 92)


def const(c):
    return lambda x, t: (c, 0.0)


def heuristic(x, t):
    return -float(np.sign(x[1])), 0.0


def randbang(seed):
    r = np.random.default_rng(seed)
    st = {'s': 1.0, 'next': 0.0}
    def f(x, t):
        if t >= st['next']:
            st['s'] = float(r.choice([-1.0, 1.0]))
            st['next'] = t + float(r.uniform(0.05, 0.8))
        return st['s'], 0.0
    return f


def single_switch(s0, tsw):
    return lambda x, t: ((s0 if t < tsw else -s0), 0.0)


alts = [('sigma_1 = +1', const(1.0)), ('sigma_1 = -1', const(-1.0)), ('sigma_1 = 0', const(0.0)),
        ('pursuit heuristic -sign(phi_1)', heuristic)]
alts += [('random bang-bang #%d' % i, randbang(100 + i)) for i in range(3)]

worst_overall, worst_name = -1e9, ''
for name, law in alts:
    v = []
    for x0 in samples[:120]:
        tr = hji.forward_sim(x0, law, T, dt=4e-3)
        if not tr['exited']:
            v.append(float(V_at(x0)) - tr['min_ell'])       # > 0 means it BEAT V
    v = np.array(v)
    if v.max() > worst_overall:
        worst_overall, worst_name = v.max(), name
    report('%-32s does not beat V' % name, v.max() < cell,
           'worst V - min_t ell = %+.4f over %d trajectories' % (v.max(), len(v)))

# A brute-force sweep over single-switch bang-bang controls: a much stronger
# adversary than any fixed law, and the one that would expose a V that is too low.
bf = []
for x0 in samples[:40]:
    best = np.inf
    for s0 in (-1.0, 1.0):
        for tsw in np.linspace(0.0, T, 21):
            tr = hji.forward_sim(x0, single_switch(s0, tsw), T, dt=8e-3)
            if not tr['exited']:
                best = min(best, tr['min_ell'])
    if np.isfinite(best):
        bf.append(float(V_at(x0)) - best)
bf = np.array(bf)
if bf.max() > worst_overall:
    worst_overall, worst_name = bf.max(), 'brute-force single-switch sweep'
report('brute-force single-switch sweep (42 controls x 40 states) does not beat V',
       bf.max() < cell, 'worst V - min_t ell = %+.4f' % bf.max())

report('OPTIMALITY: nothing tested beats V by as much as one grid cell',
       worst_overall < cell, 'worst %+.5f by "%s"  (one cell = %.5f)'
       % (worst_overall, worst_name, cell))

print()
print('-' * 92)
print('5.  Player 2 really is frozen (contrast against the two-player solve)')
print('-' * 92)
del policy, stale
V2s = np.asarray(hji.solve_backward(hji.TwoTargetPursuit(), grid, jnp.asarray(-taus), V0))
V2 = V2s[-1]
report('V(frozen sigma_2) <= V(maneuvering sigma_2) everywhere',
       np.all(V <= V2 + 2 * cell), 'max V_frozen - V_2player = %.5f' % np.max(V - V2))
e2 = np.array([Rg[np.where((v <= 0).any(axis=(1, 2)))[0].max()] for v in V2s])
print('        {V<=0} share at T:  frozen evader %.2f%%,  maneuvering evader %.2f%%'
      % (100 * np.count_nonzero(V <= 0) / V.size, 100 * np.count_nonzero(V2 <= 0) / V2.size))
print('        outer edge in R at T:  frozen %.2f (still advancing),  maneuvering %.2f'
      % (edge[-1], e2[-1]))
report('a maneuvering evader keeps the winning zone bounded in R',
       e2[-1] < B.R_hi(0.0) + 2 * dR,   # an R bound, so dR is the right unit here
       'edge %.2f vs R_hi(0) = %.4f' % (e2[-1], B.R_hi(0.0)))
print('        (This is D&S\'s bounded winning zone appearing on its own, and it is')
print('        the reason horizon convergence is an M3 test and not an M2 one.)')

np.save('V_m2_frozen_n%d_T%g_%s.npy' % (N, T, E.SCALING), V)

print()
print('=' * 92)
print(('M2 COMPLETE -- all checks passed' if not FAILS else
       '%d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS))))
print('=' * 92)
