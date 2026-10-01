# Layer 1 — M1 explorer: ℓ(x) in 3-D

**AE 8900 · 2026-09-30, v5 on 2026-10-01 · Ethan Stroup**
File: `Two_Target_Pursuit_Missile/layer1/viz/ell_explorer.html`. It is saved in the repo and was checked by md5 after each write. It is one standalone page with no build step and no server, and it opens straight from the filesystem. Companion to `claude/Layer1_M1_Explainer.md`.

## What it shows

ℓ(x) = max(|φ₁| − β, R_lo(φ₂) − R, R − R_hi(φ₂)) in its **raw** (unweighted) form, over R ∈ [0.2, 12] and φ₁, φ₂ ∈ [−π, π). The page evaluates ℓ itself in JS. The weighting choice (raw, plan or sdist) does not change the sign or the zero level set.

- **Point cloud (the default view).** 20,000 random samples by default, adjustable from 1k to 40k. Points are drawn only for values in [min, 8]. Opacity is "fade with ℓ": 0.70 · (floor + e^(−ℓ/w)), with w = 0.75. Uniform opacity is the other option.
- **Colors.** Stepped bands.
  - Inside T₁ (−0.2, −0.4, −0.6), blue **darkens with depth**.
  - Outside (0.5, 1, 1.5), red is **darkest next to the boundary** and lightens with distance. This order was flipped on request on 2026-10-01, so the region just outside T₁ stands out. Combined with the fade, near-boundary outside points are both dark and solid.
- **Isosurface ℓ = 0.** Drawn as dots by default: one dot wherever an edge of the render grid crosses zero. The grid is 48 per axis by default (range 20–100). The **shaded** style draws the marching-cubes triangles through the same dots.
- **Slice.** A plane at fixed φ₁, φ₂ or R.
  - *In the 3-D view*, the slice is a faint grey sheet, about 13 % opaque, with its ℓ = 0 contour bold and its slab's two faces dashed.
  - *In the flat panel*, the slice shows **the 3-D plot's own dots that lie within a slab around the plane**, projected onto it. The slab is ± a fraction of the axis (slider; default ±2.5 %, which is ±0.157 rad). The dots keep the same color and the same opacity as in 3-D, faintest drawn first. This makes it visibly a slice of that plot rather than a separate sampling.
  - The flat panel shows cloud points when the cloud is shown and isosurface dots when the isosurface is shown.
  - ℓ = 0 on the plane is bold, and T₁ from the closed form is an amber dashed line.
  - Hovering a dot reads out its true 3-D state and marks the same dot in the 3-D view. A plane has no thickness, so a dot inside the slab near the boundary can sit just across the bold line.
- **T₁ edges, closed form**, in the 3-D view. **Hover readout** works in both views.

## Capture (as in Layer 0)

The capture panel follows Layer 0's capture bar:

- **What goes in.** Tick the panels (3-D view, slice) plus legend and stats. The selected panels are placed side by side, each under its title. The stepped colorbar, the legend entries and the status line go underneath. Panel titles share one font size and split at the best word break when too wide (Layer 0's rule).
- **Save PNG.**
- **Record.** Captures a video of the ticked panels while you work: H.264 MP4 in Chrome and Edge (plays in PowerPoint), WebM elsewhere.
- **Make GIF.** Renders one loop frame by frame with Layer 0's in-page encoder: 255-color palette, changed-rectangle frames, about 10 s per loop. The loop is either a full turn of the 3-D view or a sweep of the slice (once round its angle, or bottom to top in R). There are 72, 120 or 180 frames, at 1200, 1600 or 2400 px wide, or full size. The view and the slice return to where they were afterwards.
- **Sizes and file names.** The text-size and lines & markers sliders apply to everything. Files are named `layer1_m1_[loop_]<panels>_<timestamp>.<ext>`.

## Layout: docking panels

There are five panels, at the leaves of a split tree. The **default layout** is one row:

- 3-D view (38.7 %)
- slice (35.1 %)
- a right column (26.2 %) with legend on top and readout | capture below.

Moving and resizing:

- **Move.** Drag a panel by its title bar (⠿).
  - Dropped on another panel's edge, it docks beside that panel.
  - Dropped on another panel's middle, the two swap.
  - Dropped on an edge of the whole area, it takes that side.
  - Esc cancels.
- **Resize.** Gutters resize their two neighbors (minimum 140 px); double-clicking a gutter evens them.
- **Save and reset.** The layout is stored in the browser under `layer1.ellExplorer.layout.v1`. **Reset layout** restores the default.
- **Hiding the slice** collapses its panel.

**Axes and view match Layer 0's 3-D panel.** φ₂ runs across, increasing to the left. φ₁ runs into the picture and R points up. The box is proportioned 2 : 1 : 1, the angles are labeled in radians, and the default view is az −155°, el 22°. The R locked, free 3-D and top view buttons are all there. Constants come from `../../layer0/barrier.js` and are checked against an inline copy. three.js r128 comes from cdnjs, with jsDelivr as a fallback.

## The τ data path (built, not yet fed)

Rendering only touches a **Field** interface: `domain`, `taus`, `range()`, `sampleGrid`, `sites`, `sampleSites` and `valueAt`. There are two implementations:

- `AnalyticField`: ℓ, static.
- `GridField`: node values, one array per τ, trilinear and periodic in both angles. Its cloud sits on the nodes, so a slab narrower than half the node spacing shows exactly one node layer.

To show `m3_out/Vsnap_101x102_T6.npz`, call `EllExplorer.setField(new EllExplorer.GridField({axes: {R, phi1, phi2}, taus, data}))`. The arrays must be in C order (R, φ₁, φ₂), with the angle axes on [−π, π) and endpoint=False. The τ slider then enables itself, and everything follows it. **Not yet written:** the npz reader or converter. Carry M3's R ≥ 0.45 mask when quoting {V ≤ 0}.

## Verification (headless Chromium, four suites, all green)

- **JS ℓ against `ell.py` (raw):** 212,033 points; 212,029 are bit-identical, and the largest difference is 8.9e−16. There are 0 sign mismatches against plan and sdist, and 0 against `barrier.in_target`.
- **Mesh:** closed, manifold and consistently oriented at 20³–97³. The volume compared with the closed-form T₁ (7.170 %) is −4.95 to −0.16 %. At 48³ it agrees with scikit-image's marching cubes to 2e−10.
- **Slab slice:**
  - At the default settings, 981 cloud dots fall within ±0.157 rad of φ₁ = 0, and none are missed.
  - The dots are drawn faintest first.
  - Hovering one reads out exactly that cloud point.
  - In isosurface mode the panel shows the 248 isosurface dots in the slab.
- **Colors:** luminance rises with ℓ outside and falls with depth inside.
- **Capture:**
  - PNG with both panels, the slice only, and none ticked (a message).
  - Video (WebM in headless Chromium).
  - GIF turn and GIF sweep, 72 frames each, with the view and the slice restored afterwards.
- **Docking:** gutters, dock beside, swap, edge dock, Esc, hiding the slice, persistence over a reload, and reset, all by real mouse drags.
- **Defaults:** a fresh load reproduces the 2026-10-01 screenshot exactly (19,219 of 20,000 points shown, 1,503 inside; same panel widths).

## Open

- ~~`layer1/` on the laptop holds only the M1/M2 files.~~ **Resolved 2026-10-01: false alarm.** Ethan confirms the M3 scripts and `m3_out/` (including `Vsnap_101x102_T6.npz`) are in his computer folder. The remaining step is the npz reader or converter.
