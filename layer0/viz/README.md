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
| `explorer.css` | responsive presentation styles; local and dependency-free |
| `workspace_chrome.js`, `test_workspace_chrome.js` | compact navigation and settings drawer; focus, Escape, and tab-switch checks with DOM doubles |
| `dock_layout.js` | pure split-tree operations, minimum sizes, drop zones, and saved-layout validation |
| `dock_workspace.js`, `dock_workspace.css` | drag-to-dock, split resizing, keyboard controls, and layout persistence |
| `test_dock_layout.js`, `test_dock_workspace.js` | docking model and controller tests; controller tests use DOM doubles, not visual browser checks |
| `barrier_export.js` | barrier appearance controls, PNG composition, growth GIF timing, progress, and cancellation |
| `barrier_render_cache.js` | exact prefix bounds and cached curve simplification for live drawing; original integration samples are retained |
| `test_barrier_render_cache.js`, `benchmark_barrier_render.js` | error-bound, playback, and cache checks; repeatable CPU/draw-command benchmark using canvas doubles |
| `gif_encoder.js` | shared local GIF encoder used by all three views |
| `test_barrier_export.js`, `test_barrier_render.js`, `test_gif_encoder.py` | export/controller checks, renderer checks with canvas doubles, and independent GIF decoding with Pillow |
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
It loads `../barrier.js`, `./bup_curves.js`, `./los_coords.js`, `./dock_layout.js`,
`./dock_workspace.js`, `./workspace_chrome.js`, `./gif_encoder.js`, `./barrier_export.js`,
and `./barrier_render_cache.js` as plain scripts. Keep `explorer.css` and
`dock_workspace.css` beside it for the interface styles.

### Explorer interface

The three views are **Barrier surface**, **Coordinates**, and **Aspect sweep**.
The boundary-family selector, backward-time slider, Play, Reset views, and Export PNG
sit together directly above the barrier plots. One slim status row combines the surface
stage, trajectory count, and selected range/angles.

The buttons beside the view tabs open a right-side settings drawer on **Barrier surface**:

- **Display:** visible layers, hover selection, isolation, seed count, and view presets.
- **Export & appearance:** PNG, growth GIF, and text/line sizing.
- **Layout:** arrangement presets, Reset layout, and docking/resizing instructions.
- **Help:** the introductory explanation, notation, and plot gestures.

The drawer overlays the page without moving or resizing the plots. You can continue
interacting with the visible workspace while it is open. Switch sections inside the
drawer, close it with **×** or **Esc**, or click its active toolbar button again. Closing
returns keyboard focus to the opener. Escape remains available to active docking gestures
and modal export/Move dialogs. Switching view tabs closes the barrier drawer.

All six workspace panels remain available, including physical geometry, costates,
invariants, and the complete state readout. **Legend & branches** and **Numerical details**
remain below the workspace. Coordinates and Aspect sweep retain their own expandable
**Export & appearance** controls, including video recording; **Fly this engagement**
holds the coordinate view's flight controls.

Arrow keys, Home, and End navigate the view tabs. Branch controls and disclosures work
with the keyboard.

### Docking and resizing

All six panels on the **Barrier surface** page share a docking workspace:

- Drag a panel by its title bar. A shaded preview shows the destination. Drop near another
  panel's **left, right, top, or bottom edge** to create a split, or in its **center** to swap
  their positions. Empty slots collapse automatically. The page scrolls near the viewport
  edge while dragging, so bottom panels can be moved up.
- Drag any divider to resize its neighboring panels. Minimum sizes keep plots usable.
  Focus a divider and use arrow keys to resize with the keyboard; Shift makes larger steps.
- Drag the handle below the entire workspace to change its height. It also supports Up/Down
  keys and Shift for larger adjustments.
- **Esc**, pointer cancellation, or loss of focus cancels an in-progress drag or resize.
  Releasing a dragged panel outside a valid destination leaves the layout unchanged.
- Each title bar's **Move** button provides an alternative: choose a target panel and a
  direction, or choose **Swap places**. This also works with the keyboard.
- **Analysis · 3D + costates** places Costates & invariants beside the 3D view in one step.
  **Overview** / **Reset layout** restores the original six-panel arrangement.
- Dock positions, split ratios, and workspace height persist locally in this browser.
  Existing view transforms and canvas elements survive a move. Corrupt saved layouts fall
  back to Overview; if browser storage is unavailable, docking still works for the session.
- Below 760 px, panels stack in the layout's traversal order; use **Move** to reorder them.
  Returning to a wider window restores the desktop splits. Complex desktop layouts can
  scroll horizontally instead of squeezing panels below their minimum sizes.

Run the docking checks with:

```sh
node --test layer0/viz/test_dock_layout.js layer0/viz/test_dock_workspace.js
```

### Barrier export and appearance

Open **Export & appearance** on **Barrier surface**:

- Choose the plots to include: 3D surface, either projection, engagement geometry, and/or
  costates & invariants. By default the 3D view sits beside the two stacked projections
  in the exported image. Other selections use one or two columns. Panel proportions follow
  their current docked sizes. The state readout is not part of the image.
- **Save PNG** captures the current τ, family, visible layers, and camera. The main toolbar's
  **Export PNG** uses these same panel choices. Image widths are 1200, 1600, or 2400 px.
- **Make growth GIF** renders from τ = 0 to **GIF maximum τ** (0.01–6). Set the growth
  duration (2–20 seconds) and number of frames (60, 90, 120, or 180). The final frame holds
  for one additional second before looping. More frames require at least 0.02 seconds per
  frame; an incompatible duration shows a validation message.
- GIFs retain the current family, layer visibility, camera, selected trajectory, and marker
  fraction. Automatic plot bounds use the requested maximum τ for the entire animation;
  existing manual zoom and pan are honored. Canvases retain their dimensions while exporting.
- Rendering shows progress and supports **Cancel export** or **Esc**. Success, cancellation,
  and errors restore the previous τ and resume Play if it was running.
- **Text size** (100–300%) scales plot labels, tick values, exported titles, and the export
  caption. **Lines & markers** (100–250%) scales strokes, dots, and arrowheads. Changes appear
  in the live plots and both export formats. These settings persist locally and have their
  own **Reset appearance**, separate from the other tabs' appearance settings.
- **3D surface transparency** (0–100%, default 50%) fades the barrier sheet and target-set
  shading without fading trajectories, outlines, or markers. At 100%, surface fills are
  hidden. The setting is saved with the other appearance controls and applies to PNG/GIF
  exports as well. The 2D projections are unaffected.
- All processing is local; exports need no network, server, or additional browser libraries.

Export checks (the Python check needs Pillow and Node.js on PATH):

```sh
node --test layer0/viz/test_barrier_export.js layer0/viz/test_barrier_render.js
python layer0/viz/test_gif_encoder.py
```

### Plot interactions

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
- **angle axes are in radians**, like Layer 1's `ell_explorer.html`. This covers the φ₁ and φ₂
  axes of the 3-D view, both face panels and the teaching tabs. The axis names carry no unit,
  since the π ticks make it plain.
  - Ticks sit at multiples of π/2, π/4 or π/8 (−π, −π/2, 0, π/2, π …) while those fit the
    axis, as dense as the axis can carry.
  - In a view zoomed in past that, they switch to round decimal radians (0.1, 0.05 …).
  - Data are still stored in degrees internally; only the ticks and labels changed.
  - Readouts, the status line and the φ₂ slider still show degrees.
- **resizing panels** — drag the split dividers or the workspace's bottom height handle.
  Canvases fill their panels and redraw as they change; see Docking and resizing above.
- **Hover selection** (Display & sampling) turns hover-selecting and click-pinning on and off. Off, moving or
  clicking the mouse over a view changes nothing and no trajectory is highlighted; rotate,
  pan and zoom still work, and the lower panels keep the last selection.
- **click** selects a trajectory in any of the three views; **Play** then walks the marker
  along it as τ elapses, and **Isolate selection** hides the other trajectories while you watch.
  Switching to another tab pauses the barrier animation.
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
  On the primed wall, **N₁′–Q₁′ is deep red** and **Q₁′–m₁′ is light red** for their
  trajectories and surfaces. BUP seed curves remain black in every view. The unprimed
  wall retains its blue trajectory and surface colors.
  **all on** restores everything; the on/off state survives changing τ or the seed count.
- **Export PNG** captures the panels chosen in **Export & appearance**, under their titles.

### Growth performance

The current family's trajectories are integrated through τ = 6 when the family, seed
count, or corner/universal setting changes. Scrubbing and Play use those existing samples;
they do not load data or repeat integration.

- Exact prefix bounds are cached in blocks and shared by the projections and 3D view.
  Backwards scrubbing, hidden branches, and isolated trajectories retain their correct bounds.
- Live trajectory lines use a cached subdivision hierarchy with a maximum approximation
  error of 0.35 CSS pixels after projection. Zooming refines the lines as needed. The seed
  and current endpoint remain exact. Integration samples, selection, switches, state
  readouts, costates, and invariants retain their full numerical resolution.
- PNG/GIF exports draw every original trajectory sample at high resolution. Live canvases
  use native screen resolution and reuse their backing bitmap until their size changes.
- Surface cells use stable stations and include the growing endpoint. Old cells no longer
  change spacing on each playback step.
- Play and high-frequency interaction redraws share the browser's animation-frame queue.
  Playback uses elapsed time at the original speed and pauses its clock in background tabs.

Run performance-related checks and the drawing benchmark with:

```sh
node --test layer0/viz/test_barrier_render_cache.js layer0/viz/test_barrier_render.js
node layer0/viz/benchmark_barrier_render.js
```

The benchmark uses no-op canvas calls, so its CPU timings are **not browser FPS**.
At 45 seeds/branch (184 maximum-range trajectories, 547,126 samples), the optimization
reduced `lineTo` calls at τ = 6 from 1,708,305 to 123,951 and eliminated the ten repeated
canvas dimension assignments per frame. Use `--baseline` to compare against the currently
committed HTML; this is useful while evaluating an uncommitted rendering change.

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
