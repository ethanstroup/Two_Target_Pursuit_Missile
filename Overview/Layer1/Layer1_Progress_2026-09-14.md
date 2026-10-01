# Layer 1 Progress — M1 and M2 closed

**AE 8900 · 2026-09-14 · Ethan Stroup**
Plan of record: `claude/Layer1_Plan.md`. Spec of record: `claude/ProblemStatement.md`.
Code: `Two_Target_Pursuit_Missile/layer1/` (`ell.py`, `hji.py`, `test_m1.py`, `test_m2.py`,
`README_LAYER1.md`).

| Milestone | State |
|---|---|
| M1 formulation verified before any solve | **DONE** — all checks pass |
| M2 one-player smoke test | **DONE** — all checks pass at 61³ and 101³ |
| M3 full two-player solve, converged in horizon and grid | not started |
| M4 acceptance against Layer 0 | not started |
| M5 mutual-kill / arrival-time comparison | not started |

---

## Tooling decision (Plan §3): `hj_reachability` 0.7.0 (JAX)

Evaluated against the plan's two hard requirements; both met natively.

- **Periodic dimensions** — `boundary_conditions.periodic` selected per dimension,
  and periodic axes are built with `endpoint=False`, so `phi = +pi` is never
  duplicated.
- **Two-player min–max Hamiltonian with a min-over-time reach formulation** —
  `ControlAndDisturbanceAffineDynamics` with `control_mode="min"`,
  `disturbance_mode="max"`, and `solver.backwards_reachable_tube` as the
  Hamiltonian postprocessor.

Plan §2.4's PDE was **verified from the library's own source rather than
transcribed**, as §2.4 requires. In `time_integration.euler_step` the two factors
of `time_direction` cancel, leaving `dV/dt = -min(0, H)` marched backward, which
is the plan's equation. The derivation is written out in `hji.py`'s module
docstring.

JAX must run in **float64** (`jax_enable_x64`), set before any array is created —
the default float32 would have made the M1 machine-precision comparison
meaningless. Asserted in `test_m1.py` §0.

## M1 — formulation verified before any solve

`ell.py` implements `ell(x) = max(|phi_1| - beta, R_lo(phi_2) - R, R - R_hi(phi_2))`
and **imports `BETA`, `A1`, `B1`, `RBAR0` from `layer0/barrier.py` rather than
re-entering them** — re-declaring `RBAR0` would be a way to silently lose the
`3 + pi` correction. That import identity is itself asserted.

- `{ell < 0}` equals `barrier.in_target` with **0 mismatches** on a 181³ =
  5.93M-node grid and on 4×10⁶ random points.
- `{ell <= 0}` differs from `in_target` only where a constraint is exactly active —
  the half-open/closed difference of D&S Eq. (7), accounted for rather than tolerated.
- `f(x, sigma)` **bit-identical** to `barrier.state_dot` on 2×10⁴ random points.
- **The M1 gate:** `dynamics.hamiltonian` vs `barrier.hamiltonian_star` on 2×10⁵
  random `(x, grad V)` — **3 ulp** of the summed terms, bit-identical at 91k of
  200k points, and within 4e-15 on every degenerate gradient (`lambda_1 = 0`,
  `lambda_2 = 0`, `lambda_R = 0`, `lambda = 0`). The `lambda_i = 0` cases are the
  range-surface and boresight BUPs, i.e. exactly where Layer 0 seeds.
- `sigma_1* = -sign(lambda_1)`, `sigma_2* = +sign(lambda_2)` reproduced on every
  sampled gradient, and H is attained at that pair.
- All four traps of Plan §3 asserted rather than intended: both angle dimensions
  periodic and R not; `ell` continuous across both seams to 0.0; `R_hi`'s corner at
  `phi_2 = 0` still present (one-sided slopes ∓2, deliberately not smoothed); the
  dissipation bound equal to the plan's analytic `|L|/R + 1 <= 2/R_min + 1`.

**A correction to the test, not the formulation.** The Hamiltonian check first
*failed* at a relative error of 3.6e-12 with an absolute error of 1.4e-14. The
criterion was wrong: normalizing by `|H|` is indefensible here because `H` vanishes
identically on the semipermeable surface, so a relative-to-result test reports the
cancellation the barrier is *made of* as if it were an error. The test now measures
against the magnitude of the summed terms. Worth carrying into M4 — test B compares
`grad V` against the Layer 0 costate near `H = 0`, where the same trap is waiting.

## M2 — one-player smoke test (`sigma_2` frozen at 0)

Two-sided: the feedback law must **achieve** V (V is not too low) and **nothing
else may beat** V (V is not too high). Every margin tightens under refinement.

| | 61³ (dR = 0.197) | 101³ (dR = 0.118) |
|---|---|---|
| reach-front speed vs. analytic 2 | 2.016 | **2.003** |
| median shortfall of the feedback law | +0.00047 | **+0.00023** |
| 90th pct shortfall | +0.043 | **+0.021** |
| max shortfall | +0.132 | +0.124 |
| sign of V vs. simulated outcome | 232/232 agree | **230/230 agree** |
| worst violation of optimality | +0.121 | **+0.062** |
| — as a fraction of dR | 0.62 | **0.53** |

Adversaries in the optimality half: σ₁ = ±1 and 0, the old pursuit heuristic, three
random bang-bang laws, and a brute-force sweep over every single-switch control on a
21-point switch-time grid. The worst was the pursuit heuristic — the law the Layer 0
sim used — and even it did not beat V by one grid cell.

---

## Three findings to carry into M3–M5

### 1. The reach front travels at exactly the maximum closing speed

Against a non-maneuvering target the winning zone's outer edge in R advances at a
measured **2.003** per unit time, against the analytic bound
`max |Rdot| = max(cos phi_1 + cos phi_2) = 2`. This is a physical check the solver
cannot pass by accident, and it is now a test.

It replaced a check that was the wrong question. *"Has the zero level set stopped
moving?"* is an **M3** criterion, not an M2 one: against a frozen evader the zone
never stops growing — it is range-limited and simply runs out of domain.

### 2. D&S's bounded winning zone appears on its own, before any acceptance test

Same grid, same horizon, player 2 released: the winning zone's growth per step
decays 0.21 → 0.03 % of the grid, and its outer edge stays pinned at **R = 5.98**,
inside `R_hi(0) = 6.1416`, while the frozen-evader front runs out to the domain
edge at 12. The two-player problem converges in horizon and the one-player one does
not. That is the structure Plan §2.2 asks M3 to confirm, showing up unprompted — and
it is corroboration that the two-player Hamiltonian has the right player maximizing,
independent of M1's algebraic check.

### 3. A finite-horizon value function must be read at the REMAINING horizon

The optimal control at elapsed time `t` is

```
sigma_1*(x, t) = -sign( dV(x, T - t)/dphi_1 )    NOT   -sign( dV(x, T)/dphi_1 )
```

Reading the terminal-horizon V throughout is the natural mistake and it is a large
one: **worst shortfall 2.04 vs 0.13** — same V, same grid, same trajectories, only
the horizon at which `grad V` is read changed. The mechanism is that the `min(0, H)`
postprocessor freezes V on large plateaus, `grad V` there is zero, and the bang-bang
law degenerates into coasting.

**This was caught the right way round, and the process is the point.** The first run
showed a 2.04 shortfall and a plausible story: a shock ridge at `phi_1 = ±pi`, which
does exist (0.85 % of nodes, concentrated at the tail-on antipode, `phi_1 = -pi`
alone carrying 3.6 %). The story was **wrong** — a one-step-lookahead policy, which a
shock would have fixed, did not help. Brute force then showed a *constant*
`sigma_1 = -1` reaching `min ell = -0.783` against `V = -0.719`, so V was correct and
slightly conservative, and the control extraction was the defect.

This is the §9 standard working: *prefer an invariant that the thing you might get
wrong actually violates.* The forward-simulation test caught a defect no invariant
would have, because `V` satisfied the PDE perfectly throughout.

`test_m2.py` now carries the stale read as an explicit passing test — it asserts
that the wrong read is measurably worse — so a future session cannot reintroduce it
and blame the value function. Two smaller fixes fell out of the same investigation:
`np.sign(0) = 0` is not an admissible bang-bang control and made the pursuer coast
(now tie-broken to ±1), and `hji.make_policy` is the only supported way to build a
feedback law so the remaining-horizon read cannot be forgotten at a call site.

**Consequence for M4.** Acceptance test C compares `sigma*` derived from `grad V`
against `barrier.py`'s bang-bang controls along the Layer 0 trajectories. Those
trajectories are parameterized by retrograde time `tau`, so the comparison must be
against `grad V(., tau)` at the matching horizon, not against the converged `V`.
Getting this wrong would fail test C on a correct V.

**Open question this raises, for M3.** The shock ridge at `phi_1 = ±pi` is where `V`
is genuinely non-differentiable and the bang-bang law is ambiguous — which is where
D&S's singular/universal lines should live, and Layer 0 *flagged* singular arcs
rather than solving them (ProblemStatement §3.4). Whether the ridge in the
two-player solve coincides with D&S's Table 3 singular lines is worth checking at
M3; if it does, it is a cheap partial answer to §8 item 6.

---

## Cost, for planning M3

Two CPU cores, no GPU. Solve cost scales as n⁴ (nodes × CFL steps):

| grid | T = 3 solve |
|---|---|
| 61³ | 31 s |
| 101³ | 4.7 min |
| 201³ | **~2 h** |

The CFL is dominated by the angular dissipation bound `2/R_min + 1 = 11` at
`R_min = 0.2` — the singular `R -> 0` trap sets the step size, so pushing `R_min`
lower is expensive and pushing it up is not available (min `R_lo` is 0.25).

The 201³ grid-convergence study of M3 is an overnight job, not an interactive one.
Memory is the other constraint: a gradient field per horizon snapshot is 1.5 GB at
101³ and would be 12 GB at 201³, so `make_policy` now keeps only the two angular
partials in float32, subsampled to 31 snapshots.
