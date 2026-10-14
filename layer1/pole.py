"""
pole.py -- the inner face as a pole: states "below R = 0" are the flipped states above it.

When the two aircraft pass through each other, range goes through zero and the line of
sight turns by pi.  So
        (-R, phi_1, phi_2)  ==  (R, phi_1 + pi, phi_2 + pi),
and D&S's Eqs. (1)-(3) respect that exactly (with R' = -R, phi' = phi + pi, both cos and
sin change sign; the controls are unchanged).  This replaces the extrapolation condition
at R_min with what the model actually says happens on a pass.

GRID.  R is staggered so that R = 0 is never a node: real rows at (i + 1/2) dR, plus
`n_ghost` rows below zero at -(1/2) dR, -(3/2) dR, ...  Ghost row k is the mirror of real
row 2*n_ghost - 1 - k with both angles shifted by n_phi/2 indices (n_phi must be even), so
the identification is index-exact, with no interpolation.

WHY GHOST ROWS AND NOT A BOUNDARY FUNCTION.  hj_reachability applies boundary conditions to
one 1-D slice at a time, so a boundary function cannot fetch values at the opposite angles.
The ghost rows are ordinary grid rows (the dynamics are already correct at negative R) and are
overwritten with the mirrored values after every time step, through the same
value_postprocessor hook the reach-avoid obstacle uses.  Within one Runge-Kutta step they are
one step stale -- the same placement compromise as the obstacle.

COST.  The CFL step is set by the innermost rows, |R| = dR/2 (see the CFL note in the M5
explainer): about 3x today's at 101x102^2 and 6x at 201x204^2.
"""

import numpy as np
import jax.numpy as jnp

import hji
import hj_reachability as hj
import sim_m5 as SIM

N_GHOST = 3          # WENO5 needs three cells on each side of a node


# ---------------------------------------------------------------------------
# Grid and the mirror map
# ---------------------------------------------------------------------------

def spacing(n_R, R_max=hji.R_MAX_DEFAULT):
    """dR such that real rows sit at (i + 1/2) dR, i = 0 .. n_R - 1, with the last at R_max."""
    return R_max / (n_R - 0.5)


def make_grid(n_R, n_phi, R_max=hji.R_MAX_DEFAULT, n_ghost=N_GHOST):
    """Pole grid: n_ghost mirror rows below zero, then n_R real rows up to R_max."""
    if n_phi % 2:
        raise ValueError('the pole map needs an even n_phi (phi + pi must be an index shift)')
    dR = spacing(n_R, R_max)
    lo = -(n_ghost - 0.5) * dR
    domain = hj.sets.Box(lo=np.array([lo, -np.pi, -np.pi]), hi=np.array([R_max, np.pi, np.pi]))
    bcs = (hj.boundary_conditions.extrapolate,
           hj.boundary_conditions.periodic,
           hj.boundary_conditions.periodic)
    return hj.Grid.from_lattice_parameters_and_boundary_conditions(
        domain, (n_R + n_ghost, n_phi, n_phi), boundary_conditions=bcs)


def mirror_rows(v, n_ghost=N_GHOST):
    """The values the ghost rows must hold: real rows 2g-1 .. g, angles shifted by pi."""
    half = v.shape[1] // 2
    src = v[2 * n_ghost - 1:n_ghost - 1:-1]
    return jnp.roll(jnp.roll(src, half, axis=1), half, axis=2)


def fill(v, n_ghost=N_GHOST):
    """Overwrite the ghost rows with the mirrored real rows."""
    return jnp.asarray(v).at[:n_ghost].set(mirror_rows(jnp.asarray(v), n_ghost))


def strip(v, n_ghost=N_GHOST):
    """Real rows only."""
    return np.asarray(v)[n_ghost:]


def geom(grid):
    """sim_m5 geometry for the full pole grid, ghost rows included (so interpolation near R = 0
    reads the mirrored values)."""
    R = np.asarray(grid.coordinate_vectors[0])
    return SIM.Geom(tuple(grid.shape), R_min=float(R[0]), R_max=float(R[-1]))


# ---------------------------------------------------------------------------
# Solver settings with the pole
# ---------------------------------------------------------------------------

def reach_avoid_settings(ell2, accuracy='very_high'):
    """M5's update (tube clamp, then the obstacle) followed by the pole fill, every step."""
    obstacle = -ell2
    return hj.SolverSettings.with_accuracy(
        accuracy,
        hamiltonian_postprocessor=hj.solver.backwards_reachable_tube,
        value_postprocessor=lambda t, v: fill(jnp.maximum(v, obstacle)))


def fisac_settings(ell1, ell2, accuracy='very_high'):
    """Fisac's Algorithm 1 written out literally (smoke check 1b), followed by the pole fill."""
    obstacle = -ell2
    return hj.SolverSettings.with_accuracy(
        accuracy,
        hamiltonian_postprocessor=hj.solver.identity,
        value_postprocessor=lambda t, v: fill(jnp.maximum(jnp.minimum(v, ell1), obstacle)))


def single_target_settings(accuracy='very_high'):
    """M3's update followed by the pole fill."""
    return hj.SolverSettings.with_accuracy(
        accuracy,
        hamiltonian_postprocessor=hj.solver.backwards_reachable_tube,
        value_postprocessor=lambda t, v: fill(v))


def ghost_residual(v, n_ghost=N_GHOST):
    """max |ghost - mirror|: zero whenever the fill has been applied."""
    v = jnp.asarray(v)
    return float(jnp.max(jnp.abs(v[:n_ghost] - mirror_rows(v, n_ghost))))


# ---------------------------------------------------------------------------
# The same identity for forward simulation
# ---------------------------------------------------------------------------

def flip(x):
    """Rows with R < 0 become (-R, phi_1 + pi, phi_2 + pi)."""
    neg = x[:, 0] < 0
    if neg.any():
        x = x.copy()
        x[neg, 0] = -x[neg, 0]
        x[neg, 1] = SIM.wrap(x[neg, 1] + np.pi)
        x[neg, 2] = SIM.wrap(x[neg, 2] + np.pi)
    return x


def substeps(x, h, max_turn=0.05, cap=400):
    """
    Substeps per row so that the line of sight turns by at most `max_turn` per substep.
    The rate |L|/R + 1 is taken at the closest the row can get within the step
    (R shrinks by at most 2h), so the count does not undershoot on a close pass.
    """
    L = np.abs(np.sin(x[:, 1]) + np.sin(x[:, 2]))
    R_eff = np.maximum(np.abs(x[:, 0]) - 2 * h, 0.02)
    return np.clip(np.ceil(h * (L / R_eff + 1) / max_turn), 1, cap).astype(int)


def stepper(x, s1, s2, h):
    """RK4 over one control interval, sub-stepped near R = 0, flipping any row that passes through it."""
    m = substeps(x, h)
    if m.max() == 1:
        return flip(SIM.rk4(x, s1, s2, h))
    y = x.copy()
    hs = h / m
    for k in range(int(m.max())):
        act = k < m
        y[act] = flip(SIM.rk4(y[act], s1[act], s2[act], hs[act]))
    return y


# ---------------------------------------------------------------------------
# Checks on the construction itself
# ---------------------------------------------------------------------------

def dynamics_equivariance(n=200000, seed=0):
    """
    max |f(Mx; s) - M_* f(x; s)| over random states and controls, where
    M: (R, phi_1, phi_2) -> (-R, phi_1 + pi, phi_2 + pi) and M_* negates only R-dot.
    Zero up to rounding if the pole identification is a symmetry of the dynamics.
    """
    rng = np.random.default_rng(seed)
    x = np.stack([rng.uniform(0.01, 12, n), rng.uniform(-np.pi, np.pi, n), rng.uniform(-np.pi, np.pi, n)], -1)
    s1, s2 = rng.uniform(-1, 1, n), rng.uniform(-1, 1, n)
    Mx = np.stack([-x[:, 0], x[:, 1] + np.pi, x[:, 2] + np.pi], -1)
    a = SIM.f(Mx, s1, s2)
    b = SIM.f(x, s1, s2) * np.array([-1.0, 1.0, 1.0])
    return float(np.max(np.abs(a - b) / (1 + np.abs(b))))
