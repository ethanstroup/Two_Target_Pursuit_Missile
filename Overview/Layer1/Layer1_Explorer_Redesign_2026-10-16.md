# Layer 1 — explorer v8: the interface redesigned after Layer 0

**AE 8900 · 2026-10-16 · Ethan Stroup**

- **File:** `Two_Target_Pursuit_Missile/layer1/viz/ell_explorer.html`. It is still one standalone
  page that opens from the filesystem with no build step.
- **Model:** Layer 0's barrier explorer (`layer0/viz/barrier_explorer.html`, `explorer/explorer.css`,
  `workspace_chrome.js`, `dock_workspace.js`, `barrier_export.js`). Its patterns are copied inline,
  not linked, so the Layer 1 page stays self-contained.
- **Companion records:** `Overview/Layer1/Layer1_M1_Explorer_2026-09-30.md` and
  `Overview/Layer1/Layer1_M5_Explorer_2026-10-16.md`.

> **Since v9 (2026-10-29).** The slice panel has a second style, *regions*: every grid node on
> the plane as a solid cell (`Overview/Layer1/Layer1_Explorer_SliceMap_2026-10-29.md`). The
> presets below are unchanged. Hidden panels no longer leave a gap in their split.

The science is unchanged:
- the fields;
- the load-time checks;
- the M5 partition;
- the engagement integrator and its laws;
- the outcome table.

Every v7 control is still on the page. Each control kept its id and its handler; some moved.

## What changed, against Layer 0's six points

| Layer 0 point | Layer 1 before (v7) | Layer 1 now (v8) |
|---|---|---|
| 1. Compact interface | A title, a subtitle paragraph, the field bar, the M5 bar and the load messages all sat above the plots. At 1536×730 the workspace began at y = 499 px, below the fold. | A one-line header, then the field tabs, then one toolbar and a status row. The workspace begins at y = 164 px. Navy/teal tokens, one type scale, one button style. |
| 2. Settings drawer | None. Everything sat in bars and in a capture card. | A non-modal drawer with **Data**, **Display**, **Export & appearance**, **Layout** and **Help**. It overlays the right edge and never resizes a plot. |
| 3. Toolbar and status row | The controls were spread over the field bar and the M5 bar. | One toolbar. A slim status row below it. |
| 4. Docking | Drag to split or swap, plus dividers (layout.v2). | Adds the Move menu, keyboard dividers, Esc to cancel, a height handle, three presets and Reset layout (layout.v3). |
| 5. Export | A capture card: PNG, GIF (turn / sweep / τ / engagement), video. GIFs ran about 10 s. | Moved into the drawer. Adds an image width for PNG too, a duration and frame count, a progress dialog with Cancel, and a restored view. Export PNG is also in the toolbar. |
| 6. Readability | Text and line sliders (saved), and a surface-opacity slider (not saved). | Text, lines & markers, and 3-D surface transparency, all saved and all applied to exports. Thicker engagement paths, kept distinct from the T₁ edges. |

**Workspace before and after,** measured headless on the M5 field:

| window | v7: workspace top, height | v8: workspace top, height | 3-D view, v7 → v8 |
|---|---|---|---|
| 1536 × 730 | 499 px, 560 px (needs scrolling) | 164 px, 536 px (fits) | 369×463 → 399×428 |
| 1920 × 1080 | 499 px, 565 px | 164 px, 886 px | 470×484 → 511×794 |

## The page, top to bottom

**Header.** One line: "Layer 1 Explorer", with "AE 8900 · Layer 1 · 1v1 HJI reachability · M1–M5" on
the right.

**Field tabs and tools.**
- **The tabs** are M1 ℓ, M2 V (frozen evader), M3 V (two-player) and M5 Vᴿᴬ (reach-avoid).
- **A tab whose file is not loaded** is grey but still clickable. It opens **Data** and says
  which file to load.
- **Arrow keys** move along the tabs.
- **The last tab is restored on the next visit,** once its file is back (auto-load or IndexedDB).
- **Tools on the right:** Data, Display, Export & appearance, Layout and Help. Data shows a red flag
  if any load-time check fails.

**Toolbar.** The controls used every few seconds:
- **The field's own option.** On M1 that is the ℓ weighting. On M5 it is "Color by" (value or
  partition).
- **Show:** point cloud, isosurface or both.
- **Time remaining $\tau$:** ◀, the slider, ▶ and the value. It reads "static" on M1.
- **Play.**
- **Reset views.**
- **Export PNG.**

**Status row.** One line:
- the field and $\tau$;
- the zone share, and on M5 the Ω shares of W₁, W₂, C and D;
- the load checks, as one link to Data ("3 files loaded · checks ✓");
- the selection: R, φ₁ and φ₂ in degrees, its set on M5, and "→ outcome at t". A **clear** button
  follows.

The full status line is still in the "Numerical details" disclosure under the workspace.

**Drawer sections.**

| section | what is there |
|---|---|
| Data | Load files, the drop hint, and the per-file load-time checks. |
| Display | Slice on/off, T₁ edges, Table 2 points (M5), the M5 set chips, the surface style and caps, mesh resolution, and the point-cloud controls (count, resample, value range, opacity mode and fade, vertical position). |
| Export & appearance | The panels to include, the image width, Save PNG, the GIF loop, duration and frames, Make GIF, Record video. Below them: text size, lines & markers, 3-D surface transparency, and Reset appearance. |
| Layout | The preset, Reset layout, and how to dock. |
| Help | What this field is (the old page subtitle), how to read the views, and the controls. |

**How the drawer behaves.**
- **Esc closes it first,** then a second Esc drops the selection.
- **Focus** goes to the drawer's × on opening and back to the tool button on closing.
- **While a dialog is open** (Move, export progress) **or a panel drag or resize is under way,**
  that owns Esc instead.
- **While an export runs,** the drawer sections are locked.
- **As in Layer 0, the drawer covers about 440 px on the right.** That includes the readout column
  and the right end of the toolbar. Close it with Esc or × to reach them.

**Engagement panel.**
- **Always visible:** both control laws, play, the time slider, speed, and the frame.
- **Folded into one line, "Start state, horizon & random starts":** the start boxes, horizon T,
  "play on select", and on M5 the random starts in W₁ / C / W₂ / D.
  - The line shows "· T = 6", so the horizon stays readable while folded.
  - Its open state is remembered.
- **In a short panel the plan view comes first.** The ℓ / R charts shrink first. They are left out
  (with a note to enlarge the panel) only when they would be too short to read.
- **At 1536×730, the default layout shows all three:** the readout line, the plan and the charts.

## Docking

**Panels:** 3-D view, Slice, Engagement, Readout, Legend. Each title bar has a grip and a **Move**
button.

**Ways to rearrange:**
- **Drag a title bar.**
  - Dropped on another panel's edge, it splits.
  - Dropped on its center (the middle 40 %), the two swap.
  - Dropped on the workspace's own edge, it docks along that side.
  - A hint shows the target. Esc cancels, and the cancel is announced.
- **Move** opens a dialog. Pick a neighbor and a position (left / right / above / below / swap).
  Hidden panels, such as the slice when it is off, are not offered.
- **Dividers:** drag one, or focus it and use the arrows (12 px; 40 px with Shift). Double-click
  evens the two sides. Esc cancels a drag.
- **Height handle** under the workspace: drag it, or use ↑ / ↓ (20 px; 80 px with Shift).
  Double-click fits the window again. The minimum is 420 px.

**Presets:**

| preset | arrangement |
|---|---|
| Overview (default) | four columns: 3-D, slice, engagement, readout over legend |
| Engagement focus | 3-D over slice, a wide engagement, readout over legend |
| Field focus | large 3-D and slice above; engagement, readout, legend below |

"Reset layout" applies Overview and fits the height. A hand-made arrangement reads "Custom".

## Export and appearance

**PNG.**
- **What it holds:** the ticked panels (3-D view, slice, engagement), each under its title. The
  legend and the stats sit beneath.
- **Image width:** 1200, 1600 (default) or 2400 px, or full size.
  - The composite is downscaled to that width, never enlarged.
  - If the panels are narrower than the request, the status says so.
- **Wrapping:** legend and stats lines wider than the image now wrap. At large text sizes they used
  to run off both edges.

**GIF.**
- **Loops:** turn the 3-D view; sweep the slice; step through $\tau$; play the engagement.
- **Settings:** a duration of 2–20 s, and 60 / 90 / 120 / 180 frames.
- **Frame delays** are whole centiseconds, spread so that the loop lasts the requested $s$ seconds
  to within 0.01 s. This is Layer 0's rule:
$$d_i = \operatorname{round}\!\left(\frac{100\,(i+1)\,s}{N}\right) - \operatorname{round}\!\left(\frac{100\,i\,s}{N}\right), \qquad i = 0, \dots, N-1.$$
- **Hold:** the $\tau$ and engagement loops hold their last frame 1 s more. Turns and sweeps loop
  seamlessly.
- **Refused settings:** a request with $100\,s < 2N$ (delays under 2 cs, which browsers clamp) is
  refused with a message, and so is a duration outside 2–20 s.
- **While it renders,** a modal dialog shows "Frame k of N" and a meter. **Cancel** or Esc stops
  it, and nothing is downloaded.
- **Afterwards,** whether finished or cancelled, $\tau$, the camera azimuth, the slice position,
  the hover and the engagement time are restored.

**Video.** As in v7: H.264 MP4 in Chrome and Edge, WebM elsewhere.

**Appearance** (saved in this browser; applied to the live plots and to every export):
- **Text size,** 100–300 %.
- **Lines & markers,** 100–250 %.
- **3-D surface transparency,** 0–85 %.
  - This replaces v7's surface-opacity slider.
  - It fades both the shaded surface and the isosurface dots.
  - With a shaded surface, "both" still shows it at 50 % while it is on. That temporary value is
    not saved.
- **Reset appearance** returns all three to the defaults.

**The engagement path** in (R, φ₁, φ₂):
- **The flown part** is magenta, 3 px × the line scale, on a white halo. It is 15 % heavier over a
  surface.
- **The part still to come** is dashed magenta at 55 %.
- **Both differ from the T₁ edges,** which are dark, thin and dashed, and from the colored cloud.
- **In the plan view,** the flown paths are 2.6 px (were 2).

## Saved in the browser

| key | holds | migrates from |
|---|---|---|
| `layer1.ellExplorer.layout.v3` | `{ version: 3, tree, height }` | `layout.v2`: its capture panel removed |
| `layer1.ellExplorer.appearance.v1` | `{ text, line, transparency }` | `sizes.v1`: text and line |
| `layer1.ellExplorer.tab.v1` | the last field tab | — |
| `layer1.ellExplorer.engMore.v1` | the "Start state" fold, open or closed | — |

Loaded files stay in IndexedDB, as before.

## Verification (headless Chromium)

**Interaction and export suite: 91 of 91 checks pass, with no page errors.** It covers:

- **Startup.**
  - Opens on M1 with the Overview preset.
  - M2 is marked empty (no file in the test tree). M3 and M5 auto-load.
  - The status row reads "checks ✓", and the partition check passes.
  - No horizontal scroll.
- **Tabs.**
  - The empty M2 tab opens Data with the file to load, and the field is unchanged.
  - M3 → M5 keeps $\tau$ (k = 6) and the selection. M1 hides the M5 controls and shows the
    weighting.
  - Arrow keys move along the tabs.
  - The tab is saved and restored after a reload.
- **Drawer and Esc order.**
  - Opening moves focus into the drawer, and the plots do not move.
  - The first Esc closes the drawer and keeps the selection, with focus returned to the button.
  - The second Esc drops the selection.
  - With the drawer and the Move dialog both open, Esc closes only the dialog.
- **Docking.**
  - Mouse drags: an edge split, with same-direction rows merged; a center swap; Esc mid-drag
    cancels, with the cancel announced.
  - The Move dialog: "below the 3-D view".
  - Dividers: arrow key, and a 60 px mouse drag.
  - The height handle, by arrows.
  - Slice off hides its panel and drops it from Move.
  - The layout, height and "Custom" are restored after a reload. Double-click fits.
  - All three presets, and Reset layout.
  - No panel is left parked.
- **Appearance.**
  - The sliders set text, line and transparency, and opacity = 1 − transparency.
  - The values are saved and restored after a reload.
  - "both" shows 50 % without saving it.
  - Old `sizes.v1` values migrate.
  - Reset appearance works.
- **Exports.**
  - Export PNG from the toolbar is 1200 px wide, and full size is wider.
  - The panel choice reaches the file name.
  - Too short a duration for the frames, and an out-of-range duration, are refused.
  - The $\tau$ GIF has 60 frames over 3 s plus a 1 s hold (400 cs). The engagement GIF is 2 s
    plus 1 s. A 90-frame turn lasts exactly 4 s.
  - The view is restored afterwards.
  - The progress dialog appears, and the drawer is locked meanwhile.
  - Cancel and Esc both stop the GIF. The view is restored, the controls come back, nothing is
    downloaded, and the drawer and selection are kept.

**Other runs, all with no page errors:**
- **file://.** M5 loaded through Data's picker: "2 files loaded · checks ✓". After a reload the M5
  tab and the files come back from IndexedDB.
- **Rollouts against Python** (the v7 reference set):
  - Outcomes agree in **1000 of 1000** runs.
  - Kill times agree to 1.6×10⁻¹².
  - The integrator is untouched.
- **Screenshots** at 1536×730 and 1920×1080, with the drawer closed and open.

## Not done / caveats

- **The drawer covers the right end of the toolbar and the readout,** as Layer 0's does. A
  narrower drawer would cramp the Display controls.
- **Layouts from v7 (layout.v2) are migrated without the capture panel.** Layouts from before v7
  are not restored.
- **"Custom" is an exact match.** Any divider change from a preset reads as Custom.
- **Large text in small panels** can still crowd the 3-D axis labels. Enlarge the panel or use the
  Field focus preset.
