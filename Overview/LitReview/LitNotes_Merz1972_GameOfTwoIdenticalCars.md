# Merz, 1972 — The Game of Two Identical Cars

## Citation
Merz, A. W. (1972). *The Game of Two Identical Cars.* Journal of Optimization Theory and
Applications, 9(5), 324–343. DOI 10.1007/BF00932932. Stanford postdoctoral work under J. V. Breakwell.

## Problem Framing
- **Game type:** Both halves of Isaacs' programme, in order — the game of kind (the *barrier*), then the game of degree solved *inside* it, giving optimal feedback controls for both players as functions of the state. The only reviewed source carrying a turn-rate-limited two-car problem all the way to a strategy synthesis rather than stopping at the partition.
- **Agent structure and lethality:** 1v1 with **fixed roles** (assumed, and load-bearing for the Hamiltonian) and **one** capture set, a disk of radius $\beta$ about P. One-sided: no mutual kill, no role determination, no second target.
- **Dynamics and kill geometry:** Two identical cars, unit speed and unit turn rate both sides, collapsing Isaacs' three parameters to one — $\beta$ = capture radius / common minimum turn radius, with every result at $\beta = 0.5$. Capture is isotropic and range-only: no aspect dependence, terminal heading requirement, or weapon envelope.
- **Dimensionality:** Third-order, $\mathbf{x} = [x, y, \theta]$ — E's position relative to P in P-fixed axes plus the angle between the velocity vectors; controls are normalized turn rates $\sigma_1, \sigma_2$ with $|\sigma_i| \le 1$.

## Core Contribution
**The barrier is closed, and closed *because* the players are identical.** With equal speeds and equal turn rates capture is not always possible: at $\theta = 0$ the evader holds its initial radial separation forever by duplicating the pursuer's control. The capture region is therefore a bounded volume, and finding that closed surface is the whole content of the game of kind. Its constant-$\theta$ cross-sections have a distinctive **"Gothic arch"** shape — a straight segment tangent to the capture circle joined to a curved one. Isaacs' treatment, which assumes a faster pursuer, may instead give an open barrier.

**A complete game-of-degree strategy map inside the barrier,** given as $\theta = \text{const}$ sections from $-165°$ to $-30°$. Across the evader's dispersal surface the evader's control switches; across the pursuer's universal surface the pursuer's control switches, with P flying straight on the surface itself and the state riding it to capture.

**The headline claim — no new singular-surface types.** With a finite capture region the *only* exceptional surfaces are a universal surface for P and a dispersal surface for E; going from second order (the homicidal chauffeur) to third introduces no new kinds. Merz then **conjectures**, without support, that the general non-identical two-car game will need fewer still, since many of the homicidal chauffeur's existed only because the pedestrian had unlimited maneuverability.

## Method
Isaacs retrogression from terminal conditions. The main equation is bilinear in both controls, so play is bang-bang off singular arcs; requiring the radial rate at contact to be non-positive gives the boundary of the usable part in two branches, with the game of degree terminating on the arc between. Retrograde derivatives of the switch functions there supply the terminal strategies, and closed-form retrograde state solutions carry them backward.

The interesting choice is that **the construction is deliberately adjoint-free.** Merz observes that the adjoints go discontinuous along the retrograde paths *before* either switch function changes sign, caused by the evader's dispersal surface, and concludes that strategies can be found without explicit knowledge of the adjoints at all — building everything instead from closed-form state solutions plus matching conditions between competing paths.

Those matching conditions also distinguish the two dispersal structures: on the barrier the competing paths have **different** times-to-go and the dispersal line is located by equating their terminal coordinates, whereas on the game-of-degree dispersal surface the times-to-go are **equal**, and that equality is the equation locating it. Both, and the universal surface, are solved numerically.

## Key Terminology Introduced
- **Game of two identical cars** — the one-parameter symmetric specialization of Isaacs' two-car game.
- **Barrier / envelope of capturable states** — the closed surface bounding the capture volume.
- **Safe contact** — barrier motion touching the capture circle tangentially without penetrating; radial separation constant, both players turning the same direction.
- **Evader's dispersal line (EDL)** — where the two barrier sheets intersect; times-to-go *differ* across it, and retrograde solutions past it are discarded.
- **Evader's dispersal surface (EDS)** — its game-of-degree counterpart, defined by *equal* times-to-go.
- **Universal line / surface (US) for P** — the locus where P's optimal control is singular (straight flight); trajectories join it and ride it to capture.
- **Gothic arch** — Merz's name for the barrier's constant-$\theta$ cross-section shape.

## Connections to Prior Literature
- **Davidovitz & Shinar (1989) — builds on; the same reduced system in a different chart.** D&S's "two identical cars" model *is* this kinematics: their $(R, \phi_1, \phi_2)$ and Merz's $(x, y, \theta)$ are two three-state reductions of the same symmetric system, after which D&S replace the isotropic disk with a two-sided aspect-dependent no-escape envelope. Since ProblemStatement §3.1 inherits D&S's chart, **Merz is the $\beta$-disk degenerate case of Layer 0**.
- **Getz & Pachter 1981 (*JGC*) — agrees by a different route.** Both obtain a closed barrier and a finite capture region, and both truncate retrograde barrier families at a dispersal curve; but G&P buy closure by fixing axes on the *faster* player, where Merz gets it from identity of the players.
- **Olsder & Breakwell (1974) and Merz & Hague (1977) — a useful contrast.** Merz's whole inventory is two exceptional surfaces and going up a dimension adds no new types, where O&B need seventeen local terminal games. What buys that richness is bidirectional lethality and asymmetry, not state count — which matters because Layer 2 adds *target sets* to D&S rather than dimension.
- **On mutual-kill codimension, no vote.** One target set and fixed roles mean the paper is silent, and it should not be counted as a fifth data point. **Buzikov & Galyaev (2023)** is likewise unresolved rather than contradicted: they report a barrier departing from Merz's above a critical capture radius, and Merz works only $\beta = 0.5$.

## Limitations / Open Questions
- **One target, fixed roles, one-sided lethality** — this qualifies the original reason for chasing the paper: it supplies the symmetric *kinematics* D&S build on, not a symmetric two-target game. Isotropic capture constrains nothing on the WEZ side, and being 1v1 it says nothing about team structure or synchronization.
- **One parameter value.** Every figure is $\beta = 0.5$, with no sweep and no critical $\beta$ at which the structure changes — unlike Getz & Pachter 1981, which sweeps and does find type changes.
- **Algebra deliberately suppressed.** Merz states outright that important relations are given in functional form only, to avoid the explicit algebra of the barrier calculation, so reimplementation means redoing it. His one surprising result — a sharp curve in the dispersal surface near $\theta \approx -60°$ — is checked only by plotting trajectories.
- **Two printing errors, noted in passing** — Eq. (13)'s terminal gradient drops a minus sign (contradicting his own Eq. 12), and the p. 328 remark on when the radial rate is positive has its indices transposed. Neither propagates into the barrier construction, but both would corrupt a transcription into a costate integrator.
- **Reference list is two items** — Isaacs (1965) and Merz's 1971 Stanford thesis. Nothing further to harvest.

## Relevance to My Research
The kinematic foundation Layers 0 and 2 sit on, and more usefully the **only reviewed source publishing a complete game-of-degree feedback solution on those kinematics**. That makes it a ready-made acceptance test for Layer 1: solve the 1v1 game of degree with the D&S target sets replaced by an isotropic $\beta = 0.5$ disk and check the solver reproduces Merz's universal and dispersal surfaces, before pointing the same method at a problem with no published answer. His discriminator between the two dispersal structures — times-to-go differ on a barrier dispersal line, equal on a game-of-degree one — is also a cheap classification test for whatever singular structure a four-target-set Layer 2 barrier turns up.
