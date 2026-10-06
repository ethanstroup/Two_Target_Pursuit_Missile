# Layer 1 — M4 audit: what the M4 record gets wrong

**AE 8900 · 2026-10-06 · Ethan Stroup**
Audit of `claude/Layer1_M4_2026-10-06.md` and `layer1/test_m4.py`, done by re-running the suite's
measurements on both grids from the M3 snapshot stacks. Read this before quoting anything from the M4
record. The M4 record itself is **not yet edited**.

**Bottom line.** The off-boresight agreement is **stronger** than M4 reported, and it converges under
refinement. Most of the record's other headlines don't hold up. The cause is one read bug, one masking
bug, one invalid control, and one misdiagnosis.

---

## 1. Snapshot read bug — the root of the "refinement makes it worse" story

`Field.nearest()` reads $V(\cdot,\tau_k)$ at the snapshot nearest the trajectory's $\tau$. That
**rounds down** for half the points. $V(x,T)$ is non-increasing in $T$, and on the active barrier it
equals 0 for every $T \ge \tau$. Below $\tau$ it is positive. So a rounded-down read biases $V$
outward.

The coarse stack is spaced 0.5 (13 snapshots). The **fine stack is spaced 1.0** (7 snapshots; the run's
own log prints this). The `test_m4.py` docstring wrongly says 0.5. Because of this, the fine run reads a
horizon up to 0.5 too early.

Tolerance 0.118 unless noted:

| quantity | coarse, M4 read | fine, M4 read | coarse, correct read | fine, correct read |
|---|---|---|---|---|
| off-boresight agreement length (median $\tau$) | 1.70 | **1.15** | 1.70 / 1.65 | **1.67 / 1.65** |
| same, fine grid at its own tolerance 0.059 | — | **0.50** | — | **1.62 / 1.60** |
| test B, off-boresight median angle | 6.02° | 8.23° | 1.94° / 0.97° | **0.47° / 0.31°** |
| test B, all retained | 6.65° | 8.97° | 2.61° / 1.09° | 0.64° / 0.37° |
| C1 $\sigma_2^*$, aggregate | 92.2 % | **85.8 %** | 97.5 % / 97.8 % | **97.5 % / 97.9 %** |

"Correct read" means the first snapshot with $\tau_k \ge \tau$ / the converged $V(\cdot,6)$. The two
agree.

- **Reproduced directly.** Dropping the coarse grid's half-integer snapshots reproduces the fine
  grid's 1.15 exactly, on the coarse grid.
- **Two of §4's four after-the-fact criterion changes were patches over this bug.** The $\sigma_2$
  "resolvable set" cut and the pinned tolerance + 1.0 bar both fall away: with a correct read, both
  original criteria pass as first written.
- **Wrong explanations to retire.** "A moving yardstick", "a lower bound still falling with
  refinement", and "refinement resolves smaller gradients" for the $\sigma_2$ drop.
- **What actually happens under refinement.** Off-boresight agreement is grid-converged at
  $\tau \approx 1.65$, and the gradient angle shrinks from about 1–2° to about 0.3–0.5° against a 35°
  $\nabla\ell$ null. That is convergence evidence, and M4 missed it.

**Fix.** Tests A and B read the converged $V$ (or ceil). Keep the matched-horizon read only for
forward-simulated feedback via `make_policy`.

## 2. Min-range "never departs" means "never tested"

- **Untested trajectories counted as agreeing.** 28 of the 48 min-range trajectories lie entirely
  below the $R \ge 0.45$ mask (median $\max R = 0.36$) and contribute **zero** tested points. `walk()`
  returns `dep_tau=None` for these, which the table reports as "never left, length 6.00". They account
  for 28 of the record's 30 (coarse) and 32 (fine) "never departs".
- **The trajectories that can be tested leave almost at once.** Over the 20 testable trajectories, the
  median departure is $\tau \approx 0.26$ with the M4 read and $\approx 0.13$ with the converged read,
  and 18 depart inward.
- **The gradient angle does not converge.** It is about 10–12° at $R$ 0.45–0.6 on both grids, and at
  $R$ 0.6–0.8 it gets **worse** under refinement (23° → 36°). All of these points sit within a few
  cells of the inner face, which M3 already flagged as leaky.
- **Status: unconfirmed on this domain.** The family is not corroborated by tests A and B.

## 3. The negative control measures a tie-break

- **The gradient vanishes at long range.** Beyond $R = 8$, $\partial V/\partial\phi_1$ is **exactly
  0** on 94–99 % of nodes, because there $V = \ell$ and $\ell$ does not depend on $\phi_1$.
- **So the 50 % is forced.** `s1_grid` is then the tie-break constant $-1$, which differs from
  $-\operatorname{sign}(\phi_1)$ on half the $\phi_1$ grid. "50.7 %" is guaranteed by construction and
  says nothing about the heuristic.
- **$\sigma_1$ in C1 has no discriminating power.** On the C1 points the heuristic matches
  `barrier.py` exactly as often as $\nabla V$ does (98.2–98.9 % for both, under every read). Only
  $\sigma_2$ discriminates: the heuristic scores 87 % there against the grid's ~98 %.
- **Status: no valid negative control yet.** The plan's control, against Layer 0 at long range, has
  no data to run on, because no retained points exceed $R = 6.26$.

## 4. Max-range: the departure is real, but the diagnosis is wrong

The departure holds under every read rule. Its cause is the **kink of $\bar R(\phi_2)$ at
$\phi_2 = 0$**:

- **The seeds sit next to the kink.** The 8 seeds have $|\phi_2| = 4.4°$ or $8.9°$: two distinct
  values, as 4 mirror pairs.
- **Before the kink they track the face.** Retrograde, they hug the face with $R-\bar R \sim 10^{-3}$.
- **They cross the kink early.** The crossing comes at $\tau \approx 0.07$–$0.15$.
- **After the kink they peel away.** $R - \bar R$ grows at about $4$ per unit $\tau$. The reason is
  that $\lambda_2 \approx -1.9$ is still the normal of the $\phi_2<0$ face, while the true face normal
  now has $+2$. So $\sigma_2 = \operatorname{sign}(\lambda_2)$ steers player 2 *toward* the kink, which
  is the wrong way for him.

This is D&S's uncovered corner (Eqs. 38–42). It is consistent with the MaxRangeAudit, but it is a
definite geometric cause.

The record's three checks in §3 were all made at **$\tau = 1.0$**, about 0.85 past the departure (the
quoted state is trajectory 4 at $\tau = 1.0$):

- Check 2's $\min_t \ell = 1.37$ is just $\ell$ at the start point.
- Check 3 shows only a local $\dot\ell$.
- Test B's max-range angles (18.22°, 0.66°) equal the $\nabla\ell$ null **exactly**, so they carry no
  information.

## 5. The 0-of-16 switch anomaly is explained; hypothesis (ii) was right

- **The 16 are not independent.** They are 8 $Rf$-mirror pairs from 8 *adjacent* off-boresight seeds
  ($\phi_2 = \pm94°\ldots\pm136°$), all $\lambda_1$ switches. The $2^{-16}$ null therefore does not
  apply.
- **Each switch is a junction.** After each one, the Layer 0 trajectory swings $\phi_1$ into the
  boresight cone and through the target set; half have $\ell \le 0$ within 0.15. The walk records an
  **inward departure 0.03–0.34 later**.
- **The grid's switch is not missing.** By design, `barrier_controls` at a snapped zero returns the
  post-switch control, and the grid matches Layer 0's **pre-switch** control 16/16.
- **So these are the inactive-segment junctions the plan asked to list.** §5(a)'s "do not re-run
  these" should be struck.

## 6. Reproducibility and low-information tests

- **Hard-coded numbers in the log.** `test_m4.py` hard-codes "median gap 1.46 vs 0.44" and
  "96 %/92 %" into printed notes. The fine log shows 96/92 although that run measured 94.9/85.8.
- **Code not in the repo.** §3's checks, §5(a)'s tests and the C1 quartile figures are not in the
  repo, despite §6's claim.
- **The seed check is vacuous.** It reads $V(\cdot,0)=\ell$ at points that lie on $\partial T$ by
  construction.
- **Test D does not touch the solve.** It checks the analytic `E.ell`, not grid $V$, at points chosen
  because they satisfy the same surface equations.
- **Test E mostly measures $\ell$.** Run on $\ell$ alone, the detector flags 1.86 % / 0.91 % of nodes,
  against 2.20 % / 1.14 % for converged $V$. The flagged nodes sit at the same $\phi = 0, \pm180°$
  locations and halve under refinement in the same way. Most of the reported "locus" is $\ell$'s own
  kinks, and the halving is what any 2-D surface does.

## 7. Corrected verdict

The off-boresight family is strongly corroborated and grid-converged:

- agreement $\tau \approx 1.65$ on both grids;
- gradient angle 0.3–0.5° on the fine grid, against a 35° null;
- both controls about 97–98 %.

The rest stands as follows:

- **Max-range** departs at the $\phi_2 = 0$ kink, because Layer 0 has no corner family.
- **Min-range** is untested or unconfirmed next to the inner face.
- **The negative control** and **tests D/E** are not yet valid tests of the solve.

## 8. To do (not done)

1. Patch `test_m4.py`:
   - ceil/converged read for A/B;
   - exclude untested trajectories from the family statistics;
   - drop the hard-coded notes;
   - a negative control that excludes $\partial V/\partial\phi_1 = 0$ nodes.

   Then re-run both grids.
2. Revise the M4 record §§1–5 to match.
3. Min-range: test on a domain with a lower $R_{\min}$ (or a fixed inner face) before drawing any
   conclusion.
4. For M5 test F: the grid has $V = \ell$ near the max-range corner, so check D&S's two small
   max-range zones specifically.

*Probe scripts (`probe_*.py`) were run in a session workspace and are not in the repo.*
