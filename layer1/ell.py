"""
ell.py -- Layer 1, M1.  The implicit surface function for T_{1->2}.

Layer1_Plan.md Sec. 2.1.  The target set (ProblemStatement Sec. 3.2, D&S Eqs. 6-9)
is the intersection of three constraints, so the natural implicit surface function
is their max:

    g_bore(x) = |phi_1| - beta                 boresight limit
    g_min(x)  = R_lo(phi_2) - R                minimum firing range
    g_max(x)  = R - R_hi(phi_2)                no-escape (maximum) range

    ell(x) = max( w_b * g_bore,  w_n * g_min,  w_x * g_max )

    ell <  0   strictly inside  T_{1->2}
    ell == 0   on its boundary
    ell >  0   outside

The weights w are strictly positive, so THE SIGN AND THE ZERO LEVEL SET ARE
INDEPENDENT OF THEM.  The reachable set, the barrier and acceptance tests A-E are
therefore invariant to the choice (Plan Sec. 2.1); only conditioning and the
numerical interpretation of a nonzero value change.  `SCALING` selects the weights.

NOT a signed distance under any of these choices -- an implicit surface function
only.  Level-set methods accept either.

Two Lipschitz kinks are GEOMETRY, not defects, and must not be smoothed away
(Plan Sec. 3, trap 3):
  * R_hi(phi) = Rbar_0 - |phi + sin phi| has a corner at phi = 0.  This is where
    D&S's own corner equations (38)-(42) live.
  * the max of three constraints has corners along every edge of the target set.
A third kink, at phi_1 = +/- pi, is the antipode of the boresight axis: it is the
correct angular distance to the boresight cone on the circle, and it sits far
outside the target set.

UNITS (Plan Sec. 2.1).  g_bore is a radian; g_min and g_max are normalized
lengths.  Their max is not a distance, so a nonzero value is a WEAPON-ENVELOPE
MARGIN in mixed units, not a "terminal miss" in the missile-guidance sense.  Do
not quote it as a distance in the report.

The module is written once against a generic array module `xp` and exposed twice,
in numpy (for comparison against layer0) and jax.numpy (for the solver), so the
two cannot drift apart.
"""

import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'layer0'))
import barrier as B

# Parameters are taken from layer0/barrier.py, never re-entered here.  Rbar_0 in
# particular is 3 + pi and not the 6.14 that D&S Sec. 4 quotes (ProblemStatement
# Sec. 3.2); re-declaring it would be a way to lose that correction.
BETA = B.BETA
A1 = B.A1
B1 = B.B1
RBAR0 = B.RBAR0

# ---------------------------------------------------------------------------
# Scaling.  See report_conditioning() for the measurement behind the default.
# ---------------------------------------------------------------------------
#
#   'plan'   Plan Sec. 2.1 as written: boresight / beta, both ranges / Rbar_0,
#            so the three terms are comparable dimensionless margins.
#   'raw'    no scaling; what M1 and M2 were originally run with.
#   'sdist'  each constraint divided by the Euclidean norm of its own gradient in
#            (R, phi_1, phi_2), making every term an approximate signed distance
#            to its own surface.
#
# DEFAULT IS 'sdist', WHICH IS A DEVIATION FROM PLAN Sec. 2.1 AS WRITTEN.  It is
# proposed as an amendment, not adopted unilaterally -- revert by changing the
# string below, or by setting LAYER1_ELL_SCALING=plan.  The evidence, all of it
# reproducible from this repo (test_m1.py Sec. 8, cmp_scaling.py):
#
#   Sec. 2.1's GOAL is |grad ell| ~ 1, "because a value function steep in one
#   direction and flat in another resolves the zero level set poorly -- precisely
#   the surface being validated".  That goal is correct.  Its prescribed weighting
#   (boresight/beta, ranges/Rbar_0) does not serve it.  Measured |grad ell| on
#   nodes within 1.0 of the zero level set:
#
#       scaling      p05   median    p95   p95/p05
#       raw        1.000    1.000  1.864      1.9
#       plan       0.163    0.330  1.273      7.8      <- worst of the three
#       sdist      0.861    1.000  1.188      1.4
#
#   Dividing the range terms by Rbar_0 = 6.14 flattens exactly the direction in
#   which the target set is thin.  The raw ell was already reasonably conditioned;
#   the prescription degrades it.
#
#   The consequence is real but small, and it is discretization error rather than
#   a different answer.  Two-player solve, disagreement in the computed {V <= 0}:
#
#       grid     raw vs sdist    plan vs raw    {V<=0} share
#       61^3         0.0079%        0.2079%     raw/sdist 11.565%, plan 11.463%
#       101^3        0.0049%        0.1157%     raw/sdist 11.631%, plan 11.577%
#
#   raw and sdist give the same answer; 'plan' consistently under-resolves the
#   winning zone, and the gap halves under refinement as discretization error
#   should.  'sdist' is also the closed-form version of the eikonal
#   reinitialization Sec. 2.1 itself offers as its fallback, done up front.
#
# What Sec. 2.1 is RIGHT about, and what this keeps: the units argument.  ell mixes
# a radian with two normalized lengths under every choice, so a nonzero value is a
# weapon-envelope margin, never a miss distance.  Nothing here makes it one.
#
SCALING = os.environ.get('LAYER1_ELL_SCALING', 'sdist')


def _weights(xp, phi2):
    """Per-term positive weights for the selected scaling."""
    if SCALING == 'raw':
        one = xp.ones_like(phi2)
        return one, one, one
    if SCALING == 'plan':
        one = xp.ones_like(phi2)
        return one / BETA, one / RBAR0, one / RBAR0
    if SCALING == 'sdist':
        # |grad g_bore| = 1
        # |grad g_min|  = |(-1, 0, -B1 sin phi_2)|
        # |grad g_max|  = |( 1, 0, (1 + cos phi_2) sign(phi_2))|
        one = xp.ones_like(phi2)
        n_min = xp.sqrt(1.0 + (B1 * xp.sin(phi2)) ** 2)
        n_max = xp.sqrt(1.0 + (1.0 + xp.cos(phi2)) ** 2)
        return one, one / n_min, one / n_max
    raise ValueError('unknown SCALING %r' % SCALING)


def _terms(xp, R, phi1, phi2):
    """The three weighted constraint residuals, in order (bore, min, max)."""
    g_bore = xp.abs(phi1) - BETA                                  # |phi_1| <= beta
    R_lo = A1 + B1 * xp.cos(phi2)                                 # Eq. (8)
    R_hi = RBAR0 - xp.abs(phi2 + xp.sin(phi2))                    # Eq. (9)
    g_min = R_lo - R                                              # R >= R_lo
    g_max = R - R_hi                                              # R <  R_hi
    w_b, w_n, w_x = _weights(xp, phi2)
    return w_b * g_bore, w_n * g_min, w_x * g_max


def _ell(xp, R, phi1, phi2):
    a, b, c = _terms(xp, R, phi1, phi2)
    return xp.maximum(a, xp.maximum(b, c))


def ell(R, phi1, phi2):
    """numpy version.  R, phi1, phi2 broadcast."""
    return _ell(np, np.asarray(R, float), np.asarray(phi1, float), np.asarray(phi2, float))


def ell_jax(state):
    """jax version, taking a stacked state vector (..., 3) = (R, phi_1, phi_2)."""
    import jax.numpy as jnp
    return _ell(jnp, state[..., 0], state[..., 1], state[..., 2])


def ell_on_grid(grid):
    """Evaluate ell at every node of an hj_reachability Grid."""
    return ell_jax(grid.states)


def components(R, phi1, phi2):
    """The three weighted residuals separately, for diagnosing which is active."""
    return _terms(np, np.asarray(R, float), np.asarray(phi1, float), np.asarray(phi2, float))


def value_scale(grid, values=None, band=1.0):
    """
    The change in `ell` across one grid cell, maximized over the three axes, over
    cells NEAR the zero level set (|ell| <= band on either side).

    This is the tolerance unit for anything measured in ell units.  It replaces
    "compare against dR", which was only meaningful while ell was unscaled: once
    the terms carry weights, a length and a value are no longer interchangeable.

    The band matters.  Measured over the whole domain the statistic is dominated
    by the far field, where a state-dependent weight multiplies a large residual
    and produces a big per-cell change that has nothing to do with resolving the
    surface: under 'sdist' that inflates it from 0.13 to 0.39, which would loosen
    every M2 tolerance by 3x for no reason.  The comparisons M2 makes live near
    {ell = 0}, so the tolerance is measured there.
    """
    V0 = np.asarray(ell_on_grid(grid) if values is None else values)
    near = np.abs(V0) <= band
    out = 0.0
    for d in range(3):
        dif = np.abs(np.diff(V0, axis=d))
        sel = np.logical_or(np.take(near, np.arange(dif.shape[d]), axis=d),
                            np.take(near, np.arange(1, dif.shape[d] + 1), axis=d))
        if sel.any():
            out = max(out, float(dif[sel].max()))
    return out


def report_conditioning(n=121):
    """
    Measure |grad ell| under each scaling, on the region that matters.

    Plan Sec. 2.1's stated goal is |grad ell| ~ 1, because a value function steep
    in one direction and flat in another resolves the zero level set poorly.  This
    function reports whether a given choice of weights achieves that, rather than
    assuming it.  Returns {scaling: (p05, median, p95, spread)} over nodes within
    one unit of the zero level set.
    """
    global SCALING
    keep = SCALING
    Rg = np.linspace(0.2, 12.0, n)
    Pg = np.linspace(-np.pi, np.pi, n, endpoint=False)
    R, P1, P2 = np.meshgrid(Rg, Pg, Pg, indexing='ij')
    out = {}
    try:
        for s in ('raw', 'plan', 'sdist'):
            SCALING = s
            L = ell(R, P1, P2)
            g = np.stack(np.gradient(L, Rg, Pg, Pg, edge_order=2), -1)
            m = np.linalg.norm(g, axis=-1)
            near = np.abs(L) < 1.0
            v = m[near]
            out[s] = (float(np.percentile(v, 5)), float(np.median(v)),
                      float(np.percentile(v, 95)),
                      float(np.percentile(v, 95) / max(np.percentile(v, 5), 1e-30)))
    finally:
        SCALING = keep
    return out
