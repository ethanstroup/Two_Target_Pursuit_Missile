# Merz & Hague, 1977 — Coplanar Tail-Chase Aerial Combat as a Differential Game

> **Revision note (2026-09-03):** This note supersedes the version drafted in overnight run 1. That draft was produced entirely from NASA CR-137809 read through a lossy PDF-to-text tool, and reported the numerical example's speed ratio as $V_B=0.90\,V_A$. **This was wrong.** Ethan supplied the actual AIAA Journal article (the paper itself, not a precursor), and it gives $V_A=1400$ fps, $V_B=700$ fps — a ratio of exactly $0.5$. Every other parameter in the CR reading matched the journal exactly ($H_A=30°$, $H_B=40°$, $\omega_{B,\max}/\omega_{A,\max}=1.1$), which is what exposed the error: one number out of six being different pointed to a transcription slip, not a different example. The speed ratio has been corrected throughout, several other markers have resolved now that the primary source is in hand, and new content from the journal article (numerical results, conclusions, dispersal-point discussion) has been added. Sections below note which source each claim comes from.

## Citation

**The paper — now read directly:**
Merz, A. W., and Hague, D. S., "Coplanar Tail-Chase Aerial Combat as a Differential Game," *AIAA Journal*, Vol. 15, No. 10, October 1977, pp. 1419–1423. DOI: 10.2514/3.7436.

**Precursor, read in overnight run 1 (free, NASA NTRS):**
Merz, A. W., and Hague, D. S., *A Differential Game Solution to the Coplanar Tail-Chase Aerial Combat Problem*, NASA CR-137809, Aerophysics Research Corporation, prepared for NASA Ames under Contract NAS2-8844. The journal article's own reference list dates this **January 1976** — resolving the earlier discrepancy between the report's cover date (1975) and NTRS's metadata (1976) in favor of 1976.

**Relationship between the two documents, now clarified:** the journal article is a condensed, peer-reviewed version of the same study. It explicitly defers the full equations of motion and adjoint equations to "Refs. 1, 5" — Isaacs' book and the CR itself — printing only the resulting optimal control laws (Eq. 3) rather than the derivation. So the CR remains the only source for the equations of motion; the journal article is the higher-confidence source for everything else, since it was read directly rather than through a text-extraction tool.

## Problem Framing

- **Game type:** Game of kind only, solved by two role-reversed barrier constructions — one for "A pursues B," one for "B pursues A." The paper states this scope explicitly: "Optimal (min-max) time strategies of both pursuer and evader would be a natural next step in the problem when either $A$ or $B$ can win, but this extension is not undertaken here." So the CR-derived note's uncertainty about whether a value function appears anywhere is now resolved — it doesn't; the game of degree is named and explicitly deferred.
- **Agent structure:** 1v1, no cooperation. Both aircraft turn-rate limited and both armed (bidirectional lethality, same structure as Getz & Pachter and Davidovitz & Shinar), reached through the "two barriers, one per role assumption" device. The paper's own framing is **role determination** — pursuer/evader is an output of the geometry, not an input.
- **Corrected numerical example.** The paper states its parameters directly: $V_A=1400$ fps, $\omega_{A,\max}=10$ deg/sec, $V_B=700$ fps, $\omega_{B,\max}=11$ deg/sec, $H_A=30°$, $H_B=40°$. **This is a substantially asymmetric pairing, not a near-symmetric one** — $A$ is twice as fast as $B$ but slightly less maneuverable (minimum turn radii 8020 ft vs. 3650 ft; normal accelerations 7.6g vs. 4.2g in a hard turn). The paper is explicit that this is a chosen illustrative case, not a general result: "these parameters do not apply to specific aircraft, but will guarantee that the 'draw' condition occurs."
- **Dimensionality:** planar relative motion, three states $(x,y,H)$ — relative position and relative heading, in axes fixed to $A$. The paper states the state and adjoint equations are given in Refs. 1 and 5 (Isaacs; the CR) and does not reprint them.

## Core Contribution

A computed **role-determination map**: for the chosen numerical parameters, the $(x,y)$ plane at each fixed relative heading $H$ is partitioned into "A wins," "B wins," and "draw" regions (Fig. 4, $H=0°,20°,30°,45°,50°,55°$). The paper's headline claim, stated plainly in the Introduction: **for the majority of possible initial conditions, neither aircraft can win if the other turns optimally** in certain critical geometries.

Confirmed directly from the text (not inferred, not passed through a summarizer):

- **The draw region's cause is asymmetry, not symmetry — and the paper flags this as untested.** "In the similar problem analyzed in Ref. 2 [Olsder & Breakwell], both forward-firing weapons had finite ranges and no terminal heading requirement was imposed. The draw region existed in this solution because the faster aircraft could remain out of range of the slower, which had the larger weapon range. In the present problem, if the faster aircraft were also more maneuverable, the draw region would presumably disappear, **but this has not yet been verified quantitatively.**" This is a hypothesis the authors state and do not check, not a result.
- **A total of 16 terminal configurations** (Table 1 plus the 4 collision cases in Fig. 3): 6 near-miss with $A$ pursuing, 6 near-miss with $B$ pursuing, 4 collision. Table 1's columns are final turn direction (A, B) and final heading condition. This resolves the earlier open question about what distinguishes the 16 cases.
- **The bang-bang/three-maneuvers tension is resolved.** For these parameters, "the assumption of infinite weapon range prevents singular arcs... by either $A$ or $B$ from appearing in the solution." A singular arc — the third maneuver — would occur when either bracketed switch-function argument in Eq. (3) is zero for a finite time; infinite weapon range rules this out here. So bang-bang is complete only *for this parameter choice*, not as a general feature of the model.
- **The collision barrier is confirmed, in the paper's own words, to be a measure-zero role-reversal surface, not a region.** "The collision barrier can be more practically interpreted as a locus across which the roles of pursuer and evader are reversed, and the representation of each aircraft as a point means that this locus in the three-dimensional state space is a **two-dimensional surface** separating distinct regions in this state space from one another." This independently confirms Davidovitz & Shinar's later "mutual kill is a knife-edge, not a volume" result, by a different route and 12 years earlier.
- **Dispersal points appear explicitly**, at corners where the barrier's slope is discontinuous and two different maneuver sets are both optimal — the evader typically chooses which, forcing a unique pursuer response. Corners also occur where the two aircraft's kill regions intersect, and roles are indeterminate there, same as at the collision barriers.
- **A cheap baseline guidance law, stated in the Conclusions:** "turn hard toward your opponent" reproduces most optimal barrier maneuvers regardless of role. The exceptions — "turn hard away" — occur only at short range, where each aircraft is inside the other's minimum-turn circle, and the paper calls this the source of "some of the important conclusions of the study."

## Method

**Isaacs' barrier construction via retrograde integration from 16 terminal configurations**, using the control laws given explicitly in Eq. (3):

$$\omega_A = \omega_{A,\max}\,\mathrm{sgn}\big[V_x y - V_y x + V_H\big],\qquad \omega_B = \omega_{B,\max}\,\mathrm{sgn}[V_H]$$

This is an exact match to what the CR-derived note transcribed as $S_A=\lambda_x y-\lambda_y x+\lambda_H$, $S_B=\lambda_H$ — the CR's switch-function transcription was correct, at least in form, even though the CR reading's EOM had a flagged sign problem elsewhere. **The equations of motion and adjoint equations are not printed in this article** — deferred to Isaacs and to the CR — so the polar-coordinate sign question raised in run 1 still cannot be settled from this document; it requires the CR pages directly.

**Terminal conditions**, given explicitly:
$$x_f=0,\ y_f>0,\ |H_f|\le H_A \quad\text{(A wins)}\qquad\qquad x_f=y_f\tan H_f,\ y_f<0,\ |H_f|\le H_B \quad\text{(B wins)}$$

**Numerics:** retrograde integration of state and adjoint equations from the 16 terminal configurations, producing barrier segments in $(x,y)$ at fixed $H$. No integration scheme, step size, or tolerance is reported — consistent with the CR's account of a heavily interactive, non-automated solution process, though the journal article doesn't repeat that discussion.

## Key Terminology Introduced

- **Role determination** — pursuer/evader identity as an output of relative geometry and vehicle parameters, not an input; the paper's stated central problem.
- **Tail-chase / heading-limited termination** — $|H_f|\le H_A$ (or $H_B$) with **range unconstrained**; a purely angular capture condition. Confirmed directly: "even when the range is unconstrained, both pilots wish to control *two* of the state variables, but they have only their turn rates as input controls."
- **Draw region** — where neither aircraft's kill region reaches the other; both can evade indefinitely. Caused here by complementary asymmetry (faster-but-less-maneuverable vs. slower-but-more-maneuverable), not by symmetry — a distinction the run-1 draft blurred.
- **Dispersal point** — a barrier corner where two maneuver sets are simultaneously optimal and the evader's choice forces the pursuer's response.
- **Collision barrier** — the surface built from simultaneous-kill terminal conditions; a two-dimensional role-reversal surface in the three-dimensional state space, not an outcome region.
- **Double-subscript maneuver notation** (e.g. $B_{RL}A_L$) — confirmed as: first aircraft's turn sequence (first direction, then second), followed by the other aircraft's single sustained direction. This clarifies the CR's $A_{LR}B_R$-style notation, though the specific $ALR$/$ARL$ labels in the CR's Fig. 5.3 are still not individually confirmed against this article.

## Limitations / Open Questions

- **Not the fully symmetric case, and now more clearly not even close.** $V_A=1400$ fps vs. $V_B=700$ fps is a 2:1 speed ratio — substantially asymmetric, not "near-symmetric but deliberately off-symmetric" as the run-1 draft characterized it. The genuinely identical-vehicle case remains Merz (1972/1976), "The Game of Two Identical Cars" — still unread when this note was written.
- **The paper's own draw-region causal claim is untested.** They state that equal maneuverability alongside the current speed difference would presumably eliminate the draw region, and say explicitly this has not been verified quantitatively. Worth remembering when reading Merz (1972): if draw dominates there too, under genuine symmetry, that's a materially different and more informative result than this paper's hedged conjecture.
- **Terminal condition is angular-only, no range gate, not WEZ/cardioid geometry.** Confirmed directly and unchanged from the CR reading — both kill regions are of infinite extent for the relevant heading ranges, an explicit consequence of assuming unbounded weapon range. The paper notes that with finite weapon ranges on both sides, "both of the aircraft's actual kill regions will be finite," and that this is the situation in which "the pilot who can apply the optimal defensive maneuvers can evade the other indefinitely" — a bounded-range case the paper flags as of interest but does not solve.
- **Equations of motion remain unverified against a page.** The journal article confirms the switch-function *form* but does not print the EOM or adjoint equations, so the CR's polar-coordinate sign question (Sec. 3.3) is still open and can only be resolved by reading the CR pages directly rather than any summarized extraction of it.
- **Fore/aft vs. lateral axis labeling in the CR's Fig. 5.1 series** — not addressed by this article; still requires the CR figures directly.
- **1v1 only.** Explicitly framed as the one-on-one problem throughout; no multi-aircraft extension, no cooperation, no synchronization — this paper contributes to the mutual-kill/bidirectional-lethality side of the literature, not the cooperative-multi-pursuer side.
- **Constant speed, coplanar motion** — the paper names both as its two immediate self-criticisms, and offers a retroactive justification for constant speed (barrier maneuvers are brief, usually under a quarter-turn, so speed stays nearly constant even under sustained maximum turn rate) without a quantitative error bound.

## New leads from this reading

- **Merz, A. W., "The Homicidal Chauffeur," *AIAA Journal*, Vol. 12, March 1974, pp. 259–260.** A 2-page item, cited as Ref. 4. Distinct from Merz's 1971 PhD thesis of the same title already sitting in harvested candidates — worth checking whether this is a summary of the thesis or an independent short communication.
- **Confirms Merz (1976) as a real, distinct citation**, not a guess: "Merz, A. W., 'The Game of Two Identical Cars,' *Multi-criteria Decision-Making and Differential Games*, ed. G. Leitmann, Plenum Press, New York, 1976, Chap. XXVI, pp. 421–442." Plenum was later absorbed into Springer, which is consistent with the DOI the scout found under a Springer imprint. Still not verified as textually identical to the 1972 JOTA article — same title, same author, different venue.
- **Olsder & Breakwell year confirmed as 1974** in this reference list, agreeing with Springer and resolving the CR-vs-Springer date discrepancy in Springer's favor.

## Connections to Prior Literature

[PENDING — REVIEW WITH ETHAN]

## Relevance to My Research

[PENDING — REVIEW WITH ETHAN]
