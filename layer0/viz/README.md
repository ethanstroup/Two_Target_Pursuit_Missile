# layer0/viz — the barrier as a swept surface

`reproduce_figures.py` redraws the figures Davidovitz & Shinar print. This directory does
the other job: it shows how the barrier is *built*. The boundary of the usable part is a
curve; every point of it is a terminal condition fixed by transversality; integrating the
state–costate system retrograde from each one gives a barrier trajectory, and the bundle of
them is the semipermeable sheet.

`../RETROGRADE_METHOD.md` is the written account, surface by surface.

## Files

| file | what it is |
|---|---|
| `bup_curves.py` | ordered seed curves along the (BUP), for all four families |
| `bup_curves.js` | its twin, for the browser — cross-checked point by point by `test_viz.py` |
| `visualize.py` | the static figure set → `figs/` |
| `barrier_explorer.html` | interactive explorer; open it straight from the filesystem |
| `test_viz.py` | 45 acceptance checks |

Both modules call `../barrier.py` / `../barrier.js` for the maths. Nothing here re-derives
anything.

## Running

```
python3 layer0/viz/test_viz.py                      # check first
python3 layer0/viz/visualize.py [outdir] [--tau 1.5] [--nseed 45]
```

The explorer needs no build and no server — open `barrier_explorer.html` in a browser.
It loads `../barrier.js` and `./bup_curves.js` as plain scripts.

- **τ = 0** draws the (BUP) alone, over the target-set boundaries with the Table 2 points
  overlaid, for direct comparison against the printed figures. Raise τ to sweep the sheet.
- **wheel** zooms about the cursor, **drag** pans (rotates, in the 3-D view; shift-drag pans
  there), **double-click** resets one view.
- **wheel-drag** — press the mouse wheel and drag — pans in every view, as in AutoCAD or
  Fusion 360. In the 3-D view it translates the whole scene; a wheel press never pins a
  trajectory.
- **click** selects a trajectory in any of the three views; **play** then walks the marker
  along it as τ elapses, and **focus** hides everything else while you watch.
- **corner + universal** on maximum range adds the two barrier pieces that are not
  roots of Eq. (32): trajectories seeded on the φ₂ = 0 corner edge O–e₁ (and O–e₁′), with
  the corner costate of Eqs. (39)–(41), and the universal line of player 1 from d₁ (and d₁′),
  flown with the singular control σ₁ = 0 and stopped at c₁, where it meets the corner sheet.
  The universal lines are drawn thick in amber.
- **corner + universal** on the off-boresight walls φ₁ = ±β adds the wall's two corners
  (Sec. 3.3), neither of which is a root of Eq. (62):
  - the **max-range corner B₁–A₁** (green), costate Eqs. (66)–(67) with Eq. (68)
    corrected (it is μ̄₂, and the sign is sgn φ₁, not sgn φ₂). Its terminal pair is
    (−sgn φ₁, +sgn φ₂), not Eq. (70)'s −sgn(sin φ₂). With that pair the two halves cross
    in retrograde time along the evader's dispersal line B₁C₁ through Table 2's C₁; with
    Eq. (70)'s pair they would diverge from B₁.
  - the **min-range corner N₁–Z₁–m₁** (red), costate Eqs. (53)–(56) with both μ's
    multiplied by −1, terminal pair Eqs. (57)–(58). The text's "M₁" for this corner is
    Table 2's m₁.

  Each corner is split where the evader's terminal control changes sign — at B₁ and at
  Z₁ — so each chip carries one pair. The min-range corner's trajectories are flown at
  DT/4 because they pass close to R = 0 late in τ.
- **φ₂ = ±π seam** — a (BUP) branch that runs across the seam (the off-boresight walls, and
  the minimum-range branches) is drawn as separate runs rather than joined by a chord across
  the plot. On the walls each run ends exactly on the seam; that one state is flown once and
  drawn at +180° and at −180°. The minimum-range seam point is singular (λ₂ = λ̇₂ = 0), so
  those branches are only cut; their nearest seeds sit within 0.3° of the seam.
- **target set** draws T₁ (Eqs. 6–9, the box of D&S Fig. 3) semi-transparent in the 3-D
  view, with the usable part of each boundary surface shaded: Eq. (32) on the max-range top,
  Eq. (46) on the min-range bottom, Eq. (62) on the φ₁ = ±β walls. The family currently
  shown is shaded darker. Turning it on reframes the 3-D view to hold the whole box; wheel
  to zoom back in.
- **segments** — every piece has a chip under the 3-D view; click it to hide or show that
  piece in all three views. Each maximum-range lens is split at its fold d₁, so its two
  halves (different σ₁) switch separately; likewise the off-boresight wall's (BUP) is split
  at Q₁ (φ₂ = ±90°), where σ₂ changes sign by Eq. (65) — N₁–Q₁ (−1,−1) and Q₁–m₁ (−1,+1)
  on φ₁ = +β. Q₁ itself is singular (the evader's universal line starts there), so each
  half ends 1e−4 rad short of it. Chips show the control pair on each piece.
  **all on** restores everything; the on/off state survives changing τ or the seed count.
- **save PNG** stitches the three trajectory views into one image for a deck.

## Ordering

Seeds are ordered along each (BUP) branch by continuation, not by sweeping φ₂: roots are
matched to the branch they continue, branches that die together at a fold are spliced, runs
meeting across the φ₂ = ±π seam are merged, and resampled points are snapped back onto the
defining root. Without that the bundle is a pile of curves rather than a surface. The two
implementations must agree — `test_viz.py` compares them seed by seed and fails past 1e−9.
