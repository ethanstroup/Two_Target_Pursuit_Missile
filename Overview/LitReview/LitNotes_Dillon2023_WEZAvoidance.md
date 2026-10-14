# Dillon, Zollars, Weintraub, & Von Moll, 2023 — Optimal Trajectories for Aircraft Avoidance of Multiple Weapon Engagement Zones

## Citation
Dillon, P. M., Zollars, M. D., Weintraub, I. E., and Von Moll, A., "Optimal Trajectories for Aircraft Avoidance of Multiple Weapon Engagement Zones," *Journal of Aerospace Information Systems*, Vol. 20, No. 8, Aug. 2023, pp. 520–525. https://doi.org/10.2514/1.I011224

## Problem Framing
- Game type: **Not a two-sided differential game.** Single-agent minimum-time optimal control problem with a dynamic, state-dependent path constraint. The WEZ is non-reactive — its envelope is a deterministic function of the evader's own state, not an adversary optimizing against the evader. Structurally closer to reach-avoid-as-obstacle-avoidance than to Isaacs-style pursuit-evasion.
- Agent structure: 1 evading aircraft; 1 or 2 static-origin WEZ threats (SAM sites), homogeneous, non-maneuvering. Constant unit velocity aircraft, no speed control.
- Dimensionality: 2D planar. State space $x(t) = [x_T, y_T, \psi]^\top \in \mathbb{R}^3$; single control $u$ = heading rate, $|u| \le 0.78$ rad/s.

## Core Contribution
Extends a prior single-WEZ result (indirect/costate methods, Weintraub et al. 2022) to the **two-WEZ case** using direct orthogonal collocation, and characterizes trajectory structure as a function of **cardioid separation distance (CSD)**:
- CSD giving ≤70% $R_{max}$ overlap → straight-line path threads between WEZs (14.0 s).
- CSD giving ≥75% overlap → no threading possible; must route around both as a combined obstacle (17.69 s, slowest case).
- 70–75% overlap ("interim" regime) → aircraft first flies tangent to one WEZ, which *reduces that WEZ's own range* by driving its bearing angle $\zeta \to 90°$ (since $\rho_{max}(\zeta) = \frac{R_{max}}{2}(\cos\zeta+1)$), opening a gap it then splits through (16.34 s).

Confirms via Hamiltonian/costate analysis (constant $\mathcal{H} = -1$, satisfying transversality) that the single-WEZ optimal structure is always **straight → tangent-to-boundary → straight**, and shows this generalizes qualitatively to the multi-WEZ case.

## Method
**Direct orthogonal collocation** (Legendre-Gauss-Radau, via GPOPS-II), building on Eide/Hager/Rao (2021). Chosen because indirect (costate-based) methods, which solved the single-WEZ case analytically in prior work, become intractable once (a) heading is added as a state with heading-rate as control (higher fidelity dynamics) and (b) a second simultaneous WEZ constraint is added. Costates are still recovered post hoc from the collocation solution to verify optimality via the constant-Hamiltonian/transversality check — direct methods aren't used blind, they're checked against the same necessary conditions indirect methods would produce.

## Key Terminology Introduced
- **WEZ (weapon engagement zone)**: dynamic threat envelope modeled as a cardioid, size/orientation state-dependent rather than fixed-radius.
- **Cardioid separation distance (CSD)**: distance between two WEZ cardioids' emanating points; the paper's control parameter for threat overlap severity.
- **Emanating point**: the origin location of a given WEZ cardioid (not the global origin, once multiple threats are present — Eqs. 13–15 offset the cardioid math accordingly).
- **$\rho_{max}(\zeta)$**: worst-case cardioid range as a function of bearing angle alone, $\frac{R_{max}}{2}(\cos\zeta+1)$ — the reduced form used when $\theta = \lambda$ (threat pointed directly at aircraft).
- **Bearing angle $\zeta$**: relative bearing from aircraft to WEZ origin; the aircraft's one geometric lever for shrinking the threat's own envelope.

## Connections to Prior Literature
- **Isaacs**: this paper sits *outside* the Isaacs ME/value-function apparatus you've been building — the WEZ doesn't optimize, so there's no ME₁/ME₂ split or true saddle point. Useful as a contrast case: it shows what the same Dubins-style kinematics (position + heading, heading-rate control) look like stripped of the second player. If you embed a real bandit into your 2v1 problem, this paper's dynamics are a plausible starting block for each vehicle's individual state equations inside a full Isaacs-style ME.
- **Mammadov & Ranasinghe**: both papers define a geometric "envelope" (Apollonius disc vs. cardioid) whose boundary depends on relative geometry and use that boundary to drive control. Key contrast: M&R solve a real two-sided game with a closed-form, decentralized, no-lookahead heading law (via Leibniz/Reynolds transport theorem on level sets); Dillon et al. solve a one-sided OCP numerically with full-horizon lookahead (collocation over the whole trajectory) and no closed-form control law. If your synchronized-impact problem ends up needing full lookahead (likely, given the terminal simultaneity constraint), direct collocation — not M&R's greedy/instantaneous approach — is the more directly transferable machinery.
- **Yan et al.**: both concern convex/geometric "safe region" constructs, but Yan solves via KKT–HJI equivalence (still fundamentally an indirect/analytic route), while this paper's whole motivation is that indirect methods stop scaling once you add a second simultaneous dynamic constraint. This is the concrete evidence that your own problem — 2 pursuers + a hard synchronization constraint + WEZ-like geometry — will likely need direct collocation (GPOPS-II-style) rather than a KKT/HJI-equivalence closed form, once complexity exceeds a single constraint.
- Directly extends Weintraub, Von Moll, Carrizales, Hanlon, & Fuchs (2022 SciTech) — the single-WEZ, indirect-method predecessor to this paper.

## Limitations / Open Questions
- WEZ is non-adversarial: no strategic, evasion-aware threat maneuvering. Not a substitute for a true 3-agent (2 friendly + 1 reactive bandit) differential game.
- 2D, constant unit speed, purely kinematic (Dubins-style) — no altitude, no speed/energy state, no aerodynamic realism.
- The 70–75% "interim" CSD threshold was found by **experimental perturbation**, not derived analytically — the author explicitly notes analytical solutions are unlikely here. Treat this regime boundary as empirical, not a general closed-form result.
- Threat geometry (origin, $R_{max}$) is fully known/static with perfect information — no sensing uncertainty.
- Only tested up to two simultaneous WEZs; scaling behavior to N WEZs (or N friendlies) is untested.

## Relevance to My Research
Confirms the cardioid WEZ formulation you're already using as shared terminology, and — more importantly — demonstrates empirically that direct orthogonal collocation is the practical fallback once indirect/costate methods break down under multiple simultaneous dynamic constraints, which is very likely to be your situation once you add a second friendly and a hard synchronization constraint on top of WEZ-style geometry. The interim-CSD tactic (shrink one threat's envelope via bearing maneuver to open a gap) is also a plausible template for an offensive analog: one friendly manipulating bearing/aspect to suppress the bandit's effective WEZ while the second friendly closes.
