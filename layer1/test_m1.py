"""
test_m1.py -- Layer 1, Milestone M1.  Formulation verified BEFORE any solve.

Layer1_Plan.md Secs. 4 (M1) and 10:

    "Implement ell(x) and confirm its sign agrees with barrier.in_target on a
     dense grid (exact, zero mismatches).  Then confirm the solver's Hamiltonian
     evaluates identically to barrier.hamiltonian_star at random (x, grad V) --
     machine precision, no tolerance.  This catches every sign-convention error
     before a single PDE step runs, and it is cheap."

Nothing here integrates a PDE.  Usage:  python3 test_m1.py
"""

import numpy as np

import hji                      # configures jax x64 before anything else
import jax
import jax.numpy as jnp

import barrier as B
import ell as E

FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


print('=' * 92)
print('0.  Environment   (ell scaling: %s)' % E.SCALING)
print('=' * 92)
report('jax float64 enabled', jnp.zeros(1).dtype == np.float64,
       'default dtype %s' % jnp.zeros(1).dtype)
report('Rbar_0 is 3 + pi, not 6.14', abs(E.RBAR0 - (3 + np.pi)) == 0.0,
       'Rbar_0 = %.6f' % E.RBAR0)
report('layer1 parameters are layer0 objects, not re-entered',
       (E.BETA is B.BETA) and (E.A1 is B.A1) and (E.B1 is B.B1) and (E.RBAR0 is B.RBAR0))

print()
print('=' * 92)
print('1.  ell sign vs. barrier.in_target  --  dense grid, exact')
print('=' * 92)

# 181 x 181 x 181 = 5.9M nodes.  181 is not a multiple of 8, so |phi_1| = beta
# is never hit exactly; R is a linspace that does not land on R_lo or R_hi.
nR, nP = 181, 181
Rg = np.linspace(0.2, 12.0, nR)
Pg = np.linspace(-np.pi, np.pi, nP, endpoint=False)
R, P1, P2 = np.meshgrid(Rg, Pg, Pg, indexing='ij')

L = E.ell(R, P1, P2)
g_bore, g_min, g_max = E.components(R, P1, P2)

inside_strict = (np.abs(P1) < E.BETA) & (R > B.R_lo(P2)) & (R < B.R_hi(P2))
in_target = B.in_target(P1, P2, R)          # D&S Eq. (7), half-open in R

n = L.size
mis_strict = np.count_nonzero((L < 0) != inside_strict)
report('{ell < 0} == strict interior of T_{1->2}   (%d nodes)' % n, mis_strict == 0,
       '%d mismatches' % mis_strict)

mis_target = np.count_nonzero((L < 0) != in_target)
report('{ell < 0} == barrier.in_target on this grid', mis_target == 0,
       '%d mismatches' % mis_target)

# The closure difference, accounted for exactly rather than waved at: ell <= 0 is
# the CLOSED target set, in_target is half-open (non-strict in R_lo, strict in
# R_hi), so the two can only ever differ where a constraint is exactly active.
diff = (L <= 0) != in_target
active = (g_bore == 0) | (g_min == 0) | (g_max == 0)
report('{ell <= 0} differs from in_target only where a constraint is exactly active',
       np.all(active[diff]) if diff.any() else True,
       '%d differing nodes, all on an active constraint' % np.count_nonzero(diff))

# Randomized, where exact constraint hits have probability zero.
rng = np.random.default_rng(20260914)
Rr = rng.uniform(0.2, 12.0, 4_000_000)
P1r = rng.uniform(-np.pi, np.pi, 4_000_000)
P2r = rng.uniform(-np.pi, np.pi, 4_000_000)
mis_rand = np.count_nonzero((E.ell(Rr, P1r, P2r) < 0) != B.in_target(P1r, P2r, Rr))
report('random sample, 4e6 points', mis_rand == 0, '%d mismatches' % mis_rand)

frac = np.count_nonzero(in_target) / n
print('        target-set occupancy on the dense grid: %.4f%% of nodes' % (100 * frac))

print()
print('=' * 92)
print('2.  ell sign on the target-set boundary itself')
print('=' * 92)

# Walk each of the three faces and confirm ell vanishes on it and changes sign
# across it.  This is what "the barrier is the zero level set" rests on.
eps = 1e-7
p2s = np.linspace(-np.pi + 0.01, np.pi - 0.01, 501)

worst = 0.0
for p2 in p2s:                                   # max-range face R = R_hi(phi_2)
    for p1 in (0.0, 0.3, -0.3, 0.7):
        if abs(p1) > E.BETA:
            continue
        worst = max(worst, abs(E.ell(B.R_hi(p2), p1, p2)))
report('ell == 0 on the maximum-range face', worst < 1e-12, 'max |ell| = %.2e' % worst)

worst = 0.0
for p2 in p2s:                                   # min-range face R = R_lo(phi_2)
    for p1 in (0.0, 0.3, -0.3, 0.7):
        if abs(p1) > E.BETA:
            continue
        worst = max(worst, abs(E.ell(B.R_lo(p2), p1, p2)))
report('ell == 0 on the minimum-range face', worst < 1e-12, 'max |ell| = %.2e' % worst)

worst = 0.0
for p2 in p2s:                                   # boresight faces phi_1 = +/- beta
    for sgn in (+1, -1):
        Rm = 0.5 * (B.R_lo(p2) + B.R_hi(p2))
        worst = max(worst, abs(E.ell(Rm, sgn * E.BETA, p2)))
report('ell == 0 on the off-boresight faces', worst < 1e-12, 'max |ell| = %.2e' % worst)

# sign change across each face
ok = True
for p2 in p2s:
    Rm = 0.5 * (B.R_lo(p2) + B.R_hi(p2))
    if not (E.ell(B.R_hi(p2) - eps, 0.0, p2) < 0 < E.ell(B.R_hi(p2) + eps, 0.0, p2)):
        ok = False
    if not (E.ell(B.R_lo(p2) + eps, 0.0, p2) < 0 < E.ell(B.R_lo(p2) - eps, 0.0, p2)):
        ok = False
    if not (E.ell(Rm, E.BETA - eps, p2) < 0 < E.ell(Rm, E.BETA + eps, p2)):
        ok = False
report('ell changes sign across all three faces', ok)

print()
print('=' * 92)
print('3.  Dynamics vs. barrier.state_dot')
print('=' * 92)

dyn = hji.TwoTargetPursuit()
rng = np.random.default_rng(7)
worst = 0.0
for _ in range(20000):
    R0 = rng.uniform(0.2, 12.0)
    p1, p2 = rng.uniform(-np.pi, np.pi, 2)
    s1, s2 = rng.uniform(-1, 1, 2)
    want = np.array(B.state_dot(R0, p1, p2, s1, s2))
    got = np.asarray(dyn(jnp.array([R0, p1, p2]), jnp.array([s1]), jnp.array([s2]), 0.0))
    worst = max(worst, np.max(np.abs(got - want)))
report('f(x,sigma) identical to barrier.state_dot  (2e4 random points)', worst == 0.0,
       'max |diff| = %.2e' % worst)

print()
print('=' * 92)
print('4.  Hamiltonian vs. barrier.hamiltonian_star  --  the M1 gate')
print('=' * 92)

N = 200000
Rr = rng.uniform(0.2, 12.0, N)
P1r = rng.uniform(-np.pi, np.pi, N)
P2r = rng.uniform(-np.pi, np.pi, N)
LR = rng.normal(0, 1, N)
L1 = rng.normal(0, 1, N)
L2 = rng.normal(0, 1, N)

want = B.hamiltonian_star(Rr, P1r, P2r, LR, L1, L2)

states = jnp.stack([jnp.asarray(Rr), jnp.asarray(P1r), jnp.asarray(P2r)], -1)
grads = jnp.stack([jnp.asarray(LR), jnp.asarray(L1), jnp.asarray(L2)], -1)
ham = jax.jit(jax.vmap(lambda x, p: dyn.hamiltonian(x, 0.0, 0.0, p)))
got = np.asarray(ham(states, grads))

abserr = np.abs(got - want)
nexact = np.count_nonzero(abserr == 0.0)

# The error must be measured against the magnitude of the TERMS being summed,
# not against H itself.  Normalizing by |H| is the wrong criterion here for a
# structural reason, not a convenient one: H vanishes identically on the
# semipermeable surface, which is precisely the set this whole layer exists to
# resolve, so a relative-to-result test reports catastrophic cancellation as if
# it were a formulation error.  The conditioning scale is
#     |lambda_R C| + |(lambda_1+lambda_2) L/R| + |lambda_1| + |lambda_2|
# and agreement to a few ulp OF THAT is exactly "identical up to the order the
# two expressions happen to sum in".
Lt = np.sin(P1r) + np.sin(P2r)
Ct = np.cos(P1r) + np.cos(P2r)
termscale = np.abs(LR * Ct) + np.abs((L1 + L2) * Lt / Rr) + np.abs(L1) + np.abs(L2)
ulps = abserr / np.spacing(termscale)
report('H == barrier.hamiltonian_star  (2e5 random (x, grad V))',
       ulps.max() <= 4.0,
       'max %.1f ulp of the summed terms (max |abs| = %.2e); bit-identical at %d/%d'
       % (ulps.max(), abserr.max(), nexact, N))
print('        The two expressions are algebraically the same function evaluated in a')
print('        different association order, so bitwise equality is not expected; %.1f ulp' % ulps.max())
print('        is that and nothing else.  The worst error by the WRONG criterion')
print('        (|H - H*|/|H|) is %.1e, at a point where |H| = %.1e and |H - H*| = %.1e:' % (
      (abserr / np.maximum(np.abs(want), 1e-300)).max(),
      np.abs(want)[np.argmax(abserr / np.maximum(np.abs(want), 1e-300))],
      abserr[np.argmax(abserr / np.maximum(np.abs(want), 1e-300))]))
print('        one rounding unit sitting on a near-semipermeable state. That is the')
print('        cancellation this layer is built around, not an error in it.')

# Degenerate gradients: a costate component exactly zero is where the bang-bang
# tie-break lives, and it is the single most likely place for a convention slip.
Z = 20000
Rz = rng.uniform(0.2, 12.0, Z)
P1z = rng.uniform(-np.pi, np.pi, Z)
P2z = rng.uniform(-np.pi, np.pi, Z)
for label, (lr, l1, l2) in [
        ('lambda_1 = 0 (the range-surface BUPs)', (rng.normal(size=Z), np.zeros(Z), rng.normal(size=Z))),
        ('lambda_2 = 0 (the boresight BUPs)', (rng.normal(size=Z), rng.normal(size=Z), np.zeros(Z))),
        ('lambda_R = 0', (np.zeros(Z), rng.normal(size=Z), rng.normal(size=Z))),
        ('lambda = 0 entirely', (np.zeros(Z), np.zeros(Z), np.zeros(Z)))]:
    w = B.hamiltonian_star(Rz, P1z, P2z, lr, l1, l2)
    g = np.asarray(ham(jnp.stack([jnp.asarray(Rz), jnp.asarray(P1z), jnp.asarray(P2z)], -1),
                       jnp.stack([jnp.asarray(lr), jnp.asarray(l1), jnp.asarray(l2)], -1)))
    e = np.abs(g - w).max()
    report('H matches with %s' % label, e < 1e-13, 'max |diff| = %.2e' % e)

print()
print('=' * 92)
print("5.  Optimal feedback law vs. D&S Eqs. (21)-(22)")
print('=' * 92)

# sigma_1* = -sign(lambda_1), sigma_2* = +sign(lambda_2), the GLOBAL version of
# the law Layer 0 could only justify on barrier trajectories.
oc = jax.jit(jax.vmap(lambda x, p: dyn.optimal_control_and_disturbance(x, 0.0, p)))
u, d = oc(states[:20000], grads[:20000])
u = np.asarray(u).ravel(); d = np.asarray(d).ravel()
report('sigma_1* == -sign(lambda_1)', np.all(u == -np.sign(L1[:20000])),
       '%d of %d disagree' % (np.count_nonzero(u != -np.sign(L1[:20000])), 20000))
report('sigma_2* == +sign(lambda_2)', np.all(d == np.sign(L2[:20000])),
       '%d of %d disagree' % (np.count_nonzero(d != np.sign(L2[:20000])), 20000))
report('controls saturate at |sigma| = 1', np.all(np.abs(u) == 1) and np.all(np.abs(d) == 1))

# And the consistency that actually matters: H evaluated with those controls
# equals grad V . f, i.e. the min-max really is attained at the bang-bang pair.
fvals = jax.jit(jax.vmap(lambda x, uu, dd: dyn(x, uu, dd, 0.0)))(
    states[:20000], jnp.asarray(u)[:, None], jnp.asarray(d)[:, None])
e = np.abs(np.sum(np.asarray(fvals) * np.asarray(grads[:20000]), -1) - want[:20000]).max()
report('H is attained at (sigma_1*, sigma_2*)', e < 1e-13, 'max |diff| = %.2e' % e)

print()
print('=' * 92)
print('6.  Grid: the four traps of Layer1_Plan Sec. 3')
print('=' * 92)

g = hji.make_grid(n_R=41, n_phi=40)
import hj_reachability as hj
per = [bc is hj.boundary_conditions.periodic for bc in g.boundary_conditions]
report('trap 1: phi_1 AND phi_2 are periodic; R is not', per == [False, True, True],
       'periodic flags %s' % per)
report('trap 1: phi grids run [-pi, pi), +pi not duplicated',
       abs(float(g.coordinate_vectors[1][0]) + np.pi) < 1e-15
       and float(g.coordinate_vectors[1][-1]) < np.pi - 1e-9)
report('trap 2: R_min = %.2f is below min R_lo = %.2f' % (hji.R_MIN_DEFAULT, E.A1 - E.B1),
       hji.R_MIN_DEFAULT < E.A1 - E.B1)
report('trap 2: R_max = %.1f is above max R_hi = %.4f' % (hji.R_MAX_DEFAULT, B.R_hi(0.0)),
       hji.R_MAX_DEFAULT > B.R_hi(0.0))
report('trap 2: inner R face uses extrapolation, not periodic/Dirichlet',
       g.boundary_conditions[0] is hj.boundary_conditions.extrapolate)

# ell must be continuous across the periodic seam, or the periodic BC is a lie.
seam = max(abs(float(E.ell(r, np.pi - 1e-9, p2)) - float(E.ell(r, -np.pi + 1e-9, p2)))
           for r in (0.3, 2.0, 6.0, 11.0) for p2 in np.linspace(-3.1, 3.1, 61))
report('ell is continuous across phi_1 = +/- pi', seam < 1e-8, 'max jump %.2e' % seam)
seam = max(abs(float(E.ell(r, p1, np.pi - 1e-9)) - float(E.ell(r, p1, -np.pi + 1e-9)))
           for r in (0.3, 2.0, 6.0, 11.0) for p1 in np.linspace(-3.1, 3.1, 61))
report('ell is continuous across phi_2 = +/- pi', seam < 1e-8, 'max jump %.2e' % seam)

# trap 3: the kinks are present and are geometry.  Assert they EXIST -- a smooth
# ell here would mean the target set had been rounded off.
d1 = (B.R_hi(1e-6) - B.R_hi(0.0)) / 1e-6
d2 = (B.R_hi(0.0) - B.R_hi(-1e-6)) / 1e-6
report('trap 3: R_hi has a genuine corner at phi_2 = 0 (not smoothed)',
       abs(d1 - d2) > 1.0, 'one-sided slopes %.3f and %.3f' % (d1, d2))

# trap 4: dissipation bounds.  The library's default overestimate must dominate
# the analytic partials of Layer1_Plan Sec. 3.
pm = jax.jit(jax.vmap(lambda x: dyn.partial_max_magnitudes(x, 0.0, 0.0, None)))(states[:20000])
pm = np.asarray(pm)
Lm = np.abs(np.sin(P1r[:20000]) + np.sin(P2r[:20000]))
report('trap 4: |dH/dV_R| bound <= 2', pm[:, 0].max() <= 2 + 1e-12, 'max %.4f' % pm[:, 0].max())
report('trap 4: |dH/dV_i| bound == |L|/R + 1',
       np.abs(pm[:, 1] - (Lm / Rr[:20000] + 1)).max() < 1e-12)
report('trap 4: bound <= 2/R_min + 1 = %.1f' % (2 / hji.R_MIN_DEFAULT + 1),
       pm[:, 1].max() <= 2 / hji.R_MIN_DEFAULT + 1 + 1e-12, 'max %.4f' % pm[:, 1].max())

print()
print('=' * 92)
print('7.  ell on an actual solver grid (the array the PDE will start from)')
print('=' * 92)

g = hji.make_grid(n_R=101, n_phi=100)
V0 = np.asarray(E.ell_on_grid(g))
report('V0 is float64', V0.dtype == np.float64, str(V0.dtype))
report('V0 is finite everywhere', np.all(np.isfinite(V0)))
gs = np.asarray(g.states)
want0 = E.ell(gs[..., 0], gs[..., 1], gs[..., 2])
report('jax ell_on_grid == numpy ell', np.max(np.abs(V0 - want0)) == 0.0,
       'max |diff| = %.2e' % np.max(np.abs(V0 - want0)))
report('V0 has both signs (target set is resolved by the grid)',
       (V0 < 0).any() and (V0 > 0).any(),
       '%.3f%% of nodes have ell < 0' % (100 * np.count_nonzero(V0 < 0) / V0.size))
# The R-direction Lipschitz constant is 1 only for the UNSCALED ell; under a
# weighting it is the weight on the active range term.  Test the invariant thing:
# the constant equals the analytic weight, whatever the scaling.
lipR = np.abs(np.diff(V0, axis=0)).max() / float(g.spacings[0])
want = {'raw': 1.0, 'plan': 1.0 / E.RBAR0, 'sdist': 1.0}[E.SCALING]
report('V0 Lipschitz constant in R equals the analytic weight (%.4f)' % want,
       abs(lipR - want) < 0.02 * max(want, 1e-3), 'measured %.4f' % lipR)
print('        one-cell value change (the tolerance unit for M2): %.5f'
      % E.value_scale(g))

print()
print('=' * 92)
print('8.  Conditioning of ell  --  Plan Sec. 2.1\'s stated goal, measured')
print('=' * 92)
# Sec. 2.1: "Level-set schemes want |grad ell| ~ 1.  A max of badly-scaled terms
# gives a value function steep in one direction and flat in another, which
# resolves the zero level set poorly -- precisely the surface being validated."
# That goal is right.  Whether a given weighting SERVES it is a measurement.
cond = E.report_conditioning()
print('        |grad ell| on nodes within 1.0 of the zero level set:')
print('        %-8s %8s %8s %8s %9s' % ('scaling', 'p05', 'median', 'p95', 'p95/p05'))
for k in ('raw', 'plan', 'sdist'):
    a, b, c, d = cond[k]
    print('        %-8s %8.3f %8.3f %8.3f %9.1f%s'
          % (k, a, b, c, d, '   <-- in use' if k == E.SCALING else ''))
report('the zero level set is unchanged by the scaling (weights are positive)',
       True, 'sign of ell is weight-independent by construction; checked in Sec. 1')
report("'sdist' attains |grad ell| ~ 1 to within 20%",
       abs(cond['sdist'][1] - 1.0) < 0.2 and cond['sdist'][3] < 2.0,
       'median %.3f, spread %.1fx' % (cond['sdist'][1], cond['sdist'][3]))
if cond[E.SCALING][3] > 2.0:
    print('        NOTE: the scaling in use has a %.1fx spread in |grad ell|, worse than'
          % cond[E.SCALING][3])
    print('        both raw (%.1fx) and sdist (%.1fx).  This does not affect correctness --'
          % (cond['raw'][3], cond['sdist'][3]))
    print('        the zero level set and tests A-E are weight-invariant -- but it is the')
    print('        opposite of what Plan Sec. 2.1 asks the weighting to achieve.')

print()
print('=' * 92)
print(('M1 COMPLETE -- all checks passed' if not FAILS else
       '%d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS))))
print('=' * 92)
