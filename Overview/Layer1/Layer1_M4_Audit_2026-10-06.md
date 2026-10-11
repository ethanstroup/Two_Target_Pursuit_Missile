# Layer 1 — M4 audit: what was fixed, and what the rerun confirmed

**AE 8900 · audit 2026-10-06, closed out by the 2026-10-07 rerun · Ethan Stroup**

The first M4 attempt reported "every assertion passes", but six problems sat behind that. This note
records each problem, the fix now in `layer1/test_m4.py`, and what the rerun logs
(`layer1/m4_101x102.log`, `layer1/m4_201x204.log`) show. Results are in
`claude/Layer1_M4_2026-10-06.md`, and the plain-language walkthrough is in
`claude/Layer1_M4_Explainer.md`.

**Status: all six resolved.** Item 3 carries into M5. One comparison stays open without blocking
it: test E against Table 3 (item 6).

---

## 1. Snapshot read

**Problem.** Points were read at the *nearest* $V$ snapshot, which lies below the point's own
$\tau$ half the time. $V$ is non-increasing in the horizon, and on the active barrier
$V(x,T)=0$ only for $T\ge\tau$. A read below $\tau$ is therefore biased outward. On a stack with
coarser snapshot spacing the bias was larger, and it made the finer grid look worse:
- off-boresight agreement fell to 1.15 at the pinned tolerance, and to 0.50 at the fine grid's own;
- the gradient angle rose to 8.2°;
- evader-control agreement fell to 85.8 %.

Four pass criteria had been revised after those failures.

**Fix.** Read at the first snapshot with $\tau_k\ge\tau$ (`M4_READ=ceil`; `conv` agrees). The
original criteria are restored: C1 aggregate above 90 %, and off-boresight median of at least 1.0
at each grid's own tolerance.

**Rerun (101 → 201):**

| | 101 | 201 |
|---|---|---|
| off-boresight agreement length | 1.69 | 1.62 |
| gradient angle | 1.94° | 0.51° |
| $\sigma_1$ agreement | 96.6 % | 97.1 % |
| $\sigma_2$ agreement | 97.5 % | 98.4 % |

Every criterion passes as originally written, and everything holds or improves under refinement.

## 2. Untested trajectories counted as agreeing

**Problem.** Some min-range trajectories lie entirely below the $R\ge0.45$ mask, so they had no
points to test. They were reported as "never left, length 6.00", which turned the family's
headline into a non-result.

**Fix.** Trajectories with no point above the mask are excluded and counted separately.

**Rerun.**
- **Excluded:** 30 trajectories (28 min-range, 2 off-boresight).
- **Min-range:** 20 of 48 are testable, and they leave at $\tau=0.26$ / $0.18$, all inward or
  never.
- **Status:** unconfirmed and deprioritized.

## 3. Negative control measured a tie-break

**Problem.** The replacement control compared the grid law with the heuristic over the whole
domain, and found about 50 % disagreement beyond $R=8$. But there $V_1$ is exactly 0 on 94–99 % of
nodes. The grid law is then the constant tie-break $\sigma_1=-1$, so 50 % disagreement is forced.
Separately, the heuristic matched Layer 0 exactly as often as $\nabla V$ did on the retained
points.

**Fix.**
- The plan's control (the heuristic must fail test C at long range) is reported as SKIP while no
  retained point reaches $R=8$.
- The band table drops $V_1=0$ nodes.
- The heuristic is scored on the C1 points for both controls.

**Rerun.**
- **The pursuer's control can't discriminate.** The heuristic equals the grid on $\sigma_1$
  (98.8 % and 99.2 %).
- **The evader's control does.** On $\sigma_2$ the heuristic scores 93.3 % / 92.3 % against the
  grid's 98.2 % / 99.1 %.
- **Where $V$ defines a law, the heuristic agrees with it.** With $V_1=0$ nodes dropped, the two
  disagree on only 2–9 % in every band.
- **Beyond $R\approx6$ there is mostly no law to score.** $V=\ell$ on 81–99 % of nodes there, so
  $V$ defines no long-range $\sigma_1$ law. **Carried into M5:** the negative control needs test
  F's simulations as its reference.

## 4. Max-range misdiagnosed

**Problem.** The record called the 8 max-range departures "a real defect in Layer 0's
maximum-range family", and gave player 2's costate control as the reason. Its three checks were
all made at $\tau=1.0$, well past the departure. Test B's max-range angle equalled the
$\nabla\ell$ null, so it carried no information.

**Resolution (Ethan's reading of the barrier explorer).**
- **The sheets enclose nothing.** The sheets from the two BUP lenses diverge and enclose no
  volume.
- **Each trajectory peels off at the ridge.** It hugs its own face to within about
  $2\times10^{-3}$ until it crosses the ridge at $\phi_2=0$, then rises over the opposite face.
- **The grid agrees.** Past the crossing, $V=\ell$.
- **The closing pieces are below resolution.** Layer 0's corner family, universal line and
  dispersal line lie within about $2.2\times10^{-3}$ of the ridge, far below a grid cell.
- **D&S's two small max-range zones lie on the target set.**

**The suite now prints each departure next to its crossing.**

**Rerun.** All 8 trajectories depart after their crossing. The lag is 0.068–0.090 on the coarse
grid and 0.040–0.059 on the fine; it shrinks with the tolerance, so the departure is tied to the
crossing. This is not a defect, and these are not junctions.

**Carried into M5:** exclude these zones from test F, since $W_1$ contains them from the initial
value alone.

## 5. The 0-of-16 switch "anomaly"

**Problem.** At the switches inside retained segments, the grid matched Layer 0 0 of 16 times.
- **It was called systematic and unexplained**, with odds of $2^{-16}$ under a coin-flip model.
- **The right explanation was ruled out.** "The switch is where the trajectory leaves the barrier"
  was rejected using a hard-coded statistic.

**Fix.** The grid's control is now compared on both sides of each switch, with the gap to the
departure.

**Rerun.**
- **Pre-switch side.** The grid matches Layer 0's pre-switch control 16/16 (coarse) and 14/14
  (fine).
- **At the switch.** It matches 0 there, because `barrier_controls` returns the post-switch
  control at a snapped zero.
- **Departure.** Every one departs inward about 0.16 later.
- **Independence.** The switches come from 8 / 7 distinct seeds, with mirror pairs, so they are
  not independent draws.

**Identification: they are not $S_1U_1$** (`layer0/viz/commuting_s1u1.py`, run 2026-10-07). An
earlier version of this note said the switches lie along D&S's commuting line $S_1U_1$. That came
from comparing endpoints only, and the run disproves it.

- **$S_1U_1$ itself is reconstructed.**
  - The $(0,-1)$ line from Table 2's $S_1$ passes Table 2's $U_1$ at $3.6\times10^{-4}$.
  - Searching from $U_1$ recovers $S_1$'s $\phi_1$ as $47.238°$, against Table 2's $47.24°$.
  - Every invariant holds to $10^{-13}$ or better.
- **The switches sit on a different surface.**
  - They all lie on $\phi_2=\pm135.00°$, 0.04–0.11 from the line.
  - They are transversal crossings ($\dot\lambda_1$ from $+0.07$ to $+0.72$), which D&S's closed
    $(-1,-1)$ orbits cannot be.
  - The crossing turns into a touch only near $U_1$, the one point the two curves share.
- **Table 3 has no pursuer switch line here.** All four of its pursuer switch lines sit at $R<0.6$.

**Conclusion.** The switches are junctions, as the grid shows: Layer 0's post-switch segments lie
outside D&S's structure. They are not a Table 3 line.

## 6. Hard-coded numbers and low-information tests

**Problem.**
- **Some printed notes were fixed text, not measurements.** One example is "median gap 1.46 vs
  0.44"; another is a "96 %/92 %" figure that the fine-grid log printed although that run measured
  otherwise.
- **The seed check and test D only exercise $\ell$.**
- **Test E's locus was mostly $\ell$'s own kinks.**

**Fix.**
- Every printed number is measured.
- Test B and test E carry nulls.
- The seed check and test D are labeled as checks of $\ell$.

**Rerun.**
- **Test E.** It flags 2.203 % / 1.146 % of masked nodes, against 1.857 % / 0.911 % for $\ell$
  alone. The solve's own excess is 0.346 % / 0.235 %.
- **Open:** compare that excess with D&S Table 3, transcribed in `layer0/table3.py` (run
  2026-10-07).
  - All 34 rows resolve to Table 2 points, and 16 have both endpoints above the mask.
  - It flags $M_1n_1$ and $I_1P_1$ as inconsistent as printed.
  - It flags $f_1c_1$ and $c_1O_1$ where they disagree with Layer 0's corner work.
  - `validate_table2.py` omits Table 2's point $k_1=(0.25,\ 0°,\ \pm180°)$; `table3.py`
    supplies it.

---

## The lesson for M5

Two of the four criteria revised after a failure were covering the read bug, which was the real
cause. Fix M5's numeric criteria before the solve runs. Give every headline number a null.
