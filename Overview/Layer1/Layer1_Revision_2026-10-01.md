# Method revision after outside review (2026-10-01)

**AE 8900 · 2026-10-01 · Ethan Stroup**
Ethan gave a second model seven project records (ProblemStatement, Layer1_Plan, the M1 explainer, the Layer 0 close-out, the M3 record, the D&S notes and the lit index) and asked for its view of the method, not the arithmetic. The review read those files plus the Layer 1 amendment and the 09-29 deck record. It did not reproduce any computation. This file records what it found, what we accepted, and what changed.

**Bottom line.** The computations stand. The step from the solved games to outcome claims did not. The main fix is to compute the two-target partition directly as a **reach-avoid** problem instead of inferring it by comparing arrival times.

## What the review found, and what we did

**1. Comparing arrival times does not decide outcomes. Accepted; this is the main change.**
- $t_1^*$ is player 1's guaranteed arrival time against a player 2 who is only avoiding. $t_2^*$ is player 2's against a player 1 who is only avoiding. These are two different games.
- Under player 1's time-optimal strategy, player 2 is not opposed and may reach $T_{2\to1}$ well before $t_2^*$.
- So Layer1_Plan §2.3's claim that "$t_1^* < t_2^*$ is a sufficient condition for player 1 to win alone" was wrong. Unequal times do not certify the first event, equal times do not show simultaneous events, and the two policies are not shown to form an equilibrium.
- The same flaw applied to M3's $\{V_1 \le 0\}\setminus\{V_2 \le 0\}$, which the record called the "win-alone set". Player 1's reach strategy does not steer around $T_{2\to1}$.
- We wrote the original claim in our own sessions, and none of our checks caught it, because every check tested the numbers and none tested which game each number came from.

*Fix: M5 is redefined as a reach-avoid solve* (Layer1_Plan §4, §7; test F in §5):
- **Value.** Compute $V^{RA}_1$: reach $T_{1\to2}\setminus T_{2\to1}$ without first entering $T_{2\to1}$, against any player-2 behavior. The reference is Fisac et al., arXiv:1410.6445.
- **Partition by guarantees.**
  - $W_1 = \{V^{RA}_1 \le 0\}$, and $W_2 = W_1\circ S$ by transpose.
  - $D = \{V_1 > 0\}\cap\{V_2 > 0\}$: each player can avoid being killed. This is a sufficient condition for a draw.
  - Contested: everything else.
- **Why this route.** This is the rigorous form of D&S's Appendix B correction, since $T_1'$ is the reach target and $T_2$ is the avoid set.
- **Cost.** One solve per grid, the same size as M3's.
- **Acceptance.** D&S's corrected five-subregion zones, plus simulations confirming that every start in $W_1$ ends in a player-1 win alone against several player-2 laws.

**2. The outcome ordering is not zero-sum. Accepted.**
- Both players rank a draw above mutual kill, so "optimal play" needs a solution concept.
- We adopt guarantees ($W_1$, $W_2$, $D$) as the partition. These hold whatever the preferences are.
- Play in the contested region is reported as dependent on the assumption.
- See ProblemStatement §5.4 and §8 item 7.
- Decision 2's soundness paragraph wrongly said $\{V \le 0\}$ is a win "against any behaviour, trading included". It is corrected in Layer1_Plan §1.

**3. Settle the Layer 1 → Layer 2 interface now. Accepted.** ProblemStatement §5.4 now says what Layer 1 must deliver:
- The 1v1 $W_1$, $W_2$, $D$ and contested sets, used as the continuation after a loss.
- The stopping rule: the game changes mode at the first kill, and simultaneous events are classified explicitly.
- Matching preferences across the levels.
- The single-target $V$ and the arrival-time fields are explicitly not the continuation value. §4's two sentences saying otherwise are corrected.

**4. "Every piece of D&S machinery ports unchanged" (§5.2) was too broad. Accepted, and checked.**
- With $H=\sum_i \lambda_i\cdot f_i$ on the six-state system:
  - **Costate equations.** They contain no control, and each pair's equations involve only that pair.
  - **First integral.** Each pair's $I_i=(\lambda_{\phi_i}+\lambda_{\psi_i})^2/R_i^2+\lambda_{R_i}^2$ is conserved whatever the controls do. $\max|\dot I_i| \approx 1.1\times10^{-13}$ over 2000 random states, costates and controls; it also follows by hand. Only one overall scale can be normalized, so the "$=1$" does not carry over.
  - **Bandit control.** $\partial H/\partial\sigma_B=\lambda_{\psi_1}+\lambda_{\psi_2}$, so the bandit's control law and $H^*=0$ are joint across the two pairs.
- **New consequence.** Pair 2's costate equations are linear and homogeneous in pair 2's costates.
  - So a single-target barrier for $T_{A_1\to B}$ is the 1v1 barrier extruded over pair 2's states.
  - All genuinely 2v1 structure therefore lives in combinations of target sets, which is reach-avoid again.
- The check script was a throwaway in the session workspace and was not saved to the repo. It is about 20 lines of sympy if it needs re-running.

**5. The $2\beta$ result was overstated. Accepted.**
- $|\Delta|>2\beta$ rules out threatening both attackers at the same instant. It does not rule out killing them one after the other.
- §5.3 and §8.3 are rescoped. The safety version is now posed as a reach-avoid question: can the unthreatened attacker always reach $T_{A_j\to B}$ before the bandit kills and re-aims?

**6. Synchronization has no observable in the stopped game. Accepted.**
- The game ends at the first kill, so $|t_{f,1}-t_{f,2}|$ is undefined unless it is labeled as a counterfactual.
- ProblemStatement §6.3 lists well-defined candidates, for example whether the other attacker also holds a shot at the kill instant.
- The instantaneous-kill row in §7 is marked as load-bearing.

**7. Scope of Layer 2. Accepted.**
- A dense six-state grid is out: 141 GB per float64 array at $51^6$.
- An exact four-target Appendix B extension is a research question, not a dependency.
- ProblemStatement §5.5 now names credible December targets, including the review's suggested contribution: when separately solved subgames compose under a shared control, and when they do not.

**8. Record-level items. Accepted, except one.**
- **Done:**
  - ProblemStatement §4's status is corrected; it said "not started".
  - Layer 0's status is qualified as single-target machinery.
  - M4's comparison is scoped to barrier segments on the active boundary, with departures listed as candidate junctions rather than failures.
  - The R ≥ 0.45 mask is described as supporting results on the retained domain only.
- **Rejected:** "the M3 scripts are missing". This was our own false flag from the 09-29 and 09-30 records. Ethan confirms that `solve_m3.py`, the other M3 scripts and `m3_out/` are on his computer. Both records are corrected.

**Noted, not changed.** "Terminal miss" is a loose name, because the value is the minimum of $\ell$ over the trajectory. The accurate description is noted in ProblemStatement §4. The name is kept so file and slide references stay valid.

## Files changed

| File | Change |
|---|---|
| `claude/ProblemStatement.md` | v0.5 → v0.6: banner; §3 status; §3.4; §4 status, continuation value, naming, Decision 2 limit; §5.2 what ports; §5.3 2β; §5.4 partition semantics + interface; §5.5 scope; §6.3 new; §7 instantaneous-kill row; §8 items 3, 6, new 7–8; §9 new bullet; §10 Layer 1 row |
| `claude/Layer1_Plan.md` | Revision note; status; §0; Decision 2 soundness; §2.3 race paragraph; §2.5 retitled; M3 marked done; M4 scope; **M5 redefined**; §5 scope note, C2 reframed, test F; §6 new bullet; **§7 rewritten**; §8, §9, §10 updated; §11 note |
| `claude/Layer1_M3_2026-09-18.md` | Revision note; "win-alone set" retitled; 4.53 % no longer called an upper bound |
| `claude/Layer1_SlideDeck_2026-09-29.md` | False missing-files flag resolved; slides 4, 11, 24 and 25 listed as needing updates in the .pptx (not edited) |
| `claude/Layer1_M1_Explorer_2026-09-30.md` | False missing-files flag resolved |

The dated progress records (`Layer1_Progress_2026-09-14.md`, `Layer1_Amendment_2026-09-15.md`) are left as written. They describe the plan as it stood on their dates.

## Not done, and needs Ethan

- **Code.** `layer1/reach_avoid.py` and `test_m5.py` are named in Plan §9 but not written. The repo has not been touched.
- **The deck.** The `Layer1_Update_2026-09-29.pptx` slides listed above.
- **Open decisions.**
  - The §5.4 team objective is still open.
  - §8 item 7 defaults to guarantees only. Confirm or change.
