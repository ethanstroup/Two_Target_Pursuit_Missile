# Build Spec v2: Interactive Two-Target Mutual-Kill Game Demo

**Source paper:** Davidovitz, A., & Shinar, J. (1989). "Two-Target Game Model of an Air
Combat with Fire-and-Forget All-Aspect Missiles." *JOTA*, Vol. 63, No. 2, pp. 133–165.

**Revision note (v2):** All equations, parameters, and figure references below have been
checked against the source PDF. Several items in v1 were either incorrect or would have
produced silent numerical failures; those are marked **[v2 FIX]** where they appear.

---

## 0. Goal and honest scope

Build an interactive HTML/JS visualization where the user clicks a starting state in the
reduced $(\phi_1, \phi_2, R)$ space of the paper's two-target game and watches a forward
simulation under a *pure-pursuit heuristic* play out to termination.

**[v2 FIX] What this demo actually demonstrates.** v1 framed this as "illustrating the
paper's game-of-kind winning-zone predictions." That claim is only defensible at short
range. Empirically (see §9 for the measurements):

- **At short range ($R_0 \lesssim 2$):** the heuristic's winner agrees with the paper's
  characterization of its dominant winning subregion — the player with the angular
  advantage, $|\phi_i| < |\phi_j|$, wins — in essentially every decisive case.
- **At long range ($R_0 \gtrsim 8$):** the heuristic *inverts* that rule, and the
  mutual-kill fraction balloons to 19–87%, whereas the paper's actual mutual-kill set is
  four measure-zero semipermeable surfaces and the draw zone is nearly the whole space.

The long-range inversion is not a numerical bug. It follows directly from the paper's own
target-set model: $\bar R_i$ depends on the **opponent's** aspect angle $\phi_j$, so
turning nose-on to your opponent maximizes *his* no-escape envelope against you. Under
symmetric pure pursuit, whoever gets nose-on first gets shot first.

Therefore the demo should be presented as: **"what naive pure pursuit does against a
fire-and-forget-armed opponent, and where it diverges from the paper's optimal barrier
strategy"** — not as an approximate reproduction of Fig. 14. The divergence is the
interesting part and should be surfaced, not buried.

**Why no exact solution is available.** The paper derives the rigorous optimal control law
only *along constructed barrier trajectories*, where costates are seeded by the
transversality condition (Eq. 20) at the boundary of the usable part (BUP) and integrated
backward via Eqs. (17)–(19). It supplies no global closed-loop feedback law for arbitrary
interior points, because in a qualitative (game-of-kind) solution the strategies inside
each winning zone are by definition arbitrary.

---

## 1. State space and dynamics

Reduced state: `x = (R, φ1, φ2)`, with $R \ge 0$ the normalized range and
$\phi_1, \phi_2 \in [-\pi, \pi]$ the off-boresight angles of the line of sight in each
player's own body frame.

Dynamics (Eqs. 1–3 of the paper, verified):

```
Ṙ   = -(cos(φ1) + cos(φ2))
φ̇1 = (sin(φ1) + sin(φ2)) / R + σ1
φ̇2 = (sin(φ1) + sin(φ2)) / R + σ2
```

The shared first term is the line-of-sight rate $\dot\psi = (\sin\phi_1+\sin\phi_2)/R$
(Eq. 5). Controls: $|\sigma_i| \le 1$ (Eq. 4), normalized turn rate.

Integrate with fixed-step RK4, `dt = 0.01` (normalized time units).

### [v2 FIX] Angle wrapping — required, not optional

**After every integration step, wrap `φ1` and `φ2` back into `[-π, π]`, before running any
target-set or termination check.**

This is not cosmetic. The dynamics will drive $\phi$ past $\pm\pi$, and the maximum-range
formula (Eq. 9 below) uses $|\phi_j + \sin\phi_j|$ **unwrapped**. Without wrapping,
$\bar R$ decreases without bound and eventually goes negative, at which point the target
set becomes silently unreachable and the sim reports spurious draws.

```js
const wrap = a => ((a + Math.PI) % (2*Math.PI) + 2*Math.PI) % (2*Math.PI) - Math.PI;
```

### [v2 FIX] Units

**All internal state, dynamics, and target-set math is in radians.** The UI displays and
accepts degrees. Convert at the boundary only. Eq. (9)'s $|\phi_j + \sin\phi_j|$ term is
correct *only* in radians — a degree/radian mix here will not throw an error, it will just
produce a wrong (and plausible-looking) target set.

### Numerical guard

Guard `R` away from exactly 0 (it appears in a denominator). If `R < 0.01` without having
already terminated in a target set, stop and report **"numerical edge case (R→0)"** — this
is *not* a game outcome and must be labeled distinctly from a draw. It occurs for a small
number of very-short-range initial conditions.

---

## 2. Target sets (Eqs. 6–9)

For each player `i = 1, 2` with opponent `j ≠ i`:

```
Boresight limit (Eq. 6):     -β ≤ φi ≤ β          ← player i's OWN angle
Range bounds    (Eq. 7):     R̲i(φj) ≤ R < R̄i(φj)  ← the OPPONENT's angle

R̲i(φj) = a + b·cos(φj)                (Eq. 8, minimum firing range)
R̄i(φj) = R̄0 - |φj + sin(φj)|          (Eq. 9, no-escape / maximum range)
```

The index asymmetry is the easiest thing to get wrong and is correct as written above:
the boresight constraint is on **player $i$'s own** off-boresight angle, while both range
bounds depend on the **opponent's** aspect angle $\phi_j$. Note the inequality in Eq. (7)
is non-strict on the lower bound and strict on the upper.

**Worked-example parameters, from Section 4 of the paper** (modelling combat at
$h = 3$ km, $V = 360$ m/s, $n_{max} = 6$, giving turn radius $\rho = 2200$ m):

```
β  = 45°  = π/4  = 0.785398 rad
R̄0 = 6.14   (Table 2 uses the more precise 6.1416 = 3 + π; either is fine)
a  = 0.55
b  = 0.30
```

`T1` and `T2` are defined symmetrically — identical missiles on both sides, so swap which
player's $\phi$ plays which role.

**Sanity checks against the paper's Table 2** (implement these as unit tests):

| Quantity | $\phi_j$ | Expected |
|---|---|---|
| $\underline R$ | 0° | 0.85 |
| $\underline R$ | ±180° | 0.25 |
| $\bar R$ | 0° | 6.14 |
| $\bar R$ | ±180° | 3.00 |

**[v2 note — do not "correct" a and b.** Appendix A of the paper states
$R_{\min}(\phi=0) = 199$ m, which normalizes to 0.09 and is inconsistent with $a+b=0.85$.
That printed value is a typo (almost certainly 1900 m → 0.86 ≈ 0.85); $R_{\min}(\pi) =
550$ m → 0.25 checks out fine. The values $a=0.55$, $b=0.3$ are correct and are confirmed
independently by Table 2. Do not adjust them to match the Appendix A line.]

### Termination check, every step (Eqs. 10–11)

Evaluate **after** wrapping, in this order:

1. State in `T1 ∩ T2` → **mutual kill**
2. State in `T1` only → **player 1 wins**
3. State in `T2` only → **player 2 wins**
4. `R < 0.01` → **numerical edge case** (not an outcome)
5. No termination by `t = 30` → **draw**

Checking the intersection first is required so simultaneous entry is classified as mutual
kill rather than being assigned to a player by check order.

---

## 3. [v2 FIX] Initial-state admissibility

The paper defines the set of admissible initial conditions as the entire game space
**excluding** $T_1 \cup T_2$ (Section 2, following Eq. 12). v1 omitted this, and the
omission is severe: on a uniform grid of clicks, the fraction of the $(\phi_1,\phi_2)$
plane already inside a target set at $t=0$ is

| $R_0$ | already terminal at $t=0$ |
|---|---|
| 1.5 | **45%** |
| 3.5 | **20%** |
| 8.0 | 0% |

**Requirement:** shade the $T_1$, $T_2$, and $T_1 \cap T_2$ regions at the current $R_0$
on the plot background, and either reject clicks inside them or accept them while
immediately reporting "initial state already terminal — not an admissible initial
condition." The target sets are analytic in $(\phi_1,\phi_2)$ at fixed $R$, so this is
cheap to render and doubles as the click mask.

---

## 4. Heuristic control law

Bang-bang, mirroring the *form* of the paper's optimal law but substituting a locally
computed heuristic for the true costate:

```
σ1 = -sign(φ1)      (σ1 = 0 when φ1 = 0)
σ2 = -sign(φ2)      (σ2 = 0 when φ2 = 0)
```

Each player turns to reduce his own off-boresight angle — pure pursuit toward his own
weapons envelope. The `φi = 0 → σi = 0` case avoids sign-function chatter.

This is intentionally simple and symmetric, and is **not** derived from the paper's
mathematics away from the barrier.

---

## 5. Visualization layout

Primary view: 2D plot, $\phi_1$ on one axis and $\phi_2$ on the other, each spanning
[-180°, 180°].

- User sets starting `R0` via slider or numeric input. **[v2 FIX] Default `R0 = 1.75`.**
  v1 suggested 3–4, which is the worst available choice: it sits in the transition between
  the two behavioral regimes *and* leaves ~20% of clicks instantly terminal. A default
  near 1.5–2.0 puts the user in the regime where the heuristic actually tracks the paper's
  angular-advantage result. Let the slider range up to ~12 so the long-range inversion is
  explorable.
- Click-to-place a starting $(\phi_{1,0}, \phi_{2,0})$ at that `R0`, subject to the
  admissibility mask from §3.
- Animate the forward trajectory as a moving point with a trail.
- Show `R(t)` as a secondary readout (numeric, or a small time-series plot) since it is not
  visible in the 2D projection.
- Draw the $\beta$ boundaries and the shaded $T_1$/$T_2$/$T_1 \cap T_2$ projections at the
  current `R0`. **These update live as `R0` changes** — that animation is itself
  informative, since it shows how the reachable kill geometry opens and closes with range.
- On termination, label the outcome clearly: "Player 1 wins", "Player 2 wins", "Mutual
  kill", "Draw (no termination)", or "Numerical edge case (R→0)".

---

## 6. [v2 FIX] Required UI disclosure

Persistently visible (fixed caption or always-open info panel, not a dismissible tooltip).
Two parts — v1's version was incomplete on the second:

> **Illustrative pursuit heuristic (σᵢ = −sign(φᵢ)).** This is not the paper's
> proven-optimal control law. Davidovitz & Shinar derive optimal barrier strategies only
> *along constructed barrier trajectories*: σᵢ\* = −sign(λᵢ) for the pursuer and
> σⱼ\* = +sign(λⱼ) for the evader in each single-target subgame (Eqs. 21–22), with
> costates seeded by transversality at the BUP and integrated backward via Eqs. (17)–(19).
> No global feedback law is given.

> **Regime warning.** At short range this heuristic reproduces the paper's angular-advantage
> result (the player with smaller |φ| wins). At long range it *inverts* it, because a
> player's own no-escape envelope grows as his **opponent** turns nose-on — so mutual pure
> pursuit produces far more mutual kills than the paper's optimal solution, where the
> mutual-kill set has measure zero.

v1 cited only the pursuer half of Eqs. (21)–(22). Both halves belong in the disclosure,
since the sign difference is the whole min-max structure.

---

## 7. Suggested tech stack

Single-file HTML/JS. Plain canvas 2D is sufficient — no charting library needed for an
animated point plus static region shading. No backend; `requestAnimationFrame` drives the
RK4 stepper. Self-contained, no external dependencies.

---

## 8. Suggested file structure

```
index.html   — layout, controls (R0 input, click target, outcome readout, disclosure text)
sim.js       — dynamics, wrapping, target-set predicates, RK4 integrator, control law
render.js    — canvas: axes, β lines, T1/T2 shading, trajectory trail, outcome label
```

A single combined file is also fine at this size.

---

## 9. [v2 NEW] Acceptance checks

The build is correct if a 73×73 uniform grid of initial conditions over
$\phi_1, \phi_2 \in [-180°, 180°]$ (inclusive), with `dt = 0.01` and a 30-unit time
horizon, reproduces approximately these outcome fractions:

| $R_0$ | terminal at $t{=}0$ | P1 wins | P2 wins | mutual kill | draw |
|---|---|---|---|---|---|
| 1.5 | 45.3% | 21.2% | 21.2% | 1.4% | 10.8% |
| 5.0 | 6.1% | 45.0% | 45.0% | 4.0% | 0% |
| 8.0 | 0% | 40.5% | 40.5% | 18.9% | 0% |
| 12.0 | 0% | 6.5% | 6.5% | 86.9% | 0% |

Two structural invariants worth asserting in tests:

1. **Exact symmetry.** The P1-win and P2-win counts must be *exactly* equal, since the
   dynamics, target sets, and control law are all symmetric under $(1 \leftrightarrow 2)$.
   Any asymmetry indicates an indexing bug — most likely $\phi_i$ vs. $\phi_j$ swapped
   somewhere in Eqs. (7)–(9).
2. **Angular-advantage agreement.** Among decisive outcomes with $|\phi_1| \ne |\phi_2|$,
   the fraction where the winner is the player with the smaller $|\phi|$ should be ~100%
   at $R_0 \le 2$, ~87% at $R_0 = 5$, and ~1% at $R_0 = 8$. If short-range agreement is
   not near 100%, something is wrong. If long-range agreement is *high*, the wrapping fix
   (§1) or the $\phi_j$ indexing (§2) is probably not implemented correctly.

A small number of "numerical edge case (R→0)" results at $R_0 \approx 1.0$ is expected and
correct; they should not be counted as draws.

---

## 10. Out of scope for v1

**Overlaying the paper's actual $W_1$/$W_2$/mutual-kill/draw regions from Fig. 14.**

**[v2 FIX — v1 described this incorrectly.]** Fig. 14 is captioned *"Two-target game
solution, viewed from infinite $R$"*. It is a **silhouette projection of the full 3D
barrier surfaces down the $R$ axis**, not a constant-$R$ slice. Overlaying it directly on
the demo's fixed-$R_0$ plot would misrepresent the paper's result — the winning zones are
3D volumes, and a given $(\phi_1,\phi_2)$ point inside the Fig. 14 silhouette is in the
winning zone for *some* range of $R$, not for the specific $R_0$ on screen.

If pursued in v2, the overlay must be labeled as a projection, shown in a separate panel
from the constant-$R$ target-set shading, or reconstructed properly as a level set. Two
further digitization notes: Fig. 14's horizontal axis is $\phi_2$ running **+180° on the
left to −180° on the right** (reversed relative to the usual convention), and the vertical
axis is $\phi_1$ with +180° at the top.

**A more rigorous v3 direction:** reconstruct actual barrier trajectories by integrating
the costate ODEs (Eqs. 17–19) backward from digitized BUP points (Table 2 gives the
coordinates of significant points; Table 3 catalogs the singular lines), using the true
$\sigma_i^* = -\text{sign}(\lambda_i)$ / $\sigma_j^* = +\text{sign}(\lambda_j)$ laws, and
overlay those trajectories for direct comparison against the heuristic paths. The first
integral $(\lambda_1+\lambda_2)^2/R^2 + \lambda_R^2 = 1$ (Eq. 23) is available as an
integration check. This is the "barrier-exact verification" path, deferred in favor of the
heuristic-first build.
