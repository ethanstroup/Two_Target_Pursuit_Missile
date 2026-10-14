# Layer 1 — M5 follow-up: the inner face and the pole condition

**AE 8900 · 2026-10-13 · Ethan Stroup**

This record is written to be read cold. It documents:
- why M5's checks 3 and 8 failed near $R\approx0.55$;
- the two fixes that were tried or considered;
- the fix adopted: a pole condition at $R=0$;
- how that fix was verified, what it established, and the decisions it leaves.

**The verification criteria in §4 were fixed before any of those tests ran.** Results are in §5.
The two diagnostics in §5.6 were added after the tests ran, and they are labeled report only.

**Bottom line.**
- **The pole condition passes all four pre-registered tests.**
- **Check 3 is fixed.** Its failures were the simulator stopping runs at the face, before a close
  pass that the grid had correctly counted as a win.
- **The game value hardly changes.** It moves only within 2 cells of its boundary.
- **Check 8 stays open.** Its flips are not caused by the coarse grid's inner face, and settling
  them needs a fine pole solve.

**Parent records:**
- `claude/Layer1_M5_2026-10-11.md` (§4.4) and `claude/Layer1_M5_Explainer.md` (§12);
- the pre-registered criteria `claude/Layer1_M5_Criteria_2026-10-11.md`.

---

## 1. The problem

M5's smoke check 3 freezes player 2 ($\sigma_2\equiv0$) and flies player 1's grid law from 500
states the grid scores as wins ($V^{RA}_1\le-\delta$). Every run should win.

**At $R_{\min}=0.2$, check 3 scored 498/500**, on $61\times62^2$ at $T=4$.
- The 2 failures started at $R=0.593$, the first row inside the $R\ge0.45$ mask.
- Both left the domain through $R=0.2$ before player 1 could shoot.
- The $101\times102^2$ grid gave the same two states $V^{RA}_1\approx-0.25$, and they exited
  there too. So this was not coarseness.

**Check 8 failed at the same place.** Its 6 coarse/fine sign flips that lie far from the barrier
all sat at $R=0.554$.

**Why the domain has an inner edge at all.** The reduced equations divide by $R$
($\dot\phi_i=L/R+\sigma_i$), and at $R=0$ the bearing angles are undefined. So the grid stopped at
$R_{\min}$, and `hj_reachability` filled values below it by linear extrapolation (outflow).

---

## 2. Fixes tried or considered

### 2.1 Moving the face to $R_{\min}=0.1$ (tried 2026-10-12, Ethan's machine)

Everything was switched to 0.1 (`hji.R_MIN_DEFAULT`, `sim_m5.R_LO_DOM`). The logs are in
`layer1/m5_out/rmin0.1/`.

| check 3, $61\times62^2$ | $R_{\min}=0.2$ | $R_{\min}=0.1$ |
|---|---|---|
| $T=4$ | 498 / 500 (pool 43,462) | **494 / 500** (pool 42,845) |
| $T=6$ | not run | 494 / 500 (pool 73,268) |

**Every inner-face failure exits through the new face, $R=0.1$.**
- At $T=4$ the failing starts sat at $R=0.497$, 0.695 and 1.092.
- One state, $(\phi_1,\phi_2)=(-5.81°,\ 17.42°)$, failed on the first masked row at both
  $R_{\min}$ values.
- At $T=6$, failing starts reached as high as $R=2.68$, diving to the face.
- Two more $T=6$ failures started exactly on the outer face $R=12$ with $\dot R>0$, so they left on
  the first step. That is a test artifact, discussed in §5.5.

**Conclusion.** The failures follow the face inward. Moving $R_{\min}$ only moves the problem, and
it doubles the cost.

### 2.2 A "no close pass" rule (considered, not adopted)

The rule would add the band $R<R_c$ ($R_c\approx0.2$, about 440 m) to player 1's avoid set:
$g=\max(-\ell_2,\ R_c-R)$. A win could then never rely on a close pass.
- **What it would cost.** It is a new modeling assumption, it shrinks $W_1$, and M3's $V_1$ would
  have to follow it.
- **Why it was set aside.** The pole condition (§3) represents passes exactly, without any new
  assumption. Its results (§5) show the close-pass wins are real, so this rule would have discarded
  genuine wins.

### 2.3 The pole condition (Ethan's proposal, adopted for verification)

Extend the grid through $R=0$ by mirroring. States "below zero" are the flipped states above it.

---

## 3. The pole condition

**The identity.** When the aircraft pass through each other, range goes through zero and the line
of sight turns by $\pi$:

$$(-R,\ \phi_1,\ \phi_2)\ \equiv\ (R,\ \phi_1+\pi,\ \phi_2+\pi).$$

**It is an exact symmetry of D&S Eqs. (1)–(3).** Put $R'=-R$ and $\phi_i'=\phi_i+\pi$. Both
$\cos$ and $\sin$ change sign, so

$$\dot R'=-\dot R=-(\cos\phi_1'+\cos\phi_2'),\qquad
\dot\phi_i'=\frac{\sin\phi_1+\sin\phi_2}{R}+\sigma_i=\frac{\sin\phi_1'+\sin\phi_2'}{R'}+\sigma_i,$$

with the controls unchanged. Checked numerically over $2\times10^5$ random states and controls:
the relative residual is $7.7\times10^{-15}$ (`pole.dynamics_equivariance`).

**The grid.**
- **Staggered so $R=0$ is never a node.** Real rows sit at $R=(i+\tfrac12)\Delta R$,
  $\Delta R=R_{\max}/(n_R-\tfrac12)$, and the last row is at $R_{\max}=12$.
- **Three ghost rows below zero,** at $-\tfrac12\Delta R$, $-\tfrac32\Delta R$, $-\tfrac52\Delta R$.
  That is WENO5's stencil half-width.
- **The mirror is index-exact.** Ghost row $k$ mirrors real row $5-k$ with both angles shifted by
  $n_\phi/2$ indices. $n_\phi$ = 62, 102 and 204 are all even.

**The implementation.** `layer1/pole.py`.
- **Why not a boundary function.** `hj_reachability` applies boundary conditions to one 1-D slice
  at a time, so a boundary function cannot fetch the opposite angles.
- **What is done instead.**
  - The ghost rows are ordinary grid rows. The dynamics are already correct at negative $R$, by the
    identity above.
  - After every time step they are overwritten with the mirrored values, through the same
    `value_postprocessor` hook the reach-avoid obstacle uses.
  - Within a Runge–Kutta step they are one step stale, which is the same compromise as the
    obstacle's placement.
- **The simulator.** `sim_m5.rollout` takes a `stepper`. `pole.stepper` sub-steps near $R=0$ so the
  line of sight turns by at most 0.05 rad per sub-step, and flips any trajectory that crosses
  $R=0$.

**Cost.** The explicit time step is

$$\Delta t=\frac{0.75}{\max_x\big[\alpha_R/\Delta R+2\,\alpha_\phi/\Delta\phi\big]},\qquad \alpha_\phi=\frac{|L|}{R}+1.$$

So it is set by the innermost rows, $R=\tfrac12\Delta R$:

| grid | innermost $R$ | step cost vs $R_{\min}=0.2$ |
|---|---|---|
| $101\times102^2$ | 0.06 | about 3× |
| $201\times204^2$ | 0.03 | about 6× |

At $61\times62^2$ the innermost row sits at $R=0.0992$, essentially where the $R_{\min}=0.1$ grid's
edge sits. There, pole and extrapolation compare at the same resolution and time step.

**What changes for analysis.** The staggered $R$ rows don't nest under 2× refinement; the angles
still do. Coarse/fine comparisons in $R$ therefore need averaging or interpolation, not exact
subsampling.

---

## 4. Verification plan (criteria fixed before the tests ran)

The four tests are independent of one another, and each one checks one part of the
construction.

### V1 — the grid against exact truth, through the pass

- **Setup.** Both turn rates frozen, at $(0,0)$ and at $(+1,-1)$, on the $61\times62^2$ pole grid
  with $T=4$.
- **The truth** is computed in an **inertial frame**.
  - Each aircraft flies a straight line or a circle, in closed form, sampled every $10^{-3}$.
  - $R,\phi_1,\phi_2$ come from the positions, and a pass is just two points getting close.
  - There is no flip, no reduced equation and no singularity anywhere in the truth.
  - The reach-avoid outcome $\min_t\max\{\ell_1,\max_{s\le t}(-\ell_2)\}$ is taken along each path,
    for every real node.
- **Pass:** 0 sign disagreements more than 2 cells from either zero set. Only paths that leave
  through $R=12$ are excluded.
- **Informative only if** at least 1000 nodes' exact paths come inside $R<0.25$.
- **Report only.** The same comparison on the $R_{\min}=0.1$ extrapolation grid, as the "before".

### V2 — the simulator against exact kinematics

- **Setup.** Check 3's 500 starts on the pole grid ($T=4$, seed 0), player 1 on the grid law,
  $\sigma_2\equiv0$.
- **Two integrations:**
  - (a) reduced coordinates with `pole.stepper`;
  - (b) inertial coordinates, with exact arcs over each control interval and bisection on the exact
    arcs for kill times. No flip is needed in (b).
- **Pass:** all 500 win in (b), and the outcome matches (a) for every start.
- **Report.** Kill-time differences between (a) and (b), and how many (b) runs pass inside
  $R<0.25$.

### V3 — nothing else changed; the near-face values settle

- **Setup.** The real game on the pole grid, $101\times102^2$ at $T=6$, for both $V^{RA}_1$ and the
  single-target $V_1$. It is compared with the existing $R_{\min}=0.2$ fields, linearly
  interpolated in $R$ onto the pole nodes; the angles coincide.
- **Pass:** for each of $V^{RA}_1$ and $V_1$, at $R\ge1$, 0 sign disagreements more than 2 cells
  from either zero set.
- **Report.**
  - Disagreements by $R$ band.
  - $W_1$ over $\Omega$, old vs pole.
  - $W_1$ at $R<1$ on the 51-row and 101-row pole grids, as a convergence check near the face.

### V4 — the guarantees near the face, on the coarse pole grid

- **(a) Near-face guarantee.** Starts are all nodes with $0.45\le R<1$, $V^{RA}_1\le-\delta$, in
  $\Omega$, capped at 1000 (seed 0). Player 1 flies the reach-avoid law against the five player-2
  laws of criteria §3.4, using the pole grid's own $V_1$ and $t_1^*$.
  - **Pass:** 0 failures.
  - **Report only:** the same near-face test on the $R_{\min}=0.2$ coarse grid, as the "before".
- **(b) Check 11 on the pole grid,** with 2000 uniform starts plus component top-ups. **Pass:**
  0 failures.
- **(c) Check 13 on the pole grid,** the converse. **Pass:** 0 wins alone against the reach-avoid
  adversary, with at least 20 informative starts.

**Overall.** The pole condition is confirmed if V1–V4 all pass. If any fails, its failures are
reported and diagnosed, and the fine runs wait.

---

## 5. Results

**All four tests pass, so by §4's rule the pole condition is confirmed.**

| test | what it checks | criterion | result | verdict | "before" |
|---|---|---|---|---|---|
| V1 $(0,0)$ | grid vs exact truth through the pass | 0 far flips, $\ge1000$ close paths | 0 of 356; 8,681 | **PASS** | also 0 |
| V1 $(+1,-1)$ | same, turning | same | 0 of 2,165; 9,732 | **PASS** | also 0 |
| V2 | simulator vs exact kinematics | 500/500 exact wins, outcomes identical | 500/500; 500/500 | **PASS** | — |
| V3 $V^{RA}_1$ | nothing else changed | 0 far flips at $R\ge1$ | 0 (and 0 at $R<1$) | **PASS** | — |
| V3 $V_1$ | same | same | 0 (and 0 at $R<1$) | **PASS** | — |
| V4(a) | guarantee near the face | 0 failures | 0 of 5,000 | **PASS** | also 0 |
| V4(b) | check 11 on the pole grid | 0 failures | 0 of 10,130 | **PASS** | — |
| V4(c) | check 13 on the pole grid | 0 wins vs adversary, $\ge20$ informative | 0 of 10,000; 270 | **PASS** | — |

Two of the "before" comparisons pass as well, so those tests show the new grid is right without
showing the old one wrong. What the old face actually broke is pinned down in §5.6.

### 5.1 V1 — the grid against exact truth

Both grids are $61\times62^2$ (234,484 real nodes), $T=4$. "Far" means more than 2 cells from
either zero set. "Below the edge" counts exact paths that dip under the grid's innermost row
($R=0.0992$ pole, $R=0.1$ extrapolation).

| controls $(\sigma_1,\sigma_2)$ | grid | disagreements (all / far) | paths inside $R<0.25$ | below the edge | excluded at $R=12$ | $\lvert V-J\rvert$ median / 95th |
|---|---|---|---|---|---|---|
| $(0,0)$ | **pole** | 356 / **0** | 8,681 | 3,756 | 40,869 | 0.0000 / 0.0133 |
| $(0,0)$ | $R_{\min}=0.1$ extrapolation | 360 / 0 | 8,681 | 3,815 | 40,869 | 0.0000 / 0.0122 |
| $(+1,-1)$ | **pole** | 2,165 / **0** | 9,732 | 5,113 | 27,107 | 0.0044 / 0.0429 |
| $(+1,-1)$ | $R_{\min}=0.1$ extrapolation | 2,263 / 0 | 9,732 | 5,197 | 27,111 | 0.0044 / 0.0433 |

The truth's own checks: converting reduced to inertial and back reproduces the state to
$1.8\times10^{-15}$, and one reduced step matches the exact arc to $5.6\times10^{-13}$.

**V1 passes for both control pairs.** The pole grid has no sign error away from the zero sets,
and the test is informative: 8,681 and 9,732 nodes have exact paths inside $R<0.25$, well over the
bar of 1000. Of those, 3,756 and 5,113 pass below the innermost row, so they cross the ghost rows.

**The "before" passes as well.** With both turn rates frozen, the $R_{\min}=0.1$ extrapolation
grid is just as accurate. So V1 shows the pole grid is right, but it does not show the old face
wrong. With frozen controls, the value near the pass is evidently smooth enough for a linear
extrapolation. The old face's trouble therefore lay elsewhere. The candidates were the simulator,
which stopped every run at $R_{\min}$ (§5.2), and the game value, where the controls are optimized
(V3, V4). For check 3, §5.6 shows it was the simulator.

### 5.2 V2 — the simulator against exact kinematics

| check 3 starts, $61\times62^2$ pole grid, $T=4$ | win alone | other |
|---|---|---|
| (a) reduced coordinates + `pole.stepper` | 500 | 0 |
| (b) exact inertial arcs | 500 | 0 |

**V2 passes.** All 500 runs win in the exact frame, and (a) and (b) agree for every start.
- **Kill times agree.** Median difference $6.9\times10^{-14}$, 99th percentile
  $4.3\times10^{-10}$. The largest difference is 0.011, in a run that wins both ways.
- **The close-pass wins are real.** 6 of the exact runs pass inside $R<0.1$, and all 6 win. In the
  exact frame nothing special happens at the pass: two aircraft go by each other and player 1
  shoots afterward.
- **This is what failed before.** At $R_{\min}=0.2$ and $0.1$, the simulator ended runs like these
  at the face and scored them "exited domain" (§2.1). The pole stepper follows them through the
  pass.

### 5.3 V3 — nothing else changed

**The solves.** $101\times102^2$ pole grid, $T=6$, $\delta=0.1194$.
- $V^{RA}_1$ took 5,693 s and $V_1$ took 4,836 s, with the two running side by side on the
  container's two cores. So these times can't be compared with the old run's 895 s to
  $\tau=6$.
- The surface moved 0.034 % and 0.032 % in the last 0.25 step, against check 7's bar of 0.5 %. So
  $T=6$ is still converged.

**Sign disagreements, pole vs $R_{\min}=0.2$.** Entries are all disagreements / those more than 2
cells from either zero set.

| $R$ band | nodes compared | $V^{RA}_1$ | $V_1$ |
|---|---|---|---|
| $[0.45,\ 1)$ | 27,595 | 228 / **0** | 236 / **0** |
| $[1,\ 2)$ | 53,361 | 42 / **0** | 36 / **0** |
| $[2,\ 4)$ | 121,743 | 62 / **0** | 76 / **0** |
| $[4,\ 12]$ | 687,427 | 56 / **0** | 10 / **0** |

**V3 passes for both fields.** There are no far disagreements anywhere, not only at $R\ge1$. Every
change sits on the boundary, and most of them in the band next to the face.

**The partition barely moves.**

| share of $\Omega$ | $W_1$ | $D$ | $C$ | $\Omega$ nodes |
|---|---|---|---|---|
| $R_{\min}=0.2$, coarse | 3.5746 % | 91.6580 % | 1.1940 % | 899,333 |
| pole, coarse | 3.5647 % | 91.7140 % | 1.1567 % | 890,126 |

The node counts differ because the pole grid's rows sit at different $R$.

**Near the face, $W_1$ is about one point smaller on the pole grid.** Share of $\Omega$ in $W_1$ at
$0.45\le R<1$:

| grid | rows | $W_1$ share |
|---|---|---|
| pole | 51 | 17.79 % |
| pole | 101 | 18.68 % |
| $R_{\min}=0.2$ | 101 | 19.69 % |
| $R_{\min}=0.2$ | 201 | 20.45 % |

- Both families grow under refinement, so the converged share is not yet known.
- At the same resolution, the pole grid gives about 1 point less. The sign changes behind that
  are the 228 disagreements in the first row of the table above, all within 2 cells of the
  boundary.
- The old fine row was added after V3 ran (§5.6).

### 5.4 V4 — the guarantees near the face

All three parts use the coarse pole grid at $T=6$, player 1's reach-avoid law, and the pole
stepper.

| part | starts | runs | failures | verdict |
|---|---|---|---|---|
| (a) near face, $0.45\le R<1$ | 1000 of a pool of 3,594 | 5,000 | **0** | PASS |
| (a) "before", $R_{\min}=0.2$ grid | 1000 of a pool of 3,704 | 5,000 | 0 | report only |
| (b) check 11 | 2,026 of 22,550 | 10,130 | **0** | PASS |

**(c) Check 13 passes.** The pool holds 2,006 starts (the old grid had 2,030) and 2,000 were drawn.
- Against the reach-avoid adversary, no player-1 law wins alone in 10,000 runs.
- The test is informative: the single-target law beats the avoiding player 2 from 270 starts,
  against a bar of 20. The old coarse grid gave 279.
- Every outcome count is within 25 of the old coarse grid's, out of 2,000 starts.
- Check 13's starts sit at $R=3.9$ to 4.7 (10th to 90th percentile), far from the face. So this
  part confirms that nothing changed rather than testing the face.

**The "before" in (a) passes too.** Against the five player-2 laws, the old grid's near-face
starts also all win, with the old simulator that stops at $R=0.2$. A likely reason is that all
five laws maneuver, while check 3's player 2 flies straight into the close pass; this was not
tested. Either way, V4(a) shows that the pole grid keeps the guarantee near the face. It does not
show that the old grid lost it there.

### 5.5 The two outer-face failures at $T=6$

Check 3 on the pole grid at $T=6$ scored 498/500. The two failures are not about the pole:

| start $(R,\phi_1,\phi_2)$ | grid $V$ | outcome |
|---|---|---|
| $(12.000,\ +168.39°,\ -23.23°)$ | $-0.221$ | exited at $t=0.002$ |
| $(12.000,\ -162.58°,\ +23.23°)$ | $-0.223$ | exited at $t=0.002$ |

- **Both start on the outer row, opening.** For the first,
  $\dot R=-(\cos168.39°+\cos23.23°)=+0.06>0$, so the run leaves through $R=12$ on its first step.
- **The grid has the same blind spot outward.** Values at $R=12$ are also set by extrapolation, so
  a win there can rely on play beyond $R=12$ that the simulator does not follow.
- **The same two states fail in Ethan's $R_{\min}=0.1$ run at $T=6$** (§2.1), with the same
  values. Neither appears at $T=4$.
- **Status.** This is the outer face's own artifact. It is separate from the inner face and is not
  addressed by the pole condition. Any check that draws starts on the outer row can hit it; check
  11 and V4(b) did not.

### 5.6 Report-only diagnostics (added after V1–V4 ran; not pre-registered)

V1 and V4(a) passed on the old grid too, so two more questions needed direct answers. Neither
diagnostic has a pass bar; both are reported as found.

**D1 — every old check 3 failure, re-flown on the pole grid** (`diag_pole_oldfails.py`). The 12
inner-face failures from §1 and §2.1 are re-flown on the $61\times62^2$ pole grid with $\sigma_2\equiv0$.

| failed at | $T$ | starts | pole-grid $V$ | (a) reduced + pole stepper | (b) exact inertial | closest pass in (b) |
|---|---|---|---|---|---|---|
| $R_{\min}=0.2$ | 4 | 2 | $-0.29$, $-0.26$ | 2 wins | 2 wins | $R=0.001$, 0.025 |
| $R_{\min}=0.1$ | 4 | 6 | $-0.43$ to $-0.21$ | 6 wins | 6 wins | $R=0.017$ to 0.099 |
| $R_{\min}=0.1$ | 6 | 4 | $-0.53$ to $-0.23$ | 4 wins | 4 wins | $R=0.047$ to 0.087 |

- **All 12 win, in both integrations, with kill times equal to within 0.001.** Every one wins by
  flying through a pass closer than $R=0.1$. One of them goes by at $R=0.001$, about 2 m.
- **The old grid's values were right.** The pole grid's value at the two original starts is
  $-0.293$ and $-0.255$. The old $61\times62^2$ grid had $-0.289$ and $-0.255$.
- **So the check 3 failures were the simulator, not the value.** The old grid correctly said
  "win", and the win runs through a close pass. The old simulator stopped each run at the face, at
  $R=0.2$ or $0.1$, before the pass.

**D2 — check 8's six far flips** (`diag_pole_check8.py`). Check 8 failed on 6 coarse/fine sign
flips at $R=0.554$, more than 3 cells from the barrier. Here is the coarse pole grid at the same
states, interpolated in $R$.

| $R$ | $\phi_1$ | $\phi_2$ | old coarse | old fine | pole coarse |
|---|---|---|---|---|---|
| 0.554 | $\mp24.71°$ | $\pm28.24°$ | $+0.183$ | $-0.036$ | $+0.258$ |
| 0.554 | $\mp21.18°$ | $\pm24.71°$ | $+0.224$ | $-0.020$ | $+0.267$ |
| 0.554 | $\mp17.65°$ | $\pm21.18°$ | $+0.274$ | $-0.007$ | $+0.274$ |

(Each row is a mirror pair under $Rf$.)

- **The pole grid sides with the old coarse grid, at all 6 states.** So the flips are not caused by
  the coarse grid's inner face.
- **What remains possible.**
  - The fine grid's own face, 6 fine cells away at $R=0.2$, could create a thin false sliver of $W_1$.
  - Or the sliver is real but shallow. The fine values there are $-0.007$ to $-0.036$, less than
    one fine cell ($\delta=0.059$), which could be too thin for either coarse grid to resolve.
- **What these states are.** Roughly head-on at $R=0.55$, about 1.2 km, closing at about 1.8. They
  meet in about 0.3 time units unless one turns away, so these states sit right where the pass
  matters.
- **What would settle it.** A fine pole solve. Check 8 stays failed until then.

The near-face $W_1$ share of the old fine grid, 20.45 %, comes from the same script. It is the last
row of the table in §5.3.

---

## 6. What this establishes

**Established**
- **The pole construction is correct.**
  - The grid matches exact inertial truth through the pass (V1).
  - The simulator matches exact kinematics (V2).
  - The flip is an exact symmetry, to $7.7\times10^{-15}$, and the ghost rows match the mirror
    exactly at the end of the solve.
- **It changes nothing it shouldn't.**
  - There are no far sign changes anywhere (V3).
  - The partition shares move by less than 0.04 points.
  - Checks 11 and 13 pass on the pole grid (V4).
- **It fixes check 3.** All 12 inner-face failures seen so far win on the pole grid (D1). Check 3
  scores 500/500 at $T=4$. At $T=6$ it scores 498/500, and both remaining failures are the outer
  face (§5.5).
- **The close-pass wins are real.** They hold in an exact inertial frame with no reduced equation,
  passing as close as $R=0.001$ (V2, D1).

**Corrected by this work**
- **The M5 record (§4.4) said the value "counts on play below $R=0.2$, which the domain does not
  contain."** For the game value that turned out mild.
  - The extrapolated face gave nearly the right values (V1, D1).
  - Only the boundary moved, by about a point of near-face share (V3).
  - The dominant failure was the simulator stopping at the face.

**Not established**
- **Check 8.** The six flips at $R=0.554$ are not explained by the coarse inner face (D2). A fine
  pole solve is needed.
- **Where the near-face $W_1$ share converges.** It grows under refinement on both grid families
  (§5.3).

---

## 7. Decisions for Ethan

1. **Adopt the pole condition, grid and simulator together, for M5 and Layer 2?** *Recommended.*
   - **Keep the two together.** `pole.stepper` costs nothing, but on an old grid a run through the
     pass would read clamped values below $R_{\min}$. The stepper belongs with the pole grid.
   - **Grid cost.** About 3× per step at $101\times102^2$ and about 6× at $201\times204^2$.
   - **One complication.** The staggered rows don't nest under 2× refinement, so check 8 would
     compare coarse and fine by interpolating in $R$.
2. **How much of M5 to rerun.**
   - **Check 3** is already done on the pole grid: 500/500 at $T=4$ (§5.2).
   - **Check 8** needs the fine pole solves of $V^{RA}_1$ and $V_1$. The old fine solve took 4.6 h
     in the container, so each would take roughly a day there. How check 8 is scored on grids that
     don't nest is fixed in §8.
   - **M3 itself does not need rerunning.** The pole-grid $V_1$ comes from
     `LAYER1_POLE=1 reach_avoid.py <n_R> <n_phi> 6 single`. That is the same solve as
     `solve_m3.py`: the same dynamics, solver settings, $\ell$, and 0.25 step for $t_1^*$, on the
     pole grid. V3 found it differs from M3's field only within 2 cells of the boundary, so M3's
     record stands. The coarse and fine `single` pole solves are what M5 needs.
   - **M4's min-range family** (M4 open item 4) was untestable because of the inner face. On pole
     fields it could be tested. This is optional.
   - **The other checks.** V3 and V4 suggest they would not change, but only the coarse grid was
     tested.
3. **The outer face** (§5.5). Two options:
   - keep starts at least 2 cells inside $R=12$;
   - or score an exit through $R=12$ separately from a failure.

   This is a test-design choice, and it only matters for check 3 so far.

Whatever is rerun gets scored against the original M5 criteria, and the M5 record is amended with
this file as the reason.

*(2026-10-13.)* Ethan chose to rerun M5 on the pole grids. The suite and an unattended driver for
it are in §9.

---

## 8. Check 8 on pole grids (procedure fixed 2026-10-13, before any fine pole solve)

**The problem.** Check 8 compares the coarse $\{V^{RA}_1\le0\}$ with the fine field at the coarse
nodes. On the $R_{\min}=0.2$ grids that was exact subsampling, `Vf[::2, ::2, ::2]`. Pole rows are
staggered, so fine rows never land on coarse rows.
- At $101\to201$ rows, each coarse row is 0.25 to 0.5 of a fine cell from the nearest fine row,
  rising toward the face: 0.48 at $R=0.54$, 0.25 at $R=6$ and 0 at $R=12$.
- The angles still nest exactly: fine node $2k$ is coarse node $k$.

**The procedure.** Interpolate the full fine pole field, ghost rows included, linearly in $R$ onto
the coarse rows, and take every second angle. Then score check 8 exactly as pre-registered:
displacement $\le0.5$ coarse cells, and 0 flips more than 3 coarse cells from the coarse barrier.
The bracketing fine rows for the first coarse row ($R=0.060$) are $R=0.030$ and $0.090$, both real.

**Why it is safe** (`diag_check8_interp.py`, report only). On the $R_{\min}=0.2$ grids, where the
answer is known, check 8 was scored twice. The second scoring rebuilt each coarse node from the two
fine rows either side, skipping the coincident row. That is a midway point across two fine cells,
so its error is about 4 times the pole grids' worst.

| fine value at coarse node | displacement | far flips | all flips |
|---|---|---|---|
| exact, as scored in M5 | 0.393 | 6 | 1,632 |
| interpolated, rows $2i\pm1$ | 0.402 | 6, the same nodes | 1,670 |

- The interpolated sign differs from the exact one at 322 of 1,019,592 nodes, all within one
  coarse cell of the fine zero set.
- Interpolation can't make a far flip: away from the zero set both bracketing rows have the same
  sign, and so does any value between them.
- So the verdict, the far-flip set, and the displacement to within 0.01 cell are unchanged.

**Two consequences.**
- A pole check 8 can be compared with M5's directly; it is not a different test.
- Its displacement carries a small upward bias, under 0.01 coarse cells by this test.

---

## 9. Rerunning M5 on the pole grids (set up 2026-10-13)

**What runs.** `python run_m5_pole.py` from `layer1/` runs the whole M5 sequence on pole grids,
unattended. It writes one log per step to `m5_out/pole_run/`, and if it is stopped, starting it
again resumes.

| step | what | needed for |
|---|---|---|
| 1 | smoke checks 1, 1b, 2, 3 at $61\times62^2$, $T=4$ | smoke |
| 2–3 | coarse march to $\tau=10$, horizon rule, cut at $T_{RA}$ | $T_{RA}$; coarse $V^{RA}_1$ |
| 4 | coarse $V_1$ (`single`) | checks 5, 6, 11–13 on coarse |
| 5–6 | $51\times52^2$ game and $V_1$ | thin / fat |
| 7 | checks on coarse and third grids | preview |
| 8–10 | fine game, check 8 preview, fine $V_1$ | the scored checks |
| 11–12 | `test_m5.py` and `converse_m5.py` | the record |

**The criteria are unchanged.** Every check is scored as pre-registered in the M5 criteria file.
Two procedures follow the grid, both fixed before any pole run:
- **Check 8** interpolates the fine field in $R$ (§8).
- **Smoke check 2** takes its exact reference from the inertial frame, as V1 did (§4). Paths pass
  through $R=0$, and only exits through $R=12$ are excluded.

**What changed in the scripts** (all switched by `LAYER1_POLE=1`, which the driver sets):
- `test_m5.py` and `converse_m5.py` read the `_pole` runs and take $V_1$ and $t_1^*$ from
  `reach_avoid.py ... single` on the same grid. Field checks use the rows at $R>0$. Rollouts use
  the full grid, its mirror rows and `pole.stepper`.
- `smoke_m5.py` builds the pole grid and uses the pole fill in both forms of check 1b.
- `sim_m5.rollout` defaults to `pole.stepper` with no inner exit.
- Pole output names carry `_pole`, json included, so no $R_{\min}=0.2$ file is overwritten.
- A grid whose $V_1$ isn't solved yet gets the checks that need only $V^{RA}_1$: 4, 7, 8, 9 and 10.

**How it was tested.**
- **Old grids, without the switch.** The suite reproduces M5's recorded `test_m5_T6.log` and
  `converse_m5_T6.log` exactly: every check value, run count and outcome table. The only
  differences are labels (check 8 now names its method, "R subsampled").
- **Pole grids, end to end.** The driver ran start to finish on $26\times26^2$ / $51\times52^2$ /
  $14\times14^2$ grids, sequentially and with `--parallel-fine`, with identical results.
  Resuming and the skip of an incomplete solve were exercised too.
- **The smoke checks** ran in pole mode at $21\times22^2$, and all passed.

**Time on Ethan's machine** (estimated: the solver is about 1.7× faster there than in the
container, numpy about 2× slower):

| part | estimate |
|---|---|
| steps 1–7 | about 2.5 h |
| each fine solve | about 16–17 h ($\approx6\times$ the old fine solve's cost) |
| steps 11–12 | under 1 h |
| total, in sequence | about 36 h |

---

## 10. Files and reproducing

```
layer1/pole.py                  the pole grid, mirror fill, solver settings, simulator stepper
layer1/inertial.py              exact inertial kinematics, conversions, inertial rollouts (V1, V2, D1)
layer1/verify_pole.py           V1-V4:  python verify_pole.py v1|v2|v3|v4 [n_R n_phi]
layer1/diag_pole_check3.py      check 3 on the pole grid:  python diag_pole_check3.py [T]
layer1/diag_pole_oldfails.py    D1: the 12 old check 3 failures on the pole grid
layer1/diag_pole_check8.py      D2: check 8's flips on the pole grid; near-face W_1 shares
layer1/diag_check8_interp.py    Sec. 8: check 8 with interpolated vs exact fine values (old grids)
layer1/run_m5_pole.py           Sec. 9: the M5 rerun on pole grids; logs in m5_out/pole_run/
layer1/diag_check3_rmin.py      check 3 at a chosen R_min (Sec. 2.1)
layer1/sim_m5.py                rollout() takes a stepper and an inner exit radius; f() guards R = 0
layer1/reach_avoid.py           LAYER1_POLE=1 solves on the pole grid; outputs tagged _pole
layer1/m5_out/rmin0.1/          Ethan's R_min = 0.1 smoke and diagnostic logs (Sec. 2.1)
layer1/m5_out/pole/             every log and json named in this record
layer1/m5_out/m5_<grid>_T6[_single]_pole_fields.npz, m5_<grid>_T6[_single]_pole.json
                                the pole fields (float32) and solve diagnostics
layer1/m5_out/Vsnap_RA_<grid>_T6[_single]_pole.npz
                                for visualization (added 2026-10-13, after the tests):
                                V(., tau) every 0.5, real rows only, with R, phi1, phi2
```

Run from `layer1/`. Times are for the 2-core container.

```
python3 diag_pole_check3.py 4                                    # check 3, pole (~3 min)
python3 diag_pole_check3.py 6                                    # (~4 min)
LAYER1_POLE=1 python3 reach_avoid.py 101 102 6 game              # coarse V_RA, pole (~1.5 h)
LAYER1_POLE=1 python3 reach_avoid.py 101 102 6 single            # coarse V_1, pole (~1.4 h)
LAYER1_POLE=1 python3 reach_avoid.py 51 52 6 game                # third grid, pole (~3 min)
python3 verify_pole.py v1                                        # (~45 min)
python3 verify_pole.py v2                                        # (~3 min)
python3 verify_pole.py v3                                        # (~1 min)
python3 verify_pole.py v4                                        # (~3 min)
python3 diag_pole_oldfails.py                                    # D1 (~6 min)
python3 diag_pole_check8.py                                      # D2 (~1 min)
```

The pole snapshot stacks (108 MB each at $101\times102^2$) stay in the session workspace. Rerunning
the solves rebuilds them.

**Reading pole files.** Pole rows are staggered, $R_i=(i+\tfrac12)\Delta R$, and the full-grid files
(`VRA`, `tRA`, `VRAsnap`, `fields`) keep the 3 mirror rows at $R<0$. Take $R$ from the file
(`R` in the fields npz, or `R_nodes` in the json), never from `linspace(0.2, 12, n_R)`. `Vsnap_RA`
drops the mirror rows.

**A fix made afterward (2026-10-13).** `reach_avoid.py cut` used to drop a `_single` or `_pole`
suffix from the tag it wrote, so a cut of a pole march would have overwritten the
$R_{\min}=0.2$ files. It now keeps the suffix. No run in this record used `cut`, and M5's one cut
(`101x102_T10` to $T=6$, game) had no suffix, so no result changes.
