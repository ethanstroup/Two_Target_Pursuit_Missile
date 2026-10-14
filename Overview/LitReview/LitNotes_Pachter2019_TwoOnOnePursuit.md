# Pachter, Von Moll, Garcia, Casbeer & Milutinović, 2019 — Two-on-One Pursuit

## Citation
Pachter, M., Von Moll, A., Garcia, E., Casbeer, D. W., & Milutinović, D. (2019).
*Two-on-One Pursuit.* Journal of Guidance, Control, and Dynamics, 42(7), 1638–1644.
DOI 10.2514/1.G004068. Engineering Note. AFIT / AFRL Control Science Center / UC Santa Cruz.
**Read from the published article (7 pp.), 2026-09-11** — supersedes an earlier read of the author manuscript.

## Problem Framing
- **Game type:** Both halves, in order — game of kind (which pursuer captures) then game of degree, solved in **closed form**. A revisit of Isaacs' "two cutters and a fugitive ship" (*Differential Games*, ex. 6.8.3), originally posed by Steinhaus in 1925.
- **Agents and lethality:** Cooperative 2v1, $P_1$ and $P_2$ vs. $E$. **One-sided**: point capture by the pursuers, no evader weapon, fixed roles. Payoff is time to capture (min–max).
- **Dynamics:** Holonomic simple motion in the plane — heading is the control, no turn limit, no dynamics at all ($A=0$). Pursuers equal speed normalized to 1; the single parameter is the evader speed $0\le\mu<1$.
- **Dimensionality:** $\mathbb{R}^6\to\mathbb{R}^3$ via a **rotating frame pegged to the $P_1P_2$ segment** — $x$ along it, $y$ the perpendicular bisector. States $(x_P,x_E,y_E)$ with $P_1$ at $(x_P,0)$, $P_2$ at $(-x_P,0)$; symmetry confines play to $x_P,y_E\ge0$.

## Core Contribution
**The game of kind is a partition by *which* pursuer captures** — $R_1$ (solo $P_1$, $P_2$ redundant), $R_2$ (mirror image), $R_{1,2}$ (both, in a pincer, **isochronously**) — not by win/lose. The evader is always caught.

**The headline is a corrected criterion, and the correction is the interesting part.** The natural geometric test — do the two Apollonius circles intersect? — gives the algebraic condition (8) $\mu^2y_E^2+(1-\mu^2)(\mu^2x_P^2-x_E^2)\ge0$, whose complement is a pair of **elliptical cones** $K_1,K_2$. Condition (8) is *necessary but not sufficient*: it also holds on subsets of $R_1$ and $R_2$, because the circles can intersect while the aim point $I$ still lies strictly inside the larger Apollonius disk, leaving one pursuer irrelevant and the BSR a "thick lens." **Theorem 1** replaces it: cooperative capture holds iff
$$-\mu x_P \le x_E \le \mu x_P,$$
so $R_{1,2}$ is a **planar wedge**, $R_1$ the wedge between $x_P=0$ and $x_E=\mu x_P$. The cones $K_1,K_2$ "have no role to play here."

**Game of degree, closed form.** In $R_1$ the active pursuer flies pure pursuit, $E$ runs directly away, and optimal trajectories are straight lines terminating on $\{x_E=x_P,\,y_E=0\}$. In $R_{1,2}$ the aim point is $I=(0,y_I)$ with $y_I$ from Eq. (13); Theorem 2 gives all three **constant optimal headings** in both frames (so straight lines in the realistic plane too), and the value function is $V=\sqrt{x_P^2+y_I^2}$ — the closed-loop flow is a straight-line field converging on the origin.

## Method
Purely geometric — Isaacs' Apollonius construction, no HJI solve and no costate integration. Constant costates (holonomic dynamics + time payoff) motivate the guess that the optimal flowfield is straight lines, and the rest is circle algebra: intersecting $C_1,C_2$ is a quadratic, and the aim point $I$ is the intersection point **farthest from $E$**. Theorem 1 is proved by computing $I$ antipodal to $E$ on $C_1$ (Eq. 9) and asking when it crosses $C_2$ — the critical configuration $I\in C_2$ is what yields $x_E=\mu x_P$.

## Key Terminology
- **BSR** — boundary of the safe region for $E$ (the Apollonius lens, or "thick lens" when one pursuer is inactive).
- **Aim point $I$** — the point of the BSR farthest from $E$; all three players head for it.
- **Redundant / irrelevant pursuer** — one whose Apollonius disk contains the other's; the game devolves to 1v1 pure pursuit.
- **Pincer movement / isochronous capture** — both pursuers arrive at $I$ simultaneously.
- **Elliptical cones $K_1,K_2$** — the circles-don't-intersect sets; the *wrong* answer, retained as the paper's cautionary object.

## Connections to Prior Literature
- **Weintraub, Pachter & Garcia (2020) §IV — the same construction, same author.** Weintraub's aimpoint $I$ as the Apollonius intersection is this paper's machinery; this Note is the fuller treatment and supplies the partition Weintraub does not.
- **Makkapati, Sun & Tsiotras (2018) — the complementary half.** Both derive simultaneous capture rather than imposing it, but Makkapati's pursuers run *prescribed* laws (a one-sided OCP) while here both sides optimize. Cited as Ref. [6].
- **Hayoun & Shima (2017) — opposite verdict on cooperation, and the models explain why.** Here the pincer is genuinely cooperative and the aim point depends on both pursuers; there, two *strong* pursuers each run the unchanged 1-on-1 law and cooperation is "not beneficial." Cooperation pays exactly when neither pursuer is individually sufficient.
- **Merz (1972) / Getz & Pachter (1981) — the opposite end of the modelling axis.** Same "which player is active" question, but those buy turn limits and pay with numerical retrogression; simple motion is what makes closed form available here.

## Limitations / Open Questions
- **One-sided, simple motion, point capture, fixed roles** — no mutual kill, no WEZ, no turn limit, no heading state. Casts **no vote** on the mutual-kill codimension question, and its partition is over *which teammate acts*, not over outcomes.
- **The authors' own extension list is the useful part:** unequal pursuer speeds; the degenerate $\mu_2=1$ case (Apollonius circle → perpendicular bisector); and, most relevantly, **finite capture radii $l_1,l_2>0$, which replace the Apollonius circles by Cartesian ovals and make the $R_1/R_2/R_{1,2}$ boundary non-planar.** Unworked.
- **Isochrony is an output here, not a constraint** — nothing enforces it, so it is Layer 3 background.
- **Bibliography: 17 refs, mostly the simple-motion Nv1 cluster already covered.** The only items not already recorded are Ibragimov's integral-constraint papers ([11], [15], [16]) — off the ladder.

## Relevance to My Research
Structurally the closest reviewed analogue to **§5.3 and §5.4**: an outcome partition *over a team*, answering "which teammate does the work, and when is the pair genuinely needed?" — the question Layer 2 asks with lethality on both sides. Two transferable items. First, the **cautionary result**: the obvious sufficient-looking geometric condition for cooperative capture is not the right one, and the correct boundary is simpler than the wrong one (planar wedge vs. elliptical cone) — a warning against reading a 2v1 outcome boundary off the naive intersection test, which is exactly the kind of shortcut a four-target-set Layer 2 construction invites. Second, the **unworked finite-capture-radius extension**: the moment capture sets acquire size, the partition boundary stops being planar — the cheapest available statement of what target-set *geometry* does to a team partition, and a hint that Layer 2's boundaries will not be tidy. Everything else here — holonomic, one-sided, point capture — is too far from v0.2's model to transfer.
