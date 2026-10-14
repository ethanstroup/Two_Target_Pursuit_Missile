# Olsder & Breakwell, 1974 — Role Determination in an Aerial Dogfight

> **Provenance (2026-09-08).** Drafted from a **local PDF** supplied by Ethan in the project
> (`G J Olsder and J V Breakwell Role Determination in an Aerial Dogfight 1974.pdf`). This is the
> **paper itself** — the *International Journal of Game Theory* article, complete with
> Tables 1–2, Figs. 1–7 and the five-item reference list.
> **Caveat on the read:** it is an old typeset scan reaching the reader as extracted text, and the
> degradation is severe — subscripts, Greek letters, minus signs and overdots are lost throughout, and
> Tables 1 and 2 are shredded past reconstruction. **Running prose survived well**, so the modelling,
> the case taxonomy and the results below are read directly. The equations of Sec. 2 were
> **re-derived and checked in sympy**, and six of them are confirmed exactly, including one whose
> printed sign is wrong in the extraction and which was settled by cross-referencing the paper's own
> Case 5 substitution. Table 1/Table 2 entries are described, not transcribed.
>
> **Addendum (2026-09-10, guided session with Ethan).** A follow-up read of the same PDF through
> direct page-image inspection (rather than the degraded text-extraction pipeline above) found the
> scan itself is clean and fully legible — the earlier degradation was a property of the extraction
> step, not the source. Three of the four `[UNVERIFIED]` markers below are resolved on this basis:
> Eq. (2.8)'s sign, the closing empirical turn rule (p. 64), and Fig. 5's $\theta$ label. Tables 1,
> 2a and 2b are also legible in this rendering and could be transcribed if a future need arises;
> they remain untranscribed here since nothing downstream currently depends on their entries.

## Citation
Olsder, G. J., and Breakwell, J. V., "Role Determination in an Aerial Dogfight," *International Journal of Game Theory*, Vol. 3, No. 1, 1974, pp. 47–66. Physica-Verlag, Vienna. DOI 10.1007/BF01766218. Received November 1973. Both authors, Department of Aeronautics and Astronautics, Stanford University, Stanford, CA 94305; Olsder supported by the Netherlands Organization for the Advancement of Pure Research (Contract No. S. 61-25) and noted as "now at Twente University of Technology, Enschede."

*(The received date of November 1973 is consistent with the 1974 volume year.)*

## Problem Framing
- **Game type:** Pure **game of kind** — and the paper says so in the strongest terms available. Sec. 1 splits the dogfight problem into (1) *given the initial conditions, determine the roles: who pursues whom?* and (2) *given the roles, what are the time-optimal strategies?*, then states: "We will be concerned only with the first question, **which is certainly the more important one**." The output is a partition of the state space by barrier ("semi-permeable") surfaces, plus optimal play defined only *in the immediate neighborhood of* those surfaces.
- **Agent structure:** 1v1, **two-target with genuine bidirectional lethality**. Each aircraft carries its own lethal zone; a combatant wins when his opponent has been maneuvered into a relative position inside his own lethal range and in the direction of his velocity. Roles are an output.
- **Both aircraft are turn-rate limited, and deliberately asymmetric in three ways at once.** Sec. 2 assumes $v_1>v_2>0$, $0<\omega_1<\omega_2$, and $0<l_1<l_2$: player 1 is **faster**, **less maneuverable**, and carries the **shorter** lethal range. All three asymmetries are load-bearing — in particular the third is what creates the escape region.
- **Three outcome regions, not two.** $\mathscr{R}_1$ (victory for player 1) and $\mathscr{R}_2$ (victory for player 2), plus — *because the faster combatant has the smaller lethal range* — an outer **"no contest" region $\mathscr{E}$ from which player 1 can guarantee escape but cannot guarantee victory**. $\mathscr{R}_1$ is bounded by part of the terminal set $T_1$ together with a semi-permeable surface $\Sigma$; the complement of $\mathscr{R}_1$ is split by a **second** semi-permeable surface $\Sigma'$ into $\mathscr{R}_2$ and $\mathscr{E}$ (Figs. 1a–1c).
- **Kill geometry: a line segment, i.e. range-bounded with zero angular width.** Aircraft $i$ has a lethal range consisting of a line segment of length $l_i$ along its own velocity vector. In the reduced frame the terminal set is literally a segment of the $y$-axis — the paper confirms this when describing Fig. 5, noting that the section of $T_1$ "is just the $y$-axis between 0 and +2" at $l_1=2$. There is **no squint angle and no terminal heading requirement**: the condition is purely on the opponent's relative *position*, and the victim's own heading is unconstrained at termination.
- **Dimensionality:** 3 states. $(x,y)$ is player 2's position in a frame centred on player 1 with the $y$-axis along player 1's velocity and $x$ to his right; $\theta$ is the angle measured clockwise from player 1's velocity vector to player 2's.
- **A stalemate is assumed impossible** — this assumption is what licenses the claim that $T_2$ is reached in finite time inside $\mathscr{R}_2$, and hence that the partition is exhaustive.

## Core Contribution
**1. An explicit, computed three-way role-determination partition for a fully asymmetric turn-limited dogfight,** where prior work had only described such a division qualitatively (the paper attributes the qualitative version to Baron, Ho & Kleinman, 1970) or partially, via reachable sets (Ciletti, Meier & Salmon, 1973). A computer program divides the 3-D state space into victory-by-1, victory-by-2, and escape regions.

**2. A complete taxonomy of the terminal situations that generate the barrier — and simultaneous kill is a large part of it.** The separating surface is not one smooth sheet but a patchwork, each piece grown backwards from its own *local* differential game:
- **Seven types of simultaneous kill** (Fig. 3, Table 1), including collision, plus their left–right reflections $1'$–$7'$. Cases 1–4 are one-turn maneuvers; case 3 is the collision case; cases 5–7 involve an **S-maneuver by player 1** to get inside the longer-ranged player 2's reach before player 2 can face him, with cases 6 and 7 adding a **straight-line singular arc** in the middle.
- **Ten types of near miss** (Fig. 4, Table 2), of two structurally different kinds: (i) the state-space path is tangent to $T_1$ or $T_2$ without crossing; (ii) **player 2 crosses player 1's lethal segment at its extremity and survives because his angular velocity about player 1 exceeds player 1's maximum turn rate** — a purely kinematic escape that "only arises if player 1's lethal range is sufficiently short."
- $\Sigma'$, the escape/victory-by-2 boundary, is built **only** from near-miss pieces in which player 1 either crosses $T_2$ at its extremity or is tangent to it without crossing. Simultaneous kill never appears on $\Sigma'$.

**3. Two named singular arcs, each pinned down by an argument rather than assumed.** From Eqs. (2.5) and (2.7), the *only* possible singular arc for player 2 (one on which $V_\theta$ stays zero) is straight-line motion $u_2=0$; symmetrically, from (2.4), (2.9) and (2.3), the only possible singular arc for player 1 is straight-line motion $u_1=0$. These appear in the final figures as the dashed loci $s_1$ and $s_2$ in the $x$–$\theta$ projection of $\Sigma$ (Figs. 7a, 7b).

**4. Dispersal lines whose tie-break belongs to a specific player.** The corners of the $\theta$-sections correspond to edges on $\Sigma$, of two types: edges that are *followed* in optimal play, and **dispersal lines** from which optimal paths depart in two different directions — with the paper noting that "the choice lying with player 2, who has the larger turn-rate." The legitimacy of joining the individual semi-permeable pieces into a composite surface is checked against **Bernhard's (1971) corner conditions** (paths must not approach an edge from either side, or must do so tangentially or with a switch on arrival), and the junctions of pieces 5–6, 6–7, a–b, b–c and c–d are reported smooth with continuous adjoint vector.

**5. A worked numerical case:** $v_1=\omega_1=1$, $v_2=3/4$, $\omega_2=3$, $l_1=2$, $l_2=\infty$. So the speed ratio is $3/4$, the turn-rate ratio $\omega_1/\omega_2=1/3$, and player 1's lethal range is twice his own minimum turning radius ($v_1/\omega_1=1$). **Taking $l_2=\infty$ deliberately eliminates $\Sigma'$** — with player 2's reach unbounded there is nowhere to escape to — so the example exercises only the $\Sigma$ construction. At these parameters cases e–h do not arise, and the player-interchanged near-miss cases occur only at infinite separation (they belong to $\Sigma'$), leaving cases 1–7, a–d and reflections; the paper further reports that some of those turn out to be unnecessary to $\Sigma$. Sections are computed for enough values of $\theta$ (Figs. 6-1 … 6-5) that "the region $\mathscr{R}_1$ and its boundary are clearly discernible" — the paper is explicit that this is a sufficient-sampling argument, **not** a proof that $\mathscr{R}_1$ is closed.

**6. An honest negative observation about a spurious region.** In one section the authors find a region outside $\mathscr{R}_1$ whose boundary player 1 can prevent the state from crossing outward — a candidate second invariant region. They then report that sections at larger $\theta$ show it contains part of $T_2$, so "the existence of this particular region, if it turns out to be closed, is thus of no significance." Worth noting as an instance of a barrier-like object that survives a single-section test and fails a global one.

## Method
**Equations of motion (2.1),** in the reduced frame, with $u_i$ the normalized turn rates $|u_i|\le1$ and the stated real-space convention $u_i=0$ straight, $u_i=+1$ full right turn, $u_i=-1$ full left turn:

$$\dot x = -\omega_1u_1y + v_2\sin\theta,\qquad \dot y = \omega_1u_1x - v_1 + v_2\cos\theta,\qquad \dot\theta = -\omega_1u_1 + \omega_2u_2$$

**Main Equation (2.2),** with the sign convention that the local game has value $V$ positive or negative according to whether it ends in favour of player 2 or player 1:

$$\max_{u_2}\ \min_{u_1}\ \big(V_x\dot x + V_y\dot y + V_\theta\dot\theta\big) = 0$$

which implies the semi-permeability of the surface $V=0$ made up of paths leading to simultaneous kill or to near miss.

**Adjoint equations (2.3) and switch functions (2.4)–(2.5).** *Verified in sympy against $-\partial H/\partial\mathbf{x}$, residual exactly zero on all three components:*

$$\dot V_x = -\omega_1u_1V_y,\qquad \dot V_y = \omega_1u_1V_x,\qquad \dot V_\theta = v_2\big(V_y\sin\theta - V_x\cos\theta\big)$$

The coefficient of $u_1$ in the Hamiltonian is exactly $-\omega_1\Delta$ with $\Delta \triangleq yV_x - xV_y + V_\theta$ (residual zero), and player 1 minimizes, giving $u_1=\operatorname{sgn}\Delta$; the coefficient of $u_2$ is $\omega_2V_\theta$ and player 2 maximizes, giving $u_2=\operatorname{sgn}V_\theta$. Both match Eqs. (2.4) and (2.5) as printed.

**Retrograde integration.** With $\tau$ measured backwards from the terminal time and $u_1$ held constant, Eq. (2.6) normalizes the terminal in-plane adjoint to unit length ($\cos\varphi=V_{x_f}$, $\sin\varphi=V_{y_f}$) and rotates it:

$$V_x = \cos(\varphi-\omega_1u_1\tau),\qquad V_y = \sin(\varphi-\omega_1u_1\tau)$$

*Verified:* this satisfies the two in-plane adjoint ODEs identically. Substituting it, together with $\theta(\tau)=\theta_f+(\omega_1u_1-\omega_2u_2)\tau$, reproduces Eq. (2.7) exactly, **including its second form**, which is the useful one:

$$\dot V_\theta = -v_2\cos(\theta+\varphi-\omega_1u_1\tau) = -v_2\cos(\theta_f+\varphi-\omega_2u_2\tau)$$

*(residual zero — note this collapses the $\omega_1u_1$ dependence, which is why $V_\theta$ can be integrated in closed form knowing only player 2's control.)* And $\dot\Delta = -v_1V_x$ (Eq. 2.9) was verified to residual zero by differentiating $\Delta$ along the dynamics — every $\omega_1u_1$ term cancels, which is the reason player 1's switch function has such a simple history.

**Eq. (2.8).** Integrating the confirmed Eq. (2.7) in retrograde time gives, for $u_2\neq0$:

$$V_\theta(\tau) = V_{\theta_f} - \frac{v_2}{\omega_2u_2}\Big[\sin(\theta_f+\varphi-\omega_2u_2\tau) - \sin(\theta_f+\varphi)\Big]$$

*(verified 2026-09-10, direct page-image read)* — this bracket was originally flagged [UNVERIFIED] because the 2026-09-08 text-extraction pipeline dropped the sign and showed a plus instead. A follow-up guided session read the original page image directly and confirmed the printed relation carries a **minus**, exactly as the Case 5 cross-check already implied: substituting $\theta_f=\pi$, $u_2=1$ into the minus form reproduces the paper's own Case 5 substitution ($V_{\theta_f}+\frac{v_2}{\omega_2}[\sin(\varphi-\alpha)-\sin\varphi]$, $\alpha=\omega_2\tau$) with symbolic residual zero, and 2000/2000 random numerical draws agreed with the minus form against 0/2000 for the plus form. Marker closed.

**Backward construction procedure.** For each local game the terminal state $(x_f,y_f,\theta_f)$ and terminal adjoint $(V_{x_f},V_{y_f},V_{\theta_f})$ are given in terms of a **single parameter with a bounded range** (Tables 1 and 2). Paths are integrated backwards only while the switch functions $\Delta$ and $V_\theta$ retain the signs matching the maneuver that defines that case, which is what bounds each piece; where the switch functions never change sign, an obvious bound is imposed instead — e.g. $\omega_2\tau<2\pi$, "since player 2 would never find it advantageous to describe a complete turn." Each local game therefore yields a *finite* patch, and the paper is explicit that "not all the pieces form part of $\Sigma$, and sometimes only a part of a piece forms part of $\Sigma$." Assembly is done by computing sections in planes $\theta=$ constant.

The terminal adjoint signs are argued **physically rather than by transversality algebra** — for case 1, for example, "a small displacement of player 2 to the right is in his favor, from which $V_{x_f}>0$" — with the Main Equation then supplying the remaining relation among $V_{x_f}$, $V_{y_f}$ and $V_{\theta_f}$. (Worked concretely for Case 1 in the 2026-09-10 guided session: with $V_{y_f}=0$ and $V_{x_f}=1$ fixed by normalization and the terminal state derivatives from (2.1), the Main Equation gives $V_{\theta_f}=-\omega_1y_f/(\omega_1+\omega_2)$ directly — reproducing Table 1's printed sign as a derived quantity rather than an independent guess, and correctly predicting $V_{\theta_f}\to0$ at $y_f=0$, matching the paper's own note that Case 3 with $\theta_f=\pi$ coincides with Case 1 at $y_f=0$.)

[UNVERIFIED: **Tables 1 and 2 are not transcribed.** They carry, per case, the terminal state, the terminal adjoint signs, the defining parameter with its bounds, and both controls (including control *sequences* such as $-1\to0\to+1$ for the singular-arc cases). The 2026-09-08 extraction reduced both tables to unaligned fragments; a 2026-09-10 direct page-image read found both tables fully legible, so this marker is a matter of transcription effort rather than recoverability — flagged as not yet done rather than not doable. The case-by-case prose in Secs. 3 and 4 is intact and is what the descriptions above rest on.]

## Key Terminology Introduced
- **Role determination** — the paper's framing of the game of kind: who pursues whom is the question, and the time-optimal problem is explicitly deferred.
- **"No contest" region $\mathscr{E}$** — escape by the faster combatant; exists only when the faster combatant has the smaller lethal range.
- **Separating surfaces $\Sigma$ and $\Sigma'$** — the inner barrier bounding victory-by-player-1 and the outer barrier separating escape from victory-by-player-2.
- **Local differential game** — the device of attaching a small terminal-payoff game to each terminal configuration and growing one patch of barrier from it.
- **Simultaneous-kill maneuvers** (7 types) vs. **near-miss maneuvers** (10 types), the latter split into tangency and angular-overtake kinds.
- **S-maneuver** — player 1's reverse-then-turn maneuver (cases 5–7) to reach the longer-ranged opponent.
- **Dispersal lines** — edges of $\Sigma$ from which optimal paths depart in two directions, here with the tie-break belonging to the higher-turn-rate player.
- **Corner (edge-joining) conditions** — Bernhard's criteria for when two semi-permeable surfaces may be joined into a composite one.
- Switch functions $\Delta = yV_x - xV_y + V_\theta$ (player 1) and $V_\theta$ (player 2).

## Limitations / Open Questions
- **The identical-combatant case is explicitly excluded.** Sec. 1 states that "a first attempt at the division of state-space in this model was made in an **unpublished paper by A. W. Merz**, restricted, however, to the case of **identical combatants**, which will be excluded in this paper." So the symmetric version of *this* formulation existed in 1973 but only in unpublished form, and this paper is not it. Recorded as a lead.
- **The partition is established numerically and by sampling.** The authors say plainly that demonstrating a region $\mathscr{R}_1$ entirely enclosed by $T_1$ and a composite semi-permeable surface "requires, of course, the construction of the sections for all values of $\theta$," and that they instead computed enough sections for the region and its boundary to be "clearly discernible." No closure proof.
- **Optimal play is defined only near the separating surface.** The abstract says so directly. There is no value function, no time-to-capture, and no feedback law valid in the interior of any region — consistent with the game-of-degree question being deferred in Sec. 1.
- **No stalemate is assumed possible**, which is what makes the three regions exhaustive; the assumption is not justified within the paper.
- **The lethal zone has zero angular width.** Capture requires the opponent to lie on a segment of the velocity ray, so the target set is measure-zero in the plane. The model is range-bounded but carries no squint angle, no aspect dependence, and no terminal heading condition.
- The worked example sets $l_2=\infty$, which switches off $\Sigma'$ entirely — so the **escape region, arguably the paper's most distinctive structural feature, is never exhibited numerically.** Its construction is described in Sec. 4 but not drawn.
- **Resolved 2026-09-10, direct page-image read.** Sec. 5's closing rule reads exactly $u_1=-\operatorname{sgn}\dot x$, $u_2=+\operatorname{sgn}\dot\theta$ (p. 64) — the two aircraft always turn oppositely with respect to their own state-rate signs, not a shared quantity as originally guessed from the degraded scan. A compact feedback heuristic in the same spirit as Merz & Hague's "turn hard toward your opponent" rule, though stated here in terms of instantaneous kinematics rather than bearing angle.
- **Resolved 2026-09-10.** Fig. 5's $\theta$ label is confirmed as $\theta=\pi/3$, matching the body text's own statement ("the section corresponding to $\theta=\pi/3$ is shown in Fig. 5").

## Connections to Prior Literature

**Merz & Hague (1977) is the closest structural neighbor in the reviewed set — same stated problem, near-opposite kill geometry.** Both are 1v1, bidirectionally lethal, turn-rate-limited-on-both-sides games of kind with role determination as the explicit output (not an input), and both build the barrier from backward-integrated local games rather than one global BUP sweep. But the two papers make opposite choices about what "lethal" means geometrically: Merz & Hague's kill condition is purely angular with unbounded range; this paper's is purely positional (a range-bounded segment with zero angular width). Together they bracket the design space your own aspect-dependent, range-bounded WEZ sits inside — a useful pair of extremes, not a direct source of transferable geometry.

**A fourth independent route to "mutual kill is codimension-one, not an open region."** The seven simultaneous-kill maneuver types (Sec. 3) are literally the pieces used to construct the separating surface $\Sigma$ itself — simultaneous kill occurs exactly on the barrier, a 2D surface in this 3D state space, not over an open volume. That is structurally the same finding as D&S's Rule III set-algebra collapse, Merz & Hague's role-reversal surface, and Getz & Pachter's (JGC) draw-on-the-$T_1$-barrier result — but reached by a fourth, independent route: here it falls directly out of the *construction procedure* (simultaneous-kill cases are ingredients of $\Sigma$, not a separately computed intersection) rather than from set algebra, geometric barrier structure, or a win-condition definition. Bears directly on ProblemStatement §8.5.

**Davidovitz & Shinar (1989) — same Isaacs costate/transversality machinery, organized differently.** Both use $\lambda=\nabla V$ and the Main Equation to grow semipermeable surfaces backward from terminal conditions. D&S grows one barrier from the usable part of two continuous target-set boundaries and combines via Appendix B's explicit case rules; this paper instead grows 17 separate patches from 17 discrete terminal-*configuration* types (not points along a target boundary) and assembles them by inspection in Sec. 5. Worth remembering as a second, structurally different template if D&S's Appendix B recipe doesn't generalize cleanly from two target sets to four (§5.5) — a target-set structure that doesn't decompose into one clean continuum is closer to what this paper solves than to what D&S solves.

**Getz & Pachter (1981, JGC) — the structurally closer of the two G&P papers** (both players turn-limited, unlike the JOTA paper's homicidal-chauffeur asymmetry), already cross-checked in this note's Citation block via its worked-example numbers. Kill geometry differs sharply — G&P's targets are angle-and-range (squint sector / all-aspect disk); this paper's is pure range, zero angular width — another data point alongside the Merz & Hague contrast above.

**Merz & Hague's own speculative bounded-both-sides case (index Active thread 5) is partly the shape of what this paper's framework already allows but doesn't draw.** Sec. 4's near-miss cases e–h and $\bar\imath,\bar\jmath$ are exactly the finite-$l_2$ branch of the construction, but the worked numerical example sets $l_2=\infty$ specifically to switch that branch off — a near-miss on Merz & Hague's open case, not a hit.

## Relevance to My Research

Low-priority machinery, honestly — the kill geometry (zero angular width, pure range) is the wrong shape for your aspect-dependent WEZ, and the paper never reaches a game of degree. What's worth keeping: the **per-terminal-configuration "local differential game" construction** as a fallback technique if D&S's Appendix B synthesis rules don't generalize cleanly from two target sets to four (§5.5) — when a barrier doesn't sweep from one clean target-boundary continuum, growing it from a menu of discrete terminal configurations instead is a proven alternative. And it's now a fourth independent data point that mutual kill collapses to a measure-zero surface rather than an open region, strengthening the case that this is a structural fact about bidirectionally-lethal two-target games generally, not an artifact of any one paper's parameters — directly relevant to whether the same collapse should be expected at Layer 2.

---

## Verification Record

No separately numbered markers beyond those tagged inline above. Summary of this session's changes:

- **Eq. (2.8) sign** — closed (was [UNVERIFIED]). Confirmed minus via direct page-image read, corroborating the prior Case-5-substitution argument.
- **Closing empirical turn rule (p. 64)** — closed. $u_1=-\operatorname{sgn}\dot x$, $u_2=+\operatorname{sgn}\dot\theta$.
- **Fig. 5 $\theta$ label** — closed. Confirmed $\theta=\pi/3$.
- **Tables 1, 2a, 2b** — still untranscribed, but downgraded from "not recoverable" to "legible, not yet transcribed" — a 2026-09-10 direct page-image read found both tables fully readable. Revisit if a future need (e.g. reconstructing a specific case's exact parameter bounds) makes the transcription worth doing.
- **Case 1's terminal adjoint** — the Main-Equation derivation of $V_{\theta_f}=-\omega_1y_f/(\omega_1+\omega_2)$ was worked live in the 2026-09-10 session (see Method) and is a clean instance of the general "physical sign argument + ME algebraic relation" recipe described in Sec. 2; not previously in the note.
