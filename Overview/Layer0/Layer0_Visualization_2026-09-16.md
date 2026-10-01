# Layer 0 Visualization — the barrier as a swept surface

**AE 8900 · 2026-09-16 · Ethan Stroup**
Everything lives in `layer0/viz/` and calls `layer0/barrier.js` / `layer0/barrier.py`.
Nothing re-derives anything. The written method account is
`claude/Layer0_RetrogradeMethod.md`, mirrored in the repo at `layer0/RETROGRADE_METHOD.md`.

`reproduce_figures.py` redraws the figures the paper prints. This does the other job:
it shows how the barrier is *built*. The (BUP) is a curve; every point of it is a terminal
condition fixed by transversality; integrating retrograde from each one gives a barrier
trajectory, and the bundle of them is the semipermeable sheet.

**All four surface families are covered** — maximum range, minimum range, and both
off-boresight limits — with seeds ordered along every branch.

---

## 1. Ordered seed curves — `bup_curves.py` / `bup_curves.js`

Sweeping φ₂ and taking whatever roots come back does not give an ordered curve, and an
unordered seed set cannot render as a surface. Three things go wrong and all three are now
handled by continuation:

- where Eq. (32) or Eq. (46) has several roots, the naive order jumps between sheets —
  fixed by matching each root to the branch it continues, by linear prediction;
- where two roots merge at a fold, the two halves of one smooth curve come back as unrelated
  lists — fixed by splicing them, with the fold point itself refined by bisecting on *whether
  two roots still exist* (near a fold the roots separate like √(φ₂\* − φ₂), so a φ₂ grid loses
  them while they are still half a degree apart in φ₁, and the traced lens stops short of d₁);
- where a family's admissible φ₂ interval is disconnected, or crosses φ₂ = ±π, the order
  jumps the width of the axes — fixed by merging across the seam and carrying φ₂ unwrapped.

Resampled points are then **snapped back onto the defining root**: linear interpolation lands
slightly off it, which shows as H\* ≈ 1e−5 at the seed, and a seed that is not semipermeable
is not a barrier point. After the snap every seed carries |H\*| ≤ 4.4e−16.

**What this produced, per family** — and every endpoint turns out to be a published point:

| family | branches | φ₂ support | endpoints |
|---|---|---|---|
| max | 2 mirror lenses | \|φ₂\| < 9.5694° | O₁, e₁, folding at **d₁** |
| min | 2 mirror arcs | \|φ₂\| ≥ 93.07°, through the seam | **h₁**, **g₁** |
| bore± | 1 each | one arc through the seam | **m₁**, **N₁** |

The minimum-range branches terminate on φ₁ = ±β, which is exactly how the paper defines g₁
and h₁; the boresight branches terminate at the corner with the minimum-range surface, which
is m₁ and N₁. So the four families are arcs of one boundary joined at corners, and the traced
curves say so.

## 2. `visualize.py` — the figure set

Eleven figures into `layer0/viz/figs/`:

| file | shows |
|---|---|
| `<fam>_1_bup.png` ×4 | the (BUP) alone in both printed faces, over the target-set boundaries, with Table 2 overlaid |
| `<fam>_2_sheet.png` ×4 | the retrograde bundle and the sheet it sweeps |
| `all_bup.png` | the whole boundary of the usable part, all four families in one picture |
| `diagnostics.png` | one trajectory in full: states, costates, σ₁\*/σ₂\*, invariants, switches marked |
| `invariants.png` | residuals over every trajectory, by family |

Table 2 points are drawn **filled and named where the curve reproduces them, hollow
otherwise**, so the verification is visible rather than asserted. 10 of the 59 lie on a
(BUP) curve; the rest are interior barrier features, as close-out §4 says.

```
python3 layer0/viz/visualize.py [outdir] [--tau 1.5] [--nseed 45]
```

## 3. `barrier_explorer.html` — the interactive version

Standalone page, no build and no server. Loads `../barrier.js` and `./bup_curves.js`.

- **τ starts at exactly 0**, where only the (BUP) is drawn, over R̄₁(φ₂) and R_min(φ₂) with
  the Table 2 points — so a family can be checked against the printed figure directly before
  any integration enters the picture. Raise τ to sweep the sheet.
- **wheel zooms about the cursor** on all three trajectory views, **drag pans** (rotates, in
  the 3-D view; shift-drag pans there), **double-click** resets one view. A view follows the
  auto-fit while scrubbing τ and freezes the moment it is touched.
- **click selects a trajectory in any of the three views**; the marker then travels it as τ
  elapses. **play** animates τ from 0; **focus** hides everything else while you watch one.
- **save PNG** stitches the three trajectory views into one labelled image for a deck.
- readout gives R, φ₁, φ₂, the three costates, σ₁\*/σ₂\*, |FI−1|, |H\*|, switch count and the
  seed; the geometry panel evaluates Eq. (7)'s firing conditions both ways round; the costate
  panel marks the switch times with log₁₀|H\*| overlaid.

Rebuild is 90–400 ms and the status line reports the bundle's own error certificate.

## 4. Verification — `test_viz.py`, 26 checks

The figures and the explorer come from two independent implementations of the same seed
curves, which is only worth having if they are provably the same object:

- **branch structure** per family (2, 2, 1, 1);
- **ordering**: the largest step along a branch is ≤ 1.21× the median, on the sphere, so
  there are no branch-to-branch jumps left;
- **every seed on the barrier**: max |FI−1| and |H\*| ≤ 1e−15 across all four families;
- **invariants along the bundle** at τ = 3: worst 4.9e−12 (minimum range, 752 switches);
- **published points**: d₁, e₁, g₁, h₁, Q₁ all within 3.4e−3 of a traced seed;
- **`bup_curves.js` reproduces `bup_curves.py`** seed by seed — max |py − js| over the
  six-vector is **1.0e−13**.

Everything that existed before still passes: `test_barrier_js.js` 14/14, `test_barrier.py`
all checks, `verify_symbolic.py` 22/23 with the documented Eq. (63) failure,
`validate_table2.py` 27 placed.

---

## Files

```
layer0/RETROGRADE_METHOD.md                 the method, surface by surface
layer0/viz/README.md                        how to run it
layer0/viz/bup_curves.py                    ordered seed curves, all four families
layer0/viz/bup_curves.js                    its twin, cross-checked by test_viz.py
layer0/viz/visualize.py                     the figure set
layer0/viz/barrier_explorer.html            the interactive explorer
layer0/viz/test_viz.py                      26 acceptance checks
layer0/viz/figs/*.png                       11 figures
```

**Stale copies to delete** — no delete capability in that session, so they are still on disk:

```
layer0/viz/figs/maxrange_[1-5]_*.png        superseded by the four-family set
layer0/visualize.py                         superseded by layer0/viz/
layer0/figs/maxrange_[1-5]_*.png            superseded; mixed in with reproduce_figures output
heuristic_simulator/barrier.js              a shim re-exporting layer0/barrier.js
heuristic_simulator/barrier_explorer.html   superseded by layer0/viz/
```
