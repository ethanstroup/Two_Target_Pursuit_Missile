"""
inertial.py -- exact two-aircraft kinematics in a fixed frame, independent of the reduced
(R, phi_1, phi_2) equations and of the pole flip.  Used to verify both (pole record, V1 and V2).

Each aircraft has unit speed and turn rate sigma; with sigma held constant over an interval its
path is a circle arc (or a straight line), in closed form.  The reduced state is only ever
*computed* from the positions:

    lambda = atan2(y_2 - y_1, x_2 - x_1)          line of sight from 1 to 2
    R      = |p_2 - p_1|
    phi_1  = psi_1 - lambda
    phi_2  = psi_2 - lambda - pi

These conventions reproduce D&S Eqs. (1)-(3) exactly as the code writes them
(R-dot = -(cos phi_1 + cos phi_2), phi_i-dot = L/R + sigma_i); `check_conventions` verifies it.
A pass is just two points getting close: nothing is singular and nothing flips.

State layout: s = (x_1, y_1, psi_1, x_2, y_2, psi_2), shape (N, 6).
"""

import numpy as np

import sim_m5 as SIM


# ---------------------------------------------------------------------------
# Kinematics and conversions
# ---------------------------------------------------------------------------

def arc(x, y, psi, sigma, t):
    """Position and heading after time t at constant unit speed and turn rate sigma (vectorized)."""
    t = np.broadcast_to(np.asarray(t, float), np.shape(x))
    sigma = np.broadcast_to(np.asarray(sigma, float), np.shape(x))
    small = np.abs(sigma) < 1e-12
    s = np.where(small, 1.0, sigma)
    psi_t = psi + sigma * t
    xa = x + np.where(small, np.cos(psi) * t, (np.sin(psi_t) - np.sin(psi)) / s)
    ya = y + np.where(small, np.sin(psi) * t, (np.cos(psi) - np.cos(psi_t)) / s)
    return xa, ya, psi_t


def advance(s, s1, s2, t):
    """Both aircraft along their exact arcs for time t (scalar or per row)."""
    x1, y1, p1 = arc(s[:, 0], s[:, 1], s[:, 2], s1, t)
    x2, y2, p2 = arc(s[:, 3], s[:, 4], s[:, 5], s2, t)
    return np.stack([x1, y1, p1, x2, y2, p2], -1)


def to_reduced(s):
    """(R, phi_1, phi_2) from inertial positions and headings."""
    dx, dy = s[:, 3] - s[:, 0], s[:, 4] - s[:, 1]
    lam = np.arctan2(dy, dx)
    R = np.hypot(dx, dy)
    return np.stack([R, SIM.wrap(s[:, 2] - lam), SIM.wrap(s[:, 5] - lam - np.pi)], -1)


def from_reduced(x):
    """Inertial state with player 1 at the origin heading along +x."""
    R, p1, p2 = x[:, 0], x[:, 1], x[:, 2]
    lam = -p1
    z = np.zeros_like(R)
    return np.stack([z, z, z, R * np.cos(lam), R * np.sin(lam), SIM.wrap(p2 + lam + np.pi)], -1)


def check_conventions(n=20000, h=1e-3, seed=0):
    """
    (round-trip error, max |reduced RK4 step - exact inertial step|) over random states and
    controls away from R = 0.  Both should be at rounding / RK4-truncation level.
    """
    rng = np.random.default_rng(seed)
    x = np.stack([rng.uniform(0.5, 12, n), rng.uniform(-np.pi, np.pi, n), rng.uniform(-np.pi, np.pi, n)], -1)
    rt = to_reduced(from_reduced(x))
    d_rt = np.abs(np.concatenate([rt[:, :1] - x[:, :1], SIM.wrap(rt[:, 1:] - x[:, 1:])], 1)).max()
    s1, s2 = rng.uniform(-1, 1, n), rng.uniform(-1, 1, n)
    a = SIM.rk4(x, s1, s2, h)
    b = to_reduced(advance(from_reduced(x), s1, s2, h))
    d_step = np.abs(np.concatenate([a[:, :1] - b[:, :1], SIM.wrap(a[:, 1:] - b[:, 1:])], 1)).max()
    return float(d_rt), float(d_step)


# ---------------------------------------------------------------------------
# V1: the exact reach-avoid outcome for frozen controls
# ---------------------------------------------------------------------------

def exact_outcome(x0, c1, c2, T, dt=1e-3, R_out=12.0):
    """
    min_t max{ ell_1(x(t)), max_{s<=t} -ell_2(x(s)) } along the exact inertial path from each
    reduced start, sampled every dt.  Also returns whether the path leaves through R = R_out and
    the smallest R it reaches.
    """
    s0 = from_reduced(np.asarray(x0, float))
    G = -SIM.ell2(x0)
    J = np.maximum(SIM.ell1(x0), G)
    left = np.zeros(len(x0), bool)
    r_min = np.asarray(x0)[:, 0].copy()
    for k in range(1, int(round(T / dt)) + 1):
        x = to_reduced(advance(s0, c1, c2, k * dt))
        r_min = np.minimum(r_min, x[:, 0])
        left |= x[:, 0] >= R_out
        G = np.maximum(G, -SIM.ell2(x))
        J = np.minimum(J, np.maximum(SIM.ell1(x), G))
    return J, left, r_min


# ---------------------------------------------------------------------------
# V2: rollouts with feedback laws, integrated exactly
# ---------------------------------------------------------------------------

def _crossing(s, s1, s2, h_hi, efun, iters=40):
    """Smallest h in (0, h_hi] with efun(reduced(s(h))) <= 0, on the exact arcs."""
    lo = np.zeros(len(s))
    hi = np.full(len(s), float(h_hi))
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        inside = efun(to_reduced(advance(s, s1, s2, mid))) <= 0
        hi = np.where(inside, mid, hi)
        lo = np.where(inside, lo, mid)
    return hi


def rollout(x0, law1, law2, T, dt=2e-3, R_out=12.0):
    """
    The stopped game with controls frozen over each dt (as in sim_m5.rollout), integrated on
    exact arcs.  Laws see only the reduced state computed from the positions.  Same outcome
    codes as sim_m5; the only exit is through R = R_out.
    """
    s = from_reduced(np.asarray(x0, float))
    N = len(s)
    outcome = np.full(N, SIM.NONE)
    t_end = np.full(N, np.inf)
    r_min = np.asarray(x0)[:, 0].copy()
    alive = np.ones(N, bool)
    for n in range(int(round(T / dt))):
        ids = np.nonzero(alive)[0]
        if ids.size == 0:
            break
        t = n * dt
        sa = s[ids]
        xa = to_reduced(sa)
        c1, c2 = law1(xa, t, ids), law2(xa, t, ids)
        sn = advance(sa, c1, c2, dt)
        xn = to_reduced(sn)
        r_min[ids] = np.minimum(r_min[ids], xn[:, 0])
        hit1, hit2 = SIM.ell1(xn) <= 0, SIM.ell2(xn) <= 0
        hit = hit1 | hit2
        if hit.any():
            sub = np.nonzero(hit)[0]
            h1 = np.full(sub.size, np.inf)
            h2 = np.full(sub.size, np.inf)
            m1, m2 = hit1[sub], hit2[sub]
            if m1.any():
                h1[m1] = _crossing(sa[sub][m1], c1[sub][m1], c2[sub][m1], dt, SIM.ell1)
            if m2.any():
                h2[m2] = _crossing(sa[sub][m2], c1[sub][m2], c2[sub][m2], dt, SIM.ell2)
            g = ids[sub]
            outcome[g] = SIM.classify(h1, h2)
            t_end[g] = t + np.minimum(h1, h2)
            alive[g] = False
        out = ~hit & (xn[:, 0] >= R_out)
        if out.any():
            g = ids[out]
            outcome[g] = SIM.EXIT
            t_end[g] = t + dt
            alive[g] = False
        s[ids] = sn
    return dict(outcome=outcome, t_end=t_end, x_end=to_reduced(s), r_min=r_min)
