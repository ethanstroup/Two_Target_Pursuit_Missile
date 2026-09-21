"""
test_viz.py -- acceptance tests for the Layer 0 visualization layer.

The figures and the browser explorer are drawn from two independent
implementations of the same seed curves, bup_curves.py and bup_curves.js. That
is only worth having if they are provably the same object, so the central test
here compares them seed by seed.

The rest is the same standard the reconstruction itself is held to: a seed that
is not semipermeable is not a barrier point, so every seed must satisfy the
first integral and H* to machine precision, and every trajectory must hold them
along its whole retrograde length. Published Table 2 points that lie on these
curves are checked against them.

Run:  python3 layer0/viz/test_viz.py
"""

import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # layer0/
sys.path.insert(0, HERE)

import barrier as B
import bup_curves as C

D = 180.0 / np.pi
FAMILIES = ('max', 'min', 'bore+', 'bore-')
NSEED = 40

n_pass = n_fail = 0


def check(ok, msg):
    global n_pass, n_fail
    if ok:
        n_pass += 1
        print('  PASS  ' + msg)
    else:
        n_fail += 1
        print('  FAIL  ' + msg)


# ---------------------------------------------------------------------------
print('=' * 78)
print('Layer 0 visualization — seed curves, invariants, published points')
print('=' * 78)

PY_SEEDS = {k: C.seeds(k, nseed=NSEED)[0] for k in FAMILIES}

print('\n1. Branch structure')
EXPECTED = {'max': 2, 'min': 2, 'bore+': 1, 'bore-': 1}
for k in FAMILIES:
    check(len(PY_SEEDS[k]) == EXPECTED[k],
          '%-6s %d connected component(s) of the (BUP), expected %d'
          % (k, len(PY_SEEDS[k]), EXPECTED[k]))

# A correctly ordered branch has no jump: consecutive seeds are neighbours.
print('\n2. Seed curves are ordered (no branch-to-branch jumps)')
for k in FAMILIES:
    worst = 0.0
    for br in PY_SEEDS[k]:
        P = np.array([[y[2], y[1]] for y in br])
        # phi_2 is an angle: a branch crossing the +/- pi seam is continuous
        # there, so differences must be wrapped or the seam reads as a jump.
        steps = np.hypot(B.wrap(np.diff(P[:, 0])), B.wrap(np.diff(P[:, 1])))
        if len(steps):
            worst = max(worst, steps.max() / max(np.median(steps), 1e-12))
    check(worst < 4.0,
          '%-6s largest step is %.2fx the median step along the curve' % (k, worst))

print('\n3. Every seed is on the barrier: FI = 1 (Eq. 23) and H* = 0 (Eq. 15)')
for k in FAMILIES:
    fi = h = 0.0
    for br in PY_SEEDS[k]:
        for y in br:
            fi = max(fi, abs(B.first_integral(y[0], y[3], y[4], y[5]) - 1.0))
            h = max(h, abs(B.hamiltonian_star(*y)))
    check(fi < 1e-12 and h < 1e-12,
          '%-6s max |FI-1| = %.2e   max |H*| = %.2e' % (k, fi, h))

print('\n4. Invariants along the retrograde bundle (tau = 3)')
for k in FAMILIES:
    fi = h = 0.0
    nsw = 0
    for br in PY_SEEDS[k]:
        for y in br[::3]:
            tr = B.integrate_retrograde(y, tau_max=3.0, dt=1e-3)
            fi = max(fi, tr['fi_err'].max())
            h = max(h, tr['h_err'].max())
            nsw += len(tr['switches'])
    check(fi < 1e-8 and h < 1e-8,
          '%-6s max |FI-1| = %.2e   max |H*| = %.2e   (%d switches located)'
          % (k, fi, h, nsw))

print('\n5. Published Table 2 points lie on the traced curves')
# (name, family, R, phi_1 deg, phi_2 deg) — Table 2, p. 155
T2 = [('d_1', 'max', 5.8083, 18.88, -9.56),
      ('e_1', 'max', 6.1416, 36.08, 0.00),
      ('g_1', 'min', 0.2665, 45.00, -160.92),
      ('h_1', 'min', 0.5347, 45.00, 92.92),
      ('Q_1', 'bore+', 1.7071, 45.00, 90.00)]
FINE = {k: C.seeds(k, nseed=1200)[0] for k in ('max', 'min', 'bore+')}
for name, fam, R, p1, p2 in T2:
    best = 1e9
    for br in FINE[fam]:
        for y in br:
            d = max(abs(y[0] - R),
                    abs(B.wrap(y[1] - p1 / D)),
                    abs(B.wrap(y[2] - p2 / D)))
            best = min(best, d)
    check(best < 6e-3,
          '%-5s (%s) printed (%.4f, %.2f°, %.2f°) — nearest traced seed within %.1e'
          % (name, fam, R, p1, p2, best))

print('\n6. The maximum-range fold is d_1')
lens = PY_SEEDS['max'][0]
k = int(np.argmax([abs(y[2]) for y in lens]))
check(abs(lens[k][2] * D + 9.56) < 0.02,
      'lens turns at phi_2 = %.4f°, Table 2 d_1 is -9.56°' % (lens[k][2] * D))

print('\n7. bup_curves.js reproduces bup_curves.py')
js = r'''
var C = require('./bup_curves.js');
var out = {};
['max','min','bore+','bore-'].forEach(function (k) {
  out[k] = C.seeds(k, %d).branches;
});
process.stdout.write(JSON.stringify(out));
''' % NSEED
try:
    raw = subprocess.run(['node', '-e', js], cwd=HERE, capture_output=True,
                         text=True, timeout=300)
    if raw.returncode != 0:
        check(False, 'node failed: ' + raw.stderr.strip().splitlines()[-1])
    else:
        JS = json.loads(raw.stdout)
        for k in FAMILIES:
            a, b = PY_SEEDS[k], JS[k]
            if len(a) != len(b):
                check(False, '%-6s branch count %d (py) vs %d (js)' % (k, len(a), len(b)))
                continue
            worst = 0.0
            n = 0
            for ba, bb in zip(a, b):
                if len(ba) != len(bb):
                    worst = np.inf
                    break
                for ya, yb in zip(ba, bb):
                    worst = max(worst, np.max(np.abs(np.array(ya) - np.array(yb))))
                    n += 1
            check(worst < 1e-9,
                  '%-6s %d seeds compared, max |py - js| over the 6-vector = %.2e'
                  % (k, n, worst))
except FileNotFoundError:
    check(False, 'node not found — cannot cross-check the JS twin')

print('\n8. Maximum-range extras: corner edge O-e_1 and the d_1 universal line')
CS = C.corner_seeds(NSEED)
fi = max(abs(B.first_integral(y[0], y[3], y[4], y[5]) - 1) for br in CS for y in br)
h = max(abs(B.hamiltonian_star(*y)) for br in CS for y in br)
check(fi < 1e-12 and h < 1e-12,
      'corner seeds: max |FI-1| %.1e, max |H*| %.1e' % (fi, h))
pairs = [sorted(set(tuple(int(v) for v in B.barrier_controls(*y)) for y in br)) for br in CS]
check(pairs == [[(-1, 1)], [(1, -1)]],
      'corner controls: O-e_1 %s, O-e_1\' %s (mirror images)' % (pairs[0], pairs[1]))
yd = C.d1_seed()
check(abs(yd[0] - 5.808) < 5e-4 and abs(yd[1] * D - 18.88) < 5e-3 and abs(yd[2] * D + 9.56) < 1e-2,
      'd_1 = (%.5f, %.4f, %.4f), Table 2 (5.808, 18.88, -9.56)' % (yd[0], yd[1] * D, yd[2] * D))
UL = C.universal_lines()
l1 = max(np.abs(Y[:, 4]).max() for _, Y in UL)
hu = max(max(abs(B.hamiltonian_star(*y)) for y in Y) for _, Y in UL)
check(l1 < 1e-12 and hu < 1e-12,
      'universal lines hold lambda_1 = 0 (%.1e) and H* = 0 (%.1e) with sigma_1 = 0' % (l1, hu))
end = UL[0][1][-1]
check(np.linalg.norm(end[:3] - [6.14377, 18.4861 / D, -0.0672 / D]) < 1e-4,
      'd_1 line ends at c_1 = (%.5f, %.4f, %.4f), as dispersal_e1c1O.py solves it'
      % (end[0], end[1] * D, end[2] * D))
js2 = r"""
var C = require('./bup_curves.js');
process.stdout.write(JSON.stringify({ corner: C.cornerSeeds(%d), d1: C.d1Seed(),
  tc: C.c1Tau(), ends: C.universalLines().map(function (u) { return u.path[u.path.length - 1].y; }) }));
""" % NSEED
try:
    raw = subprocess.run(['node', '-e', js2], cwd=HERE, capture_output=True, text=True, timeout=120)
    J = json.loads(raw.stdout)
    w = max(np.abs(np.array(a) - np.array(b)).max()
            for ba, bb in zip(CS, J['corner']) for a, b in zip(ba, bb))
    w = max(w, np.abs(np.array(J['d1']) - yd).max(), abs(J['tc'] - C.c1_tau(yd)),
            max(np.abs(np.array(e) - Y[-1]).max() for e, (_, Y) in zip(J['ends'], UL)))
    check(w < 1e-9, 'bup_curves.js extras reproduce bup_curves.py: max |py - js| = %.2e' % w)
except Exception as e:
    check(False, 'JS extras cross-check failed: %s' % e)

print('\n' + '=' * 78)
print('%d passed, %d failed' % (n_pass, n_fail))
print('=' * 78)
sys.exit(1 if n_fail else 0)
