# Layer 1 — status

**AE 8900 · Ethan Stroup · started 2026-09-14 · updated 2026-10-28**

**Layer 1 is closed (2026-10-15).** The summary is `Overview/Layer1/Layer1_CloseOut_2026-10-15.md`,
and what Layer 2 receives is its §3. The status entries below are kept as they were written.
Plan of record: `Overview/Layer1/Layer1_Plan.md`. Spec of record: `Overview/ProblemStatement.md`.

## Layout (reorganized 2026-10-14)

```
layer1/
  common/   ell.py, hji.py -- shared by every milestone; hji puts layer0/common/ on sys.path
  M1/       formulation gate: test_m1.py, cmp_scaling.py
  M2/       one-player smoke test: test_m2.py, solve_m2_snap.py, m2_out/
  M3/       two-player solve: solve_m3.py, grid_study.py, zone_structure.py, win_alone.py,
            sym_test.py, m3_out/
  M4/       acceptance against Layer 0: test_m4.py, l0_traj.py, test_e_table3.py,
            m4_out/ (the m4_*.log runs, test E's logs)
  M4/diag/  report-only diagnostics for test E (diag_table3_misses.py)
  M5/       reach-avoid partition and inner face: reach_avoid.py, sim_m5.py, smoke_m5.py,
            test_m5.py, converse_m5.py, pole.py, inertial.py, verify_pole.py, run_m5_pole.py,
            c2_longrange.py, m5_out/
  M5/diag/  report-only diagnostics (diag_*.py)
  M5/m5_out/m5_out_V0/       the original R_min = 0.2 M5 outputs
  M5/m5_out/m5_out_V1_pole/  the pole rerun's outputs, of record (fields, json, snapshots,
                             pole_run/ logs, C2 long range, test E)
  viz/      ell_explorer.html
```

**Run every script from its own milestone folder** (`cd layer1/M3; python solve_m3.py ...`),
as everything was once run from `layer1/`: each milestone writes its outputs to its own
`m<k>_out/` relative to the working directory. The diagnostics run from `M5/` as
`python diag/diag_<name>.py`, so they find `m5_out/`. Each script adds `common/` (and the
diagnostics `M5/`) to `sys.path` itself. M4 and M5 read M3's fields from `../M3/m3_out/`.
The scripts added at close-out (`c2_longrange.py`, `diag/diag_pole_rerun.py`, `test_e_table3.py`,
`M4/diag/diag_table3_misses.py`) read the pole fields from `m5_out/m5_out_V1_pole/` by default.
`test_m5.py` and `converse_m5.py` still read `m5_out/` directly; to rescore, move the pole outputs
back there or point `OUT` at `m5_out/m5_out_V1_pole`.

| Milestone | State |
|---|---|
| M1 formulation verified before any solve | **DONE** — `test_m1.py`, all checks pass |
| M2 one-player smoke test | **DONE** — `test_m2.py`, all checks pass |

**2026-09-15.** `ell.py` now carries the Plan §2.1 weighting, selectable. M1 and M2
re-run and green under all three choices. One proposed amendment to §2.1 — see
"The ell weighting" below; it is a one-line revert and it wants your decision
before the 201³ run.
| M3 full two-player solve, converged in horizon and grid | **DONE** — `solve_m3.py` + `grid_study.py`, all checks pass |
| M4 acceptance against Layer 0 | **DONE** 2026-10-07 — `M4/test_m4.py`; `Overview/Layer1/Layer1_M4_2026-10-06.md` |
| M5 two-target partition by reach-avoid (redefined 2026-10-01) | **DONE** 2026-10-11; rerun on the pole grids 2026-10-15, of record — `Overview/Layer1/Layer1_M5_PoleRerun_2026-10-15.md` |
| Test C2 at long range | **PASS** 2026-10-15 — `M5/c2_longrange.py`; `Overview/Layer1/Layer1_C2LongRange_2026-10-15.md` |
| Test E against D&S Table 3 (after close-out) | **FAIL by one hit** 2026-10-28 (6 of 9, bar 7; $P=1.6\times10^{-4}$) — `M4/test_e_table3.py`; `Overview/Layer1/Layer1_TestE_Table3_2026-10-28.md` |

**2026-10-01. M2's frozen-evader V is not valid everywhere — open, needs a decision.**
V is a minimum of `ell` along a trajectory, so `V >= min ell = -beta` always. The
frozen-evader solve breaks that from τ ≈ 0.75 on: it starts at the inner face
R = 0.2 near φ₁ = φ₂ = 0 (nose-on, closing, i.e. leaving through that face) and
grows without limit (min V = −1.45e4 at T = 3 in M2's own 101³ configuration; 3.3 %
of nodes more than 0.05 below −β, out to R = 5.3). None of `test_m2.py`'s checks can
see it: none bounds V from below, and the trajectory tests drop every sample that
leaves the R domain. M3 does not do this (min V −0.802). Found while building
`solve_m2_snap.py` for the explorer, which reports the bound as a failing check;
the inner-face condition has not been changed. Explorer record:
`Overview/Layer1/Layer1_M1_Explorer_2026-09-30.md`.
*(Closed 2026-10-15. The breakdown is the R = 0.2 inner face. On M2's own 101³ grid it reproduces
exactly: min V = −14,594 at T = 3, with 3.29 % of nodes below the bound. On the 101 × 102² pole grid
the same frozen-evader solve keeps V ≥ min ℓ = −0.785 to within the scheme's usual 0.04 (min V
−0.825, at R = 1.85). `M5/diag/diag_m2_pole.py`; logs in `M5/m5_out/m5_out_V1_pole/`; close-out §5.)*

**2026-09-18.** M3 closed. Full record: `Overview/Layer1/Layer1_M3_2026-09-18.md`. Headline
numbers and the one grid rule that came out of it are below; the fields M4 and M5
need are in `m3_out/`.

### M3 in brief

Four grids solved, two overnight-scale. Converged in horizon by τ = 6 (the zero
level set's motion falls to 0.24 % of its own node count; a tail fit from τ ≤ 6
predicts an independent τ = 10 run to 0.004 % of grid volume). Converged in grid:
the barrier moves **0.159 coarse cells** under 2× refinement, with zero
disagreements further than 3 cells from it. Winning zone 12.08 % of the grid,
outer edge R = 6.100, inside `R_hi(0) = 6.1416`.

Plan §10's pre-flight is discharged: the mirror game is built from scratch and
solved, giving `V_2 = V_1 ∘ S` to 6.5e-13 with zero winning-zone disagreement. So
`t_2* = t_1* ∘ S` is an axis transpose and M5 needs no second solve.

### The grid rule — read this before choosing `n_phi`

**`n_phi` must NOT be a multiple of 8.** β = π/4 lands exactly on a grid node when
it is (node index `0.625 * n_phi`), and that is the target set's own kink. The
reflection symmetry — exact in the continuum, since `ell` is Rf-invariant to 4e-15
and the dynamics are Rf-equivariant — then degrades badly:

| grid | β on a node? | `t_1*` mirror mismatch | M5 smoke test (raw) |
|---|---|---|---|
| 101 × 100 | no | 0 nodes | 100.0000 % |
| 201 × 200 | **yes** | **21 642 nodes** (2.2 % of the zone) | 98.8407 % |
| 101 × 102 | no | 0 nodes | 100.0000 % |
| 201 × 204 | no | **0 nodes** | **100.0000 %** |

Use the nested pair **`101 × 102` / `201 × 204`**: both keep β off-node and
204 = 2 × 102 still nests, so the grid study stays exact subsampling.

Projecting onto the symmetry also fixes it, and `grid_study.py` reports that — but
M5 must not be measured on projected data, since its question is whether anything
*besides* the symmetry diagonal appears.

### Inner-boundary mask

The extrapolation condition at `R = R_min` leaks: it produces small blobs of
barely-negative V at R = 0.200 and 0.318 that forward simulation shows are
unreachable (`min ell` = +0.41 to +0.54). They are the only grid-study
disagreements not adjacent to the barrier, and left in they made the win-alone
component count come out at exactly D&S's five. **Use `R_MARGIN = 0.45` in M4's
tests**; `{V ≤ 0}` should not be quoted without it.

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

marched backward — which is the plan's §2.4 equation, dV/dtau = min[0, H], written
in the library's time t = -tau. The cancellation is on H only: the Lax-Friedrichs
dissipation carries one factor of `time_direction`, so its effective sign in tau is +
(clarified 2026-10-02). Worked through in the docstring of `hji.py`.

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

and imports `BETA`, `A1`, `B1`, `RBAR0` **from `layer0/common/barrier.py` rather than
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
layer1/common/ell.py      implicit surface fn, numpy + jax; parameters from layer0;
                          SCALING selects the weighting (default 'sdist', see above)
layer1/common/hji.py      dynamics, grid, solver setup, gradient/feedback/forward-sim;
                          make_policy is the ONLY supported way to build a feedback law
layer1/M1/test_m1.py      M1 — formulation verified before any solve, + conditioning (§8)
layer1/M2/test_m2.py      M2 — one-player smoke test, two-sided
layer1/M1/cmp_scaling.py  does the weighting move the computed zero level set? (it does
                          not, beyond discretization error — the table above)
layer1/README_LAYER1.md   this file
```

Added at M3:

```
layer1/M3/solve_m3.py        the march: pre-flight, horizon convergence, emits V and t_1*
layer1/M3/grid_study.py      nested-grid comparison + the exact-symmetry checks
layer1/M3/zone_structure.py  connected components of {V<=0}, phi-periodic
layer1/M3/win_alone.py       components of W_1 = {V_1<=0} \ {V_2<=0}, with the R mask
layer1/M3/sym_test.py        the beta-on-node isolation experiment
layer1/M3/m3_out/            m3_<grid>_fields.npz   V and t_1* (float32; sign of V exact,
                             round-trip error 4.7e-07 against a 0.059 cell scale)
                             Vsnap_101x102_T6.npz   V(.,tau) every 0.5, for M4 test C1
                             m3_<grid>.json         convergence diagnostics
```

Added 2026-10-01, for the explorer:

```
layer1/M2/solve_m2_snap.py     the frozen-evader (M2) game re-solved on M3's 101x102 grid to
                               tau = 6, snapshotted like Vsnap; ~13 min on two cores.
                               Reports the lower-bound check, which FAILS (see the note above)
layer1/M2/m2_out/              Vsnap_frozen_101x102_T6.npz   V(.,tau) every 0.5, + R, phi1, phi2
                               m2_frozen_101x102_T6.json     zone share, front, nodes below the bound
layer1/viz/ell_explorer.html   ell (M1) and V(x, tau) of M2 and M3; loads the two Vsnap
                               files in the browser (load files... or drop them on the page)
```

Env switches: `M3_PREFLIGHT=0`, `M3_SNAP_EVERY` (solve_m3); `R_MARGIN` (win_alone,
grid_study); `COARSE` / `FINE` (grid_study); `LAYER1_ELL_SCALING` (everything).

Added 2026-10-11, for M5 (record `Overview/Layer1/Layer1_M5_2026-10-11.md`, criteria
`Overview/Layer1/Layer1_M5_Criteria_2026-10-11.md`):

```
layer1/M5/reach_avoid.py  the reach-avoid solve: V <- max(V + dtau min(0,H), -ell_2),
                          V(x,0) = max(ell_1, -ell_2); kinds game | single | frozen_p2;
                          `cut <tag> T` takes horizon-T outputs from a longer march
layer1/M5/sim_m5.py       vectorized rollouts of the stopped game, event-located kills,
                          make_policy's remaining-horizon read, the five player-2 laws
layer1/M5/smoke_m5.py     checks 1, 1b, 2, 3 at 61x62^2
layer1/M5/test_m5.py      checks 4-12, partition volumes, thin/fat, C2
layer1/M5/converse_m5.py  check 13 (added 2026-10-12): outside W_1 the reach-avoid
                          adversary stops every player-1 law
layer1/M5/diag/diag_*.py  report-only diagnostics behind the record's Sec. 4
layer1/M5/m5_out/         m5_<grid>_T6_fields.npz (V_RA float32, reach-avoid arrival time,
                          and from 2026-10-13 the node arrays R, phi1, phi2),
                          m5_<grid>_T*.json, all logs
                          Vsnap_RA_<tag>.npz (added 2026-10-13): V_RA(., tau) every 0.5 for
                          visualization, in M3's Vsnap layout plus R, phi1, phi2; real rows
                          only. Written by every solve; for older runs:
                          python reach_avoid.py vsnap <tag> [<tag> ...]
                          (since 2026-10-15 these sit in m5_out/m5_out_V0/)
```

Added 2026-10-13, for the inner face (record `Overview/Layer1/Layer1_M5_InnerFace_2026-10-13.md`):

```
layer1/M5/pole.py                     pole condition at R = 0: staggered rows (i + 1/2) dR, 3 ghost rows
                                      below zero refilled every step by the mirror
                                      (-R, phi1, phi2) = (R, phi1 + pi, phi2 + pi); solver settings with
                                      the pole; pole.stepper flips rollouts through the pass
layer1/M5/inertial.py                 exact inertial kinematics (closed-form arcs), conversions to and
                                      from (R, phi1, phi2), exact outcomes and rollouts (truth for V1, V2)
layer1/M5/verify_pole.py              V1-V4 of the record's Sec. 4:  python verify_pole.py v1|v2|v3|v4
layer1/M5/diag/diag_pole_check3.py    smoke check 3 on the pole grid
layer1/M5/diag/diag_check3_rmin.py    smoke check 3 at a chosen R_min (the R_min = 0.1 trial)
layer1/M5/diag/diag_pole_oldfails.py  the 12 old check 3 failures re-flown on the pole grid (D1)
layer1/M5/diag/diag_pole_check8.py    check 8's far flips on the pole grid; near-face W_1 shares (D2)
layer1/M5/run_m5_pole.py              M5 rerun on the pole grids, unattended and resumable (see below)
layer1/M5/diag/diag_check8_interp.py  check 8 scored with fine values interpolated in R vs exact (old
                                      grids): the procedure for check 8 on pole grids, which don't nest
layer1/M5/m5_out/pole/                V1-V4 and D1-D2 logs and json, pole solve logs
layer1/M5/m5_out/rmin0.1/             the R_min = 0.1 smoke and diagnostic logs
```

**Rerunning M5 on the pole grids** (2026-10-13): `python run_m5_pole.py` (from `M5/`) runs every solve and
check in order (smoke, coarse march and cut, V_1, third grid, fine game and V_1, checks 4-13),
one log per step in `m5_out/pole_run/` (the run of record was then moved to
`m5_out/m5_out_V1_pole/pole_run/`), and resumes where it stopped if started again
(`--list` shows the steps; `--parallel-fine` runs the two fine solves at once). Under
`LAYER1_POLE=1`, `smoke_m5.py`, `test_m5.py` and `converse_m5.py` read the `_pole` runs: V_1
from `reach_avoid.py ... single`, field checks on the rows at R > 0, rollouts with
pole.stepper, check 8 with the fine field interpolated in R, smoke check 2 against the
inertial truth. Their json carry `_pole`. Without the variable they reproduce the M5 logs
exactly.

Solve on the pole grid with `LAYER1_POLE=1 python reach_avoid.py <n_R> <n_phi> <T> [kind]`;
`n_phi` must be even. Outputs carry the suffix `_pole`. Pole rows are staggered,
R = (i + 1/2) dR with dR = 12 / (n_R - 1/2), and the full-grid files (VRA, tRA, VRAsnap,
fields) keep 3 mirror rows at R < 0; read R from the file (fields npz, or R_nodes in the
json), never linspace(0.2, 12, n_R). Vsnap_RA drops the mirror rows.

Added 2026-10-15, for the pole rerun and the close-out (records
`Overview/Layer1/Layer1_M5_PoleRerun_2026-10-15.md`, `Overview/Layer1/Layer1_C2LongRange_2026-10-15.md`,
`Overview/Layer1/Layer1_CloseOut_2026-10-15.md`):

```
layer1/M5/c2_longrange.py           test C2 at long range, LR-1 to LR-5 (pre-registered)
layer1/M5/diag/diag_pole_rerun.py   PoleRerun Sec. 6 diagnostics: checks 4, 5, 6, 8, 9, C, near face
layer1/M5/diag/diag_m2_pole.py      M2's frozen-evader bound, old inner face vs pole (closes the
                                    2026-10-01 M2 item above)
layer1/M5/m5_out/m5_out_V0/         the original R_min = 0.2 M5 outputs and logs
layer1/M5/m5_out/m5_out_V1_pole/    m5_<grid>_T6[_single]_pole_fields.npz, json, VRA/tRA .npy,
                                    VRAsnap / Vsnap_RA snapshots, pole_run/ logs, c2_longrange.*,
                                    diag_pole_rerun.log, diag_m2_pole_*.log, test_e_table3.json
```

Added 2026-10-28, for test E against D&S Table 3 (record
`Overview/Layer1/Layer1_TestE_Table3_2026-10-28.md`; run from `M4/`):

```
layer1/M4/test_e_table3.py           T3-1 level, T3-2 locus, T3-3 the S_1 U_1 line (pre-registered);
                                     log in m4_out/, json beside the pole fields
layer1/M4/diag/diag_table3_misses.py report only: the misses, the S_1 U_1 samples, hit radii 1-4
```

`test_m4.py` exists (M4). The `mutual_kill.py` named earlier was superseded by the
reach-avoid M5 (Plan revision 2026-10-01).

Run any suite under a different weighting with `LAYER1_ELL_SCALING=raw|plan|sdist`.

## Cost, for planning M3

Two CPU cores, no GPU. Solve cost scales as n⁴ (nodes × CFL steps):
61³ / T=3 ≈ 31 s, 101³ ≈ 4 min, **201³ ≈ 2 h**. The CFL is dominated by the
angular dissipation bound `2/R_min + 1 = 11` at `R_min = 0.2`, i.e. the singular
`R -> 0` trap sets the step size. The 201³ grid convergence study of M3 is a
single overnight job, not an interactive one.
