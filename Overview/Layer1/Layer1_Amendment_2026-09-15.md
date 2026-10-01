# Layer 1 — the `ell` weighting, and the M1/M2 re-run

**AE 8900 · 2026-09-15 · Ethan Stroup**
Plan of record: `claude/Layer1_Plan.md`. Prior record: `claude/Layer1_Progress_2026-09-14.md`.
Code: `Two_Target_Pursuit_Missile/layer1/`.

**One decision is open and wants your answer before M3's 201³ run.** Everything else
here is a completed re-run.

| Milestone | State |
|---|---|
| M1 | **DONE**, re-run 2026-09-15, green under all three weightings |
| M2 | **DONE**, re-run 2026-09-15 at 61³ and 101³, green |
| M3 | ready to start |
| M4, M5 | not started |

---

## The open decision: Plan §2.1's weighting

§2.1 (added in the 2026-09-14 20:04 revision) asks for `ell` to be nondimensionalized —
boresight term over `beta`, both range terms over `Rbar_0` — and gives conditioning as
the reason:

> *"Level-set schemes want `|grad ell| ~ 1`. A max of badly-scaled terms gives a value
> function steep in one direction and flat in another, which resolves the zero level
> set poorly — precisely the surface being validated."*

**The goal is right. The prescribed weighting does not serve it.** Measured, not argued
(`test_m1.py` §8, reproducible in 25 s) — `|grad ell|` on nodes within 1.0 of the zero
level set:

| scaling | p05 | median | p95 | p95/p05 |
|---|---|---|---|---|
| `raw` — no weighting, what M1/M2 originally used | 1.000 | 1.000 | 1.864 | 1.9 |
| `plan` — §2.1 as written | 0.163 | 0.330 | 1.273 | **7.8** |
| `sdist` — each term over the norm of its own gradient | 0.861 | 1.000 | 1.188 | **1.4** |

Dividing the range terms by `Rbar_0 = 6.14` flattens exactly the direction in which the
target set is thin. The raw `ell` was already reasonably conditioned at 1.9× spread; the
prescription degrades it to 7.8×.

### What it costs, measured on the actual solve

`cmp_scaling.py` runs the two-player solve under each weighting and compares the
computed `{V <= 0}`:

| grid | raw vs sdist | plan vs raw | `{V<=0}` share of grid |
|---|---|---|---|
| 61³ | 0.0079 % | 0.2079 % | raw/sdist 11.565 %, plan 11.463 % |
| 101³ | 0.0049 % | 0.1157 % | raw/sdist 11.631 %, plan 11.577 % |

Read this carefully, because the effect is small and it would be easy to overstate:

- **All three converge to the same answer.** The weights are strictly positive, so
  `{ell <= 0}` and therefore the barrier are weight-invariant in exact arithmetic. The
  disagreements above are discretization error and they halve under refinement, exactly
  as discretization error should.
- `raw` and `sdist` agree to **5 parts in 10⁵** of grid volume — the same answer.
- `plan` is the outlier by ~24×, and consistently *under-resolves* the winning zone
  (11.577 % vs 11.631 % at 101³).
- Outer edge in R is 5.982 under all three, so nothing gross is happening.

So this is not a correctness question. It is a "which weighting resolves the surface
best per unit of compute" question, and M3's grid study costs two hours.

### `sdist` is what §2.1 itself falls back to

§2.1's closing sentence: *"If convergence is still poor, reinitialize by solving the
eikonal equation `|grad ell| = 1` to recover a true signed distance with the same zero
level set."* Dividing each constraint by the Euclidean norm of its own gradient in
`(R, phi_1, phi_2)` is the closed-form approximation of exactly that, done up front for
free instead of by an eikonal solve. So the amendment is in the spirit of §2.1 rather
than against it — it substitutes the fallback for the prescription.

### What §2.1 is right about, and what is kept unchanged

**The units argument.** `ell` maxes a radian against two normalized lengths under *every*
weighting. A nonzero value is a **weapon-envelope margin in mixed units**, never a miss
distance, and nothing in this amendment makes it one. `ell.py`'s docstring carries that
warning, and it should carry into the report.

### Status and how to decide

`SCALING = 'sdist'` is now the default in `ell.py`, **flagged in the source as a
deviation from the plan of record awaiting your decision**, with the full evidence in a
comment block. Reverting is one string, or `LAYER1_ELL_SCALING=plan` at the command
line. Every suite runs under any of the three.

If you accept it, §2.1's prescription sentence should be amended; if you reject it, set
the default back to `'plan'` before M3 and nothing else changes — the acceptance tests
A–E are weight-invariant either way.

---

## The M1/M2 re-run

Both suites pass under all three weightings. Figures below are under `sdist`.

**M1** — unchanged in substance: `ell` sign vs `barrier.in_target` with zero mismatches
on 5.93M nodes and 4×10⁶ random points; `f` bit-identical to `barrier.state_dot`; the
Hamiltonian gate at 3 ulp. Two test changes:

- the "Lipschitz constant in R is ~1" check now asserts the constant equals the
  *analytic weight* for the active weighting, which is the weight-invariant statement;
- a new §8 measures the conditioning of all three weightings and prints the table above,
  so the §2.1 question is re-decidable from a single fast run rather than from this note.

**M2** — green at both resolutions, every margin tightening under refinement:

| | 61³ | 101³ |
|---|---|---|
| one-cell value change (the tolerance unit) | 0.1967 | 0.1180 |
| reach-front speed vs. analytic 2 | 2.016 | **2.003** |
| median shortfall of the feedback law | +0.00028 | **+0.00022** |
| 90th pct shortfall | +0.037 | **+0.018** |
| max shortfall | +0.116 | +0.124 |
| sign of V vs. simulated outcome | 232/232 | **230/230** |
| worst violation of optimality | +0.116 | **+0.067** |
| — as a fraction of one cell | 0.59 | **0.57** |

**One honest caveat.** At 101³ the *max* shortfall (0.124) sits just above one cell
(0.118), while the median is ~500× smaller and the 90th percentile is 0.018. The suite
asserts `max < 3 cells` for that reason. The tail is a handful of trajectories near the
`phi_1 = ±pi` shock ridge, not a systematic bias — but it is a tail that does not shrink
with refinement, and if M4's test C shows the same trajectories failing, the ridge is the
place to look first.

### A test unit changed, and it is worth knowing why

M2's tolerances used to be quoted against `dR`. That only worked while `ell` was
unscaled: once terms carry weights, a length and a value are no longer interchangeable.
They are now quoted against `ell.value_scale` — the change in `ell` across one grid cell
— measured **near the zero level set**, not over the whole domain.

The restriction is load-bearing. Measured over the whole domain, the statistic is
dominated by the far field, where a state-dependent weight multiplies a large residual
and produces a per-cell change that has nothing to do with resolving the surface: under
`sdist` that inflated it from 0.118 to 0.239 and would have loosened every M2 tolerance
threefold for no reason. The first `sdist` run of M2 passed with that inflated tolerance
before the restriction was added, which is the kind of pass that is worse than a failure.

---

## Ready for M3

`solve_m3.py` is still to be written. The plan's §10 opening move stands, with one
addition:

0. **Decide the weighting** (above), or accept the `sdist` default.
1. Re-read the 2026-09-14 note's three findings — the remaining-horizon read is the one
   that silently ruins M4's test C1, and it is already enforced by `hji.make_policy`.
2. Assert the §2.5 transpose identity on the actual grid arrays before relying on
   `t_2* = t_1* o S`. Thirty seconds, and it is the difference between M5 being a
   transpose and a second overnight solve. I did not find this check committed anywhere
   in `layer1/`, so treat §2.5's "verified at zero residual over 2×10⁵ random states" as
   applying to the *continuum* identities, not to the discretized grid.

Costs are unchanged from the 2026-09-14 note: 101³ solve ≈ 3 min at T = 3 with two
output times, ≈ 5 min with 61; 201³ ≈ 2 h. Gradient storage is the binding constraint at
201³ — `make_policy` keeps only the two angular partials in float32, subsampled to 31
horizon snapshots.
