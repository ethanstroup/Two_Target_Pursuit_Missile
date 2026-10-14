# Two-Target Pursuit — 2v1 Air Combat with Bidirectional Lethality

**AE 8900 · Ethan Stroup · Fall 2026**

Two friendly aircraft engage one hostile aircraft in the horizontal plane. All three carry
all-aspect fire-and-forget missiles, so any of them can kill any opponent; nobody is a designated
pursuer. The hostile aircraft has one nose and can only threaten one attacker at a time. The
project asks how the outcome (who kills whom, or nobody) partitions the state space, given that.

It is built in **layers**, each a self-contained problem closed before the next starts. Layers 0
and 1 are the 1v1 game of Davidovitz & Shinar (1989), solved first by their analytic method and
then numerically; Layer 2 is the 2v1 game itself. The full specification is
[`Overview/ProblemStatement.md`](Overview/ProblemStatement.md).

## Status

| Layer | Question | State |
|---|---|---|
| 0 | Reconstruct D&S's 1v1 barriers from the costate equations | **Closed 2026-09-11.** Barrier trajectories and the boundary of the usable part verified against the paper's Table 2 |
| 1 | Solve the 1v1 game numerically (HJI reachability) and partition it by guarantees | **M1–M4 done; M5 solved 2026-10-11.** The central claims hold and D&S's corrected boundary is reproduced; the failed checks are diagnosed in the M5 record, and the 2026-10-13 inner-face follow-up leaves check 8 open |
| 2 | The 2v1 game: six states, four target sets | Not started |
| 3 | Synchronization as a derived property | Deferred |

## Repository layout

```
Overview/                 written records: the spec, plans, results, explainers
  ProblemStatement.md       the specification of record
  Layer0/                   Layer 0 records
  Layer1/                   Layer 1 plan, milestone records and explainers
  LitReview/                literature review index and per-paper notes
  A. Davidovitz and J. Shinar ... 1989.pdf   the base paper
layer0/                   code: barrier reconstruction        (see layer0/README_LAYER0.md)
  common/  closeout/  singular_lines/  viz/
layer1/                   code: HJI solve, milestones M1-M5   (see layer1/README_LAYER1.md)
  common/  M1/  M2/  M3/  M4/  M5/  viz/
heuristic_simulator/      the original interactive demo: forward simulation under a
                          pure-pursuit heuristic (index.html), plus its acceptance tests
```

Large solver outputs (`layer1/M*/m*_out/`) and generated figures (`*.png`) are not tracked by
git; the scripts regenerate them.

## Where to start reading

1. [`Overview/ProblemStatement.md`](Overview/ProblemStatement.md): §1 is the engagement in words,
   §3–§6 the layers.
2. Layer 0: [`Layer0_CloseOut_2026-09-11.md`](Overview/Layer0/Layer0_CloseOut_2026-09-11.md) for
   what was verified, then [`Layer0_RetrogradeMethod.md`](Overview/Layer0/Layer0_RetrogradeMethod.md)
   for how a barrier trajectory is built.
3. Layer 1: [`Layer1_Plan.md`](Overview/Layer1/Layer1_Plan.md), then the explainers in milestone
   order (`Layer1_M1_Explainer.md` … `Layer1_M5_Explainer.md`). They are plain-language
   walkthroughs written to be read cold.
4. The dated files (`Layer1_M4_2026-10-06.md`, `Layer1_M5_2026-10-11.md`, …) are the records of
   what each run found. Read them for detail, in date order.

The dated records quote file paths as they were on their dates. The code was reorganized into
the folders above on 2026-10-14; each layer's README maps the current layout.

## Setup

Python 3.13 (what `.venv` was built with) and the pinned packages:

```
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Layer 1 uses `hj_reachability` 0.7.0 on JAX in float64. The browser explorers
(`layer0/viz/barrier_explorer.html`, `layer1/viz/ell_explorer.html`, `heuristic_simulator/index.html`)
open straight from the filesystem with no build step. The JavaScript test scripts need Node.js;
nothing else does.

Quick checks that the setup works:

```
python layer0/closeout/test_mirror.py      # seconds
cd layer1/M1 && python test_m1.py          # a few minutes
```

Each layer's README has the full run order.
