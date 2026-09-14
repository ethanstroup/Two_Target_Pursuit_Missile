"""
test_barrier.py -- integration tests on the retrograde barrier construction.

The two invariants are the test.  A barrier trajectory must carry
    FI = (l1+l2)^2/R^2 + lR^2  ==  1   (Eq. 23)
    H* = min max lambda.f      ==  0   (Eq. 15)
all the way back from the BUP.  H* is the sharper test: it is not automatically
preserved by the costate ODEs, so any error in the control switching shows up
there first.

Usage:  python3 test_barrier.py
"""

import numpy as np
import barrier as B

D = np.pi / 180.0
FAILS = []


def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


def seeds_maxrange(n=40):
    """BUP points on the maximum-range surface, Eq. (32) = 0."""
    out = []
    for p2 in np.linspace(-np.pi + 0.05, np.pi - 0.05, 2 * n + 1):
        if abs(p2) < 0.02:
            continue
        for p1 in B.bup_maxrange(p2):
            R = B.R_hi(p2)
            lR, l1, l2 = B.lam_maxrange(p2)
            out.append(('max-range', np.array([R, p1, p2, lR, l1, l2])))
    return out


def seeds_minrange(n=40):
    """BUP points on the minimum-range surface, Eq. (46) = 0."""
    out = []
    for p2 in np.linspace(-np.pi + 0.05, np.pi - 0.05, 2 * n + 1):
        if abs(np.sin(p2)) < 0.02:
            continue
        for p1 in B.bup_minrange(p2):
            R = B.R_lo(p2)
            lR, l1, l2 = B.lam_minrange(p2)
            out.append(('min-range', np.array([R, p1, p2, lR, l1, l2])))
    return out


def seeds_boresight(n=60):
    """BUP points on the off-boresight limit surfaces, Eq. (62) equality."""
    out = []
    for sgn in (+1, -1):
        p1 = sgn * B.BETA
        for p2 in np.linspace(-np.pi + 0.02, np.pi - 0.02, n):
            R = B.bup_boresight(p2, sgn)
            if R is None:
                continue
            lR, l1, l2 = B.lam_boresight(R, p1, p2)
            out.append(('boresight', np.array([R, p1, p2, lR, l1, l2])))
    return out


print('=' * 90)
print('1.  Terminal costates satisfy the first integral and semipermeability at the BUP')
print('=' * 90)

all_seeds = seeds_maxrange() + seeds_minrange() + seeds_boresight()
print('   %d BUP seeds: %d max-range, %d min-range, %d off-boresight'
      % (len(all_seeds),
         sum(1 for k, _ in all_seeds if k == 'max-range'),
         sum(1 for k, _ in all_seeds if k == 'min-range'),
         sum(1 for k, _ in all_seeds if k == 'boresight')))

for fam in ('max-range', 'min-range', 'boresight'):
    ss = [y for k, y in all_seeds if k == fam]
    fi = np.array([abs(B.first_integral(y[0], y[3], y[4], y[5]) - 1) for y in ss])
    hs = np.array([abs(B.hamiltonian_star(*y)) for y in ss])
    report('%-10s  FI = 1 at the BUP' % fam, fi.max() < 1e-10, 'max |FI-1| = %.2e' % fi.max())
    report('%-10s  H* = 0 at the BUP' % fam, hs.max() < 1e-9, 'max |H*|   = %.2e' % hs.max())

print()
print('=' * 90)
print('2.  Invariants along retrograde barrier trajectories')
print('=' * 90)

for fam in ('max-range', 'min-range', 'boresight'):
    ss = [y for k, y in all_seeds if k == fam]
    fi_max, h_max, lengths = 0.0, 0.0, []
    for y0 in ss:
        tr = B.integrate_retrograde(y0, tau_max=6.0, dt=1e-3)
        fi_max = max(fi_max, tr['fi_err'].max())
        h_max = max(h_max, tr['h_err'].max())
        lengths.append(tr['tau'][-1])
    report('%-10s  FI drift over %d trajectories' % (fam, len(ss)),
           fi_max < 1e-6, 'max |FI-1| = %.2e,  mean retro length %.2f' % (fi_max, np.mean(lengths)))
    report('%-10s  H* drift over %d trajectories' % (fam, len(ss)),
           h_max < 1e-6, 'max |H*|   = %.2e' % h_max)

print()
print('=' * 90)
print('3.  Step-size convergence (RK4 should be 4th order in the invariant drift)')
print('=' * 90)

y0 = [y for k, y in all_seeds if k == 'max-range'][len(seeds_maxrange()) // 2]
prev = None
for dt in (8e-3, 4e-3, 2e-3, 1e-3):
    tr = B.integrate_retrograde(y0, tau_max=3.0, dt=dt)
    e = tr['fi_err'].max()
    rate = '' if prev is None else '  ratio %.1f' % (prev / max(e, 1e-300))
    print('        dt = %.0e   max |FI-1| = %.3e%s' % (dt, e, rate))
    prev = e
report('RK4 convergence order >= 3 in the first integral', prev is not None and prev < 1e-8,
       'finest-step drift %.2e' % prev)

print()
print('=' * 90)
print('4.  Barrier strategies reproduce the paper\'s printed control laws')
print('=' * 90)

# Eq. (33)/(52): on the minimum-range BUP, sigma_1* = sign(sin phi_1).
ss = [y for k, y in all_seeds if k == 'min-range']
ok = True
for y in ss:
    s1, _ = B.barrier_controls(*y)
    if abs(np.sin(y[1])) > 1e-6 and s1 != np.sign(np.sin(y[1])):
        ok = False
        break
report('Eq. (52)  sigma_1* = sign(sin phi_1) on the minimum-range BUP', ok)

# Eq. (45): sigma_2* = -sign(sin phi_2) there too.
ok = all(B.barrier_controls(*y)[1] == -np.sign(np.sin(y[2]))
         for y in ss if abs(np.sin(y[2])) > 1e-6)
report('Eq. (45)  sigma_2* = -sign(sin phi_2) on the minimum-range BUP', ok)

# Eq. (31): sigma_2* = sign(phi_2) on the maximum-range BUP.
ss = [y for k, y in all_seeds if k == 'max-range']
ok = all(B.barrier_controls(*y)[1] == np.sign(y[2]) for y in ss if abs(y[2]) > 1e-6)
report('Eq. (31)  sigma_2* = sign(phi_2) on the maximum-range BUP', ok)

# Eq. (61): sigma_1* = -sign(phi_1) on the off-boresight BUP.
ss = [y for k, y in all_seeds if k == 'boresight']
ok = all(B.barrier_controls(*y)[0] == -np.sign(y[1]) for y in ss)
report('Eq. (61)  sigma_1* = -sign(phi_1) on the off-boresight BUP', ok)

# Eq. (65): sigma_2* = sign(cos phi_2) sign(phi_1) there.
bad = [(y[1] / D, y[2] / D, B.barrier_controls(*y)[1],
        np.sign(np.cos(y[2])) * np.sign(y[1]))
       for y in ss if abs(np.cos(y[2])) > 1e-6
       and B.barrier_controls(*y)[1] != np.sign(np.cos(y[2])) * np.sign(y[1])]
report('Eq. (65)  sigma_2* = sign(cos phi_2) sign(phi_1) on the off-boresight BUP',
       not bad, '' if not bad else '%d of %d disagree, e.g. %s' % (len(bad), len(ss), bad[0]))

# The Eq. (63) discrepancy, demonstrated rather than asserted: seed with the
# printed lambda_1f instead of the derived one and see what breaks.
bad_printed = 0
for y in ss:
    R, p1, p2 = y[0], y[1], y[2]
    l1_printed = (np.sin(p1) + np.sin(p2)) * np.sign(p1)
    yy = np.array([R, p1, p2, 0.0, l1_printed, 0.0])
    s2 = B.barrier_controls(*yy)[1]
    if abs(np.cos(p2)) > 1e-6 and s2 != np.sign(np.cos(p2)) * np.sign(p1):
        bad_printed += 1
print('        seeding instead with Eq. (63) exactly as printed: %d of %d seeds then '
      'contradict Eq. (65)' % (bad_printed, len(ss)))
print('        (all of them at phi_1 = -beta, where the spurious sign(phi_1) flips '
      'the strategy pair)')

print()
print('=' * 90)
print('5.  Corner costates solved from Eqs. (15) + (23) vs. the paper\'s closed forms')
print('=' * 90)

# Maximum-range corner at phi_2 = 0, Eqs. (38)-(41).
worst = 0.0
tested = 0
for p1 in np.linspace(-B.BETA + 0.02, B.BETA - 0.02, 21):
    if abs(p1) < 0.02:
        continue
    R = B.R_hi(0.0)
    sols = B.lam_corner(R, p1, 0.0, np.array([1.0, 0.0, 2.0]), np.array([1.0, 0.0, -2.0]))
    if not sols:
        continue
    q = 1.0 / np.sqrt((np.cos(p1) + 1)**2 + (B.RBAR0 + abs(np.sin(p1)))**2)   # Eq. (41)
    want = np.array([q * (B.RBAR0 + abs(np.sin(p1))),                          # Eq. (39)
                     0.0,
                     q * B.RBAR0 * (np.cos(p1) + 1) * np.sign(p1)])            # Eq. (40)
    # The corner admits more than one lambda satisfying Eqs. (15) and (23) --
    # the two barrier sheets meeting there.  The test is that the paper's
    # closed form is one of them.
    worst = max(worst, min(np.max(np.abs(lam - want)) for lam, _, _ in sols))
    tested += 1
report('Eqs. (39)-(41)  maximum-range corner at phi_2 = 0', worst < 1e-6,
       'max component error %.2e over %d phi_1 values' % (worst, tested))

# Minimum-range / off-boresight corner, Eqs. (53)-(56).
worst = 0.0
tested = 0
for p2 in np.linspace(-np.pi + 0.1, np.pi - 0.1, 41):
    for sp1 in (+1, -1):
        p1 = sp1 * B.BETA
        R = B.R_lo(p2)
        sols = B.lam_corner(R, p1, p2, B.n_minrange(p2), B.n_boresight(p1))
        if not sols:
            continue
        L = np.sin(p1) + np.sin(p2)
        qt = 1.0 / np.sqrt(
            (np.cos(p1) + np.cos(p2) - B.B1 * np.sin(p2) *
             (np.sign(p1) - np.sign(np.sin(p2))))**2
            + (L * np.sign(p1) - B.R_lo(p2))**2)                               # Eq. (56)
        m1 = qt * (-(np.cos(p1) + np.cos(p2)) * B.R_lo(p2)
                   + B.B1 * np.sin(p2) * (L - B.R_lo(p2) * np.sign(np.sin(p2))))  # Eq. (54)
        m2 = qt * (L * np.sign(p1) - B.R_lo(p2))                               # Eq. (55)
        want = np.array([-m2, m1 * np.sign(p1), -m2 * B.B1 * np.sin(p2)])      # Eq. (53)
        if np.linalg.norm(want) < 1e-9:
            continue
        # compare directions, the scale is fixed by the first integral either way
        d = min(min(np.max(np.abs(lam - want)), np.max(np.abs(lam + want)))
                for lam, _, _ in sols)
        worst = max(worst, d)
        tested += 1
report('Eqs. (53)-(56)  minimum-range / off-boresight corner', worst < 5e-3,
       'max component error %.2e over %d corner points' % (worst, tested))

print()
print('=' * 90)
print('%d checks run, %d failed' % (0, len(FAILS)) if not FAILS else
      '%d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS)))
print('=' * 90)
