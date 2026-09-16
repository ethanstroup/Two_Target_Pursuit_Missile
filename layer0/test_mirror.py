"""
test_mirror.py -- verify the target-set-2 mirror rather than assuming it.

Claim: the second single-target game (player 2 hunting player 1) is obtained
from the first by the index swap (phi_1, lambda_1) <-> (phi_2, lambda_2),
WITH the min/max roles exchanged.

Nothing here is assumed.  T_2's usable-part conditions are recomputed from
first principles -- T_2's own outer normals, its own min-max with the roles
reversed -- and compared against the swapped call of the T_1 functions.

Run: python3 test_mirror.py
"""
import numpy as np
import barrier as B

fails = []
def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('   ' + detail) if detail else ''}")
    if not ok:
        fails.append(name)


def minmax_T1(R, p1, p2, n):
    """min_{sigma1} max_{sigma2} n.xdot   -- player 1 is the attacker."""
    L = np.sin(p1) + np.sin(p2)
    C = np.cos(p1) + np.cos(p2)
    return -n[0]*C + (n[1]+n[2])*L/R - abs(n[1]) + abs(n[2])

def minmax_T2(R, p1, p2, n):
    """min_{sigma2} max_{sigma1} n.xdot   -- player 2 is the attacker.
    Same field; the roles of the two controls are exchanged."""
    L = np.sin(p1) + np.sin(p2)
    C = np.cos(p1) + np.cos(p2)
    return -n[0]*C + (n[1]+n[2])*L/R + abs(n[1]) - abs(n[2])


print("1. H* swap identity:  H*_2(x, lam) == H*_1(swap x, swap lam)")
rng = np.random.default_rng(0)
worst = 0.0
for _ in range(20000):
    R = rng.uniform(0.3, 7.0)
    p1, p2 = rng.uniform(-np.pi, np.pi, 2)
    lR, l1, l2 = rng.uniform(-3, 3, 3)
    a = minmax_T2(R, p1, p2, (lR, l1, l2))
    b = B.hamiltonian_star(R, p2, p1, lR, l2, l1)      # T_1 machinery, swapped
    worst = max(worst, abs(a - b))
check("H* mirror", worst < 1e-12, f"max residual {worst:.2e}")


print("\n2. T_2 usable part, recomputed from T_2's own normals vs swapped T_1 call")

# --- max-range face of T_2:  R = Rhi(phi_1),  outer normal (1, -dRhi(p1), 0)
#
# phi_1 = 0 is EXCLUDED, and not as a fudge.  Rbar(phi) = Rbar_0 - |phi + sin phi|
# has a kink at phi = 0, so the max-range face has a CORNER there and no unique
# outer normal -- sign(0) = 0 collapses the normal instead of picking a side.
# This is the exact mirror of the phi_2 = 0 corner on T_1 that the paper handles
# with its own corner equations (Eqs. 38-42) and that lam_corner solves via the
# two-normal cone.  Including the line would be testing a single normal where
# the geometry has two.  Off that one line the mirror is exact to 2.3e-15.
worst = 0.0; n_pts = 0
for p1 in np.linspace(-np.pi, np.pi, 181):
    if abs(p1) < 1e-9:                      # the corner curve, see above
        continue
    for p2 in np.linspace(-B.BETA, B.BETA, 61):
        R = B.R_hi(p1)
        n = (1.0, -B.dR_hi(p1), 0.0)
        lhs = minmax_T2(R, p1, p2, n) * R          # scaled as Eq. (32) is
        rhs = B.up_maxrange(p2, p1)                # T_1 residual, indices swapped
        worst = max(worst, abs(lhs - rhs)); n_pts += 1
check("max-range (UP)_2", worst < 1e-10, f"{n_pts} pts (phi_1=0 corner excluded), max residual {worst:.2e}")

# --- min-range face of T_2:  R = Rlo(phi_1),  outer normal (-1, dRlo(p1), 0)
worst = 0.0; n_pts = 0
for p1 in np.linspace(-np.pi, np.pi, 181):
    for p2 in np.linspace(-B.BETA, B.BETA, 61):
        R = B.R_lo(p1)
        n = (-1.0, B.dR_lo(p1), 0.0)
        lhs = minmax_T2(R, p1, p2, n) * R
        rhs = B.up_minrange(p2, p1)
        worst = max(worst, abs(lhs - rhs)); n_pts += 1
check("min-range (UP)_2", worst < 1e-10, f"{n_pts} pts, max residual {worst:.2e}")

# --- boresight face of T_2:  |phi_2| = beta,  outer normal (0, 0, sign p2)
worst = 0.0; n_pts = 0
for sgn in (+1, -1):
    p2 = sgn * B.BETA
    for p1 in np.linspace(-np.pi, np.pi, 181):
        for R in np.linspace(0.3, 6.0, 40):
            n = (0.0, 0.0, float(sgn))
            lhs = minmax_T2(R, p1, p2, n) * R
            rhs = B.up_boresight(R, p2, p1)
            worst = max(worst, abs(lhs - rhs)); n_pts += 1
check("boresight (UP)_2", worst < 1e-10, f"{n_pts} pts, max residual {worst:.2e}")


print("\n3. target sets are each other's mirror:  T_2(R,p1,p2) == T_1(R,p2,p1)")
bad = 0; n_pts = 0
for R in np.linspace(0.25, 6.3, 60):
    for p1 in np.linspace(-np.pi, np.pi, 73):
        for p2 in np.linspace(-np.pi, np.pi, 73):
            t2 = (abs(p2) <= B.BETA) and (B.R_lo(p1) <= R < B.R_hi(p1))
            t1_sw = bool(B.in_target(p2, p1, R))
            if t2 != t1_sw: bad += 1
            n_pts += 1
check("target-set mirror", bad == 0, f"{n_pts} pts, {bad} mismatches")


print("\n4. the mirror is NOT a plain symmetry: H*_2 != H*_1 at the same argument")
diff = 0
for _ in range(2000):
    R = rng.uniform(0.3, 7.0); p1, p2 = rng.uniform(-np.pi, np.pi, 2)
    lR, l1, l2 = rng.uniform(-3, 3, 3)
    if abs(B.hamiltonian_star(R,p1,p2,lR,l1,l2) - minmax_T2(R,p1,p2,(lR,l1,l2))) > 1e-9:
        diff += 1
check("roles genuinely exchanged", diff > 1900,
      f"{diff}/2000 sample points differ, as they must")

print()
print(f"{4 - len(fails)} of 4 groups passed" if not fails else f"FAILURES: {fails}")
raise SystemExit(1 if fails else 0)
