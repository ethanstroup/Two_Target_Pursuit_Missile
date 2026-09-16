"""
hji.py -- Layer 1, M2-M3.  HJI reachability solve for the D&S 1v1 game of degree.

Layer1_Plan.md Secs. 2-3.

WHAT IS SOLVED
--------------
    V(x,T) = min_{sigma_1} max_{sigma_2} min_{t in [0,T]} ell(x(t))

the deepest penetration of player 1's weapon envelope that player 1 can
guarantee within horizon T, against player 2's best evasion.  Zero level set =
the Layer 0 barrier; {V <= 0} = player 1's winning zone within time T.

THE PDE, VERIFIED AGAINST THE LIBRARY RATHER THAN TRANSCRIBED
-------------------------------------------------------------
Layer1_Plan Sec. 2.4 quotes the min-over-time reach form

    dV/dt + min[0, H(x, grad V)] = 0,   V(x,0) = ell(x)

and instructs that it be verified against the reference before being relied on.
Done, by reading hj_reachability 0.7.0's own source (this is the check, not a
restatement of the plan):

  solver.py      backwards_reachable_tube = lambda x: jnp.minimum(x, 0),
                 installed as `hamiltonian_postprocessor`.
  time_integration.euler_step
                 time_direction = sign(time_step);  for a backward solve the
                 target times decrease so time_direction = -1.
                 signed_hamiltonian = time_direction * dynamics.hamiltonian
                 dvalues_dt = -postprocessor(time_direction * LF(signed_ham))
                 The two factors of time_direction cancel:
                     dvalues_dt = -min(0, H)
                 which is dV/dt + min(0,H) = 0 exactly.  Then
                     values <- values + time_step * dvalues_dt
                 with time_step < 0, i.e. marched backward.  Confirmed.
  dynamics.Dynamics.hamiltonian
                 H = grad_value @ f(x, u*, d*) with u* minimizing and d*
                 maximizing when control_mode="min", disturbance_mode="max".

So the library's H is min_{sigma_1} max_{sigma_2} grad V . f, which is
barrier.hamiltonian_star with lambda := grad V.  test_m1.py asserts that
numerically at machine precision rather than taking it on trust.

SIGN CONVENTION
---------------
D&S's, phi_dot = LOS rate + sigma (ProblemStatement Sec. 2).  Under the opposite
convention every control law flips sign.  The dynamics below are copied in
structure from barrier.state_dot and cross-checked against it in test_m1.py.
"""

import jax
jax.config.update("jax_enable_x64", True)   # must precede any array creation

import jax.numpy as jnp
import numpy as np

import hj_reachability as hj

import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', 'layer0'))
sys.path.insert(0, _HERE)

import barrier as B
import ell as E


class TwoTargetPursuit(hj.ControlAndDisturbanceAffineDynamics):
    """
    D&S reduced 1v1 dynamics, state x = (R, phi_1, phi_2):

        Rdot      = -(cos phi_1 + cos phi_2)                       Eq. (1)
        phi_1 dot = (sin phi_1 + sin phi_2)/R + sigma_1            Eq. (2)
        phi_2 dot = (sin phi_1 + sin phi_2)/R + sigma_2            Eq. (3)

    Player 1 is the `control` and MINIMIZES the value (drives the state into its
    own weapon envelope, where ell < 0).  Player 2 is the `disturbance` and
    MAXIMIZES.  This is the assignment that makes

        H(x,p) = min_{sigma_1} max_{sigma_2} p.f
               = -p_R (cos phi_1 + cos phi_2) + (p_1+p_2) L/R - |p_1| + |p_2|

    identical to barrier.hamiltonian_star.
    """

    def __init__(self, max_turn_rate=1.0, control_mode="min", disturbance_mode="max"):
        self.max_turn_rate = max_turn_rate
        control_space = hj.sets.Box(jnp.array([-max_turn_rate]), jnp.array([max_turn_rate]))
        disturbance_space = hj.sets.Box(jnp.array([-max_turn_rate]), jnp.array([max_turn_rate]))
        super().__init__(control_mode, disturbance_mode, control_space, disturbance_space)

    def open_loop_dynamics(self, state, time=0.0):
        R, p1, p2 = state[0], state[1], state[2]
        L = jnp.sin(p1) + jnp.sin(p2)
        C = jnp.cos(p1) + jnp.cos(p2)
        return jnp.array([-C, L / R, L / R])

    def control_jacobian(self, state, time=0.0):
        # sigma_1 enters phi_1 dot only
        return jnp.array([[0.0], [1.0], [0.0]])

    def disturbance_jacobian(self, state, time=0.0):
        # sigma_2 enters phi_2 dot only
        return jnp.array([[0.0], [0.0], [1.0]])


class FrozenEvader(TwoTargetPursuit):
    """
    M2 smoke test: sigma_2 == 0, a non-maneuvering target.  The problem collapses
    to single-player reachability, checkable against direct forward simulation.
    """

    def disturbance_jacobian(self, state, time=0.0):
        return jnp.array([[0.0], [0.0], [0.0]])


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

R_MIN_DEFAULT = 0.2     # below min R_lo = a - b = 0.25, so below the target set
R_MAX_DEFAULT = 12.0    # target set tops out at R_hi(0) = 6.1416; L0 reaches ~7


def make_grid(n_R=101, n_phi=101, R_min=R_MIN_DEFAULT, R_max=R_MAX_DEFAULT):
    """
    Grid over (R, phi_1, phi_2).

    Trap 1 of Layer1_Plan Sec. 3: BOTH angle dimensions are periodic.  Getting
    this wrong produces a plausible-but-wrong barrier rather than an obvious
    failure, so it is asserted in test_m1.py rather than merely intended.

    Trap 2: R -> 0 is singular (the L/R terms blow up).  R_min = 0.2 keeps the
    domain off it and the inner face uses linear extrapolation (outflow), not
    periodic and not Dirichlet.  Both R faces lie entirely outside the target
    set with ell growing linearly in R, which is exactly what linear
    extrapolation reproduces.

    Periodic dimensions are constructed with endpoint=False by the library, so
    the phi coordinate vectors run [-pi, pi) and phi = +pi is never duplicated.
    """
    domain = hj.sets.Box(lo=np.array([R_min, -np.pi, -np.pi]),
                         hi=np.array([R_max, np.pi, np.pi]))
    bcs = (hj.boundary_conditions.extrapolate,
           hj.boundary_conditions.periodic,
           hj.boundary_conditions.periodic)
    return hj.Grid.from_lattice_parameters_and_boundary_conditions(
        domain, (n_R, n_phi, n_phi), boundary_conditions=bcs)


def make_solver_settings(accuracy="very_high"):
    """Min-over-time reach: the Hamiltonian is clamped at zero from above."""
    return hj.SolverSettings.with_accuracy(
        accuracy, hamiltonian_postprocessor=hj.solver.backwards_reachable_tube)


def solve_backward(dynamics, grid, times, initial_values=None, accuracy="very_high",
                   progress_bar=False):
    """
    Marches V backward from V(x,0) = ell(x).

    `times` must be non-increasing and start at 0.0, e.g. -np.linspace(0, T, k).
    Returns an array of shape (len(times),) + grid.shape.
    """
    times = jnp.asarray(times)
    if initial_values is None:
        initial_values = E.ell_on_grid(grid)
    ss = make_solver_settings(accuracy)
    return hj.solve(ss, dynamics, grid, times, initial_values, progress_bar=progress_bar)


# ---------------------------------------------------------------------------
# Reading a solved V back: gradients, the feedback law, and forward simulation.
# Used by M2 (smoke test) and M4 (acceptance tests B and C).
# ---------------------------------------------------------------------------

def grad_field(grid, values):
    """Central-difference grad V on the grid, shape grid.shape + (3,)."""
    return grid.grad_values(values)


def make_interp(grid, field):
    """Multilinear interpolator for a grid-shaped field, periodic in phi_1, phi_2."""
    f = jax.jit(lambda x: grid.interpolate(field, x))
    return lambda x: np.asarray(f(jnp.asarray(x, dtype=jnp.float64)))


def feedback(grad):
    """
    D&S Eqs. (21)-(22), read off grad V:
        sigma_1* = -sign(dV/dphi_1)     player 1 minimizes
        sigma_2* = +sign(dV/dphi_2)     player 2 maximizes
    This is the same law as barrier.barrier_controls with lambda := grad V, but
    global rather than restricted to barrier trajectories -- the stated purpose
    of this layer.

    Tie-break: numpy's sign(0) is 0, which is not an admissible bang-bang control
    and makes the pursuer coast.  Where a partial vanishes exactly, either
    extreme gives the same Hamiltonian to first order, so the tie is broken to
    +1 deterministically.  (barrier.barrier_controls breaks the same tie using
    the costate derivative; that information is not available pointwise from a
    grid, and it is not needed, because a vanishing partial on the grid is a
    plateau rather than the isolated BUP zero the costate version handles.)
    """
    s1 = -np.where(grad[..., 1] >= 0, 1.0, -1.0)
    s2 = np.where(grad[..., 2] >= 0, 1.0, -1.0)
    return s1, s2


def make_policy(grid, values_stack, taus, freeze_p1=False, freeze_p2=False, k_max=31):
    """
    The feedback law of a FINITE-HORIZON value function, read at the REMAINING
    horizon.

    This is the one piece of Layer 1 that is easy to get wrong in a way the
    invariants do not catch, so it is written out.  `solve_backward` returns
    V(., tau) for tau = 0 .. T, and V(., T) is the value with a full T of time
    left.  A trajectory that has already run for t has only T - t left, so its
    optimal control is

        sigma_1*(x, t) = -sign( dV(x, T - t) / dphi_1 )

    NOT -sign(dV(x,T)/dphi_1).  Using the terminal-horizon V throughout is wrong
    wherever V has stopped evolving -- the min-over-time postprocessor
    min(0, H) freezes V on large plateaus, grad V there is zero, and the law
    degenerates into coasting.  Measured on the M2 sample: reading V(.,T)
    throughout leaves a worst shortfall of 2.04 against V, reading V(., T-t)
    leaves 0.12, i.e. under one grid cell.  Same V, same grid; only the read
    changed.

    `taus` must be the increasing retrograde times (taus[0] = 0), matching
    values_stack along its first axis.

    MEMORY.  One gradient field is grid.size * 3 * 8 bytes, 25 MB at 101^3, so one
    per horizon snapshot is 1.5 GB at K = 61 and gets the process killed.  Two
    reductions, neither of which costs the control anything:
      * only the two ANGULAR partials are kept -- dV/dR does not enter Eqs. (21)-(22);
      * they are stored as float32, because only their SIGN is ever read.
    The stack is subsampled to at most `k_max` snapshots.  Snapshot spacing of
    0.1 in retrograde time is finer than any switch this grid can resolve.
    """
    taus = np.asarray(taus, float)
    T = float(taus[-1])
    if len(values_stack) > k_max:
        sel = np.unique(np.linspace(0, len(values_stack) - 1, k_max).round().astype(int))
    else:
        sel = np.arange(len(values_stack))
    tau_sel = taus[sel]
    K = len(sel)

    interps = []
    for i in sel:
        g = np.asarray(grad_field(grid, jnp.asarray(values_stack[i])))[..., 1:]
        interps.append(make_interp(grid, jnp.asarray(g, dtype=jnp.float32)))

    def sigma_fn(x, t):
        k = int(np.argmin(np.abs(tau_sel - (T - t))))
        g = interps[k](x)
        if not np.all(np.isfinite(g)):
            return 0.0, 0.0
        s1 = -1.0 if g[0] >= 0 else 1.0        # sigma_1* = -sign(dV/dphi_1)
        s2 = 1.0 if g[1] >= 0 else -1.0        # sigma_2* = +sign(dV/dphi_2)
        return (0.0 if freeze_p1 else s1), (0.0 if freeze_p2 else s2)

    return sigma_fn


def make_static_policy(grid, values, freeze_p1=False, freeze_p2=False):
    """
    The same law read from ONE value snapshot at every time.  This is the wrong
    thing for a finite-horizon problem (see make_policy) and exists so that
    test_m2.py can measure how wrong, rather than assert it.
    """
    g = np.asarray(grad_field(grid, jnp.asarray(values)))[..., 1:]
    gi = make_interp(grid, jnp.asarray(g, dtype=jnp.float32))

    def sigma_fn(x, t):
        gg = gi(x)
        if not np.all(np.isfinite(gg)):
            return 0.0, 0.0
        s1 = -1.0 if gg[0] >= 0 else 1.0
        s2 = 1.0 if gg[1] >= 0 else -1.0
        return (0.0 if freeze_p1 else s1), (0.0 if freeze_p2 else s2)

    return sigma_fn


def forward_sim(x0, sigma_fn, T, dt=2e-3, R_min=R_MIN_DEFAULT, R_max=R_MAX_DEFAULT):
    """
    RK4 forward from x0 under a (possibly state- and time-dependent) control pair.

    `sigma_fn(x, t) -> (sigma_1, sigma_2)`.  The control is FROZEN over a step,
    for the same reason barrier.integrate_retrograde freezes it: a bang-bang law
    re-read by each RK4 stage smears every switch over a whole step.

    Returns dict with the trajectory, the running ell, min_t ell, and whether the
    trajectory left the R domain (outside which the grid solution is only an
    outflow approximation and the reported minimum is a within-domain one).
    """
    x = np.array(x0, dtype=float)
    xs = [x.copy()]
    ts = [0.0]
    ells = [float(E.ell(x[0], x[1], x[2]))]
    t = 0.0
    exited = False

    def f(y, s1, s2):
        Rd, p1d, p2d = B.state_dot(y[0], y[1], y[2], s1, s2)
        return np.array([Rd, p1d, p2d])

    nsteps = int(round(T / dt))
    for _ in range(nsteps):
        s1, s2 = sigma_fn(x, t)
        k1 = f(x, s1, s2)
        k2 = f(x + 0.5 * dt * k1, s1, s2)
        k3 = f(x + 0.5 * dt * k2, s1, s2)
        k4 = f(x + dt * k3, s1, s2)
        x = x + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        x[1] = float(B.wrap(x[1]))
        x[2] = float(B.wrap(x[2]))
        t += dt
        xs.append(x.copy()); ts.append(t)
        ells.append(float(E.ell(x[0], x[1], x[2])))
        if not (R_min < x[0] < R_max):
            exited = True
            break

    ells = np.array(ells)
    return dict(t=np.array(ts), x=np.array(xs), ell=ells,
                min_ell=float(ells.min()), exited=exited,
                t_arrive=(float(np.array(ts)[np.argmax(ells <= 0)]) if (ells <= 0).any() else np.inf))
