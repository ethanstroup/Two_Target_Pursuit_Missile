# Layer 1 Plan — 1v1 Game of Degree via HJI Reachability

**AE 8900 · drafted 2026-09-14 · Ethan Stroup**
**Status:** **instructions closed 2026-09-14; revised 2026-10-01** (M5 redefined, see the
revision note below). M1–M3 done. M4 and the redefined M5 are executable as written. M1 and M2 are already done — see
`claude/Layer1_Progress_2026-09-14.md`. Layer 0 closed 2026-09-11
(`claude/Layer0_CloseOut_2026-09-11.md`).
**Schedule slot:** ProblemStatement §10, weeks 3–6.

> **Revision 2026-10-01 — read this before §2.3, §2.5, §4 (M5), §5 (C2, M4 scope) and §7.**
> An outside review of the method found that the plan's route from the solved games to outcome
> claims did not hold. The single-target solve (M1–M3) is unaffected. What changed:
> - **§2.3's "sufficient condition" claim is withdrawn.** $t_1^*$ and $t_2^*$ are guarantees
>   against *different* opponent behaviors (each against a purely avoiding opponent), so
>   comparing them does not certify which event happens first under any common strategy pair.
> - **M5 is redefined** as a two-target **reach-avoid** solve: player 1 reaches
>   $T_{1\to2}\setminus T_{2\to1}$ without first entering $T_{2\to1}$, against any player-2
>   behavior. That is the rigorous form of D&S's Appendix B correction, it runs on the existing
>   grid, and D&S's corrected zones are its acceptance test (new test F).
> - **§7 is rewritten**: the Appendix B correction is replaced by a reach-avoid computation, not
>   by a comparison of arrival times.
> - **Decision 2's soundness argument is corrected**: $\{V\le0\}$ is a guarantee of reaching
>   $T_{1\to2}$ in the single-target game, not of winning in the two-target game.
> - **M4's comparison is scoped** to barrier segments that are actually part of the boundary.
> Record: `claude/Layer1_Revision_2026-10-01.md`.

This document is written to be read cold, by a session with no prior context. Everything
needed to start is here or named here.

---

## 0. The one-paragraph version

Layer 0 produced verified barrier *trajectories* for the 1v1 Davidovitz & Shinar game, but
no way to play from an arbitrary interior state. Layer 1 solves for a value function
$V(R,\phi_1,\phi_2)$ on a grid whose zero level set is the same barrier Layer 0 already
computed independently. That overlap is the point: Layer 0 becomes a hard correctness test on
Layer 1, not merely its predecessor.

The value supplies a feedback law too, but **not one law everywhere** — $\nabla V$ governs play
on the barrier, the arrival-time gradients govern the interior, and neither is defined on the
singular set. §2.3 is the section to read before trusting any extracted control.

**Which outcome each player can guarantee in the two-target game is a separate object** — it
comes from the reach-avoid solve of M5, not from $V$ or from comparing arrival times
(revision 2026-10-01).

---

## 1. Decisions

### Decision 1: the payoff is terminal miss, not signed time

**ProblemStatement §8 item 2 is hereby closed.** §4 listed three candidate payoffs. The
choice is **terminal miss / margin**, implemented as a level-set reachability value.

### Why not signed time-to-kill

It was the standing recommendation, and it does not survive contact with §4's own
acceptance criterion — *"the zero level set of $V$ reproduces the Layer 0 barrier
trajectories."*

On the barrier the state reaches the boundary of the usable part **tangentially and in
finite time** (Layer 0's own retrograde trajectories run to $\tau = 3$ with $R$ still
bounded near 7, so the forward time-to-graze is finite). So approaching the barrier from
inside the winning zone, $t_{\text{kill}}$ tends to a finite *positive* value; just outside,
the payoff is $-t_{\text{death}}$, finite and negative. $V$ therefore **jumps** across the
barrier. The barrier is the discontinuity surface of $V$, and $V = 0$ is the *target set*,
not the barrier. The acceptance test does not typecheck.

Two further defects: $t_{\text{death}}$ is undefined on the entire draw region (an open set,
so not a removable issue), and a function that is $+$finite on one side of a surface and
$-$finite on the other cannot be represented on a grid near precisely the surface Layer 1
exists to validate.

**Correction to ProblemStatement §4.** The sentence *"The barrier from Layer 0 is the zero
level set of the last two options"* is correct for terminal miss and incorrect for signed
time. Recorded as a spec error found by the §9 standard.

### Why terminal miss works

On the barrier the state grazes $\partial T_{1\to2}$ — penetration depth exactly zero. Inside
the winning zone it penetrates (negative). Outside it never arrives (positive). The barrier
*is* the zero level set, by construction, which is what §4 wanted.

**Nothing is lost.** The appeal of signed time was the time structure. In this formulation
the arrival time is recovered as a derived field — the time index at which the value first
crosses zero — so $t_{\text{kill}}(x)$ is available for visualization and for the Layer 2
continuation value, without being the quantity the solver optimizes.

### Decision 2: a doomed player prefers mutual kill

**Adopted 2026-09-14.** This closes the marker that previously stood open in §2.3. Each
player's preference ordering, best to worst:

1. win alone
2. draw
3. mutual kill
4. die alone

The operative clause is **3 ≻ 4**: a player who cannot avoid being killed prefers to take the
opponent with him. The 2 ≻ 3 clause is D&S's own "prefer draw to mutual kill" convention,
retained unchanged. §11 records what would change under the alternative assumption
("survive longest"), including why it was not chosen.

**The most important consequence: this does not move the barrier.** The barrier separates
states where player 2 *can* avoid $T_{1\to2}$ from states where he cannot. Outcomes 1 and 2
are available on and outside it, so a rational player 2 there plays pure avoidance — which is
exactly the behaviour the reach value of §2.2 already assumes. Outcome 3 becomes relevant only
*strictly inside* player 1's winning zone, where avoidance is impossible by construction. The
two regions are disjoint. Therefore:

- the reach formulation of §2.2 is **unchanged**;
- acceptance tests A, B, D and E are **unchanged**;
- **M1, M2 and M3 are unaffected**, including the work already completed;
- only the **interior feedback law** (§2.3) and **test C2** (§5) change;
- **M5 is promoted** from a bonus result to this layer's central one.

There is also a soundness reason the barrier cannot move: $\{V \le 0\}$ is defined by a
*maximum over all* player-2 strategies, so it is a guarantee, not a best-response calculation,
and guarantees are preference-independent.

*(Corrected 2026-10-01.)* What $\{V \le 0\}$ guarantees is that player 1 can force entry into
$T_{1\to2}$ **in the single-target game**, which ignores that play would stop if $T_{2\to1}$ were
entered first. An earlier version said it is the set where player 1 "wins against any player-2
behaviour, trading included." That is false: player 1's reach strategy does not steer around
$T_{2\to1}$, so a trading player 2 may get his kill in first or simultaneously. The set where
player 1 wins *alone* against any behavior is the reach-avoid set of M5. That set is also a
guarantee, so it is also preference-independent; Decision 2 still governs only what happens
outside the guaranteed sets.

**What it newly requires.** Mutual kill is defined by $T_{2\to1}$, so the second target set
enters Layer 1 rather than waiting for Layer 2. The index-swap mirror — verified at machine
precision in `layer0/test_mirror.py` — is therefore **required**, not optional. §2.5 shows it
costs no second solve.

---

## 2. Formulation

### 2.1 Implicit surface function

$T_{1\to2}$ is the intersection of three constraints (ProblemStatement §3.2), so

$$\ell(x) \;=\; \max\Big(\, |\phi_1| - \beta, \;\; \underline R(\phi_2) - R, \;\; R - \bar R(\phi_2) \,\Big)$$

with $\ell < 0$ strictly inside $T_{1\to2}$, $\ell = 0$ on its boundary, $\ell > 0$ outside.
This is exactly the three predicates in `barrier.in_target`, written as a single scalar.

**On units, and why the name "miss" is borrowed.** This $\ell$ takes a max over a *radian*
and two *normalized lengths*. It is not a distance, and calling the resulting value a
"terminal miss" imports a name from the linear missile-guidance literature, where miss really
is metres of lateral separation. Prefer **weapon-envelope margin**; the payoff family is the
same, the physical interpretation is not.

**What the units mismatch does and does not break.** The winning zone is
$\{x : \text{player 1 can force the trajectory to touch } \{\ell \le 0\}\}$, and "touch
$\{\ell\le0\}$" depends only on **the set**, not on the function representing it. Any $\ell$
with the same zero level set and sign convention yields the same reachable set and therefore
the same barrier. **The acceptance tests of §5 are invariant to the scaling.** What the
mismatch does affect:

- *Interpretation.* A nonzero $V$ is a margin in mixed units, not a physical miss. Do not
  quote it as a distance in the report.
- *Conditioning.* Level-set schemes want $|\nabla\ell| \approx 1$. A max of badly-scaled terms
  gives a value function steep in one direction and flat in another, which resolves the zero
  level set poorly — precisely the surface being validated.

**So nondimensionalize before solving:** divide the boresight term by $\beta$ and the range
terms by a characteristic range (e.g. $\bar R_0$), so the three terms are comparable
dimensionless margins. If convergence is still poor, reinitialize by solving the eikonal
equation $|\nabla\ell| = 1$ to recover a true signed distance with the *same* zero level set.

### 2.2 Value function

$$V(x,T) \;=\; \min_{\sigma_1(\cdot)} \; \max_{\sigma_2(\cdot)} \; \min_{t \in [0,T]} \; \ell\big(x(t)\big)$$

read as: the deepest penetration of player 1's weapon envelope that player 1 can guarantee
within horizon $T$, against player 2's best evasion.

- Player 1's winning zone within time $T$: $\;\{x : V(x,T) \le 0\}$
- **The barrier:** $\;\{x : V(x,T) = 0\}$ — the direct Layer 0 acceptance test
- Arrival time: $\;t^*(x) = \min\{T : V(x,T) \le 0\}$ — the min-max time-to-capture, and
  **the source of the interior feedback law** (§2.3). Not a by-product; read §2.3 before
  treating it as one.

Solve backward from $V(x,0) = \ell(x)$ to a horizon large enough that the zero level set
stops moving (convergence to the infinite-horizon barrier — check this, do not assume it).

### 2.3 The Hamiltonian is already written and already tested

$$\nabla V \cdot f \;=\; V_R\big[-(\cos\phi_1+\cos\phi_2)\big] \;+\; V_1\Big[\tfrac{L}{R}+\sigma_1\Big] \;+\; V_2\Big[\tfrac{L}{R}+\sigma_2\Big], \qquad L = \sin\phi_1+\sin\phi_2$$

Player 1 minimizes, player 2 maximizes, and the controls separate:

$$H(x,\nabla V) \;=\; -V_R(\cos\phi_1+\cos\phi_2) \;+\; (V_1+V_2)\tfrac{L}{R} \;-\; |V_1| \;+\; |V_2|$$

**This is `barrier.hamiltonian_star` with $\lambda := \nabla V$, character for character.**
The function that served as Layer 0's semipermeability invariant is Layer 1's Hamiltonian.
Two consequences worth having in hand before any code is written:

1. **The optimal feedback law is immediate — on the set where $V$ is differentiable:**
   $\sigma_1^* = -\operatorname{sign}(\partial V/\partial\phi_1)$,
   $\sigma_2^* = +\operatorname{sign}(\partial V/\partial\phi_2)$, extending D&S Eqs.
   (21)–(22) off the barrier trajectories they were derived on.

   **This is NOT a globally valid law, and the first draft of this plan wrongly said it was.**
   The value function of a differential game is generically only Lipschitz, and the bang-bang
   law fails exactly where the interesting structure lives:
   - **Dispersal surfaces** — $\nabla V$ is two-valued and the optimal control is genuinely
     non-unique. That is the definition of a dispersal surface, not a numerical artifact.
   - **Universal surfaces / singular arcs** — a gradient component holds at zero over an
     interval and the optimal control is *intermediate*, not bang-bang. D&S Table 3 lists
     strategies such as $(-1,0)$ and $(0,+1)$; `barrier.integrate_retrograde` already detects
     and flags these rather than chattering through them.
   - **$\nabla V = 0$** — inside the target set (the game is over) and on any plateau in the
     draw region, $\operatorname{sign}$ is undefined.

   Practically: use the viscosity-consistent (upwind) gradient the solver already computes,
   and expect to need an explicit tie-break or regularization near kinks. Do not smooth $V$ to
   make the kinks go away — they are the answer, see test E in §5.

   **The deeper problem, and the one that actually governs interior play.** The above is about
   where $\nabla V$ fails to *exist*. There is a separate and more important issue about what
   $\nabla V$ *means* once it does exist, strictly inside the winning zone.

   D&S's $\sigma_2^* = +\operatorname{sign}(\lambda_2)$ is derived **on the barrier**, where
   play is balanced and both players are genuinely extremizing. Inside player 1's winning zone
   player 2 has already lost, a game of kind assigns no preference to anything player 2 does,
   and that derivation has no force. ProblemStatement §6.2 states this; it is why the existing
   sim substitutes a heuristic.

   **A margin payoff does not repair this, it disguises it.** $V$ does discriminate in the
   interior — it measures how deep into the WEZ player 1 can force the state — so formally the
   indifference is gone. But under the §7 assumption of *instantaneous kill on target-set
   entry*, depth of penetration is physically meaningless: 0.4 deep and 0.05 deep are the same
   outcome. A feedback law read off $\nabla V$ inside the winning zone therefore optimizes a
   quantity nobody cares about.

   **So take the interior law from the arrival time, not from $V$.** Inside the winning zone
   the meaningful question is *how long can player 2 survive*, which is well posed exactly
   where capture is guaranteed. That is the classical Isaacs structure — game of kind first for
   the barrier, then a time-optimal game of degree in the interior — and the level-set solve
   supplies both objects at once:

   | object | from | valid where |
   |---|---|---|
   | the barrier | $\{V = 0\}$ | everywhere; this is the Layer 0 acceptance test |
   | interior feedback law | $\nabla t^*(x)$ | strictly inside the winning zone |
   | barrier feedback law | $\nabla V$ | on $\{V=0\}$, where it must match the Layer 0 costate |

   Verify the arrival-time extraction and its gradient against the chosen toolbox's own
   documentation — several expose a "time to reach" field directly, and the conventions differ.

   **[CLOSED 2026-09-14] — a doomed player 2 goes for the mutual kill.** §1, Decision 2. The
   interior laws follow directly, and they are *simpler* than the alternative, not harder:

   | region | player 1 plays | player 2 plays |
   |---|---|---|
   | on the barrier $\{V=0\}$ | $-\operatorname{sign}(\partial V/\partial\phi_1)$ | $+\operatorname{sign}(\partial V/\partial\phi_2)$ |
   | strictly inside the winning zone | race, from $\nabla t_1^*$ | race, from $\nabla t_2^* = \nabla(t_1^* \circ S)$ |
   | outside the winning zone | not this layer's object | avoid, from $\nabla V$ |

   Inside the winning zone **both players are time-optimal toward their own target set**, for
   different reasons: player 2 because reaching $T_{2\to1}$ before dying is his only remaining
   improvement, player 1 because killing faster is exactly how that trade is denied. The
   interior becomes a race between two arrival-time fields.

   **The race does not decide the outcome (revised 2026-10-01).** $t_1^*$ is computed against a
   player 2 who is *avoiding*, and $t_2^*$ against a player 1 who is avoiding. Neither is the
   actual play. An earlier version of this paragraph said $t_1^* < t_2^*$ is a *sufficient*
   condition for player 1 to win alone. **It is not.** Once player 1 commits to his time-optimal
   strategy he is no longer trying to stop player 2, and against that particular strategy player 2
   may reach $T_{2\to1}$ well before $t_2^*$. Two worst-case deadlines from two different games
   say nothing about event order under a common strategy pair. So:
   - unequal arrival times do not certify the first event;
   - equal arrival times do not establish simultaneous events in actual play;
   - the two separately time-optimal laws are not shown to form an equilibrium.

   The table's "race" rows are therefore a **behavioral model** of interior play under Decision 2,
   useful for simulation and for test C2, not a solution of the two-target game. Which outcome
   each side can guarantee is M5's reach-avoid solve. Inside player 1's reach-avoid set, his law
   comes from that value (and its arrival time), not from $\nabla t_1^*$.
2. **The acceptance test gets much sharper** (§5): on the barrier, $\nabla V$ from the grid
   should reproduce the Layer 0 costate $\lambda$ up to positive scaling.

### 2.4 The PDE

Two equivalent devices exist for keeping the value from "growing back" once a trajectory has
reached the target, and **they are not the same equation** — check which one your chosen
toolbox implements before comparing results:

1. **Freezing input** (Mitchell, Bayen & Tomlin 2005, the original). The target-reaching
   player gets an augmented control that can halt the dynamics once inside the target, so
   the plain HJI PDE $\partial V/\partial\tau + H(x,\nabla V) = 0$, $V(x,0)=\ell(x)$, suffices.
2. **Variational inequality** (the later and now more common form, and what most toolboxes
   expose):
   $$\frac{\partial V}{\partial \tau} \;+\; \min\Big[\,0,\; H(x,\nabla V)\,\Big] \;=\; 0, \qquad V(x,0) = \ell(x).$$

**Verify whichever form you use against its own primary source before relying on it — do not
transcribe either from this document.** (The attribution of form 2 to Mitchell et al. 2005 was
an error in this plan's first draft, caught 2026-09-14; their paper uses form 1.) ProblemStatement §9's re-derive-don't-transcribe standard applies to this
plan exactly as it applies to a published paper, and the sign convention on $H$ interacts
with the $\dot\phi = \text{LOS rate} + \sigma$ convention noted in §6 below.

**Player-ordering trap.** Mitchell et al. write $H = \max_a \min_b \nabla V \cdot f$ with
$a$ the *evader* and $b$ the *target-reaching* player. This project writes
$\min_{\sigma_1}\max_{\sigma_2}$ with $\sigma_1$ the attacker. Same object, opposite
labelling; getting it backwards produces a plausible-looking barrier for the wrong player.
M1's Hamiltonian check against `barrier.hamiltonian_star` catches this.

### 2.5 The second value function costs nothing

Let $S$ be the index swap $(R,\phi_1,\phi_2) \mapsto (R,\phi_2,\phi_1)$ with the two controls
exchanged, and $Rf$ the reflection $(R,\phi_1,\phi_2) \mapsto (R,-\phi_1,-\phi_2)$ with the
controls negated. All four of the following are **exact identities** — verified at *zero*
residual, not merely small, over $2\times10^5$ random states, alongside
`layer0/test_mirror.py`'s machine-precision check of the same structure at the Hamiltonian
level:

$$\ell_2(x) = \ell_1(Sx), \qquad \ell_1(Rf\,x) = \ell_1(x)$$
$$f(Sx;\sigma_2,\sigma_1) = S\,f(x;\sigma_1,\sigma_2), \qquad f(Rf\,x;-\sigma) = Rf\,f(x;\sigma)$$

Two consequences, both load-bearing:

**1. $V_2 = V_1 \circ S$ and $t_2^* = t_1^* \circ S$ — no second PDE solve.** The second game is
the first one relabelled. On a grid whose $\phi_1$ and $\phi_2$ discretizations are identical
this is an axis transpose, not a computation. Given the ~2 h cost at $201^3$ recorded in the
progress note, that is the difference between one overnight job and two. **Assert the identity
on the computed arrays rather than assuming the grid is symmetric** — an unequal or offset
angular discretization silently breaks it.

**2. A symmetry identity for the arrival-time fields.** *(Retitled 2026-10-01: this was
"the mutual-kill surface is predicted by symmetry alone." The identity below is correct; reading
$\{t_1^* = t_2^*\}$ as the mutual-kill set is not, for the reason in §2.3.)*
$\{t_1^* = t_2^*\} = \{x : t_1^*(x) = t_1^*(Sx)\}$. That holds wherever $Sx = x$, i.e.
$\phi_1 = \phi_2$; and wherever $Sx = Rf\,x$, i.e. $\phi_1 = -\phi_2$, because $t_1^*$ is
$Rf$-invariant. Hence

$$\{t_1^* = t_2^*\} \;\supseteq\; \{|\phi_1| = |\phi_2|\},$$

the same surfaces as D&S's Eq. (87). That is a useful smoke test on the grid (if it fails, the
angular discretization is asymmetric). It is a statement about where two worst-case times tie,
not about where mutual kill happens. The same two symmetries do carry over to M5:
$V^{RA}_2 = V^{RA}_1 \circ S$, so the second reach-avoid set is also a transpose, and both
reach-avoid sets are $Rf$-invariant. See §4 (M5) and §7.

---

## 3. Grid and numerics

**Domain.** $R \in [R_{\min}, R_{\max}]$, $\phi_1,\phi_2 \in S^1$.

| item | value | why |
|---|---|---|
| $R_{\max}$ | 10–12 | target set tops out at $\bar R(0) = 6.1416$; Layer 0 trajectories reach $R \approx 7$ |
| $R_{\min}$ | $\approx 0.2$ | below $\min \underline R = 0.25$, so below the target set entirely |
| initial grid | $101^3$ | 3D is cheap; refine to $201^3$ for the convergence study |

**Four traps, in rough order of how much time they will cost if missed.**

1. **$\phi_1$ and $\phi_2$ are periodic.** Both angle dimensions need periodic boundary
   conditions. This is the single most common source of silent wrongness in this kind of
   solve, and it will look like a plausible-but-wrong barrier rather than an obvious
   failure. Any toolbox chosen must support periodic dimensions natively.
2. **$R \to 0$ is singular.** The $L/R$ terms blow up. $R_{\min} = 0.2$ keeps the domain off
   it; use an extrapolation (outflow) condition at the inner face, not periodic and not
   Dirichlet.
3. **$\ell$ is only Lipschitz.** $\bar R(\phi) = \bar R_0 - |\phi + \sin\phi|$ has a kink at
   $\phi = 0$, and the `max` of three constraints has corners along every edge of the target
   set. Viscosity solutions handle this correctly, but do not expect clean high-order
   convergence, and do not "fix" the kink — it is the geometry, and it is where D&S's own
   corner equations (Eqs. 38–42) live.
4. **$H$ is non-differentiable in $\nabla V$** (the $|V_1|$, $|V_2|$ terms). Standard for
   two-player reachability; Lax–Friedrichs needs bounds on the partials for the dissipation
   coefficient: $|\partial H/\partial V_R| \le 2$, and
   $|\partial H/\partial V_i| \le |L|/R + 1 \le 2/R_{\min} + 1$.

**Direct precedent worth knowing about.** Mitchell, Bayen & Tomlin's worked example in the
paper that introduced this formulation is **the game of two identical cars** — Merz (1972),
which is precisely the kinematic model D&S build on (LitNotes: "game of two identical cars
dynamics (Merz, 1972)"). So the method proposed here has already been applied to this
project's own base dynamics; what is new here is the aspect-dependent WEZ target set in place
of a fixed capture radius.

**Tooling.** Do not write a level-set solver from scratch — this is weeks of avoidable
work. Evaluate existing packages against two hard requirements: *periodic dimensions* and
*two-player (min-max) Hamiltonians with a min-over-time reach formulation.* Candidates worth
evaluating, in rough order of fit for a Python/JS codebase: `hj_reachability` (JAX),
`optimized_dp`, and Mitchell's original `ToolboxLS`/`helperOC` (MATLAB). Confirm the
current API of whichever is chosen against its own documentation; do not assume interfaces
from memory.

---

## 4. Milestones

**M1 — Formulation, verified before any solve. DONE 2026-09-14.** $\ell(x)$ vs.
`barrier.in_target` with zero mismatches on 5.93M nodes; `dynamics.hamiltonian` vs.
`barrier.hamiltonian_star` to 3 ulp. Details and two carried findings in
`claude/Layer1_Progress_2026-09-14.md`.

**M2 — One-player smoke test. DONE 2026-09-14.** $\sigma_2$ frozen; reach front at the
analytic closing speed 2.003 vs 2; every margin tightens under refinement; the old pursuit
heuristic fails to beat $V$ by even one grid cell.

**M3 — Full two-player solve. DONE 2026-09-18** (`claude/Layer1_M3_2026-09-18.md`). Converged in horizon (zero level set stops moving — the
progress note already observes the outer edge pinning at $R = 5.98$ against
$\bar R(0) = 6.1416$) and in grid ($101^3$ vs $201^3$, measuring drift of the **zero level
set**, not of $V$). Budget it as an overnight job: ~2 h at $201^3$, and gradient storage is the
binding constraint.

**M4 — Acceptance against Layer 0.** §5 below. This is the gate for the single-target solve.
*(Scoped 2026-10-01: Layer 0's trajectories are locally correct characteristics, but the global
assembly that decides which segments are actually part of the barrier was never done. Compare
only where a trajectory is on the active boundary — see §5's note — and treat a departure as a
candidate inactive segment, not automatically as a failure.)*

**M5 — The two-target partition by reach-avoid, now this layer's central claim.**
*(Redefined 2026-10-01; the previous M5, a comparison of $t_1^*$ with $t_2^*$, is withdrawn —
§2.3.)*

1. *Solve one reach-avoid value* $V^{RA}_1$ on the M3 grid ($101\times102^2$, then
   $201\times204^2$): **reach** $T'_{1} = T_{1\to2} \setminus T_{2\to1}$ (winning alone) while
   **avoiding** $T_{2\to1}$ (being killed or traded), player 1 minimizing and player 2
   maximizing over *all* behaviors. The constraint set comes free: $\ell_2 = \ell_1 \circ S$.
   This is the standard reach-avoid formulation (Fisac et al., arXiv:1410.6445). **Verify the
   variational inequality and its sign conventions against that source before implementing**
   (§2.4's rule). **Tooling, checked against the 0.7.0 source on 2026-10-01:**
   `hj_reachability/solver.py` ships `static_obstacle(obstacle)`, a value postprocessor that
   applies $V \leftarrow \max(V, \text{obstacle})$ after every time step, alongside the
   `backwards_reachable_tube` Hamiltonian postprocessor ($\min(H,0)$) that M3 already uses. So
   the reach-avoid solve is `SolverSettings(hamiltonian_postprocessor=backwards_reachable_tube,
   value_postprocessor=static_obstacle(-ell_2))` with initial value $\max(\ell_1, -\ell_2)$, where
   $\ell_2 = \ell_1 \circ S$ on the grid. One caveat from the source: the postprocessor is applied
   at the end of each Runge-Kutta step, not at the intermediate stages (a TODO in
   `time_integration.py` says so). Still confirm this matches Fisac et al.'s formulation.
2. *Form the partition by guarantees* (ProblemStatement §5.4):
   $W_1 = \{V^{RA}_1 \le 0\}$, $W_2 = W_1 \circ S$ by transpose (assert the identity on the
   grid), $D = \{V_1 > 0\} \cap \{V_2 > 0\}$ from M3's fields (each player can avoid being
   killed even ignoring the stopping rule, so this is a sufficient condition for a draw), and
   **contested** = the remainder outside the target sets. Report each as a volume fraction on the
   $R \ge 0.45$ masked domain, with its grid-convergence drift.
3. *The result.* How large is the contested set, and where is it? D&S found mutual kill only on
   the surfaces $|\phi_1| = |\phi_2|$ ($M' = \emptyset$). If the contested set is thin and sits
   there, the D&S picture is reproduced by a different route. If it is fat, that is a finding
   about the formulation. Either is a result. Within the contested set, report what the Decision 2
   behavioral model (test C2) produces, labeled as assumption-dependent.
4. *Compare with the old objects*, to record how far off they were: $W_1$ against M3's
   $\{V_1 \le 0\} \setminus \{V_2 \le 0\}$ (the set previously called "win-alone"), and the
   contested set against the 4.53 % "both can force a kill" volume.

Cost: one solve per grid, the same size as M3's (about 13 min at $101\times102^2$ and 4 h at
$201\times204^2$ on the 2-core machine).

---

## 5. Acceptance tests, in increasing sharpness

Layer 0 hands over 122 verified barrier trajectories across three BUP families. Tests A–C
use them directly; D and E use the Table 2 points; F (added 2026-10-01) tests M5.

> **Scope of A–C (2026-10-01).** The 122 trajectories are correct *local* characteristics seeded
> from the single-target BUP. Layer 0 never did the global assembly (Table 3's singular lines,
> Step 4's closedness test) that decides which parts of each trajectory are actually on the
> winning-zone boundary. A trajectory may leave the active boundary at a dispersal or
> universal line and continue as a valid but irrelevant characteristic. So score A–C on each
> trajectory up to the first point where it leaves $\{V = 0\}$ by more than grid tolerance,
> report the fraction of trajectory length that passes, and list each departure point as a
> candidate inactive-segment junction to check against Table 3, rather than as a failure.
> The R ≥ 0.45 mask from M3 applies throughout.

**A — Level test.** $|V| < $ grid tolerance at every point of every Layer 0 barrier
trajectory. Necessary, not sufficient: a badly wrong $V$ can still have a zero set passing
near a curve.

**B — Gradient test.** Along those trajectories, $\nabla V$ normalized should reproduce the
Layer 0 costate $\lambda$ (which was normalized by the first integral $=1$), up to positive
scaling. This tests *direction*, not just level, and is much harder to pass by accident.
This is the test to trust.

> **Trap, carried from M1.** Do **not** score this with an error normalized by the quantity
> being compared. $H$ vanishes identically on the semipermeable surface and $V$ vanishes on the
> barrier, so a relative-to-result criterion reports the cancellation the barrier is *made of*
> as though it were error. M1 failed on exactly this at a relative error of 3.6e-12 with an
> absolute error of 1.4e-14. Score against the magnitude of the summed terms, or compare
> directions via the angle between $\nabla V$ and $\lambda$.

**C — Feedback law test.** Two halves, and they use different objects (§2.3):

*C1, on the barrier.* $\sigma^*$ derived from $\nabla V$ must reproduce `barrier.py`'s
bang-bang controls along the Layer 0 trajectories, **including at the located switches**.

> **Trap, carried from M2.** A finite-horizon value must be read at the **remaining** horizon:
> $\sigma_1^*(x,t) = -\operatorname{sign}\big(\partial V(x, T-t)/\partial\phi_1\big)$, never
> $\partial V(x,T)$. The Layer 0 trajectories are parameterized by retrograde time $\tau$, so
> C1 must compare against $\nabla V(\cdot,\tau)$ at the matching horizon. Getting this wrong
> fails C1 on a correct $V$ — in M2 it cost a factor of 16 in shortfall. Build the law only via
> `hji.make_policy`.

*C2, in the interior — under Decision 2.* *(Reframed 2026-10-01: this is a test of the
behavioral model, not of optimality — §2.3.)* Both players race toward their own target set, so
this half of the test is run against the **arrival-time gradients**, not $\nabla V$:

- player 1's law from $\nabla t_1^*$, player 2's from $\nabla t_2^* = \nabla(t_1^*\circ S)$;
- **the specific behavioural claim to check:** a doomed player 2 should turn *toward*
  $T_{2\to1}$ to force the trade, and the resulting engagements should terminate in a mutual
  kill or a player-2 kill, not in player 2 fleeing. Compare where these engagements end against
  M5's partition: a start in $W_1$ must still end in a player-1 win even against this trading
  player 2, because $W_1$ is a guarantee (and if player 1 plays the reach-avoid law, this is a
  direct check of that guarantee);
- no long-range inversion of the angular-advantage result beyond $R \approx 8$, which is the
  §4 criterion proper and the heuristic's known failure.

Do **not** run C2 against $\nabla V$. Inside the winning zone that gradient optimizes
penetration depth into the WEZ, which under instantaneous kill on entry is physically
meaningless — see §2.3.

**D — Table 2 test.** $\{V = 0\}$ should pass through the 27 Table 2 points that
`validate_table2.py` placed on determined surfaces.

**E — Singular-structure test.** $V$'s non-differentiability locus *is* the singular-surface
structure: dispersal, universal, equivocal and switch surfaces are where the gradient jumps or
vanishes. Detect it numerically (gradient jumps / large second differences) and compare
against D&S Table 3's 25 singular lines. **This is how Layer 0's largest open item closes:**
32 of 59 Table 2 points remain unplaced precisely because they are interior features —
universal-line endpoints, dispersal junctions, switch-line crossings — and if they lie on the
detected locus, Layer 1 places them. Cheap to run once $V$ exists, and a result in its own
right rather than only a check.

**F — Two-target acceptance (M5, added 2026-10-01).** $W_1$ should reproduce D&S's
**corrected** winning zone for player 1: five disconnected closed subregions (two small
max-range zones, two off-boresight zones, one large minimum-range zone), Figs. 8 and 13, with
the Table 2 points that lie on the corrected boundary on $\partial W_1$. Simulate from sampled
states in $W_1$ with player 1 on the reach-avoid law against several player-2 laws (avoid,
trade via $\nabla t_2^*$, the pursuit heuristic): every run must end in a player-1 win alone. A
single counterexample means the reach-avoid formulation or its implementation is wrong.

**Negative control — run this, it is not optional.** The old heuristic
$\sigma_i = -\operatorname{sign}(\phi_i)$ must **fail** test C at long range. A test suite
that passes for both the right answer and a known-wrong one is not testing anything.

---

## 6. Carried-forward facts a new session must not rediscover

- **$\bar R_0 = 3 + \pi = 6.141593$, not 6.14.** D&S Sec. 4 quotes the rounded value; Table 2
  pins the exact one. Already corrected in `sim.js` and asserted in `test_acceptance.js`.
- **D&S Eq. (63) carries a spurious $\operatorname{sign}\phi_1$** and contradicts the paper's
  own Eqs. (64)–(65) at $\phi_1 = -\beta$. Use `barrier.lam_boresight`, never the printed
  equation. Details in close-out §5.2.
- **Sign convention.** The codebase uses D&S's $\dot\phi = \text{LOS rate} + \sigma$. Under
  the opposite convention every control law flips sign. ProblemStatement §2 has the full
  warning.
- **Index asymmetry.** Boresight bound on the *shooter's own* angle; both range bounds on the
  *target's* aspect angle. Easiest thing in the model to get wrong.
- **Layer 0's barriers are single-target** — seeded from the uncorrected $T_{1\to2}$. That is
  exactly right as ground truth for this layer, which solves the same single-target reach
  problem. The Appendix B correction $T_1' = T_1 \setminus \bar T_2$ belongs to Layer 2; see
  §7.
- **$f_1$'s defining condition is unrecoverable** from the printed text. Open marker, not a
  blocker here.
- **A doomed player prefers a mutual kill** (§1, Decision 2), with the ordering
  win alone ≻ draw ≻ mutual kill ≻ die alone. This is a *modelling* decision, not a derived
  fact. It does not affect the barrier, M3, M5, or tests A/B/D/E — only the interior feedback
  law and test C2. §11 records the alternative and how to switch.
- **$V_2 = V_1 \circ S$ and $t_2^* = t_1^* \circ S$** (§2.5). Never solve the second game;
  transpose the first. Assert the identity on the grid before relying on it.
- **Read a finite-horizon value at the remaining horizon**, $\nabla V(x, T-t)$, via
  `hji.make_policy`. The natural mistake costs a factor of 16 in M2's shortfall metric.
- **Do not compare $t_1^*$ with $t_2^*$ to decide an outcome** (revision 2026-10-01). They are
  guarantees from different games. Outcome guarantees come from the reach-avoid solve (M5).
- **Do not score gradient/Hamiltonian agreement with a relative error.** $H$ and $V$ both vanish
  on the surface being tested, so relative error reports the barrier's defining cancellation as
  a defect.

---

## 7. How this layer replaces the Appendix B correction (rewritten 2026-10-01)

D&S's target-set correction $T_i' = T_i \setminus \bar T_j$ exists because **a game of kind
has no clock**: it infers who gets there first from set overlap, and then needs the case rules
of Appendix B to recombine the single-target pieces.

**The previous version of this section** argued that arrival-time fields $t_1^*$, $t_2^*$ supply
that clock, so the partition becomes a comparison $t_1^* \lessgtr t_2^*$ and Appendix B's
bookkeeping is unnecessary. That argument fails for the reason in §2.3: the two fields are
guarantees from two different games, and comparing them does not establish which event comes
first. Withdrawn.

**What does replace it is a reach-avoid solve.** "Player 1 can reach $T_{1\to2}\setminus
T_{2\to1}$ without first entering $T_{2\to1}$, against any player-2 behavior" is exactly the
statement Appendix B's corrected sets approximate, and an HJI reach-avoid value computes it
directly. The correction $T_1' = T_1 \setminus \bar T_2$ appears as the reach target; what
Appendix B handles with case rules (faces of $\partial T_1'$ inherited from $\partial T_2$, the
$M'$ / $M$ split) is handled by the constraint in the PDE. This is a construction, not a
conjecture, and test F checks it against D&S's own corrected zones.

**Why it matters for Layer 2.** The 2v1 partition is a reach-avoid problem with more sets:
an attacker reaches $T_{A_i\to B}$ while the team avoids $T_{B\to A_1}$ and $T_{B\to A_2}$, with a
continuation game when one attacker is lost. Getting the two-target version right in 1v1, with
ground truth to compare against, is the step that makes the four-target version credible. It
also gives the Layer 2 continuation value (ProblemStatement §5.4).

**What does not go away.** The singular structure still exists. It moves from something
catalogued by hand into the non-differentiability locus of the value, where any controller
playing from an arbitrary state still has to handle it, and where test E still has to extract it.
"Cheaper to obtain" is the claim; "no longer present" is not.

Either outcome of M5 — a thin contested set on $|\phi_1| = |\phi_2|$, or a fat one — is a result.

---

## 8. Explicitly out of scope for Layer 1

Scope discipline matters more here than anywhere, because each of these is individually
tempting and collectively a semester.

- **The four-target synthesis.** Layer 2. *(2026-10-01: the two-target version is now in scope,
  as M5's reach-avoid solve; see §7.)*
- **The 25 singular lines of D&S Table 3**, and the winning-zone assembly of their Fig. 13.
  ProblemStatement §8 item 6 already decided to defer these on the grounds that Layer 1's
  $V$ produces the same object globally and more cheaply. That decision stands and §7
  strengthens it.
- **Anything 2v1.** Six states, four target sets, Layer 2.
- **Resolving $f_1$.** Open marker, unrelated to this layer.

---

## 9. Files

Existing, in `Two_Target_Pursuit_Missile/`:

```
layer0/barrier.py          dynamics, costates, hamiltonian_star, BUP, retrograde integrator
layer0/test_mirror.py      verifies the T_2 index swap (4/4, machine precision)
layer0/validate_table2.py  the 59 Table 2 points, 27 placed
layer0/test_barrier.py     invariant + control-law tests; emits the 122 trajectories
layer0/LAYER0_CLOSEOUT.md  what Layer 0 does and does not supply
```

Existing, in `layer1/` (M1–M2, see the progress note):

```
layer1/ell.py              implicit surface fn; imports BETA/A1/B1/RBAR0 from layer0/barrier.py
layer1/hji.py              hj_reachability 0.7.0 setup; make_policy is the ONLY supported
                           way to build a feedback law (it enforces the remaining-horizon read)
layer1/test_m1.py          formulation gate
layer1/test_m2.py          one-player smoke test, incl. the stale-horizon read as a failing case
layer1/README_LAYER1.md
```

Created at M3 (see the M3 record), plus still to be created:

```
layer1/solve_m3.py         converged two-player solve + grid study; emits V and t1* (exists)
layer1/test_m4.py          acceptance tests A-E plus the negative control
layer1/reach_avoid.py      M5: V_RA_1 (reach T1 minus T2, avoid T2); W1, W2 = W1 o S, D, contested
layer1/test_m5.py          test F: D&S corrected zones + W1 guarantee simulations
```

Reference documents: `claude/ProblemStatement.md` (the spec of record),
`claude/Layer0_CloseOut_2026-09-11.md`, `claude/Layer0_StudyGuide.md` (the retrograde method
explained with worked numbers), `LitNotes_DavidovitzShinar1989_TwoTargetAirCombat.md`.

---

## 10. Next session's opening move

*(Rewritten 2026-10-01. M1–M3 are closed; the previous text described starting M3.)*

1. **Read `claude/Layer1_Revision_2026-10-01.md`** and this plan's revision note at the top.
   The arrival-time comparison is withdrawn; do not build M5 on it.
2. **Set up M5's reach-avoid solve** on the $101\times102^2$ grid: derive the variational
   inequality from Fisac et al. (arXiv:1410.6445) rather than transcribing it, confirm how
   `hj_reachability` 0.7.0 takes a constraint set, and run a one-player smoke test first (player 2
   frozen, as in M2) where the answer can be checked by hand.
3. **Run M4** in parallel, scoped as §5's note says. It needs only M3's existing fields.
4. Then $201\times204^2$ overnight for M5's grid study, and test F.

---

## 11. The alternative assumption, and what it would change

> *Revision 2026-10-01.* The comparison below predates M5's redefinition. Two corrections:
> the "race" row is a behavioral model, not a solution with a sufficient-condition guarantee
> (§2.3); and M5 now computes reach-avoid sets, which are guarantees and so do **not** depend on
> this assumption at all. The assumption affects only play in the contested set and test C2.
> Where the text below says M5 computes $\{t_1^* = t_2^*\}$, read it as the old M5.

Decision 2 chose *a doomed player prefers mutual kill*. The alternative is
**survive longest**: a doomed player 2 maximizes time-to-being-killed. It is the classical
choice, so it deserves a recorded comparison rather than a dismissal.

**The good news first: the two differ in exactly one place.** Player 1's interior law is
$\nabla t_1^*$ under both — killing faster is optimal whether the opponent is fleeing or
trading. And $t_1^*$ and $t_2^*$ both come from the single M3 solve (§2.5). So:

| | mutual kill (chosen) | survive longest (alternative) |
|---|---|---|
| player 1 interior law | $\nabla t_1^*$ | $\nabla t_1^*$ — same |
| player 2 interior law | $\nabla t_2^*$, racing to $T_{2\to1}$ | $\nabla t_1^*$, maximizing it |
| extra solves needed | none | none |
| game structure | a race between two guarantees; not zero-sum; an ambiguous band | genuinely zero-sum in $t_1^*$; classical time-optimal pursuit; unique value |
| theoretical support | weaker — the race is a sufficient-condition argument | strong and classical |
| $T_{2\to1}$ needed for play | yes | no |
| M3, M5, tests A/B/D/E | unaffected | unaffected |
| test C2 | as written in §5 | player 2 should flee, not turn in |

**So the decision is cheaply reversible**, which is worth knowing before defending it: nothing
in M3 or M5 depends on it, and switching means reading player 2's interior law from a different
field that has already been computed. Running C2 **both ways** is a few extra lines and makes a
genuinely informative figure for the report — the same geometry, two doomed-player models, two
visibly different endgames.

**Why mutual kill was chosen anyway.** Survive-longest is theoretically tidier but models the
wrong agent. These aircraft carry all-aspect fire-and-forget missiles; a pilot who cannot escape
does not spend his remaining seconds maximizing them, he takes the shot. Choosing the tidier
assumption would make the interior trajectories an artifact of a convenience, which is precisely
the failure mode ProblemStatement §4 item 1 exists to prevent.

**The subtle difference in what M5's result *means*.** M5 computes $\{t_1^* = t_2^*\}$ either
way — the set where each player *can* kill the other at the same moment is a geometric fact,
independent of preferences. What changes is whether that set is ever *realized*:

- under mutual kill, player 2 actually goes for it, so those states end in a genuine mutual kill;
- under survive-longest, player 2 never takes the shot, so mutual kill is a geometric region that
  play never visits, and D&S's "$M' = \emptyset$, mutual kill is measure-zero" becomes a
  statement about geometry with no behavioural content.

Report the measured set as geometry, and state the assumption when drawing any conclusion about
outcomes.

**What would justify revisiting this.** If M5 finds a *fat* ambiguous band (§2.3's caveat), the
race formulation is weak precisely where it matters, and the zero-sum survive-longest game — with
its unique value and standard theory — becomes the more defensible basis for interior claims,
with mutual kill demoted to a geometric side-result. That is a measurement, not a judgement call,
and M5 makes it.
