"""
verify_symbolic.py -- symbolic re-derivation of every Davidovitz & Shinar (1989)
equation that the Layer 0 barrier reconstruction depends on.

Davidovitz, A., and Shinar, J., "Two-Target Game Model of an Air Combat with
Fire-and-Forget All-Aspect Missiles", JOTA 63(2), Nov. 1989, pp. 133-165.

Standard (ProblemStatement.md Sec. 9): re-derive, do not transcribe.  Every check
below is either an exact symbolic identity or a randomized numerical check over
admissible states.  Failures are reported, not silently tolerated.
"""

import sympy as sp
import numpy as np

R, ph1, ph2, s1, s2 = sp.symbols('R phi_1 phi_2 sigma_1 sigma_2', real=True)
lR, l1, l2 = sp.symbols('lambda_R lambda_1 lambda_2', real=True)
a1, b1, Rbar0 = sp.symbols('a_1 b_1 Rbar_0', positive=True)

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + detail) if detail else ''))


print('=' * 78)
print('A.  Dynamics, costates, first integral')
print('=' * 78)

L = sp.sin(ph1) + sp.sin(ph2)          # line-of-sight numerator, Eq. (5)
C = sp.cos(ph1) + sp.cos(ph2)

Rdot = -C                               # Eq. (1)
ph1dot = L / R + s1                     # Eq. (2)
ph2dot = L / R + s2                     # Eq. (3)

lRdot = L * (l1 + l2) / R**2                       # Eq. (17)
l1dot = -(lR * sp.sin(ph1) + sp.cos(ph1) * (l1 + l2) / R)   # Eq. (18)
l2dot = -(lR * sp.sin(ph2) + sp.cos(ph2) * (l1 + l2) / R)   # Eq. (19)

# --- Eqs. (17)-(19) are the costate equations of H = lambda . f.  Re-derive
# them from H rather than trusting the print.
H = lR * Rdot + l1 * ph1dot + l2 * ph2dot
check('Eq. (17)  lambda_R-dot = -dH/dR',
      sp.simplify(-sp.diff(H, R) - lRdot) == 0)
check('Eq. (18)  lambda_1-dot = -dH/dphi_1',
      sp.simplify(-sp.diff(H, ph1) - l1dot) == 0)
check('Eq. (19)  lambda_2-dot = -dH/dphi_2',
      sp.simplify(-sp.diff(H, ph2) - l2dot) == 0)

# --- Eq. (23): first integral (lambda_1+lambda_2)^2/R^2 + lambda_R^2 = C.
# Must be conserved for ANY sigma_1, sigma_2 (the controls cancel identically).
FI = (l1 + l2)**2 / R**2 + lR**2
dFI = (sp.diff(FI, R) * Rdot + sp.diff(FI, ph1) * ph1dot + sp.diff(FI, ph2) * ph2dot
       + sp.diff(FI, lR) * lRdot + sp.diff(FI, l1) * l1dot + sp.diff(FI, l2) * l2dot)
check('Eq. (23)  first integral conserved, control-independent',
      sp.simplify(dFI) == 0)

print()
print('=' * 78)
print('B.  Target set, Eqs. (6)-(9)')
print('=' * 78)

Rlo = a1 + b1 * sp.cos(ph2)                              # Eq. (8),  R_under_1(phi_2)
Rhi = Rbar0 - sp.Abs(ph2 + sp.sin(ph2))                  # Eq. (9),  R_bar_1(phi_2)

# On (-pi, pi), phi + sin(phi) carries the sign of phi, so |.| differentiates to
# (1+cos phi) sign(phi).
dRhi = -(1 + sp.cos(ph2)) * sp.sign(ph2)
check('Eq. (29)  dRbar_1/dphi_2 = -(1+cos phi_2) sign(phi_2)',
      all(abs(float(sp.diff(Rhi, ph2).subs(ph2, v)) - float(dRhi.subs(ph2, v))) < 1e-12
          for v in (-3.0, -1.2, -0.3, 0.3, 1.2, 3.0)))

dRlo = -b1 * sp.sin(ph2)
check('Eq. (44)  dRunder_1/dphi_2 = -b_1 sin(phi_2)',
      sp.simplify(sp.diff(Rlo, ph2) - dRlo) == 0)

print()
print('=' * 78)
print('C.  Usable parts:  min_{sigma_i} max_{sigma_j} n . xdot < 0,  Eq. (13)')
print('=' * 78)

# --- C1.  Maximum-range surface  R = Rbar_1(phi_2).  Eqs. (28)-(32).
# Outer normal, Eq. (28): (1, 0, -dRbar_1/dphi_2).
nR = sp.Matrix([1, 0, -dRhi])
f = sp.Matrix([Rdot, ph1dot, ph2dot])
expr = (nR.T * f)[0]
expr_on = expr.subs(R, Rhi)
# n has no phi_1 component => sigma_1 absent; maximize over sigma_2.
coeff_s2 = sp.simplify(sp.diff(expr_on, s2))
check('Eq. (31)  sigma_2* = sign(phi_2)   [coefficient of sigma_2 is (1+cos phi_2) sign phi_2]',
      sp.simplify(coeff_s2 - (1 + sp.cos(ph2)) * sp.sign(ph2)) == 0)

# Eq. (32):  Rbar(phi_2)[1-cos phi_1] < -(sin phi_1 + sin phi_2)(1+cos phi_2) sign phi_2
# sympy will not reduce sign(x)**2 -> 1 nor open |phi_2 + sin phi_2|, so this
# identity is checked numerically on a grid over the admissible (phi_1, phi_2).
lhs32 = Rhi * (1 - sp.cos(ph1))
rhs32 = -L * (1 + sp.cos(ph2)) * sp.sign(ph2)
_f_max = sp.lambdify((ph1, ph2, s2),
                     expr_on.subs({Rbar0: 3 + sp.pi}), 'numpy')
_f_32 = sp.lambdify((ph1, ph2),
                    (lhs32 - rhs32).subs({Rbar0: 3 + sp.pi}), 'numpy')
_f_Rhi = sp.lambdify(ph2, Rhi.subs({Rbar0: 3 + sp.pi}), 'numpy')
_rng = np.random.default_rng(0)
_p1 = _rng.uniform(-np.pi, np.pi, 4000)
_p2 = _rng.uniform(-np.pi, np.pi, 4000)
_p2 = _p2[np.abs(_p2) > 1e-6]
_p1 = _p1[:len(_p2)]
_lhs = _f_max(_p1, _p2, np.sign(_p2)) * _f_Rhi(_p2)
_rhs = _f_32(_p1, _p2)
check('Eq. (32)  UP condition equivalent to max_{sigma_2} n.xdot < 0',
      np.max(np.abs(_lhs - _rhs)) < 1e-10,
      '[max residual %.2e over 4000 random states]' % np.max(np.abs(_lhs - _rhs)))

# --- C2.  Minimum-range surface  R = Runder_1(phi_2).  Eqs. (43)-(46).
nr = sp.Matrix([-1, 0, dRlo])
expr = (nr.T * f)[0].subs(R, Rlo)
coeff_s2 = sp.simplify(sp.diff(expr, s2))
check('Eq. (45)  sigma_2* = -sign(sin phi_2)   [coefficient of sigma_2 is -b_1 sin phi_2]',
      sp.simplify(coeff_s2 - (-b1 * sp.sin(ph2))) == 0)
maxval = sp.simplify(expr.subs({s2: -sp.sign(sp.sin(ph2))}))
lhs46 = Rlo * (sp.cos(ph1) + sp.cos(ph2) + b1 * sp.Abs(sp.sin(ph2)))
rhs46 = b1 * sp.sin(ph2) * L
check('Eq. (46)  UP condition equivalent to max_{sigma_2} n.xdot < 0',
      sp.simplify(maxval * Rlo - (lhs46 - rhs46)) == 0)

# --- C3.  Off-boresight limit surfaces  phi_1 = +/- beta.  Eqs. (59)-(62).
sgn = sp.Symbol('s', real=True)          # stands for sign(phi_1) = +/-1
nb = sp.Matrix([0, sgn, 0])
expr = (nb.T * f)[0]
coeff_s1 = sp.simplify(sp.diff(expr, s1))
check('Eq. (61)  sigma_1* = -sign(phi_1)   [minimizing, coefficient of sigma_1 is sign phi_1]',
      sp.simplify(coeff_s1 - sgn) == 0)
minval = sp.simplify(expr.subs({s1: -sgn}).subs(sgn**2, 1))
# Eq. (62): R > (sin phi_1 + sin phi_2) sign phi_1
check('Eq. (62)  UP condition  R > (sin phi_1 + sin phi_2) sign(phi_1)',
      sp.simplify((minval * R - (L * sgn - R)).expand().subs(sgn**2, 1)) == 0)

print()
print('=' * 78)
print('D.  Transversality, Eq. (20), normalized to C = 1 in Eq. (23)')
print('=' * 78)

# --- D1.  Maximum-range BUP.  Eqs. (34)-(37).
p = 1 / sp.sqrt(Rhi**2 + (1 + sp.cos(ph2))**2)             # Eq. (36)
lRf = p * Rhi                                              # Eq. (34)
l1f = sp.Integer(0)
l2f = p * Rhi * (1 + sp.cos(ph2)) * sp.sign(sp.sin(ph2))   # Eq. (35)
fi = ((l1f + l2f)**2 / Rhi**2 + lRf**2)
check('Eqs. (34)-(36)  satisfy the first integral with C = 1',
      all(abs(float(fi.subs({ph2: v, Rbar0: 3 + sp.pi}).evalf()) - 1) < 1e-12
          for v in (-3.0, -1.2, -0.3, 0.3, 1.2, 3.0)))
_ratio = sp.lambdify(ph2, (l2f / lRf).subs({Rbar0: 3 + sp.pi}), 'numpy')
_norm = sp.lambdify(ph2, (-dRhi).subs({Rbar0: 3 + sp.pi}), 'numpy')
check('Eqs. (34)-(35)  are parallel to the outer normal of Eq. (28)',
      all(abs(float(_ratio(v)) - float(_norm(v))) < 1e-12
          for v in (-3.0, -1.2, -0.3, 0.3, 1.2, 3.0)),
      '[sign(sin phi_2) = sign(phi_2) on (-pi, pi); checked numerically]')

l1dot_f = l1dot.subs({lR: lRf, l1: l1f, l2: l2f, R: Rhi})
eq37 = -p * (Rhi * sp.sin(ph1) + (1 + sp.cos(ph2)) * sp.cos(ph1) * sp.sign(sp.sin(ph2)))
check('Eq. (37)  lambda_1-dot on the maximum-range BUP',
      sp.simplify(l1dot_f - eq37) == 0)

# --- D2.  Minimum-range BUP.  Eqs. (47)-(51).
pu = 1 / sp.sqrt(a1**2 + b1**2 + 2 * a1 * b1 * sp.cos(ph2))    # Eq. (50)
check('Eq. (50)  p_under = 1/sqrt(Runder^2 + b_1^2 sin^2 phi_2)',
      sp.simplify(1 / pu**2 - (Rlo**2 + b1**2 * sp.sin(ph2)**2)) == 0)

lRf2 = -pu * Rlo                                    # Eq. (47)
l1f2 = sp.Integer(0)                                # Eq. (48)
l2f2 = -pu * Rlo * b1 * sp.sin(ph2)                 # Eq. (49)
fi2 = (l1f2 + l2f2)**2 / Rlo**2 + lRf2**2
check('Eqs. (47)-(50)  satisfy the first integral with C = 1',
      sp.simplify(fi2 - 1) == 0)
check('Eqs. (47), (49)  are parallel to the outer normal of Eq. (43)',
      sp.simplify(l2f2 / lRf2 - (-dRlo)) == 0)

l1dot_f2 = l1dot.subs({lR: lRf2, l1: l1f2, l2: l2f2, R: Rlo})
eq51 = pu * (a1 * sp.sin(ph1) + b1 * sp.sin(ph1 + ph2))
check('Eq. (51)  lambda_1-dot on the minimum-range BUP',
      sp.simplify(l1dot_f2 - eq51) == 0)

# --- D3.  Off-boresight BUP.  Eqs. (63)-(65).  THE ONE THAT DOES NOT CHECK OUT.
# Normal is (0, sign phi_1, 0); normalization (lambda_1+lambda_2)^2/R^2 = 1
# forces lambda_1 = R sign(phi_1).  On this BUP the equality in Eq. (62) gives
# R = (sin phi_1 + sin phi_2) sign(phi_1), hence lambda_1 = sin phi_1 + sin phi_2.
Rbup = L * sgn
l1f3_derived = Rbup * sgn                                 # = sin phi_1 + sin phi_2
l1f3_printed = L * sgn                                    # Eq. (63) as printed
check('Eq. (63) as printed satisfies the first integral',
      sp.simplify((l1f3_printed**2 / Rbup**2).subs(sgn**2, 1) - 1) == 0,
      '(it does, up to sign -- normalization alone cannot separate the two)')

l2dot_from_derived = sp.simplify(
    l2dot.subs({lR: 0, l1: l1f3_derived, l2: 0, R: Rbup}).subs(sgn**2, 1))
l2dot_from_printed = sp.simplify(
    l2dot.subs({lR: 0, l1: l1f3_printed, l2: 0, R: Rbup}).subs(sgn**2, 1))
eq64 = -sp.cos(ph2) * sgn                                 # Eq. (64) as printed
check('Eq. (64) reproduced from the DERIVED lambda_1f = sin phi_1 + sin phi_2',
      sp.simplify(l2dot_from_derived - eq64) == 0)
check('Eq. (64) reproduced from the PRINTED lambda_1f of Eq. (63)',
      sp.simplify(l2dot_from_printed - eq64) == 0,
      '<-- expected FAIL: Eq. (63) carries one extra factor of sign(phi_1)')

print()
print('=' * 78)
print('E.  Worked-example parameters, Sec. 4 and Appendix A')
print('=' * 78)

# Appendix A, Eq. (96): Rbar_0 = (R_tc)max/rho + pi.  Table 2 pins (R_tc)max/rho.
num = {a1: 0.55, b1: 0.30}
Rhi_num = sp.lambdify(ph2, Rhi.subs({Rbar0: 3 + sp.pi}), 'numpy')
Rlo_num = sp.lambdify(ph2, Rlo.subs(num), 'numpy')
beta = np.pi / 4
tab = [
    ('A_1  (Rbar at phi_2 = pi)',          float(Rhi_num(np.pi)),      3.0,    1),
    ('O_1  (Rbar at phi_2 = 0)',           float(Rhi_num(0.0)),        6.1416, 4),
    ('beta (Rbar at phi_2 = +beta)',       float(Rhi_num(beta)),       4.649,  3),
    ('delta(Rbar at phi_2 = -beta)',       float(Rhi_num(-beta)),      4.649,  3),
    ('M_1  (Runder at phi_2 = pi)',        float(Rlo_num(np.pi)),      0.25,   2),
    ('Z_1  (Runder at phi_2 = 0)',         float(Rlo_num(0.0)),        0.85,   2),
    ('nu   (Runder at phi_2 = +beta)',     float(Rlo_num(beta)),       0.762,  3),
    ('eta  (Runder at phi_2 = -beta)',     float(Rlo_num(-beta)),      0.762,  3),
    ('gamma(R = 2 sin beta, Sec. 3.4)',    float(2 * np.sin(beta)),    1.414,  3),
]
# Table 2 prints 1-4 decimals; the fair test is agreement to within half an
# ulp of the printed precision, not to machine epsilon.
allok = True
for name, got, want, nd in tab:
    d = abs(got - want)
    tol = 0.5 * 10.0**(-nd) + 1e-12
    ok = d <= tol
    allok = allok and ok
    print('        %-34s computed %9.5f   Table 2 %8.4f   |d| = %.2e  (tol %.0e)  %s'
          % (name, got, want, d, tol, 'ok' if ok else 'OUT'))
check('Table 2 range coordinates reproduced with Rbar_0 = 3 + pi',
      allok, '(each to within half an ulp of its printed precision)')

Rhi_614 = sp.lambdify(ph2, Rhi.subs({Rbar0: sp.Float('6.14')}), 'numpy')
print('        with Rbar_0 = 6.14 instead:  A_1 -> %.5f (Table 3.0),'
      '  O_1 -> %.5f (Table 6.1416),  beta -> %.5f (Table 4.649)'
      % (float(Rhi_614(np.pi)), float(Rhi_614(0.0)), float(Rhi_614(beta))))

print()
print('=' * 78)
nfail = sum(1 for _, ok, _ in results if not ok)
print('%d checks, %d passed, %d failed' % (len(results), len(results) - nfail, nfail))
for name, ok, detail in results:
    if not ok:
        print('   FAILED: %s  %s' % (name, detail))
print('=' * 78)
