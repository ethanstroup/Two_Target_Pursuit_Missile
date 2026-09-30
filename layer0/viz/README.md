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
| `los_coords.js` | world frame (x, y, heading) ↔ (R, φ₁, φ₂), for the coordinates tabs; T₁ comes from `../barrier.js` |
| `test_los_coords.js` | 11 checks on `los_coords.js`, including against `../../heuristic_simulator/sim.js`; `test_viz.py` §10 runs it |
| `test_viz.py` | 45 acceptance checks, plus the 11 from `test_los_coords.js` |

Both modules call `../barrier.py` / `../barrier.js` for the maths. Nothing here re-derives
anything.

## Running

```
python3 layer0/viz/test_viz.py                      # check first
python3 layer0/viz/visualize.py [outdir] [--tau 1.5] [--nseed 45]
```

The explorer needs no build and no server — open `barrier_explorer.html` in a browser.
It loads `../barrier.js`, `./bup_curves.js` and `./los_coords.js` as plain scripts.

- **τ = 0** draws the (BUP) alone, over the target-set boundaries with the Table 2 points
  overlaid, for direct comparison against the printed figures. Raise τ to sweep the sheet.
- **wheel** zooms about the cursor, **drag** pans (rotates, in the 3-D view; shift-drag pans
  there), **double-click** resets one view.
- **R locked / free 3-D / top view**: the buttons in the 3-D view's top-left corner.
  - **R locked** (the default) is an oblique view. The (φ₂, φ₁) floor turns and tilts,
    but R is always drawn straight up at full length.
  - **free 3-D** is a true, rigid rotation. R shortens with elevation, and from directly
    above you see the (φ₂, φ₁) plane. Elevation stops at ±90° in both modes, so the view
    never turns upside down; drag sideways to spin about R.
  - **top view** goes straight down with φ₂ increasing to the left and φ₁ up, the same
    orientation as the face (φ₂, φ₁) panel, and switches to free 3-D.
  - The default view (az −155°, el 22°) has φ₂ increasing to the left, as printed. The
    3-D box is proportioned φ₂ : φ₁ : R = 2 : 1 : 1, with one scale for both screen axes.
- **resizing panels** — drag the gutter between two panels to move the split, a panel's
  bottom edge to change its row's height, or the grip in its bottom-right corner to do both.
  Canvases fill their panels and redraw as they change. The layout is remembered in this
  browser; **reset layout** puts it back.
- **select** (toolbar) turns hover-selecting and click-pinning on and off. Off, moving or
  clicking the mouse over a view changes nothing and no trajectory is highlighted; rotate,
  pan and zoom still work, and the lower panels keep the last selection.
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

## Coordinates tabs

The tab bar under the title switches between **Barrier Sheet** and two teaching views,
**Coordinates** and **φ₂ Sweep**. The page remembers the last tab you used in this browser.
Panel titles are in Title Case and are written once, in each card's `data-title`, so the page
and the captures always show the same title.

- **Coordinates** has three linked panels:
  - **World Frame (x, y)**
    - Drag either aircraft, or the handle at its nose, and the ψ, φ₁ and φ₂ arcs follow, as
      in D&S Fig. 1.
    - **envelope in world** draws player 2's firing envelope around it; the envelope turns
      with player 2.
  - **Target Frame (Player 2 Body Axes)**
    - Player 2 sits at the origin, nose up, as in Fig. 2.
    - The panel is drawn from (R, φ₁, φ₂) alone. Player 1 sits at (−R sin φ₂, R cos φ₂),
      and its nose must lie in the ±β cone about the line of sight.
  - **Target Set T₁ in (R, φ₁, φ₂)**
    - T₁ is drawn as in Fig. 3, with the current state as a dot: green in T₁, red outside.
    - **φ₂–R** turns the box to the unrolled side view.
  - **Zoom and pan in the world and target-frame panels**
    - The wheel zooms about the cursor.
    - Dragging empty space pans. So does a middle-drag or shift-drag anywhere.
    - A double-click or the **reset** button restores the view.
  - **rigid motion** rotates and translates the whole world. It reports the largest change
    in (R, φ₁, φ₂), which stays at rounding level: only ψ moves.
  - **↻ spin player 1** turns player 1 continuously, at 36°/s, until pressed again. The
    state runs parallel to the φ₁ axis.
  - **fly** integrates unit-speed kinematics with the chosen σ₁ and σ₂ and traces the path
    in all three panels.
    - **pause** stops the flight.
    - **scrub** moves back and forth along the recorded path.
    - **resume** carries on from the point shown. Anything after that point is re-flown, so
      a σ changed while paused takes effect from there.
  - **grid carry** colors points inside the envelope by φ₂ and carries them into the box.
- **φ₂ Sweep**: player 1 holds φ₁ = 0 at range R while player 2 turns.
  - Ways to turn player 2:
    - press and drag in the world panel;
    - drag in the unrolled plot;
    - use the slider;
    - press **play**, which turns it at 36°/s.
  - The envelope turns with player 2. The amber segment along the line of sight is R̄(φ₂),
    and the matching slice of the box is highlighted.
  - R̄ is 3 + π nose-on and 3 tail-on.
  - The world panel zooms with the wheel and pans with shift-drag or middle-drag.
- **Capture**: the capture bar in each tab exports the selected panels side by side, each
  under its title. Underneath go the tab's legend and its readout (**stats**), both optional
  and both at the same size. The stats are read live, so they change during a video or GIF.
  - **save PNG** writes one image.
  - **● record** starts a video and **■ stop** ends it and downloads it. Switching tabs also
    stops the recording. Chrome and Edge write H.264 MP4, which plays in PowerPoint. A browser
    without an H.264 recorder writes WebM instead, and the status line says so.
  - **make GIF** renders one full turn of the tab into a looping GIF, frame by frame. It does
    not record in real time, so the file is ready when the status line says so.
    - On Coordinates, you choose whether player 1 or player 2 turns. The full 360° path is
      drawn in the box and the state dot moves along it.
    - On φ₂ Sweep, player 2 turns.
    - Choose 72, 120 or 180 frames, and 1200, 1600 or 2400 px wide, or full size. A full turn
      lasts about 10 s at any frame count.
    - The page is held still while the GIF renders and returns to where it was afterwards.
  - Tab canvases are backed at 2× or more, so captures are sharp on a 1× screen too.
- **Sizes for slides**: the capture bar's **text size** and **lines & markers** sliders
  control how big things are drawn. What the panels show is exactly what PNG, video and GIF
  captures get.
  - **text size** (100–300 %) scales every piece of text: tick values, axis names, in-plot
    labels, the status lines, and the capture's panel titles, legend and stats.
  - **lines & markers** (100–250 %) scales line widths, aircraft, dots and arrowheads. The
    data still fills each panel.
  - The sliders are remembered in this browser. **reset** returns them to the file's defaults.
  - Those defaults, and every base size, are in one block near the top of the tabs' script.
    Search `barrier_explorer.html` for `PRESENTATION SIZES`. Each entry says what it controls.
  - All panel titles in a capture share one font size. A title too long for its panel wraps
    onto two lines instead of shrinking on its own.

Conventions (`los_coords.js`) are those of `heuristic_simulator/sim.js`: φ₁ = ψ − θ₁,
φ₂ = ψ + π − θ₂ and dθᵢ/dt = −σᵢ, where ψ is the line-of-sight direction from player 1 to
player 2. So both angles are measured clockwise, φ₁ > 0 puts player 2 on player 1's left, and
σ = +1 is a right turn. With unit speeds these reproduce `Barrier.stateDot` (checked by finite
differences). The mirror image — counterclockwise angles, dθ/dt = +σ — satisfies the same
equations, so `test_los_coords.js` also checks against `Sim.recoverReduced` and `Sim.physDeriv`
directly. The engagement-geometry panel on the barrier tab uses the same sense.

## Ordering

Seeds are ordered along each (BUP) branch by continuation, not by sweeping φ₂: roots are
matched to the branch they continue, branches that die together at a fold are spliced, runs
meeting across the φ₂ = ±π seam are merged, and resampled points are snapped back onto the
defining root. Without that the bundle is a pile of curves rather than a surface. The two
implementations must agree — `test_viz.py` compares them seed by seed and fails past 1e−9.
