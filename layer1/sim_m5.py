"""
sim_m5.py -- Layer 1, M5.  Vectorized forward simulation of the stopped two-target game.

Criteria file (claude/Layer1_M5_Criteria_2026-10-11.md) Sec. 3.3-3.4.

Thousands of rollouts are needed (check 11 alone is 5 laws x ~2200 starts), so the
per-trajectory Python loop of hji.forward_sim is replaced by one loop over time
with every live trajectory advanced together.  The read rule for a value-based law
is hji.make_policy's, unchanged: the snapshot NEAREST to the remaining horizon
T - t, with the same sign tie-break.  `assert_matches_make_policy` checks that
equivalence on sampled states before any result is trusted.

Outcomes (criteria Sec. 3.3):
    WIN   player 1 enters T_{1->2} first, by more than TIE_EPS
    LOSS  player 2 enters T_{2->1} first
    MUTUAL  both entries within TIE_EPS of each other (never a win)
    NONE  no entry by the horizon
    EXIT  left 0.2 < R < 12 before any entry
Kill instants are located inside the step by bisection to ~1e-11 in time.
"""

import numpy as np

import ell as E

R_LO_DOM, R_HI_DOM = 0.2, 12.0
TIE_EPS = 1e-6
WIN, LOSS, MUTUAL, NONE, EXIT = 1, 2, 3, 0, 4
OUTCOME_NAMES = {WIN: 'win alone', LOSS: 'player-2 kill', MUTUAL: 'mutual kill',
                 NONE: 'no kill', EXIT: 'exited domain'}


# ---------------------------------------------------------------------------
# Geometry, dynamics, constraint functions
# ---------------------------------------------------------------------------

class Geom:
    """Node layout of hji.make_grid: R endpoints included, phi in [-pi, pi) endpoint=False."""

    def __init__(self, shape, R_min=R_LO_DOM, R_max=R_HI_DOM):
        self.n_R, self.n_phi = shape[0], shape[1]
        self.R_min, self.R_max = R_min, R_max
        self.dR = (R_max - R_min) / (self.n_R - 1)
        self.dphi = 2 * np.pi / self.n_phi

    def coords(self):
        R = np.linspace(self.R_min, self.R_max, self.n_R)
        P = -np.pi + np.arange(self.n_phi) * self.dphi
        return R, P

    def node_states(self, idx):
        """States of flat node indices."""
        i, j, k = np.unravel_index(idx, (self.n_R, self.n_phi, self.n_phi))
        R, P = self.coords()
        return np.stack([R[i], P[j], P[k]], -1)


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def f(x, s1, s2):
    """D&S Eqs. (1)-(3), phi_dot = LOS rate + sigma."""
    R, p1, p2 = x[:, 0], x[:, 1], x[:, 2]
    L = np.sin(p1) + np.sin(p2)
    return np.stack([-(np.cos(p1) + np.cos(p2)), L / R + s1, L / R + s2], -1)


def rk4(x, s1, s2, h):
    """One RK4 step of size h (scalar or per-row) with the controls frozen over it."""
    h = np.asarray(h, float)
    hh = h[:, None] if h.ndim else h
    k1 = f(x, s1, s2)
    k2 = f(x + 0.5 * hh * k1, s1, s2)
    k3 = f(x + 0.5 * hh * k2, s1, s2)
    k4 = f(x + hh * k3, s1, s2)
    y = x + (hh / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    y[:, 1] = wrap(y[:, 1])
    y[:, 2] = wrap(y[:, 2])
    return y


def ell1(x):
    return E.ell(x[:, 0], x[:, 1], x[:, 2])


def ell2(x):
    """ell_2 = ell_1 o S."""
    return E.ell(x[:, 0], x[:, 2], x[:, 1])


# ---------------------------------------------------------------------------
# Fields on the grid
# ---------------------------------------------------------------------------

def angular_partials(V, dphi):
    """Central differences in phi_1, phi_2 (periodic), float32 -- grid.grad_values' rule."""
    V = np.asarray(V, np.float64)
    d1 = (np.roll(V, -1, 1) - np.roll(V, 1, 1)) / (2 * dphi)
    d2 = (np.roll(V, -1, 2) - np.roll(V, 1, 2)) / (2 * dphi)
    return d1.astype(np.float32), d2.astype(np.float32)


def interp(geom, field, x):
    """Multilinear interpolation, periodic in both angles, R clamped to the grid (grid.interpolate's rule)."""
    pr = (x[:, 0] - geom.R_min) / geom.dR
    p1 = ((x[:, 1] + np.pi) / geom.dphi) % geom.n_phi
    p2 = ((x[:, 2] + np.pi) / geom.dphi) % geom.n_phi
    i0 = np.floor(pr).astype(int)
    j0 = np.floor(p1).astype(int)
    k0 = np.floor(p2).astype(int)
    wr, w1, w2 = pr - i0, p1 - j0, p2 - k0
    i0c, i1c = np.clip(i0, 0, geom.n_R - 1), np.clip(i0 + 1, 0, geom.n_R - 1)
    j0c, j1c = j0 % geom.n_phi, (j0 + 1) % geom.n_phi
    k0c, k1c = k0 % geom.n_phi, (k0 + 1) % geom.n_phi
    out = np.zeros(len(x))
    for ii, a in ((i0c, 1 - wr), (i1c, wr)):
        for jj, b in ((j0c, 1 - w1), (j1c, w1)):
            for kk, c in ((k0c, 1 - w2), (k1c, w2)):
                out += a * b * c * field[ii, jj, kk]
    return out


def nearest_node_value(geom, field, x):
    i = np.clip(np.rint((x[:, 0] - geom.R_min) / geom.dR).astype(int), 0, geom.n_R - 1)
    j = np.rint((x[:, 1] + np.pi) / geom.dphi).astype(int) % geom.n_phi
    k = np.rint((x[:, 2] + np.pi) / geom.dphi).astype(int) % geom.n_phi
    return field[i, j, k]


class SnapshotStack:
    """V(., tau_k) snapshots reduced to their angular partials."""

    def __init__(self, geom, snaps, keep=(1, 2)):
        self.geom = geom
        keys = sorted(snaps, key=float)
        self.taus = np.array([float(k) for k in keys])
        self.d1, self.d2 = [], []
        for k in keys:
            d1, d2 = angular_partials(snaps[k], geom.dphi)
            self.d1.append(d1 if 1 in keep else None)
            self.d2.append(d2 if 2 in keep else None)

    def nearest(self, r):
        """make_policy's rule: the snapshot nearest to remaining horizon r."""
        return int(np.argmin(np.abs(self.taus - r)))

    def first_at_least(self, t):
        """Per-trajectory: first snapshot with tau_k >= t (last one if none)."""
        k = np.searchsorted(self.taus, t - 1e-12, side='left')
        return np.minimum(k, len(self.taus) - 1)


# ---------------------------------------------------------------------------
# Control laws.  Signature: law(x, t, ids) -> sigma array, ids = global trajectory ids.
# ---------------------------------------------------------------------------

def sign_min(g):
    """Minimizer's bang-bang law, make_policy tie-break: -1 where g >= 0."""
    return np.where(g >= 0, -1.0, 1.0)


def sign_max(g):
    """Maximizer's bang-bang law, make_policy tie-break: +1 where g >= 0."""
    return np.where(g >= 0, 1.0, -1.0)


def finite_or_zero(sig, g):
    return np.where(np.isfinite(g), sig, 0.0)


def law_value_p1(stack, T):
    """sigma_1 = -sign(dV/dphi_1) at remaining horizon T - t (minimizer)."""
    def law(x, t, ids):
        g = interp(stack.geom, stack.d1[stack.nearest(T - t)], x)
        return finite_or_zero(sign_min(g), g)
    return law


def law_value_p2(stack, T):
    """sigma_2 = +sign(dV/dphi_2) at remaining horizon T - t (maximizer)."""
    def law(x, t, ids):
        g = interp(stack.geom, stack.d2[stack.nearest(T - t)], x)
        return finite_or_zero(sign_max(g), g)
    return law


def law_value_p1_capped(stack, T):
    """As law_value_p1, remaining horizons beyond the last snapshot read the last one."""
    def law(x, t, ids):
        r = min(T - t, stack.taus[-1])
        g = interp(stack.geom, stack.d1[stack.nearest(r)], x)
        return finite_or_zero(sign_min(g), g)
    return law


def law_value_p2_capped(stack, T):
    """As law_value_p2, remaining horizons beyond the last snapshot read the last one."""
    def law(x, t, ids):
        r = min(T - t, stack.taus[-1])
        g = interp(stack.geom, stack.d2[stack.nearest(r)], x)
        return finite_or_zero(sign_max(g), g)
    return law


def swapped(x):
    return x[:, [0, 2, 1]]


def law_trade_p2(stack1, t1star):
    """
    Player 2 racing to T_{2->1}: sigma_2 = -sign(dt_2*/dphi_2) = -sign(dV_2/dphi_2) read
    at the first snapshot tau_k >= t_2*(x).  With V_2 = V_1 o S and t_2* = t_1* o S,
    dV_2/dphi_2 (x) = dV_1/dphi_1 (Sx), so the V_1 stack is read at swapped states.
    """
    geom = stack1.geom

    def law(x, t, ids):
        xs = swapped(x)
        t2 = nearest_node_value(geom, t1star, xs)
        k = stack1.first_at_least(np.where(np.isfinite(t2), t2, np.inf))
        g = np.empty(len(x))
        for kk in np.unique(k):
            m = k == kk
            g[m] = interp(geom, stack1.d1[kk], xs[m])
        return finite_or_zero(sign_min(g), g)
    return law


def law_trade_p1(stack1, t1star):
    """C2's player 1: -sign(dV_1/dphi_1) read at the first snapshot tau_k >= t_1*(x)."""
    geom = stack1.geom

    def law(x, t, ids):
        t1 = nearest_node_value(geom, t1star, x)
        k = stack1.first_at_least(np.where(np.isfinite(t1), t1, np.inf))
        g = np.empty(len(x))
        for kk in np.unique(k):
            m = k == kk
            g[m] = interp(geom, stack1.d1[kk], x[m])
        return finite_or_zero(sign_min(g), g)
    return law


def law_heuristic(i):
    """The old pursuit heuristic, sigma_i = -sign(phi_i)."""
    def law(x, t, ids):
        return -np.sign(x[:, i])
    return law


def law_zero():
    def law(x, t, ids):
        return np.zeros(len(x))
    return law


def law_random(n_traj, T, period=0.25, seed=0):
    """sigma = +/-1 with equal probability, redrawn every `period`, fixed seed per run."""
    table = np.random.default_rng(seed).choice([-1.0, 1.0], size=(n_traj, int(np.ceil(T / period)) + 2))

    def law(x, t, ids):
        return table[ids, int(t // period)]
    return law


# ---------------------------------------------------------------------------
# Rollout engine
# ---------------------------------------------------------------------------

def locate_crossing(x, s1, s2, h_hi, efun, iters=40):
    """Smallest h in (0, h_hi] with efun(x(h)) <= 0, by bisection (efun(x) > 0, efun(x(h_hi)) <= 0)."""
    lo = np.zeros(len(x))
    hi = np.full(len(x), float(h_hi))
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        inside = efun(rk4(x, s1, s2, mid)) <= 0
        hi = np.where(inside, mid, hi)
        lo = np.where(inside, lo, mid)
    return hi


def classify(h1, h2):
    """Outcome for trajectories with at least one crossing this step; inf = no crossing."""
    out = np.where(h1 < h2, WIN, LOSS)
    both = np.isfinite(h1) & np.isfinite(h2) & (np.abs(h1 - h2) <= TIE_EPS)
    return np.where(both, MUTUAL, out)


def rollout(x0, law1, law2, T, dt=2e-3):
    """
    Advance every trajectory to its first kill (or T, or exit).  Returns dict with
    per-trajectory outcome code, event time and final state.
    """
    x = np.array(x0, float)
    N = len(x)
    outcome = np.full(N, NONE)
    t_end = np.full(N, np.inf)
    alive = np.ones(N, bool)
    pre1, pre2 = ell1(x) <= 0, ell2(x) <= 0
    started = pre1 | pre2
    outcome[started] = np.where(pre1 & pre2, MUTUAL, np.where(pre1, WIN, LOSS))[started]
    t_end[started] = 0.0
    alive &= ~started
    nsteps = int(round(T / dt))
    for n in range(nsteps):
        ids = np.nonzero(alive)[0]
        if ids.size == 0:
            break
        t = n * dt
        xa = x[ids]
        s1, s2 = law1(xa, t, ids), law2(xa, t, ids)
        xn = rk4(xa, s1, s2, dt)
        hit1, hit2 = ell1(xn) <= 0, ell2(xn) <= 0
        hit = hit1 | hit2
        if hit.any():
            h1 = np.full(int(hit.sum()), np.inf)
            h2 = np.full(int(hit.sum()), np.inf)
            sub = np.nonzero(hit)[0]
            m1, m2 = hit1[sub], hit2[sub]
            if m1.any():
                h1[m1] = locate_crossing(xa[sub][m1], s1[sub][m1], s2[sub][m1], dt, ell1)
            if m2.any():
                h2[m2] = locate_crossing(xa[sub][m2], s1[sub][m2], s2[sub][m2], dt, ell2)
            g = ids[sub]
            outcome[g] = classify(h1, h2)
            t_end[g] = t + np.minimum(h1, h2)
            alive[g] = False
        out_dom = ~hit & ~((xn[:, 0] > R_LO_DOM) & (xn[:, 0] < R_HI_DOM))
        if out_dom.any():
            g = ids[out_dom]
            outcome[g] = EXIT
            t_end[g] = t + dt
            alive[g] = False
        x[ids] = xn
    return dict(outcome=outcome, t_end=t_end, x_end=x)


def summarize(outcome):
    return {OUTCOME_NAMES[k]: int(np.sum(outcome == k)) for k in OUTCOME_NAMES}


# ---------------------------------------------------------------------------
# Equivalence with hji.make_policy (criteria Sec. 3.3)
# ---------------------------------------------------------------------------

def assert_matches_make_policy(grid, snaps, n=300, seed=1):
    """
    Compare law_value_p1 / law_value_p2 against hji.make_policy (k_max = every
    snapshot) at random states and times.  Returns (n_compared, n_mismatch_p1,
    n_mismatch_p2, n_mismatch_away_from_ties).
    """
    import hji
    keys = sorted(snaps, key=float)
    taus = np.array([float(k) for k in keys])
    T = float(taus[-1])
    stack = SnapshotStack(Geom(snaps[keys[0]].shape), snaps)
    pol = hji.make_policy(grid, [snaps[k] for k in keys], taus, k_max=len(keys))
    rng = np.random.default_rng(seed)
    x = np.stack([rng.uniform(0.5, 7.0, n), rng.uniform(-np.pi, np.pi, n),
                  rng.uniform(-np.pi, np.pi, n)], -1)
    ts = rng.uniform(0, T, n)
    l1, l2 = law_value_p1(stack, T), law_value_p2(stack, T)
    mm1 = mm2 = hard = 0
    for i in range(n):
        a1, a2 = pol(x[i], ts[i])
        b1 = l1(x[i:i + 1], ts[i], None)[0]
        b2 = l2(x[i:i + 1], ts[i], None)[0]
        k = stack.nearest(T - ts[i])
        g1 = interp(stack.geom, stack.d1[k], x[i:i + 1])[0]
        g2 = interp(stack.geom, stack.d2[k], x[i:i + 1])[0]
        if a1 != b1:
            mm1 += 1
            hard += abs(g1) > 1e-5
        if a2 != b2:
            mm2 += 1
            hard += abs(g2) > 1e-5
    return n, mm1, mm2, hard
