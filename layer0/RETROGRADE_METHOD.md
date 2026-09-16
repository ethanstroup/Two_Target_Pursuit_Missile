# The Retrograde Construction, Surface by Surface

**AE 8900 · Layer 0 · 2026-09-16**
Base model: Davidovitz, A., and Shinar, J., "Two-Target Game Model of an Air Combat with
Fire-and-Forget All-Aspect Missiles," *JOTA* **63**(2), Nov. 1989, pp. 133–165.

How a barrier trajectory is generated, for each of the four surfaces that carry a boundary
of the usable part. Companion to `LAYER0_CLOSEOUT.md`, which records what the
reconstruction verified; this records *how it runs*. Implemented in `layer0/barrier.py`,
ported in `layer0/barrier.js`, seeded by `layer0/viz/bup_curves.py`, drawn by
`layer0/viz/visualize.py` and `layer0/viz/barrier_explorer.html`.

---

## 1. Why the integration runs backward

The barrier is a **semipermeable surface**: a surface in the state space
x = (R, φ₁, φ₂) across which the minimising player cannot be forced and the maximising
player cannot force passage. Isaacs' characterisation is local — at every point of the
surface there is a normal λ for which

```
H*(x, λ) = min max λ · f(x, σ₁, σ₂) = 0                                  Eq. (15)
            σ₁   σ₂
```

and the surface is swept by the trajectories that satisfy this together with the costate
equations

```
λ̇_R = (sin φ₁ + sin φ₂)(λ₁+λ₂)/R²                                        Eq. (17)
λ̇ᵢ  = −[λ_R sin φᵢ + cos φᵢ (λ₁+λ₂)/R]                                   Eqs. (18)-(19)
```

under the strategies that achieve the min-max,

```
σ₁* = −sign(λ₁),      σ₂* = +sign(λ₂)                                    Eqs. (21)-(22)
```

The difficulty is that this is a **condition, not an initial-value problem**. Nothing in
it says where a barrier trajectory starts. Asking for the barrier forward in time is a
two-point boundary-value problem: you would have to guess a costate at some interior state
and shoot until the trajectory happens to terminate correctly on the target-set boundary.

What *is* known outright is the terminal condition. A barrier trajectory ends on the
boundary of the usable part — the set of target-set boundary points from which the
outcome is still genuinely in dispute — and there the costate is not free. **Transversality
(Eq. 20) fixes it**: λ must be parallel to the outer normal of the target-set boundary at
that point, normalised by the first integral. So at every point of the (BUP) the entire
six-dimensional state–costate vector is determined in closed form.

That converts the boundary-value problem into an initial-value problem run in reverse.
Set τ = −t and integrate

```
dy/dτ = −f(y),     y = (R, φ₁, φ₂, λ_R, λ₁, λ₂)
```

from each (BUP) point. Every such run is a barrier trajectory, exactly, from the first
step. The **bundle** of them over the whole (BUP) is the barrier sheet.

This is why the (BUP) has to be produced as an *ordered curve* rather than a set of points:
the bundle is a surface parametrised by (arclength along the (BUP), τ), and neighbouring
seeds must be genuine neighbours on the barrier for that parametrisation to mean anything.

## 2. The machinery common to all four surfaces

Everything below is per-surface only in its seeding. Once seeded, all four families run
through the same integrator.

**Two invariants ride along, and they are the error estimate.**

```
FI = (λ₁+λ₂)²/R² + λ_R²  ≡ 1            Eq. (23) with C = 1
H* = min max λ · f       ≡ 0            Eq. (15)
```

`H*` is the sharper of the two and the reason to carry both. FI is conserved by the costate
ODEs **whatever the control does** — `verify_symbolic.py` shows the controls cancel
identically in d(FI)/dt — so FI cannot detect a wrong control. H\* can: it *is* the
semipermeability condition, so it fails the moment the strategy pair is wrong.

**The control is frozen over an RK4 step.** σ₁\* and σ₂\* are piecewise constant. Letting
each of the four RK4 stages re-read `sign(λ)` smears every switch across a whole step. FI
stays at 1e−14 while it happens; H\* drifts to 1e−3. Both facts together are what identified
the bug.

**Switches are located, not stepped over.** Each crossing of λ₁ or λ₂ through zero is
bisected out (60 iterations), the step is cut exactly there, the costate component is
snapped to zero, and the control is re-read past it.

**Where a costate component vanishes, the sign comes from its derivative.** This is not a
convenience: λ₁ = 0 identically on both range surfaces and λ₂ = 0 identically on both
boresight surfaces, so at *every* seed one of the two controls is undefined by
Eqs. (21)-(22) as written. Going backward, λ ≈ −τ λ̇_f to first order, so
sign(λ) = −sign(λ̇), and `barrier_controls` reads the sign from λ̇. That reproduces the
paper's own Eqs. (33) and (65) rather than assuming them — which is what makes the printed
control laws a *test* of the seeding rather than an input to it.

**Singular arcs are flagged, not chattered through.** On a universal line a costate
component stays at zero over an interval and the optimal control is intermediate rather
than bang-bang (Table 3 lists strategies such as (−1, 0) and (0, +1)). A bang-bang
integrator cannot represent that, so `integrate_retrograde` detects λᵢ ≈ 0 *and* λ̇ᵢ ≈ 0
together and returns them in its `singular` field.

**Seeds are put back exactly on the (BUP).** The seed curves are traced by continuation and
then resampled at equal arclength; linear interpolation between traced points lands
slightly *off* the defining root, which shows up as H\* ≈ 1e−5 at the seed. A seed that is
not semipermeable is not a barrier point, so the resampled φ₂ is re-solved for its root.
After that every seed carries |H\* | ≤ 4.4e−16.

---

## 3. Surface I — the maximum-range surface, R = R̄₁(φ₂)

**The surface.** The far edge of player 1's launch envelope, Eq. (9):

```
R̄₁(φ₂) = R̄₀ − |φ₂ + sin φ₂|,        R̄₀ = 3 + π = 6.141593
```

R̄₀ is `3 + π`, not the 6.14 quoted in Sec. 4 — see close-out §5.1. The outer normal is
n = (1, 0, (1 + cos φ₂) sign φ₂), from Eqs. (28)-(29).

**The boundary of the usable part.** The usable-part condition Eq. (13) evaluated on this
surface is Eq. (32); with equality it defines the (BUP):

```
R̄₁(φ₂)(1 − cos φ₁) + (sin φ₁ + sin φ₂)(1 + cos φ₂) sign φ₂ = 0,   |φ₁| ≤ β
```

**Terminal costate.** Eqs. (34)-(36), normalised by FI = 1:

```
p = 1/√(R̄₁² + (1+cos φ₂)²)
λ = p · ( R̄₁,  0,  R̄₁ (1 + cos φ₂) sign(sin φ₂) )
```

λ₁ = 0 identically, so σ₁\* comes from λ̇₁. λ₂ ≠ 0 off φ₂ = 0, and its sign gives
σ₂\* = sign(φ₂) directly — the paper's Eq. (31), recovered rather than assumed.

**What the curve looks like.** Solving Eq. (32) for φ₁ ∈ [−β, β] gives **two roots** at each
φ₂, which merge and vanish at |φ₂| = 9.5694°. The family therefore lives entirely inside
|φ₂| < 9.57°, and is a **closed lens**: out along the inner branch to the fold, back along
the outer one. `sign(φ₂)` in Eq. (32) makes φ₂ = 0 a genuine discontinuity of the root set,
so there are two mirror lenses, one per sign of φ₂, and together they form the S-curve
through the origin that Fig. 4 shows.

Both ends and the turn are published points:

| feature | solved here | Table 2 |
|---|---|---|
| φ₂ → 0 limit, inner branch | R 6.14119, φ₁ 0.011° | **O₁** (6.1416, 0°, 0°) |
| the fold | R 5.80833, φ₁ 18.923°, φ₂ −9.569° | **d₁** (5.808, 18.88°, −9.56°) |
| φ₂ → 0 limit, outer branch | R 6.14119, φ₁ 36.066° | **e₁** (6.142, 36.07°, 0°) |

The fold needs care. Near it the two roots separate like √(φ₂\* − φ₂), so a grid in φ₂ loses
them while they are still half a degree apart in φ₁, and the traced lens stops short of d₁.
`refine_fold` closes it by bisecting on *whether two roots still exist* and taking their
mean at the limit.

**Downstream.** This is the mildest family for the switching machinery: over 90 trajectories
the **first control switch does not occur until τ = 3.14**, and there are none at all below
that. At τ ≤ 6 there are 144. Residuals over the bundle: max |FI−1| = 7.5e−15,
max |H\*| = 3.4e−14.

---

## 4. Surface II — the minimum-range surface, R = R_min(φ₂)

**The surface.** The near edge of the envelope, Eq. (8), a cardioid-like curve in the
target's aspect angle:

```
R_min(φ₂) = a₁ + b₁ cos φ₂,     a₁ = 0.55,  b₁ = 0.30
```

The outer normal points *inward* in range: n = (−1, 0, −b₁ sin φ₂), Eqs. (43)-(44).

**The (BUP).** Eq. (46) with equality:

```
R_min(φ₂)(cos φ₁ + cos φ₂ + b₁|sin φ₂|) − b₁ sin φ₂ (sin φ₁ + sin φ₂) = 0,   |φ₁| ≤ β
```

**Terminal costate.** Eqs. (47)-(50):

```
pᵤ = 1/√(a₁² + b₁² + 2a₁b₁ cos φ₂)
λ  = −pᵤ R_min · ( 1,  0,  b₁ sin φ₂ )
```

Again λ₁ = 0, so σ₁\* comes from λ̇₁, and reproduces Eq. (52), σ₁\* = sign(sin φ₁).
λ₂ = −pᵤR_min b₁ sin φ₂ is non-zero, so σ₂\* = sign λ₂ = −sign(sin φ₂) directly — Eq. (45).

Eq. (50)'s printed form a₁² + b₁² + 2a₁b₁ cos φ₂ is *exactly* R_min² + b₁² sin²φ₂ —
re-derived symbolically, not assumed.

**What the curve looks like.** Two mirror branches, one per sign of φ₁. Each lives entirely
at **large aspect angle, |φ₂| ≥ 93.07°**, runs continuously **through φ₂ = ±180°**, and
terminates at both ends on the off-boresight limit φ₁ = ±β. φ₁ sweeps from ≈ ±44.8° down to
≈ ±2.66° at the seam and back. The ±π seam is a boundary of the *coordinate*, not of the
problem, so `bup_curves` merges the two runs across it and carries φ₂ unwrapped; drawn
without that step the branch appears to jump the width of the axes.

Both endpoints are published points, and they are precisely how the paper defines them —
"Eq. (46) = 0 at φ₁ = β":

| endpoint | solved here | Table 2 |
|---|---|---|
| φ₂ = 93.066° | R 0.53395, φ₁ 44.804° | **h₁** (0.535, 45°, 92.92°) |
| φ₂ = −161.037° | R 0.26628, φ₁ 44.843° | **g₁** (0.267, 45°, −160.9°) |

**Downstream.** This is by far the most switch-dense family — short range, high angular
rate, so λ₁ and λ₂ cross zero repeatedly. The **first switch is at τ = 0.05**, and 90
trajectories accumulate 376 switches by τ = 1.5, 816 by τ = 3, and 1686 by τ = 6. It is
therefore the family that actually exercises the frozen-control and bisected-switch
machinery, and the right one to regress against. Residuals stay at max |FI−1| = 1.6e−13,
max |H\*| = 1.7e−13.

---

## 5. Surfaces III and IV — the off-boresight limits, φ₁ = ±β

These are two distinct surfaces, not one, and the distinction is where the paper's Eq. (63)
goes wrong.

**The surfaces.** The launch envelope is bounded in the shooter's *own* look angle:
|φ₁| ≤ β, with β = π/4. Each limit is a plane in the state space. Outer normal, Eq. (59):

```
n = (0, sign φ₁, 0)
```

**The (BUP).** Eq. (62) with equality gives R in closed form — there is no root to solve:

```
R = (sin φ₁ + sin φ₂) sign φ₁
```

valid wherever that R falls inside the range band, R_min(φ₂) ≤ R < R̄₁(φ₂).

**Terminal costate.** λ must be parallel to n, so λ = μ(0, sign φ₁, 0), and the first
integral forces μ = R:

```
λ = ( 0,  R sign φ₁,  0 )
```

**This is not what Eq. (63) prints.** Eq. (63) gives λ₁f = (sin φ₁ + sin φ₂) sign φ₁, which,
using the (BUP) relation above, is one factor of sign(φ₁) more than R sign φ₁. The paper
decides against itself: Eq. (64) gives λ̇₂f = −(cos φ₂) sign φ₁, and from Eq. (19) with
λ_R = λ₂ = 0 one has λ̇₂ = −cos φ₂ · λ₁/R. The derived λ₁f gives λ₁/R = sign φ₁ and
reproduces Eq. (64); the printed one gives λ₁/R = 1 and produces −cos φ₂, contradicting it.
Eq. (65) then follows from Eq. (64), so the printed Eq. (63) is inconsistent with the two
equations immediately after it.

It is invisible on φ₁ = +β and it inverts the whole strategy pair on φ₁ = −β. Seeding with
Eq. (63) as printed makes **110 of 220 boresight seeds contradict Eq. (65)** — every one of
them at φ₁ = −β. That is a standing assertion in `test_barrier.py` and `test_barrier_js.js`,
and it is the reason these count as two surfaces in this document.

Here λ₂ = 0, so σ₂\* comes from λ̇₂ and gives σ₂\* = sign(cos φ₂) sign(φ₁) — Eq. (65),
recovered. λ₁ = R sign φ₁ ≠ 0, so σ₁\* = −sign(φ₁) directly.

**What the curves look like.** One branch each. φ₁ is fixed, so the curve is R(φ₂), and the
only structural work is finding where it leaves the range band and rejoining across the
seam. For φ₁ = +β it is admissible on φ₂ ∈ [8.218°, 180°] ∪ [−180°, −154.784°], which is one
arc through the seam. Both endpoints are the **corner with the minimum-range surface**, and
both are published:

| endpoint (φ₁ = +β) | solved here | Table 2 |
|---|---|---|
| φ₂ = 8.218° | R 0.85004 | **m₁** (0.847, 45°, 8.05°) |
| φ₂ = −154.784° | R 0.28108 | **N₁** (0.279, 45°, −154.6°) |

The φ₁ = −β surface is the mirror, running φ₂ = 154.784° → −8.218°. Table 2 tabulates only
player 1's points, so its endpoints are the untabulated primed mirrors — which is why the
`bore-` family reports zero Table 2 points while being numerically identical to `bore+`.

**Downstream.** Both boresight families behave identically: **first switch at τ = 1.92**,
none below it, 26 by τ = 3 and 100 by τ = 6 over 45 trajectories. Residuals are the largest
of the four but still small: max |FI−1| = 3.1e−14, max |H\*| = 4.0e−14 at τ ≤ 1.5, rising to
≈ 2.5e−9 at τ ≤ 6.

---

## 6. The corners, which is where the four families meet

Every branch endpoint above is a **corner** of the target-set boundary — a state where two
of the four surfaces meet and the outer normal is not unique. The maximum-range lens ends at
the φ₂ = 0 corner; the minimum-range branches end at the minimum-range/boresight corner
(g₁, h₁); the boresight branches end at the same corner from the other side (m₁, N₁). So the
four families are not four disconnected objects: they are arcs of one boundary, joined at
corners.

At a corner the gradient must be a **non-negative combination of the two adjoining outer
normals**. The paper supplies three closed forms for the multipliers (Eqs. 38-42, 53-58,
66-70), each a page of algebra.

`lam_corner` does not use them. It solves for the combination directly from the two
conditions the costate has to satisfy anyway — H\* = 0 and FI = 1 — which reduces to one
scalar equation in one angle. The paper's closed forms then become a *test* rather than an
input, and they pass to machine precision: 1.1e−15 at the φ₂ = 0 corner, 3.3e−16 at the
minimum-range/boresight corner. Two independent routes to the same numbers.

One thing that surfaced and the closed forms hide: **the corner condition admits more than
one admissible root** — the two barrier sheets meeting there. `lam_corner` returns all of
them rather than silently picking one, and which sheet to take is the caller's choice.

---

## 7. Scope

The bundle supplies verified barrier *trajectories* and a verified (BUP), for all four
surfaces. It does not by itself supply the assembled *winning zones*: stitching the
trajectories into the closed five-subregion surface of Fig. 13 requires locating the
dispersal, universal, equivocal, switch and commuting lines of Table 3 — 25 singular lines —
and applying the case-by-case closedness test. Singular arcs are detected rather than
solved, and corner-root selection is still the caller's. These are close-out §6 items about
the *construction*, unchanged by anything here; none of them blocks Layer 1, which needs a
correct zero level set to check its value function against, and the (BUP) plus the four
trajectory families give that.

---

## 8. What each family contributes, side by side

| | maximum range | minimum range | off-boresight ±β |
|---|---|---|---|
| surface | R = R̄₁(φ₂), Eq. (9) | R = R_min(φ₂), Eq. (8) | φ₁ = ±β |
| outer normal | (1, 0, (1+cos φ₂) sign φ₂) | (−1, 0, −b₁ sin φ₂) | (0, sign φ₁, 0) |
| (BUP) condition | Eq. (32) = 0 | Eq. (46) = 0 | Eq. (62) = 0, closed form |
| vanishing costate | λ₁ ≡ 0 | λ₁ ≡ 0 | λ₂ ≡ 0 |
| law recovered from λ̇ | Eq. (33) | Eq. (52), σ₁\* = sign(sin φ₁) | Eq. (65) |
| law direct from λ | Eq. (31), σ₂\* = sign φ₂ | Eq. (45), σ₂\* = −sign(sin φ₂) | Eq. (61), σ₁\* = −sign φ₁ |
| branches | 2 mirror lenses | 2 mirror arcs | 1 each |
| φ₂ support | \|φ₂\| < 9.57° | \|φ₂\| ≥ 93.07°, through the seam | one arc through the seam |
| endpoints | O₁, e₁; folds at d₁ | h₁, g₁ | m₁, N₁ |
| first switch | τ = 3.14 | τ = 0.05 | τ = 1.92 |
| switches, τ ≤ 6 | 144 / 90 traj. | 1686 / 90 traj. | 100 / 45 traj. |
| max \|H\*\|, τ ≤ 1.5 | 3.4e−14 | 1.7e−13 | 4.0e−14 |

---

## 9. Reproducing every number in this document

```
python3 layer0/viz/test_viz.py              # 26 checks: seed curves, invariants, Table 2,
                                            #   and the JS twin against the Python original
python3 layer0/viz/visualize.py             # the figure set, all four families
node    heuristic_simulator/test_barrier_js.js   # 14 checks on the reconstruction itself
python3 layer0/verify_symbolic.py           # 23 sympy re-derivations of the equations used
python3 layer0/validate_table2.py           # the published ground truth
```

`layer0/viz/barrier_explorer.html` opens in a browser with no build step: hold τ at 0 to see
a family's (BUP) alone against the target-set boundaries and the Table 2 points, then raise
τ to watch the sheet sweep.
