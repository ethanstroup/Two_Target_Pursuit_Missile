# [Yan, Duan, Shi, Zhong, Bullo, 2022] — Matching-Based Capture Strategies for 3D Heterogeneous Multiplayer Reach-Avoid Games

## Citation
Yan, R., Duan, X., Shi, Z., Zhong, Y., & Bullo, F. (2022). Matching-based capture strategies for 3D heterogeneous multiplayer reach-avoid differential games. *Automatica*, 140, 110207.

## Problem Framing
- **Game type:** Reach-avoid differential game, decomposed into a game-of-kind building block (Corollary 1: win/lose/tie trichotomy) plus one solved game-of-degree (Theorem 3.2: HJI value function for a specific subgame). Multi-evader assignment is layered on top as a combinatorial (NP-hard) optimization.
- **Agent structure:** $N_p$ pursuers vs. $N_e$ evaders, heterogeneous speeds for all players, heterogeneous capture radii $r_i \geq 0$ (isotropic sphere capture, no aspect-angle dependence). Requires pursuers strictly faster than every evader ($v_{P_i}/v_{E_j} > 1$). Holonomic, simple-motion dynamics (instantaneous heading control), no turn-rate constraints.
- **Dimensionality:** Full 3D Euclidean space $\mathbb{R}^3$, single flat plane $\mathcal{T}$ separating play region from goal region (extended to a bounded convex play region with planar exit in Sec. 5). A 3-pursuer-vs-1-evader subgame state space is 12-dimensional.

## Core Contribution
Three linked results:
1. **Evasion Space (ES) convexity** (Lemma 3.1): For pursuit coalition $P_s$ and evader $E_j$, the closure of $\bar{\mathbb{E}}(s,j) = \{x : f_{ij}(x) \geq 0,\ \forall i \in s\}$, built from potential functions $f_{ij}(x) = \|x-x_{P_i}\| - \alpha_{ij}\|x-x_{E_j}\| - r_i$, is always bounded and strictly convex.
2. **3-pursuer degeneracy** (Lemma 3.3): The interception point $I(s,j)$ (closest point of $\bar{\mathbb{E}}(s,j)$ to the goal) always depends on at most 3 pursuers, regardless of coalition size. Dimensional argument: an isolated point in $\mathbb{R}^3$ is generically pinned by exactly 3 active constraint surfaces; a 4th constraint can only confirm or filter an existing candidate, never create a new one.
3. **Guaranteed feedback strategy + HJI-as-convex-program** (Theorem 3.1, Theorem 3.2): Steering each relevant pursuer straight at $I(s,j)$ guarantees $\dot{z}_{I(s,j)} \geq 0$ regardless of evader strategy. For a related game-of-degree, the HJI value function equals the optimal value of the same small convex program — avoiding a PDE solve that would need ~$10^{12}$ grid points for a 3-pursuer coalition.

Layered on top: multi-evader assignment is formalized as Maximum Bipartite Matching with Conflict graph (MBMC), proven NP-hard (reduction from 3-dimensional matching), with a polynomial-time 1/3-approximation (Sequential Matching Algorithm) and a receding-horizon wrapper that only switches matchings when strictly improved.

## Method
- Potential-function/level-set approach defining ES boundaries as zero-sets of $f_{ij}$, generalizing the 2-player zero-capture-radius Apollonius circle to nonzero radii and multiple cooperating pursuers.
- Polar-coordinate parametrization + curvature lemma to prove strict convexity — necessary to guarantee a unique closest point to the goal exists.
- KKT conditions on the convex program defining $I(s,j)$, connected directly to the HJI Main Equation — used both to derive the feedback strategy (Thm 3.1) and to prove the value-function equivalence (Thm 3.2). This KKT↔HJI bridge is the paper's most reusable technique.
- Quartic-equation elimination (eliminating $\rho$ across three sphere equations) to bound intersection candidates for any 3-pursuer subcoalition at 4.
- Reduction from 3-dimensional matching (NP-complete) to prove MBMC is NP-hard; local-search-with-size-2-swaps chained across 3 passes for the approximation algorithm.

## Key Terminology Introduced
- **Evasion Space (ES)** $\mathbb{E}(s,j)$: positions an evader can reach without capture by coalition $P_s$, regardless of $P_s$'s control.
- **Interception point** $I(s,j)$: unique point in $\bar{\mathbb{E}}(s,j)$ closest to the goal region — the pursuit team's aim point.
- **Pursuit coalition** $P_s$: subset of pursuers treated as a joint decision-making unit against one evader.
- **Game of kind vs. degree** (as used here): kind = win/lose/tie trichotomy based on whether $\bar{\mathbb{E}}(s,j)$ intersects the goal; degree = optimizing *where* capture happens, given a win is guaranteed.
- **MBMC**: bipartite matching between coalitions and evaders with a conflict graph forbidding coalitions sharing a pursuer from being matched simultaneously.
- **Sequential Matching Algorithm**: 3-pass greedy approximation for MBMC (max-flow on 1-pursuer coalitions, then local search on 2- and 3-pursuer coalitions).

## Connections to Prior Literature
- **Isaacs' *Differential Games***: Directly extends Isaacs' Sec. 6.7–6.8 Evasion Space concept (originally single pursuer, zero capture radius = Apollonius circle) to multiple cooperating pursuers with nonzero, heterogeneous radii in 3D. The KKT/HJI equivalence (Thm 3.2) is a novel bridge, explicitly flagged by the authors as generalizable.
- **Mammadov & Ranasinghe (2025)**: Both exploit Apollonius-type convex geometry for tractability, but M&R's control law is instantaneous/greedy with no lookahead, while this paper's ES-based feedback strategy carries a finite-horizon guarantee via a Lyapunov-style monotonicity argument (Thm 3.1).
- **Dillon, Zollars, Weintraub, Von Moll (WEZ/cardioid)**: Capture sets here are strictly isotropic (spheres), unlike a cardioid WEZ. The load-bearing convexity result was proven specifically for spherical capture sets via a polar-coordinate curvature argument — this does **not** automatically transfer to aspect-angle-dependent cardioid boundaries.
- **My 2v1 synchronized-impact problem**: Terminal set here is a *union* (any one pursuer capturing ends the game) — structurally opposite my *equality/coupling*-style synchronization constraint ($\tau_1 = \tau_2$). None of the ES machinery handles temporal coupling; it is purely spatial. The KKT-based value-function trick (Thm 3.2) is the most transferable piece if the simultaneity constraint can be phrased as a small convex feasibility problem.

## Limitations / Open Questions
- Isotropic, orientation-independent capture sets only — no aspect-angle/WEZ-style dependence.
- No synchronization or timing-coordination constraint between coalition members — multi-pursuer machinery is entirely about guaranteeing a win, not coordinating arrival time.
- Feedback strategy (Thm 3.1) is guaranteed-win, not proven optimal in general; only the specific closest/farthest-capture game of degree is fully solved.
- Receding-horizon matching (Sec. 4.2) explicitly lacks a global optimality guarantee — greedy, one-step improvements only.
- Value function differentiability assumed away in Thm 3.2 ("states where $V$ is differentiable"); barrier and singular surfaces are explicitly left unanalyzed.
- Requires pursuers strictly faster than evaders ($\alpha_{ij} > 1$) throughout; slower or equal-speed cases left as future work.

## Relevance to My Research
The KKT-to-HJI equivalence (Thm 3.2) is the most directly transferable technique — a candidate method for solving a synchronized-impact value function without a full PDE solve, if the simultaneity constraint can be written as a convex program. However, the paper's central convexity result rests entirely on isotropic spherical capture sets, so before reusing any Evasion-Space or 3-pursuer-degeneracy machinery, I need to check whether an analogous convexity property holds for cardioid-shaped WEZ boundaries — it may not, given their aspect-angle dependence.
