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

print('\n9. Off-boresight corners: max-range B_1-A_1 and min-range N_1-Z_1-m_1 (Sec. 3.3)')
BC = {s: C.boresight_corner_seeds(s, NSEED) for s in (+1, -1)}
allseeds = [(s, pc, y) for s in BC for pc, ys in BC[s] for y in ys]
fi = max(abs(B.first_integral(y[0], y[3], y[4], y[5]) - 1) for _, _, y in allseeds)
h = max(abs(B.hamiltonian_star(*y)) for _, _, y in allseeds)
check(fi < 1e-12 and h < 1e-12,
      'corner seeds (%d): max |FI-1| %.1e, max |H*| %.1e' % (len(allseeds), fi, h))

# the costate is a NON-NEGATIVE combination of the two outer normals, and it is
# the one lam_corner finds independently (H* = 0, FI = 1 on the normal cone)
res = mu_min = dlc = 0.0
mu_min = np.inf
for s, pc, y in allseeds:
    na = B.n_maxrange(y[2]) if pc.startswith('max') else B.n_minrange(y[2])
    nb = B.n_boresight(y[1])
    M = np.column_stack([na, nb])
    mu = np.linalg.lstsq(M, y[3:], rcond=None)[0]
    res = max(res, np.abs(M @ mu - y[3:]).max())
    mu_min = min(mu_min, mu.min())
    sols = B.lam_corner(y[0], y[1], y[2], na, nb)
    dlc = max(dlc, min(np.abs(sl[0] - y[3:]).max() for sl in sols) if sols else np.inf)
check(res < 1e-12 and mu_min >= 0.0,
      'costates lie in the normal cone: residual %.1e, smallest mu %.1e' % (res, mu_min))
check(dlc < 1e-10, 'costates match lam_corner\'s independent solve to %.1e' % dlc)

# terminal controls, seed by seed
bad_max = bad_min = 0
for s, pc, y in allseeds:
    got = tuple(int(v) for v in B.barrier_controls(*y))
    if pc.startswith('max'):
        bad_max += got != (-s, int(np.sign(y[2])))
    else:
        bad_min += got != (-s, -int(np.sign(np.sin(y[2]))))
check(bad_max == 0,
      'max-range corner pair is (-sgn phi_1, +sgn phi_2) at every seed (%d off) -- '
      'NOT Eq. (70)\'s -sgn(sin phi_2)' % bad_max)
check(bad_min == 0,
      'min-range corner pair is Eqs. (57)-(58), (-sgn phi_1, -sgn sin phi_2) (%d off)' % bad_min)

# Eq. (68) as printed (sign phi_2) is not semipermeable where sgn phi_1 != sgn phi_2
worst_printed = 0.0
for s in (+1, -1):
    p1 = s * B.BETA
    for q in np.linspace(-3.0, 3.0, 61):
        if abs(q) < 1e-3:
            continue
        R = B.R_hi(q); L = np.sin(p1) + np.sin(q)
        mb1 = (1 - np.cos(p1)) * R + L * (1 + np.cos(q)) * np.sign(q)
        mb2 = R - L * np.sign(q)                                   # as printed
        lam = np.array([mb2, mb1 * s, mb2 * (1 + np.cos(q)) * np.sign(q)])
        lam = lam / np.sqrt(B.first_integral(R, *lam))
        worst_printed = max(worst_printed, abs(B.hamiltonian_star(R, p1, q, *lam)))
check(worst_printed > 1e-2,
      'Eq. (68) as printed (sign phi_2) breaks H* = 0 by up to %.2e; corrected (sign phi_1) holds it'
      % worst_printed)

# ends of the min-range corner and the corner vertices, against Table 2
m1, N1 = C.min_corner_ends(+1)
ok = (abs(B.R_lo(m1) - 0.847) < 5e-4 and abs(m1 * D - 8.05) < 1e-2 and
      abs(B.R_lo(N1) - 0.279) < 5e-4 and abs(N1 * D + 154.6) < 5e-2)
check(ok, 'm_1 = (%.4f, %.3f deg), N_1 = (%.4f, %.3f deg); Table 2 (0.847, 8.05), (0.279, -154.6)'
      % (B.R_lo(m1), m1 * D, B.R_lo(N1), N1 * D))

# phi_1 = -beta is the mirror image of phi_1 = +beta, piece for piece
MIRROR = {'max+': 'max-', 'max-': 'max+', 'min+': 'min-', 'min-': 'min+'}
Pp, Pm = dict(BC[+1]), dict(BC[-1])
wm = max(np.abs(np.array(C.mirror(a)) - np.array(b)).max()
         for k in Pp for a, b in zip(Pp[k], Pm[MIRROR[k]]))
check(wm < 1e-12, 'phi_1 = -beta corners are the mirror image of +beta: max diff %.1e' % wm)

# the retrograde path leaves T_1 at once: the barrier grazes the corner from
# outside.  The one exception is the seed at N_1, where the corner meets the
# wall's smooth (BUP) and the first-order separation vanishes.
inside = []
for s, pc, y in allseeds:
    z, sig = y.copy(), B.barrier_controls(*y)
    for _ in range(10):
        z = B._rk4_retro(z, 1e-4, sig)
    if B.in_target(z[1], z[2], z[0]):
        inside.append((s, pc, y[2] * D))
check(all(pc.startswith('min') and abs(abs(q) - abs(N1 * D)) < 0.5 for _, pc, q in inside),
      'retrograde paths start outside T_1 at every corner seed but the one at N_1 (%d inside)'
      % len(inside))

# the two halves of the max-range corner cross retrograde along the evader's
# dispersal line B_1 C_1, through Table 2's C_1 = (4.3, 113.87, -25.27)
def _fl(y, sig, tau, n=None):
    n = n or max(int(abs(tau) / 4e-3), 10)
    for _ in range(n):
        y = B._rk4_retro(y, tau / n, sig)
    return y
def _corner_max(q):
    return np.array([B.R_hi(q), B.BETA, q, *C.lam_corner_max(q, +1)])
qp = 149.49 / D
def _F(v):
    qm, tp, tm = v
    d = (_fl(_corner_max(qp), (-1.0, 1.0), tp) - _fl(_corner_max(qm), (-1.0, -1.0), tm))[:3]
    d[1:] = B.wrap(d[1:])
    return d
x = np.array([-94.24 / D, 2.127, 1.238])
for _ in range(20):
    f = _F(x)
    J = np.column_stack([(_F(x + e) - f) / 1e-7 for e in np.eye(3) * 1e-7])
    dx = np.linalg.solve(J, -f)
    x = x + dx
    if np.abs(dx).max() < 1e-12:
        break
z = _fl(_corner_max(qp), (-1.0, 1.0), x[1])
C1 = np.array([4.3, 113.87, -25.27])
dz = np.array([z[0], z[1] * D, z[2] * D]) - C1
check(abs(dz[0]) < 0.01 and abs(dz[1]) < 0.1 and abs(dz[2]) < 0.1,
      'dispersal line B_1C_1 of the two corner halves passes (%.3f, %.2f, %.2f); Table 2 C_1 (4.3, 113.87, -25.27)'
      % (z[0], z[1] * D, z[2] * D))
# with Eq. (70)'s pairs the halves would diverge from B_1 and could not cross
q0 = 0.05
dp = -B.state_dot(B.R_hi(q0), B.BETA, q0, -1.0, -1.0)[2]      # phi_2 > 0 half, Eq. (70)
dm = -B.state_dot(B.R_hi(-q0), B.BETA, -q0, -1.0, 1.0)[2]     # phi_2 < 0 half, Eq. (70)
check(dp > 0 and dm < 0,
      'with Eq. (70)\'s pairs the halves separate from B_1 (d phi_2/d tau = %+.2f, %+.2f): no B_1C_1'
      % (dp, dm))

# invariants along the corner bundles.  The min-range corner's paths pass close
# to R = 0, so they are flown at dt = 5e-4 (the explorer uses DT/4 for them).
fi = h = 0.0
nsw = 0
for s in BC:
    for pc, ys in BC[s]:
        dt = 5e-4 if pc.startswith('min') else 1e-3
        for y in ys[::3]:
            tr = B.integrate_retrograde(y, tau_max=3.0, dt=dt)
            fi = max(fi, tr['fi_err'].max()); h = max(h, tr['h_err'].max())
            nsw += len(tr['switches'])
check(fi < 1e-7 and h < 1e-7,
      'corner bundles to tau = 3: max |FI-1| %.1e, max |H*| %.1e (%d switches located)'
      % (fi, h, nsw))

js3 = r"""
var C = require('./bup_curves.js');
process.stdout.write(JSON.stringify([1, -1].map(function (s) {
  return C.boresightCornerSeeds(s, %d); })));
""" % NSEED
try:
    raw = subprocess.run(['node', '-e', js3], cwd=HERE, capture_output=True, text=True, timeout=120)
    J = json.loads(raw.stdout)
    w, same = 0.0, True
    for s, jj in zip((+1, -1), J):
        for (pk, ys), jp in zip(BC[s], jj):
            same = same and pk == jp['piece'] and len(ys) == len(jp['seeds'])
            w = max(w, max(np.abs(np.array(a) - np.array(b)).max() for a, b in zip(ys, jp['seeds'])))
    check(same and w < 1e-9, 'bup_curves.js corner seeds reproduce bup_curves.py: max |py - js| = %.2e' % w)
except Exception as e:
    check(False, 'JS corner cross-check failed: %s' % e)

print('\n' + '=' * 78)
print('%d passed, %d failed' % (n_pass, n_fail))
print('=' * 78)
sys.exit(1 if n_fail else 0)
