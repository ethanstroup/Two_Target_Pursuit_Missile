# Layer 0 — D&S Sec. 3.3 Read-Through: Off-Boresight Limit Surfaces (2026-09-21)

**AE 8900 · Ethan Stroup.** I checked Section 3.3 equation by equation against the layer0 code (`barrier.py`). Every point below was computed, not transcribed. The corner seeding is now in the repo (see Code state). The B₁C₁ and Q₁ checks were run from scratch scripts (`b1c1_check.py`, `q1_univ.py`); the B₁C₁ solve is also repeated in `test_viz.py` §9.

## What Sec. 3.3 sets up (φ₁ = +β; φ₁ = −β is the mirror image)

The face φ₁ = β has a usable part bounded by three pieces.

| piece | where | costate | terminal pair |
|---|---|---|---|
| smooth BUP, R = L·sgn φ₁ | N₁ → ±π → Q₁ → m₁ | Eq. (63), corrected: λ = (0, R sgn φ₁, 0) | (−1,−1) on N₁…Q₁ and (−1,+1) on Q₁…m₁ (Eq. 65) |
| min-range corner | N₁ → K₁ → Z₁ → m₁ | Eqs. (53)–(56) with μ × (−1) | (−1,+1) for φ₂ < 0 and (−1,−1) for φ₂ > 0; the switch is at Z₁ |
| max-range corner | A₁ → B₁ → A₁ (all φ₂) | Eq. (66), with Eq. (68) corrected | (−1,−1) for φ₂ < 0 and (−1,+1) for φ₂ > 0; this is **not** what Eq. (70) says |

Here L = sin φ₁ + sin φ₂.

These points match Table 2 at its printed precision:

- m₁ = (0.8470, 8.044°)
- N₁ = (0.2789, −154.646°)
- Q₁: R = 1.7071
- h₁ = (0.5347, 92.919°)
- g₁ = (0.2665, −160.923°)

A corner is part of the BUP only where exactly one of its two faces is usable. That is also the condition for a costate with both μ > 0 and H\* = 0. On the min-range corner this gives two separate pieces:

- **N₁–Z₁–m₁** (Sec. 3.3). The boresight face is usable, and the μ signs are flipped.
- **h₁–±π–g₁** (Sec. 3.2's h₁g₁). The min-range face is usable.

The gaps (m₁, h₁) and (g₁, N₁) are not usable on either face.

## Findings

1. **"M₁" in the Sec. 3.3 text means m₁.** The text says the NUP is bounded by "N₁Q₁M₁" and that the corner runs "between M₁ and N₁". Fig. 6 labels that point m₁. Table 2's M₁ = (0.25, 45°, ±180°) lies on the other corner piece.
2. **Eq. (68) has two typos.**
   - It is printed as μ̄₁ but should be μ̄₂.
   - It uses sgn φ₂ where sgn φ₁ belongs. The corrected form is μ̄₂ = q̄[R̄ − L sgn φ₁].
   - As printed, H\* reaches up to 9e−2 wherever sgn φ₁ ≠ sgn φ₂. With the correction, H\* ≤ 2e−16, and the costate agrees with `lam_corner`'s independent solve.
3. **Eq. (70) has the wrong sign, and Sec. 4.2's text repeats the error.**
   - Eq. (66) gives λ₂ = μ̄₂(1 + cos φ₂) sgn φ₂ with μ̄₂ > 0, so Eq. (22) gives σ₂\* = +sgn φ₂, not −sgn(sin φ₂). The printed form looks copied from Eq. (58).
   - Fig. 10's labels agree with the derivation: (−1,1) left of B₁ (φ₂ > 0) and (−1,−1) on the right.
   - The dispersal line settles it. With the derived pairs, the two A₁B₁A₁ families cross in retrograde time along a line from B₁ through Table 2's **C₁**: computed (4.296, 113.92°, −25.32°) against printed (4.3, 113.87°, −25.27°). With Eq. (70)'s pairs they would diverge, and no B₁C₁ could exist.
4. **Q₁ universal line (evader).**
   - The singular control is exactly σ₂ = 0: λ̈₂ = A·σ₂ with A = −λ_R cos φ₂ + λ₁ sin φ₂/R, and there is no σ-free term on the arc.
   - Flown retrograde from Q₁ with (−1,0), the line passes **J₁ at τ = 0.020** and **D₁ at τ = 1.835**, each within 2.2e−4 of Table 2.

## Code state (updated later the same day)

Both corners are now seeded on both walls, in Python and JS, and committed to `layer0/viz`. `test_viz.py` passes **45/45** (it was 32).

- **`bup_curves.py` / `.js`** — new functions:
  - `min_corner_ends`: m₁ and N₁ in closed form.
  - `lam_corner_max`: Eqs. (66)–(67), with Eq. (68) corrected.
  - `lam_corner_min`: Eqs. (53)–(56), with the μ flip.
  - `boresight_corner_seeds(sgn, n)`: returns the pieces max+, max−, min− and min+, split at B₁ and Z₁.
- **Control checks** (test_viz §9):
  - Every seed has FI = 1 and H\* = 0 to 1e−15.
  - Every costate lies in the normal cone (μ ≥ 0) and matches `lam_corner` to 7e−16.
  - The max-range corner pair is (−sgn φ₁, +sgn φ₂) at every seed, and the min-range corner pair follows Eqs. (57)–(58).
  - The B₁C₁ line passes through C₁. With Eq. (70)'s pairs, the two halves separate from B₁ instead.
  - The −β wall is the exact mirror of the +β wall.
- **Explorer:**
  - On the off-boresight families, "corner + universal" now adds four chips: the max-range corner in green and the min-range corner in red.
  - The min-range corner is flown at DT/4. Its trajectories pass near R = 0 late in τ, and at full DT the invariants degrade to 7e−6.
  - Branches that cross the φ₂ = ±π seam are drawn as separate runs, so the chord across the plot is gone. On the walls, each run ends exactly on the seam. The min-range seam point is singular (λ₂ = λ̇₂ = 0, where the integrator chatters), so those branches are only cut.
  - Pressing the mouse wheel and dragging pans every view; in 3-D it translates the whole scene.

## New finding: some BUP seeds fly back into T₁

This came from checking in_target along each retrograde path, out to τ ≤ 3.

- **Wall BUP.** Seeds from about 138° through ±180° to N₁ enter T₁ immediately and stay inside. The (−1,−1) path meets the wall from the inside there, because φ̈₁ = C/R < 0. This is consistent with Sec. 4.3's remark that no barrier trajectory terminates on Q̄₁N₁.
- **Min-range corner N₁–Z₁.**
  - Seeds beyond about −124° re-enter T₁ somewhere between τ ≈ 0 and 0.53. That makes them closed trajectories, which should be cut where they re-enter.
  - The grazing seed is at −124.06°; Table 2's q₁ is at −124.34°.
  - That seed touches T₁ again at the wall's own min-range corner, near φ₂ ≈ 170°. Sec. 4.4 says these trajectories end on K₁′q₁′ instead. So the q₁ match is suggestive, not a reproduction.
- **Max-range lens.** Seeds with φ₂ ∈ (−3.5°, 0) pass briefly through T₁, for τ between 0.001 and 0.067.

The explorer still draws every trajectory in full. I offered Ethan an option to cut each trajectory where it re-enters T₁, but it is not built.

## Next steps

1. Decide whether to cut trajectories where they re-enter T₁. This affects every family.
2. Move the B₁C₁ dispersal solve and the Q₁/J₁D₁ universal line into the repo.
3. Optionally add the h₁g₁ piece of the min-range corner. It is the min-range face's BUP and belongs to the 'min' family.
4. Work through the Sec. 4.2/4.3 structure: a₁E₁, H₁C₁, E₁G₁, G₁D₁, the switch line A₁a₁, and the S₁U₁ commuting line.
