# Layer 1 — M4 rerun on the pole field: criteria

**AE 8900 · criteria fixed 2026-10-29, before the run · Ethan Stroup**

This record is written to be read cold.
- **§1–§6 are fixed before the run.** Results go in §7, appended afterward. Nothing above §7
  changes after the run.
- **Code:** `layer1/M4/test_m4.py` with `LAYER1_POLE=1`, and its loader `layer1/M4/pole_source.py`.

**What was seen before writing.** No value of the solved $V$ was read, at any trajectory point or
anywhere else. Only these were looked at:
- the M4 record, audit and logs from the $R_{\min}=0.2$ run (`Overview/Layer1/Layer1_M4_2026-10-06.md`,
  called "v2" here), and the M5 pole record (`Overview/Layer1/Layer1_M5_PoleRerun_2026-10-15.md`);
- Layer 0's 122 trajectories, regenerated, and $\ell$ along them;
- the coarse pole file's metadata and its $\tau=0$ snapshot. That snapshot is $\ell$ on the grid:
  it equals `float32(pole.fill(ell))` exactly;
- two dry runs of the new code on a stand-in field $V:=\ell$, with every snapshot replaced by the
  $\tau=0$ one (coarse from the file, fine built the same way). They checked the mechanics, and
  they supply the null numbers in §2 and §3.

---

## 1. Why rerun, and what changes

- **The field of record changed.** Since 2026-10-15 it is M5's single-target $V_1$ on the pole
  grids (PoleRerun §5, decision 1). v2 ran on M3's $R_{\min}=0.2$ grid, whose inner face leaked.
- **What the run reads.** `VRAsnap_<grid>_T6_single_pole.npz`: $V(\cdot,\tau)$ every 0.25 in
  $\tau$ (v2 had 0.5). The 3 mirror rows are kept, so values just above $R=0$ are the solve's own.
- **Unchanged:** the ceil read, the samples, and the tolerance rule. $\delta$ is the grid's own
  one-cell value change: 0.1194 coarse and 0.0599 fine (v2: 0.118 and 0.059).
- **The loader refuses** anything that is not the single-target pole solve under the same $\ell$
  weighting. It also stops if the grid rows, the $\tau$ axis, the mirror rows or the cell disagree
  with the file (`pole_source.py`, docstring).
- **Added:** report-only items for every family (§4) and a scored min-range block (§5).

---

## 2. The gate, unchanged

Mask $R\ge0.45$, ceil read, tolerance $\delta$.

| check | criterion (as in v2) |
|---|---|
| Layer 0 bundle | $\max\lvert FI-1\rvert$ and $\max\lvert H^*\rvert$ below $10^{-6}$ |
| A, seeds | BUP seeds read $\lvert\ell\rvert\le\delta$ on the $\tau=0$ snapshot (checks $\ell$) |
| **A, off-boresight** | median agreement length $\ge1.0$ |
| **B, off-boresight** | median angle between $\nabla V$ and $\lambda$ below $15°$ |
| B, all retained points | median angle below $45°$ |
| **C1** | $\sigma_1^*$ and $\sigma_2^*$ each above 90 % on the retained points |
| negative control | SKIP while no retained point reaches $R=8$ |
| D | analytic $\ell$ below $5\times10^{-3}$ at the eligible Table 2 points (checks $\ell$) |
| E | the flagged fraction is between 0 and 5 % of masked nodes |

- **Prediction:** it passes on both grids, with numbers close to v2's. The pole changed $V$
  mainly below $R=1$ (PoleRerun §4.2–4.3).
- **If anything fails,** M4's gate is reopened on the field of record. No criterion changes.
- **The gate can tell a solve from no solve.** On the stand-in $V:=\ell$ it fails three checks
  on both grids:

| stand-in $V:=\ell$ | 101 | 201 | bar |
|---|---|---|---|
| A, off-boresight median length | 0.74 | 0.50 | $\ge1.0$ |
| B, off-boresight median angle | $23.0°$ | $17.1°$ | $<15°$ |
| C1, $\sigma_2^*$ | 53.7 % | 53.3 % | $>90$ % |

---

## 3. What $\ell$ alone shows

**The $\ell$ null** is M4's own walk with $V$ replaced by $\ell$ on the grid (the $\tau=0$
snapshot), on the same samples and with the same $\delta$. It is the agreement a solve that did
nothing would get.

| median agreement length in $\tau$ | v2, 101 | null, 101 | v2, 201 | null, 201 |
|---|---|---|---|---|
| off-boresight | 1.69 | 0.74 | 1.62 | 0.50 |
| min-range | 0.26 | 0.26 | 0.18 | 0.18 |
| max-range | 0.20 | 0.20 | 0.16 | 0.16 |

The nulls are on the pole grids.

- **Off-boresight.** v2's agreement runs about 1 in $\tau$ past the null on both grids. That part
  is the solve's.
- **Max-range.** All 8 departure times in v2's table (record §3.1) equal the null's, on both
  grids. That is the record's own reading (§4.2): past the crossing, $V=\ell$.
- **Min-range.** v2's medians equal the null's. The record blamed the leaky inner face (§4.4).
  $\ell$ gives a different reason.

### 3.1 The min-range bundle runs into $T_1$, or along its face

Retrograde from their seeds:
- **20 trajectories** (seeds at $\lvert\phi_2\rvert\le132.85°$, $R$ from 0.35 to 0.53) go inside
  $T_1$ at once. $R$ rises above $R_{lo}(\phi_2)$ while $\lvert\phi_1\rvert<\beta$, and $\ell$
  falls to between $-0.10$ and $-0.41$. By $\tau\approx1$ they leave $T_1$ again and climb to
  $\ell=0.16$–$1.01$. In forward time, each one crosses $T_1$ and leaves it at its seed.
- **28 trajectories** (seeds at $\lvert\phi_2\rvert\ge137.28°$, $R$ from 0.25 to 0.33) stay within
  0.084 of $\partial T_1$ for all $\tau\le6$, switching 9 to 34 times. 20 of them are mostly just
  inside; 8 are just outside, with $\ell\le0.06$.

So $\ell$ alone decides $\lvert V\rvert\le\delta$ along this bundle:
- **Inside $T_1$ by more than a cell,** $V\le\ell<-\delta$ forces a departure. $V$ is
  non-increasing in $\tau$, so $V\le\ell$ node for node.
- **Within a cell of $\partial T_1$,** $\ell$ already agrees.

No mask changes this, and neither does the pole. The grid-$\ell$ classes of all 48 at $R\ge0.20$,
from the dry runs:

| the null departs | 101 | 201 |
|---|---|---|
| inside: enters $T_1$ | 14 | 26 |
| never: within a cell of $\partial T_1$ throughout | 28 | 22 |
| outside: leaves outward | 6 | 0 |

*An inference, not a measurement:* `seeds_minrange` keeps every root of D&S Eq. (46). The seeds
whose retrograde flow enters $T_1$ lie on the branch of the BUP where the forward flow leaves
$T_1$, so they are not barrier trajectories.

### 3.2 The off-boresight bundle enters $T_1$ too, later

36 of the 64 tested trajectories reach $\ell<-\delta$ (analytic $\ell$). They first do so at
$\tau$ from 0.68 to 4.30 coarse (median 2.26), and from 0.45 to 4.27 fine (median 1.74). v2
counted 36 inside departures on each grid. Whether those are the same events is what §4's
classes show.

---

## 4. Report only, every family (rules fixed now)

- **R-1, the null.** Per family: the $\ell$-null length, and the median per-trajectory difference
  between $V$'s length and the null's.
- **R-2, what made each departure.**
  - *forced:* $V<-\delta$ at a point where the grid's $\ell<-\delta$. The trajectory is inside
    $T_1$ there, and the departure is automatic.
  - *own:* $V<-\delta\le\ell$. The solve puts the point in the winning zone where $\ell$ alone
    would not.
  - *outside:* $V>\delta$.
  - *never:* no departure.

  The retained-switch line in C1 also prints how many of its inside departures are forced.

**How they will be read (fixed now):**
- **I-1, the switch junctions** (record §4.3). If every inside departure after a retained switch
  is forced on both grids, the junction reading is withdrawn: after the switch, the Layer 0
  trajectory enters $T_1$, and the departure says nothing about the post-switch segment. Any own
  departure keeps the junction reading for that switch.
- **I-2, the outward off-boresight departures** (record open item 2). Not addressed here; the
  item stays open.

---

## 5. Min-range, scored

- **Mask $R\ge0.20$.** It keeps every min-range sample (the lowest is $R=0.242$) and stays above
  the rows where M5's check 4 found the fine-grid asymmetry ($R\le0.15$). The gate's 0.45 is
  untouched.
- **Classes,** from the grid-$\ell$ null on each grid: enters $T_1$, within a cell, outward.
- **Informative:** the outward class only. Only there can $\lvert V\rvert\le\delta$ past the null be
  the solve's own work.

| per grid | verdict |
|---|---|
| fewer than 10 informative trajectories (5 mirror pairs) | **NOT TESTABLE** |
| otherwise, median of ($V$'s length − the null's) over the informative ones $\ge0.5$ in $\tau$ | **PASS** |
| otherwise | **FAIL** |

**Across grids:** NOT TESTABLE if either grid is; PASS if both pass; otherwise FAIL.

**Expected: NOT TESTABLE on both grids,** with 6 and 0 informative. The counts depend on $\ell$
alone, so the run must reproduce them. If it doesn't, the loader is reading something else.

**Report only:**
- $V$'s departure kinds in each class.
- *Enters $T_1$:* $V$ departs inside at or before the null. Expected for all of them, since
  $V\le\ell$; a miss is a loader fault.
- *After re-exit:* for each trajectory that enters $T_1$ and later climbs to $\ell\ge2\delta$, $V$ at
  the first such sample, counted as within $\delta$, below $-\delta$ or above $+\delta$. This says
  what the grid makes of those segments. Layer 0 gives no truth there.

**If NOT TESTABLE, as expected:**
- close M4's open item 4 as *not testable with Layer 0's min-range bundle* (§3.1), instead of
  *needs a smaller $R_{\min}$ or a fixed inner face*;
- correct record §4.4: the 20 trajectories left $\{V=0\}$ because they enter $T_1$, if the run
  shows those departures as forced.

---

## 6. Running it

From `layer1/M4/`, in cmd:

```
set "LAYER1_POLE=1"
python test_m4.py 101x102_T6_single_pole > m4_out\m4_101x102_pole.log
python test_m4.py 201x204_T6_single_pole > m4_out\m4_201x204_pole.log
```

In PowerShell, set it with `$env:LAYER1_POLE = "1"` and write the log with
`| Out-File -Encoding utf8 m4_out\<name>.log`.

- **Time.** The dry runs took 2 min coarse and 8 min fine in the cloud workspace.
- **Memory.** The fine stack is read one 34 MB snapshot at a time.
- **Inputs.** `layer1/M5/m5_out/m5_out_V1_pole/` (`VRAsnap_*` and `m5_*.json`); set `M4_POLE_DIR`
  if they move.

---

## 7. Results

**Not run (status 2026-11-04).** `m4_out/` holds no pole logs. Until the run is done:

- **M4 of record** stays the $R_{\min}=0.2$ run ("v2", `Overview/Layer1/Layer1_M4_2026-10-06.md`).
  The final report quotes its numbers.
- **§3.1 stands without the run.** It depends only on $\ell$, and on $V\le\ell$ for any $V$ with
  $V(\cdot,0)=\ell$ that does not increase in $\tau$. So the min-range bundle cannot test the solve on
  any grid. The M4 record (§4.4, open item 4) and the close-out (§2, §6 item 2) now say this. The
  run would still check the expected NOT TESTABLE verdict and the forced/own classes of §4.
- **If it is run,** §1–§6 apply as written, and the results go here.

*Edit 2026-11-04:* the header and §6 no longer say to run on branch `Test`, because the code is on
`main` now. No criterion changed.
