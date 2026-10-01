# Problem Statement — AE 8900

**2v1 Air Combat with Bidirectional Lethality**

**Author:** Ethan Stroup · **Started:** 2026-09-09 · **Status:** v0.6, draft for revision
**Deliverable:** AE 8900 final report + presentation, end of Fall 2026 semester (~14 weeks from this date)

> **v0.6 change (2026-10-01).** **An outside review of the method found a gap between the games
> solved and the outcomes claimed, and it was right.** Comparing the two arrival-time fields
> $t_1^*$, $t_2^*$ does not certify who arrives first: each is a guarantee against an opponent
> who is only *avoiding*, so the comparison is between two different games. M3's set
> $\{V_1 \le 0\} \setminus \{V_2 \le 0\}$ is likewise not a "win-alone" set. **Layer 1's M5 is
> redefined as a two-target reach-avoid solve** — player 1 reaches $T_{1\to2} \setminus T_{2\to1}$
> while staying out of $T_{2\to1}$ — which is the exact object D&S's Appendix B correction
> approximates, costs one more solve on the existing grid, and is checkable against D&S's
> corrected five-subregion zones. Also: §4 status corrected (it still said "not started"); §5.2's
> "everything ports unchanged" replaced by what was actually checked (per-pair first integrals do
> port; the control law and $H^\* = 0$ couple); §5.3's $2\beta$ result rescoped — it rules out
> *simultaneous* threat, not sequential kills, so it is not a safety condition; §5.4 gains the
> partition semantics and the Layer 1 → Layer 2 interface; §6.3 records that "impact-time
> difference" is undefined after the first kill. Full record:
> `claude/Layer1_Revision_2026-10-01.md`.
>
> **v0.5 change (2026-09-14, later).** **Doomed-player behaviour is decided:** a player who
> cannot avoid being killed prefers a mutual kill to dying alone (§7, new assumption row; §4).
> Layer 1's instructions are **closed** — no open decisions remain at that layer. M1 and M2 are
> already done (`claude/Layer1_Progress_2026-09-14.md`). §5.4 records what this does and does
> not settle for Layer 2.
>
> **v0.4 change (2026-09-14).** **Layer 1's two open decisions are closed** and the plan
> is written: `claude/Layer1_Plan.md`. The payoff is **terminal miss**, not signed
> time-to-kill — §4 records why the signed-time option fails this document's own acceptance
> criterion. §3.4 gains the target-set-2 mirror (now verified, not assumed) and states
> plainly that Layer 0's barriers are **single-target**. §8 items 2 and 6 updated.
>
> **v0.3 change (2026-09-11).** **Layer 0 is closed.** §3.4 is rewritten from a task list
> into a record of what was built and what remains; §3.2 records a corrected parameter;
> §9 gains a third verification standard. Full detail in
> `claude/Layer0_CloseOut_2026-09-11.md`. Nothing else in the document changed.
>
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
| $\sigma_i, \sigma_B$ | normalized turn-rate controls, $\vert\sigma\vert \le 1$ |
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

**Status: CLOSED 2026-09-11** — as a reconstruction of D&S's **single-target** barrier machinery
(BUP, retrograde trajectories, invariants, Table 2 acceptance). It is **not** a reconstruction of
the assembled two-target outcome partition; §3.4 says what remains. Close-out record:
`claude/Layer0_CloseOut_2026-09-11.md`.
Code: `Two_Target_Pursuit_Missile/layer0/` plus `barrier.js`.

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
$\rho = 2200$ m): $\beta = 45°$, $a = 0.55$, $b = 0.30$, and

$$\bar R_0 = 3 + \pi = 6.141593 .$$

**Not 6.14.** D&S Sec. 4 *quotes* 6.14, but Appendix A Eq. (96) defines
$\bar R_0 = (R_{tc})_{\max}/\rho + \pi$, and their Table 2 pins $(R_{tc})_{\max}/\rho$
exactly — its point $A_1$ is $\bar R(\pi)$ and is printed as **3.0**. With $3+\pi$, four
Table 2 entries come out to their printed precision ($A_1 = 3.00000$, $O_1 = 6.14159$,
$\beta = \delta = 4.64909$ against 3.0, 6.1416, 4.649); with 6.14 none of them do. The
codebase had 6.14 and now has $3+\pi$, with tightened assertions so it cannot regress.

### 3.3 Outcomes

Terminal classification, evaluated in this order: mutual kill ($T_{1\to2} \cap T_{2\to1}$),
then P1 win, then P2 win, then draw at the horizon. Admissible initial conditions exclude
$T_{1\to2} \cup T_{2\to1}$.

D&S's result at these parameters: each player's winning zone is five disconnected closed
subregions, and mutual kill collapses to four measure-zero semipermeable surfaces
($|\phi_1| = |\phi_2|$) rather than an open volume. **This is parameter-dependent** — Rule
III of their Appendix B permits genuine open-volume mutual kill — and testing whether the
collapse survives into Layer 2 is one of the questions this project can answer.

### 3.4 What was built, and what remains

**Before the close-out.** The simulation (`sim.js`, `render.js`, `index.html`,
`test_acceptance.js`, spec v2) had verified dynamics, correct index asymmetry, angle
wrapping with the $\pm\pi$ boundary case handled, RK4 integration, analytic target-set
shading, an admissibility mask, and a 73×73 acceptance grid. What it did not have was the
control law: it substituted the heuristic $\sigma_i = -\operatorname{sign}(\phi_i)$, which
tracks the paper's angular-advantage result at short range and **inverts it** beyond
$R \approx 8$.

**The close-out (2026-09-11).** Built and verified:

1. **The equation set re-derived, not transcribed.** 23 sympy checks on Eqs. (17)–(19),
   (23), (29), (31)–(32), (34)–(37), (39)–(46), (50)–(51), (53)–(56), (61)–(65). 22 pass.
   The failure is real — see §3.5.
2. **The BUP is solved, not digitized.** All three usable-part boundaries and both corner
   curves follow from closed-form conditions in the paper, so nothing had to be read off a
   figure.
3. **Retrograde state–costate integration** under the paper's own
   $\sigma_1^* = -\operatorname{sign}(\lambda_1)$, $\sigma_2^* = +\operatorname{sign}(\lambda_2)$,
   with the costate seeded by transversality. Two invariants are carried:
   $(\lambda_1+\lambda_2)^2/R^2 + \lambda_R^2 = 1$ (Eq. 23) and
   $H^\* = \min_{\sigma_1}\max_{\sigma_2}\lambda\cdot f = 0$ (Eq. 15). Both hold to
   $\le 1.4\times10^{-10}$ over 122 trajectories of retrograde length 6.
4. **Acceptance against Table 2.** 27 of 59 published points lie on a surface the equations
   determine, each to within the table's printed precision; six more are fixed by systems of
   equations and reproduce to a worst $|\Delta R|$ of $5.2\times10^{-4}$.
5. **Figures 4, 5, 6, 8, 10 and 11 redrawn** from the reconstruction in the paper's own axis
   orientation, with the Table 2 points overlaid.
6. **`barrier.js`**, a port of the same machinery for the browser visualiser, passing the
   same invariant tests.
7. **The target-set-2 mirror, verified rather than assumed** (`layer0/test_mirror.py`,
   2026-09-14). $T_{2\to1}$'s usable-part conditions are recomputed from $T_2$'s own outer
   normals with the min/max roles exchanged, and compared against the swapped call of the
   $T_1$ machinery: agreement to $2.3\times10^{-15}$ on all three families, plus the
   identity $H^\*_2(x,\lambda) = H^\*_1(\text{swap } x, \text{swap } \lambda)$ to
   $3.6\times10^{-15}$. The one excluded set is the $\phi_1 = 0$ line, where $\bar R$'s kink
   makes the outer normal non-unique — the exact mirror of $T_1$'s $\phi_2 = 0$ corner, so
   the exclusion confirms the structure rather than evading it.

**These are single-target barriers.** Every BUP in `barrier.py` is seeded from the
*uncorrected* $T_{1\to2}$. D&S's Appendix B correction $T_1' \triangleq T_1 \setminus \bar T_2$
is **not** applied, and it is not a small omission at the level of the set: $T_1 \cap T_2$ is
31.7% of $T_1$'s volume on a $120^3$ grid. It is, however, a small omission at the level of
the *seeds*, because retrograde integration is local — a trajectory knows only its seed point
and normal. Of the BUP seeds, 0% of the min-range family, 2.7% of the max-range family and
18.9% of the off-boresight family (all at $|\phi_2| \le \beta$) fall inside $\bar T_2$ and
would be removed by the correction; the rest carry over verbatim. What the correction *adds* —
new faces of $\partial T_1'$ inherited from $\partial T_2$, which do carry a usable part — has
no counterpart in `barrier.py` at all. **[UNVERIFIED]** — quick numerical checks at one grid
resolution, 2026-09-14, not held to the §9 symbolic standard.

This is exactly the right ground truth for Layer 1's single-target reach solve (§4). The
two-target synthesis is now Layer 1's M5, done as a reach-avoid solve rather than by set algebra
(`claude/Layer1_Plan.md` §7, revised 2026-10-01); extending it to four target sets is Layer 2
(§5.5).

**What remains, and it is not small.** Layer 0 now supplies verified barrier *trajectories*
and a verified BUP. It does not supply the assembled *winning zones*: stitching the
trajectories into the closed five-subregion surface of D&S Fig. 13 needs the 25 singular
lines of their Table 3 located and Step 4's case-by-case closedness test applied. Singular
arcs (universal lines, where a costate component stays at zero and the optimal control is
intermediate rather than bang-bang) are **detected and flagged, not solved**. 32 Table 2
points remain unplaced, one of which — $f_1$ — has a defining condition that is not
recoverable from the text as printed (**open marker**, §3.5).

None of that blocks Layer 1, which needs a correct zero level set to check against and now
has one locally. Global assembly is what Layer 1's own solution would produce anyway, which
is the better order.

### 3.5 Two things found in the printed article

**Eq. (63) carries a spurious $\operatorname{sign}\phi_1$.** On $\phi_1 = \pm\beta$ the
outer normal is $(0, \operatorname{sign}\phi_1, 0)$, so the first integral forces
$\lambda_{1f} = R\operatorname{sign}\phi_1 = \sin\phi_1 + \sin\phi_2$. Eq. (63) prints
$(\sin\phi_1+\sin\phi_2)\operatorname{sign}\phi_1$. **The paper decides against itself**:
its own Eq. (64), $\dot\lambda_{2f} = -(\cos\phi_2)\operatorname{sign}\phi_1$, follows from
the derived value and not from the printed one. Seeding the integrator as printed, 110 of
220 boresight BUP seeds then contradict Eq. (65) — all at $\phi_1 = -\beta$, where the
extra sign flips the whole strategy pair. At $\phi_1 = +\beta$ nothing shows.

**$f_1$'s defining condition does not close.** The paper locates $f_1$ where
"$\tilde\lambda_{1f} = 0$", but Eq. (38) makes $\tilde\lambda_1 \equiv 0$ along the entire
$\phi_2 = 0$ corner, and the natural reading $\dot{\tilde\lambda}_{1f} = 0$ is impossible:
Eq. (42), which re-derives exactly as printed, is
$-q[\bar R_0|\sin\phi_1| + 1 + \cos\phi_1]\operatorname{sign}\phi_1$, and the bracket is
strictly positive. Open.

---

## 4. Layer 1 — 1v1 game of degree

**Status: in progress.** M1–M3 closed (2026-09-14 to 09-18: formulation verified, one-player
smoke test, converged two-player single-target solve). M4 (acceptance against Layer 0) and M5
(two-target reach-avoid partition, redefined 2026-10-01) open. This is the enabling layer and the
first new work of the semester.

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
   **The close-out added measured support for this:** correcting $\bar R_0$ by 0.026% moved
   the §9 grid's mutual-kill fraction by 1.3 points at $R_0 = 8$ and 1.7 at $R_0 = 12$, and
   sweeping $\bar R_0$ across 6.140–6.150 moves them **non-monotonically**, while $R_0 = 5$
   barely moves. The long-range heuristic statistics are not stable to three digits in a
   model parameter, so they are a weak regression baseline and a worse basis for a claim.
2. **Layer 2 needs a continuation value.** Under the recursion in §5.4, the engagement after
   one attacker is lost *is* the Layer 0/1 game. What the 2v1 problem needs from it is the
   **1v1 outcome classification** — which outcome each side can guarantee from the post-loss
   state — so Layer 1's output is a required input to Layer 2 rather than a parallel line of
   work. *(Corrected 2026-10-01: earlier text said "its value function", meaning the
   single-target margin $V$. That is not the object; the reach-avoid partition of M5 is. See
   §5.4.)*
3. **It is where the numerical method gets validated.** Whichever solver is chosen, this is
   the only layer with ground truth to check it against before it is pointed at a problem
   nobody has solved.

Solve for a value function $V(R, \phi_1, \phi_2)$ over the 1v1 game, yielding a feedback
law valid everywhere, not only on the barrier.

**DECIDED 2026-09-14: the payoff is terminal miss, solved as a level-set reachability value;
the method is an HJI grid.** Full plan in `claude/Layer1_Plan.md`. The candidates were:

- **Time-to-kill.** $V = \min_{\sigma_1}\max_{\sigma_2} t_f$ subject to termination in
  $T_{1\to2}$. Classical, but ill-posed wherever player 1 cannot win.
- **Terminal miss / margin.** A scalar measuring how deeply the terminal state penetrates
  the target set, or how far it misses. Defined everywhere, and the natural analogue of
  Hayoun & Shima's zero-effort-miss framing.
- **Capture-region-signed time.** Time-to-kill inside the winning zone, negative
  time-to-being-killed outside. **Rejected, and the stated reason for it was wrong.**

**Why signed time was rejected.** It was this document's own recommendation (§8 item 2, now
closed) and it fails this document's own acceptance criterion. On the barrier the state
reaches the boundary of the usable part *tangentially and in finite time* — Layer 0's
retrograde trajectories run to $\tau = 3$ with $R$ still bounded near 7 — so approaching from
inside the winning zone $t_{\text{kill}}$ tends to a finite **positive** value, while just
outside the payoff is $-t_{\text{death}}$, finite and negative. $V$ **jumps** across the
barrier. The barrier is $V$'s discontinuity surface; $V = 0$ is the *target set*. The claim
that it is "continuous across the barrier by construction" is false. Separately,
$t_{\text{death}}$ is undefined on the entire draw region — an open set, so not removable —
and no grid can represent a function that is $+$finite on one side of a surface and $-$finite
on the other, near precisely the surface Layer 1 exists to validate.

The barrier from Layer 0 is the zero level set of the **terminal-miss** option, which makes
Layer 0 a hard correctness test on Layer 1 rather than merely a predecessor. (Earlier drafts
of this section claimed this of "the last two options"; it holds for terminal miss and not for
signed time. Spec error, found by the §9 standard, corrected 2026-09-14.) On the barrier the
state grazes $\partial T_{1\to2}$, so the penetration depth is exactly zero; inside it
penetrates, outside it never arrives. Nothing is lost by the change: the arrival-time field
$t^*(x)$ is recovered as a derived quantity from the level-set solution, so the signed-time
picture remains available for visualization without being what the solver optimizes.
*(2026-10-01: this sentence previously also offered $t^*$ as Layer 2's continuation value. It is
not — see item 2 above and §5.4.)* **On the name:** "terminal miss" is loose. The solved quantity
is the minimum of $\ell$ over the trajectory, not miss at a fixed final time; "weapon-envelope
reachability" is the accurate description (`claude/Layer1_M1_Explainer.md`).

**Method: DECIDED — HJI grid.** Three routes were live: an HJI solve on a
$(R,\phi_1,\phi_2)$ grid; direct orthogonal collocation (Dillon et al.'s route, and the
review's standing recommendation once multiple simultaneous constraints appear); or
Yan et al.'s KKT-based convex reformulation. The HJI grid is chosen — three states is small
enough that a dense solve is cheap, and the result is a global law rather than a trajectory.
Collocation stays in reserve if the grid solve proves intractable.

**One structural fact worth having before any code is written.** With $\lambda := \nabla V$,
the Hamiltonian $\min_{\sigma_1}\max_{\sigma_2} \nabla V \cdot f$ is *character for
character* `barrier.hamiltonian_star` — the same function that served as Layer 0's
semipermeability invariant. So the optimal feedback law is immediate,
$\sigma_1^* = -\operatorname{sign}(\partial V/\partial\phi_1)$ and
$\sigma_2^* = +\operatorname{sign}(\partial V/\partial\phi_2)$ — the global version of
D&S Eqs. (21)–(22), which Layer 0 could only justify along barrier trajectories. And the
acceptance test sharpens accordingly: on the barrier, $\nabla V$ from the grid should
reproduce the Layer 0 costate $\lambda$ up to positive scaling, which tests direction rather
than merely level.

**Doomed-player behaviour (decided 2026-09-14).** Interior play needs an answer to "what does
a player do once he cannot avoid being killed," and a game of kind does not supply one. **The
assumption is that he prefers a mutual kill to dying alone** (§7). Consequences: the barrier is
untouched (it separates *can avoid* from *cannot*, which is preference-independent); inside the
winning zone both players become time-optimal toward their own target set, so the interior is a
race between arrival-time fields; and the second target set $T_{2\to1}$ therefore enters Layer 1
rather than waiting for Layer 2 — obtained free by the verified index swap, with no second
solve. **Limit on this (2026-10-01):** the ordering is an outcome ranking, not a solution
concept. It does not by itself select a policy, and the two separately time-optimal policies are
not shown to form an equilibrium. Which outcome each side can *guarantee* comes from the
reach-avoid solve (M5), not from comparing $t_1^*$ with $t_2^*$. The alternative, *maximize survival time*, is the classical choice and is recorded with a
switching procedure in `claude/Layer1_Plan.md` §11; the two differ only in which gradient field
player 2's interior law is read from.

**Acceptance:** four tests of increasing sharpness against the 122 verified Layer 0
trajectories — level ($|V| < $ grid tolerance on them), gradient ($\nabla V$ vs. the Layer 0
costate), feedback law (bang-bang controls reproduced, switches included, and no long-range
inversion), and Table 2 ($\{V=0\}$ through the 27 placed points) — plus a **negative
control**: the old pursuit heuristic must *fail* the feedback test at long range, or the
suite is not testing anything. Detail in `claude/Layer1_Plan.md` §5.

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
bandit's single control $\sigma_B$.** Nothing else is shared in the *kinematics*. This is the
mathematical statement of "the bandit has one nose."

**What ports and what does not (checked 2026-10-01; record in
`claude/Layer1_Revision_2026-10-01.md`).** An earlier version said every piece of D&S machinery
"ports to each pair unchanged." That was too broad. What was actually checked, with the barrier
Hamiltonian $H = \sum_i \lambda_i \cdot f_i$:

- **Costate equations: per pair, unchanged.** $\dot\lambda = -\partial H/\partial x$ contains no
  control, and pair $i$'s costate rates involve only pair $i$'s states and costates.
- **First integral: ports as two conserved quantities**, $I_i = (\lambda_{\phi_i}+\lambda_{\psi_i})^2/R_i^2
  + \lambda_{R_i}^2$, each conserved whatever the controls do (numerically, $|\dot I_i| \le 10^{-13}$
  over 2000 random states, costates and controls; it also follows by hand). Only one overall scale
  can be normalized; the ratio $I_1/I_2$ is set by transversality, so "$=1$" does not port.
- **Control law and semipermeability: coupled.** $\partial H/\partial\sigma_B = \lambda_{\psi_1} +
  \lambda_{\psi_2}$, so the bandit's optimal turn and the condition $H^\* = 0$ are joint across the
  pairs. Pairwise barrier trajectories are not 2v1 barrier trajectories.
- **A useful consequence.** Pair 2's costate equations are linear and homogeneous in pair 2's
  costates. A single-target barrier for $T_{A_1\to B}$ has zero pair-2 terminal costate, so pair 2's
  costate stays zero and that barrier is the 1v1 barrier extruded over pair 2's states. **All the
  genuinely 2v1 structure therefore lives in the combination of target sets** — reach one while
  avoiding another — which is exactly where M5's reach-avoid formulation sits.

So the difficulty is concentrated in one scalar control appearing in two places, as before, but
the claim that the pairwise *optimal-trajectory* machinery transfers unchanged is withdrawn.

*Layer 0's close-out makes this concrete rather than aspirational: `barrier.py` implements
that machinery for one pair, tested, so the Layer 2 implementation is two instances of a
verified object plus the coupling — not a rewrite.*

### 5.3 Four target sets, not three

$$T_{A_i \to B} = \big\{ |\phi_i| \le \beta \ \wedge\ \underline R(\psi_i) \le R_i < \bar R(\psi_i) \big\}$$
$$T_{B \to A_i} = \big\{ |\psi_i| \le \beta \ \wedge\ \underline R(\phi_i) \le R_i < \bar R(\phi_i) \big\}$$

The bandit's lethality **splits by which attacker it engages**, which is why there are four
sets and not three.

**A one-line consequence, and its limit.** $B$ can hold both attackers inside its
boresight cone only if $|\psi_1| \le \beta$ and $|\psi_2| \le \beta$ simultaneously. Since
the angular separation of the attackers as seen from $B$ is $\Delta = \psi_1 - \psi_2$,
this requires

$$|\Delta| \le 2\beta .$$

At $\beta = 45°$: **if the attackers keep their angular separation about the bandit above
90°, the bandit cannot threaten both at the same instant, regardless of range.** That is what
the inequality establishes, and only that. It does **not** show that neither attacker can be
threatened, or that the team stays safe over time: the bandit can still turn onto one attacker,
kill it, and then turn onto the other. *(Corrected 2026-10-01; earlier text promoted this to a
team-safety condition, §8.3.)* The useful version is a question, not a result: does keeping
$|\Delta| > 2\beta$ deny the bandit enough time between threats that the second attacker can
always reach $T_{A_2\to B}$ first? That is a reach-avoid statement on the six-state system, and it
is still a strong candidate for an analytic result.

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

**What the Layer 1 decision settles here, and what it does not.** §4 adopts *a doomed player
prefers a mutual kill*. That answers the question for a **single** doomed aircraft deciding
whether to trade itself — so it constrains the bandit's endgame behaviour, and it constrains
each attacker's. It does **not** answer the team question above, which is different in kind: the
team may rationally value $A_1$'s life differently from how $A_1$ values it, and a max-min team
objective can prefer outcomes no individual would choose. Treat the 1v1 assumption as an input
to the team-objective decision, not as the decision. **Still open.**

The third question has a convenient answer: **treat the post-loss engagement as the Layer 0
game.** That makes the layer stack a genuine recursion rather than a sequence of unrelated
problems — provided the continuation carries the same outcome preferences, not an unrelated
numerical margin.

**Partition semantics (added 2026-10-01).** The individual ordering
win alone ≻ draw ≻ mutual kill ≻ die alone is **not zero-sum**: both players rank a draw above
mutual kill. So "optimal play" and "the partition" are undefined until a solution concept is
chosen. This project uses **guarantees**, which are well defined whatever the opponent prefers:

- $W_1$: player 1 can guarantee winning alone (reach $T_{1\to2}\setminus T_{2\to1}$ without first
  entering $T_{2\to1}$, against any player-2 behavior). $W_2$ by the index swap.
- $D$: each player can guarantee not being killed, so the outcome is a draw under any play.
- **Contested**: everything else. Here the outcome depends on what the players actually do, and
  the preference ordering (and an equilibrium concept, if one is chosen) decides it. Results in
  this region are labeled as assumption-dependent.

Mutual kill is an *event* in the stopped game (simultaneous first entry), not a guaranteed
outcome region, unless a computation shows otherwise. The 2v1 partition uses the same three-way
split at the team level, once §5.4's team objective is fixed.

**Layer 1 → Layer 2 interface (fixed now, not after Layer 1 closes).** What Layer 2 needs from
the 1v1 layer, and therefore what Layer 1 must deliver:

1. The 1v1 sets $W_1$, $W_2$, $D$ and the contested remainder on the $(R,\phi_1,\phi_2)$ grid,
   from the reach-avoid solve (Layer 1 M5). This is the continuation after one attacker is lost.
2. A stopping rule: the 2v1 game changes mode at the first kill. Bandit killed → game over.
   One attacker killed → the state projects onto the surviving pair and continues as the 1v1 game
   with item 1 as its outcome. Simultaneous events are classified explicitly, not by tie-break.
3. Preferences that match across the levels: the 1v1 ordering above for each aircraft, and the
   team ordering of §5.4 for the team. The 1v1 sets are guarantee-based, so they hold under either.

The single-target margin $V$ and the arrival-time fields remain useful (barrier, feedback on the
barrier, visualization), but they are not the continuation value.

### 5.5 Method

Extend D&S's Appendix B synthesis rules from two target sets to four. The rules decompose a
two-target game into single-target subgames, correct for target-set overlap via
$T_i' \triangleq T_i \setminus \bar T_j$, and recombine by explicit case rules. Whether
that recipe generalizes to four sets with a shared control is unknown and is itself a
contribution if answered either way.

**Scope note (2026-10-01).** This is a research question, not a dependency the semester should
hang on. Going from two targets to four adds more than bookkeeping: a terminal event can remove
one aircraft and leave a continuation game, and the shared $\sigma_B$ means separately optimal
pair behaviors need not be jointly realizable. An exact decomposition needs a theorem, not the
"two coupled copies" picture (Chen et al., arXiv:1611.00122, treat decomposition with shared
controls under specific structural conditions). A dense six-state grid is not an option: one
float64 array is about 141 GB at $51^6$ and 8.5 TB at $101^6$. Credible December targets are
analytic results, restricted or low-dimensional slices, and a precise statement of **when
separately solved subgames compose into the shared-control game and when they do not** — a
well-defined failure of composition would itself be a result.

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

### 6.3 The observable is not yet defined (added 2026-10-01)

Under instantaneous kill on target-set entry, the game **stops at the first kill**. If $A_1$
kills $B$ at $t_{f,1}$, there is no $t_{f,2}$: the bandit is gone. So $|t_{f,1}-t_{f,2}|$ is not
a quantity the stopped model produces. It can be defined as a counterfactual (the time $A_2$
*would* have entered $T_{A_2\to B}$ under continued play), but it must be labeled as such.
Candidate observables that are well defined in the stopped game:

- whether, at the kill, the other attacker is also inside $T_{A_j\to B}$ (both attackers holding
  a shot when the first one fires);
- whether, at the kill, the bandit had a shot on either attacker (the kill was "uncontested");
- the margin of the second attacker to its own target set at the kill instant.

Layer 3 needs one of these fixed before it needs a better optimizer.

---

## 7. Assumptions, and how firmly each is held

| Assumption | Status |
|---|---|
| Planar, coplanar motion | Firm for this project. D&S, Merz & Hague and Olsder & Breakwell all take it; Merz & Hague name it as a self-criticism. |
| Constant, equal speeds | Firm at Layers 0–2. Merz & Hague's justification (barrier maneuvers are brief, usually under a quarter turn) applies. Relaxing it is future work. |
| Equal turn-rate limits | Firm at Layers 0–2, following D&S's identical-cars model. Breaking it is a natural Layer 4. |
| Identical weapons on all three aircraft | Firm at Layers 0–2. Heterogeneous envelopes are future work. |
| Fire-and-forget, instantaneous kill on target-set entry | Firm. No missile flyout, no time of flight, no $P_k < 1$. Ciletti et al. (1973) is the only source found that models finite weapon speed. **Load-bearing (2026-10-01):** it is what makes the game stop at the first kill, what makes "mutual kill" a simultaneous-first-entry event (and so plausibly measure-zero), and what makes the second impact time undefined (§6.3). Results about mutual kill and synchronization are results *about this assumption*. |
| Perfect state information, both sides | Firm. Standard for this literature. |
| Attackers cooperate fully; bandit knows this | Firm. |
| Kill is permanent and removes the aircraft | Firm, with the continuation-game convention of §5.4. |
| **A doomed player prefers a mutual kill to dying alone** (ordering: win alone ≻ draw ≻ mutual kill ≻ die alone) | Decided 2026-09-14, and **a modelling choice rather than a derived fact** — flagged as such wherever interior results are reported. Firm at Layer 1. It does not affect the barrier, the reach solve, or the mutual-kill *geometry*; it governs only interior play. The alternative (maximize survival time) is classical and tidier but models an unarmed evader, not an aircraft carrying an all-aspect missile. Cheaply reversible: `claude/Layer1_Plan.md` §11. |

---

## 8. Decisions still open

1. **§5.4 — team objective and outcome ordering.** Blocks Layer 2. *(2026-09-14: partially
   informed, not closed. The 1v1 doomed-player ordering is now decided — win alone ≻ draw ≻
   mutual kill ≻ die alone, §7 — which fixes each individual aircraft's endgame preference. The
   team's valuation of losing $A_1$ is a separate decision and remains open; see §5.4.)*
2. ~~**§4 — Layer 1 payoff and solution method.**~~ **CLOSED 2026-09-14: terminal miss
   (level-set reachability), HJI grid.** The standing recommendation of signed time-to-kill
   was rejected — it fails this document's own acceptance criterion, see §4. Plan in
   `claude/Layer1_Plan.md`.
3. **Whether the $2\beta$ separation result (§5.3) is a strategy or a consequence.** With
   synchronization deferred, this is promoted to the **leading candidate for the semester's
   headline analytic result**. *(Rescoped 2026-10-01.)* If the team can *guarantee* maintaining
   $|\Delta| > 2\beta$ from a given initial state, that guarantees the bandit never threatens both
   attackers **at once** — a barrier in its own right. It is **not** by itself a sufficient
   condition for team safety, because sequential kills remain possible. The safety question is
   whether separation plus geometry lets the unthreatened attacker reach $T_{A_j\to B}$ before
   the bandit can complete a kill and re-aim; that is a reach-avoid question. Worth
   attacking early rather than waiting for week 7. *(The Layer 0 machinery it needs now
   exists and is tested — `barrier.py`'s usable-part and max-min primitives apply directly
   to the $\psi_i$ target sets.)*
4. **Bandit's information about which attacker is "primary."** Not yet modelled at all.
5. **Does the D&S mutual-kill collapse survive into 2v1?** D&S found mutual kill reduces to
   measure-zero surfaces at their parameters, but noted this is parameter-dependent. With
   four target sets and a shared control the question reopens, and it is answerable at
   Layer 2 without a game of degree.
6. **How far to push Layer 0's surface assembly.** §3.4 leaves the winning-zone assembly and
   the Table 3 singular lines undone, deliberately. Revisit once Layer 1 has a value
   function, which produces the same object globally and more cheaply. *(2026-09-14: this
   reasoning extends to the Appendix B target-set correction as well. That correction exists
   because a game of kind has no clock — it infers priority from set overlap. Layer 1 supplies
   a clock, so the partition becomes a comparison of arrival times. Falsifiable prediction:
   mutual kill as $\{t_1^* = t_2^*\}$ is generically codimension-1 and should sit on
   $|\phi_1| = |\phi_2|$, which is exactly D&S Eq. (87). `claude/Layer1_Plan.md` §7 makes
   this milestone M5.)* *(2026-10-01: withdrawn as stated. Comparing $t_1^*$ with $t_2^*$ does
   not establish event order, because each is a guarantee against a different opponent behavior.
   The partition is obtained instead from a reach-avoid solve, which is the rigorous form of the
   Appendix B correction; M5 is redefined accordingly. The symmetry fact
   $\{t_1^*=t_2^*\} \supseteq \{|\phi_1|=|\phi_2|\}$ still holds but is no longer read as the
   mutual-kill set.)*
7. **Solution concept for the contested region (added 2026-10-01).** Guarantees define $W_1$,
   $W_2$ and $D$ (§5.4). In the remainder the outcome depends on play, and the non-zero-sum
   ordering means a choice is needed: report guarantees only, or adopt an equilibrium concept.
   Default: guarantees only, with contested-region behavior reported as assumption-dependent.
8. **Layer 3's observable (added 2026-10-01).** §6.3. Must be fixed before any synchronization
   claim.

---

## 9. Verification standard

Carried over from the literature-review process, which has been working:

- Every equation that will be used is **re-derived and checked symbolically** before being
  relied on, not transcribed. Where a symbolic residual fails to collapse, confirm
  numerically before recording a discrepancy.
- **Test the lemmas away from the published figures**, not only the equations. An over-
  general lemma does not announce itself the way a typo does (Hayoun & Shima, Lemma 4.2).
- **A parameter quoted to three significant figures can often be pinned exactly from a table
  of significant points** — check before adopting the quotation. D&S's $\bar R_0$ is
  quoted as 6.14 and is $3+\pi$; the difference is decidable from four Table 2 entries and
  it propagated into the codebase for weeks (§3.2).
- **Carry an invariant the integrator cannot satisfy by accident.** Layer 0's first integral
  (Eq. 23) is conserved by the costate equations *whatever the control does* — the controls
  cancel identically — so it cannot detect a wrong control law. The semipermeability
  condition $H^\* = 0$ (Eq. 15) can, and did: it is what exposed both the stage-wise control
  re-evaluation and the un-located switches, while the first integral sat at $10^{-14}$
  throughout. **Prefer an invariant that the thing you might get wrong actually violates.**
- Anything not verified is marked **[UNVERIFIED]** inline, with a statement of what would
  settle it.
- **A guarantee computed against one opponent behavior is not a prediction under another**
  (added 2026-10-01). Two worst-case quantities computed in different games cannot be compared to
  decide what happens under a common strategy pair. The arrival-time comparison of Layer 1 §2.3
  failed this, and nobody caught it until an outside review. When a claim combines objects from
  different games, say which game each comes from.
- Every numerical layer has an **acceptance test** against a known quantity — Layer 0
  against the D&S figures and Table 2 values (done: 27 of 59 points placed, 6 solved to
  $5\times10^{-4}$), Layer 1 against the Layer 0 barrier, Layer 2 against Layer 0 in the
  degenerate limit $R_2 \to \infty$.
- The $R_2 \to \infty$ check is worth stating explicitly: **Layer 2 must reduce exactly to
  Layer 0** when the second attacker is removed to infinity. That is a free, strong
  regression test on the six-state implementation.

---

## 10. Schedule to December

| Weeks | Work | Output |
|---|---|---|
| 1–2 | Close Layer 0: barrier reconstruction from costate ODEs; validate against D&S figures. In parallel, attack the $2\beta$ separation result (§8.3) — it needs only Layer 0 machinery | **Barrier reconstruction done 2026-09-11** — verified trajectories, BUP, Table 2 acceptance, figures. $2\beta$ result not yet attempted |
| 3–6 | Layer 1: pick payoff, solve the 1v1 game of degree, verify zero level set against Layer 0 | Global feedback law; validated numerical method. **As of 2026-10-01:** M1–M3 done; M4 acceptance and M5 reach-avoid partition (redefined) remain |
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
Layer 0's close-out record is `claude/Layer0_CloseOut_2026-09-11.md`; the retrograde method it
uses is explained with worked numbers in `claude/Layer0_StudyGuide.md`. Layer 1's plan of
record is `claude/Layer1_Plan.md`.
