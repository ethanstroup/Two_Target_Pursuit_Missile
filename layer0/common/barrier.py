"""
barrier.py -- Layer 0 barrier reconstruction for the Davidovitz & Shinar (1989)
two-target game of kind.

Davidovitz, A., and Shinar, J., "Two-Target Game Model of an Air Combat with
Fire-and-Forget All-Aspect Missiles", JOTA 63(2), Nov. 1989, pp. 133-165.

What this module supplies that the existing JS sim does not: the PAPER'S OWN
barrier strategies, sigma_1* = -sign(lambda_1) and sigma_2* = +sign(lambda_2)
(Eqs. 21-22), obtained by integrating the coupled state-costate system
retrograde from the boundary of the usable part, with the costate seeded by the
transversality condition Eq. (20).

Two independent invariants are carried along every trajectory and are the
integration's own error estimate:

    FI  = (lambda_1+lambda_2)^2/R^2 + lambda_R^2  ==  1     Eq. (23), C = 1
    H*  = min_sigma1 max_sigma2 [lambda . f]      ==  0     Eq. (15)

H* is the stronger of the two: it is the semipermeability condition itself, it
is not automatically preserved by the costate ODEs the way FI is, and it is
sensitive to getting the control switching wrong.

Every equation used here is re-derived in verify_symbolic.py (22 of 23 checks
pass; the failure is Eq. (63), see NOTE below).
"""

import numpy as np

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

BETA = np.pi / 4          # off-boresight limit, Sec. 4
A1 = 0.55                 # Eq. (8)
B1 = 0.30                 # Eq. (8)

# Sec. 4 quotes Rbar_0 = 6.14.  Appendix A, Eq. (96), defines it as
# Rbar_0 = (R_tc)max/rho + pi, and Table 2 pins (R_tc)max/rho = 3.0 exactly
# (point A_1, which is Rbar at phi_2 = pi).  Rbar_0 = 3 + pi = 6.14159 then
# reproduces four Table 2 entries to their printed precision where 6.14 does
# not -- see verify_symbolic.py section E.  6.14 is the rounded quotation.
RBAR0 = 3.0 + np.pi

TOL_ZERO = 1e-9


def wrap(a):
    """Wrap into [-pi, pi).  Eq. (9) uses phi + sin phi unwrapped."""
    a = np.asarray(a, dtype=float)
    return (a + np.pi) % (2 * np.pi) - np.pi


# ---------------------------------------------------------------------------
# Target set, Eqs. (6)-(9).  Index asymmetry: the boresight bound is on the
# shooter's OWN angle; both range bounds depend on the TARGET's aspect angle.
# ---------------------------------------------------------------------------

def R_lo(phi_opp):
    """Eq. (8)  minimum firing range."""
    return A1 + B1 * np.cos(phi_opp)


def R_hi(phi_opp):
    """Eq. (9)  no-escape (maximum) firing range."""
    return RBAR0 - np.abs(phi_opp + np.sin(phi_opp))


def dR_lo(phi_opp):
    """Eq. (44)"""
    return -B1 * np.sin(phi_opp)


def dR_hi(phi_opp):
    """Eq. (29)"""
    return -(1 + np.cos(phi_opp)) * np.sign(phi_opp)


def in_target(phi_own, phi_opp, R):
    """Eq. (7): non-strict lower bound, strict upper bound."""
    return (np.abs(phi_own) <= BETA) & (R >= R_lo(phi_opp)) & (R < R_hi(phi_opp))


# ---------------------------------------------------------------------------
# Dynamics and costates, Eqs. (1)-(3) and (17)-(19)
# ---------------------------------------------------------------------------

def state_dot(R, p1, p2, s1, s2):
    L = np.sin(p1) + np.sin(p2)
    return (-(np.cos(p1) + np.cos(p2)),      # Eq. (1)
            L / R + s1,                       # Eq. (2)
            L / R + s2)                       # Eq. (3)


def costate_dot(R, p1, p2, lR, l1, l2):
    L = np.sin(p1) + np.sin(p2)
    S = l1 + l2
    return (L * S / R**2,                                    # Eq. (17)
            -(lR * np.sin(p1) + np.cos(p1) * S / R),         # Eq. (18)
            -(lR * np.sin(p2) + np.cos(p2) * S / R))         # Eq. (19)


def first_integral(R, lR, l1, l2):
    """Eq. (23).  Should equal 1 along every barrier trajectory."""
    return (l1 + l2)**2 / R**2 + lR**2


def hamiltonian_star(R, p1, p2, lR, l1, l2):
    """
    Eq. (15):  min_{sigma_1} max_{sigma_2} [lambda_R Rdot + l1 phi1dot + l2 phi2dot].

    Player 1 (pursuer) minimizes, player 2 (evader) maximizes, so the controls
    separate:  -|lambda_1| + |lambda_2|.  Must vanish on a semipermeable surface.
    """
    L = np.sin(p1) + np.sin(p2)
    C = np.cos(p1) + np.cos(p2)
    return -lR * C + (l1 + l2) * L / R - np.abs(l1) + np.abs(l2)


def barrier_controls(R, p1, p2, lR, l1, l2):
    """
    Eqs. (21)-(22):  sigma_1* = -sign(lambda_1),  sigma_2* = +sign(lambda_2).

    Where a costate component vanishes at the terminal point (it does on every
    BUP -- lambda_1 = 0 on the range surfaces, lambda_2 = 0 on the boresight
    surfaces) the sign is taken from the retrograde first-order behaviour:
    going backward, lambda ~ -tau * lambdadot_f, so sign(lambda) = -sign(lambdadot).
    That reproduces the paper's Eqs. (33) and (65) rather than assuming them.
    """
    _, l1d, l2d = costate_dot(R, p1, p2, lR, l1, l2)
    s1 = -np.sign(l1) if abs(l1) > TOL_ZERO else np.sign(l1d)
    s2 = np.sign(l2) if abs(l2) > TOL_ZERO else -np.sign(l2d)
    return float(s1), float(s2)


def field(y, sigma=None):
    """
    Full state-costate vector field, forward in time, on the barrier.

    If `sigma` is given the control is held fixed; otherwise it is taken from
    the current costate.  Holding it fixed is what the integrator does within a
    step: the barrier control is genuinely piecewise constant, and letting the
    four RK4 stages each pick their own sign across a switch is exactly the
    O(dt) smearing that shows up in H*.
    """
    R, p1, p2, lR, l1, l2 = y
    s1, s2 = sigma if sigma is not None else barrier_controls(R, p1, p2, lR, l1, l2)
    Rd, p1d, p2d = state_dot(R, p1, p2, s1, s2)
    lRd, l1d, l2d = costate_dot(R, p1, p2, lR, l1, l2)
    return np.array([Rd, p1d, p2d, lRd, l1d, l2d])


def _rk4_retro(y, h, sigma):
    """One RK4 step of dy/dtau = -field(y) with the control held fixed."""
    k1 = -field(y, sigma)
    k2 = -field(y + 0.5 * h * k1, sigma)
    k3 = -field(y + 0.5 * h * k2, sigma)
    k4 = -field(y + h * k3, sigma)
    z = y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    z[1] = wrap(z[1])
    z[2] = wrap(z[2])
    return z


def integrate_retrograde(y0, tau_max=12.0, dt=2e-3, R_min=0.02, R_max=12.0,
                         singular_tol=1e-7):
    """
    Integrate the barrier trajectory BACKWARD from a BUP point.

    Retrograde time tau = -t, so dy/dtau = -field(y).  Two things make this
    different from a plain RK4 sweep, and both are needed to hold H*:

      * the control is FROZEN over a step.  sigma_1* = -sign(lambda_1) and
        sigma_2* = +sign(lambda_2) are piecewise constant; letting each RK4
        stage re-read the sign smears every switch over a whole step.
      * switches are LOCATED, not stepped over.  The crossing of lambda_1 or
        lambda_2 through zero is bisected out, the step is cut exactly there,
        and the control is re-read past it (barrier_controls then takes the
        sign from lambdadot, reproducing the paper's Eqs. 33 and 65).

    A trajectory that sits on a SINGULAR arc -- a universal line, where a
    costate component stays at zero over an interval and the optimal control is
    intermediate rather than bang-bang (Table 3 lists strategies such as (-1,0)
    and (0,+1)) -- is outside what a bang-bang integrator can represent.  Those
    are detected and flagged in the return value rather than silently chattered
    through.

    Returns dict with the trajectory, the switch times, any singular-arc flag,
    and the two invariant residual histories.
    """
    y = np.array(y0, dtype=float)
    ys = [y.copy()]
    taus = [0.0]
    sigs = []
    switches = []
    singular = []
    tau = 0.0
    guard = 0
    max_steps = int(4 * tau_max / dt) + 1000

    while tau < tau_max and guard < max_steps:
        guard += 1
        h = min(dt, tau_max - tau)
        if h <= 0:
            break

        sigma = barrier_controls(*y)

        # Singular-arc guard: a costate component AND its derivative both at
        # zero means the bang-bang law is undetermined here.
        _, l1d, l2d = costate_dot(y[0], y[1], y[2], y[3], y[4], y[5])
        if abs(y[4]) < singular_tol and abs(l1d) < singular_tol:
            singular.append((tau, 1))
        if abs(y[5]) < singular_tol and abs(l2d) < singular_tol:
            singular.append((tau, 2))

        z = _rk4_retro(y, h, sigma)
        if not np.all(np.isfinite(z)):
            break

        # locate the earliest costate sign change inside this step
        event = None
        for idx in (4, 5):
            if y[idx] * z[idx] < 0.0:
                lo, hi = 0.0, h
                for _ in range(60):
                    mid = 0.5 * (lo + hi)
                    if y[idx] * _rk4_retro(y, mid, sigma)[idx] <= 0.0:
                        hi = mid
                    else:
                        lo = mid
                hstar = 0.5 * (lo + hi)
                if event is None or hstar < event[0]:
                    event = (hstar, idx)

        if event is not None and event[0] > 1e-13:
            hstar, idx = event
            y = _rk4_retro(y, hstar, sigma)
            y[idx] = 0.0            # snap exactly onto the switching surface
            tau += hstar
            switches.append((tau, idx - 3))
        elif event is not None:
            # sitting on the switch already: the control has flipped, step on
            y[event[1]] = 0.0
            sigma = barrier_controls(*y)
            y = _rk4_retro(y, h, sigma)
            tau += h
        else:
            y = z
            tau += h

        sigs.append(sigma)
        ys.append(y.copy())
        taus.append(tau)
        if not (R_min < y[0] < R_max):
            break

    Y = np.array(ys)
    fi = first_integral(Y[:, 0], Y[:, 3], Y[:, 4], Y[:, 5])
    hs = hamiltonian_star(Y[:, 0], Y[:, 1], Y[:, 2], Y[:, 3], Y[:, 4], Y[:, 5])
    return dict(tau=np.array(taus), Y=Y,
                sigma=np.array(sigs) if sigs else np.zeros((0, 2)),
                R=Y[:, 0], phi1=Y[:, 1], phi2=Y[:, 2],
                lR=Y[:, 3], l1=Y[:, 4], l2=Y[:, 5],
                switches=switches, singular=singular,
                fi_err=np.abs(fi - 1.0), h_err=np.abs(hs))


# ---------------------------------------------------------------------------
# Boundary of the usable part (BUP), the three families.
# The UP condition is Eq. (13); the BUP replaces the inequality by equality.
# ---------------------------------------------------------------------------

def up_maxrange(p1, p2):
    """Eq. (32) residual.  Negative => in (UP)_1.  Zero => on (BUP)_1."""
    L = np.sin(p1) + np.sin(p2)
    return R_hi(p2) * (1 - np.cos(p1)) + L * (1 + np.cos(p2)) * np.sign(p2)


def up_minrange(p1, p2):
    """Eq. (46) residual.  Negative => in (UP)_1."""
    L = np.sin(p1) + np.sin(p2)
    return (R_lo(p2) * (np.cos(p1) + np.cos(p2) + B1 * np.abs(np.sin(p2)))
            - B1 * np.sin(p2) * L)


def up_boresight(R, p1, p2):
    """Eq. (62) residual for the lower limit.  Negative => in (UP)_1."""
    L = np.sin(p1) + np.sin(p2)
    return L * np.sign(p1) - R


def _bisect(f, lo, hi, n=200):
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def bup_maxrange(p2):
    """
    (BUP)_1 on the maximum-range surface: solve Eq. (32) with equality for
    phi_1 in [-beta, beta] at the given phi_2.  Returns list of phi_1 roots.
    """
    f = lambda x: up_maxrange(x, p2)
    grid = np.linspace(-BETA, BETA, 801)
    vals = f(grid)
    roots = []
    for i in range(len(grid) - 1):
        if vals[i] == 0.0:
            roots.append(grid[i])
        elif vals[i] * vals[i + 1] < 0:
            r = _bisect(f, grid[i], grid[i + 1])
            if r is not None:
                roots.append(r)
    return roots


def bup_minrange(p2):
    """(BUP)_1 on the minimum-range surface: Eq. (46) with equality."""
    f = lambda x: up_minrange(x, p2)
    grid = np.linspace(-BETA, BETA, 801)
    vals = f(grid)
    roots = []
    for i in range(len(grid) - 1):
        if vals[i] * vals[i + 1] < 0:
            r = _bisect(f, grid[i], grid[i + 1])
            if r is not None:
                roots.append(r)
    return roots


def bup_boresight(p2, sgn=+1):
    """
    (BUP)_1 on the off-boresight surface phi_1 = sgn*beta: Eq. (62) equality
    gives R = (sin phi_1 + sin phi_2) sign(phi_1) directly.  Returns R or None
    if that R is outside the target-set range band.
    """
    p1 = sgn * BETA
    R = (np.sin(p1) + np.sin(p2)) * np.sign(p1)
    if R <= 0:
        return None
    if not (R_lo(p2) <= R < R_hi(p2)):
        return None
    return R


# ---------------------------------------------------------------------------
# Terminal costates from transversality, Eq. (20), normalized to C = 1.
# ---------------------------------------------------------------------------

def lam_maxrange(p2):
    """Eqs. (34)-(36) -- verified symbolically, including the first integral."""
    Rb = R_hi(p2)
    p = 1.0 / np.sqrt(Rb**2 + (1 + np.cos(p2))**2)
    return (p * Rb, 0.0, p * Rb * (1 + np.cos(p2)) * np.sign(np.sin(p2)))


def lam_minrange(p2):
    """Eqs. (47)-(50) -- verified symbolically, including the first integral."""
    Rl = R_lo(p2)
    pu = 1.0 / np.sqrt(A1**2 + B1**2 + 2 * A1 * B1 * np.cos(p2))
    return (-pu * Rl, 0.0, -pu * Rl * B1 * np.sin(p2))


def lam_boresight(R, p1, p2):
    """
    Transversality on phi_1 = +/- beta.  The outer normal is (0, sign phi_1, 0),
    so lambda = mu (0, sign phi_1, 0) and the first integral forces mu = R:

        lambda_1f = R sign(phi_1) = sin phi_1 + sin phi_2   on the BUP.

    NOTE -- Eq. (63) as PRINTED gives lambda_1f = (sin phi_1 + sin phi_2) sign(phi_1),
    one factor of sign(phi_1) more than this.  The paper's own Eq. (64),
    lambdadot_2f = -(cos phi_2) sign(phi_1), is reproduced by the expression above
    and NOT by Eq. (63) as printed.  See verify_symbolic.py section D3.  The
    discrepancy is invisible for phi_1 = +beta and flips the whole barrier
    strategy pair for phi_1 = -beta, so it matters.
    """
    return (0.0, R * np.sign(p1), 0.0)


def lam_corner(R, p1, p2, n_a, n_b):
    """
    Costate at a corner of the target-set boundary, where the gradient must be a
    non-negative combination of the outer normals of the two adjoining surfaces
    (Refs. 18, 20; the paper's Eqs. 38, 53, 66 are the three instances).

    Rather than transcribing those closed forms, solve for the combination
    directly from the two conditions it must satisfy:

        H*(lambda) = 0        Eq. (15), semipermeability
        FI(lambda) = 1        Eq. (23) with C = 1

    There can be more than one admissible root -- the two barrier sheets meeting
    at the corner -- so every one is returned and the caller picks.  That is why
    this does not silently return "the" corner costate.

    Returns list of (lambda, mu_a, mu_b), possibly empty.
    """
    n_a = np.asarray(n_a, float)
    n_b = np.asarray(n_b, float)

    def h_of_theta(th):
        lam = np.cos(th) * n_a + np.sin(th) * n_b
        nrm = first_integral(R, lam[0], lam[1], lam[2])
        if nrm <= 0:
            return np.nan
        lam = lam / np.sqrt(nrm)
        return hamiltonian_star(R, p1, p2, lam[0], lam[1], lam[2])

    ths = np.linspace(0.0, np.pi / 2, 4001)
    hs = np.array([h_of_theta(t) for t in ths])
    sols = []
    for i in range(len(ths) - 1):
        if np.isfinite(hs[i]) and np.isfinite(hs[i + 1]) and hs[i] * hs[i + 1] <= 0:
            th = _bisect(h_of_theta, ths[i], ths[i + 1])
            if th is None:
                continue
            lam = np.cos(th) * n_a + np.sin(th) * n_b
            lam = lam / np.sqrt(first_integral(R, lam[0], lam[1], lam[2]))
            if not sols or np.max(np.abs(lam - sols[-1][0])) > 1e-8:
                sols.append((lam, float(np.cos(th)), float(np.sin(th))))
    return sols


def n_maxrange(p2):
    """Eq. (28)"""
    return np.array([1.0, 0.0, -dR_hi(p2)])


def n_minrange(p2):
    """Eq. (43)"""
    return np.array([-1.0, 0.0, dR_lo(p2)])


def n_boresight(p1):
    """Eq. (59)"""
    return np.array([0.0, np.sign(p1), 0.0])
