# Getz & Pachter, 1981 — Two-Target Pursuit-Evasion Differential Games in the Plane

## Citation
Getz, W. M., and Pachter, M., "Two-Target Pursuit-Evasion Differential Games in the Plane," *Journal of Optimization Theory and Applications*, Vol. 34, No. 3, July 1981, pp. 383–403.

## Problem Framing
- **Game type:** Pure **game of kind** — state-space partition into win-P1/win-P2/draw/stagnation regions, solved via Isaacs' barrier/semipermeable-surface machinery (retrogression from the boundary of the usable part, BUP) combined with Lyapunov/invariance arguments (following Getz & Leitmann, 1979) to certify each region. No cost functional, no HJI PDE, no value function — the corresponding **game of degree** (min/max time-to-capture subject to not passing through the opponent's target) is explicitly named as unsolved future work.
- **Agent structure:** 2 players, **1v1**, no cooperation or team structure. Introduces the **two-target** concept: each player has his own independent capture set ($T_1$, $T_2$), removing any a priori pursuer/evader role assignment — either player can be forcing the other, depending on state. Worked example (Section 3) uses the **homicidal-chauffeur simplification**: player 1 is turn-rate-limited (min turning radius $R$), player 2 has zero turning radius (infinite maneuverability, heading is a direct control). Speed ratio $\gamma=1/2$ (player 1 twice as fast). Target geometry is also asymmetric in kind, not just maneuverability: $T_1$ is a directional squint cone (range $r_1$, half-angle $\alpha$), $T_2$ is an omnidirectional circle (range $r_2$). The fully symmetric, both-sides-turn-limited version ("game of two cars") is cited from companion papers, not solved here.
- **Dimensionality:** Full state 6D → relative-motion reduction to $\mathbb{R}^2\times S^1$ → further reduction to $\mathbb{R}^2$ in the homicidal-chauffeur worked example, since player 2's heading is direct control and drops out of the state.

## Core Contribution
A fully worked **game map** (Fig. 5) for a generic two-target homicidal chauffeur example ($\gamma=1/2$, $r_1=2R$, $r_2=R$, $\alpha=\pi/6$): the reduced state space is partitioned into regions I–V, each with an assigned outcome (win-P1, win-P2, or draw) and an explicit feedback strategy guaranteeing it. The partition is built by:
1. Identifying the **usable part** of each target's boundary — the points $A=(1/2,\sqrt3/2)$ and $B=(\sqrt3/2,-1/2)$ mark where usability of $T_1$ and $T_2$'s boundaries respectively switches on/off, found by solving $\max_{u_1}\min_{u_2}v_n=0$ (or the symmetric $u_2$/$u_1$ version for $T_2$) directly on the target boundary.
2. Growing **barrier curves** $[AK]$ and $[BF]$ outward from those points by integrating the same $v_n=0$ condition along an entire curve (not just a point).
3. Certifying every region off the barrier via direct integration (regions I, II) or **Lyapunov functions** (regions III, IVa/IVb — piecewise, patched at a seam curve to preserve continuity).

A key structural finding: at $K=(3,-\sqrt3)$, no semipermeable extension of the barrier exists under either sign of $u_1$ — this forces a **swerve maneuver**: player 1 must recede (play the "wrong" turn direction) across a separate switching curve $[KL]$ before he can resume closing on $T_1$ below $[FK]$. Two singular surfaces (dispersal, universal, in Isaacs' taxonomy) also appear on the $y$-axis.

Section 4 sweeps the four problem parameters ($\gamma$, $\rho_1=r_1/R$, $\rho_2=r_2/R$, $\alpha$) and shows the map's *qualitative type* changes, not just its size — e.g., for $1<\rho_1<2$ the arc $[AF)$ stops being a player-2 win and becomes a forced mutual-annihilation draw; for large enough weapon range at equal speeds ($\gamma=1$), a genuine **stagnation region** appears where neither player can force a win without conceding the other's forcing region.

## Method
**Isaacs' BUP/retrogression method** (Ch. 6, semipermeable surfaces) for barrier construction, executed via explicit ODE integration rather than costate propagation: for a curve $y(x)$ with normal $n=(-y',1)^\top$, the normal velocity is $v_n = n\cdot(\dot x,\dot y)$; setting $\max_{u_1}\min_{u_2}v_n=0$ and substituting the bang-bang optimal $u_1$ and sinusoid-optimal $u_2$ yields an implicit ODE for the barrier curve itself.

**Lyapunov/invariance method** (Getz & Leitmann, 1979) for certifying win-regions off the barrier — hand-picked functions ($V=y-\sqrt3x$ in region III; $V=x^2+y^2-4$ and $V=\sqrt3x-y$ patched across IVa/IVb) shown to have a definite-sign derivative under worst-case opposing play. This sidesteps ever solving a global value function — each region gets its own local certificate instead. The paper frames this as the method's main selling point: "simple, direct, constructive, and flexible" relative to a full HJI solve.

## Key Terminology Introduced
- **Two-target game**: differential game where each player has an independent capture set; no a priori pursuer/evader assignment.
- **Usable part (UP)**: the portion of a target's boundary where the owning player can always force entry against optimal defense (max-min $v_n\geq0$).
- **Boundary of the usable part (BUP)**: the point(s) where boundary usability switches; barrier curves are seeded here.
- **Semipermeable surface / barrier**: a curve satisfying $\max_{u_1}\min_{u_2}v_n=0$ pointwise — crossable in one direction only, separating guaranteed-win regions.
- **Swerve maneuver**: a forced receding detour required where the barrier construction fails to extend (here, below $[FK]$), crossing a switching curve before resuming direct approach.
- **Dispersal surface**: singular surface where a player has two equally optimal controls with an arbitrary tie-break (here, $u_1=\pm1$ on part of the $y$-axis).
- **Universal surface**: singular surface where the opponent's best defense pins the state on it; deviation lets the other player force a win into either adjoining region.
- **Stagnation region**: a region (Section 4.4) where neither player can force a win and cannot move apart without ceding the opponent's forcing region.
- **Weapon range ratio** $\rho_i=r_i/R$: dimensionless parameter, central to Section 4's sensitivity analysis.

## Connections to Prior Literature
- **Isaacs' *Differential Games*:** This is a full worked instance of the barrier/BUP/semipermeable-surface apparatus (Ch. 6), which I hadn't yet reviewed directly — complements the ME/costate machinery already covered in Ch. 1, 2, 4.1–4.2. Same retrogression logic, executed geometrically (ODE integration) rather than via costates.
- **Weintraub, Pachter & Garcia (2020):** Same Isaacs-framework family, opposite half. Weintraub solves a *game of degree* (min-time value function, HJI-verified) for a *cooperative* 2-pursuer team against a single non-reactive evader. This paper solves a *game of kind* for a genuinely adversarial 1v1 pair — no cooperation, no synchronization, but the target *can* fight back.
- **Yan et al. (2022) / Mammadov & Ranasinghe (2025):** Both are one-sided — pursuers capture, the evader cannot reciprocate — despite rich multi-agent geometry. This is the first reviewed source where the "evader" is armed and can win outright, matching my problem's bidirectional-lethality requirement.
- **Dillon, Zollars, Weintraub & Von Moll (2023):** Both use bounded angular kill-envelope geometry (squint cone here vs. cardioid there), but Dillon's WEZ is non-reactive (single-agent OCP). Here, both targets are actively contested by an optimizing opponent — the genuine two-sided version of the same geometric idea.
- **Fills a previously flagged gap:** this paper (plus its own citation, Getz & Leitmann, 1979) was already on my "mutual-engagement foundations" reading list. It also surfaces two further citations worth chasing directly: **Olsder & Breakwell (1974)** and **Merz & Hague (1977)** — the actual solved cases of the fully symmetric, both-sides-turn-limited two-target game of two cars, which this paper only partially transfers to via a Lyapunov argument, not solves directly.

## Limitations / Open Questions
- **1v1 only** — no team/coalition structure, hence zero treatment of synchronization, which is the core of my own problem.
- The worked example uses the **homicidal-chauffeur simplification** (player 2 unconstrained maneuverability), not the symmetric both-sides-turn-limited case my homogeneous 2v1 base case will need. The paper claims a partial transfer (win regions for player 1 carry over to the full two-car case, via barrier projection + Lyapunov argument) but does not solve the symmetric case itself.
- Pure game of kind — the matching game of degree is explicitly unsolved, left as future work.
- Section 4's parameter sensitivity results are case-by-case worked figures (5, 7–10), not a general closed-form map as a function of $(\gamma,\rho_1,\rho_2,\alpha)$.
- Target geometry (directional cone vs. omnidirectional circle) is a specific asymmetric choice for this example, not a general result for two arbitrary WEZ-style targets.

## Relevance to My Research
This is the closest source so far to a genuine bidirectional-lethality building block for the 1v1 mutual-kill base case that's a prerequisite to my full 2v1 synchronized-impact problem — its game-of-kind trichotomy (plus draw/stagnation outcomes) and its BUP + Lyapunov barrier-construction method are directly reusable as a template, though it says nothing about synchronization since it's strictly 1v1. Its citation trail (Olsder & Breakwell, 1974; Merz & Hague, 1977) also points directly to the turn-limited-on-both-sides two-target result my homogeneous case will eventually need.
