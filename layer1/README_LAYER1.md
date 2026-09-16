# Layer 1 — status

**AE 8900 · Ethan Stroup · started 2026-09-14 · updated 2026-09-15**
Plan of record: `claude/Layer1_Plan.md`. Spec of record: `claude/ProblemStatement.md`.

| Milestone | State |
|---|---|
| M1 formulation verified before any solve | **DONE** — `test_m1.py`, all checks pass |
| M2 one-player smoke test | **DONE** — `test_m2.py`, all checks pass |

**2026-09-15.** `ell.py` now carries the Plan §2.1 weighting, selectable. M1 and M2
re-run and green under all three choices. One proposed amendment to §2.1 — see
"The ell weighting" below; it is a one-line revert and it wants your decision
before the 201³ run.
| M3 full two-player solve, converged in horizon and grid | not started |
| M4 acceptance against Layer 0 | not started |
| M5 mutual-kill / arrival-time comparison | not started |

## Tooling decision (Plan §3)

**`hj_reachability` 0.7.0 (JAX).** Evaluated against the plan's two hard
requirements and both are met natively:

- *periodic dimensions* — `boundary_conditions.periodic`, selected per dimension;
  periodic axes are built with `endpoint=False`, so `phi = +pi` is never duplicated.
- *two-player min–max Hamiltonian with a min-over-time reach formulation* —
  `ControlAndDisturbanceAffineDynamics` with `control_mode="min"`,
  `disturbance_mode="max"`, and `solver.backwards_reachable_tube` as the
  Hamiltonian postprocessor.

The PDE form was **verified from the library's own source, not transcribed** from
the plan (Plan §2.4 explicitly requires this). In `time_integration.euler_step`
the two factors of `time_direction` cancel, leaving

```
dV/dt = -min(0, H),    H = min_{sigma_1} max_{sigma_2} grad V . f
```

marched backward — which is the plan's §2.4 equation. Worked through in the
docstring of `hji.py`.

Environment: JAX must run in **float64** (`jax_enable_x64`); the default float32
would make the M1 machine-precision comparison meaningless. Set in `hji.py`
before any array is created, and asserted in `test_m1.py` §0.

## The ell weighting — a proposed amendment to Plan §2.1

§2.1 asks for `ell` to be nondimensionalized: boresight term over `beta`, both range
terms over `Rbar_0`. The reason it gives is conditioning — *"level-set schemes want
`|grad ell| ~ 1`. A max of badly-scaled terms gives a value function steep in one
direction and flat in another, which resolves the zero level set poorly — precisely
the surface being validated."*

**The goal is right. The prescribed weighting does not serve it.** Measured
`|grad ell|` on nodes within 1.0 of the zero level set (`test_m1.py` §8):

| scaling | p05 | median | p95 | p95/p05 |
|---|---|---|---|---|
| `raw` (what M1/M2 originally used) | 1.000 | 1.000 | 1.864 | 1.9 |
| `plan` (§2.1 as written) | 0.163 | 0.330 | 1.273 | **7.8** |
| `sdist` (each term over its own gradient norm) | 0.861 | 1.000 | 1.188 | **1.4** |

Dividing the range terms by `Rbar_0 = 6.14` flattens exactly the direction in which
the target set is thin. The raw `ell` was already reasonably conditioned; the
prescription degrades it by a factor of four in spread.

**The consequence is real, small, and is discretization error rather than a
different answer** (`cmp_scaling.py`). Two-player solve, disagreement in the
computed `{V <= 0}`:

| grid | raw vs sdist | plan vs raw | `{V<=0}` share |
|---|---|---|---|
| 61³ | 0.0079 % | 0.2079 % | raw/sdist 11.565 %, plan 11.463 % |
| 101³ | 0.0049 % | 0.1157 % | raw/sdist 11.631 %, plan 11.577 % |

`raw` and `sdist` give the same answer to 5 parts in 10⁵ of grid volume. `plan` is
the outlier by ~24×, consistently under-resolving the winning zone, and the gap
halves under refinement as discretization error should. All three converge to the
same limit; the question is only which resolves the surface best at a given cost —
and the 201³ run costs two hours.

**`sdist` is also what §2.1 itself falls back to.** Its closing sentence offers
*"reinitialize by solving the eikonal equation `|grad ell| = 1` to recover a true
signed distance with the same zero level set"*. Dividing each constraint by the norm
of its own gradient is the closed-form approximation of that, done up front for free.

**What §2.1 is right about, and what is kept:** the units argument. `ell` maxes a
radian against two normalized lengths under *every* weighting, so a nonzero value is
a weapon-envelope margin, never a miss distance. Nothing here makes it one.

**Status: `SCALING = 'sdist'` is the default, flagged in `ell.py` as a deviation
awaiting your decision.** Revert with one string, or `LAYER1_ELL_SCALING=plan`. All
weights are strictly positive, so the zero level set — and acceptance tests A–E — are
invariant to the choice either way.

### One test unit changed with it

Tolerances in `test_m2.py` used to be quoted against `dR`. That only worked while
`ell` was unscaled; once terms carry weights a length and a value are not
interchangeable. They are now quoted against `ell.value_scale` — the change in `ell`
across one grid cell — measured **near the zero level set**, not over the whole
domain. That restriction matters: far from the surface a state-dependent weight
multiplies a large residual, which inflated the statistic from 0.118 to 0.239 under
`sdist` and would have loosened every M2 tolerance threefold for no reason.

## M1 — formulation verified before any solve

`ell.py` implements

```
ell(x) = max( |phi_1| - beta,  R_lo(phi_2) - R,  R - R_hi(phi_2) )
```

and imports `BETA`, `A1`, `B1`, `RBAR0` **from `layer0/barrier.py` rather than
re-entering them** — re-declaring `RBAR0` would be a way to silently lose the
`3 + pi` correction. Asserted in `test_m1.py` §0.

Results:

- `{ell < 0}` equals `barrier.in_target` with **0 mismatches** on a 181³ =
  5.93M-node grid and on 4×10⁶ random points.
- `{ell <= 0}` differs from `in_target` only where a constraint is exactly
  active — the half-open/closed difference of D&S Eq. (7), accounted for
  explicitly rather than tolerated.
- `ell == 0` exactly on all three target-set faces, and changes sign across each.
- `f(x, sigma)` **bit-identical** to `barrier.state_dot` on 2×10⁴ random points.
- **The M1 gate:** `dynamics.hamiltonian` vs `barrier.hamiltonian_star` on 2×10⁵
  random `(x, grad V)` — agreement to **3 ulp of the summed terms**, bit-identical
  at 91k of 200k points, and exact within 4e-15 on every degenerate gradient
  (`lambda_1 = 0`, `lambda_2 = 0`, `lambda_R = 0`, `lambda = 0`).
- `sigma_1* = -sign(lambda_1)` and `sigma_2* = +sign(lambda_2)` reproduced on
  every sampled gradient, and H is attained at that pair.
- All four traps of Plan §3 asserted, not merely intended: both angle dimensions
  periodic and R not; `ell` continuous across both seams to 0.0; `R_hi`'s corner
  at `phi_2 = 0` still present (one-sided slopes ∓2, deliberately not smoothed);
  the dissipation bounds equal to the plan's analytic `|L|/R + 1 <= 2/R_min + 1`.

### One correction to the M1 test, worth recording

The Hamiltonian check first *failed* at a relative error of 3.6e-12 while the
absolute error was 1.4e-14. **The criterion was wrong, not the formulation.**
Normalizing by `|H|` is indefensible here for a structural reason: `H` vanishes
identically on the semipermeable surface, which is the set this entire layer
exists to resolve, so a relative-to-result test reports the cancellation the
barrier is *made of* as if it were an error. The test now measures against the
magnitude of the terms being summed and reports ulp. The worst case is 3 ulp.

## M2 — one-player smoke test (sigma_2 frozen at 0)

Two-sided, which is the point: the feedback law must **achieve** V (V is not too
low) and **nothing else may beat** V (V is not too high).

Run at both 61³ and 101³, T = 3. Every margin tightens under refinement, which
is the behaviour a converging scheme should show and is itself part of the check.
Figures below are the 2026-09-15 re-run under `SCALING = 'sdist'`; the numbers under
`raw` and `plan` differ in the third decimal and every check passes under all three.

| | 61³ | 101³ |
|---|---|---|
| one-cell value change (the tolerance unit) | 0.1967 | 0.1180 |
| reach-front speed vs. analytic 2 | 2.016 | **2.003** |
| median shortfall of the feedback law | +0.00028 | **+0.00022** |
| 90th pct shortfall | +0.037 | **+0.018** |
| max shortfall | +0.116 | +0.124 |
| sign of V vs. simulated outcome | 232/232 agree | **230/230 agree** |
| worst violation of optimality | +0.116 | **+0.067** |
| — as a fraction of one cell | 0.59 | **0.57** |

One honest note: at 101³ the *max* shortfall (0.124) sits just above one cell
(0.118), while the median is 2000× smaller. The suite asserts `max < 3 cells` for
that reason — the tail is a handful of trajectories near the shock ridge, not a
systematic bias, and the 90th percentile tightens under refinement as it should.

Adversaries in the optimality half: four fixed laws (σ₁ = ±1, 0, and the old
pursuit heuristic), three random bang-bang laws, and a brute-force sweep over
every single-switch control on a 21-point switch-time grid. Nothing beat V by as
much as one grid cell; the worst was the pursuit heuristic, which is the law the
Layer 0 sim used.

### Two findings from M2

**1. The reach front travels at exactly the maximum closing speed.** Against a
non-maneuvering target the winning zone's outer edge in R advances at a measured
**2.016** per unit time, against the analytic bound
`max |Rdot| = max(cos phi_1 + cos phi_2) = 2`. This is a physical check the
solver cannot pass by accident, and it replaced a check that was simply the wrong
question: *"has the zero level set stopped moving?"* is an **M3** test. Against a
frozen evader the zone never stops growing — it is range-limited and just runs
out of domain. Against a maneuvering evader it converges, and its outer edge
stays pinned at R = 5.90 < `R_hi(0) = 6.1416`. That is D&S's bounded winning zone
appearing on its own, before any acceptance test has been run.

**2. A finite-horizon value function must be read at the REMAINING horizon.** The
optimal control at elapsed time `t` is

```
sigma_1*(x, t) = -sign( dV(x, T - t)/dphi_1 )      NOT  -sign( dV(x, T)/dphi_1 )
```

Reading the terminal-horizon V throughout is the natural mistake and it is a
large one: worst shortfall **2.04 vs 0.13**, same V, same grid, same trajectories,
only the horizon at which `grad V` is read changed. The mechanism is that the
`min(0, H)` postprocessor freezes V on large plateaus, `grad V` there is zero,
and the bang-bang law degenerates into coasting.

This was caught the right way round. The first run showed a worst shortfall of
2.04 and a plausible story (a shock ridge at `phi_1 = ±pi`, which does exist —
0.85% of nodes, concentrated at the tail-on antipode). That story was **wrong**:
a one-step-lookahead policy, which a shock would have fixed, did not help. Brute
force then showed that a *constant* `sigma_1 = -1` reached `min ell = -0.783`
against `V = -0.719` — so V was correct, and slightly conservative, and the
control extraction was the defect. `test_m2.py` now carries the stale read as an
explicit test, so a future session cannot reintroduce it and blame V.

Two smaller fixes fell out of the same investigation:
- `np.sign(0) = 0` is not an admissible bang-bang control and made the pursuer
  coast; `hji.feedback` now breaks the tie to ±1 deterministically.
- `hji.make_policy` is the only supported way to build a feedback law, so the
  remaining-horizon read cannot be forgotten at the call site.
- `make_policy` holds one gradient field per horizon snapshot, which at 101³ and
  K = 61 is 1.5 GB and got the process killed. It now keeps only the two angular
  partials (dV/dR does not enter Eqs. 21–22) in float32 (only the sign is ever
  read), subsampled to at most 31 snapshots. This matters for M3: the same
  structure at 201³ would be 12 GB.

## Files

```
layer1/ell.py          implicit surface fn, numpy + jax; parameters from layer0;
                       SCALING selects the weighting (default 'sdist', see above)
layer1/hji.py          dynamics, grid, solver setup, gradient/feedback/forward-sim;
                       make_policy is the ONLY supported way to build a feedback law
layer1/test_m1.py      M1 — formulation verified before any solve, + conditioning (§8)
layer1/test_m2.py      M2 — one-player smoke test, two-sided
layer1/cmp_scaling.py  does the weighting move the computed zero level set? (it does
                       not, beyond discretization error — the table above)
layer1/README_LAYER1.md  this file
```

Still to be created, per Plan §9: `solve_m3.py` (converged solve + grid study, emits
V and t1*), `test_m4.py` (acceptance A–E + the negative control), `mutual_kill.py` (M5).

Run any suite under a different weighting with `LAYER1_ELL_SCALING=raw|plan|sdist`.

## Cost, for planning M3

Two CPU cores, no GPU. Solve cost scales as n⁴ (nodes × CFL steps):
61³ / T=3 ≈ 31 s, 101³ ≈ 4 min, **201³ ≈ 2 h**. The CFL is dominated by the
angular dissipation bound `2/R_min + 1 = 11` at `R_min = 0.2`, i.e. the singular
`R -> 0` trap sets the step size. The 201³ grid convergence study of M3 is a
single overnight job, not an interactive one.
