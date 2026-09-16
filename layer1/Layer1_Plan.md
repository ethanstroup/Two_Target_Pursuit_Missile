# Layer 1 Plan — 1v1 Game of Degree via HJI Reachability

**AE 8900 · drafted 2026-09-14 · Ethan Stroup**
**Status:** **instructions closed 2026-09-14.** No decisions remain open at this layer; M3–M5
are executable as written. M1 and M2 are already done — see
`claude/Layer1_Progress_2026-09-14.md`. Layer 0 closed 2026-09-11
(`claude/Layer0_CloseOut_2026-09-11.md`).
**Schedule slot:** ProblemStatement §10, weeks 3–6.

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
*maximum over all* player-2 strategies, so it is the set where player 1 wins against **any**
player-2 behaviour, trading included. It is a guarantee, not a best-response calculation, and
guarantees are preference-independent.

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
   interior becomes a race between two arrival-time fields — which is the object §7 already
   wanted for the partition, so one construction serves both purposes.

   **One honest caveat on the race.** $t_1^*$ is computed against a player 2 who is *avoiding*,
   and $t_2^*$ against a player 1 who is avoiding. Both cannot be the actual play, so each is a
   **guarantee rather than a prediction**: $t_1^* < t_2^*$ is a *sufficient* condition for
   player 1 to win alone, $t_2^* < t_1^*$ for player 2, and the states where neither strict
   inequality holds form a band Layer 1 does not resolve. Whether that band is measure-zero or
   fat is exactly M5's question, and exactly what decides whether §7's claim survives. Say
   "sufficient condition", not "the partition", when writing this up.
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

### 2.5 The second value function costs nothing, and predicts the mutual-kill surface

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

**2. The mutual-kill surface is predicted by symmetry alone.**
$\{t_1^* = t_2^*\} = \{x : t_1^*(x) = t_1^*(Sx)\}$. That holds wherever $Sx = x$, i.e.
$\phi_1 = \phi_2$; and wherever $Sx = Rf\,x$, i.e. $\phi_1 = -\phi_2$, because $t_1^*$ is
$Rf$-invariant. Hence

$$\{t_1^* = t_2^*\} \;\supseteq\; \{|\phi_1| = |\phi_2|\},$$

which is *precisely* D&S's Eq. (87) result, obtained here from two symmetries instead of a page
of set algebra.

**So M5's content is not "does $|\phi_1| = |\phi_2|$ appear."** Symmetry guarantees it; if it
fails to appear, there is a bug, and that makes a good cheap smoke test. **M5's content is
whether anything *else* appears** — whether $\{t_1^* = t_2^*\}$ has an open-volume component
in addition to those surfaces. D&S found none at these parameters ($M' = \emptyset$). See §7.

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

**M3 — Full two-player solve.** Converged in horizon (zero level set stops moving — the
progress note already observes the outer edge pinning at $R = 5.98$ against
$\bar R(0) = 6.1416$) and in grid ($101^3$ vs $201^3$, measuring drift of the **zero level
set**, not of $V$). Budget it as an overnight job: ~2 h at $201^3$, and gradient storage is the
binding constraint.

**M4 — Acceptance against Layer 0.** §5 below. This is the gate.

**M5 — The mutual-kill result, now this layer's central claim.** Form $t_2^* = t_1^* \circ S$ by
transpose (§2.5 — no second solve), then:
1. *Smoke test:* confirm $\{t_1^* = t_2^*\} \supseteq \{|\phi_1| = |\phi_2|\}$. Symmetry
   guarantees this; failure means a bug, most likely an asymmetric angular grid.
2. *The actual question:* measure whether $\{t_1^* \approx t_2^*\}$ has an **open-volume
   component** beyond those surfaces, at a tolerance tied to grid resolution and reported with
   it. D&S predict none ($M' = \emptyset$) at these parameters.
3. *Report the ambiguous band* where neither strict inequality holds (§2.3's caveat) as a
   measured volume fraction, not as a footnote. Its size is the result.

---

## 5. Acceptance tests, in increasing sharpness

Layer 0 hands over 122 verified barrier trajectories across three BUP families. Tests A–C
use them directly; D and E use the Table 2 points.

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

*C2, in the interior — under Decision 2.* Both players race toward their own target set, so
this half of the test is run against the **arrival-time gradients**, not $\nabla V$:

- player 1's law from $\nabla t_1^*$, player 2's from $\nabla t_2^* = \nabla(t_1^*\circ S)$;
- **the specific behavioural claim to check:** a doomed player 2 should turn *toward*
  $T_{2\to1}$ to force the trade, and the resulting engagements should terminate in a mutual
  kill on a set consistent with M5 — not in player 2 fleeing;
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
- **Do not score gradient/Hamiltonian agreement with a relative error.** $H$ and $V$ both vanish
  on the surface being tested, so relative error reports the barrier's defining cancellation as
  a defect.

---

## 7. Why this layer probably dissolves the Appendix B correction

D&S's target-set correction $T_i' = T_i \setminus \bar T_j$ exists because **a game of kind
has no clock.** It infers "who gets there first" from set overlap, because set operations
are the only tool available without a time coordinate.

Layer 1 supplies a clock. With arrival-time fields $t_1^*(x)$ and $t_2^*(x)$ — the second
obtained free by the verified index swap — the partition is a comparison rather than a set
construction, and the $M'/M$ bookkeeping of Appendix B should not be needed at all.

**The prediction is now sharper than "falsifiable" — half of it is a theorem.** §2.5 shows
from the swap and reflection symmetries alone that
$\{t_1^* = t_2^*\} \supseteq \{|\phi_1| = |\phi_2|\}$, which is D&S's Eq. (87) surface. That
half is not in question and serves as a smoke test. The open half is whether the set is
*exactly* those surfaces or has an open-volume component as well — i.e. whether
$M' = \emptyset$ survives, which D&S themselves flag as parameter-dependent.

If it does: Layer 2's §5.5 method ("extend Appendix B from two target sets to four") can
likely be replaced by a cheaper comparison-of-value-functions argument, which is a
substantial de-risking of the hardest part of the semester. If it does not: that is a real
finding about the formulation and worth chasing.

**Scope this claim carefully.** What dissolves is the need to *enumerate* singular lines in
order to obtain the partition — the partition becomes an inequality between arrival-time
fields. The singular structure itself does **not** go away. It moves from something catalogued
by hand into the non-differentiability locus of $V$, where it still has to be handled by any
controller that plays from an arbitrary state (§2.3) and still has to be extracted to place
the 32 Table 2 points (§5, test E). "Cheaper to obtain" is the claim; "no longer present" is
not.

Either outcome is a result. This is M5, and it is the most likely source of the report's
central claim.

---

## 8. Explicitly out of scope for Layer 1

Scope discipline matters more here than anywhere, because each of these is individually
tempting and collectively a semester.

- **The Appendix B correction and the two-target synthesis.** Layer 2. See §7.
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

To be created:

```
layer1/solve_m3.py         converged two-player solve + grid study; emits V and t1*
layer1/test_m4.py          acceptance tests A-E plus the negative control
layer1/mutual_kill.py      t2* = t1* o S by transpose; the M5 measurements of §4
```

Reference documents: `claude/ProblemStatement.md` (the spec of record),
`claude/Layer0_CloseOut_2026-09-11.md`, `claude/Layer0_StudyGuide.md` (the retrograde method
explained with worked numbers), `LitNotes_DavidovitzShinar1989_TwoTargetAirCombat.md`.

---

## 10. Next session's opening move

M1 and M2 are closed. **Start at M3**, and before launching the long solve do two cheap things
in this order:

1. **Re-read `claude/Layer1_Progress_2026-09-14.md`'s three findings.** The remaining-horizon
   read is the one that will silently ruin M4 test C if forgotten, and it is already encoded in
   `hji.make_policy` — use that, never a hand-rolled gradient read.
2. **Assert the §2.5 transpose identity on the actual grid** before relying on
   $t_2^* = t_1^*\circ S$. It is exact in the continuum and holds numerically only if the
   $\phi_1$ and $\phi_2$ discretizations are identical. Thirty seconds, and it is the
   difference between M5 being a transpose and M5 being a second overnight solve.

Then run M3 at $101^3$ for structure and queue $201^3$ overnight for the convergence study.

---

## 11. The alternative assumption, and what it would change

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
