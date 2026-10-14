# Mammadov & Ranasinghe, 2026 — Area-Optimal Control for Heterogeneous Multi-Agent Pursuit

## Citation
Mammadov, K., & Ranasinghe, D. C. (2026). *Area-Optimal Control Strategies for Heterogeneous Multi-Agent Pursuit.* Proceedings of the AAAI Conference on Artificial Intelligence (arXiv:2511.15036v2, posted Nov 2025).

## Problem Framing
- **Game type:** Zero-sum, instantaneous min-max game-of-degree. Not a classical game-of-kind — no barrier surface or win/lose state-space partition; objective is continuous minimization/maximization of a geometric quantity (area) at every instant.
- **Agent structure:** N pursuers with heterogeneous speeds $V_i$, one evader with speed $V_e$, all $V_i > V_e$. Simple kinematic point-mass agents with instantaneous unit-heading control (no turn-rate or dynamics constraints).
- **Dimensionality:** 2D planar ($\mathbb{R}^2$); state space is $2(N+1)$ position coordinates.

## Core Contribution
Defines the evader's **safe-reachable set** $S_e(t)$ = intersection of $N$ Apollonius discs (one per pursuer-evader pair), and frames the game as $\min_{\{u_i\}} \max_v \dot{A}_e(t)$, where $A_e(t) = \text{Area}(S_e(t))$. Because $\dot{A}_e(t)$ decomposes into independent inner-product terms per agent, the game decouples: each agent's optimal heading is simply $\pm$ the (normalized) area gradient w.r.t. its own position. The paper's central result (Theorem 1.4) gives this gradient a clean **geometric closed form**: each active pursuer's optimal heading points directly at the **centroid of the boundary arc it contributes** to $\partial S_e(t)$; the evader's optimal heading is a **weighted sum of vectors toward each active pursuer's arc centroid**, weighted by arc length and speed-ratio terms. Under optimal play, $\dot{A}_e(t) = V_e\|F_e\| - \sum_i V_i\|F_{p_i}\|$ — a direct competition of weighted gradient magnitudes.

## Method
Standard approach would require a closed-form area formula for an N-disc intersection, then differentiating it — intractable for $N>2$. Instead, the paper applies the **Leibniz integral rule / Reynolds transport theorem** to implicit **level-set functions** $F_i(q,t) = \|q-c_i(t)\|^2 - r_i(t)^2$ defining each disc boundary. This yields the area's rate of change as a boundary flux integral (normal velocity of $\partial S_e(t)$), without ever needing an explicit area formula — sidestepping the geometric intractability entirely.

## Key Terminology Introduced
- **Safe-reachable set $S_e(t)$** — intersection of all pursuers' Apollonius discs; the evader's instantaneous "safe zone."
- **Apollonius disc** — locus of points the evader can reach at least as fast as a given pursuer (ratio-of-distances circle).
- **Active index set $I(t)$** — pursuers whose disc boundary actually contributes an arc to $\partial S_e(t)$ (i.e., not fully contained in another disc).
- **Level-set function $F_i(q,t)$** — implicit function whose zero set defines disc $i$'s boundary; used to compute normal boundary velocity.
- **Arc centroid $C_{\text{arc},i}(t)$** — average position along the boundary arc contributed by pursuer $i$; target point for that pursuer's optimal heading.
- **Speed ratio $\alpha_i = V_e/V_i$** — quantifies pursuer $i$'s speed advantage; controls disc geometry and evader's escape-weighting.

## Connections to Prior Literature
- **Isaacs' *Differential Games*:** Sharp contrast in approach — this paper avoids the full HJI/value-function/Main Equation machinery entirely, substituting a purely instantaneous geometric proxy (area) for the value function. Gains real-time tractability but forfeits the global-optimality guarantee Isaacs' ME-based approach provides.
- **Yan et al. 2022:** Strong structural parallel — their **Evasion Space (ES)** and this paper's **safe-reachable set $S_e(t)$** are both geometric "how much freedom does the evader retain" constructs. Yan et al.'s **KKT/HJI equivalence** (a convex-program reformulation of the HJI condition) is a candidate technique worth testing against Ethan's simultaneity-constrained terminal condition — Mammadov & Ranasinghe sidestep HJI altogether via the greedy/instantaneous route instead.
- **Dillon, Zollars, Weintraub, & Von Moll:** Shares the general "geometric engagement envelope" framing (cardioid WEZ vs. Apollonius disc) but that work targets single-engagement avoidance geometry, whereas this paper targets cooperative multi-pursuer containment.
- **Shah & Schwager (2019)**, cited within the paper as direct predecessor: equal-speed pursuers, half-plane safe-set geometry. This paper's core generalization is extending that framework to heterogeneous speeds (Apollonius discs replace half-planes).

## Limitations / Open Questions
- Purely **greedy/instantaneous** control — no lookahead, no proof of optimality over a finite horizon; a non-myopic evader could plausibly exploit this against a team of purely reactive pursuers.
- Capture condition is only "$A_e \to 0$" — no treatment of **simultaneous or synchronized arrival**, multiple evaders, or any notion of coordinated timing among pursuers.
- Simple kinematics (holonomic, instantaneous heading change) — no turn-rate, acceleration, or WEZ-style engagement-envelope constraints relevant to aerial combat.
- No obstacles, no partial information, single evader only — explicitly flagged by the authors as future work.

## Relevance to My Research
The area-gradient/Leibniz-rule machinery is a clean example of deriving a decentralized, closed-form control law from a purely geometric objective without solving an HJI PDE — useful as a contrast case to Isaacs' and Yan et al.'s value-function-based approaches. Its explicit lack of any simultaneity or synchronization treatment underscores that this greedy area-minimization framework, as-is, would need substantial restructuring (likely toward Yan et al.'s KKT/HJI-equivalence route) before it could handle a synchronized-impact terminal constraint like the one central to my 2v1 problem.
