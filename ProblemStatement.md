# Problem Statement — AE 8900

**2v1 Air Combat with Bidirectional Lethality**

**Author:** Ethan Stroup · **Started:** 2026-09-09 · **Status:** v0.2, draft for revision
**Deliverable:** AE 8900 final report + presentation, end of Fall 2026 semester (~14 weeks from this date)

> **v0.2 scope change (2026-09-09).** Synchronized impact is **deferred**. The driving
> question for this semester is the **2v1 game of kind with bidirectional lethality** —
> which is itself an unfilled gap: the literature review found no source combining genuine
> bidirectional lethality with cooperative multi-pursuer team structure. The synchronization
> formulation is preserved in §6 as deferred work, not deleted. The longer-arc project name
> ("2v1 Synchronized-Impact Pursuit-Evasion") is unchanged.

---

## 0. Why this file exists

Eight days of literature review ran against a problem specification that existed only
informally. This file is that specification. It is the reference every later decision keys
off: what is being solved, in what order, under what assumptions, and what counts as done.

It is written in **layers**. Each layer is a self-contained problem with its own state
space, its own solvable question, and its own acceptance criteria. A layer is not started
until the one below it is closed. The layers exist so that the semester ends with a
finished result at *some* level rather than an unfinished one at the top.

Anything marked **[OPEN]** is an unresolved decision, not an oversight.

---

## 1. The engagement in words

Two friendly aircraft (**attackers** $A_1$, $A_2$) engage a single hostile aircraft
(**bandit** $B$) in the horizontal plane. All three carry all-aspect fire-and-forget
missiles. Lethality is **bidirectional**: the bandit can kill either attacker, and either
attacker can kill the bandit. Nobody is a designated pursuer; roles are an output of the
geometry, not an input.

The bandit has **one nose**. Its weapon envelope is a boresight-limited, aspect-dependent
region attached to its own heading, so it can only threaten one attacker at a time unless
the two attackers are angularly close as seen from the bandit. That single fact is what
makes a two-attacker engagement qualitatively different from two independent duels.

**The question this project asks:** how does the outcome of a bidirectionally lethal air
combat partition the state space when one side has two aircraft and the other has one, and
the lone aircraft can only point its weapon in one direction at a time?

No source in the literature review answers this. Every reviewed paper with genuine
bidirectional lethality is 1v1; every reviewed paper with cooperative multi-pursuer
structure has one-sided lethality. The intersection is empty, and it is where this project
sits.

---

## 2. Notation and conventions

| Symbol | Meaning |
|---|---|
| $A_1, A_2$ | attackers (the team) |
| $B$ | bandit |
| $R_i$ | range from $A_i$ to $B$, normalized by minimum turn radius $\rho$ |
| $\phi_i$ | off-boresight angle of the LOS $A_i \to B$, measured in $A_i$'s body frame |
| $\psi_i$ | off-boresight angle of the LOS $B \to A_i$, measured in $B$'s body frame |
| $\sigma_i, \sigma_B$ | normalized turn-rate controls, $|\sigma| \le 1$ |
| $\beta$ | boresight (squint) half-angle of the weapon |
| $\underline R(\cdot), \bar R(\cdot)$ | minimum and no-escape firing range |
| $T_{X \to Y}$ | target set: states in which $X$ can kill $Y$ |

**Normalization.** All aircraft fly at constant equal speed $V$ with equal maximum turn
rate $\omega_{\max}$. Lengths are normalized by the common minimum turn radius
$\rho = V/\omega_{\max}$, times by $\rho/V$. Speed is therefore unity and $|\sigma| \le 1$.

**Sign-convention trap — read this before porting any equation.**
Deriving $\dot\phi$ from the inertial kinematics with $\phi \triangleq \lambda - \theta_A$
(LOS bearing minus own heading) gives

$$\dot\phi = \frac{\sin\phi + \sin\psi}{R} - \sigma .$$

Davidovitz & Shinar print a **plus**. The two differ by $\sigma \mapsto -\sigma$, which is
immaterial to the dynamics (the control set is symmetric) but flips the sign of every
control law. The existing codebase in this repository uses **D&S's convention**
($\dot\phi = \text{LOS rate} + \sigma$), under which the pure-pursuit heuristic is
$\sigma_i = -\operatorname{sign}(\phi_i)$. **This document adopts D&S's convention
throughout** so that code and paper agree. Under the opposite convention the same
heuristic reads $\sigma_i = +\operatorname{sign}(\phi_i)$.

---

## 3. Layer 0 — 1v1 base case (Davidovitz & Shinar 1989)

**Status: substantially built. Closing this layer is the first task of the semester.**

### 3.1 State and dynamics

Reduced state $x = (R, \phi_1, \phi_2) \in \mathbb{R}_{>0} \times S^1 \times S^1$, where
players 1 and 2 are symmetric and $\phi_2$ plays the role $\psi_1$ plays in Layer 2.

$$\dot R = -(\cos\phi_1 + \cos\phi_2), \qquad
\dot\phi_i = \frac{\sin\phi_1 + \sin\phi_2}{R} + \sigma_i, \qquad |\sigma_i| \le 1 .$$

Three states rather than six: $2 \times 3 = 6$ configuration variables less the three
dimensions of planar rigid motion.

### 3.2 Target sets

For player $i$ against opponent $j$:

$$T_{i \to j} = \Big\{ \, |\phi_i| \le \beta \ \wedge \ \underline R(\phi_j) \le R < \bar R(\phi_j) \, \Big\}$$

$$\underline R(\phi_j) = a + b\cos\phi_j, \qquad
\bar R(\phi_j) = \bar R_0 - |\phi_j + \sin\phi_j| .$$

**The index asymmetry is the single easiest thing to get wrong.** The boresight bound is on
the shooter's *own* angle; both range bounds depend on the *target's* aspect angle
$\phi_j$. The no-escape range is largest when the target is nose-on ($\phi_j = 0$), because
a closing target cannot escape as far — which is why, under mutual pure pursuit, turning
nose-on to your opponent maximizes *his* envelope against you.

Worked parameters (D&S Sec. 4, modelling $h = 3$ km, $V = 360$ m/s, $n_{\max} = 6$,
$\rho = 2200$ m): $\beta = 45°$, $\bar R_0 = 6.14$, $a = 0.55$, $b = 0.30$.

### 3.3 Outcomes

Terminal classification, evaluated in this order: mutual kill ($T_{1\to2} \cap T_{2\to1}$),
then P1 win, then P2 win, then draw at the horizon. Admissible initial conditions exclude
$T_{1\to2} \cup T_{2\to1}$.

D&S's result at these parameters: each player's winning zone is five disconnected closed
subregions, and mutual kill collapses to four measure-zero semipermeable surfaces
($|\phi_1| = |\phi_2|$) rather than an open volume. **This is parameter-dependent** — Rule
III of their Appendix B permits genuine open-volume mutual kill — and testing whether the
collapse survives into Layer 2 is one of the questions this project can answer.

### 3.4 What is built, and what is missing

Built (`sim.js`, `render.js`, `index.html`, `test_acceptance.js`, spec v2): verified
dynamics, correct index asymmetry, angle wrapping with the $\pm\pi$ boundary case handled,
RK4 integration, analytic target-set shading, an admissibility mask, and a 73×73
acceptance grid with measured outcome fractions at four ranges.

Missing, and this is the whole reason Layer 1 exists: **the control law is a heuristic.**
D&S derive $\sigma^* = -\operatorname{sign}(\lambda)$ only *along barrier trajectories*,
with costates seeded by transversality at the boundary of the usable part. There is no
global feedback law, because in a pure game of kind the strategies inside a winning zone
are arbitrary by definition. The current sim substitutes $\sigma_i = -\operatorname{sign}(\phi_i)$,
which tracks the paper's angular-advantage result at short range and **inverts it** beyond
$R \approx 8$.

**To close Layer 0:** reconstruct actual barrier trajectories by integrating the costate
ODEs backward from digitized BUP points, using the true $\sigma_i^* = -\operatorname{sign}(\lambda_i)$
/ $\sigma_j^* = +\operatorname{sign}(\lambda_j)$ laws, with the first integral
$(\lambda_1+\lambda_2)^2/R^2 + \lambda_R^2 = 1$ as an integration check. This produces
ground truth against which every later layer is validated.

---

## 4. Layer 1 — 1v1 game of degree

**Status: not started. This is the enabling layer and the first new work of the semester.**

Layer 0 gives a partition of the state space. It does not give optimal play from an
arbitrary interior state. Layer 1 closes that gap in the one setting where the answer is
checkable against a published solution.

**Why this layer still earns its place with synchronization deferred.** Three standing
reasons, none of which depend on Layer 3:

1. **You cannot trust a simulation without it.** The existing Layer 0 sim substitutes a
   pursuit heuristic and consequently *inverts* the paper's own angular-advantage result
   beyond $R \approx 8$. That failure was catchable because D&S published the right answer.
   The same failure at Layer 2 — six states, no published answer, less intuition — would
   not be caught. A verified global feedback law is the instrument, not the result.
2. **Layer 2 needs a continuation value.** Under the recursion in §5.4, the engagement after
   one attacker is lost *is* the Layer 0/1 game. Its value function is exactly the terminal
   payoff the 2v1 problem needs, so Layer 1's output is a required input to Layer 2 rather
   than a parallel line of work.
3. **It is where the numerical method gets validated.** Whichever solver is chosen, this is
   the only layer with ground truth to check it against before it is pointed at a problem
   nobody has solved.

Solve for a value function $V(R, \phi_1, \phi_2)$ over the 1v1 game, yielding a feedback
law valid everywhere, not only on the barrier. Candidate payoffs, **[OPEN]**:

- **Time-to-kill.** $V = \min_{\sigma_1}\max_{\sigma_2} t_f$ subject to termination in
  $T_{1\to2}$. Classical, but ill-posed wherever player 1 cannot win.
- **Terminal miss / margin.** A scalar measuring how deeply the terminal state penetrates
  the target set, or how far it misses. Defined everywhere, and the natural analogue of
  Hayoun & Shima's zero-effort-miss framing.
- **Capture-region-signed time.** Time-to-kill inside the winning zone, negative
  time-to-being-killed outside. Continuous across the barrier by construction.

The barrier from Layer 0 is the zero level set of the last two options, which makes Layer 0
a hard correctness test on Layer 1 rather than merely a predecessor.

**Method [OPEN].** Three routes are live, all sourced from the review: an HJI solve on a
$(R,\phi_1,\phi_2)$ grid; direct orthogonal collocation (Dillon et al.'s route, and the
review's standing recommendation once multiple simultaneous constraints appear); or
Yan et al.'s KKT-based convex reformulation. Recommendation is to prototype the HJI grid
first — three states is small enough that a dense solve is cheap, and the result is a
global law rather than a trajectory.

**Acceptance:** the zero level set of $V$ reproduces the Layer 0 barrier; optimal play from
interior states does not exhibit the long-range inversion the heuristic shows.

---

## 5. Layer 2 — 2v1 game of kind

**Status: formulated below, not solved.**

### 5.1 Reduced state — six states, verified

Add $A_2$. Nine configuration variables less three for planar rigid motion gives **six**
reduced states:

$$x = (R_1, \phi_1, \psi_1, R_2, \phi_2, \psi_2).$$

These are complete and independent: $\psi_1, \psi_2$ fix the two LOS directions in $B$'s
frame, $R_1, R_2$ fix the attacker positions on those lines, and $\phi_1, \phi_2$ fix the
attacker headings. The inter-attacker range is then determined, not free.

### 5.2 Dynamics — the structure is the result

Derived from the full planar kinematics and **verified symbolically (residual exactly zero
on all four components, 2026-09-09)**, in D&S's sign convention:

$$\dot R_i = -(\cos\phi_i + \cos\psi_i), \qquad
\dot\phi_i = \frac{\sin\phi_i + \sin\psi_i}{R_i} + \sigma_i, \qquad
\dot\psi_i = \frac{\sin\phi_i + \sin\psi_i}{R_i} + \sigma_B .$$

**The 2v1 system is exactly two copies of the D&S 1v1 system, coupled only through the
bandit's single control $\sigma_B$.** Nothing else is shared. This is the mathematical
statement of "the bandit has one nose," and it is the most useful structural fact in this
document: every piece of D&S machinery — target sets, barrier construction, the costate
formalism, the first integral — ports to each pair unchanged, and the entire difficulty of
the 2v1 problem is concentrated in one scalar control appearing in two places.

### 5.3 Four target sets, not three

$$T_{A_i \to B} = \big\{ |\phi_i| \le \beta \ \wedge\ \underline R(\psi_i) \le R_i < \bar R(\psi_i) \big\}$$
$$T_{B \to A_i} = \big\{ |\psi_i| \le \beta \ \wedge\ \underline R(\phi_i) \le R_i < \bar R(\phi_i) \big\}$$

The bandit's lethality **splits by which attacker it engages**, which is why there are four
sets and not three.

**A one-line consequence worth stating early.** $B$ can hold both attackers inside its
boresight cone only if $|\psi_1| \le \beta$ and $|\psi_2| \le \beta$ simultaneously. Since
the angular separation of the attackers as seen from $B$ is $\Delta = \psi_1 - \psi_2$,
this requires

$$|\Delta| \le 2\beta .$$

At $\beta = 45°$: **if the attackers keep their angular separation about the bandit above
90°, the bandit cannot threaten both at once, regardless of range.** That is a hard,
parameter-explicit team constraint that falls straight out of the formulation, and it is a
strong candidate for the first analytic result of the project.

### 5.4 Outcome partition **[OPEN]**

Five raw outcomes exist — bandit killed with both attackers alive; bandit killed with one
attacker lost; both sides lost; bandit survives with one or both attackers lost; draw — and
they must be ordered into a preference before any game can be posed. The team objective is
**[OPEN]** and is a genuine modelling decision, not a detail:

- Is losing one attacker to kill the bandit a **win** or a **trade**?
- Does the team maximize the guaranteed outcome (max-min), or the outcome against a
  worst-case bandit that is itself trying to survive *and* kill?
- If $A_1$ is lost, does $A_2$ continue as a 1v1 (in which case Layer 0/1 is literally the
  continuation game), or is the engagement over?

The third question has a convenient answer: **treat the post-loss engagement as the Layer 0
game.** That makes the layer stack a genuine recursion rather than a sequence of unrelated
problems, and gives the 2v1 terminal condition a well-defined continuation value as soon as
Layer 1 supplies $V$.

### 5.5 Method

Extend D&S's Appendix B synthesis rules from two target sets to four. The rules decompose a
two-target game into single-target subgames, correct for target-set overlap via
$T_i' \triangleq T_i \setminus \bar T_j$, and recombine by explicit case rules. Whether
that recipe generalizes to four sets with a shared control is unknown and is itself a
contribution if answered either way.

---

## 6. Layer 3 — synchronization as a derived property **[DEFERRED]**

**Status: out of scope for AE 8900 as of v0.2. Formulation retained; no work planned this
semester.** Kept in full because the framing is already correct and the deferral is a
scheduling decision, not a change of mind — this is the natural continuation once Layers
0–2 are closed.

### 6.1 The question

Define impact times $t_{f,i}$ as the instant the state enters $T_{A_i \to B}$.
**Synchronization is not imposed.** The team plays optimally against the objective fixed in
§5.4, and the question is measured, not assumed:

> Under aspect-dependent bidirectional lethality and turn-rate-limited dynamics, does
> team-optimal play drive $|t_{f,1} - t_{f,2}| \to 0$?

The literature says this is a live question rather than a foregone one. Simultaneity is a
*derived* property of optimal play in Makkapati et al. (2018) and Pachter et al. (2019) —
but both are simple motion with point capture and one-sided lethality. Hayoun & Shima
(2017) get equal intercept times only as a restriction on initial geometry, arranged before
the endgame, and conclude that cooperation between two strong pursuers is *not beneficial*.
Nobody has asked the question with a boresight-limited, aspect-dependent envelope on both
sides.

Three outcomes are all publishable: simultaneity emerges (confirms the intuition, extends
the derived-from-optimal-play result to a much harder model); it does not (the one-nose
constraint is better exploited by sequencing, which contradicts the tactical intuition); or
it emerges only in an identifiable region of the state space (the most likely and most
interesting answer — a *synchronization region*, and a barrier bounding it).

### 6.2 The precondition this layer carries

**Synchronization cannot be derived from a pure game of kind.** In a game of kind, strategies
in the interior of a winning zone are arbitrary by definition — any strategy that keeps you
in the zone is optimal, so impact *timing* is undetermined and $|t_{f,1}-t_{f,2}|$ is not a
well-defined function of the initial state. Asking "does optimal play synchronize?" of a
game of kind is asking a question the object cannot answer.

This is the same limitation the existing codebase already ran into: D&S give no interior
feedback law, so the sim had to substitute a heuristic, and the heuristic's answers at long
range are artifacts of the heuristic rather than facts about the game.

So this layer requires a **2v1 game of degree**, not merely the 2v1 game of kind that Layer
2 delivers. That is a substantial further step beyond anything scheduled below, and it is
the main reason this layer is deferred rather than compressed into the semester. Layer 1
supplies the 1v1 half of that machinery, so the deferral costs nothing already planned.

---

## 7. Assumptions, and how firmly each is held

| Assumption | Status |
|---|---|
| Planar, coplanar motion | Firm for this project. D&S, Merz & Hague and Olsder & Breakwell all take it; Merz & Hague name it as a self-criticism. |
| Constant, equal speeds | Firm at Layers 0–2. Merz & Hague's justification (barrier maneuvers are brief, usually under a quarter turn) applies. Relaxing it is future work. |
| Equal turn-rate limits | Firm at Layers 0–2, following D&S's identical-cars model. Breaking it is a natural Layer 4. |
| Identical weapons on all three aircraft | Firm at Layers 0–2. Heterogeneous envelopes are future work. |
| Fire-and-forget, instantaneous kill on target-set entry | Firm. No missile flyout, no time of flight, no $P_k < 1$. Ciletti et al. (1973) is the only source found that models finite weapon speed. |
| Perfect state information, both sides | Firm. Standard for this literature. |
| Attackers cooperate fully; bandit knows this | Firm. |
| Kill is permanent and removes the aircraft | Firm, with the continuation-game convention of §5.4. |

---

## 8. Decisions still open

1. **§5.4 — team objective and outcome ordering.** Blocks Layer 2. Needs deciding before
   Layer 1 finishes, because the choice of Layer 1 payoff should anticipate it.
2. **§4 — Layer 1 payoff and solution method.** Blocks Layer 1. Recommendation: signed
   time-to-kill, HJI grid.
3. **Whether the $2\beta$ separation result (§5.3) is a strategy or a consequence.** With
   synchronization deferred, this is promoted to the **leading candidate for the semester's
   headline analytic result**. If the team can *guarantee* maintaining $|\Delta| > 2\beta$
   from a given initial state, that is a sufficient condition for team safety and a barrier
   in its own right — proved with Layer 0 machinery, no game of degree required. Worth
   attacking early rather than waiting for week 7.
4. **Bandit's information about which attacker is "primary."** Not yet modelled at all.
5. **Does the D&S mutual-kill collapse survive into 2v1?** D&S found mutual kill reduces to
   measure-zero surfaces at their parameters, but noted this is parameter-dependent. With
   four target sets and a shared control the question reopens, and it is answerable at
   Layer 2 without a game of degree.

---

## 9. Verification standard

Carried over from the literature-review process, which has been working:

- Every equation that will be used is **re-derived and checked symbolically** before being
  relied on, not transcribed. Where a symbolic residual fails to collapse, confirm
  numerically before recording a discrepancy.
- Anything not verified is marked **[UNVERIFIED]** inline, with a statement of what would
  settle it.
- Every numerical layer has an **acceptance test** against a known quantity — Layer 0
  against the D&S figures and Table 2 values, Layer 1 against the Layer 0 barrier, Layer 2
  against Layer 0 in the degenerate limit $R_2 \to \infty$.
- The $R_2 \to \infty$ check is worth stating explicitly: **Layer 2 must reduce exactly to
  Layer 0** when the second attacker is removed to infinity. That is a free, strong
  regression test on the six-state implementation.

---

## 10. Schedule to December

| Weeks | Work | Output |
|---|---|---|
| 1–2 | Close Layer 0: barrier reconstruction from costate ODEs; validate against D&S figures. In parallel, attack the $2\beta$ separation result (§8.3) — it needs only Layer 0 machinery | Ground-truth barrier; possibly the first analytic result already in hand |
| 3–6 | Layer 1: pick payoff, solve the 1v1 game of degree, verify zero level set against Layer 0 | Global feedback law; validated numerical method |
| 7–10 | Layer 2: implement six-state dynamics and four target sets; $R_2\to\infty$ regression against Layer 0; partition what can be partitioned | 2v1 game of kind, partially solved |
| 11–12 | Layer 2 depth: characterize the mutual-kill structure (§8.5); extend D&S Appendix B rules to four target sets as far as they go | The report's central result |
| 13–14 | Write-up, presentation | Final report |

**Honest scoping.** Layers 0 and 1 are achievable with confidence. Layer 2 is achievable as
a formulation plus partial solution, and the extra four weeks freed by deferring Layer 3
go directly into making that partial solution less partial. A finished Layer 1 plus a
substantively partitioned Layer 2 — and ideally the $2\beta$ result proved — is a
successful semester and a well-defined starting point for the synchronization work after.

---

## 11. Primary sources this rests on

- **Davidovitz & Shinar (1989)**, *JOTA* 63(2), 133–165 — Layers 0 and 2 base model,
  no-escape WEZ, Appendix B synthesis rules.
- **Getz & Pachter (1981)**, *JGC* 4(1), 15–21 — the $\max_{u_1}\min_{u_2} v_n = 0$
  primitive for finding usable-part boundaries on any target geometry.
- **Weintraub, Pachter & Garcia (2020)**, arXiv:2003.05013 — HJI verification machinery;
  Apollonius aimpoint as the simple-motion synchronization baseline.
- **Merz (1972)**, *JOTA* 9(5), 324–343 — the symmetric two-car kinematics D&S build on.
- **Hayoun & Shima (2017)**, *JOTA* 174(3), 837–857 — the contrary result that cooperation
  between strong pursuers is not beneficial; the null hypothesis for §6.1.
- **Makkapati, Sun & Tsiotras (2018)**, AIAA 2018-2107 and **Pachter et al. (2019)**,
  *JGCD* 42(7) — simultaneity as a derived property under simple motion.
- **Dillon et al. (2023)** — aspect-dependent WEZ framing; direct-collocation fallback.

Full notes for each in `LitReview_Index.md` and the `LitNotes_*.md` files.
