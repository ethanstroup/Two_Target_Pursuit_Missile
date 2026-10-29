# Layer 1 Close-Out — the 1v1 game of degree and the two-target partition

**AE 8900 · 2026-10-15 · Ethan Stroup**
Plan of record: `Overview/Layer1/Layer1_Plan.md` (revised 2026-10-01).
Spec of record: `Overview/ProblemStatement.md`.

This record is written to be read cold. It is the one document a Layer 2 plan should cite for
what Layer 1 delivers.

---

## What this closes

ProblemStatement §4 set Layer 1's task:
- solve a value function over the 1v1 game, giving a feedback law usable from any state;
- check it against Layer 0 and the D&S paper;
- include a negative control;
- show no long-range inversion.

§5.4 then fixed what Layer 1 must hand to Layer 2:
1. the 1v1 sets $W_1$, $W_2$, $D$ and the contested remainder $C$;
2. a stopping rule;
3. matching preferences.

**Status: Layer 1 is closed.**
- **What exists.** The partition is solved on two grids, with feedback laws and a verified
  simulator.
- **What it was checked against:**
  - Layer 0's barrier trajectories (M4);
  - D&S's corrected winning zones and both guarantee directions (M5);
  - the heuristic's long-range inversion (test C2, run today).
- **What is open.** §6 lists what is not closed. None of it blocks Layer 2.
- **What blocks Layer 2** is one decision, ProblemStatement §8 item 1 (the team objective), not
  work.

Per Ethan, 2026-10-15, Layer 2 is not started yet. The schedule slot for Layer 1 (weeks 3–6) ends
2026-10-20.

---

## 1. Milestones

| | what | state | headline | record |
|---|---|---|---|---|
| M1 | formulation, verified before any solve | DONE 09-14 | $\ell$ against `barrier.in_target`: 0 mismatches on 5.93 M nodes; $H$ against `hamiltonian_star` to 3 ulp | `Layer1_Progress_2026-09-14.md` |
| M2 | one-player smoke test ($\sigma_2\equiv0$) | DONE 09-14 | reach front at closing speed 2.003 against 2; the heuristic fails to beat $V$ by even one cell | the same, and `layer1/README_LAYER1.md` |
| M3 | converged two-player single-target solve | DONE 09-18 | barrier moves 0.16 coarse cells under 2× refinement; converged by $\tau=6$; edge at $R=6.100$; $V_2=V_1\circ S$ to $6.5\times10^{-13}$ | `Layer1_M3_2026-09-18.md` |
| M4 | acceptance against Layer 0 | DONE 10-07 | off-boresight family: level agreement for a median 1.65 in $\tau$; direction $0.51°$ against a $33°$ null; controls 97–98 % | `Layer1_M4_2026-10-06.md` |
| M5 | two-target partition by reach-avoid | DONE; pole rerun 10-15 is of record | 9 of 14 checks pass; guarantee 0 failures in 11,885 runs; converse 0 wins in 10,000; Table 2 0 / 17 misses; contested set fat | `Layer1_M5_2026-10-11.md`, `…_InnerFace_2026-10-13.md`, `…_PoleRerun_2026-10-15.md` |
| C2, long range | no long-range inversion | **PASS** 10-15 | every live state at $R\ge8$ is a guaranteed draw; the avoid law is killed in 0 of 53,290 runs; the harness reproduces the inversion | `Layer1_C2LongRange_2026-10-15.md` |

---

## 2. Acceptance against the plan (Plan §5)

| test | what it checks | state | where |
|---|---|---|---|
| A, level | $\lvert V\rvert<$ tolerance on Layer 0 trajectories | PASS on the off-boresight family. Max-range departures are the correct answer. Min-range is unconfirmed (§6) | M4 §3.1, §4.2, §4.4 |
| B, gradient | $\nabla V$ against the Layer 0 costate | PASS: $0.51°$ against a $32.6°$ null on the fine grid | M4 §3.2 |
| C1, controls on the barrier | bang-bang controls reproduced | PASS: 97.1 % / 98.4 %, and they improve with refinement | M4 §3.3 |
| C2, interior model | the trading player 2; $W_1$ starts still win; no long-range inversion | $W_1$ starts win against the trader (check 11, PASS). Race in $C$ reported (499 / 498 / 3). **Long range PASS** | M5 checks 11, C2; C2 record |
| D, Table 2 | $\{V=0\}$ through the placed points | on $\partial T_1$, a check of $\ell$ (M4). On $\partial W_1$: 0 / 12 and 0 / 5 misses (M5 check 10, PASS) | M4 §3.4; M5 |
| E, singular structure | kink locus against Table 3 | locus measured (excess 0.235 % of nodes). Compared with Table 3 on 2026-10-28: **FAIL** by one hit, with strong partial agreement (§6, item 1) | M4 §3.4; Test E record |
| F, two-target | D&S's corrected zones; guarantee simulations | Table 2 PASS; guarantee PASS; converse PASS; topology FAIL as specified, with the structure right | M5 |
| negative control | a known-wrong law must fail | M4: SKIP (no long-range Layer 0 points). M5 check 12: FAIL (the heuristic plays as well inside $W_1$). Covered from the other side by check 13 (PASS) and C2's LR-4 (PASS) | M4 §3.5; M5 §4.5; C2 |

**Every scored failure on record is diagnosed:**

| check | why it fails | where |
|---|---|---|
| M5 check 4, fine grid | a $0.042\,\delta$ asymmetry on the tail-chase line at $R\le0.15$; $W_1$ is exactly symmetric | PoleRerun §4.1 |
| check 5 | the scheme's non-monotonicity, $0.27\,\delta$ inside $T_{2\to1}$; the set inclusion holds | PoleRerun §4.4 |
| check 6 | sign noise on D&S's mutual-kill diagonal | PoleRerun §4.5 |
| check 9 | mis-specified; the components are right | M5 §4.6 |
| check 12 | the heuristic is good inside $W_1$ | M5 §4.5 |

All stay scored as failures, as run.

---

## 3. What Layer 2 receives (ProblemStatement §5.4 interface)

**1. The 1v1 partition.**
- **Fields of record:** the pole fields, adopted 2026-10-15.
  - Files: `layer1/M5/m5_out/m5_out_V1_pole/m5_<grid>_T6_pole_fields.npz` ($V^{RA}_1$) and
    `…_T6_single_pole_fields.npz` ($V_1$, with $t_1^*$ as `tRA`).
  - Grids: $101\times102^2$ and $201\times204^2$.
- **How to form the sets.** $W_1=\{V^{RA}_1\le0\}$; $W_2=W_1\circ S$ by axis transpose;
  $D=\{V_1>0\}\cap\{V_1\circ S>0\}$; $C=\Omega\setminus(W_1\cup W_2\cup D)$, with
  $\Omega=\{R\ge0.45,\ \ell_1>0,\ \ell_2>0\}$.
- **Shares on the fine grid,** as a share of $\Omega$:

  | $W_1$ | $W_2$ | $D$ | $C$ |
  |---|---|---|---|
  | 3.564 % | 3.564 % | 91.863 % | 1.060 % |

  $W_1$ and $W_2$ overlap on 0.05 %. That is the mutual-kill diagonal.
- **Reading the files.**
  - Rows are staggered, $R_i=(i+\tfrac12)\Delta R$, and the first 3 rows are mirror rows at $R<0$.
    Take $R$ from the file.
  - Values are stored as float32.
- **What $C$ is.**
  - The player-1 half (49.9 %) is exactly the part of M3's old "win-alone" set that player 1 cannot
    guarantee. The player-2 half (49.9 %) is its mirror.
  - The evidence supports reading $C$ as a draw, except a 0.2 % sliver where both players can force
    a kill (M5 §4.8; check 13 passes on the pole grids).
  - Whether Layer 2 treats it that way is §7's decision 2.

**2. The stopping rule.**
- Play stops at the first entry into a target set.
- Simultaneous entries, within $10^{-6}$, are classified as mutual kills, never by tie-break
  (`sim_m5.classify`).
- On the grid, the $W_1\cap W_2$ overlap is a tie, not a win for either side.

**3. Preferences.**
- The 1v1 ordering is fixed: win alone ≻ draw ≻ mutual kill ≻ die alone (Decision 2).
- $W_1$, $W_2$ and $D$ are guarantees, so they hold under any ordering. The team ordering is not
  fixed (§7).

**Also delivered.**
- **Feedback laws** read at the remaining horizon: `hji.make_policy`, and `sim_m5`'s vectorized
  equivalents, asserted equal.
- **The pole stepper,** which carries runs through $R=0$.
- **An exact inertial-frame simulator** (`inertial.py`).
- **The arrival-time field $t_1^*$.**
- **Verification code a Layer 2 solver can reuse:** the transpose identity check, reflection,
  ordering and convergence checks.

**Caveats for any consumer.**
- The horizon is $T=6$; the value is converged in horizon.
- Values on the outer row $R=12$ come from extrapolation (InnerFace §5.5).
- The fine $V$ carries the check 4 asymmetry on the tail-chase line, far from any zero set.

---

## 4. Findings worth carrying forward

1. **Comparing arrival times does not decide outcomes; reach-avoid does.**
   - $t_1^*$ and $t_2^*$ are guarantees from two different games.
   - The partition comes from a reach-avoid solve, which is the rigorous form of D&S's Appendix B
     correction and checkable against it (Revision 2026-10-01; M5).
   - This carries straight into Layer 2, which is reach-avoid with more sets.
2. **The contested set is real, fat, and a draw.**
   - It is 1.06 % of live states, with the same physical thickness on every grid.
   - D&S's draw zone hides it.
   - Player 2 can always stop player 1 there (check 13), and player 1 can always retreat safely,
     so it is a draw whenever a player prefers a draw to dying alone (M5 §4.8).
3. **The inner face is a pole, not a wall.**
   - The identity $(-R,\phi_1,\phi_2)\equiv(R,\phi_1+\pi,\phi_2+\pi)$ is exact for D&S's
     dynamics.
   - Using it fixed check 3, which had been the simulator stopping at the face. It also settled
     check 8, the old fine grid's own face (PoleRerun §4.2).
   - It also removes M2's frozen-evader breakdown (§5).
   - Layer 2 has two ranges, $R_1$ and $R_2$. The same identity should hold pair by pair, since each
     pair's equations have D&S's form (ProblemStatement §5.2). That has not been checked
     numerically.
4. **The heuristic's long-range "inversion" is both players pressing into a draw region** (C2).
   - From $R\ge8$ neither player can force a kill, and either can refuse.
   - Kills there need both to press. Most of the Layer 0 simulator's long-range "mutual kills" are
     near-simultaneous one-sided kills that its 0.01-step classification merges.
5. **Grid rules.**
   - $n_\phi$ must not be a multiple of 8, so that $\beta$ stays off-node (M3).
   - $n_\phi$ must be even for the pole.
   - $\ell$ uses the `sdist` weighting (Amendment 2026-09-15).
   - Field checks use the $R\ge0.45$ mask.
   - Check 4's asymmetry grew with refinement, so a Layer 2 grid should carry a reflection check.

---

## 5. Done at close-out (2026-10-15, on Ethan's go-ahead to finish Layer 1)

- **The pole fields are adopted** as M5's fields of record (PoleRerun decision 1).
- **Check 4 (fine) is accepted as diagnosed** and stays scored FAIL. Its mechanism is an optional open
  item (PoleRerun decision 2).
- **Checks 5, 6, 9 and 12 stay scored FAIL** as specified (M5 decision 4, unchanged).
- **Test C2 at long range was pre-registered and run: PASS** (`Layer1_C2LongRange_2026-10-15.md`).
  - Its criteria were written to Ethan's machine before the first run.
  - The harness first reproduced the logged coarse check 13 line for line.
- **M2's frozen-evader breakdown is closed (report only, `diag/diag_m2_pole.py`).**
  - README_LAYER1 had it open since 2026-10-01. On M2's own $101^3$ grid the old face reproduces it
    exactly: min $V=-14{,}594$ at $T=3$, with 3.29 % of nodes below the bound.
  - On the $101\times102^2$ pole grid the same solve keeps the bound $V\ge\min\ell=-0.785$ at every
    step to $T=3$. Its min $V$ is $-0.825$, at $R=1.85$, away from the face, with 0 nodes more than
    0.05 below the bound.
  - The $0.04$ undershoot is the scheme's, the same as M3's $-0.802$; the old grid shows it too
    before its face takes over.
  - $61\times62^2$ gives the same picture: the old face breaks at $\tau=2.75$, and the pole holds.
- **The parent records are amended:**
  - the M5 record (§1, §3.1, §5);
  - InnerFace (§6, §7);
  - PoleRerun (check 4's cause corrected, decision status);
  - the Plan's status;
  - `README_LAYER1.md`'s status table;
  - ProblemStatement §4, §5.4's interface heading and §10 (v0.7).

---

## 6. What is not closed (none blocks Layer 2)

1. **Test E against D&S Table 3.**
   - The excess kink locus is measured, but not yet compared with the 34 transcribed rows in
     `layer0/singular_lines/table3.py` (M4 open item 1).
   - The 28 outward off-boresight departures are candidates for it (M4 item 2).
   - *(Run 2026-10-28, pre-registered: `Overview/Layer1/Layer1_TestE_Table3_2026-10-28.md`.)*
     - **Score:** FAIL by one hit.
     - **What agrees:** 6 of 9 scored endpoints lie within 1 cell of the right player's switch
       locus on the barrier, against a bar of 7 and a chance probability of
       $1.6\times10^{-4}$. 30 of 36 samples of $S_1U_1$ lie on it.
     - **What misses:** $D_1$, $U_1$ and $I_1$. The grid's commuting line ends about $10°$ short of
       $U_1$.
     - **What it placed:** five more Table 2 points ($b_1$, $C_1$, $E_1$, $G_1$, $H_1$).
     - **Not compared:** the 28 outward departures.
2. **M4's min-range family.** It was untestable behind the old inner face, and it is testable on the
   pole fields now. Not run.
3. **The optional $J_1$ seed check** (M4 item 3).
4. **What causes the fine-grid check 4 asymmetry** (PoleRerun §4.1, decision 2b). The solve is
   float64, so it grows from roundoff; where and why is not known.
5. **The outer face $R=12$.** It is extrapolated, so a win that relies on play beyond 12 is not
   followed (InnerFace §5.5). This is a test-design choice; no scored check depends on it.
6. **C2 at long range on the fine grid.** It ran on the coarse grid, because the fine snapshot
   stacks are too large to move off Ethan's machine. `c2_longrange.py` runs there unchanged.
7. **Interior play is behavioral only.** The race model of Plan §2.3 is not shown to be an
   equilibrium, and is labeled assumption-dependent wherever it is reported. This is by design.
8. **Layer 0's carried items** ($f_1$'s marker; Table 3 assembly) are unchanged. For Layer 2's
   purposes, Layer 1's partition supersedes the assembly.

---

## 7. Decisions that remain Ethan's (the Layer 2 entry)

1. **The team objective and outcome ordering** (ProblemStatement §5.4, §8 item 1). Is losing one
   attacker to kill the bandit a win or a trade? Is the team objective max-min? **This blocks
   Layer 2's partition.** Building the six-state dynamics, the four target sets and the
   $R_2\to\infty$ regression does not depend on it.
2. **$C$ in the continuation after one attacker is lost:** a draw (the evidence supports it except
   for 0.2 %), or its own category (M5 decision 3).
3. **Layer 2's method.** A dense six-state grid is out: one float64 array is about 141 GB at $51^6$
   (ProblemStatement §5.5). The candidates are analytic results, low-dimensional slices, and the
   question of when separately solved subgames compose. It belongs in a Layer 2 plan.
4. **The $2\beta$ separation result** (ProblemStatement §8 item 3) has not been attempted. It is the
   leading candidate for a headline analytic result. It is a guarantee question, so it does not wait
   on decision 1.

---

## 8. Records and files

**Records**, in `Overview/Layer1/`:

| file | what it records |
|---|---|
| `Layer1_Plan.md` | the plan of record |
| `Layer1_Progress_2026-09-14.md` | M1, M2 |
| `Layer1_Amendment_2026-09-15.md` | the $\ell$ weighting |
| `Layer1_M3_2026-09-18.md` | M3 |
| `Layer1_Revision_2026-10-01.md` | the reach-avoid redefinition |
| `Layer1_M4_2026-10-06.md`, `Layer1_M4_Audit_2026-10-06.md` | M4 |
| `Layer1_M5_Criteria_2026-10-11.md` | M5's pre-registered criteria |
| `Layer1_M5_2026-10-11.md` | M5 |
| `Layer1_M5_InnerFace_2026-10-13.md` | the inner face and the pole condition |
| `Layer1_M5_PoleRerun_2026-10-15.md` | the M5 rerun on pole grids |
| `Layer1_C2LongRange_2026-10-15.md` | test C2 at long range |
| `Layer1_TestE_Table3_2026-10-28.md` | test E against D&S Table 3 (after the close-out) |
| `Layer1_CloseOut_2026-10-15.md` | this record |

The explainers (`Layer1_M*_Explainer.md`, `Layer1_M1_Explorer_2026-09-30.md`) are companions, not
records.

**Code**, in `layer1/`:
- `common/` (`ell.py`, `hji.py`), `M1/` to `M4/`;
- `M5/`: `reach_avoid.py`, `pole.py`, `sim_m5.py`, `inertial.py`, `smoke_m5.py`, `test_m5.py`,
  `converse_m5.py`, `c2_longrange.py`, `run_m5_pole.py`, `verify_pole.py`, and `diag/`.
- Run each script from its own milestone folder (`README_LAYER1.md`).

**Close-out runs, from `layer1/M5/`:**

```
python diag/diag_pole_rerun.py                         # PoleRerun Sec. 6 (~15 s)
LAYER1_POLE=1 python c2_longrange.py                   # test C2 at long range (~3 min here)
python diag/diag_m2_pole.py 101 102 3 101              # M2 frozen evader, old face vs pole (~25 min here)
```
