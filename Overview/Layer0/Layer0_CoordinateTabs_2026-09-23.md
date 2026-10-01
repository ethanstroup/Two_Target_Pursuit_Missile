# Layer 0 — coordinate tabs in barrier_explorer.html (2026-09-23; sizes 2026-09-29; radians 2026-09-30)

**AE 8900 · Ethan Stroup.** Two presentation tabs were added to `layer0/viz/barrier_explorer.html` in `Two_Target_Pursuit_Missile`. They show how world coordinates (x, y) become the reduced state (R, φ₁, φ₂), and how the firing envelope becomes the target set T₁.

## What was added

| file | what it is |
|---|---|
| `barrier_explorer.html` | Tab bar with **Barrier Sheet** (the existing page), **Coordinates** and **φ₂ Sweep**. The new code is scoped under `.lx` / `lx-` and runs in its own script at the end of the file. |
| `los_coords.js` | UMD module. Converts between world and LOS coordinates, computes the target frame, applies rigid motion and integrates world kinematics with RK4. T₁ comes from `Barrier.Rlo/Rhi/PARAMS`, with the same inequalities as `canFire`. |
| `test_los_coords.js` | 11 checks, all passing. Two of them check against the heuristic simulator: `Sim.recoverReduced`, and `Sim.physInit`/`physDeriv`. |
| `test_viz.py` | New §10 runs `node test_los_coords.js`. |
| `README.md` | "Coordinates tabs" section: features, sizes and conventions. |

## Presentation features

**Panel titles.** Title Case, with no A/B/C letters. Each is stored once in the card's `data-title` attribute, and that single string feeds both the page and the captures.
- Coordinates: World Frame (x, y) · Target Frame (Player 2 Body Axes) · Target Set T₁ in (R, φ₁, φ₂).
- φ₂ Sweep: World Frame (x, y) · Unrolled Target Set (φ₂, R) at φ₁ = 0 · Target Set T₁ in (R, φ₁, φ₂).

**Angle axes in radians** (2026-09-30, to match Layer 1's `ell_explorer.html`). This covers every φ₁ and φ₂ axis in the explorer: the Barrier Sheet 3-D view, both face panels, and the teaching tabs.
- **How ticks are chosen.** `angleTicks(lo, hi, maxN)` takes the densest set that fits the axis, stepping through π, π/2, π/4 and π/8. The labels read −π, −π/2, 0, π/2, π and so on. When a view is zoomed in past π/8, it switches to round decimal radians such as 0.1 and 0.05.
- **Axis names carry no unit.** They read φ₁ and φ₂, not "φ₁ [rad]"; Ethan's call, since the π ticks make the unit plain.
- **Internals unchanged.** Barrier Sheet data stay in degrees internally. Only the ticks and labels changed.
- **Still in degrees.** The readouts, status line and φ₂ slider still show degrees.

**Sizes for slides** (2026-09-29).
- Set in one block: search the file for `PRESENTATION SIZES` (`var SIZES = {...}`). The textScale default is 1.6.
- The capture bar has a **text size** slider (100–300 %) and a **lines & markers** slider (100–250 %). Both are stored in localStorage under `layer0.barrierExplorer.sizes.v1`.
- **reset** returns both sliders to `SIZES`.
- What the panels show is exactly what PNG, video and GIF capture.
- All panel titles in a capture share one font size. A title that is too long wraps onto two lines.

**Zoom and pan.**
- World and target-frame panels: the wheel zooms, dragging empty space pans, and double-click or **reset** restores the view.
- Sweep world panel and 3-D panels: shift-drag pans.

**Fly.** Pause/resume and a **scrub** slider. **Spin player 1** is a continuous toggle at 36°/s.

**Capture bar.** Choose the panels, plus **legend** and **stats**, which is the live readout. Then save one of:
- **save PNG**;
- **● record**: H.264 MP4 in Chrome and Edge, WebM otherwise;
- **make GIF**: one full turn, 72, 120 or 180 frames, from an in-page encoder.

## Angle convention (project standard = heuristic_simulator/sim.js)

- φ₁ = ψ − θ₁ and φ₂ = ψ + π − θ₂, both measured clockwise from the LOS.
- dθᵢ/dt = −σᵢ.
- The tests check this against sim.js directly.

## Fix to the engagement-geometry panel

`drawGeometry()` now draws A₁ at −φ₁, which is consistent with sim.js.

## Device-commit gotcha (reproduced)

Committing again from the same staging path reported success but wrote the previous content. The fix is to stage each new version under a new folder (`outputs/viz_v3/`, `viz_v4/`, and so on). After committing, stage the file back and compare md5 hashes. This was done through `viz_v6`, and every copy was verified.
