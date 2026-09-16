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
| `test_viz.py` | 26 acceptance checks |

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
- **click** selects a trajectory in any of the three views; **play** then walks the marker
  along it as τ elapses, and **focus** hides everything else while you watch.
- **save PNG** stitches the three trajectory views into one image for a deck.

## Ordering

Seeds are ordered along each (BUP) branch by continuation, not by sweeping φ₂: roots are
matched to the branch they continue, branches that die together at a fold are spliced, runs
meeting across the φ₂ = ±π seam are merged, and resampled points are snapped back onto the
defining root. Without that the bundle is a pile of curves rather than a surface. The two
implementations must agree — `test_viz.py` compares them seed by seed and fails past 1e−9.
