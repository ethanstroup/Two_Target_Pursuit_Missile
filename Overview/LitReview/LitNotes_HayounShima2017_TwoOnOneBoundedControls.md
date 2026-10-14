# Hayoun & Shima, 2017 — A Two-on-One Linear Pursuit–Evasion Game with Bounded Controls

## Citation
Hayoun, S. Y., and Shima, T. (2017). *A Two-on-One Linear Pursuit–Evasion Game with Bounded
Controls.* Journal of Optimization Theory and Applications, 174(3), 837–857.
DOI 10.1007/s10957-017-1142-z. Dept. of Aerospace Engineering, Technion.

## Problem Framing
- **Game type:** zero-sum **game of degree** — a cost, a value $J^\ast$, closed-form optimal feedback
  for all three agents. No game of kind is posed, but a partition falls out anyway: retro-time
  propagation fills the space with regular zones, and the leftover voids are the singular zones.
- **Agent structure:** 2 pursuers vs. 1 evader, the **team collapsed into a single player holding two
  controls** — which is what makes a two-person zero-sum formulation available at all. Roles are inputs.
- **Lethality: one-sided.** Only the pursuers can win; the evader only maximizes miss. **The paper
  lands on the team-structure side of the gap, not the bidirectional side** — it does not close it.
- **Dynamics:** planar endgame **linearized about a common reference line** (all three near head-on or
  tail-chase), constant speeds, bounded lateral acceleration with **first-order lag**. An acceleration
  bound, not a turn limit; no heading state.
- **Kill geometry:** none in the WEZ sense — capture is a scalar terminal miss, isotropic, all-aspect.
- **Dimensionality / method:** 7 states reduced by the **terminal projection transformation** to two
  zero-effort-miss coordinates, giving the game space $(Z_1,Z_2,\theta)$, $\theta=t_{go}/\tau_E$;
  two-sided PMP, then closed-form retro-time propagation.
- **Synchronization: a precondition on initial geometry, not a constraint on play.** $t_{f_1}=t_{f_2}$
  reduces to $x_1^o/x_2^o=V_{c_1}/V_{c_2}$, arranged by salvo launch or a mid-course phase *before* the
  endgame. **This corrects the original premise for reading it**, which had the paper as the closest literal
  match to a synchronization constraint.

## Core Contribution
**A new cost — the product of the two miss distances,** $J=|y_1(t_f)|\cdot|y_2(t_f)|$ — argued against
both standard choices on the grounds that each misrepresents somebody's interest. $J_{\min}$ reflects
the evader's goal but makes the outcome depend on one pursuer only, leaving a marginally
less-threatening pursuer with no unique optimal strategy; $J_{\text{sum}}$ gives every pursuer
something to do but does not reflect the significance of the minimum. The product interpolates: like
the sum when the misses are comparable, like the min when one pursuer dominates.

**A full solution for two "strong" pursuers** — strong meaning advantage over the evader in *both*
maneuverability ($\mu_i>1$) and **agility** ($\mu_i\varepsilon_i>1$). Three singular zones emerge. The
central **capture zone** $\mathcal D_0$ has $J^\ast=0$, all three controls non-unique, and a
semipermeable boundary — a trajectory may enter it off a non-optimal evasive maneuver, but one starting
inside never leaves. Its **enlargement region** $\Delta\mathcal D_0$ holds states in neither pursuer's
own 1-on-1 capture zone from which the pair still captures, and requires $Z_1Z_2<0$: the evader must be
predicted to terminate *between* the pursuers. The novel object is the pair of **no-escape zones**
$\mathcal D_0^E$, where the pursuers **guarantee equal misses regardless of what the evader does** and
it is the evader whose control is non-unique.

**The conclusion drawn from it: cooperation between "strong" pursuers is not beneficial.** The optimal
pursuit law $u_{P_i}^\ast=\operatorname{sign}\{Z_i\}$ is the **unchanged 1-on-1 strategy** — each pursuer
chases its own zero-effort miss and ignores its partner; only the evader's law is elaborate. The
enlarged capture zone and the NEZ are said twice to follow from the *presence* of a second pursuer,
not from coordination.

## Method
Two-sided PMP is admissible because the reduced dynamics are separable in the controls. The
Hamiltonian is linear in all three controls, the adjoints are **constant**, and transversality on the
product cost gives $\lambda_i(0)\propto\operatorname{sign}\{Z_i(0)\}|Z_j(0)|$ — **each pursuer's
adjoint scaled by the *other* pursuer's miss**. That is the entire mechanism by which the product cost
couples them, and why the evader's law depends on both NZEMs while the pursuers' do not. Play is
bang-bang; Appendix B reads the evader's behaviour out of the sign algebra — evade the most threatening
pursuer, singular when $|Z_1|=|Z_2|$, the analytic origin of the NEZ. Optimality is certified by
showing candidate trajectories never intersect, **not** by HJI verification — a route available only
because linearization makes every trajectory closed-form.

## Key Terminology Introduced
- **Zero-effort miss (ZEM)** $z_i$ / **normalized ZEM** $Z_i$ — the miss if nobody controlled from now
  on; here, the reduced state itself.
- **Product cost**; **"strong" pursuer** (maneuverability *and* **agility**); **capture zone**
  $\mathcal D_0$, **enlargement region** $\Delta\mathcal D_0$, **no-escape zone (NEZ)** $\mathcal D_0^E$;
  **artificial universal line** (after Lewin), the CZ/NEZ boundary trajectory.
- **Singular zone** — the paper's own definition, worth keeping distinct from Isaacs': a void bounded
  by optimal trajectories emanating in retro-time from same-cost terminal states, inside which some
  player's strategy is indeterminate and $J^\ast$ is constant.

## Connections to Prior Literature
- **Davidovitz & Shinar (1989) — the complementary half of the gap.** D&S are bidirectional,
  turn-limited, aspect-dependent, 1v1; this is one-sided, acceleration-limited, isotropic, 2v1. They
  cover both axes and overlap on none, which makes the pair the cleanest citation for the gap.
- **Ganebny, Kumkov, Le Ménec & Patsko — agrees, by a different cost.** The paper reports its
  product-cost level sets coinciding with their $J_{\min}$ ones, because the evader maneuvers away from
  whichever pursuer achieves the smaller miss anyway — so the two costs differ less in consequence than
  the motivating argument suggests.
- **Makkapati (2018), Pachter et al. (2019), Weintraub §IV — same cluster, three relationships to
  synchronization.** Derived from optimal play in the first two, imposed as a terminal constraint via
  Weintraub's Apollonius aimpoint, and a precondition on initial geometry here. All one-sided.
- **Merz (1972), Getz & Pachter (1981), Olsder & Breakwell (1974) — same vocabulary, inverse
  construction.** That lineage sweeps a barrier from a usable part; this propagates from *every*
  terminal state and takes the singular zones as the voids left over.

## Limitations / Open Questions
- **Only the "strong pursuer" case is solved**, and the assumption is load-bearing throughout the
  appendices. The cooperation claim is scoped to it.
- **Synchronization is assumed, not achieved** — no cost term for it, nothing maintaining it.
- **Linearized and one-sided:** no heading state, turn limit or aspect dependence, hence no WEZ or
  two-target structure, no mutual kill, no role determination.
- Noticed in passing, none of it propagating: Eq. (30) carries $\mp$ where its own Eq. (27) and Lemma
  4.1 give $\pm$; Fig. 9's caption names $\mathcal D_0$ where the text says NEZ; and $\varepsilon_1$ is
  $2$ in the Figs. 3–6 captions but $1$ in the Sec. 4.3 simulations, unremarked.
- Lemma 4.2's proof cites propositions giving positivity, not the bound claimed. The bound holds at the
  plotted parameters and looks like it fails when one pursuer far outclasses the other — worth a check
  before leaning on the result for very unequal pursuers.
- Bibliography (17 items) harvested and exhausted.

## Relevance to My Research
The **product cost's motivating argument** — not its algebra, which needs a continuous miss — is a live
candidate for the §5.4 team objective, since "depends on the best attacker only" and "sums away the
decisive outcome" are exactly the traps in ordering win / trade / mutual kill / draw. Its **"cooperation
is not beneficial" result is the standing null hypothesis**: a Layer 2 team benefit has to beat two
attackers independently running the D&S 1v1 strategy. And its NEZ is the same *shape* of claim as
§5.3's $|\Delta|>2\beta$ — a team guarantee irrespective of the lone agent — but reached with no
coordination at all, which is what makes §5.3 worth attacking early.
