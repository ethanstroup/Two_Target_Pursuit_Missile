# Layer 0 — barrier reconstruction from the costate ODEs

**AE 8900 · Ethan Stroup · layout reorganized 2026-10-14**
Close-out record: `Overview/Layer0/Layer0_CloseOut_2026-09-11.md`. The dated records of later
work are beside it in `Overview/Layer0/`; this file only says where the code lives and how to
run it.

## Layout

```
layer0/
  common/           shared by every folder below, by Layer 1 and by the heuristic simulator
    barrier.py        dynamics, costates, invariants, BUP, retrograde integrator
    barrier.js        its port for the browser (explorers, heuristic_simulator/test_barrier_js.js)
    validate_table2.py  the 59 Table 2 points (TABLE2) and their acceptance test
  closeout/         the 2026-09-11 close-out: the reconstruction verified
    verify_symbolic.py  23 sympy re-derivations       -> 22 pass, 1 documented failure
    test_barrier.py     invariants and printed control laws on the 122 trajectories
    test_mirror.py      the T_2 index swap (4/4, machine precision)
    reproduce_figures.py  redraws Figs. 4, 5, 6, 8, 10, 11 -> figs/
    sens.js             Rbar_0 sensitivity of the spec Sec. 9 grid statistics
    figs/
  singular_lines/   assembling the barrier: the max-range audit and the Table 3 singular lines
    diag_maxrange.py    max-range BUP audit             -> figs/diag_maxrange.{png,txt}
    corner_family.py    corner-edge family, f_1 diagnostic -> figs/fig8_dispersal.png
    universal_d1.py     universal line from d_1          -> figs/universal_d1.png
    dispersal_e1c1O.py  dispersal line e_1 c_1 O, and c_1 -> figs/dispersal_e1c1O.png
    fig8_zones.py       Fig. 8 capture zones             -> figs/fig8_capture_zones.png
    commuting_s1u1.py   commuting line S_1 U_1           -> figs/commuting_s1u1.png
    table3.py           Table 3 transcribed, with lookups against TABLE2
    figs/
  viz/              the barrier as a swept surface: seed curves, figure set, interactive explorer
    barrier_explorer.html  the explorer; open it straight from the filesystem
    bup_curves.py/.js   BUP seed curves (Python and its browser twin)
    visualize.py        the static figure set -> figs/
    test_viz.py         seed curves, invariants, and the JS twin against Python
    explorer/           the explorer's stylesheets, JS modules and their tests
    README.md           the full file list and the explorer's interface
```

`singular_lines/` scripts use `viz/bup_curves.py` for the BUP seed curves. Every Python script
puts `common/` (and, where needed, `viz/`) on `sys.path` from its own location, so they run
from any working directory.

## Which record goes with which folder

| `Overview/Layer0/` record | folder |
|---|---|
| `Layer0_CloseOut_2026-09-11.md`, `Layer0_RetrogradeMethod.md` | `common/`, `closeout/` |
| `Layer0_Visualization_2026-09-16.md`, `Layer0_CoordinateTabs_2026-09-23.md` | `viz/` |
| `Layer0_MaxRangeAudit_2026-09-17.md`, `Layer0_Fig8_CaptureZones_2026-09-17.md`, `Layer0_Handoff_2026-09-21.md` | `singular_lines/` |
| `Layer0_BoresightSec33_2026-09-21.md` | `viz/` (`bup_curves`, `test_viz` §9) |

## Run order

```
python3 layer0/closeout/verify_symbolic.py      # equations
python3 layer0/common/validate_table2.py        # published ground truth
python3 layer0/closeout/test_barrier.py         # the reconstruction
python3 layer0/closeout/test_mirror.py          # the T_2 index swap Layer 1 relies on
python3 layer0/closeout/reproduce_figures.py layer0/closeout/figs
python3 layer0/viz/test_viz.py                  # seed curves, and the JS twin (needs node)
node    heuristic_simulator/test_barrier_js.js  # the JS port
node    heuristic_simulator/test_acceptance.js  # the existing sim, re-baselined
node    layer0/closeout/sens.js                 # the sensitivity result of the close-out Sec. 5.3
```

Requires `numpy`, `scipy`, `sympy`, `matplotlib`; the JS checks need Node.js.
