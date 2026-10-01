# Maximum-Range Barrier — Audit against D&S Sec. 4.1

**AE 8900 · 2026-09-17 · Ethan Stroup**
Question asked: are all the pieces needed for the two small closed maximum-range capture
zones being generated, or only the ordinary backward-integrated sheets?

**Answer: only the ordinary sheets.** Of the paper's two maximum-range families, one is
generated and one is absent, and none of the pieces that close a zone exist.

Run it: `python3 layer0/viz/diag_maxrange.py` → `layer0/viz/figs/diag_maxrange.{png,txt}`
Corner family and the f₁ question: `python3 layer0/viz/corner_family.py`

> **Amended 2026-09-21 (later).** Finding 8: the dispersal line e₁c₁O is found, closed, and meets the universal line at c₁ ≈ f₁.
>
> **Amended 2026-09-21.** Finding 7 revises Finding 6: 18.5° also has a genuine meaning — it is where the universal-line costate is semipermeable on the corner — and the universal line from d₁ passes within 2e−3 of f₁.
>
> **Amended 2026-09-17 (later).** Findings 3 and 6 below supersede the earlier statement
> that "f₁'s defining condition is not recoverable from the printed text." It is
> recoverable, exactly, and it turns out to rest on a misplaced sign in Eq. (42). See
> Finding 6.

---

## Headline numbers

| | |
|---|---|
| BUP seeds | 122, in 2 branches |
| branch counts by (σ₁\*, σ₂\*) | (−1,−1) 30 · (−1,+1) 31 · (+1,−1) 31 · (+1,+1) 30 |
| d₁ solved | R 5.80833, φ₁ 18.8775°, φ₂ −9.5695° (Table 2: 5.808, 18.88, −9.56) |
| f₁ | **not on the maximum-range BUP** — Eq. (32) residual 0.317 there; it is on the φ₂ = 0 corner edge, and is spurious (Finding 6) |
| control switches detected | 196 |
| min distance between families | 9e−5 normalized (τ ≤ 2) — at O₁, their shared endpoint |
| intersection points | 478, all within \|φ₂\| ≤ 0.254° |
| continuous dispersal line | **no** |
| universal-line handling | **no** — detection only, and the detector never fires |
| assembled surface watertight | **n/a** — no mesh is ever assembled |

## What is correct

Eq. (32) is implemented exactly as stated: `max |(LHS − RHS) − up_maxrange|` = **0.00e+00**
over 20 000 random points. Both symmetric branches are sampled, every seed satisfies
Eq. (32) to 6.7e−16, and λ₁f = 0 identically. The closed form

λ̇₁f = −ρ[R̄ sin φ₁ + (1+cos φ₂) cos φ₁ sgn(sin φ₂)]

agrees with the integrator's own `costate_dot` to **8.3e−17**, and σ₁\* = sign(λ̇₁f),
σ₂\* = sign(λ₂f) reproduce `barrier_controls` on every seed with no disagreement.

## Finding 1 — the σ₁ switch locus *is* the fold of Eq. (32)

Verified numerically: **∂(Eq. 32)/∂φ₁ ≡ −λ̇₁f / ρ** (residual 8.1e−10, finite-difference
limited). So solving λ̇₁f = 0 on the BUP is the same problem as finding where Eq. (32)'s two
φ₁ roots merge. That point is d₁, and the two σ₁ families are exactly the two halves of the
lens: inner O₁ → d₁ and outer d₁ → e₁. `refine_fold` already locates it to 2.5e−3° in φ₁.

## Finding 2 — f₁ is not on this BUP; the corner edge is the missing piece

Table 2 puts O₁, f₁, e₁ all at φ₂ = 0, R = R̄(0) = 6.14159, differing only in φ₁
(0°, 18.5°, 36.07°). They are collinear along the **φ₂ = 0 corner edge** of the
maximum-range surface — R̄ = R̄₀ − \|φ₂ + sin φ₂\| has a slope jump there, from +2 to −2, so
the outer normal is not unique.

That resolves the structure of Sec. 4.1: the two segments e₁f₁O and e₁d₁O share their
endpoints and together **bound the usable part in the φ₂ ≤ 0 half** — the lens on one side,
the corner edge on the other. One family is seeded on the lens; the other on the corner.

**The corner family was never seeded.** `bup_curves.py` builds seeds only from
`lam_maxrange` / `lam_minrange` / `lam_boresight` — it references `lam_corner`,
`n_maxrange`, `n_minrange`, `n_boresight` exactly zero times. `lam_corner` exists and
`test_barrier.py` validates it at this very corner to 1.1e−15. Nothing called it.

`layer0/viz/corner_family.py` now does. 60 seeds on 0 < φ₁ < e₁, max \|FI−1\| 3.3e−16,
max \|H\*\| 1.1e−15 at the seeds and 2.7e−14 integrated. Control pair **(−1,+1) throughout** —
see Finding 6 for why the (+1,+1) half does not appear.

Consequence chain, as it now stands: corner family seeded → two families exist → they
contact only at their **shared endpoints** O and e₁, not along a curve → still no dispersal
line, no c₁, no closed capture zone.

## Finding 3 — e₁ is the branch point of the corner costate

Scanning `lam_corner` along the corner: it admits **two** admissible costates only for
φ₁ ∈ [36.1°, 44.8°], and bisecting the threshold gives **φ₁ = 36.0755°** against Table 2's
e₁ at 36.07° — a difference of 0.0055°. So e₁ is exactly where the corner costate becomes
double-valued.

Closed form, now derived rather than bisected. Writing λ = (λ_R, 0, λ₂) on the corner cone
spanned by (1,0,−2) and (1,0,+2), H\* = 0 with FI = 1 has two roots. The λ₂ > 0 root is the
paper's Eqs. (39)–(41) and is admissible on the whole segment. The λ₂ < 0 root has cone
ratio \|λ₂\|/(2λ_R) > 1 — one of μ⁺, μ⁻ negative — and reaches 1 **exactly** at

R̄₀ tan(φ₁/2) = 2  ⟹  φ₁ = 2 arctan(2/R̄₀) = 36.0755° = e₁

which is the same closed form as the φ₂ → 0⁻ limit of Eq. (32). Two independent routes to
e₁, agreeing to machine precision.

## Finding 4 — the red/blue sheets do not meet

Resolved in retrograde time, because past τ ≈ 3 the angles wind through ±180° and every
sheet threads every other one:

| family pair | τ≤0.4 | τ≤1.0 | τ≤2.0 |
|---|---|---|---|
| lobe0 inner × lobe0 outer | 0.00175 | 0.00174 | 0.00174 |
| lobe0 inner × lobe1 inner | 0.07797 | 0.07732 | 0.07686 |
| lobe0 inner × lobe1 outer | 0.00009 | 0.00009 | 0.00009 |
| lobe0 outer × lobe1 inner | 0.11779 | 0.11779 | 0.11779 |
| lobe0 outer × lobe1 outer | 0.07967 | 0.07901 | 0.07854 |
| lobe1 inner × lobe1 outer | 0.00231 | 0.00228 | 0.00228 |

The 9e−5 closest approach is at R 6.1412, φ₁ ±0.011°, φ₂ ∓0.011° — that is O₁, the point the
two mirror lenses already **share**. All 478 candidate points sit within \|φ₂\| ≤ 0.254° of
it. One point thickened by the tolerance, not a curve. The two lobes otherwise stay 0.077
apart and never meet.

**The projection trap is real and measured.** For lobe0 inner × lobe1 inner at τ ≤ 2:
**102** point pairs fall within tolerance in the (φ₁, φ₂) projection, and **0** in full
(R, φ₁, φ₂). The projection overstates contact by a factor of 102.

## Finding 5 — the singular detector is dead code

`integrate_retrograde` flags a singular arc when \|λᵢ\| < 1e−7 **and** \|λ̇ᵢ\| < 1e−7. The
closest any trajectory in the bundle comes to that condition is **1.9e−03** — five orders of
magnitude away. Zero flags were raised over 122 trajectories. It offers no protection in
practice, and nothing propagates a universal arc: the intermediate control is never
computed. Nothing fakes σ₁ = ±1 there either, which is the one thing that would be worse.

## Finding 6 — f₁ = 18.5° is reproducible exactly, and it comes from a misplaced sign in Eq. (42)

Table 2 lists f₁ at (6.142, 18.5, 0.0) — on the corner segment — and Sec. 4.1 says two
universal lines of player 1 terminate at d₁ and f₁, so σ₁ should flip there. On the
admissible corner costate it does not, and the number 18.5 is recoverable to both printed
digits from the printed equation read literally.

**Step 1. Eqs. (39)–(41) are right.** Transcribed and checked: H\* = 0 to ≤2.2e−16 and
FI − 1 = 0 to ≤4.4e−16 at every φ₁ on the segment, both signs. They are also the unique
λ₂ > 0 root of {H\* = 0, FI = 1} on the corner cone, so they are not a guess.

**Step 2. Eq. (42) is right on φ₁ > 0 and wrong on φ₁ < 0.** Substituting (39)–(41) into
Eq. (18) reproduces the printed

λ̇₁f = −q[ R̄₀\|sin φ₁\| + (cos φ₁ + 1) sgn φ₁ ]

to **2.2e−16** for φ₁ > 0 — and disagrees grossly for φ₁ < 0 (at −18.5° the true value is
+0.5776, the printed expression gives 0). The true λ̇₁f is odd under the paper's own mirror
symmetry M, so the sgn φ₁ belongs **outside** the bracket:

λ̇₁f = −q[ R̄₀\|sin φ₁\| + cos φ₁ + 1 ] · sgn φ₁   (max err 1.1e−16 on both signs)

**Step 3. The misplaced sign creates f₁.** Read as printed, on φ₁ < 0 the bracket becomes a
*difference*, and that difference has a root:

R̄₀\|sin φ₁\| = 1 + cos φ₁ ⟺ R̄₀ tan(\|φ₁\|/2) = 1 ⟹ \|φ₁\| = 2 arctan(1/R̄₀) = **18.4960°**

and with the paper's own rounded R̄₀ = 6.14, **18.5007°** — Table 2's f₁ = 18.5 to both
digits. Compare e₁, which is the same construction with the honest factor 2 (the jump in
∂R̄/∂φ₂ across φ₂ = 0): R̄₀ tan(φ₁/2) = 2 → 36.0755°, Table 2's 36.07. f₁ and e₁ differ only
in that factor — precisely what the misplaced sign destroys.

**Step 4. The alternative reading also fails.** The λ₂ < 0 root of {H\* = 0, FI = 1} does
have λ̇₁f = 0 at 18.4960° — same algebra — but its cone ratio there is 1.0272 > 1, i.e.
μ⁺ or μ⁻ is negative. It is outside the normal cone for every φ₁ below e₁ and only enters at
e₁ itself (Finding 3). So it is not a barrier costate anywhere on the segment where f₁ is
tabulated.

**Conclusion.** On the corner segment the true λ̇₁f is strictly negative for φ₁ > 0
(range −0.31 to −0.78, no sign change over 4000 samples), so **σ₁ = −sgn φ₁ throughout and
there is no switch at f₁**. Only the (−1,+1) family is reproducible from the paper's own
equations; the (+1,+1) family Fig. 8 shows below f₁ does not follow from them. Nothing in
the code fakes it.

Two caveats, stated plainly: this identifies *a* sign placement that reproduces 18.5 exactly
and is inconsistent with the paper's own mirror symmetry — it does not prove that is how the
authors got the number; and it does not rule out a condition for f₁ coming from somewhere
outside Sec. 3.1 that happens to land on the same value. The 4-significant-figure match to a
2-parameter-free closed form makes coincidence unlikely.

Reproduce: `python3 layer0/viz/corner_family.py` → the `f_1 diagnostic` block, or call
`corner_family.f1_diagnostic()`.

## Termination events

All 162 trajectories stopped on the **τ limit** — none reached R_min, R_max, went
non-finite, or hit the step guard. So nothing is terminating on a geometric event; the
retrograde length is purely a visualization choice. Invariants over the bundle:
max \|FI−1\| = 1.6e−14, max \|H\*\| = 7.0e−14.

## What would have to be built

1. ~~Seed the φ₂ = 0 corner family~~ — **done**, `layer0/viz/corner_family.py`. Not yet
   wired into `bup_curves.py` / `bup_curves.js` / the explorer as a fifth family.
2. **Resolve the (+1,+1) family.** Finding 6 shows it does not follow from Eqs. (38)–(42)
   as printed, or from the second cone root. Either the paper has a further condition not
   in Sec. 3.1, or Fig. 8's lower family rests on the same sign slip. This is the live
   question, and it is now sharply posed rather than open-ended.
3. **Universal-arc propagation** at d₁ (which is real — Finding 1) — the intermediate
   control on a singular arc, not a bang-bang substitute.
4. **Dispersal-line construction** from the two families. They currently touch only at O
   and e₁, with the gap at f₁ *widening* as the contact tolerance tightens.
5. **c₁** as the universal/dispersal junction. Table 2: (5.925, 18.7, 4.78) — note φ₂ > 0,
   so c₁ is interior, and the lens lobe meeting the corner family there is the φ₂ > 0 one.
6. **Mesh assembly and a watertightness test** — the code plots surfaces; it does not build
   a solid, so "closed" cannot currently be checked at all.

## A bug found and fixed while doing this

The diagnostic figure came out empty on first render. Cause: `diag_maxrange.py` defines
`D = 180/π` while `visualize.py` defines `D = π/180`, and the plotting idiom `angle / D` was
copied across, dividing radians by 57.3 instead of multiplying. Only the new diagnostic's
figure was affected — `visualize.py` and the explorer use their own convention correctly —
but it is a live trap for anything else copied between those two files.

## Finding 7 — the universal line from d₁ (option 1), and what f₁ really is

`python3 layer0/viz/universal_d1.py` → `layer0/viz/figs/universal_d1.png`

**Singular control, derived not assumed.** With λ₁ = 0, sympy gives
λ̈₁ = A·σ₁ with A = −λ_R cos φ₁ + λ₂ sin φ₁ / R and **no σ-free term**. Keeping
λ₁ = λ̇₁ = 0 therefore needs σ₁ = 0 exactly — Table 3's "0". On the line,
λ̇₁ = 0 and FI = 1 give the closed form **λ = (cos φ₁, 0, −R sin φ₁)**, A ≡ −1 (never
degenerates), held by the integrator to 5e−13. Invariants: |λ₁| 3e−14, |λ̇₁| 8e−14,
|FI−1| 1e−14, |H\*| 4e−14.

**Where it goes.** Retrograde from d₁ with σ = (0,−1), it skims just outside the
max-range surface (R − R̄ ≈ 0.001) and crosses φ₂ = 0 at R 6.1462, φ₁ 18.482° —
**passing within 2.0e−3 of f₁** in full (R, φ₁, φ₂).

| on the line at | τ | R | φ₁ |
|---|---|---|---|
| φ₂ = −4.78° | 0.0865 | 5.9760 | 18.712° |
| φ₂ = 0 | 0.1739 | 6.1462 | 18.482° |
| φ₂ = +4.78° | 0.2624 | 6.3185 | 18.193° |

**f₁ is real, as a universal-line point.** Put the universal costate on the corner:
H\* = R̄₀ sin φ₁ − 1 − cos φ₁, which vanishes exactly at R̄₀ tan(φ₁/2) = 1 → 18.4960°.
So f₁ is where a universal line of player 1 can leave the φ₂ = 0 edge semipermeably.
That is the same bracket as Eq. (42) read literally, which is why the literal reading
reproduced 18.5 — Finding 6's "sign slip" explains the arithmetic coincidence but not
the meaning. Caveat: that costate is 2.7% outside the corner normal cone.

**f₁c₁ as (0,+1) does not work.** A (0,+1) universal costate at f₁ needs λ_R < 0
(H\* = 3.90 there). The universal line from f₁ that does satisfy everything is (0,−1),
and it runs parallel to the d₁ line at a constant 2.0e−3 — same controls, same
autonomous state ODE, so they cannot meet. In effect f₁–d₁ is one universal line, (0,−1)
throughout.

**c₁ as printed is inconsistent.** Table 2's (5.925, 18.7, +4.78) lies *inside* T₁
(R̄(4.78°) = 5.9748). The universal line at φ₂ = −4.78° gives φ₁ = 18.712° (table 18.7)
and R = 5.976 — so the table's φ₁ fits the φ₂ < 0 side, with R and the sign of φ₂ off.
Also: along every retrograde trajectory in this region R strictly increases
(dR/dτ = cos φ₁ + cos φ₂ > 0), so the corner family never gets below R = R̄₀ = 6.1416.
Any dispersal line involving the corner family, and any c₁ on it, must have R ≥ 6.1416.

**Resolved in Finding 8.** Where the dispersal line e₁c₁ (Table 3: families (−1,−1) and (−1,+1)) actually
meets this universal line. By the R bound, only near f₁ or beyond it (φ₂ > 0).

## Finding 8 — the dispersal line e₁c₁O, solved exactly (option 2)

`python3 layer0/viz/dispersal_e1c1O.py` → `layer0/viz/figs/dispersal_e1c1O.png`

**The missing sheet piece was the peel-offs.** Every point of the d₁ universal line launches
a barrier trajectory to each side: σ₁ = −1 gives λ₁ > 0, σ₁ = +1 gives λ₁ < 0 (since λ̈₁ = −σ₁
there), both self-consistent. They continue the lens sheets past d₁: (−1,−1) continues the
lens-outer family, and (+1,−1) continues the lens-inner family. Invariants on the peel-offs are
1e−14, with no switches for τ ≤ 0.6.

**Method.** An exact 3×3 solve per sheet member, X_corner(s, τ_C) = X_member(τ_B), with fixed-control
state flows (rtol 1e−12). Residuals are ≤ 9e−16. No point-cloud proximity.

| piece | sheets | members meeting | φ₁ range | R − R̄₀ | φ₂ |
|---|---|---|---|---|---|
| e₁ → c₁ | (−1,−1) × (−1,+1) | 54/75 | 18.49° – 36.03° | 5e−5 – 2.2e−3 | −0.067° – −0.002° |
| O → c₁ | (+1,−1) × (−1,+1) | 75/75 | 0 – 18.48° | 0 – 2.2e−3 | −0.067° – 0 |

The 21 non-meeting members are lens-outer trajectories seeded within ~4.5° of e₁. They would
need a corner seed beyond e₁, so the line starts on the corner trajectory from e₁ itself,
at φ₁ = 36.03°. The sheets cross at a clear angle (≈55°), so this is a transversal
intersection, not a graze.

**c₁ = the d₁ universal line × the corner sheet** = (6.14377, 18.4861°, −0.0672°), valid with
residual 1e−17. It is **2.5e−3 from f₁**. Both halves of the dispersal line end there. So
e₁c₁O is closed, and it meets the universal line d₁c₁ exactly as Sec. 4.1 describes.

**Why the earlier contact test missed it.** The whole line sits at τ_C ≤ 0.0011 on the corner
sheet — within the first two integration steps, below the point-cloud stride — and the
peel-offs were not in the lens family at all.

**Geometry.** The whole dispersal line lies within 2.2e−3 in R and 0.07° in φ₂ of the corner
edge. At Fig. 8's scale it is on top of the φ₂ = 0 axis. Magnified 100× in φ₂, it has
exactly the shape Fig. 8 sketches: bowing into φ₂ < 0 from e₁ to c₁ on the universal line,
and back to O.

**Against the paper.** The structure matches: dispersal e₁c₁O, universal line d₁c₁ with (0,−1),
c₁ at its junction, and both zones closed. There are three differences. c₁ coincides with f₁
to 2.5e−3, rather than Table 2's (5.925, 18.7, +4.78), which is inside T. There is no separate
(0,+1) universal line f₁c₁. And the lower half pairs (+1,−1) with (−1,+1), not Table 3's
c₁O entry (+1,−1)(+1,+1), because the corner family is (−1,+1) throughout.

**Still not done.** A watertightness check of the assembled closed zone (mesh assembly). The
mirror zone follows by M symmetry but was not recomputed.
