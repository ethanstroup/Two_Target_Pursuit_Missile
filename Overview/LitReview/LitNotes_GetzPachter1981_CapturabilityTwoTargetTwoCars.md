# Getz & Pachter, 1981 — Capturability in a Two-Target "Game of Two Cars"

> **Provenance (drafted 2026-09-08, completed 2026-09-10).** The paper itself. Its PDF
> *text layer* is badly degraded, so equations were re-derived in sympy rather than transcribed; on
> 2026-09-10 the **pages were read as images**, which are fully legible, settling four of six markers
> and exposing a printed error in Eq. (10).
>
> **Different paper from `LitNotes_GetzPachter1981_TwoTargetPursuitEvasion.md`** — same authors and
> year, different journal. That note covers *JOTA* 34(3), cited here as Ref. 7 and identified as the
> **homicidal-chauffeur ($R_2=0$) version** of this problem.

## Citation
Getz, W. M., and Pachter, M., "Capturability in a Two-Target 'Game of Two Cars'," *Journal of Guidance and Control*, Vol. 4, No. 1, Jan.–Feb. 1981, pp. 15–21. DOI 10.2514/3.19715 (AIAA 81-4002). NRIMS/CSIR, Pretoria. Received 26 Sept. 1979; revised 12 May 1980.

## Problem Framing
- **Game type:** pure **game of kind**. Barriers built from each target's BUP by geometric/invariance arguments; the authors state explicitly that they do *not* use Isaacs' value-function route. Game of degree deferred.
- **Agents / lethality:** 1v1, no cooperation, genuinely **bidirectional** — each player carries his own capture set, so roles are an *output* of the partition.
- **Dynamics:** both turn-rate limited. $\gamma=w_2/w_1=1/2$, $\beta=w_1R_2/(w_2R_1)=1$, hence $R_2/R_1=1/2$ and **equal maximum turn rates** — asymmetric in speed and radius, symmetric in turn rate.
- **Kill geometry:** $T_1$ a **sector of a disk** ($r_1=1$, $\alpha_1=30°$); $T_2$ a **full disk** ($r_2=1$) — "player 2 has a swivelling gun," all-aspect. Both range-bounded, no terminal heading requirement, of positive area, and **$\theta$-independent cylinders** in the reduced space *(verified, sympy)*.
- **Dimensionality:** 3 states $(x,y,\theta)$, origin on player 1, $y$ along his velocity.
- **Win definition (Sec. II):** capture in a target's *interior* is immediate; on its *boundary* only if the opponent stays a nonzero period — grazing is not fatal.

## Core Contribution
1. **The $T_1$ barrier is open** ⇒ player 1 has full state-space capturability. Its boundary condition is **imposed by $T_2$**, not natural, so it is explicitly *not* a one-target-game solution.
2. **The $T_2$ barrier is closed** ⇒ player 2 captures only inside the enclosed region. Since $T_2$ is circular and player 2 is *slower*, this answers **Isaacs' research problem** (Ref. 1, p. 244) on pursuit by a slower pursuer — enabled by a modelling choice, **axes fixed on the faster player rather than the pursuer**.
3. **The partition (Sec. VI).** Interiors bounded in cross-section by $A_1B$, $BA_2$, $A_2A_1$ → player 2 wins; everything exterior, excluding $T_2$ and the barriers → player 1; the $A_1B$ segments → **draw, defined here as "a simultaneous win for both players"**, except the small region $PBQP$ (a player-1 win, by Eq. (6)); the $A_2B$ segments → player 2 `[UNVERIFIED 1]`. **Mutual kill therefore lives *on* a barrier surface, not in an open region.**
4. **Against the $R_2=0$ version (Fig. 6):** infinite maneuverability for player 2 enlarges both his capturability region and the swerve region — the two-car case is tighter on both counts.

## Method
Reduced dynamics *(verified, sympy — residual 0 against Eqs. (8), (10)–(12))*:
$$\dot x=-yu_1+\gamma\sin\theta,\quad \dot y=xu_1-1+\gamma\cos\theta,\quad \dot\theta=-u_1+\tfrac{1}{\beta}u_2,\quad |u_i|\le1 .$$
A barrier satisfies **Eq. (7)**, $\max_{u_i}\min_{u_j}\langle n,f\rangle=0$; with $n=(-y_x,1,-y_\theta)$ this is the PDE Eq. (8), with bang-bang controls **Eq. (9)**, $u_1=\operatorname{sign}(x+yy_x+y_\theta)$ and $u_2=\operatorname{sign}(y_\theta)$.

Since $|u_i|=1$ the candidate pairs are $u_1=\pm u_2$, with $u_2=0$ generating the **universal curve** between them. Under fixed controls the dynamics are linear and integrate in closed form (Eqs. 10–12, all confirmed by back-substitution **bar one printed sign in Eq. 10**). Sheets are grown from each BUP with extreme controls, patched with a universal curve at the join, and terminated where Eq. (9)'s right-hand sides vanish; the barrier being $2\pi$-periodic in $\theta$, the **dispersal curve is its self-intersection with its own $2\pi$-translate**. The route yields the partition without ever solving for $V$ — at the cost of no interior strategy, the trade the project already knows from D&S.

## Key Terminology Introduced
- **All-aspect range / swivelling gun** vs. **half-squint-angle $\alpha$** — the disk and the sector.
- **Natural vs. imposed BUP boundary condition** — cut off by one's own geometry, or the opponent's.
- **Open vs. closed barrier** — closed ⇒ capture confined; open ⇒ full state-space capturability.
- **Universal curve** ($u_2=0$) as a patch between sheets; **swerve maneuver** — turn *away*, then reverse.
- **Draw** — a *simultaneous win for both players*, i.e. mutual kill.

## Connections to Prior Literature
- **Sequel to `LitNotes_GetzPachter1981_TwoTargetPursuitEvasion.md`** (its Ref. 7): the two 1981 papers are the $R_2=0$ and $R_2>0$ halves of one programme, and Fig. 6 here *is* that paper's result. Both run on Pachter & Getz (1980, *OCAM*) — the machinery paper behind both.
- **Agrees with D&S (1989) and Merz & Hague (1977) by a third independent route: mutual kill is codimension-one.** D&S reach it by Rule III set algebra, Merz & Hague geometrically, G&P by locating draws *on* the $T_1$ barrier — three formulations, three parameter regimes, one answer.
- **Same object under a different name as D&S's transversality condition.** G&P's $\max\min\langle n,f\rangle=0$ acts directly on the surface normal; D&S seed costates by $\lambda_f=n_i$ and integrate backward. G&P's form is more portable — it never commits to a costate ODE.
- **Conflicts with D&S on terminal-manifold structure.** D&S's target sets are aspect-dependent and twist with the state; G&P's are $\theta$-independent cylinders — an easy terminal manifold paid for with asymmetric dynamics. Layer 2 inherits D&S's harder choice, so **the barrier machinery transfers but the target algebra does not.**
- **Builds on Olsder & Breakwell (1974)** (Ref. 4) — both two-target, both-sides-turn-limited, asymmetric, differing in kill geometry (zero-width segment there, positive area here). G&P's secondhand reports of O&B's five example parameters and Merz & Hague's three (Ref. 5) were confirmed against those articles on 2026-09-08.
- **No contact with the cooperative-team papers**, all one-sided lethality. **The gap is unchanged:** another 1v1 on the bidirectional side.

## Limitations / Open Questions
- **One parameter set**, no sweep, **results delivered as labelled figures** rather than closed-form boundaries; **game of degree unsolved**, so the swerve's switching surface has no form; Eq. (7) is only *necessary* but used as if sufficient.
- **Two printed errors**, confirmed against the page images rather than scan artifacts: the $\sin\theta_0$ in Eq. (10)'s $y$-component, and the sentence introducing Eq. (6) naming $T_2$ where the equation is unambiguously $T_1$'s. The first is load-bearing for coding the barrier — see below.
- `[UNVERIFIED 1]` — Sec. VI's justification for the $A_2B$ segments reads against the Sec. II win definition; now known to be the paper's own terseness, not a lost clause.
- No team, no cooperation, no synchronization; instantaneous kill on target entry.

## Relevance to My Research
The $\max\min\langle n,f\rangle=0$ primitive is the general-geometry statement of the usable-part condition — it applies to *any* target shape, including Layer 2's aspect-dependent envelopes — and is what `ProblemStatement.md` §11 earmarks this paper for: locating BUPs on all four Layer 2 target sets without committing to costates first. The frame-choice lesson is also directly actionable, since G&P get a *closed* barrier only by attaching axes to the faster aircraft rather than the nominal pursuer — a live decision in the six-state reduction. And this is a third independent vote that mutual kill is codimension-one, bearing on open decision #5.

---

## Verification Record

Two passes. **2026-09-08 (scout):** equations reconstructed from the degraded text layer and checked in sympy; four checks passed, six markers recorded. **2026-09-10 (guided, with Ethan):** pages read as images at 400 dpi — fully legible, which settles most of the earlier markers and converts two of them into *printed errors in the article*.

**Confirmed, residual exactly zero**

- **Eq. (1) / reduced dynamics.** Substituted into $\langle n,f\rangle$ with $n=(-y_x,1,-y_\theta)$, $\gamma=1/2$, $\beta=1$: reproduces printed **Eq. (8)** term for term, including its $(\sin\theta)/2$, $(\cos\theta)/2$ and $-1$ coefficients — confirming $\gamma$ and $\beta$ *from the equations*, not only the prose. Reconfirmed 2026-09-10 by back-substitution of Eqs. (10)–(12).
- **Eq. (4) — BUP of $T_1$**, now legible: $x_0=1/2$, $y_0=\sqrt3/2$, constant in $\theta_0$. Since $x_0^2+y_0^2=1$ and $\arctan(y_0/x_0)=60°$, this pins **$r_1=1$, $\alpha_1=30°$**. *Resolves 2026-09-08 marker 5 — the scout's inference from a single surviving number was correct.*
- **Eq. (5) — BUP of $T_2$**: satisfies $x_0^2+y_0^2=1$ identically ⇒ $r_2=1$ in units of $R_1$. On that circle the normal velocity $\gamma(x\sin\theta+y\cos\theta)-y$ is **control-independent** and vanishes exactly at the Eq. (5) point, confirming it as the $\max\min v_n=0$ locus and explaining why an all-aspect circular target gives a closed-form BUP.
- **Eq. (11)**, $[yu_1-\tfrac12\sin\theta_0]^2+[xu_1-1+\tfrac12\cos\theta_0]^2=C(\theta_0)$: the $\theta$-frozen invariant, centre $\big(u_1(1-\tfrac12\cos\theta_0),\,u_1\tfrac12\sin\theta_0\big)$, matching term for term. *Resolves marker 3 — the printed heading is "For $u_1=u_2$", as the scout conjectured; the extraction had merged two headings. Nothing depended on it.*
- **Eq. (12)** ($u_2=0$): back-substituted, residual 0 in both components. *Resolves marker 2 in the scout's favour — the "missing $+1/u_1$" is present in print, folded into the numerator "2" of $[2-(\theta-\theta_0)\sin\theta]/2u_1$. No discrepancy.*
- **Eq. (10) $x$-component** ($u_1=-u_2$): residual 0 as printed, including the "$2+\cos\theta$" numerator.

**Printed errors in the article (not scan damage)**

- **Eq. (10), $y$-component — a genuine typo, and load-bearing.** The article prints $[\sin(\tfrac{\theta+\theta_0}{2})-\sin\theta_0]/2u_1$. Integrating Eq. (1) in complex form ($z=x+iy$, $\dot z=iu_1z+\tfrac{i}{2}e^{-i\theta}-i$, $\theta=\theta_0-2u_1t$) gives $\sin\theta$. With $\sin\theta$ both residuals vanish identically; with $\sin\theta_0$ they are $-\tfrac12\sin\theta_0-\tfrac12\sin(2u_1t-\theta_0)$ and $-\cos(2u_1t-\theta_0)$ — nonzero everywhere, not a simplification failure. The $x$-component prints the analogous term as $\cos\theta$, so the equation is asymmetric on its face. **Consequence:** Eq. (10) grows two of the four barrier parts, so coding the barrier from the printed formula produces a wrong surface. Use $\sin\theta$. Confirmed by zooming the typeset page — the subscript is genuinely there.
- **The sentence introducing Eq. (6)** reads "the natural boundary of the usable part of *$T_2$* would emerge." But Eq. (6), $x_0=[\sin(\theta_0-30°)+1]/4$, $y_0=[\sin(\theta_0-30°)+1]\sqrt3/4$, has $y_0/x_0=\sqrt3$ — it lies along $T_1$'s straight sector edge at $60°$ from the $x$-axis, radius $[\sin(\theta_0-30°)+1]/2\le1=r_1$, reaching Eq. (4) exactly at its maximum. It is unambiguously the **natural BUP of $T_1$**, emerging when $r_2<1$ stops cutting it off. *Resolves marker 6 — the scout read the context correctly.* The dependent $PBQP$ exception is now locatable: $P$ and $Q$ **do** appear in Fig. 4, at the foot of the barrier on the BUP line $x=1/2$, straddling $B$ near $\theta\approx120°$, so $PBQP$ is the small closed region pinched between the BUP and the two barrier branches meeting at $B$. The mechanism — player 2 taken inside $T_1$'s *natural* usable part while player 1 only grazes $\partial T_2$ — is a reconstruction, not something the paper spells out.

**Open**

- `[UNVERIFIED 1]` — **Sec. VI, the $A_2B$ segments.** The paper: "the points on the barrier surface which emanate from $T_2$, namely the segments $A_2B$ in Fig. 5, are initial conditions which result in a win for player 2, since player 1 only grazes the second player's target set." *Uncertain:* by the Sec. II definition a graze is precisely what does **not** constitute capture, so the stated reason appears to argue the opposite conclusion. *Checked:* read from the 400 dpi page image and faithful — this is the paper's own terseness, so a fresh look at the printed article will **not** settle it. *What would settle it:* the analogous argument in Ref. 7, the *JOTA* companion, whose note is already in this project — a cheap in-project cross-check. *Downstream:* it relabels one family of barrier points, so it matters only if these figures are used as validation data; it touches neither the equations of motion nor the barrier construction.

**Transcription corrections to the 2026-09-08 draft**

- Sec. VI reads $A_2A_1$, not $A_2A_2$.
- Eq. (9) has a second component the extraction lost: $u_2=\operatorname{sign}(y_\theta)$.
- Markers 2, 3, 5 and 6 are resolved above and are no longer live. **One live marker remains.**
