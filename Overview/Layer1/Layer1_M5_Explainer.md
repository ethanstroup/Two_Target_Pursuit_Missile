# Layer 1 — M5 Explainer

**AE 8900 · reference doc, written 2026-10-12**

**Companion docs:**
- `claude/Layer1_M1_Explainer.md` through `claude/Layer1_M4_Explainer.md`;
- the M5 record `claude/Layer1_M5_2026-10-11.md`;
- the pre-registered criteria `claude/Layer1_M5_Criteria_2026-10-11.md`;
- the 10-01 method revision `claude/Layer1_Revision_2026-10-01.md`;
- `claude/Layer1_Plan.md` §4 (M5), §5 (test F) and §7.

**Code and logs:**
- `Two_Target_Pursuit_Missile/layer1/reach_avoid.py`, `sim_m5.py`, `smoke_m5.py`, `test_m5.py`,
  `converse_m5.py`;
- the `diag_*.py` scripts;
- the logs in `layer1/m5_out/`.

This is a plain-language walkthrough of what M5 does and why each check exists, in the same style
as the M1–M4 explainers. Every number here comes from the logs, which were run with the inner face
at $R_{\min}=0.2$. A rerun at $R_{\min}=0.1$ is in progress (§8).

**Notation.**
- **Watch the clash.** In M5, $V_1$ and $V_2$ are the two *single-target values* (Plan §2.5):
  $V_1$ is player 1 hunting player 2, and $V_2=V_1\circ S$. So gradient components are written as
  partial derivatives here, such as $\partial V^{RA}_1/\partial\phi_1$, not as $V_1$.
- $V^{RA}_1$ is the new reach-avoid value.
- $\tau$ is the time remaining.
- $\delta$ is one grid cell's change in value: 0.118 on $101\times102^2$ and 0.059 on
  $201\times204^2$.

---

## 1. What M5 is, and why it exists

**M1–M4 answered a single-target question.** $V_1$ asks: can player 1 force the state into his
weapon envelope $T_{1\to2}$, ignoring that player 2 shoots back? M3 solved it and M4 showed it
agrees with Layer 0.

**The real game has two weapons and stops at the first kill.** What a pilot cares about is
whether he can kill *without being killed first*. The single-target value cannot say: player 1's
best way into $T_{1\to2}$ may fly straight through $T_{2\to1}$.

**The old plan tried to get there by comparing arrival times, and the 10-01 review showed why
that fails.**
- $t_1^*$ is player 1's guaranteed time against a player 2 who only avoids.
- $t_2^*$ is the reverse.
- Those are two different games, so comparing the times says nothing about which event comes
  first when both players play at once.
- The set M3 called "win-alone", $\{V_1\le0\}\setminus\{V_2\le0\}$, had the same flaw.

**M5 computes the right object directly.** It is one more HJI solve, the same size as M3's, of a
**reach-avoid** value: player 1 must *reach* $T_{1\to2}$ while *avoiding* $T_{2\to1}$ on the way,
against every player-2 behavior. That is the rigorous version of D&S's Appendix B correction
$T'_1=T_1\setminus\bar T_2$, and D&S's corrected zones become its acceptance test (test F).

---

## 2. The reach-avoid value

$$V^{RA}_1(x,\tau)=\min_{\sigma_1}\max_{\sigma_2}\ \min_{t\in[0,\tau]}\ \max\Big\{\ell_1\big(x(t)\big),\ \max_{s\in[0,t]}\big[-\ell_2\big(x(s)\big)\big]\Big\}$$

**Read it from the inside out:**

- **The inner max over $s$** is a running record: "have I been inside $T_{2\to1}$ yet?"
  - $-\ell_2$ is positive only inside player 2's envelope.
  - So the term stays negative while player 1 has never been shot at, and turns positive for good
    the moment he has.
- **The max with $\ell_1$** asks two things at once at time $t$: am I in my own envelope, *and*
  have I stayed clear of his until now? It is $\le0$ only if both hold.
- **The min over $t$** says that achieving this at any one instant is enough, because the game
  stops at the first kill.
- **The min-max** is player 1 doing his best against player 2 doing his worst.

**So $V^{RA}_1(x)\le0$ means a guarantee.** Player 1 can reach $T_{1\to2}$ without first entering
$T_{2\to1}$, whatever player 2 does. That set is $W_1$.

**This is the form in Fisac et al.** (arXiv:1410.6445, Eq. 4), with payoff $l=\ell_1$ and
"discriminator" $g=-\ell_2$. Their formula ignores what happens after the target is reached, which
is exactly the stopped game.

---

## 3. How the solver computes it

**Start from the M3 machinery.** M3's update in time remaining was
$V\leftarrow V+\Delta\tau\,\min(0,\hat H)$, where $\hat H$ is the Lax–Friedrichs numerical
Hamiltonian and the clamp at zero is the "min over time" (M1 explainer §5).

**M5 adds one operation, the obstacle:**

$$V\leftarrow\max\big(V+\Delta\tau\,\min(0,\hat H),\ -\ell_2\big),\qquad V(x,0)=\max(\ell_1,-\ell_2).$$

**What the obstacle does.** The max with $-\ell_2$ pins $V$ at or above a positive number inside
$T_{2\to1}$. Inside player 2's envelope, player 1 can never be credited with a win, however close
he is to his own target. Everything else, from the dynamics and Hamiltonian to the grid and $\ell$,
is M3's unchanged.

**In `hj_reachability` this is one setting:**
- `hamiltonian_postprocessor = backwards_reachable_tube`, which is M3's clamp;
- `value_postprocessor = static_obstacle(-ell_2)`.

**One step differs from Fisac's own algorithm, and it doesn't matter.**
- **Fisac's Algorithm 1** takes three steps: a Hamiltonian step, then $\min$ with $\ell_1$, then
  $\max$ with $-\ell_2$.
- **The library** takes the min with the *previous* $V$ instead of with $\ell_1$.
- **Why these agree.** For a time-invariant problem $V$ can only go down as the horizon grows, and
  the previous $V$ already has the min with $\ell_1$ folded into it. One line of lattice algebra
  makes it exact:

$$\max\{g,\min\{\max\{g,a\},W\}\}=\max\{g,\min\{a,W\}\}=\max\{g,\min\{l,W\}\}.$$

  Here $a=\min\{l,W'\}$, and monotonicity gives $W\le W'$. Criteria §2 has the full version.
- **Checked numerically.** Check 1b runs both versions and finds they differ only next to the zero
  level set.

**Two smaller points.**
- **No information-pattern caveat.** The controls separate in $H$ (the $-|\cdot|+|\cdot|$ terms
  from M1), so $\min\max=\max\min$ and the upper and lower values coincide. It doesn't matter who
  "moves first".
- **Where the obstacle is applied.** The library applies it after each full Runge–Kutta step, not
  at the intermediate stages. Fisac's algorithm does the same, so this matches the reference.

---

## 4. The partition: who can guarantee what

**The game is not zero-sum.** Both players rank a draw above a mutual kill. So "optimal play" is
undefined until a solution concept is chosen, and M5 uses **guarantees**. They hold whatever the
opponent prefers.

| set | definition | meaning |
|---|---|---|
| $W_1$ | $V^{RA}_1\le0$ | player 1 can guarantee winning alone |
| $W_2$ | $W_1\circ S$ | player 2 can, by the index swap (an axis transpose, no second solve) |
| $D$ | $V_1>0$ and $V_2>0$ | each can avoid ever being shot, so the outcome is a draw under any play |
| $C$ | everything else | no guarantee settles it: **contested** |

**Live states.** Everything is measured over $\Omega$: $R\ge0.45$ and outside both target sets. M3
found the inner face leaky, so states below the mask aren't trusted. States inside a target set are
already decided.

**Why $D$ uses the single-target values.** If player 1 can avoid $T_{2\to1}$ forever ($V_2>0$) and
player 2 can avoid $T_{1\to2}$ forever ($V_1>0$), nobody can be shot, whatever the stopping rule.
That is a sufficient condition for a draw.

---

## 5. Pre-registration

**M4's lesson was that criteria chosen with the answer visible are fragile.** So every M5 number
was fixed in the criteria file before the first reach-avoid solve ran:
- the tolerances;
- the horizon rule;
- the Table 2 points to score;
- the simulation protocol;
- the thin-or-fat rule.

**After that, nothing was re-tuned.** Checks that failed are reported as failures, with their
diagnosis beside them. Check 13 was added later, as a dated addendum written before it ran.

**Choosing the Table 2 points.**
- **Candidates.** Every point D&S name in Sec. 5 (the corrected game) or draw in Fig. 13 or 14.
- **Dropped by rule:**
  - points below the mask;
  - the row `table3.py` flags as inconsistent as printed;
  - $\beta,\gamma,\delta,\eta$, which lie on both target boundaries, where $V^{RA}_1=0$ exactly by
    construction.
- **The result.** 12 points off $\partial T_{1\to2}$, scored two-sided, and 5 on it.
- **Why the 5 are scored one-sided.** There the initial value already forces $V^{RA}_1\le0$, so the
  check can only fail from below.
- **The sharpest part.** Five of the twelve, $\alpha,\varepsilon,\rho_1,\zeta_1,\tau$, exist *only*
  in D&S's corrected construction.

---

## 6. Smoke tests, at $61\times62^2$ (checks 1, 1b, 2, 3)

| # | what it tests | result |
|---|---|---|
| 1 | $\ell_2$ written out independently equals $\ell_1\circ S$ | exact, on every grid |
| 1b | the library update against Fisac's algorithm written out literally | 218 sign flips, all within 2 cells: same answer |
| 2 | both controls frozen, at $(0,0)$ and $(+1,-1)$, against exact forward integration from every node | 732 and 2078 flips, all within 2 cells |
| 3 | $\sigma_2\equiv0$, 500 rollouts of player 1's grid law from $V^{RA}_1\le-\delta$ | **498 / 500**: 2 leave through $R=0.2$ |

**Why check 2 is the important one.** With both controls frozen there is no game, only a flow.
The exact reach-avoid outcome can then be computed by integrating forward from every node and
taking the running min-max along each path. If the obstacle were applied in the wrong place, or
the Runge–Kutta stages mishandled it, this is where it would show.

**Check 3's two failures** are the first sign of the inner-face problem (§12).
- Both start at $R=0.593$, the first row inside the mask on this grid.
- Both are inside min range and closing nose-on.
- The grid says player 1 wins ($V^{RA}_1\approx-0.25$, and the $101\times102^2$ grid says the
  same), but the winning maneuver runs below $R=0.2$, where the domain ends.

---

## 7. The solve

**Horizon.** It is fixed by rule, not assumed. The coarse grid was marched to $\tau=10$.
- The rule picks the smallest whole $\tau\ge6$ after which every 0.25-step moves less than 0.5 % of
  the zero level set. That gives $T_{RA}=6$: the largest step after 6 moves 0.21 %.
- $\{V^{RA}_1\le0\}$ grows only from 8.110 % to 8.148 % of the grid between $\tau=6$ and 10.

**Size.**
- $\{V^{RA}_1\le0\}$ is 8.25 % of the fine grid. The single-target $\{V_1\le0\}$ is 12.08 %.
- About a third of what player 1 could force in the single-target game he cannot force once
  player 2's gun counts.
- Part of that is the overlap $T_{1\to2}\cap T_{2\to1}$, which $W_1$ excludes by construction: 2.3 %
  of the masked grid. §11 covers the live states.

**Cost on the 2-core container.** The fine solve took 4.6 h. On Ethan's machine the M3 fine march
took 1.8 h, so expect M5 fine to take about the same there.

---

## 8. Field checks (4–9)

| # | check | result | what's going on |
|---|---|---|---|
| 4 | reflection $V(R,-\phi_1,-\phi_2)=V$ | PASS | exact in the continuum; residual $1.9\times10^{-4}$ on the fine grid |
| 5 | ordering $V^{RA}_1\ge V_1$ | FAIL, small | exact in the continuum, since adding a constraint can only make winning harder; the scheme is not strictly monotone, and dips up to $0.125\,\delta$ in $\Omega$ |
| 6 | $W_1$ disjoint from $W_2$ and from $D$ | FAIL, informative | see below |
| 7 | horizon converged | PASS | final step moves 0.30 % of the surface on the fine grid |
| 8 | grid convergence of $\partial W_1$ | FAIL, local | the boundary moves 0.39 coarse cells (bar 0.5, met), but 6 flips sit far from it, all at $R=0.554$ (§12) |
| 9 | topology: 3 components | FAIL, definitional | see below |

**Check 6 found D&S's mutual-kill surfaces.**
- On the fine grid, 3608 nodes are in both $W_1$ and $W_2$. Every one lies *exactly* on
  $|\phi_1|=|\phi_2|$, with $|\phi_1|>\beta$ and $|V^{RA}_1|<0.1\,\delta$.
- Those are D&S's four mutual-kill surfaces (their Eq. 89), where the two winning zones touch.
- In the continuum $V^{RA}_1=0$ there. On a grid that sign is a coin toss:
  - on the coarse grid it came out positive, so 0 overlap;
  - on the fine grid it came out negative, so 3608 overlap.
- The 16 nodes in $W_1\cap D$ have $|V|<0.015\,\delta$: ties of the same kind.

**Check 9 counted the right shapes in the wrong box.**
- **What was found.** $W_1\cap\Omega$ has 4 components: two mirror halves of the big min-range
  region, and the two off-boresight zones.
- **Why.** Removing $T'_1$ and $R<0.45$ cuts the big region in two.
- **What happens when the cut is undone.** Allow either connection back, and the count is exactly
  D&S's: one region symmetric under reflection, plus a mirror pair.
- **The off-boresight zones sit where D&S drew them:** $R\in[4.74,6.10]$,
  $|\phi_1|\in[46°,74°]$, $|\phi_2|\le41°$.

**Why the failures stay failures.** The criteria were fixed in advance. Re-scoring a check after
seeing why it failed is how fragile criteria creep back in. So the record keeps the FAIL and puts
the diagnosis beside it.

---

## 9. Test F: does $W_1$ match D&S, and does the guarantee hold?

**Check 10, Table 2: PASS, 17 of 17.**
- Every off-target point has $|V^{RA}_1|\le0.68\,\delta$.
- The five corrected-construction points sit at $0.17$–$0.68\,\delta$; $\alpha$ is the farthest.
- A solve that had the wrong game would have no reason to pass through $\alpha$, $\varepsilon$ and
  $\rho_1$. Those are where D&S's *new* barriers meet the old one.

**Check 11, the guarantee: PASS, 0 failures in 11,895 runs.**
- **The test.** From 2379 starts with $V^{RA}_1\le-\delta$, player 1 flies
  $-\operatorname{sign}(\partial V^{RA}_1/\partial\phi_1)$. Each start is run against five player-2
  laws.
- **The result.** Every run ends with player 1 winning alone.

**How the simulator works.** `sim_m5.py` is built for this.
- **Vectorized.** All trajectories advance together in one loop over time: about 12,000 runs in a
  few minutes.
- **Read at the remaining horizon.** Each law reads the snapshot nearest $T-t$, which is M2's rule.
  It is checked against `hji.make_policy` before use and agreed on 300 of 300 states.
- **Kills located exactly.** Each kill instant is found inside its time step by bisection, to about
  $10^{-11}$.
- **Ties never go to a winner.** Kills within $10^{-6}$ of each other count as a **mutual kill**.
  Leaving the domain counts as a failure.

**The five player-2 laws:**

| law | rule | what it represents |
|---|---|---|
| reach-avoid adversary | $+\operatorname{sign}(\partial V^{RA}_1/\partial\phi_2)$ | player 2's best play against the guarantee |
| avoid | $+\operatorname{sign}(\partial V_1/\partial\phi_2)$ | M3's evader: run from player 1's envelope |
| trade | $-\operatorname{sign}(\partial t_2^*/\partial\phi_2)$ | a doomed player 2 racing to shoot (Decision 2) |
| heuristic | $-\operatorname{sign}(\phi_2)$ | the old simulator's pursuit law |
| random | $\pm1$, redrawn every 0.25 | a sanity check |

**How the trade law is computed without differentiating a staircase.** $t_2^*$ is stored in steps
of 0.25, so its gradient is mostly zero with spikes. Instead:
- On the level set where $t_2^*=c$, the value $V_2(x,c)$ is zero. Differentiating gives
  $\nabla V_2+\partial_\tau V_2\,\nabla t_2^*=0$.
- Since $\partial_\tau V_2\le0$, $\nabla t_2^*$ points the same way as $\nabla V_2$ read at
  $\tau=t_2^*(x)$.
- So the law reads $V_2$'s gradient at that horizon. With $V_2=V_1\circ S$, that is $V_1$'s
  gradient at the swapped state.

---

## 10. The negative control, and the converse

**Check 12: FAIL.** It flew the old heuristic $-\operatorname{sign}(\phi_1)$ as player 1, expecting
some player-2 law to beat it from at least 20 starts. None did, on either grid.

**It isn't the harness.**
- With a coasting player 1, against the trader, player 1 wins only 47 of 400 deep starts.
- Turning away wins none.
- So the simulator registers losses.

**The heuristic simply plays well inside $W_1$.**
- **The plan's premise.** It said the heuristic is "known-wrong", but that holds only at long range,
  beyond $R\approx8$. $W_1$ ends at $R\approx6.1$.
- **It fits M4.** At short range the heuristic matched the barrier control 99 % of the time.
- **Deep inside $W_1$, pointing at the opponent never runs player 1 through $T_{2\to1}$ first.**
  The states where avoiding $T_{2\to1}$ matters are the contested set, and check 11 never starts
  there.

**So check 11 shows $W_1$ isn't too big, but not that it isn't too small.** That gap is what check
13 closes.

**Check 13, the converse: PASS.** It was pre-registered as an addendum before it ran.
- **Starts.** The states M3's old set promised player 1 and $W_1$ denies, one cell in from each
  edge: $V_1\le-\delta$, $V_2>0$, $V^{RA}_1\ge+\delta$. That is 2000 of them.
- **Player 1** flies each of five laws: reach-avoid, single-target, time-optimal, heuristic and
  random.
- **Result.** Against the reach-avoid adversary, none win alone in 10,000 runs.
- **It isn't trivially passed.** Against the merely avoiding player 2, player 1 wins from 335 of the
  same starts. They are winnable states, held only by player 2's strategy.
- **Check 11 is this test's control.** The same adversary lost every run from inside $W_1$.

**All four deterministic player-1 laws do the same thing here: turn hard toward player 2.** Kill
times match in 1997–2000 of 2000 runs. That turn is fatal:
- player 2 kills in a median of 0.20 time units;
- with player 1's nose about $76°$ off and player 2 already pointing at him, turning in takes
  player 1 into player 2's envelope before his own shot comes on.

---

## 11. The contested set

**Size:** 1.06 % of live states on the fine grid.
- 49.9 % of it is the player-1 half ($V_1\le0<V_2$).
- 49.9 % is the mirror.
- 0.2 % is states where both can force a kill.

**What the player-1 half is.** It is exactly M3's old "win-alone" set minus $W_1$. All of that
difference lies in $C$. The old set over-claimed by 0.53 % of $\Omega$, about 14 % of itself.

**Where it is.** Two mirror volumes:
- $R\approx3.2$–$5.7$, median 4.45;
- player 1 off his own boresight, $|\phi_1|\approx46$–$111°$;
- player 2 roughly pointing at him.

**Thin or fat? Fat.**
- **The rule's verdict.** Across the three grids the contested fraction goes 1.354 % → 1.194 % →
  1.056 %. The three-grid fit gives a convergence order $p=0.22$, below the pre-registered validity
  floor of 0.25. So the rule fell back to the two-grid ratio, $0.885\ge0.85$: **fat**.
- **The cleaner evidence is thickness.** Peeling layers off the player-1 half until it vanishes
  takes 7 layers on the coarse grid and 14 on the fine. That is the same physical thickness, about
  7 coarse cells. A smeared surface would stay a fixed number of *cells* thick and shrink with the
  cell instead.

**Why it is a draw, and not just "contested".** Check 13 shows pressing the attack is fatal. A
report-only run showed retreating is safe:
- player 1 flies the evader law of the mirror game, $+\operatorname{sign}(\partial V_2/\partial\phi_1)$;
- he is killed in 0 of 10,000 runs, and every run ends with no kill;
- against the adversary and the avoider, every run that leaves the domain does so through $R=12$,
  with the range opening.

Now suppose player 1 retreats and player 2 plays his reach-avoid law. Then:
- player 2 can't kill player 1, because $V_2>0$;
- nobody can force a mutual kill, because that needs player 1 inside $T_{2\to1}$;
- player 1 can't win alone, because $V^{RA}_1>0$.

That's a draw, and neither player gains by switching: player 1 pressing dies, and player 2 has no
way to kill a player 1 who is retreating.

**The only preference the argument needs** is that player 1 prefers a draw to dying alone, which
every ordering the project considers satisfies. D&S also file these states as draws, but they get
there through their "draw beats mutual kill" convention. This reaches the same answer without it.

**What stays genuinely contested** is only the 0.2 % sliver where both can force a kill. That is
D&S's measure-zero mutual-kill set $M$, which the grid also finds essentially empty: 0.002 % of
$\Omega$.

---

## 12. The inner face

**Two checks fail at the same place.**
- Check 3's two rollouts start at $R=0.593$ and exit through $R=0.2$.
- Check 8's six distant flips are all at $R=0.554$: the coarse grid says $+0.18$ to $+0.27$, the
  fine grid $-0.007$ to $-0.036$.

**What's going on.** Near the inner face, the reach-avoid value relies on maneuvers that pass below
$R=0.2$, which the domain doesn't contain. At very short range the line-of-sight rate $L/R$ is
large, so the geometry can swing fast enough to matter. M3 masked $R<0.45$ for a two-cell leak, but
for this value that isn't wide enough.

**What it doesn't touch.**
- All 193 of check 11's fine-grid starts below $R=0.8$ still won.
- The contested set lies at $R>3$.

**The rerun at $R_{\min}=0.1$ tells two causes apart:**
- **A fixed few-cell leak at the face:** the failures disappear from the scored region.
- **Real play close to $R=0$:** they move inward with the face.

It costs about 2× per solve, because the time step is set by $2/R_{\min}+1$, which goes from 11 to
21.

**What happened (2026-10-13).** The full story is in `claude/Layer1_M5_InnerFace_2026-10-13.md`.
- **At $R_{\min}=0.1$ the failures moved inward.** So it is real play close to $R=0$: the winning
  maneuver is a close pass, where the two aircraft fly by each other and player 1 shoots
  afterward.
- **The fix: a pole condition.** Range can't go negative, but a pass looks exactly like $R$
  going through zero with the line of sight flipping by $\pi$:
  $(-R,\phi_1,\phi_2)\equiv(R,\phi_1+\pi,\phi_2+\pi)$. So the grid continues through $R=0$, and
  the rows "below zero" are filled with the flipped values from above. The simulator flips a
  trajectory the same way when it crosses zero.
- **It was checked four ways, against criteria written first.** The tests compared it with exact
  inertial kinematics (no reduced equations at all), with the old fields away from the face, and
  with checks 11 and 13. All four passed.
- **What it showed about check 3.** The old grid's values were right: those states really are
  wins, by a close pass (one goes by at $R=0.001$, about 2 m). The old simulator just stopped every
  run at the face, before the pass. All 12 old failures win now.
- **What it showed about check 8.** The coarse pole grid agrees with the old coarse grid at the
  six flips, not with the fine one. So those flips aren't the coarse face. A fine pole solve would
  settle them, at about 6× the old fine solve's cost.

---

## 13. What M5 does and does not establish

**Established**
- **The guarantee holds in both directions.** From inside $W_1$ player 1 always wins alone (check
  11). From the old set's over-claim, player 2 can always stop him (check 13).
- **D&S's corrected game is reproduced:**
  - all 17 tagged Table 2 points, including the five that exist only in the corrected construction;
  - the off-boresight zones, where D&S put them;
  - the mutual-kill surfaces $|\phi_1|=|\phi_2|>\beta$, as the shared edge of $W_1$ and $W_2$;
  - D&S's open mutual-kill set $M$, essentially empty.
- **M3's old "win-alone" set over-claimed by about 14 %.** The over-claim is a fat band of states
  that resolve to a draw: attack and die, retreat and survive.

**Not established**
- **The guarantee near the inner face,** at $R\approx0.55$–$0.6$, as scored in M5. The 2026-10-13
  follow-up fixes check 3 with the pole condition (§12); check 8's flips remain open.
- **That the reach-avoid law beats simple pursuit *inside* $W_1$.** It doesn't. They play alike
  there.
- **Exact topology and monotonicity at the $0.01\,\delta$ level.** Checks 5, 6 and 9 fail as
  specified, with diagnoses.
- **That the contested band survives infinite refinement.** Its thickness is constant from coarse
  to fine, but the three-grid fit is not in its asymptotic range.

---

## 14. How to read a run

Run from `layer1/` and save each run to a file. The order matters, because later steps read
earlier outputs:

```
python smoke_m5.py 4                     | Tee-Object m5_out/smoke_61x62.log
python reach_avoid.py 101 102 10         | Tee-Object m5_out/solve_101x102_T10.log
python reach_avoid.py cut 101x102_T10 6
python reach_avoid.py 51 51 6
python reach_avoid.py 51 51 6 single
python reach_avoid.py 201 204 6          | Tee-Object m5_out/solve_201x204_T6.log
python test_m5.py 6                      | Tee-Object m5_out/test_m5_T6.log
python converse_m5.py 6                  | Tee-Object m5_out/converse_m5_T6.log
```

**Start at the last line of `test_m5_T6.log`.** It lists every failed check by name. With
$R_{\min}=0.2$ that list is checks 5 and 6 on both grids, plus 8, 9 and 12.

| where | look at | in the $R_{\min}=0.2$ logs |
|---|---|---|
| `solve_101x102_T10.log`, last lines | `horizon rule: T_RA = ...` | 6.0 |
| `test_m5`, fine block | W_1 / D / C over Omega | 3.64 % / 91.72 % / 1.06 % |
| `test_m5`, check 6 fine | W_1 & W_2 count | 3608 (all on the diagonal, see `diag_partition.log`) |
| `test_m5`, check 10 | off- and on-target misses | 0/12 and 0/5 |
| `test_m5`, check 11 | failed runs | 0 of 11,895 |
| `test_m5`, thin/fat | DECISION line | FAT, by the two-grid fallback |
| `converse_m5`, fine | wins against the reach-avoid adversary; informativeness | 0 for all five laws; 335 |

**What would be a real problem in a future run:**
- **any** failed run in check 11 or any win in check 13, away from the inner face;
- a Table 2 point off-target by more than $\delta$;
- $W_1\cap W_2$ nodes that are *not* on $|\phi_1|=|\phi_2|$;
- the horizon rule failing to settle by $\tau=10$.

**For the $R_{\min}=0.1$ rerun,** watch three things:
- whether check 3 passes;
- whether check 8's distant flips vanish;
- whether the contested fraction stays near 1 %. It should, since it lives at $R>3$.

---

## 15. Concepts worth having straight

**A guarantee is a different object from a best response.** $V_1\le0$ says player 1 can force a
kill *if the game didn't stop*. It says nothing about who shoots first. Only the reach-avoid value
answers that.

**Adding a constraint can only make winning harder.** So $V^{RA}_1\ge V_1$ in the continuum. When
the grid breaks that by a fraction of a cell, the cause is a numerical scheme that isn't strictly
monotone, not a different answer.

**On a measure-zero surface the grid's sign is noise.** The mutual-kill surfaces have
$V^{RA}_1=0$ exactly, and whether nodes there land in $W_1$, $W_2$ or neither changes from grid to
grid.

**A test that checks one side of a boundary needs a partner for the other side.** Check 11 shows
$W_1$ isn't too big, and check 13 that it isn't too small. Each is the other's control.

**A negative control has to be wrong where you test it.** The heuristic is wrong at long range,
but $W_1$ has no long range.

**"Contested" is a statement about guarantees, not about outcomes.** Contested states can still
have a clear outcome once you ask what each player can do safely, and here that outcome is a draw.

**Pre-register, then report failures as failures.** Diagnosing a failure is allowed. Redefining
the check after seeing it fail is not.

---

## 16. Quick file map

```
layer1/reach_avoid.py      the solve: obstacle, march with snapshots every 0.25, horizon rule,
                           kinds game | single | frozen_p2, and `cut` for a shorter horizon
layer1/sim_m5.py           vectorized rollouts, kill-event location, the tie rule, all control laws
layer1/smoke_m5.py         checks 1, 1b, 2, 3 at 61x62^2
layer1/test_m5.py          checks 4-12, partition volumes, thin/fat, C2
layer1/converse_m5.py      check 13
layer1/diag_check3.py      the two check-3 exits, at 61 and 101
layer1/diag_m5_fields.py   ordering violations; topology with and without the mask
layer1/diag_m5_partition.py  the W_1 & W_2 overlap, check-8 flips, what the contested set is
layer1/diag_negctl.py      bad player-1 laws, to show the harness registers losses
layer1/diag_retreat.py     player 1 retreating from the contested states
layer1/m5_out/             m5_<grid>_T6_fields.npz, json diagnostics, every log
```

**Cost on 2 cores:**
- smoke tests: about 30 min;
- coarse to $\tau=10$: 25 min;
- fine: 4.6 h (container) or about 2 h (Ethan's machine), doubled at $R_{\min}=0.1$;
- `test_m5`: about 9 min;
- `converse_m5`: about 4 min.
