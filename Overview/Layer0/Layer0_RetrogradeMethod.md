# The Retrograde Construction, Surface by Surface

**AE 8900 · Layer 0 · 2026-09-16 · Ethan Stroup**
Base model: Davidovitz, A., and Shinar, J., "Two-Target Game Model of an Air Combat with
Fire-and-Forget All-Aspect Missiles," *JOTA* **63**(2), Nov. 1989, pp. 133–165.

How a barrier trajectory is generated, for each of the four surfaces that carry a boundary
of the usable part. Companion to `Layer0_CloseOut_2026-09-11.md`, which records what the
reconstruction verified; this records *how it runs*. Copy of record lives in the repo at
`layer0/RETROGRADE_METHOD.md`; implemented in `layer0/barrier.py`, ported in
`layer0/barrier.js`, seeded by `layer0/viz/bup_curves.py`, drawn by `layer0/viz/`.

---

## 1. Why the integration runs backward

The barrier is a **semipermeable surface** in x = (R, φ₁, φ₂). Isaacs' characterisation is
local — at every point there is a normal λ with

```
H*(x, λ) = min max λ · f(x, σ₁, σ₂) = 0                                  Eq. (15)
            σ₁   σ₂
```

and the surface is swept by trajectories satisfying this together with the costate equations

```
λ̇_R = (sin φ₁ + sin φ₂)(λ₁+λ₂)/R²                                        Eq. (17)
λ̇ᵢ  = −[λ_R sin φᵢ + cos φᵢ (λ₁+λ₂)/R]                                   Eqs. (18)-(19)
```

under the min-max strategies σ₁* = −sign(λ₁), σ₂* = +sign(λ₂) (Eqs. 21-22).

This is a **condition, not an initial-value problem** — nothing in it says where a barrier
trajectory starts. Forward in time it is a two-point boundary-value problem: guess a costate
at some interior state and shoot until the trajectory happens to terminate correctly.

What *is* known outright is the terminal condition. A barrier trajectory ends on the boundary
of the usable part, and there the costate is not free: **transversality (Eq. 20) fixes it** —
λ parallel to the target-set boundary's outer normal, normalised by the first integral. So at
every (BUP) point the whole six-dimensional state–costate vector is closed form.

That turns the boundary-value problem into an initial-value problem run in reverse: with
τ = −t, integrate dy/dτ = −f(y) from each (BUP) point. Every run is a barrier trajectory
exactly, from the first step, and the **bundle** of them over the (BUP) is the barrier sheet.

Which is also why the (BUP) has to be produced as an *ordered curve* rather than a point set:
the bundle is a surface parametrised by (arclength along the (BUP), τ), and neighbouring
seeds must be genuine neighbours on the barrier for that to mean anything.

## 2. Machinery common to all four surfaces

**Two invariants ride along and are the error estimate.** FI = (λ₁+λ₂)²/R² + λ_R² ≡ 1
(Eq. 23) and H\* ≡ 0 (Eq. 15). H\* is the sharper: FI is conserved by the costate ODEs
*whatever the control does* — the controls cancel identically — so it cannot detect a wrong
control. H\* is the semipermeability condition itself, so it fails immediately.

**The control is frozen over an RK4 step.** Letting each stage re-read sign(λ) smears every
switch across a step: FI stays at 1e−14 while H\* drifts to 1e−3. Both facts together found
the bug.

**Switches are located, not stepped over** — each λ₁ or λ₂ zero crossing bisected out (60
iterations), the step cut there, the component snapped to zero, the control re-read past it.

**Where a costate component vanishes, the sign comes from its derivative.** λ₁ ≡ 0 on both
range surfaces and λ₂ ≡ 0 on both boresight surfaces, so at *every* seed one control is
undefined by Eqs. (21)-(22) as written. Backward, λ ≈ −τλ̇_f, so sign(λ) = −sign(λ̇). That
reproduces the paper's Eqs. (33) and (65) instead of assuming them — which makes the printed
control laws a *test* of the seeding rather than an input to it.

**Singular arcs are flagged, not chattered through** — λᵢ ≈ 0 *and* λ̇ᵢ ≈ 0 together.

**Seeds are put back exactly on the (BUP).** Traced by continuation, resampled at equal
arclength, then re-solved for the defining root: linear interpolation lands slightly off it,
which shows as H\* ≈ 1e−5 at the seed, and a seed that is not semipermeable is not a barrier
point. After the snap every seed carries |H\*| ≤ 4.4e−16.

## 3. Surface I — maximum range, R = R̄₁(φ₂) = R̄₀ − |φ₂ + sin φ₂|, R̄₀ = 3 + π

Outer normal n = (1, 0, (1 + cos φ₂) sign φ₂), Eqs. (28)-(29). (BUP) from Eq. (32) = 0.
Terminal costate Eqs. (34)-(36): λ = p(R̄₁, 0, R̄₁(1+cos φ₂) sign(sin φ₂)), p = 1/√(R̄₁² +
(1+cos φ₂)²). λ₁ = 0, so σ₁\* comes from λ̇₁; λ₂ ≠ 0 gives σ₂\* = sign(φ₂) — Eq. (31),
recovered.

**Shape.** Two roots per φ₂, merging and vanishing at |φ₂| = 9.5694°, so the family lives
inside |φ₂| < 9.57° and is a **closed lens** — out along the inner branch to the fold, back
along the outer. sign(φ₂) in Eq. (32) makes φ₂ = 0 a genuine discontinuity of the root set,
so there are two mirror lenses, which together form Fig. 4's S-curve through the origin.

| feature | solved | Table 2 |
|---|---|---|
| φ₂ → 0, inner branch | R 6.14119, φ₁ 0.011° | **O₁** (6.1416, 0°, 0°) |
| the fold | R 5.80833, φ₁ 18.923°, φ₂ −9.569° | **d₁** (5.808, 18.88°, −9.56°) |
| φ₂ → 0, outer branch | R 6.14119, φ₁ 36.066° | **e₁** (6.142, 36.07°, 0°) |

The fold needs care: the roots separate like √(φ₂\* − φ₂), so a φ₂ grid loses them while they
are still half a degree apart in φ₁. `refine_fold` bisects on *whether two roots still exist*.

**Downstream.** The mildest family for the switching machinery: over 90 trajectories the
first switch is at **τ = 3.14**, none below; 144 by τ ≤ 6. max |FI−1| 7.5e−15, |H\*| 3.4e−14.

## 4. Surface II — minimum range, R = R_min(φ₂) = a₁ + b₁cos φ₂

Outer normal n = (−1, 0, −b₁ sin φ₂), Eqs. (43)-(44). (BUP) from Eq. (46) = 0. Costate
Eqs. (47)-(50): λ = −pᵤR_min(1, 0, b₁ sin φ₂), pᵤ = 1/√(a₁²+b₁²+2a₁b₁cos φ₂) — whose printed
form is exactly R_min² + b₁²sin²φ₂. λ₁ = 0, so σ₁\* from λ̇₁ reproduces Eq. (52); λ₂ ≠ 0 gives
σ₂\* = −sign(sin φ₂) directly, Eq. (45).

**Shape.** Two mirror branches, each entirely at **large aspect angle, |φ₂| ≥ 93.07°**,
running continuously **through φ₂ = ±180°** — the seam bounds the coordinate, not the problem
— with φ₁ sweeping ±44.8° → ±2.66° and back. Both ends terminate on the off-boresight limit,
which is exactly how the paper defines them ("Eq. (46) = 0 at φ₁ = β"):

| endpoint | solved | Table 2 |
|---|---|---|
| φ₂ = 93.066° | R 0.53395, φ₁ 44.804° | **h₁** (0.535, 45°, 92.92°) |
| φ₂ = −161.037° | R 0.26628, φ₁ 44.843° | **g₁** (0.267, 45°, −160.9°) |

**Downstream.** By far the most switch-dense family — short range, high angular rate. First
switch at **τ = 0.05**; 90 trajectories give 376 switches by τ = 1.5, 816 by τ = 3, 1686 by
τ = 6. It is therefore the family that actually exercises the frozen-control and
bisected-switch machinery, and the right one to regress against. max |FI−1| 1.6e−13.

## 5. Surfaces III and IV — off-boresight, φ₁ = ±β

Two distinct surfaces, not one — and the distinction is where Eq. (63) goes wrong.

Outer normal n = (0, sign φ₁, 0), Eq. (59). Eq. (62) = 0 gives R = (sin φ₁ + sin φ₂) sign φ₁
in closed form, valid where R_min ≤ R < R̄₁. Transversality plus the first integral forces
λ = (0, R sign φ₁, 0).

**Eq. (63) as printed gives one factor of sign(φ₁) more.** The paper decides against itself:
Eq. (64) is λ̇₂f = −(cos φ₂) sign φ₁, and Eq. (19) with λ_R = λ₂ = 0 gives λ̇₂ = −cos φ₂ · λ₁/R.
The derived λ₁f gives λ₁/R = sign φ₁ and reproduces Eq. (64); the printed one gives λ₁/R = 1
and contradicts it. Invisible at φ₁ = +β, inverts the whole strategy pair at φ₁ = −β: seeding
with Eq. (63) as printed makes **110 of 220 boresight seeds contradict Eq. (65)**, every one
at φ₁ = −β. That is a standing assertion in both test suites, and the reason these count as
two surfaces here.

λ₂ = 0, so σ₂\* from λ̇₂ recovers Eq. (65), σ₂\* = sign(cos φ₂) sign(φ₁); λ₁ ≠ 0 gives
σ₁\* = −sign(φ₁), Eq. (61).

**Shape.** One branch each — φ₁ fixed, so the curve is R(φ₂). For φ₁ = +β it is admissible on
φ₂ ∈ [8.218°, 180°] ∪ [−180°, −154.784°], one arc through the seam, with both endpoints the
**corner with the minimum-range surface**:

| endpoint (φ₁ = +β) | solved | Table 2 |
|---|---|---|
| φ₂ = 8.218° | R 0.85004 | **m₁** (0.847, 45°, 8.05°) |
| φ₂ = −154.784° | R 0.28108 | **N₁** (0.279, 45°, −154.6°) |

φ₁ = −β is the mirror. Table 2 tabulates only player 1's points, so its endpoints are the
untabulated primed mirrors — which is why `bore-` reports zero Table 2 points while being
numerically identical to `bore+`.

**Downstream.** Both identical: first switch at **τ = 1.92**, none below; 26 by τ = 3, 100 by
τ = 6 over 45 trajectories.

## 6. The corners, where the four families meet

Every branch endpoint above is a **corner** of the target-set boundary. The maximum-range
lens ends at the φ₂ = 0 corner; the minimum-range branches at the minimum-range/boresight
corner (g₁, h₁); the boresight branches at the same corner from the other side (m₁, N₁). The
four families are arcs of one boundary, joined at corners — not four disconnected objects.

At a corner the gradient must be a non-negative combination of the two adjoining outer
normals. The paper gives three closed forms (Eqs. 38-42, 53-58, 66-70), each a page of
algebra. `lam_corner` uses none of them: it solves for the combination from the two
conditions the costate must satisfy anyway, H\* = 0 and FI = 1, which is one scalar equation
in one angle. The closed forms then become a *test*, and pass to 1.1e−15 and 3.3e−16. The
corner condition admits more than one admissible root — the two sheets meeting there — and
all are returned rather than one silently chosen.

## 7. Scope

The bundle supplies verified barrier *trajectories* and a verified (BUP) for all four
surfaces. It does not by itself assemble the winning zones: stitching them into the closed
five-subregion surface of Fig. 13 needs the 25 singular lines of Table 3 and the
case-by-case closedness test. Singular arcs are detected rather than solved; corner-root
selection remains the caller's. These are close-out §6 items about the *construction*,
unchanged by this work, and none blocks Layer 1.

## 8. Side by side

| | maximum range | minimum range | off-boresight ±β |
|---|---|---|---|
| surface | R = R̄₁(φ₂), Eq. (9) | R = R_min(φ₂), Eq. (8) | φ₁ = ±β |
| outer normal | (1, 0, (1+cos φ₂) sign φ₂) | (−1, 0, −b₁ sin φ₂) | (0, sign φ₁, 0) |
| (BUP) condition | Eq. (32) = 0 | Eq. (46) = 0 | Eq. (62) = 0, closed form |
| vanishing costate | λ₁ ≡ 0 | λ₁ ≡ 0 | λ₂ ≡ 0 |
| recovered from λ̇ | Eq. (33) | Eq. (52), σ₁\* = sign(sin φ₁) | Eq. (65) |
| direct from λ | Eq. (31), σ₂\* = sign φ₂ | Eq. (45), σ₂\* = −sign(sin φ₂) | Eq. (61), σ₁\* = −sign φ₁ |
| branches | 2 mirror lenses | 2 mirror arcs | 1 each |
| φ₂ support | \|φ₂\| < 9.57° | \|φ₂\| ≥ 93.07°, through the seam | one arc through the seam |
| endpoints | O₁, e₁; fold at d₁ | h₁, g₁ | m₁, N₁ |
| first switch | τ = 3.14 | τ = 0.05 | τ = 1.92 |
| switches, τ ≤ 6 | 144 / 90 traj. | 1686 / 90 traj. | 100 / 45 traj. |
| max \|H\*\|, τ ≤ 1.5 | 3.4e−14 | 1.7e−13 | 4.0e−14 |

## 9. Reproducing every number here

```
python3 layer0/viz/test_viz.py              # 26 checks: seed curves, invariants, Table 2,
                                            #   and the JS twin against the Python original
python3 layer0/viz/visualize.py             # the figure set, all four families
node    heuristic_simulator/test_barrier_js.js   # 14 checks on the reconstruction
python3 layer0/verify_symbolic.py           # 23 sympy re-derivations
python3 layer0/validate_table2.py           # the published ground truth
```

`layer0/viz/barrier_explorer.html` opens in a browser with no build step: hold τ at 0 to see
a family's (BUP) alone against the target-set boundaries and the Table 2 points, then raise τ
to watch the sheet sweep.
