# Layer 1 — explorer: $\ell(x)$, and $V(x,\tau)$ for M2 and M3

**AE 8900 · 2026-09-30, v6 on 2026-10-01 · Ethan Stroup**
File: `Two_Target_Pursuit_Missile/layer1/viz/ell_explorer.html`. It is saved in the repo and was checked by md5 after each write. It is one standalone page with no build step and no server, and it opens straight from the filesystem. Companion to `claude/Layer1_M1_Explainer.md`.

**v6 (2026-10-01):** the page now also shows the solved value functions of M2 (frozen evader) and M3 (two-player), and steps through $\tau$. Building the M2 field turned up a defect in M2's frozen-evader solve; see "The M2 field is not valid everywhere" below.

## The three fields

A **field** bar at the top picks what is drawn:

- **$\ell$ · M1.** $\ell(x)=\max\big(|\phi_1|-\beta,\ R_{lo}(\phi_2)-R,\ R-R_{hi}(\phi_2)\big)$, evaluated in the page, over $R\in[0.2,12]$ and $\phi_1,\phi_2\in[-\pi,\pi)$. The default weighting is still **raw**. An "$\ell$ weighting" menu adds `sdist` and `plan`, matching `ell.py`'s `_weights` term for term. The weighting never changes the sign or the zero set.
- **V · M2 frozen evader.** $V(x,\tau)$ with $\sigma_2\equiv 0$, from `m2_out/Vsnap_frozen_101x102_T6.npz`.
- **V · M3 two-player.** $V(x,\tau)$, from `m3_out/Vsnap_101x102_T6.npz`.

Both V files were solved under `sdist`, so $V(x,0)=\ell_{\text{sdist}}(x)$, not the raw $\ell$ shown by default.

## Stepping through $\tau$

- The $\tau$ control has ◀ / ▶, a slider, **play** (about 0.7 s per snapshot, stopping at $\tau=6$), and the ← → keys.
- It steps through the 13 stored snapshots, $\tau=0,0.5,\dots,6$. **Nothing is interpolated in $\tau$**, because an in-between frame would not be a solution.
- $\tau$ is the **horizon**, the time remaining, not forward time. This is the M2 remaining-horizon convention.
- $V$ can only fall as $\tau$ grows, so $\{V\le 0\}$ only grows.
- **Switching between M2 and M3 keeps $\tau$**, the view, the slice and the point-cloud nodes. The two share one color scale, so the same color means the same value in both.
- **Status line.** At each $\tau$ it gives:
  - the share of grid nodes with $V\le 0$, and that share among nodes with $R\ge 0.45$ (M3's mask);
  - the other game's share at the same $\tau$;
  - the outer edge in $R$, flagged when it reaches the outer face $R=12$.
- **Readout.** For the hovered state it shows:
  - $V$, and the other game's $V$ at the same state and $\tau$;
  - the first snapshot with $V\le 0$, which is $t_1^*$ to the snapshot spacing;
  - $\ell$ and its three terms in the field's own weighting.
- **Panel titles carry the game and $\tau$**, for example "M3 two-player: V(x, τ = 2) on (R, φ₁, φ₂)", so captures say what they show.

## Loading the files

- A `file://` page cannot fetch files, so **"load files…"** (or dropping files on the page) reads them in the browser:
  - a small zip reader (stored or deflated entries, zip64 extras);
  - the browser's `DecompressionStream`;
  - numpy's `.npy` header.
- **Which slot.** A name with "frozen" or "m2" goes to M2; anything else goes to M3.
- **Node arrays.** They come from the file when present. M2's file has them; M3's does not, so the page uses `hji.make_grid`'s defaults: $R$ from 0.2 to 12 with both ends included, and angles uniform on $[-\pi,\pi)$ with `endpoint=False`.
- **Drop the matching `.json` too** (`m3_out/m3_101x102_T6.json`, `m2_out/m2_frozen_101x102_T6.json`). The page then checks its own node counts against the solver's, as described under "Load-time checks".
- **Kept in the browser.** Loaded files are stored in IndexedDB and restored on the next visit, while the page still opens on $\ell$. Served over http(s) instead, the page fetches `../m2_out` and `../m3_out` itself.

**Load-time checks**, shown under the field bar for each file:

- $\tau=0$ equals $\ell$ (in the file's weighting) at every node;
- $V$ never rises with $\tau$;
- $V\ge\min\ell$ minus one cell (next section);
- the share of nodes with $V\le 0$ equals the solver json at every snapshot.

## The M2 field is not valid everywhere, and neither is M2's original solve

**The bound.** $V(x,\tau)=\min_{\sigma_1}\max_{\sigma_2}\min_{t\in[0,\tau]}\ell(x(t))$ is a minimum of $\ell$ along a trajectory. So $V\ge\min\ell=-\beta$ at every node and every $\tau$.

**Where it breaks.** The frozen-evader solve breaks this bound from $\tau\approx 0.75$:

- It starts at the inner face $R=0.2$ near $\phi_1=\phi_2=0$. These states are nose-on and closing at speed 2, so they leave the domain through that face.
- From there it grows without limit:

| $\tau$ | $\min V$ | nodes more than one cell (0.118) below $-\beta$ | out to $R$ |
|---|---|---|---|
| 0.75 | $-2.6$ | 152 | 0.55 |
| 1 | $-11$ | 802 | 1.03 |
| 3 | $-7.0\times10^{3}$ | 33,630 (3.2 %) | 5.16 |
| 6 | $-7.8\times10^{8}$ | 219,020 (20.8 %) | 11.17 |

**M2's own configuration does the same.** `test_m2.py`'s 101³ grid, $T=3$, `hj.solve` with 61 outputs, re-run here, gives:

- $\min V=-1.45\times10^4$ at $T=3$;
- 3.3 % of nodes more than 0.05 below $-\beta$, out to $R=5.3$.

At 61³ there is no blow-up, but 7 % of nodes still sit more than 0.05 below the bound (worst $-0.94$).

**Why M2's tests could not see it:**

- No check in `test_m2.py` bounds $V$ from below.
- The trajectory tests drop every sample that leaves the $R$ domain, and these are exactly the states that do.

**M3 is not affected.** Its $\min V=-0.802$, within 0.017 of the bound and well under a cell.

**What was done:**

- `solve_m2_snap.py` reports the bound as a check, and that check FAILS.
- The json records, per $\tau$, the count of nodes below the bound and how far out in $R$ they reach.
- The page draws those nodes **grey**, keeps them out of the color scale, and counts them in the status line. The readout says "not a valid value".
- The $V=0$ surface still wraps them.

**Not done.** The inner-face boundary condition is unchanged, because that is a method decision. M2's README status is annotated, not changed.

The rest of the M2 field behaves as M2 recorded:

- The front moves at 1.990 (analytic 2) until it meets $R=12$ at $\tau\approx 3$. After that, values near $R=12$ depend on the outer face's extrapolation condition.
- $V_{\text{frozen}}\le V_{\text{M3}}+0.031$ at every common snapshot.

## M2 field: how it was made

`layer1/solve_m2_snap.py` re-solves the frozen-evader game on M3's 101×102×102 grid to $\tau=6$:

- It marches with `hj.step` every 0.25 and snapshots every 0.5, exactly as `solve_m3.march` does.
- Nothing in `hji.py` or `ell.py` changed.
- It takes 522 s on two cores.
- The cloud environment reproduces Ethan's M3 snapshot at $\tau=0.5$ bit for bit, and two runs of the M2 script are bit-identical.
- **The npz (31 MB) is over the 20 MB limit for writing into the folder from a session.** It was delivered in the chat. Save it to `layer1/m2_out/`, or rerun the script from `layer1/`. The json is in the repo.

## Display (unchanged from v5 unless noted)

- **Point cloud (default view).**
  - 20,000 samples, adjustable from 1k to 40k: random states for $\ell$, random grid nodes for V.
  - Drawn for values in [min, 8].
  - Opacity fades with the value: $0.70\,(\text{floor}+e^{-v/w})$ with $w=0.75$. Uniform opacity is the alternative.
- **Colors.** Stepped bands. Inside, blue darkens with depth. Outside, red is darkest next to the boundary. The two V fields share the bands $-0.2,-0.4,-0.6,-0.8\,/\,0.5,1,1.5$.
- **Isosurface of the zero set.** Drawn as dots where render-grid edges cross zero (default 48³), or shaded marching cubes.
- **Slice.** As in v5: the 3-D plot's own dots within a slab, the zero contour bold, and $T_1$ from the closed form as an amber dashed line.

## Capture

As in v5, plus:

- A GIF loop **"step through τ"**: each snapshot is held for an equal share of about 10 s, and $\tau$ is restored afterwards.
- **Titles, legend and stats are re-read on every frame.** In v5 they were frozen at the first frame, which was wrong for a slice sweep and for $\tau$. The canvas is sized for the largest frame.
- File names are `layer1_<m1|m2|m3>_[loop_]<panels>[_tau<τ>]_<timestamp>.<ext>`.

## Layout and data path

- Docking panels are unchanged (`layer1.ellExplorer.layout.v1`).
- Rendering still touches only the **Field** interface:
  - `AnalyticField` for $\ell$;
  - `GridField` for V, which now also carries its weighting, its game, and `bound()`: $\min\ell$, the cell, and the floor.
- `EllExplorer.setField`, `selectSource`, `loadFiles`, `readNpz` and `zoneStats` are exposed.

## Verification (headless Chromium, all green)

**$\ell$**

- JS $\ell$ against `ell.py` on $2\times10^4$ random states, under all three weightings: 19,999 / 19,998 / 20,000 bit-identical, max diff $8.9\times10^{-16}$.
- The v5 defaults still reproduce: 19,219 of 20,000 shown, 1,503 inside.
- The mesh still reports $T_1$'s closed-form volume, 7.170 %.

**M3**

- Load checks green: $\tau=0$ equals $\ell_{\text{sdist}}$ at every node (difference 0); $V$ never rises.
- Zone share equals `m3_101x102_T6.json` exactly at all 13 snapshots.
- Zone share, masked share and outer edge equal numpy at every snapshot.
- Trilinear `valueAt` equals `hj_reachability`'s `grid.interpolate` to $8\times10^{-15}$ on 3,000 random states.

**M2**

- The same checks as M3, plus the page's count of nodes below the floor equals the solver json at every snapshot.
- The cell (0.118) equals `ell.value_scale`.

**Interaction**

- Stepping costs a median of 40–65 ms per snapshot.
- Arrow keys, play, the $\ell$ ↔ V switch, and M3 → M2 keeping $\tau=3$ with the same nodes and the same bands all work.
- The readout on a bad node says "not a valid value".
- PNG and $\tau$-GIF captures are written (72 frames, 1 MB), with the turn GIF still working.
- After a reload, both files are restored from the browser and the page stays on $\ell$.
- Over http, the page fetches both files itself.
- No page errors.

## Open

- **M2's inner-face instability (needs Ethan).** Options:
  - leave M2 as a range-limited smoke test and add the lower-bound check to `test_m2.py`, where it would fail at 101³;
  - change the inner-face condition for the frozen game and re-run M2;
  - mask the M2 field by the bound for display only, which is what the page does now.
- Saving the M2 npz into `m2_out/` (download, or rerun the script).
