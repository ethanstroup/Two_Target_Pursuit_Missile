# Layer 1 — explorer v7: the M5 tab, selecting a state, and the 1v1 engagement

**AE 8900 · 2026-10-16 · Ethan Stroup**
File: `Two_Target_Pursuit_Missile/layer1/viz/ell_explorer.html`, the same page as M1–M3
(`Overview/Layer1/Layer1_M1_Explorer_2026-09-30.md`). Still one standalone file that opens from
the filesystem with no build step. Companion to `Overview/Layer1/Layer1_M5_Explainer.md`.

> **Interface since v8 (same day).** The page was redesigned after Layer 0's explorer
> (`Overview/Layer1/Layer1_Explorer_Redesign_2026-10-16.md`). Everything below still works; some
> controls moved:
> - **Loading and the load-time checks** are under **Data**. The status row says "N files loaded ·
>   checks ✓" and links there.
> - **The M5 bar is gone.** "Color by" (value or partition) is in the toolbar. The set chips and
>   "D&S Table 2 points" are under **Display**.
> - **Capture** is now **Export & appearance**, and "Export PNG" is in the toolbar.
> - **The start boxes, the horizon T, "play on select" and the random starts** fold into **Start
>   state** in the engagement panel.

**What v7 adds:**
- **An M5 field,** "Vᴿᴬ · M5 reach-avoid", next to ℓ · M1, V · M2 and V · M3.
- **Selecting.** A click now selects a state, and the selection stays when the cursor leaves.
  Before this, the page only read out what was under the cursor.
- **An engagement panel.** The selected (R, φ₁, φ₂) is flown forward as a 1v1 engagement. Its
  path is drawn back into the 3-D view and onto the slice.
- **An outcome table** in the readout: the selected state against every pair of control laws.

## Loading M5

- **Load** with "load files…" or by dropping files on the page, as before. Files are kept in the
  browser (IndexedDB) and restored on the next visit. Served over http, the page fetches them
  itself from `../M5/m5_out/m5_out_V1_pole/`, or from `../M5/m5_out/`.

| file (from `layer1/M5/m5_out/m5_out_V1_pole/`) | what the page does with it |
|---|---|
| `Vsnap_RA_101x102_T6_pole.npz` | **required.** Vᴿᴬ₁(x, τ) at τ = 0, 0.5, …, 6, with node arrays (real rows only) |
| `Vsnap_RA_101x102_T6_single_pole.npz` | M5's single-target V₁ on the same grid. It gives D and C, and the V₁ laws |
| `m5_101x102_T6_pole.json`, `m5_101x102_T6_single_pole.json` | load-time checks (below) |
| `test_m5_T6_pole_fields.json` | checks the partition shares at τ = 6 |

- **Other grids.** The 51×52² files work the same way. The 201×204² Vsnaps (133–143 MB
  compressed, about 0.4 GB each in memory) load, but they are heavy for a browser.
- **Files the page refuses, with a message.**
  - `VRAsnap_*` has mirror rows, no node arrays, and a 0.25 cadence.
  - `m5_*_fields.npz` holds the final V only.
- **The load messages** now collapse to one line ("every load-time check passes ✓"). Click
  "details" for the per-file lines.

## Load-time checks (all pass on the 51 and 101 pole grids)

- **τ = 0 equals max(ℓ₁, −ℓ₂)** (sdist) at every node, with a difference of exactly 0. For the
  single-target file it equals ℓ₁.
- **V never rises with τ,** and **V ≥ min V(·, 0) − one cell.**
- **The zone share equals the solver json** at all 13 snapshots.
  - A pole run's json counts its 3 mirror rows below R = 0.
  - Each mirror row is a real row with both angles turned by π, so the page counts the first
    three real rows twice.
  - It also checks that the json's `R_nodes` equal the file's R.
- **The partition at τ = 6 equals `test_m5_T6_pole_fields.json`.**
  - On 101×102²: W₁ 3.5647 %, W₂ 3.5647 %, D 91.7140 % and C 1.1567 % of Ω, over 890,126 Ω nodes.
  - On 51×52²: 116,440 Ω nodes.
  - Both match exactly.

## The M5 field

**When it opens.** The M5 field opens at τ = 6, M5's T_RA. Coming from M2 or M3 it keeps their τ
instead. An M5 bar appears under the field bar.

**Color by value** (the default). The nodes are colored by Vᴿᴬ₁ in the same bands as M2 and M3,
and all V fields share one color scale. The isosurface is Vᴿᴬ₁ = 0, which is ∂W₁.

**Color by partition.** Each node is colored by its set at this τ, exactly as `test_m5.partition`
assigns it:

| set | color | rule |
|---|---|---|
| W₁ | blue (player 1) | Vᴿᴬ₁ ≤ 0 |
| W₂ | orange (player 2) | W₁ ∘ S, an axis transpose |
| C, contested | teal | the rest of Ω |
| D, draw | grey, hidden by default | V₁ > 0 and V₂ = V₁ ∘ S > 0 |
| W₁ ∩ W₂ | dark | a tie on a mutual-kill surface; appears only where it exists |
| in a target, R < 0.45 | light grey, hidden by default | outside Ω |

- **The chips** in the M5 bar show and hide each set and give its share of Ω at this τ.
- **Sampling.** The cloud is drawn from the shown sets only, about the "points" count. So a 3 %
  set isn't lost among draws from the whole grid.
- **Stability across τ.** Each node has a fixed random key, so a node stays drawn from one τ to
  the next while its set stays shown.
- **The colors** are validated as a categorical set: they pass every all-pairs CVD and contrast
  check.
- **Without the single-target file,** the page shows W₁, W₂ and "D or C".

**Also on the M5 field:**
- **T₂→₁'s closed-form edges,** = S(T₁), dashed in 3-D and dotted on the slice. Vᴿᴬ₁ is held
  positive inside them.
- **D&S Table 2 points.** These are the 17 points of check 10: 12 filled (off the target, scored
  |Vᴿᴬ₁| ≤ δ) and 5 hollow (on ∂T₁, scored Vᴿᴬ₁ ≥ −δ).
  - Hover or click one to read it.
  - Its readout shows whether it meets its bar on the loaded grid, with δ from the m5 json.
  - Check 10 itself scores the 201 grid.
- **"Random start in W₁ / C / W₂ / D"** selects a random node of that set at this τ.
- **The status line** adds the partition of Ω at this τ.
- **The readout** adds:
  - the state's set, in words;
  - Vᴿᴬ₂ = Vᴿᴬ₁ ∘ S;
  - V₁ and V₂;
  - the first snapshot with Vᴿᴬ₁ ≤ 0;
  - max(ℓ₁, −ℓ₂);
  - ℓ₂.

## Selecting (every field)

- **What a click can select:** a cloud point, an isosurface dot, the shaded surface, the slice
  sheet, or a Table 2 point. On the flat slice, a click takes the dot under the cursor, or else
  the exact state on the plane.
- **The selection is a green double ring** in 3-D and on the slice. It stays put.
- **The readout shows the hovered state while you hover,** and returns to the selection when the
  cursor leaves. A "selected / hover" tag says which one it is showing.
- **Esc or "✕ clear"** drops the selection.
- **Typing a start.** The engagement panel's "start R φ₁ φ₂ (deg)" boxes select a typed state.
  They also show the selected one.
- **Degrees.** The readout now gives φ₁ and φ₂ in degrees as well as radians.

## The engagement

**The picture.**
- Player 1 starts at the origin, nose up. Player 2 is at range R and bearing φ₁ off player 1's
  nose.
- The convention is Layer 0's (`los_coords.js`, `heuristic_simulator/sim.js`): φ₁ > 0 puts
  player 2 on player 1's left, and σ = +1 is a right turn. `inertial.py` uses the mirror image.
  Both give D&S Eqs. (1)–(3) exactly.

**The integration.**
- Both aircraft fly exact unit-speed arcs, with σ held over each 0.002 step. This is
  `inertial.rollout`.
- The reduced state is computed from the positions, so a close pass is just two aircraft passing,
  as on the pole grid.
- The first kill is bisected inside its step (40 halvings) and classified by `sim_m5`'s tie rule:
  player 1 first by more than 10⁻⁶ wins alone; within 10⁻⁶ is a mutual kill.
- R ≥ 12 is "left the domain", which is the grid's outer face. A start inside a target is decided
  at t = 0.

**The laws** are `sim_m5`'s. Each is read at the snapshot nearest the remaining horizon
min(T − t, 6), from angular central differences on the nodes, interpolated through the mirror row
below the first node on a pole grid.

| player 1 | rule | | player 2 | rule |
|---|---|---|---|---|
| reach-avoid | −sign ∂Vᴿᴬ₁/∂φ₁ | | reach-avoid adversary | +sign ∂Vᴿᴬ₁/∂φ₂ |
| single-target | −sign ∂V₁/∂φ₁ | | own reach-avoid | −sign ∂Vᴿᴬ₂/∂φ₂ |
| retreat (`diag_retreat`) | +sign ∂V₂/∂φ₁ | | avoid (M3's evader) | +sign ∂V₁/∂φ₂ |
| heuristic | −sign φ₁ | | single-target | −sign ∂V₂/∂φ₂ |
| straight | 0 | | heuristic, straight, random | as for player 1 |
| random | ±1 every 0.25 | | | |

- **The V₁ laws** use M5's single-target file. Without it they fall back to M3's V.
- **A law whose file isn't loaded** is listed but disabled.
- **The defaults** are reach-avoid against the reach-avoid adversary: the guarantee of check 11.

**The panel.**
- **Plan view,** in a fixed frame or in player 1's frame. In player 1's frame player 2 sits at
  (R, φ₁) in polar form.
  - Both live weapon envelopes are drawn. Each shooter's radii come from the target's aspect
    angle, and an envelope darkens while the opponent is in it.
  - The paths are drawn faint in full and solid up to now. Also shown: the line of sight, the
    arcs and values of φ₁ and φ₂, σ₁ and σ₂, and a ✕ on the victim at the kill.
- **Two charts on one time axis:**
  - ℓ₁, ℓ₂ and Vᴿᴬ₁(x(t), T − t). ≤ 0 means "can fire", and Vᴿᴬ stays ≤ 0 along a guaranteed win.
  - R(t).
  - Click or drag on a chart to scrub.
- **Controls:** play/pause, a time slider, speed (0.25×–4×), the horizon T (default 6), and
  "play on select".
- **In the 3-D view and on the slice,** the run's path in (R, φ₁, φ₂) is solid up to the replay
  time and dashed after it. A ring moves with the replay.

**The outcome table** (in the readout) runs the selected state against every available pair of
laws, up to 6 × 7. A cell gives the outcome and the kill time. Clicking it plays that pair.

**Capture** (Export & appearance since v8). "engagement" is a capture panel. The GIF menu gains "play the engagement", which
moves the plan view, the 3-D ring and the slice path together. The slice capture now includes the
path and the selection.

**Layout.** The default is four columns: the 3-D view, the slice, the engagement, then the
readout above the legend. (In v7 the capture card sat under the legend; v8 moved it into the
drawer, presets and all, as recorded in the redesign record.) Layouts saved before v7 (layout.v1)
lack the new panel and are not restored.

## Verification (headless Chromium)

**Rollouts against Python.**
- The reference is `sim_m5`'s own laws, on the same Vsnap snapshots with the mirror rows rebuilt,
  integrated by `inertial.rollout`.
- The starts were 125: 25 each from W₁, W₂, C and D at τ = 6 on 101×102², plus 25 random off-node
  states.
- They were run under 8 law pairs.
- **Outcomes agree in 1000 of 1000 runs,** and kill times agree to 1.6×10⁻¹².
- A rollout costs about 0.8 ms, so a full table takes about 40 ms.

**The 0.5 snapshot cadence.**
- The page reads the Vsnap every 0.5, where the scored runs read VRAsnap every 0.25.
- From 800 deep W₁ starts (Vᴿᴬ₁ ≤ −δ, 101×102² pole grid, seed 0), the reach-avoid law wins all
  800 at both cadences. That holds against the reach-avoid adversary, avoid, heuristic, own
  reach-avoid and random.

**Interaction.** All of these were exercised in headless Chromium:
- real mouse clicks on cloud points and Table 2 points, slice dots and the slice plane;
- Esc and "clear";
- the outcome-table cells;
- the random-start buttons;
- switching ℓ / M3 / M5 with the selection kept, and the M5 bar hidden off M5;
- file:// loading through the picker, and restore after a reload;
- the http auto-load;
- the τ and engagement GIFs, and the PNG capture.

There were no page errors.

## Not done / caveats

- **The trade law (t₂*) is not offered.** It needs t₁* per node, which the Vsnap doesn't carry
  at full resolution.
- **The random law** uses the page's own seeded generator, not numpy's stream. The same seed
  gives a different sequence from `sim_m5`.
- **Cadence.** Near switching surfaces, the 0.5 cadence can pick a different snapshot than the
  scored runs did. The W₁ test above found no outcome changes.
- **D and C need the single-target file on the same grid.** A V₁ from another grid is flagged
  and not used.
