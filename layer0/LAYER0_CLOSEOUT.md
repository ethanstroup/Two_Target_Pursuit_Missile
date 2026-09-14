# Layer 0 Close-Out — Barrier Reconstruction from the Costate ODEs

**AE 8900 · 2026-09-11 · Ethan Stroup**
Base model: Davidovitz, A., and Shinar, J., "Two-Target Game Model of an Air Combat with
Fire-and-Forget All-Aspect Missiles," *JOTA* **63**(2), Nov. 1989, pp. 133–165.

---

## What this closes

`ProblemStatement.md` §3.4 defined the close-out task:

> reconstruct actual barrier trajectories by integrating the costate ODEs backward from
> digitized BUP points, using the true σ₁\* = −sign(λ₁) / σ₂\* = +sign(λ₂) laws, with the
> first integral (λ₁+λ₂)²/R² + λ_R² = 1 as an integration check. This produces ground truth
> against which every later layer is validated.

That is done, and it did not need digitizing anything. Every element of the boundary of
the usable part — all three surface families and both corner curves — is determined by
closed-form conditions in the paper, so the BUP is *solved*, not read off a figure. The
barrier trajectories are then integrated retrograde from it.

**Status: Layer 0 is closed as ground truth for Layer 1.** Section 6 below is explicit
about what is *not* closed, because it matters for how Layer 2 is scoped.

---

## 1. The equation set, re-derived

`verify_symbolic.py` re-derives in sympy every equation the reconstruction depends on,
rather than transcribing it (ProblemStatement §9). **23 checks, 22 pass.**

| Verified | How |
|---|---|
| Eqs. (17)–(19), costate equations | derived as −∂H/∂x from H = λ·f; exact |
| Eq. (23), first integral | d/dt = 0 exactly, and **independent of both controls** |
| Eqs. (29), (44), target-set slopes | exact / numeric on (−π, π) |
| Eqs. (31), (32), max-range UP | σ₂\* and the UP inequality both recovered from min max n·ẋ |
| Eqs. (45), (46), min-range UP | exact |
| Eqs. (61), (62), off-boresight UP | exact |
| Eqs. (34)–(37), max-range transversality | including the first integral with C = 1; Eq. (37) exact |
| Eqs. (47)–(51), min-range transversality | Eq. (50)'s form a₁²+b₁²+2a₁b₁cos φ₂ is exactly R̲² + b₁²sin²φ₂; Eq. (51) exact |
| Eqs. (39)–(41), φ₂ = 0 corner | reproduced to 1.1e−15 by an independent solve (§3) |
| Eqs. (53)–(56), min-range/boresight corner | reproduced to 3.3e−16 by the same solve |

The one check that fails is **Eq. (63)**, and it fails for a reason — see §5.2.

Two printed slips noticed in passing and **not** load-bearing here: Eq. (36) prints
`(1 cos φ₂)` where the derivation gives `(1 + cos φ₂)` (a dropped plus in typesetting, and
the equation is right with it), and Eq. (35) writes `sign(sin φ₂)` where Eq. (29) writes
`sign(φ₂)` — the same thing on (−π, π), so no discrepancy.

---

## 2. The reconstruction

`barrier.py` (and `barrier.js`, a faithful port for the browser visualizer) integrates the
coupled six-dimensional state–costate system

```
Ṙ  = −(cos φ₁ + cos φ₂)                     λ̇_R = (sin φ₁ + sin φ₂)(λ₁+λ₂)/R²
φ̇ᵢ = (sin φ₁ + sin φ₂)/R + σᵢ               λ̇ᵢ = −[λ_R sin φᵢ + cos φᵢ(λ₁+λ₂)/R]
```

backward from the BUP under σ₁\* = −sign(λ₁), σ₂\* = +sign(λ₂).

**Two invariants are carried, and they are the error estimate:**

```
FI = (λ₁+λ₂)²/R² + λ_R²  ≡ 1       Eq. (23)
H* = min_σ₁ max_σ₂ λ·f   ≡ 0       Eq. (15)
```

H\* is the sharper of the two and is the reason to bother with it. FI is conserved by the
costate ODEs *whatever the control does* — the symbolic check shows the controls cancel
identically — so FI cannot detect a wrong control. H\* can. It is the semipermeability
condition itself, and it is what the whole construction means.

Two things were needed to hold H\*, and both were found by watching it fail:

1. **Freeze the control over an RK4 step.** The barrier control is piecewise constant.
   Letting each of the four stages re-read `sign(λ)` smears every switch across a whole
   step. FI stayed at 1e−14 throughout; H\* drifted to 1e−3.
2. **Locate the switches.** Each crossing of λ₁ or λ₂ through zero is bisected out, the
   step is cut exactly there, and the control is re-read past it — at which point λ = 0 and
   the sign comes from λ̇, which is the paper's own Eqs. (33) and (65) rather than an
   assumption bolted on.

With both, over 122 trajectories of retrograde length 6 seeded across all three families:

```
                 max |FI − 1|      max |H*|
max-range          1.1e-14         3.1e-14
min-range          3.6e-12         5.5e-12
off-boresight      1.1e-10         1.4e-10
```

`barrier.js` reproduces the same figures (9.0e−11 / 1.1e−10 over 53 trajectories and 450
located switches), so the browser path and the Python path are the same object.

---

## 3. Corner costates, solved instead of transcribed

At a corner of the target-set boundary the gradient must be a non-negative combination of
the two adjoining outer normals. The paper gives three closed forms for the multipliers
(Eqs. 38–42, 53–58, 66–70), each a page of algebra.

`lam_corner` does not use them. It solves for the combination directly from the two
conditions it has to satisfy anyway — H\* = 0 and FI = 1 — which is one scalar equation in
one angle. The paper's closed forms then become a *test* rather than an input, and they
pass to machine precision (1.1e−15 at the φ₂ = 0 corner, 3.3e−16 at the minimum-range /
boresight corner). Two independent routes to the same numbers.

One thing this surfaced that the closed forms hide: **the corner condition has more than
one admissible root** — the two barrier sheets meeting there. `lam_corner` returns all of
them rather than silently picking one. Selecting between them is part of what §6 lists as
still open.

---

## 4. Acceptance against Table 2

Table 2 ("Coordinates of significant points", p. 155) is the only hard numerical ground
truth the paper publishes. All 59 points are transcribed in `validate_table2.py` and tested
against every surface and curve the equations determine.

**27 of 59 lie on a determined surface, each to within the table's own printed precision.**
The remaining 32 are interior barrier features — universal-line endpoints, dispersal
junctions, switch-line crossings — that only the full construction produces; they are
listed as unplaced rather than quietly dropped.

The sharper test is the six points fixed by a *system* of equations, where nothing is
fitted:

| point | defining conditions | solved | Table 2 | ΔR |
|---|---|---|---|---|
| d₁ | Eq. (32) = 0 **and** Eq. (37) = 0 | 5.8083, 18.88°, −9.57° | 5.808, 18.88°, −9.56° | 3.3e−4 |
| Q₁ | boresight BUP at cos φ₂ = 0 | 1.7071, 45°, 90° | 1.707, 45°, 90° | 1.1e−4 |
| g₁ | Eq. (46) = 0 at φ₁ = β | 0.2665, 45°, −160.92° | 0.267, 45°, −160.9° | 5.2e−4 |
| h₁ | Eq. (46) = 0 at φ₁ = β | 0.5347, 45°, 92.92° | 0.535, 45°, 92.92° | 2.8e−4 |
| e₁ | max-range BUP, φ₂ → 0 | 6.1416, 36.08°, 0° | 6.142, 36.07°, 0° | 4.1e−4 |
| γ | φ₁ = φ₂ = β, R = 2 sin β (Sec. 3.4) | 1.4142, 45°, 45° | 1.414, 45°, 45° | 2.1e−4 |

Worst residual 5.2e−4, which is Table 2's own rounding. d₁ is the strongest single result
here: two independent transcendental conditions, solved simultaneously, landing on the
printed point to 0.01° in both angles.

`reproduce_figures.py` redraws Figs. 4, 5, 6, 8, 10 and 11 from the reconstruction, in the
paper's own axis orientation, with the Table 2 points overlaid. Fig. 4's S-curve through
the origin, Fig. 5's usable part concentrated at φ₂ = ±π, and Fig. 6's non-usable wedge
bounded by N₁Q₁M₁ all come out as printed.

---

## 5. Three findings

### 5.1 R̄₀ is 3 + π, not 6.14 — and the code had 6.14

Sec. 4 quotes R̄(0) = 6.14. Appendix A Eq. (96) defines R̄₀ = (R_tc)max/ρ + π, and Table 2
pins (R_tc)max/ρ exactly: point A₁ is R̄ at φ₂ = π, printed as **3.0**. So R̄₀ = 3 + π =
6.141593, and 6.14 is the rounded quotation.

This is not pedantry — it is decidable from the table:

| | R̄₀ = 3 + π | R̄₀ = 6.14 | Table 2 |
|---|---|---|---|
| A₁ = R̄(π) | **3.00000** | 2.99841 | 3.0 |
| O₁ = R̄(0) | **6.14159** | 6.14000 | 6.1416 |
| β = R̄(β) | **4.64909** | 4.64750 | 4.649 |
| δ = R̄(−β) | **4.64909** | 4.64750 | 4.649 |

O₁ at four decimals is the decisive one: 6.1416 is 3 + π rounded, and is not 6.14.
`sim.js` had `Rbar0: 6.14`; it now has `3 + Math.PI`, with the reasoning in the comment and
tightened assertions in `test_acceptance.js` so it cannot silently regress.

### 5.2 Eq. (63) carries a spurious sign(φ₁) — settled by the paper's own Eq. (64)

On the off-boresight surface φ₁ = ±β the outer normal is (0, sign φ₁, 0), so λ = μ(0, sign
φ₁, 0), and the first integral forces μ = R. Hence

> λ₁f = R sign(φ₁) = sin φ₁ + sin φ₂   (using the BUP relation R = (sin φ₁ + sin φ₂) sign φ₁)

Eq. (63) prints **(sin φ₁ + sin φ₂) sign φ₁** — one factor of sign(φ₁) more.

The paper decides against itself. Eq. (64) gives λ̇₂f = −(cos φ₂) sign φ₁, and from Eq. (19)
with λ_R = λ₂ = 0 one has λ̇₂ = −cos φ₂ · λ₁/R. The derived λ₁f gives λ₁/R = sign φ₁ and
reproduces Eq. (64); the printed λ₁f gives λ₁/R = 1 and produces −cos φ₂, contradicting it.
Eq. (65), σ₂\* = sign(cos φ₂) sign φ₁, follows from Eq. (64), so the printed Eq. (63) is
inconsistent with the two equations immediately after it.

It is not cosmetic. Seeding the integrator with Eq. (63) as printed, **110 of 220 boresight
BUP seeds then contradict Eq. (65)** — every one of them at φ₁ = −β, where the extra
sign(φ₁) flips the whole strategy pair. At φ₁ = +β the two agree and nothing shows. A
demonstration of this is a standing assertion in `test_barrier.py` and `test_barrier_js.js`.

This is the **fifth** reviewed primary carrying a checkable error in a load-bearing
equation, and the **fourth of five** caught by internal consistency against another printed
equation in the same paper rather than by external re-derivation. That pattern is now the
strongest argument for §9's re-derive-don't-transcribe standard.

### 5.3 The long-range acceptance-grid statistics are not a stable quantity

Correcting R̄₀ by 0.0016 — 0.026% — moved the spec §9 outcome fractions:

| R₀ | mutual-kill fraction at 6.1400 | at 3 + π | shift |
|---|---|---|---|
| 5 | 3.98% | 3.83% | 0.15 pp |
| 8 | 18.93% | 17.66% | 1.3 pp |
| 12 | 86.94% | 85.29% | 1.7 pp |

`sens.js` sweeps R̄₀ across 6.1400–6.1500 and the long-range fractions move **non-
monotonically** over that range, by more than the acceptance test's ±1.5 pp tolerance. The
short-range rows barely move at all.

So the §9 grid is a good regression test at short range and a poor one beyond R ≈ 8. That
is independent, measured support for ProblemStatement §4's case for Layer 1: the existing
sim's long-range behaviour is an artefact of the heuristic, and now demonstrably also of
three-digit parameter choices, not a fact about the game. The §9 expected table has been
re-baselined for the corrected constant, with the superseded values kept in the comment.

---

## 6. What is *not* closed

Layer 0 now supplies verified barrier *trajectories* and a verified BUP. It does not yet
supply the assembled *winning zones*. Specifically:

1. **The barrier surface is not assembled.** Trajectories are correct individually;
   stitching them into the closed five-subregion surface of Fig. 13 requires locating the
   dispersal, universal, equivocal, switch and commuting lines of Table 3 — 25 singular
   lines — and applying Step 4's case-by-case closedness test. That is the bulk of what
   D&S's thesis did.
2. **Singular arcs are detected, not solved.** On a universal line a costate component
   stays at zero over an interval and the optimal control is intermediate, not bang-bang
   (Table 3 lists strategies (−1, 0) and (0, +1)). `integrate_retrograde` flags these in its
   `singular` return field rather than chattering through them. Handling them is required
   before the surface can be assembled.
3. **32 of 59 Table 2 points remain unplaced** — they are the interior features above.
   One of them is a live question rather than just unfinished work: **f₁**. The paper says
   f₁ is where "λ̃₁f = 0", but Eq. (38) makes λ̃₁ ≡ 0 along the whole φ₂ = 0 corner, and the
   natural reading λ̃̇₁f = 0 is impossible — Eq. (42), which re-derives exactly as printed,
   is −q[R̄₀|sin φ₁| + 1 + cos φ₁] sign φ₁, and the bracket is strictly positive. So f₁'s
   defining condition is not recoverable from the text as printed. **Open marker.**
4. **Corner-root selection.** §3 found the corner condition admits more than one admissible
   costate; which sheet is taken is currently the caller's choice.

None of this blocks Layer 1. Layer 1 needs a correct zero level set to check its value
function against, and the BUP plus the trajectory families give that locally; the full
assembly is what Layer 1's own solution would produce globally, which is the better order
to do it in.

---

## 7. Files

```
layer0/
  barrier.py             core: dynamics, costates, invariants, BUP, retrograde integrator
  verify_symbolic.py     23 sympy re-derivations          → 22 pass, 1 documented failure
  validate_table2.py     Table 2 acceptance test
  test_barrier.py        integration tests on the invariants and the printed control laws
  reproduce_figures.py   redraws Figs. 4, 5, 6, 8, 10, 11 → figs/
  figs/                  the reconstructed figures
  sens.js                Rbar_0 sensitivity of the §9 grid statistics
  LAYER0_CLOSEOUT.md     this file
barrier.js               port of barrier.py for the browser visualiser
test_barrier_js.js       node acceptance tests for barrier.js  (14 pass)
```

Run order:

```
python3 layer0/verify_symbolic.py      # equations
python3 layer0/validate_table2.py      # published ground truth
python3 layer0/test_barrier.py         # the reconstruction
python3 layer0/reproduce_figures.py layer0/figs
node    test_barrier_js.js             # the JS port
node    test_acceptance.js             # the existing sim, re-baselined
node    layer0/sens.js                 # the sensitivity result of §5.3
```

Requires `numpy`, `scipy`, `sympy`, `matplotlib`.
