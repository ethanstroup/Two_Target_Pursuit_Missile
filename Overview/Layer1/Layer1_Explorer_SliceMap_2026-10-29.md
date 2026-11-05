# Layer 1 — explorer v9: the slice as solid regions

**AE 8900 · 2026-10-29 · Ethan Stroup**

- **File:** `Two_Target_Pursuit_Missile/layer1/viz/ell_explorer.html`, the same single page.
- **Builds on:** `Overview/Layer1/Layer1_Explorer_Redesign_2026-10-16.md` (v8) and
  `Overview/Layer1/Layer1_M5_Explorer_2026-10-16.md`.

**What v9 adds.** The slice panel has a second style, **regions**. Every grid node on the plane is
drawn as a solid cell, as in the M5 slides' partition figures.

**How it got here.** Earlier on 2026-10-29 this was a separate "slice map" panel. Since it showed
the same plane as the slice panel, the two were combined at Ethan's request, and the regions are
now an option of the slice panel itself. The separate panel, its toolbar button and its layout
preset are gone.
- A layout saved while the separate panel existed comes back without it.
- Its stored setting (`layer1.ellExplorer.sliceMap.v1`) is cleared on load.

## The two styles

The slice panel's **dots | regions** switch sits next to the value box.

**dots** is unchanged from v8: the 3-D plot's own dots within a slab of the plane.

**regions:**
- **Each cell** is centered on its grid node.
- **Partition (Color by: partition, M5)** colors each node by its set at the current $\tau$,
  exactly as `test_m5.partition` labels it:

| set | color | note |
|---|---|---|
| $W_1$: player 1 wins alone | blue `#1f5fa8` | as in 3-D |
| $W_2$: player 2 wins alone | orange `#d4600f` | as in 3-D |
| $C$: contested | teal `#13936a` | as in 3-D |
| $D$: guaranteed draw | near-white `#f4f5f7` | as on the slides |
| $W_1 \cap W_2$: a tie | gold `#e3b505` | only where present |
| inside a target set | dark gray `#33383e` | as on the slides |
| $R < 0.45$, outside $\Omega$ | light gray `#dfe3e7` | only where present |
| $D$ or $C$ | gray `#c3c9d0` | when the single-target $V_1$ is not loaded |

  - The panel draws these sets' legend under the plot, and the shares of $\Omega$ on the plane
    above it. Ties count in both $W$s, as in `test_m5.fractions`.
  - $W_1$, $W_2$, $C$, the target gray and the tie gold pass the dataviz validator's all-pairs
    checks: color-vision deficiency $\Delta E \ge 10$, normal vision $\Delta E \ge 19$.
  - $D$ and the targets differ from the 3-D view, where they are hidden by default. Here they are
    recolored so the small sets stand out.
- **Value mode** draws:
  - the same stepped bands as the 3-D view;
  - the zero contour in bold, from the plane's own nodes;
  - $T_1$ dashed and, on M5, $T_2 = S(T_1)$ dotted, at the same plane;
  - the share with $V \le 0$, above the plot.

**Shared by both styles:**
- **Axes:** the slice panel's axes, which follow the 3-D view. $\phi_2$ runs to the left. An
  $R$ slice puts $\phi_2$ across and $\phi_1$ up. This is the slide figures' $R$ plane, transposed
  and mirrored.
- **Node planes:** in regions, a grid field (M2, M3, M5) is read on its own nodes. The slider,
  the value box and the step buttons all put the slice on the nearest node plane, so the title,
  the box and the 3-D sheet agree. For example, $R = 2$ on the $101 \times 102^2$ pole grid becomes
  $R = 1.97$.
- **M1's analytic $\ell$** is evaluated at the exact value, on a lattice of 180 per angle and 150
  in $R$.

**New controls, both styles:**
- **◀ ▶** step one grid node plane. The angles wrap. For M1 a step is $0.1$ in $R$ or $5^\circ$.
- **Regions hides the slab control** and the slab's faces in 3-D. Neither applies to a node
  plane.
- **Hover** a cell to read its node ("grid node on the slice"). **Click** to select it and play
  its 1v1 engagement.
- **Also drawn:** the selection ring and the engagement's path, as for the dots.
- **The style is saved** in this browser as `layer1.ellExplorer.sliceStyle.v1`. It follows
  $\tau$, Play, the field tabs and the export settings. The slice panel's PNG, GIF and video
  capture the regions as drawn.

**One fix in the workspace, found while testing:**
- **Hidden panels no longer leave a gap.** Hiding a panel (slice off) left the rest of its split
  at its old fraction. In v8 the Overview with the slice off filled 1127 of 1496 px. Split sizes
  are now flex-grow × 1000, so the visible panels always fill.
- **Short panels drop their how-to line** and keep the plot. This is a container query at 340 px.
- **Preset matching** now allows $10^{-6}$ in the split sizes, so a migrated Overview still reads
  as Overview.

## The engagement panel's angle arcs near $\pm 180^\circ$ (same day)

**The problem.** In the plan view, an angle near $\pm 180^\circ$ flips sign from one step to the
next, and its arc and label jumped to the other side and back.

**The fix.**
- **An arc now keeps the side it was drawn on** until the angle is back inside $\pm 179^\circ$:
  $1^\circ$ of hysteresis. Within that band it sweeps on past $180^\circ$ (up to $181^\circ$), and its
  label follows.
- **A new run starts fresh.**
- **The readouts are unchanged.** The panel's text line and the readout keep
  $(-180^\circ, 180^\circ]$.

**Checked by replaying runs step by step.** From $(R, \phi_1, \phi_2) = (4.203, 179.9^\circ, 0^\circ)$:
- $\phi_2$'s raw value flips sign 114 times along the run; its arc now flips 0 times;
- $\phi_1$'s arc flips only where $\phi_1$ really crosses $\pm 181^\circ$ (twice).

From $(4.5, 170^\circ, 175^\circ)$: 156 raw flips, 0 drawn.

## Player 1's reach-avoid adversary law, and the Kill boxes (same day)

### The new law

**Player 1 gains "reach-avoid adversary", $\sigma_1 = +\operatorname{sign}\,\partial V^{RA}_2/\partial\phi_1$.**
- In player 2's reach-avoid game, player 1 is the maximizer. With $V^{RA}_2 = V^{RA}_1 \circ S$,
  $\partial V^{RA}_2/\partial\phi_1$ at $x$ is $\partial V^{RA}_1/\partial\phi_2$ read at $S x$.
- It is player 2's "reach-avoid adversary" law mirrored under $S$, the swap of the two players.
- `sim_m5` has no player-1 law of this kind. `converse_m5` scores only player 2's adversary.
- The outcome table is now up to $7 \times 7$.

**Checks on the law:**
- **It mirrors player 2's law exactly.** At 2,000 random states and horizons, $\sigma_1$ at $x$
  equals player 2's adversary $\sigma_2$ at $S x$.
- **Runs swap correctly.** Over 200 random starts, (new law vs player 2's own reach-avoid) from
  $x$ and (reach-avoid vs player 2's adversary) from $S x$ end with swapped outcomes in all 200.
  Their kill times agree within $4 \times 10^{-12}$.
- **The mirrored guarantee holds.** From 150 deep $W_2$ starts ($V^{RA}_2 \le -0.12$), player 2's
  own reach-avoid kills alone against it every time. This is check 11's guarantee, mirrored.

### The Kill boxes

**A Kill box sits beside each player's law, ticked by default.**
- **Unticked, that player cannot end the run.** Its envelope is still drawn, with a dashed
  outline, and still darkens when the opponent is inside.
- **The text line says so.** It reads "2 in 1's envelope (kill off)" instead of "1 can fire".
- **The run flies on.** It ends only by the other player's kill, by leaving the domain, or at $T$.
- **The outcome table follows the boxes too.** Its caption names the player whose kill is off,
  and so does the engagement title used in exports.
- **This shows what happens in the contested set** when only one side may end the fight.

**Checks on the Kill boxes:**
- **Player 1's kill off.** On a $W_1$ start that player 1 wins at $t = 2.11$, the run flew on
  with player 2 inside player 1's envelope for 1,502 steps, and ended with no kill by $T$.
- **The table follows.** The $7 \times 7$ table recomputed with no player-1 kills. With both
  kills off, every pair ended with no kill or at $R = 12$.
- **Ticking the boxes again** restores the win.
- **Defaults are unchanged.** With both kills on, outcomes still agree with Python in 1000 of
  1000 runs.

## Verification (headless Chromium, M5 101×102² pole grid, $\tau = 6$)

**Regions against the arrays.**
- The reference is computed straight from `Vsnap_RA_…_pole.npz` and
  `Vsnap_RA_…_single_pole.npz`:
  - $W_1 = \{V^{RA}_1 \le 0\}$;
  - $W_2 = W_1 \circ S$;
  - $D = \{V_1 > 0\} \cap \{V_1 \circ S > 0\}$;
  - $C$ is the rest.
- It covers nine planes: $R = 2, 4.52, 5.48$; $\phi_1 = 0, \pi/8, \pi/4$; $\phi_2 = 0, \pi/2, \pi$.
- **The rendered pixel at each sampled node's center matches its set at all 2,780 sampled
  cells.** Of those, 956 are on the $R$ planes, 864 on $\phi_1$ and 960 on $\phi_2$. Target and
  mask cells were excluded.
- Hovering at those pixels returns that node.
- The slice lands on the nearest node plane every time.

**Value mode.** 143 interior cells carry their node's band color.

**Controls.**
- Typed values snap to node planes; ▶ and ◀ step $2\pi/102$; the angles wrap at $\pm\pi$.
- The slider lands on node planes.
- Click selects the node and plays its engagement; the selection ring is drawn.
- PNG and the $\tau$ GIF capture the regions.
- The style is restored after a reload, and switching back to dots brings back the dots and the
  slab.
- With the slice off, the row fills.
- The M1 regions are at the exact plane.
- A layout saved with the separate map comes back as Overview.
- **30 of 30 checks pass.**

**Regression.**
- The v8 suite passes 91 of 91: tabs, drawer and Esc order, docking, appearance and exports.
- Engagement rollouts against Python agree in 1000 of 1000, with kill times to $1.6 \times 10^{-12}$.
- file:// loading works.
- There are no page errors.

## Not done / caveats

- **The orientation differs from the slides.** The regions use the slice panel's axes ($\phi_2$
  to the left), not the slides' ($\phi_1$ across, $\phi_2$ up), so the dots and the regions line
  up when switching. An $R$ plane therefore looks transposed and mirrored next to a slide figure.
- **The 101 grid's planes are not the slide's planes.** Asking for $R = 2, 4.52, 5.48$ gives
  $1.97, 4.48, 5.43$. The slides' values match the fine grid. Loading the 201 Vsnaps puts the
  regions on those planes, at about 0.4 GB in memory per file.
