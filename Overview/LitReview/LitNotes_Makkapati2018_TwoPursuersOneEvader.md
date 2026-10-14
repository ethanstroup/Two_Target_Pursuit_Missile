## Citation

Makkapati, V. R., Sun, W., & Tsiotras, P. (2018). "Pursuit-Evasion Problems Involving Two Pursuers and One Evader." *AIAA SciTech Forum* (2018 AIAA GNC Conference), AIAA 2018-2107. DOI: 10.2514/6.2018-2107.

## Problem Framing

- **Game type.** A one-sided optimal control problem in game's clothing. Only the evader optimizes (max time-to-capture); both pursuers follow fixed, non-optimizing guidance laws — constant bearing (Scenario 1) or pure pursuit (Scenario 2) — not strategies chosen in response to the evader. PMP/costate machinery is applied, but to a single-player problem, not a min-max.
- **Agent structure.** Two identical, speed-superior pursuers ($u>v$, capture guaranteed) vs. one evader. "Cooperation" is structural (both give chase) rather than strategic (neither adapts to the other or to the evader beyond its fixed law).
- **Lethality.** One-sided — the evader carries no weapon; the only terminal event is its own capture.
- **Dynamics.** Simple motion: constant equal speed per player, heading is a direct (unbounded-rate) control, holonomic. No turn-rate limit anywhere.
- **Kill geometry.** Point capture — a disk of radius $\epsilon$ centered on the evader, entered by either pursuer.
- **Dimensionality.** Scenario 1 reduces to 2 states $(r_1,r_2)$ because constant-bearing LOS angles are frozen. Scenario 2 reduces to 3 states $(r_1,r_2,\psi)$ in a frame rotating with, and pegged to, pursuer $P_1$.
- **Method family.** PMP/costate-transversality on the evader's problem; Apollonius-circle geometry for the Scenario 1 closed form; direct collocation (GPOPS-II) where Scenario 2 has no closed form.
- **Synchronization.** *Derived*, not imposed or assumed — the paper's central result.

**Which side of the gap:** one-sided lethality, so squarely on the team-structure side of the review's empty intersection. Does not close it.

**Closest neighbor:** Pachter et al. (2019), "Two-on-One Pursuit" — same setting shape (cooperative 2v1, one-sided, point capture, simple motion, Apollonius geometry) and the same simultaneity conclusion, but Pachter et al. is a genuine two-sided cooperative game (both pursuers jointly optimize; closed-form value function for kind *and* degree), while here the pursuers don't optimize at all. Hayoun & Shima (2017) is the closer analogue specifically on synchronization, and the contrast is sharper: H&S get equal intercept times only as a precondition on initial geometry, while this paper derives them from the evader's optimal play, exactly like Pachter et al.

## Core Contribution

Two propositions (IV.1 for Scenario 1, IV.2 for Scenario 2) proving that whenever the problem is *non-degenerate* — $P_2$'s initial position lies where it can actually affect the outcome — the evader's time-maximizing strategy necessarily produces **simultaneous capture**, $r_1(t_c)=r_2(t_c)=\epsilon$. The proof is by contradiction on the terminal costate structure: assuming only one pursuer's constraint is active at $t_c$ forces pure evasion from that pursuer alone, which is shown to let the *other* pursuer capture strictly earlier. Non-degeneracy is established first, via a geometric partition (Voronoi bisector plus an isochrone curve — circle $\mathcal C_2$ in Scenario 1, ellipse $\mathcal E$ in Scenario 2) of where $P_2$ must start to matter at all. Scenario 1 then reaches a fully closed-form answer: the optimal constant evader heading points at the farther intersection of the Apollonius circles of $(E,P_1)$ and $(E,P_2)$. Scenario 2 has no closed form (Prop. IV.3's $\tan\theta^*$ is implicit and piecewise); it is solved numerically (GPOPS-II) and supplemented by a suboptimal heading — equalize both pursuers' nominal one-on-one capture times, Eq. (71) — matching the optimal capture time to within ~2.5%.

## Method

The paper asks a screening question — does $P_2$ matter at all? — before optimizing anything: the non-degenerate-region construction converts that into a closed-form geometric test (inside/outside an isochrone). Only there is PMP applied, to the evader alone, with both pursuers' fixed laws substituted directly into the dynamics. Constant bearing freezes the LOS angles, which is what buys Scenario 1 its closed form; pure-pursuit headings are state-dependent, which is what pushes Scenario 2 into collocation instead.

## Key Terminology Introduced

- **Degenerate / non-degenerate region** — partition of $P_2$'s initial position by whether it can influence the game at all; degenerate ⇒ pure evasion from $P_1$ is optimal and $P_2$ is a spectator.
- **Isochrone** ($\mathcal C_2$, $\mathcal E$) — locus of $P_2$ initial positions yielding the same capture time as $P_1$ acting alone; bounds the non-degenerate region.
- **Constant bearing / pure pursuit** — the two fixed (non-optimizing) pursuer guidance laws studied in Scenarios 1 and 2.
- **Equal-capture-time suboptimal strategy** — closed-form evader heading equalizing the two pursuers' independent capture times; a cheap near-optimal substitute for the numerical Scenario 2 solution.

## Connections to Prior Literature

**Same object, different name.** The isochrone ellipse $\mathcal E$ (Eq. 11) is the Apollonius/aimpoint machinery seen elsewhere in this review (Weintraub's aimpoint $I$, Pachter et al.'s BSR) — an equal-arrival-time locus from two foci — but here it bounds *relevance* of the second agent rather than locating a capture aim point.

**Agrees with, on synchronization taxonomy:** confirms ProblemStatement §6.1's placement of this paper (with Pachter et al. 2019) as *derived-from-optimal-play*, versus Hayoun & Shima's precondition-on-initial-geometry route or Weintraub §IV's imposed-terminal-constraint route — now verified from primary text rather than secondhand.

**Differs sharply from Pachter et al. (2019)** despite the surface similarity: there the pursuers are the optimizing team and the aim point genuinely depends on both (the redundant-pursuer result); here the pursuers are fixed and only the evader optimizes, so "cooperation" is nominal. Confirms the earlier characterization — "the pursuers do not optimize... a one-sided OCP, not a game."

**Unrelated to the bidirectional-lethality lineage** (D&S, Merz & Hague, Olsder & Breakwell, both Getz & Pachter papers) on every axis: no evader target set, no mutual kill, no turn-rate limits, no WEZ.

## Limitations / Open Questions

No closed-form solution for Scenario 2 — numerical only, with a heuristic fallback. Requires speed superiority ($u>v$) and perfect information for the evader. Simple motion throughout: no turn-rate constraint, no weapon envelope on either side. The least directly transferable paper in the review to Layer 2's turn-limited, boresight-WEZ model — but the isochrone screening idea (test whether the second agent can matter before solving the full game) is a cheap, borrowable pattern.

## Relevance to My Research

Confirms, from primary text, ProblemStatement §6.1's citation of this paper as deriving simultaneity from optimal play under simple motion and point capture — previously asserted, now verified. Firmly on the team-structure/one-sided side of the gap and contributes nothing to Layer 2's bidirectional machinery directly, but the isochrone non-degeneracy test is worth keeping in mind as a cheap screen for when a second attacker's presence is structurally irrelevant.
