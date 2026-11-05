# Layer 1 — M5 Explainer

**AE 8900 · reference doc · rewritten 2026-10-14 · updated 2026-10-16 for the pole rerun and the
Layer 1 close-out**

This walks through M5 in the order it runs. It covers what M5 computes, then every check from 1 to 13,
then what the checks add up to.

**How to read it.**
- **§0** is the whole milestone on one page, with the scorecard.
- **§1–6** are the background the checks need. Skip to §7 if you already know it.
- **§7–11** are the checks, in the order they run. Every check is laid out the same way:
  *question*, *how*, *pass if*, *result*, *what it means*.
- **§12–16** put it together: what M5 shows, the inner-face follow-up, how to read a run, and the
  file map.

**Where the numbers come from.**
- Part B's numbers are from the original M5 run of 2026-10-11, with its inner face at
  $R_{\min}=0.2$.
- The 2026-10-13 follow-up replaced that face with a pole condition. The whole sequence was then
  rerun on pole grids (2026-10-13/14), and **that rerun is of record**.
- Where the rerun changes a check, the check says so. §0's scorecard shows both runs, and §13
  collects the rerun.

**Companion docs:**
- the M5 record `Overview/Layer1/Layer1_M5_2026-10-11.md`;
- the pre-registered criteria `Overview/Layer1/Layer1_M5_Criteria_2026-10-11.md`;
- the inner-face record `Overview/Layer1/Layer1_M5_InnerFace_2026-10-13.md`;
- the pole-rerun record `Overview/Layer1/Layer1_M5_PoleRerun_2026-10-15.md`;
- test C2 at long range, `Overview/Layer1/Layer1_C2LongRange_2026-10-15.md`;
- the Layer 1 close-out `Overview/Layer1/Layer1_CloseOut_2026-10-15.md`;
- the M1–M4 explainers, the 10-01 revision `Overview/Layer1/Layer1_Revision_2026-10-01.md`, and
  `Overview/Layer1/Layer1_Plan.md` §4 (M5), §5 (test F) and §7.

---

## 0. M5 on one page

**The question.** From a given state, can player 1 kill player 2 *without being killed first*,
whatever player 2 does?

**What M5 computes.** One HJI solve, the same size as M3's, of a **reach-avoid value** $V^{RA}_1$.
Where $V^{RA}_1\le0$, player 1 can guarantee winning alone. That set is $W_1$. By symmetry it gives
player 2's set $W_2$, and with M3's single-target values it gives the draw set $D$ and the
contested remainder $C$.

**The headline.**
- **$W_1$ reproduces D&S's corrected winning zones**, including all 17 tagged Table 2 points.
- **The guarantee holds in both directions.** From inside $W_1$ player 1 always wins alone (check
  11). From the states just outside it, player 2 can always stop him (check 13).
- **The contested set** is 1.06 % of live states, and it resolves to a draw.

**Scorecard.** 9 of 14 checks pass on the original run, and 10 of 14 on the pole rerun, which is of
record.

| # | stage | the question | pass if | original run | pole rerun (of record) |
|---|---|---|---|---|---|
| 1 | smoke | does $\ell_2$, built on its own, equal $\ell_1$ with the angles swapped? | difference $\le10^{-6}\,\delta$ | **PASS** | **PASS** |
| 1b | smoke | does the library's update match Fisac's algorithm? | no sign difference beyond 2 cells | **PASS** | **PASS** |
| 2 | smoke | with both controls frozen, does the grid match the exact answer? | no sign difference beyond 2 cells | **PASS** | **PASS** |
| 3 | smoke | from grid wins, does the grid's law win (player 2 flying straight)? | 500 of 500 | **FAIL** 498 / 500 | **PASS** 500 / 500 |
| 4 | fields | is $V^{RA}_1$ mirror-symmetric? | residual $<0.01\,\delta$ | **PASS** | **FAIL** on the fine grid, $0.042\,\delta$; harmless (§9) |
| 5 | fields | is winning alone never easier than single-target winning? | within $0.01\,\delta$ | **FAIL**, by small margins | **FAIL**, the same |
| 6 | fields | are $W_1$, $W_2$ and $D$ disjoint? | 0 shared nodes | **FAIL**: ties on the mutual-kill surfaces | **FAIL** on the fine grid only, the same ties |
| 7 | fields | has the horizon converged? | last step moves $<0.5\,\%$ | **PASS** | **PASS** |
| 8 | fields | does $\partial W_1$ hold still under refinement? | $\le0.5$ cell, no far flips | **FAIL**: 6 far flips at $R=0.554$ | **PASS**: 0 far flips |
| 9 | fields | does $W_1$ have D&S's three pieces? | 3 components, no $R$ mask | **PASS** | **PASS** |
| 10 | fields | do D&S's Table 2 points lie on $\partial W_1$? | $\le2$ and $\le1$ misses | **PASS**, 0 and 0 | **PASS**, 0 and 0 |
| 11 | sims | from inside $W_1$, does player 1 always win alone? | 0 failures | **PASS**, 0 of 11,895 | **PASS**, 0 of 11,885 |
| 12 | sims | would check 11 catch a bad player-1 law? | $\ge20$ starts caught | **FAIL**: the "bad" law isn't bad here | **FAIL**, the same |
| 13 | sims | just outside $W_1$, can player 2 always stop him? | 0 wins, $\ge20$ informative | **PASS**, 0 of 10,000 | **PASS**, 0 of 10,000 |

**The failures, by cause** (five on the original run, four on the rerun).

| cause | checks | status |
|---|---|---|
| the inner face at $R=0.2$ | 3, 8 | both fixed by the pole condition; they pass in the rerun |
| numerical margins smaller than a cell | 5, 6 | permanent; no effect on the partition |
| an asymmetry on the tail-chase line, fine pole grid only | 4 (rerun) | far from every zero set, and $W_1$ is exactly symmetric; cause not established |
| the check's premise was wrong | 12 | check 13 covers the gap, and test C2 at long range tests the heuristic where it is wrong |

---

# Part A — Background the checks need

## 1. Why M5 exists

**M1–M4 answered a single-target question.** $V_1$ asks whether player 1 can force the state into
his weapon envelope $T_{1\to2}$, ignoring that player 2 shoots back. M3 solved it, and M4 showed it
agrees with Layer 0.

**The real game has two weapons and stops at the first kill.** Player 1's best way into
$T_{1\to2}$ may fly straight through $T_{2\to1}$. The single-target value can't see that.

**The old plan compared arrival times, and the 10-01 review showed why that fails.**
- $t_1^*$ is player 1's guaranteed time against a player 2 who only avoids, and $t_2^*$ is the
  reverse.
- Those come from two different games, so comparing them says nothing about which kill comes first
  when both players act at once.
- M3's "win-alone" set, $\{V_1\le0\}\setminus\{V_2\le0\}$, had the same flaw.

**M5 computes the right object directly.** The reach-avoid value says: reach $T_{1\to2}$ while
avoiding $T_{2\to1}$ on the way, against every player-2 behavior. It is the rigorous form of D&S's
Appendix B correction $T'_1=T_1\setminus\bar T_2$, so D&S's corrected zones become its acceptance
test, test F (checks 9–11).

---

## 2. The reach-avoid value

$$V^{RA}_1(x,\tau)=\min_{\sigma_1}\max_{\sigma_2}\ \min_{t\in[0,\tau]}\ \max\Big\{\ell_1\big(x(t)\big),\ \max_{s\in[0,t]}\big[-\ell_2\big(x(s)\big)\big]\Big\}$$

**Read it from the inside out.**
- **The max over $s$** is a running record of "have I been inside $T_{2\to1}$ yet?" Since $-\ell_2$
  is positive only inside player 2's envelope, the record turns positive for good the moment
  player 1 has been shot at.
- **The max with $\ell_1$** asks two things at time $t$: am I in my envelope, *and* have I stayed
  clear of his until now? It is $\le0$ only if both hold.
- **The min over $t$** says reaching that at any one instant is enough, because the game stops at
  the first kill.
- **The min–max** is player 1 doing his best against player 2 doing his worst.

**So $V^{RA}_1(x)\le0$ is a guarantee.** Player 1 can reach $T_{1\to2}$ without first entering
$T_{2\to1}$, whatever player 2 does. This is Fisac et al.'s form (arXiv:1410.6445, Eq. 4) with
payoff $l=\ell_1$ and "discriminator" $g=-\ell_2$.

---

## 3. How the solver computes it

**M3's update, plus one operation.** M3 stepped
$V\leftarrow V+\Delta\tau\,\min(0,\hat H)$, where $\hat H$ is the Lax–Friedrichs numerical
Hamiltonian. M5 adds the *obstacle*:

$$V\leftarrow\max\big(V+\Delta\tau\,\min(0,\hat H),\ -\ell_2\big),\qquad V(x,0)=\max(\ell_1,-\ell_2).$$

**What the obstacle does.** Inside $T_{2\to1}$ it pins $V$ at a positive number. Player 1 can
never be credited with a win from inside player 2's envelope. The dynamics, Hamiltonian, grid and
$\ell$ are all M3's, unchanged.

**One step differs from Fisac's own algorithm.**
- **Fisac's Algorithm 1** takes three steps per time step: a Hamiltonian step, a min with
  $\ell_1$, and a max with $-\ell_2$.
- **The library** takes the min with the *previous* $V$ instead of with $\ell_1$.
- **They agree.** $V$ can only fall as the horizon grows, and the previous $V$ already has the min
  with $\ell_1$ folded in. One line of lattice algebra makes it exact (criteria §2):

$$\max\{g,\min\{\max\{g,a\},W\}\}=\max\{g,\min\{a,W\}\}=\max\{g,\min\{l,W\}\}.$$

- **Check 1b** tests this numerically.

**No information-pattern caveat.** The controls separate in $H$, so $\min\max=\max\min$. It
doesn't matter who "moves first".

---

## 4. The partition: who can guarantee what

**The game isn't zero-sum.** Both players rank a draw above a mutual kill. So M5 uses
**guarantees**, which hold whatever the opponent prefers.

| set | definition | meaning |
|---|---|---|
| $W_1$ | $V^{RA}_1\le0$ | player 1 can guarantee winning alone |
| $W_2$ | $W_1\circ S$ | player 2 can; $S$ swaps the angles, so this is an axis transpose, not a second solve |
| $D$ | $V_1>0$ and $V_2>0$ | each player can avoid ever being shot, so it's a draw under any play |
| $C$ | everything else in $\Omega$ | no guarantee settles it: **contested** |

**$\Omega$ is the set of live states.** It is $R\ge0.45$ and outside both target sets. States
inside a target are already decided. M3 masked $R<0.45$ because the inner face leaked.

**Why $D$ uses the single-target values.** If player 1 can avoid $T_{2\to1}$ forever and player 2
can avoid $T_{1\to2}$ forever, nobody gets shot, whatever the stopping rule.

---

## 5. Terms the checks use

- **$\delta$, one cell.** The value change across one grid cell (`ell.value_scale`): 0.197 at
  $61\times62^2$, 0.118 at $101\times102^2$, 0.059 at $201\times204^2$. Every tolerance is a
  multiple of it.
- **Sign flip.** A node where two fields disagree on whether $V\le0$.
- **Far flip.** A sign flip more than 2 cells from either zero set (3 coarse cells in check 8).
  Flips right at a boundary are expected from discretization, but far ones mean something is wrong.
- **One cell deep.** Starts are drawn from $V\le-\delta$, not $V\le0$, so a start is never a coin
  toss on the boundary.
- **Grids.** $61\times62^2$ for the smoke tests; $101\times102^2$ (coarse) and $201\times204^2$
  (fine) as in M3 and M4; $51\times51^2$ as a third grid for the thin-or-fat fit.
- **Scored where.** Field checks are scored on both main grids. Simulation checks are scored on the
  fine grid, and the coarse grid is reported.
- **Outcome of a simulated run:**
  - **win alone:** player 1 enters $T_{1\to2}$ first, by more than $10^{-6}$ in time;
  - **player-2 kill:** player 2 is first;
  - **mutual kill:** both within $10^{-6}$ of each other, never counted as a win;
  - **no kill:** nobody by the horizon;
  - **exited:** the run left the domain.

  In checks 3, 11 and 12, anything other than "win alone" is a failure.
- **Pre-registration.** Every bar was fixed in the criteria file before the first reach-avoid
  solve. Check 13 was added later as a dated addendum, written before it ran. Failed checks stay
  failed, with the diagnosis beside them.

---

## 6. How a run is organized

| order | step | script | grid | gives |
|---|---|---|---|---|
| 1 | smoke tests | `smoke_m5.py 4` | $61\times62^2$, $T=4$ | checks 1, 1b, 2, 3 |
| 2 | coarse march to $\tau=10$ | `reach_avoid.py` | coarse | the horizon $T_{RA}$ (§8) |
| 3 | coarse cut at $T_{RA}$, third grid, fine solve | `reach_avoid.py` | coarse, third, fine | the fields |
| 4 | field checks | `test_m5.py` | coarse and fine | checks 4–10 |
| 5 | simulation checks | `test_m5.py` | fine scored, coarse reported | checks 11, 12; C2 |
| 6 | the converse | `converse_m5.py` | fine scored, coarse reported | check 13 |

Check 1 also runs at the start of every solve.

---

# Part B — The checks, in the order they run

## 7. Stage 1: smoke tests ($61\times62^2$, $T=4$)

These test the machinery on a small grid before the expensive solves.

### Check 1 — $\ell_2$ matches $\ell_1$ with the angles swapped

- **Question.** Does player 2's target function, written out on its own, equal $\ell_1\circ S$
  exactly?
- **Why it matters.** The obstacle $-\ell_2$ and the symmetry $W_2=W_1\circ S$ both rely on it.
- **Pass if.** $\max|\ell_2-\ell_1\circ S|\le10^{-6}\,\delta$, on every grid.
- **Result. PASS.** The difference is exactly 0.

### Check 1b — the library's update against Fisac's algorithm

- **Question.** Does `hj_reachability`'s form of the update give the same value as Fisac's
  Algorithm 1 written out literally (§3)?
- **How.** Both forms are solved on the smoke grid, and their signs are compared.
- **Pass if.** No sign flip more than 2 cells from either zero set.
- **Result. PASS.** There are 218 flips, all within 2 cells.
- **What it means.** The algebra in §3 holds numerically, so the library's form is safe to use.

### Check 2 — frozen controls against the exact answer

- **Question.** When there's no game, does the grid get the reach-avoid outcome right?
- **How.**
  - Both turn rates are frozen, at $(0,0)$ and at $(+1,-1)$. Then the state just follows a flow.
  - The exact outcome at every node comes from integrating forward and taking the running min–max
    along the path.
  - Nodes whose paths leave $0.2<R<12$ are excluded: 46,480 and 34,260 of them.
- **Pass if.** No sign flip more than 2 cells from the exact zero set.
- **Result. PASS.** There are 732 and 2078 flips, all within 2 cells.
- **What it means.** The obstacle sits in the right place in the time step. This is where an
  implementation error would most likely show.
- **On the pole grid.** The exact answer is integrated in an inertial frame, so paths can pass
  through $R=0$. Only exits through $R=12$ are excluded. That is the inner-face record's V1, and it
  passed.

### Check 3 — the grid's law wins against a straight-flying player 2

- **Question.** From states the grid calls wins, does flying the grid's own law actually win?
- **How.**
  - The game is solved with $\sigma_2\equiv0$.
  - There are 500 starts with $V\le-\delta$ in $\Omega$ (seed 0).
  - Player 1 flies $-\operatorname{sign}(\partial V/\partial\phi_1)$, read at the remaining horizon.
  - First, the vectorized law is checked against `hji.make_policy`; it agrees on 300 of 300
    states.
- **Pass if.** All 500 win alone.
- **Result. FAIL, 498 / 500.** Both failures start at $R=0.593$, the first row inside the mask,
  nose-on and closing. Both leave through $R=0.2$ before player 1 can shoot.
- **What it means.** The grid was right: these are wins that run through a close pass, and the
  simulator stopped them at the domain's edge. On the pole grid check 3 scores 500 / 500 (§13).

---

## 8. Stage 2: the solve and its horizon

**The horizon is fixed by rule, not assumed.**
- The coarse grid is marched to $\tau=10$, measuring how much of the zero level set moves in each
  0.25 step.
- $T_{RA}$ is the smallest whole $\tau\ge6$ after which every step moves less than 0.5 % of it.
- That gives $T_{RA}=6$: the largest step after 6 moves 0.21 %, and $\{V^{RA}_1\le0\}$ grows only
  from 8.110 % to 8.148 % of the grid between $\tau=6$ and 10.

**Then.**
- The coarse fields at $\tau=6$ are cut from that march.
- The fine grid is solved to $\tau=6$, which took 4.6 h in the container.
- The third grid is solved for both the game and the single-target value.
- $D$ uses M3's $V_1$ at $\tau=6$.

**Size.** $\{V^{RA}_1\le0\}$ is 8.25 % of the fine grid, against 12.08 % for $\{V_1\le0\}$. About a
third of what player 1 could force in the single-target game he can't force once player 2's gun
counts.

---

## 9. Stage 3: field checks (4–10)

These look only at the solved fields. Checks 4–7 run on both grids, check 8 compares them, and
checks 9 and 10 score the fine grid.

### Check 4 — mirror symmetry

- **Question.** Is $V^{RA}_1$ unchanged when the engagement is mirrored, $(\phi_1,\phi_2)\to(-\phi_1,-\phi_2)$?
- **Pass if.** $\max|V^{RA}_1-V^{RA}_1\circ Rf|<0.01\,\delta$.
- **Result. PASS.** The residuals are $6.0\times10^{-8}$ (coarse) and $1.9\times10^{-4}$ (fine),
  against bars of $1.2\times10^{-3}$ and $5.9\times10^{-4}$.
- **On the pole grids: FAIL on the fine grid.**
  - The residual is $2.5\times10^{-3}=0.042\,\delta$.
  - All of it is on the tail-chase line ($\phi_1\approx\pm180°$, $\phi_2\approx0$), mostly at $R\le0.15$,
    far from every zero set.
  - $W_1$ is exactly symmetric, and the single-target $V_1$ shows the same spot.
  - The solve is float64, so this grows from roundoff; why is not established (pole-rerun record
    §4.1).

### Check 5 — winning alone is never easier than single-target winning

- **Question.** Is $V^{RA}_1\ge V_1$ everywhere? It must be in the continuum, since adding the
  avoid constraint can only make winning harder.
- **Pass if.** $V^{RA}_1\ge V_1-0.01\,\delta$ at every masked node, and $W_1\subseteq\{V_1\le0\}$
  node for node.
- **Result. FAIL, by small margins.**
  - The worst violations are $0.26\,\delta$ (coarse) and $0.20\,\delta$ (fine), both inside
    $T_{2\to1}$. Within $\Omega$ they are at most $0.125\,\delta$.
  - 6 and 16 nodes of $W_1$ lie outside $\{V_1\le0\}$, all ties with $|V|<0.015\,\delta$.
  - **On the pole grids,** the margins are about the same ($0.26\,\delta$ coarse, $0.27\,\delta$ fine,
    inside $T_{2\to1}$). The inclusion $W_1\subseteq\{V_1\le0\}$ now holds node for node on both
    grids.
- **What it means.** The scheme, WENO5 with TVD-RK3, isn't strictly monotone, so it can dip a
  fraction of a cell. The $0.01\,\delta$ bar was tighter than the scheme can meet. The partition
  isn't affected.

### Check 6 — the sets don't overlap

- **Question.** Is $W_1$ disjoint from $W_2$ and from $D$? Two players can't both guarantee winning
  alone, and a guaranteed draw can't be a guaranteed win.
- **Pass if.** 0 shared nodes of each kind, in $\Omega$.
- **Result. FAIL.** $W_1\cap W_2$ has 0 nodes (coarse) and 3608 (fine). $W_1\cap D$ has 6 and 16.
- **What it means. The check found real structure, not an error.**
  - Every one of the 3608 lies exactly on $|\phi_1|=|\phi_2|$, with $|\phi_1|>\beta$ and
    $|V^{RA}_1|<0.1\,\delta$.
  - Those are D&S's four mutual-kill surfaces (their Eq. 89), where the two winning zones touch and
    $V^{RA}_1=0$ exactly.
  - The grid's sign on such a surface is noise. It came out positive on the coarse grid and
    negative on the fine.
  - The $W_1\cap D$ nodes are ties of the same kind.
- **On the pole grids.** The coarse grid passes, with 0 and 0. The fine grid has 3542 nodes of
  $W_1\cap W_2$, all on the diagonal, and 0 of $W_1\cap D$.

### Check 7 — the horizon has converged

- **Pass if.** The final 0.25 step moves less than 0.5 % of $\{V^{RA}_1=0\}$.
- **Result. PASS.** It moves 0.167 % (coarse) and 0.297 % (fine).
- **On the pole grids,** it moves 0.034 % and 0.043 %, five to seven times less.

### Check 8 — the boundary holds still under refinement

- **Question.** Does $\partial W_1$ stay put from the coarse grid to the fine one?
- **How.** This is M3's metric.
  - The fine field is compared with the coarse one at the coarse nodes.
  - **Displacement** is the number of sign flips divided by the number of boundary nodes, times 6.
    It is the boundary's average shift in coarse cells.
  - Separately, flips more than 3 coarse cells from the coarse boundary are counted.
- **Pass if.** Displacement $\le0.5$, and 0 far flips.
- **Result. FAIL.**
  - The displacement is 0.393 (the bar is met).
  - But 6 of 1632 flips are far, all at $R=0.554$, the first coarse row inside the mask. There the
    coarse grid says $+0.18$ to $+0.27$ and the fine grid $-0.007$ to $-0.036$.
- **What it means.** The fine grid finds a thin sliver of $W_1$ next to the face that the coarse
  grid doesn't.
  - The coarse pole grid agrees with the old coarse grid there, so the coarse face isn't the cause.
  - On pole grids the rows don't line up, so the fine field is interpolated in $R$. Tested on the
    old grids, that gives the same verdict (inner-face record §8).
- **Settled by the pole rerun: PASS.**
  - The displacement is 0.294 coarse cells, with 0 far flips.
  - At the six states both pole grids give $V^{RA}_1=\ell_1=+0.258$ to $+0.274$.
  - So the old fine grid's sliver came from its own face at $R=0.2$ (pole-rerun record §4.2).

### Check 9 — $W_1$ has D&S's shape

- **Question.** Does $W_1\cap\Omega$ come in D&S's three pieces? Those are one region symmetric
  under mirroring (the min-range region) and a mirror pair (the two off-boresight zones).
- **Pass if.** 3 components of $W_1$ outside the target sets, counted without the $R\ge0.45$ mask
  (which would cut the min-range region in two at $R=0.45$): one mirror-symmetric, two mirrors of
  each other.
- **Result. PASS: 3 components.** One mirror-symmetric min-range region and the two off-boresight
  zones (3757 nodes each).
- **The off-boresight zones sit where D&S drew them:** $R\in[4.74,6.10]$,
  $|\phi_1|\in[46°,74°]$, $|\phi_2|\le41°$.
- **On the pole grids** the count is the same: 3 components (261,406 nodes and 3626 each).

### Check 10 — D&S's Table 2 points lie on $\partial W_1$ (test F)

- **Question.** Do the points D&S publish on their corrected boundary sit on the grid's boundary?
- **How.**
  - Points were tagged from the paper before the solve: every Table 2 point named in D&S's
    corrected-game section or drawn in their Figs. 13–14.
  - Some were dropped by rule:
    - three below the mask;
    - two in a row `table3.py` flags as inconsistent as printed;
    - four on both target boundaries ($\beta,\gamma,\delta,\eta$), where $V^{RA}_1=0$ by
      construction.
  - **12 points off $\partial T_{1\to2}$** are scored two-sided: $|V^{RA}_1|\le\delta$.
  - **5 points on $\partial T_{1\to2}$** are scored one-sided, $V^{RA}_1\ge-\delta$, because
    there the starting value already forces $V^{RA}_1\le0$.
- **Pass if.** At most 2 misses among the 12, and at most 1 among the 5.
- **Result. PASS, 0 and 0.** Every off-target point is within $0.68\,\delta$.
- **What it means. This is the sharpest evidence that M5 solves D&S's corrected game.**
  - Five of the points, $\alpha,\varepsilon,\rho_1,\zeta_1,\tau$, exist only in the corrected
    construction.
  - They sit at $|V^{RA}_1|=0.040,\ 0.022,\ 0.019,\ 0.017,\ 0.010$, with $\delta=0.059$.
  - A solve of the wrong game would have no reason to pass through them.

---

## 10. Stage 4: simulation checks (11–13)

### How the simulations work (read once)

- **Integration.** RK4 with $\Delta t=2\times10^{-3}$, with the controls held fixed within each
  step. All trajectories advance together.
- **Value-based laws** read the snapshot nearest the remaining horizon $T-t$. This is
  `hji.make_policy`'s rule, checked against it before use.
- **Kill instants** are found inside their step by bisection, to about $10^{-11}$, then classified
  by the outcome rule (§5).
- **The five player-2 laws:**

| law | rule | what it represents |
|---|---|---|
| reach-avoid adversary | $+\operatorname{sign}(\partial V^{RA}_1/\partial\phi_2)$ | player 2's best play against the guarantee |
| avoid | $+\operatorname{sign}(\partial V_1/\partial\phi_2)$ | M3's evader: run from player 1's envelope |
| trade | $-\operatorname{sign}(\partial t_2^*/\partial\phi_2)$ | a player 2 who can't escape racing to shoot first |
| heuristic | $-\operatorname{sign}(\phi_2)$ | the old simulator's pursuit law |
| random | $\pm1$, redrawn every 0.25 | a sanity check |

- **The trade law avoids differentiating a staircase.** $t_2^*$ is stored in steps of 0.25, so its
  gradient is mostly zero. But on the level set $t_2^*=c$, $V_2(x,c)=0$, so $\nabla t_2^*$ points
  along $\nabla V_2$ read at $\tau=t_2^*(x)$. The law reads that instead.

### Check 11 — from inside $W_1$, player 1 always wins alone

- **Question.** Does the guarantee hold in simulation, against every kind of player 2?
- **How.**
  - 2000 starts are drawn uniformly from $V^{RA}_1\le-\delta$ in $\Omega$ (seed 0), then topped up
    so every component has at least 200. That makes 2379 on the fine grid.
  - Player 1 flies $-\operatorname{sign}(\partial V^{RA}_1/\partial\phi_1)$.
  - Each start is run against all five player-2 laws.
- **Pass if.** 0 failures.
- **Result. PASS, 0 failures in 11,895 runs** on the fine grid. The coarse grid had 0 in 10,110.
  The pole rerun gives 0 in 11,885 (fine) and 0 in 10,130 (coarse).
- **What it means.** $W_1$ isn't too big.
- **The harness can register a loss.** This was checked separately: against the trader, a coasting
  player 1 wins only 47 of 400 deep starts, and one turning away wins none.

### Check 12 — would check 11 catch a bad player-1 law?

- **Question.** Is check 11 sharp enough to fail a wrong law? Player 1 flies the old heuristic
  $-\operatorname{sign}(\phi_1)$ from the same starts.
- **Pass if.** At least 20 starts are beaten by some player-2 law.
- **Result. FAIL: 0 of 2379** on the fine grid, and 0 of 2022 on the coarse.
- **What it means. The heuristic isn't bad here.**
  - The plan called it known-wrong, but that holds only at long range, beyond $R\approx8$, and
    $W_1$ ends at $R\approx6.1$.
  - In M4 it matched the barrier control 99 % of the time at short range.
  - So check 11 can't tell the reach-avoid law from good pursuit *inside* $W_1$. It shows $W_1$
    isn't too big, not that it isn't too small. Check 13 was added for that.
- **The pole rerun gives the same, 0 of 2377.**
- **The heuristic is now tested where it is wrong:** test C2 at long range
  (`Overview/Layer1/Layer1_C2LongRange_2026-10-15.md`).
  - From $R\ge8$ the heuristic player 1 is killed from 10,350 of 10,658 starts.
  - Layer 1's avoid law is killed in none of 53,290 runs.

### Check 13 — just outside $W_1$, player 2 can always stop him

*Added 2026-10-12 as a pre-registered addendum (criteria §7), written before it ran.*

- **Question.** Where $W_1$ says no, can player 2 really stop player 1 from winning alone,
  whatever player 1 flies? This tests that $W_1$ isn't too small.
- **How.**
  - The starts are the states M3's old "win-alone" set claimed and $W_1$ denies, one cell in from
    each edge: $V_1\le-\delta$, $V_2>0$, $V^{RA}_1\ge+\delta$. The pool has 25,402 nodes on the
    fine grid, and 2000 are drawn.
  - Player 1 flies five laws: reach-avoid, single-target, time-optimal, heuristic and random.
  - Each is run against all five player-2 laws, but only the reach-avoid adversary is scored.
- **Pass if.** 0 wins alone against the adversary. The test also has to be informative: player
  1's single-target law must beat the merely *avoiding* player 2 from at least 20 starts.
- **Result. PASS, 0 wins in 10,000 runs.** It is informative: 335 starts are won against the
  avoider. The coarse grid gave 0 and 279. The pole rerun gives 0 wins, with 346 informative starts
  (fine) and 270 (coarse).
- **What it means.** $W_1$ isn't too small, so checks 11 and 13 together pin its boundary from both
  sides.
  - The starts are winnable, but only if player 2 plays badly.
  - All four deterministic laws turn player 1 hard toward player 2. That is fatal: player 2 kills
    in a median of 0.20 time units.

---

## 11. Report-only results

These are measured, not scored. Their rules were fixed in advance.

### The partition, as a share of $\Omega$

| set | $51\times51^2$ | $101\times102^2$ | $201\times204^2$ |
|---|---|---|---|
| $W_1$ (and $W_2$) | 3.596 % | 3.575 % | 3.636 % |
| $D$ | 91.454 % | 91.658 % | 91.723 % |
| contested $C$ | 1.354 % | 1.194 % | **1.056 %** |

On the pole grids, of record ($51\times52^2$, since the pole needs an even $n_\phi$):

| set | $51\times52^2$ | $101\times102^2$ | $201\times204^2$ |
|---|---|---|---|
| $W_1$ (and $W_2$) | 3.588 % | 3.565 % | 3.564 % |
| $D$ | 91.944 % | 91.714 % | 91.863 % |
| contested $C$ | 1.068 % | 1.157 % | **1.060 %** |

### Old against new

On the fine grid, M3's old "win-alone" set is 3.645 % of $\Omega$ and $W_1$ is 3.636 %. The two are
not the same set:
- 0.518 % is in $W_1$ but not the old set;
- 0.527 % is in the old set but not $W_1$. That is the old set's over-claim, about 14 % of it, and
  all of it lies in $C$.

### Thin or fat: is $C$ a real band or a smeared surface?

- **The rule's verdict: fat.**
  - The contested fraction goes 1.354 % → 1.194 % → 1.056 % across the three grids.
  - The three-grid fit gives convergence order $p=0.22$, below the validity floor of 0.25.
  - So the rule falls back to the two-grid ratio, $0.885\ge0.85$: fat.
- **The cleaner evidence is thickness.** Peeling layers off the player-1 half of $C$ until it
  vanishes takes 7 layers on the coarse grid and 14 on the fine. That is the same physical
  thickness. A smeared surface would stay a fixed number of *cells* thick instead.
- **The pole rerun.** The contested fraction goes 1.068 % → 1.157 % → 1.060 %. That isn't monotone,
  so the fit isn't valid. The fallback ratio is 0.917: fat again. The erosion counts are 7 and 14
  again.

### The contested set is a draw

**Where it is.** $C$ is two mirror volumes at $R\approx3.2$–$5.7$. Player 1 is off his own
boresight ($|\phi_1|\approx46$–$111°$), and player 2 is pointing roughly at him.

**Pressing is fatal (check 13), and retreating is safe.** In a report-only run, player 1 flew the
evader law of the mirror game and was killed in 0 of 10,000 runs.

**So, with player 1 retreating and player 2 playing his reach-avoid law:**
- player 2 can't kill him, since $V_2>0$;
- there is no mutual kill, since that needs player 1 inside $T_{2\to1}$;
- player 1 can't win alone, since $V^{RA}_1>0$.

That is a draw, and neither player gains by switching. It needs only that player 1 prefers a draw
to dying alone. Only a 0.2 % sliver of $C$, where both players can force a kill, stays genuinely
contested.

### C2: both players racing (assumption-dependent)

From 1000 contested starts on the fine grid: player 1 wins alone 480 times, player 2 kills 518
times, and there are 2 mutual kills. $C$ is symmetric under the swap, so a near-even split is
expected. The pole rerun gives 499, 498 and 3.

---

# Part C — Putting it together

## 12. What M5 establishes

**Established.**
- **The guarantee holds in both directions** (checks 11 and 13).
- **D&S's corrected game is reproduced:**
  - all 17 Table 2 points (check 10);
  - the off-boresight zones (check 9);
  - the mutual-kill surfaces as the shared edge of $W_1$ and $W_2$ (check 6).
- **The machinery is right** where exact answers exist (checks 1, 1b and 2).
- **M3's old "win-alone" set over-claimed by about 14 %.** The over-claim is a fat band that
  resolves to a draw.
- **$\partial W_1$ converges under refinement** (check 8, settled on the pole grids).
- **No long-range inversion** (test C2 at long range). Every live state at $R\ge8$ is a guaranteed
  draw, and a player on the avoid law is never killed.

**Not established.**
- **Mirror symmetry at the $0.01\,\delta$ level on the fine pole grid** (check 4). The asymmetry is
  on the tail-chase line, far from every zero set, and its cause is open.
- **That the reach-avoid law beats simple pursuit *inside* $W_1$.** It doesn't; they play alike
  there (check 12).
- **Monotonicity and disjointness at the $0.01\,\delta$ level** (checks 5 and 6).
- **That the contested band survives infinite refinement.** Its thickness holds from coarse to fine,
  but the three-grid fit isn't in its asymptotic range.

---

## 13. The inner-face follow-up and the pole rerun

The full story is in `Overview/Layer1/Layer1_M5_InnerFace_2026-10-13.md` (the follow-up) and
`Overview/Layer1/Layer1_M5_PoleRerun_2026-10-15.md` (the rerun).

**What happened.**
- Checks 3 and 8 both failed right at the inner face.
- Moving the face to $R_{\min}=0.1$ moved the failures inward with it, so they came from real play
  close to $R=0$: a close pass.
- The fix was a **pole condition.** A pass looks exactly like $R$ going through zero with the line
  of sight flipping by $\pi$: $(-R,\phi_1,\phi_2)\equiv(R,\phi_1+\pi,\phi_2+\pi)$.
  - The grid continues through $R=0$, and rows "below zero" hold the flipped values from above.
  - The simulator flips a trajectory the same way when it crosses zero.
- Four tests were written before they ran, and all four passed.

**What it changes, check by check.**

| check | effect of the pole condition |
|---|---|
| 2 | the exact answer is integrated in an inertial frame, so paths pass through $R=0$; it passed (V1) |
| 3 | fixed: 500 / 500. All 12 failures seen so far win, by passes as close as $R=0.001$ |
| 8 | open after the follow-up; **settled by the rerun**: 0 far flips, displacement 0.294 |
| 11, 13 | pass on the coarse pole grid: 0 of 10,130 and 0 of 10,000 |
| the rest | the field moves only within 2 cells of the boundary; the partition shares move by at most 0.06 points |

**The rerun (of record).** `run_m5_pole.py` rescored every check on pole grids, against the same
criteria. It ran on Ethan's machine on 2026-10-13/14, taking 23.1 h.
- **10 of 14 pass,** against 9 of 14 originally. Checks 3 and 8 now pass; check 4 now fails on the
  fine grid.
- **The partition barely moves.** On the fine grid $W_1$ is 3.564 % of $\Omega$ and $C$ is 1.060 %.
- **Late-horizon motion drops five to seven times.**
- **The pole fields are M5's fields of record,** and Layer 2's input (close-out §3).

---

## 14. How to read a run

**The pole rerun.** Run `python run_m5_pole.py` from `layer1/M5/`.
- Each step logs to `m5_out/pole_run/NN_<step>.log`.
- `--list` shows which steps are done, and starting it again resumes.
- The scored results are in the last two logs, `final_tests` and `final_check13`.
- The 2026-10-13/14 run's outputs were moved afterward to `m5_out/m5_out_V1_pole/`. The original
  run's outputs are in `m5_out/m5_out_V0/`.

**Start at the last line of the `test_m5` log.** It lists every failed check by name.
- **Original run:** checks 5 and 6 on both grids, plus 8, 9 and 12.
- **Pole rerun:** check 5 on both grids, plus 4, 6, 9 and 12 on the fine grid.

| where | look at | M5 run ($R_{\min}=0.2$) | pole rerun |
|---|---|---|---|
| coarse march log, last lines | `horizon rule: T_RA = ...` | 6.0 | 6.0 |
| `test_m5`, fine block | $W_1$ / $D$ / $C$ over $\Omega$ | 3.64 % / 91.72 % / 1.06 % | 3.56 % / 91.86 % / 1.06 % |
| `test_m5`, check 6 fine | $W_1\cap W_2$ count | 3608, all on the diagonal | 3542, all on the diagonal |
| `test_m5`, check 8 | displacement; far flips | 0.393; 6 | 0.294; 0 |
| `test_m5`, check 10 | off- and on-target misses | 0 / 12 and 0 / 5 | 0 / 12 and 0 / 5 |
| `test_m5`, check 11 | failed runs | 0 of 11,895 | 0 of 11,885 |
| `test_m5`, thin/fat | DECISION line | FAT, by the fallback | FAT, by the fallback |
| `converse_m5`, fine | wins against the adversary; informativeness | 0; 335 | 0; 346 |

**What would be a real problem:**
- any failed run in check 11, or any win in check 13;
- a Table 2 point off-target by more than $\delta$;
- $W_1\cap W_2$ nodes that are *not* on $|\phi_1|=|\phi_2|$;
- the horizon rule failing to settle by $\tau=10$.

**One known artifact on pole runs.** A start drawn on the outer row $R=12$ while the range is
opening leaves the grid on its first step, and scores as "exited". That is the outer face, not the
pole.

---

## 15. Concepts worth having straight

- **A guarantee is not a best response.** $V_1\le0$ says player 1 could force a kill *if the game
  didn't stop*. Only the reach-avoid value says who shoots first.
- **Adding a constraint can only make winning harder.** So $V^{RA}_1\ge V_1$ in the continuum.
  When the grid breaks that by a fraction of a cell, the scheme is at fault, not the answer.
- **On a measure-zero surface the grid's sign is noise.** On the mutual-kill surfaces
  $V^{RA}_1=0$, and which side the nodes land on changes from grid to grid.
- **A test of one side of a boundary needs a partner for the other side.** Check 11 shows $W_1$
  isn't too big, and check 13 that it isn't too small.
- **A negative control has to be wrong where you test it.** The heuristic is wrong at long range,
  but $W_1$ has no long range. Test C2 at long range tests it there.
- **"Contested" is about guarantees, not outcomes.** Contested states can still have a clear
  outcome, and here it's a draw.
- **Pre-register, then report failures as failures.** Diagnosing a failure is fine. Redefining the
  check after seeing it fail is not.

---

## 16. File map

```
layer1/M5/reach_avoid.py      the solve: obstacle, snapshots every 0.25, horizon rule,
                              kinds game | single | frozen_p2, `cut`, `vsnap`
layer1/M5/sim_m5.py           vectorized rollouts, kill location, the tie rule, all control laws
layer1/M5/smoke_m5.py         checks 1, 1b, 2, 3
layer1/M5/test_m5.py          checks 4-12, the partition, thin/fat, C2 in the contested set
layer1/M5/converse_m5.py      check 13
layer1/M5/c2_longrange.py     test C2 at long range
layer1/M5/run_m5_pole.py      the whole sequence on pole grids, unattended
layer1/M5/pole.py             the pole grid and the simulator's flip (inner-face record)
layer1/M5/inertial.py         exact inertial-frame kinematics (inner-face record V1, V2)
layer1/M5/verify_pole.py      the inner-face record's tests V1-V4
layer1/M5/diag/diag_*.py      report-only diagnostics (run from layer1/M5/)
layer1/M5/m5_out/m5_out_V0/       the original run's outputs and logs
layer1/M5/m5_out/m5_out_V1_pole/  the pole rerun's fields, json, snapshots and pole_run/ logs
```

**Cost.** In the 2-core container:
- the smoke tests take about 30 min;
- the coarse march to $\tau=10$, 25 min;
- the fine solve, 4.6 h;
- `test_m5`, about 9 min, and `converse_m5`, about 4 min.

On pole grids each solve costs about 3× (coarse) to 6× (fine) as much. On Ethan's machine each fine
pole solve took 11.0 h, and the whole rerun 23.1 h.
