# Layer 1 — M4 Explainer

**AE 8900 · reference doc, written 2026-10-07**

**Companion docs:**
- `claude/Layer1_M1_Explainer.md`, `claude/Layer1_M2_Explainer.md` and `claude/Layer1_M3_Explainer.md`;
- the M4 record `claude/Layer1_M4_2026-10-06.md`;
- the audit `claude/Layer1_M4_Audit_2026-10-06.md`;
- `claude/Layer1_Plan.md` §5.

**Code and logs:**
- `Two_Target_Pursuit_Missile/layer1/test_m4.py`;
- `layer1/l0_traj.py`;
- `layer0/table3.py`;
- `layer0/viz/commuting_s1u1.py`;
- the logs `layer1/m4_101x102.log` and `layer1/m4_201x204.log`.

This is a plain-language walkthrough of what M4 does and why each check exists, in the same style as
the M1–M3 explainers. Every number here comes from the logs.

**Notation** follows the project docs:
- $\nabla V$ has components $V_R, V_1, V_2$;
- $\lambda$ is Layer 0's costate;
- $\tau$ is retrograde time on a Layer 0 trajectory, which is also the time remaining in the value
  function.

---

## 1. What M4 is, and why it exists

**M3 settled whether the solve is stable; M4 asks whether it is right.** M3 showed the solve is
converged and self-consistent. M4 compares it with something built a completely different way:
Layer 0's barrier trajectories.

That overlap is the point of having two layers (Plan §0). The two layers reach the same object by
different routes:

- **Layer 0** integrates characteristics *backward* from the boundary of the usable part (BUP), one
  trajectory at a time. Each one comes from an exact ODE with its own error checks.
- **Layer 1** solves a PDE *globally* on a grid and never looks at a trajectory.

**If they agree where both apply, each corroborates the other.**

**One caveat shapes everything.** Layer 0's trajectories are correct *local* characteristics, but
Layer 0 never did the global assembly that decides which pieces actually bound the winning zone
(the 10-01 revision). So a trajectory can be right as a characteristic and still leave the real
barrier partway along. M4 therefore asks two things:

- How far along does each trajectory stay on the grid's barrier?
- Where it leaves, which way does it go?

---

## 2. What is being compared

**Layer 0's bundle.** There are 122 trajectories in three families, one per face of the target set:

| family | count | seeded on |
|---|---|---|
| max-range | 8 | $R=\bar R(\phi_2)$ |
| min-range | 48 | $R=\underline R(\phi_2)$ |
| off-boresight | 66 | $\lvert\phi_1\rvert=\beta$ |

- **Seeding.** Seeds sit on a fixed grid in $\phi_2$: 4.4° on the range faces, 6.1° on boresight.
- **Integration.** Each trajectory is integrated retrograde to $\tau=6$, carrying its costate
  $\lambda$.
- **Accuracy.** Its own invariants hold to $10^{-10}$: the first integral equals 1, and $H^*=0$.
- **Reproducibility.** `l0_traj.py` regenerates the bundle by calling `test_barrier.py`'s own seed
  functions, so M4 tests the same bundle Layer 0 verified.

**Layer 1's field.** M3's $V(\cdot,\tau)$ snapshots, every 0.5 in $\tau$, on $101\times102^2$ and
$201\times204^2$.

**What should match, on the barrier:**

1. **Level.** $V=0$.
2. **Direction.** $\nabla V$ is parallel to $\lambda$. Both are normals to the same surface, and
   Layer 1's Hamiltonian is literally `barrier.hamiltonian_star` with $\lambda:=\nabla V$ (M1).
3. **Controls.**
   - The pursuer's control from the grid, $-\operatorname{sign}(V_1)$, should equal Layer 0's
     $-\operatorname{sign}(\lambda_1)$.
   - The evader's control from the grid, $+\operatorname{sign}(V_2)$, should equal Layer 0's
     $+\operatorname{sign}(\lambda_2)$.

These are tests A, B and C1. Tests D and E use D&S's Tables 2 and 3 instead of the trajectories.

---

## 3. The one subtle thing: which horizon to read

**$V$ only goes down as the horizon grows.** $V(x,T)$ is non-increasing in $T$, because the
$\min[0,H]$ clamp only lowers it.

**What that means for a point on the barrier.** Take a point at retrograde time $\tau$ on the
active barrier. Starting there, player 1 can graze the target in time $\tau$ and no sooner. So:

$$V(x,T)=0\ \text{ for every } T\ge\tau,\qquad V(x,T)>0\ \text{ for } T<\tau.$$

**So the level test must read a horizon at or above $\tau$.** Two reads do that, and they agree:
- **ceil (the default):** the first snapshot with $\tau_k\ge\tau$;
- **conv:** the converged $V(\cdot,6)$.

**Reading the nearest snapshot is the trap.** That rounds below $\tau$ half the time, and biases
$V$ outward. The first version of this suite did exactly that. A stack with coarser snapshot spacing
then looked worse, and that read as "the finer grid is worse" (audit item 1).

**How this relates to M2's trap.** M2's rule was to read a feedback law at the *remaining*
horizon; it governs forward simulation through `hji.make_policy`. Here nothing is simulated. The
point's horizon is known, and reading *below* it is the error.

---

## 4. Test A — level

**What it does.** It walks each trajectory from $\tau=0$ and stops at the first sampled point where
$|V|$ exceeds the tolerance. The $\tau$ there is the **agreement length**, and the sign of $V$
there is the **departure side**:

- **inside** ($V<0$): the characteristic has crossed into the winning zone's interior. That is
  what an inactive segment beyond a junction looks like.
- **outside** ($V>0$): the grid says player 1 cannot reach from there at all.

**Tolerance.** It is one cell's change in value: 0.118 on the coarse grid and 0.059 on the fine.
`M4_TOL` can pin it across grids, but with the correct read it isn't needed.

**Untested trajectories.** A trajectory lying entirely below the $R\ge0.45$ mask has no points to
test. It is excluded and counted separately, never counted as agreeing: 28 min-range trajectories
and 2 off-boresight.

| family | tested / total | median length, 101 / 201 | departure side |
|---|---|---|---|
| off-boresight | 64 / 66 | **1.69 / 1.62** | 36 inside, 28 outside |
| min-range | 20 / 48 | 0.26 / 0.18 | inside |
| max-range | 8 / 8 | 0.20 / 0.16 | all outside |

**Reading it, family by family:**

- **Off-boresight.** This is the result. Layer 0 and the grid agree for about 1.65 time units on
  both grids, even though the fine grid's tolerance is half as large; the longest stretch is 4.2.
  - The 36 inward departures are candidate junctions (§7 identifies 16 of them).
  - The 28 outward departures are not yet explained. They are test E's job (§9).
- **Min-range.** It sits next to the inner face, which M3 found leaks. It is unconfirmed rather than
  failed, and deprioritized.
- **Max-range.** The departure is correct (§5).

**Agreement length in $\tau$ is not distance in state.** A trajectory seeded next to a stagnation
point barely moves, so it collects "agreement" time while sitting at one state. The median is
robust to a few such cases, but a single trajectory's length can mislead.

---

## 5. Max range: leaving $\{V=0\}$ is the right answer

All 8 max-range trajectories leave early and outward. The barrier explorer shows why: the sheets
from the two BUP lenses run away from each other and enclose no volume. The numbers agree:

- **Each trajectory stays on its own face until it reaches the ridge.** It stays within about
  $2\times10^{-3}$ of its own face of $\bar R(\phi_2)$ until it crosses $\phi_2=0$, the kink of
  $\bar R$. The crossing comes at $\tau$ 0.08–0.17, depending on the seed.
- **The departure is tied to that crossing.**
  - On the coarse grid each trajectory departs 0.068–0.090 after its crossing, and on the fine grid
    0.040–0.059 after.
  - The lag shrinks with the tolerance, as it should if the crossing is the cause.
- **The grid agrees there is nothing to reach.** Past the crossing, $V=\ell$: player 1 cannot
  improve on the margin he already has.
- **The closing pieces are below grid resolution.** Layer 0's own corner work (corner family,
  universal line from $d_1$, dispersal line $e_1c_1O$, $c_1$) puts every closing piece within about
  $2.2\times10^{-3}$ in $R$ of the ridge. That is 30–60 times thinner than a grid cell.
- **D&S's two "small max-range capture zones" lie on the target set.** They are the usable part of
  the max-range face, bounded by the BUP lens and the ridge, and closed only in Fig. 8's
  $(\phi_2,\phi_1)$ projection.

**Consequences:**
- **Test B carries no information here.** The max-range rows of test B sit at or near the
  $\nabla\ell$ null (§6).
- **The corner family should not join the M4 bundle.** It would behave the same way.
- **For M5's test F, the recommendation is to exclude these zones.** $W_1$ contains them from the
  initial value alone.

---

## 6. Test B — gradient direction (the test to trust)

**It is scored as an angle, never as a relative error** (M1's trap). $V$ and $H$ both vanish on
the barrier, so dividing by them reports the barrier's defining cancellation as error.

**Every angle has a null beside it.** Near a seed, $\lambda$ *is* the face normal, by
transversality, so agreement there is partly owed to the seeding. The null is the same angle with
$\nabla\ell$ (the $\tau=0$ snapshot) in place of $\nabla V$. The solve earns credit only for doing
better than that.

| family | 101 (null) | 201 (null) |
|---|---|---|
| off-boresight | **1.94°** (34.3°) | **0.51°** (32.6°) |
| min-range | 11.15° (40.6°) | 6.75° (8.0°) |
| max-range | 18.36° (18.22°) | 0.17° (0.50°) |

**Reading it, family by family:**
- **Off-boresight is the strongest evidence M4 has.**
  - The angle is about 4 times smaller on the finer grid.
  - On the fine grid it is 64 times below the null, with 85 % of points within 10°.
  - Improving under refinement is what convergence to the right answer looks like.
- **Min-range is not informative on the fine grid.**
  - There the tighter tolerance keeps only points near the seeds, where $\lambda$ is still the face
    normal.
  - So the null is small too, and the grid barely beats it.
- **Max-range sits at or near its null**, as §5 explains.

---

## 7. Test C1 — controls, and the switch junctions

**What it checks.** A bang-bang control is the sign of one gradient component, and C1 compares
the grid's sign with Layer 0's on the retained points.

| | 101 | 201 |
|---|---|---|
| pursuer $\sigma_1^*$ | 96.6 % | 97.1 % |
| evader $\sigma_2^*$ | 97.5 % | 98.4 % |

**Results.** Both controls clear the 90 % criterion and improve with refinement. The rates where
the deciding component is clearly nonzero ($|V_i|\ge0.15$) are printed for information: 98–99 %.

**The switches.** At the Layer 0 switches inside retained segments (16 on the coarse grid, 14 on
the fine), the grid matches Layer 0's control **at** the switch 0 times. The reasons:

1. **At a switch, Layer 0 reports the post-switch control.** `barrier_controls` at a snapped zero
   returns the control for after the switch, by design. The grid matches Layer 0's **pre-switch**
   control every time: 16/16 and 14/14.
2. **Each switch is where its trajectory leaves the barrier.** Test A records an inward departure
   about 0.16 later, every time.
3. **They are not independent.** They come from 8 (coarse) and 7 (fine) neighboring seeds, in
   mirror pairs.
4. **They are not a Table 3 line.**
   - **Where they sit.** Every one lies on the plane $\phi_2=\pm135.00°$. Under $(-1,-1)$,
     $\dot\phi_1=\dot\phi_2$, so each trajectory reaches that plane at a $\phi_1$ fixed by its seed.
   - **They cross rather than touch.** They are transversal crossings of $\lambda_1=0$, with
     $\dot\lambda_1$ from $+0.07$ to $+0.72$.
   - **Table 3 has no pursuer switch line in this region.** All four sit at $R<0.6$.

**The nearby Table 3 structure: D&S's commuting line $S_1U_1$.** D&S fill the hole inside the
closed barrier trajectory $J_1E_1J_1$ with closed $(-1,-1)$ orbits around the stagnation point $S_1$.
The commuting line $S_1U_1$ (the pursuer's strategy $(0,-1)$) connects them. On those orbits,
$\lambda_1$ only *touches* zero, so $\sigma_1=-1$ never changes. `layer0/viz/commuting_s1u1.py`
builds the line.

**The construction:**
- **Control and costate.** It uses the same singular costate as the $d_1$ universal line,
  $\lambda=(\cos\phi_1,\ 0,\ -R\sin\phi_1)$, with $\sigma_1=0$.
- **Where it can start.** On that costate,
  $$H^*=R\sin\phi_1-1-\cos(\phi_1-\phi_2),$$
  which vanishes at every point of the stagnation curve $R=2\sin\phi_1$, $\phi_2=\pi-\phi_1$.
  Table 2's $S_1=(1.468,\ 47.24°,\ 132.76°)$ sits on that curve.

**The results:**
- **The line from $S_1$ lands on $U_1$.** It passes Table 2's $U_1=(1.721,\ 91.14°,\ 134.99°)$ at
  $3.6\times10^{-4}$, which is Table 2's own precision.
- **The reverse check agrees.** Searching from $U_1$ recovers $S_1$'s $\phi_1$ as $47.238°$.
- **The construction is exact.** Every invariant holds to $10^{-13}$.

So $S_1U_1$ is a reconstructed Table 3 line, with two newly placed Table 2 points.

**How the switches relate to it.** M4's 16 switch points sit 0.04–0.11 from the line. The switch
plane meets it at one point, $U_1$. That is also where $\dot\lambda_1$ on the plane passes through
zero, so Layer 0's crossing becomes a touch exactly where the commuting line ends.

---

## 8. The negative control

**What the plan asks for.** The old heuristic $\sigma_i=-\operatorname{sign}(\phi_i)$ must *fail*
test C at long range. A suite that passes both the right law and a known-wrong one tests nothing.

**What can be scored today, on the C1 points:**

| | 101: grid / heuristic | 201: grid / heuristic |
|---|---|---|
| pursuer $\sigma_1$ | 98.8 / 98.8 % | 99.2 / 99.2 % |
| evader $\sigma_2$ | 98.2 / 93.3 % | 99.1 / 92.3 % |

- **The evader's control discriminates**, and the gap widens on the finer grid.
- **The pursuer's control does not.** At these short ranges the heuristic agrees with the paper.

**The long-range version is a SKIP.** No retained Layer 0 point gets beyond $R\approx6.3$.

**$V$ couldn't serve as the reference out there anyway.** The report-only band table shows why:
- **Beyond $R\approx6$, $V=\ell$ on 81–99 % of grid points.** In the single-target game, player 1's
  heading doesn't change the margin he can guarantee there. So $V$ defines no $\sigma_1$ law to
  score anything against.
- **Where $V$ does define a law, the heuristic disagrees with it on only 2–9 %.**
- **So the long-range control needs a different reference:** M5's test F simulations, started at
  long range.

---

## 9. Tests D and E

**D — Table 2 points.** `validate_table2.py` carries 59 of Table 2's 60 points ($k_1$ is missing).
Of those, 26 lie on the target boundary $\partial T_1$, and at the 20 masked ones the analytic
$\ell$ vanishes to $8.8\times10^{-4}$.
- **It checks the target geometry, not the solve.** The points were selected because they satisfy
  the same surface equations.
- **What it does pin down.** It is a real check on $\bar R_0=3+\pi$ and on the index asymmetry.

**E — singular structure.** The detector flags grid nodes where a one-sided derivative changes
sign. It also flags $\ell$'s own kinks and smooth extrema, so it is run on $\ell$ alone as a null:

| | 101 | 201 |
|---|---|---|
| $\ell$ alone | 1.857 % | 0.911 % |
| converged $V$ | 2.203 % | 1.146 % |
| excess (the solve's own structure) | 0.346 % | 0.235 % |

**Closing test E means comparing that excess with D&S Table 3**, which is in `layer0/table3.py`:
- **Size.** 34 rows, all resolving to Table 2 points. 16 have both endpoints above the mask.
- **One line already rebuilt.** $S_1U_1$ is reconstructed (§7).
- **Inconsistent as printed.** $M_1n_1$ and $I_1P_1$: the control that changes doesn't match the
  player named.
- **Disagree with Layer 0's corner work.** $f_1c_1$ and $c_1O_1$.
- **A missing point.** `table3.py` also supplies Table 2's missing point $k_1$.

Each line type predicts what the grid should show on $\{V=0\}$ between its endpoints:

| Table 3 line type | what to look for in $V$ |
|---|---|
| dispersal, semidispersal | a jump in $\nabla V$ (a kink) |
| switch line | a sign change in the named player's $V_i$ |
| universal, commuting | that player's $V_i$ held near 0 |
| equivocal | gradient continuous, curvature jumps (hardest to see) |

---

## 10. What M4 does and does not establish

**Established**

- **On the off-boresight family, the grid and Layer 0 agree** where both apply, and the agreement
  holds or improves under refinement:
  - in level: 1.69 → 1.62, at half the tolerance;
  - in direction: 1.94° → 0.51°, against a null near 33°;
  - in control: 97–98 %.

  This is the external correctness check M3 could not provide, and it is M4's gate for the
  single-target solve.
- **The max-range departure is explained.** The sheets enclose nothing the grid can resolve, and
  the grid agrees ($V=\ell$).
- **The switch junctions are explained.** They are transversal $\lambda_1$ crossings on
  $\phi_2=\pm135°$, past which Layer 0's characteristics leave D&S's structure. They are not a
  Table 3 line.
- **D&S's commuting line $S_1U_1$ is reconstructed.** It matches Table 2's $S_1$ and $U_1$ to table
  precision.

**Not established (none of it blocks M5)**

- **The min-range family.** Most of it is untested, and the rest is unconfirmed next to the inner
  face.
- **A long-range negative control.** It moves to M5's test F.
- **Test E's comparison with Table 3,** and with it the 28 outward off-boresight departures.
- **C2 and anything about the two-target game.** Those are M5.

---

## 11. How to read a run

Run from `layer1/`, and save each run to a file:

```
python test_m4.py 101x102_T6 | Tee-Object m4_101x102.log
python test_m4.py 201x204_T6 | Tee-Object m4_201x204.log
```

**Start at the last line.** `M4 COMPLETE -- every asserted check passed; 1 SKIPPED` is the result
both logs show. Any `FAIL` names the check that broke. Lines without PASS, FAIL or SKIP are
information. The header should say `read ceil`.

| section | look at | in the logs |
|---|---|---|
| A, off-boresight row | tested/n, median | 64/66; 1.69 and 1.62 |
| A, min-range row | tested/n | 20/48, short, inward |
| A, max-range block | departure next to its $\phi_2=0$ crossing | each 0.04–0.09 after its crossing, outside |
| B, off-boresight row | angle vs bracketed null | 1.94° and 0.51°, nulls 34° and 33° |
| C1 | $\sigma_1$, $\sigma_2$ agreement | 96.6 / 97.5 % and 97.1 / 98.4 % |
| C1, switches | pre-side / at-switch | 100 % / 0 % inside retained segments |
| negative control | $\sigma_2$ heuristic vs grid | 93 % and 92 % vs 98 % and 99 %; SKIP line expected |
| D | max $\lvert\ell\rvert$ | $8.8\times10^{-4}$ |
| E | excess over the $\ell$ null | 0.35 % and 0.24 % |

**What would be a real problem in a future run:**
- an off-boresight median below 1 on either grid;
- an off-boresight angle not far below its null, or growing from 101 to 201;
- either control below 90 %;
- a crash.

---

## 12. Concepts worth having straight

**Read a value at a horizon no shorter than the point's own time.** $V$ only decreases with the
horizon, so reading early biases toward "outside". The bias then looks like a resolution effect.

**A pass rate needs a null.** Each of M4's headline numbers is only meaningful next to what a
trivial construction scores:
- test B against $\nabla\ell$;
- C1 against the old heuristic;
- test E against $\ell$'s own kinks.

Without the null, a high number may simply be owed to how the test was built.

**Untested is not passed.** A trajectory with no points above the mask was never compared with
anything.

**A control that passes for everything tests nothing,** and so does one that fails for everything.
Where a value is flat, its "law" is a tie-break, and agreement or disagreement with it means
nothing.

**Criteria set after seeing the answer are fragile.** For M5, fix the numeric criteria before the
solve runs.

**A departure is information, not a failure.** Under the 10-01 scoping, where a characteristic
leaves the barrier is the finding. Three kinds have been seen:
- the max-range sheets, which enclose nothing;
- the $\lambda_1$-switch junctions on $\phi_2=\pm135°$;
- the 28 outward off-boresight departures, which are still unexplained.

---

## 13. Quick file map

```
layer1/test_m4.py              the suite: A, B, C1, negative control, D, E
layer1/l0_traj.py              regenerates the 122-trajectory bundle from test_barrier.py's seeds
layer1/m4_101x102.log          the M4 run logs
layer1/m4_201x204.log
layer1/m3_out/Vsnap_*.npz      M3's V(., tau) snapshot stacks, read by test_m4.py
layer0/table3.py               D&S Table 3 as data, with Table 2 lookups
layer0/viz/commuting_s1u1.py   the S1 U1 commuting line, checked against U1 and the L0 switches
```

**Environment switches for `test_m4.py`:**
- `M4_READ`: `ceil` (the default) or `conv`;
- `M4_TOL`: pins the tolerance across grids;
- `R_MARGIN`: the $R$ mask, default 0.45;
- `LAYER1_ELL_SCALING`: `raw`, `plan` or `sdist`.

**Cost.** About 1 minute at $101\times102^2$ and about 4 minutes at $201\times204^2$.
