# Layer 1 — M5 rerun on the pole grids

**AE 8900 · runs 2026-10-13/14, scored 2026-10-15 · Ethan Stroup**

This record is written to be read cold. It scores the full M5 sequence rerun on the pole grids
against the **unchanged** pre-registered criteria, compares every check with the original
$R_{\min}=0.2$ run, and diagnoses each failure.

**Criteria of record:** `Overview/Layer1/Layer1_M5_Criteria_2026-10-11.md` (§1–7, unchanged).
**Why the rerun:** `Overview/Layer1/Layer1_M5_InnerFace_2026-10-13.md` §7 (Ethan chose to rerun M5 on
pole grids) and §8–9 (the check 8 procedure on non-nesting rows and the driver, both fixed
before any fine pole solve ran).
**Original run:** `Overview/Layer1/Layer1_M5_2026-10-11.md`.
**Logs:** `layer1/M5/m5_out/m5_out_V1_pole/pole_run/01_smoke.log` … `12_final_check13.log`.

Sections 1–5 are the scored run, as logged. Section 6 holds report-only diagnostics computed
after the scoring (`diag/diag_pole_rerun.py`); none of them was pre-registered, and none changes a
score.

---

## 1. Verdict

| | original ($R_{\min}=0.2$) | **pole rerun** |
|---|---|---|
| checks passed | 8 of 14 | **9 of 14** |
| failed | 3, 5, 6, 8, 9, 12 | **4, 5, 6, 9, 12** |
| newly passing | — | **3, 8** (and check 6 on the coarse grid) |
| newly failing | — | **4** (fine grid only) |

**What the rerun establishes.**
- **Check 8 is settled.** The six far flips at $R=0.554$ were the old fine grid's own inner face.
  At those states both pole grids give $V^{RA}_1=\ell_1=+0.258$ to $+0.274$, equal to four decimals.
  The old fine grid said $-0.007$ to $-0.036$.
- **Check 3 passes in the scored suite,** 500 / 500, as the inner-face record predicted.
- **The central results stand unchanged.**
  - The guarantee: 0 failures in 11,885 runs.
  - The converse: 0 wins alone in 10,000 runs, informative from 346 starts.
  - Table 2: 0 / 12 and 0 / 5 misses.
  - The contested set is **FAT**.
- **The partition barely moves.** On the fine grid, $W_1$ moves by $-0.07$ points of $\Omega$ and $C$ by
  $+0.004$. Almost all of the $W_1$ change is the old fine grid's false near-face sliver.
- **Late-horizon motion drops 5–7×.** The final 0.25-step moves 0.034 % (coarse) and 0.043 %
  (fine) of $\{V^{RA}_1=0\}$, against 0.167 % and 0.297 % before.

**What fails, and why.**
- **Check 4, fine (new).** The worst asymmetry is $0.042\,\delta$ against a bar of $0.01\,\delta$.
  - It lies on the tail-chase line, $\phi_1\approx\pm180°$ with $\phi_2\approx0$, almost all of it
    in the three innermost rows ($R\le0.15$).
  - It sits far from the zero level set, and $W_1$ is exactly $Rf$-symmetric.
  - No set or simulation result depends on it (§4.1).
- **Checks 5, 6, 9 and 12.** Same failures and same diagnoses as the original (§4.4–4.6).
  - Check 5's set-inclusion half now holds on both grids.
  - Check 6 now fails only on the D&S mutual-kill diagonal.

---

## 2. What ran

`python run_m5_pole.py` from `layer1/M5/` ran unattended on Ethan's machine and in sequence. The
outputs were moved afterward from `m5_out/` to `m5_out/m5_out_V1_pole/`.

| step | what | finished | wall time |
|---|---|---|---|
| 1 | smoke checks 1, 1b, 2, 3 at $61\times62^2$, $T=4$ | 10-13 22:50 | 13.6 min |
| 2–3 | coarse $V^{RA}_1$ march to $\tau=10$, horizon rule, cut at $T_{RA}$ | 10-13 23:19 | 28.3 min |
| 4 | coarse $V_1$ (`single`) | 10-13 23:36 | 17.0 min |
| 5–6 | $51\times52^2$ game and $V_1$ | 10-13 23:37 | 0.9 min |
| 7 | preview checks on coarse and third grids | 10-13 23:37 | 0.5 min |
| 8 | **fine $V^{RA}_1$**, $201\times204^2$, $T=6$ | 10-14 10:37 | **11.0 h** |
| 9 | check 8 preview | 10-14 10:37 | 0.1 min |
| 10 | **fine $V_1$** | 10-14 21:40 | **11.0 h** |
| 11–12 | `test_m5.py 6`, `converse_m5.py 6` | 10-14 21:41 | 1.5 min |

- **Total time** was 23.1 h, against the 36 h estimated in InnerFace §9.
- **Each fine solve** took 11.0 h (1,650 s per 0.25 of $\tau$), against the 16–17 h estimated.
- **The third grid** is $51\times52^2$, not $51\times51^2$, because the pole map needs an even
  $n_\phi$.

---

## 3. Results

### 3.1 Scored checks

| # | Check | pole rerun | numbers | original |
|---|---|---|---|---|
| 1 | $\ell_2$ written out $=\ell_1\circ S$ | **PASS** | max difference 0 on every grid | PASS |
| 1b | library form vs Algorithm 1 | **PASS** | 324 sign flips, 0 more than 2 cells out | PASS (218) |
| 2 | frozen controls vs exact inertial truth | **PASS** | $(0,0)$: 356 flips; $(+1,-1)$: 2165 flips; 0 far. 40,868 and 27,107 nodes excluded (left through $R=12$) | PASS |
| 3 | $\sigma_2\equiv0$, grid-law rollouts | **PASS** | 500 / 500 win alone; 6 runs pass inside $R=0.25$ | FAIL (498 / 500) |
| 4 | reflection | **FAIL** | coarse $1.2\times10^{-7}$ (bar $1.19\times10^{-3}$); **fine $2.53\times10^{-3}$ (bar $5.99\times10^{-4}$)** | PASS |
| 5 | $V^{RA}_1\ge V_1-0.01\,\delta$ | **FAIL** | worst $0.26\,\delta$ coarse, $0.27\,\delta$ fine, both inside $T_{2\to1}$; $W_1\subseteq\{V_1\le0\}$ holds (0 nodes on each grid) | FAIL |
| 6 | $W_1\cap W_2=W_1\cap D=\emptyset$ | **FAIL** | coarse 0 and 0; fine 3542 and 0 | FAIL (coarse 0 / 6, fine 3608 / 16) |
| 7 | horizon | **PASS** | final step moves 0.034 % (coarse), 0.043 % (fine) | PASS (0.167 %, 0.297 %) |
| 8 | grid convergence of $\partial W_1$ | **PASS** | displacement 0.294 coarse cells; 0 of 1212 flips beyond 3 cells (fine field interpolated in $R$, InnerFace §8) | FAIL (0.393; 6 of 1632) |
| 9 | topology of $W_1\cap\Omega$ | **FAIL** | 4 components $[122247, 122247, 3626, 3626]$, two mirror pairs | FAIL |
| 10 | Table 2 points on $\partial W_1$ | **PASS** | 0 / 12 off-target misses; 0 / 5 on-target misses | PASS |
| 11 | $W_1$ guarantee | **PASS** | 0 failures in 11,885 runs (2377 starts × 5 laws) | PASS (11,895) |
| 12 | negative control | **FAIL** | 0 of 2377 starts beaten (bar 20) | FAIL |
| 13 | converse guarantee | **PASS** | 0 wins alone in 10,000 runs against the adversary; informative from 346 starts (bar 20) | PASS (335) |

Check 4 and the field half of checks 5–6 are scored on both main grids. A check passes only if both
grids do.

### 3.2 Horizon

- **$T_{RA}=6$ again,** by the pre-registered rule.
- **The coarse march.** From $\tau=6$ to 10, $\{V^{RA}_1\le0\}$ grows from 7.867 % to 7.874 % of the
  grid. No 0.25-step after $\tau=6$ moves more than 0.034 % of the surface. The original moved up
  to 0.21 %, growing 8.110 % → 8.148 %.
- **Attribution.** The inner face is the only modeling change between the runs, so most of the old
  late-horizon motion came from it. The pole grid's rows also sit at different $R$, so this is
  not a clean ablation.

### 3.3 The partition, as a share of $\Omega$

| set | $51\times52^2$ | $101\times102^2$ | $201\times204^2$ | original fine |
|---|---|---|---|---|
| $W_1$ (and $W_2$) | 3.588 % | 3.565 % | **3.564 %** | 3.636 % |
| $D$ | 91.944 % | 91.714 % | **91.863 %** | 91.723 % |
| contested $C$ | 1.068 % | 1.157 % | **1.060 %** | 1.056 % |
| $\Omega$ nodes | 116,440 | 890,126 | 7,064,091 | 7,171,813 |

- **Overlap.** $W_1$ and $W_2$ overlap on the diagonal (3542 nodes), so the fine row sums to 100.05 %.
- **Node counts.** They differ from the original because the pole rows sit at different $R$.
- **Terminal sets.** As a share of $R\ge0.45$ on the fine grid, $T'_1$ and $T'_2$ are 4.864 %
  each and $T_{1\to2}\cap T_{2\to1}$ is 2.323 %.

### 3.4 Thin or fat

- **The fit.** $v=1.068\,\%$, $1.157\,\%$, $1.060\,\%$ on grids 51, 101 and 201. That is not
  monotone in $h$, so the three-point fit is **not valid**: the successive differences change sign
  and no real $p$ exists. The original fit was invalid too, with $p=0.218$.
- **The fallback.** $r=v_{201}/v_{101}=0.917\ge0.85$, so the decision is **FAT**. The original
  had $r=0.885$, also FAT.
- **Supporting measurement (report only, §6).** It takes 7 erosions to empty the player-1 half of
  $C$ on the coarse grid and 14 on the fine. That is the same physical thickness, exactly as in
  the original.
- **The non-monotone point** is the third grid. On the pole family it gives 1.068 %, against
  1.354 % for the old $51\times51^2$. That grid is pre-asymptotic in both families.

### 3.5 Report-only results (as logged)

| item | pole fine | original fine |
|---|---|---|
| $\{V_1\le0\}\setminus\{V_2\le0\}$ vs $W_1$ | 3.574 % vs 3.564 % | 3.645 % vs 3.636 % |
| in $W_1$, not the old set / in the old set, not $W_1$ | 0.518 % / 0.529 % | 0.518 % / 0.527 % |
| $\{V_1\le0\}\cap\{V_2\le0\}$; share of it left in $C$ | 0.989 %; 0.21 % | 0.987 %; 0.2 % |
| $C$ within one coarse cell of $\lvert\phi_1\rvert=\lvert\phi_2\rvert$ | 0.46 % | 0.37 % |
| C2 race from 1000 contested starts (win / p2-kill / mutual / none) | 499 / 498 / 3 / 0 | 480 / 518 / 2 / 0 |
| C2 race, coarse | 455 / 447 / 97 / 1 | 441 / 465 / 94 / 0 |

The "old set" here is built from the pole grid's own $V_1$, the `single` solve, not M3's field
(InnerFace §7, decision 2).

**Check 10 values on the fine grid**, $\delta=0.0599$:

| set | values of $V^{RA}_1$ |
|---|---|
| off-target | $\alpha$ $-0.039$, $\varepsilon$ $+0.023$, $\zeta_1$ $+0.017$, $\rho_1$ $+0.021$, $\tau$ $+0.010$, $E_1$ $+0.023$, $F_1$ $-0.003$, $H_1$ $+0.012$, $S_1$ $-0.021$, $U_1$ $+0.033$, $a_1$ $+0.010$, $b_1$ $+0.016$ |
| on-target | $A_1$ $+0.004$, $B_1$ $+0.002$, $K_1$ $+0.010$, $\tilde Q_1$ $-0.0001$, $h_1$ $+0.014$ |

- The farthest off-target point is again $\alpha$, at $0.66\,\delta$.
- The five points that exist only in the corrected construction are within $0.002$ of where they
  were in the original run.

**Check 13 on the fine grid, in detail.**
- **The pool** holds 24,928 nodes (original 25,402). Start $R$: 10th percentile 3.92, median
  4.40, 90th percentile 4.88.
- **The deterministic player-1 laws.** All four lose every run to the adversary, the trader and the
  heuristic.
- **Against the avoiding player 2,** each of them wins alone from 346 starts.
- **Random bang-bang** never wins alone against the adversary: 1461 player-2 kills, 401 no-kill
  and 138 exits.
- **The coarse grid** is the same as V4(c): a pool of 2006, 270 informative starts, and 0 wins.

---

## 4. Findings

### 4.1 Check 4 fails on the fine grid; the asymmetry is real but harmless

**Where it is** (§6, `diag_pole_rerun.py`):

| region of the fine $V^{RA}_1$ | $\max\lvert V-V\circ Rf\rvert$ | in units of $\delta$ | nodes above $0.01\,\delta$ |
|---|---|---|---|
| all real rows (as scored) | $2.53\times10^{-3}$ | 0.042 | 138 |
| $R\ge0.45$ (identical over $\Omega$) | $8.66\times10^{-4}$ | 0.0145 | 12 |
| $\lvert V\rvert<2\,\delta$ | $6.7\times10^{-8}$ | 0.000 | 0 |

- **All 138 nodes are on the tail-chase line.** That is $|\phi_1|\ge176.5°$ and $|\phi_2|\le1.8°$:
  player 2 sits directly behind player 1 at equal speed.
  - The line is fixed by $Rf$, since $(\pi,0)\mapsto(-\pi,0)=(\pi,0)$.
  - On it, $\dot R=-(\cos\phi_1+\cos\phi_2)=0$ and $\sin\phi_1+\sin\phi_2=0$.
- **126 of the nodes are at $R=0.150$,** the third real row. That is the deepest row the mirror
  copies into the ghost rows; it fills the outermost one. Row by row from $R=0.030$:
  $3.9\times10^{-6}$, $3.3\times10^{-4}$, $2.5\times10^{-3}$, $8.8\times10^{-5}$,
  $1.7\times10^{-5}$, and below $10^{-6}$ by $R=0.39$.
- **The other 12 are at $R=6.494$,** with $V\approx+1.44$, i.e. $24\,\delta$ from zero. The original
  fine field had its largest asymmetry at the same spot ($R=6.454$, $|\phi_1|=176.5°$, $\phi_2\approx0$,
  $1.9\times10^{-4}$). So that spot predates the pole; it has grown about 4.6×.
- **It is not the reach-avoid obstacle.** The fine single-target $V_1$ carries the same spot at
  $R=0.150$, at $2.51\times10^{-3}$. Over $\Omega$, $V_1$ stays within $0.0011\,\delta$.
- **The coarse pole grid is symmetric to storage precision,** in both fields.
  - The solves run in float64: `hji.py` enables `jax_enable_x64`.
  - The fields are saved as float32. The coarse $1.2\times10^{-7}$ is that rounding, at 2 nodes.

**Why it is harmless.**
- $W_1=W_1\circ Rf$ node for node, on both grids. The same holds for $\{V_1\le0\}$.
- Near the zero level set the asymmetry is at roundoff, $6.7\times10^{-8}$.
- The worst nodes have $V\approx+1.68$, i.e. $28\,\delta$ from zero, at $R=0.15$, below the mask.
- So no partition set, no simulation start and no check that uses the sign of $V^{RA}_1$ can see it.

**What causes it is not established.**
- **What is known.** The scheme is $Rf$-symmetric in exact arithmetic, the coarse grid keeps that
  symmetry, and the solve runs in float64. So on the fine grid something seeded at roundoff grows
  to $10^{-3}$.
- **A hypothesis, not tested.** The growth happens on the tail-chase line, which is both
  $Rf$-fixed and an equilibrium of the dynamics ($\dot R=0$, $L=0$). The fine grid takes many more
  steps, because $\Delta t$ is set by its innermost row at $R=0.03$, so it gives that amplification
  longer to act.
- **What would test it.** Rerun the first few 0.25-steps of the fine `single` solve and record the
  asymmetry on that line after every step, to see where it starts and how fast it grows (§5).
- *(Corrected 2026-10-15, same day. An earlier version of this paragraph blamed float32 roundoff.
  The solves are float64; only the saved fields are float32.)*

**Score.** Check 4 stays **FAIL** as pre-registered. The criterion has no mask, and the asymmetry
exceeds the bar even inside $\Omega$, though only on 12 nodes, by $0.0045\,\delta$.

### 4.2 Check 8 is settled: the six far flips were the old fine grid's face

| $R$ | $\phi_1$ | $\phi_2$ | old coarse | old fine | **pole coarse** | **pole fine** | $\ell_1$ there |
|---|---|---|---|---|---|---|---|
| 0.554 | $\mp24.71°$ | $\pm28.24°$ | $+0.1828$ | $-0.0363$ | $+0.2577$ | $+0.2577$ | $+0.2577$ |
| 0.554 | $\mp21.18°$ | $\pm24.71°$ | $+0.2240$ | $-0.0196$ | $+0.2665$ | $+0.2665$ | $+0.2664$ |
| 0.554 | $\mp17.65°$ | $\pm21.18°$ | $+0.2741$ | $-0.0066$ | $+0.2741$ | $+0.2741$ | $+0.2741$ |

- **Both pole grids give $V^{RA}_1=\ell_1$ at all six states.** Player 1 cannot improve on his
  starting margin there.
- **The old fine grid's negative sliver is gone.** InnerFace §5.6 (D2) left two possibilities:
  the fine grid's own face at $R=0.2$, or a real but shallow sliver. The pole fine field rules out
  the second.
- **Agreement across the boundary** (§6). The old fine field, interpolated in $R$ onto the pole
  rows, disagrees with the pole fine field in sign at 5302 nodes at $R\ge0.45$. None of them is more
  than 2 fine cells from either zero set.
  - 4368 of those nodes are at $0.45\le R<1$.
  - In $\Omega$ there, 4010 were $W_1$ only on the old grid, against 82 only on the pole grid.
  - That excess is most of the drop in fine $W_1$: $-0.058$ points of $\Omega$ on the common rows,
    and $-0.072$ between the two runs' own $\Omega$.

### 4.3 The near-face share of $W_1$ is converging

$W_1$ share of $\Omega$ at $0.45\le R<1$ (§6):

| grid family | 51 rows | 101 rows | 201 rows |
|---|---|---|---|
| pole | 17.79 % | 18.68 % | **19.17 %** |
| $R_{\min}=0.2$ | — | 19.70 % | 20.45 % |

- **The pole increments are $+0.89$ then $+0.49$ points.** They roughly halve, which is
  first-order-like convergence.
- **A three-point extrapolation** gives about 19.8 %, with an observed order of 0.85. This is report
  only, an estimate rather than a measurement.
- **The old family grows faster,** by $+0.75$, and sits above the pole family at every resolution.

This answers InnerFace §6's open item ("where the near-face $W_1$ share converges") as far as these
grids can.

### 4.4 Check 5: the same non-monotonicity; the inclusion half now holds

- **The worst nodes are in the same corner as before.** They are inside $T_{2\to1}$, near the
  corner $\eta$ at $R\approx0.8$, $|\phi_1|\approx51°$–$53°$.
  - Coarse: $0.26\,\delta$ (original $0.26\,\delta$).
  - Fine: $0.27\,\delta$ (original $0.20\,\delta$).
- **Inside $\Omega$:** $0.16\,\delta$ coarse and $0.063\,\delta$ fine, against the original
  $0.125\,\delta$ and $0.124\,\delta$.
- **$W_1\subseteq\{V_1\le0\}$ now holds node for node on both grids.** The original had 6 and 16
  sign-tie violations. Those were the same nodes as its $W_1\cap D$ count.
- **The diagnosis of the original record (§4.7) stands.** WENO5 with TVD-RK3 is not strictly
  monotone, and the pre-registered $0.01\,\delta$ bar is tighter than the scheme can meet.

### 4.5 Check 6: only the mutual-kill diagonal remains

- **Coarse passes:** 0 and 0. The original had 6 nodes in $W_1\cap D$.
- **Fine:** $W_1\cap W_2$ has 3542 nodes and $W_1\cap D$ has 0.
  - All 3542 lie exactly on $|\phi_1|=|\phi_2|$, at $|\phi_1|\in[45.9°,130.6°]$, $R\in[0.81,4.58]$.
  - There $|V^{RA}_1|/\delta$ has a median of 0.072 and a maximum of 0.090.
- **This is D&S Eq. (89),** the four surfaces where the two winning zones touch. It is sign noise on a
  surface where $V^{RA}_1=0$ in the continuum (original §4.2), unchanged.

### 4.6 Checks 9 and 12: unchanged

- **Check 9.** It finds the same four components: two $Rf$-mirror halves of the min-range subregion
  (122,247 nodes each) and the two off-boresight zones (3626 each).
  - Relaxing the $R$ mask gives 3 components, one $Rf$-invariant (261,406 nodes) plus the mirror
    pair.
  - Including $T'_1$ also gives 3 (624,290 plus 9043 ×2).
  - The structure is D&S's. The check's definition is not (original §4.6).
- **Check 12.** The heuristic is beaten from 0 of 2377 starts, as before (original §4.5). Check 13
  covers that gap from the other side.

---

## 5. Decisions for Ethan

1. **Make the pole fields M5's fields of record and Layer 2's input?** *Recommended.*
   - They pass every check the original passed except check 4, and check 4's deviation touches no
     set.
   - They fix checks 3 and 8 and settle the near-face boundary.
   - Files are named `m5_<grid>_T6[_single]_pole_fields.npz` in `m5_out/m5_out_V1_pole/`. Rows are
     staggered, so take $R$ from the file, never from `linspace`.
2. **Check 4 on the fine grid.** It stays scored FAIL. Choose one of:
   - **(a)** Accept it as diagnosed in §4.1. *Recommended:* nothing downstream reads it.
   - **(b)** Localize it. Rerun the first few 0.25-steps of the fine `single` solve and record the
     asymmetry on the tail-chase line after each step. That is about 27 min per 0.25-step on your
     machine, from this run's 1,650 s.
   - **Not** symmetrizing the field after the fact. That would change the method after the result
     was visible.
3. **Checks 5, 6, 9 and 12.** The original decision stands: keep them scored as failures. If any is
   restated for Layer 2, say so in the record.
4. **Amend the parent records,** as InnerFace §7 calls for:
   - **M5 record.** Add a follow-up line to §1 and §3.1: 9 of 14 on the pole grids; checks 3 and 8 now
     pass; check 4 fine fails (this record §4.1).
   - **InnerFace record.** Close the two items in §6's "Not established": check 8 (this record §4.2)
     and the near-face share (§4.3).

*(Status 2026-10-15, at the Layer 1 close-out, on Ethan's go-ahead to finish Layer 1. Record:
`Overview/Layer1/Layer1_CloseOut_2026-10-15.md`.)*
- **1:** adopted.
- **2:** (a) taken; (b) left as an optional open item.
- **3:** stands.
- **4:** done.

---

## 6. Report-only diagnostics (added 2026-10-15, after scoring; not pre-registered)

`layer1/M5/diag/diag_pole_rerun.py` reads only the float32 field files, so it takes about 15 s. Its
log is `m5_out/m5_out_V1_pole/diag_pole_rerun.log`. It reports:

- **check 4:** the asymmetry by row, over $R\ge0.45$, over $\Omega$ and near the zero set; the worst
  node; whether $W_1=W_1\circ Rf$. For both $V^{RA}_1$ and $V_1$, both grids.
- **check 5:** the worst node and whether it is inside $T_{2\to1}$; counts above $0.01\,\delta$ and
  $0.1\,\delta$; sign flips.
- **check 6:** where $W_1\cap W_2$ sits.
- **contested:** composition, $R$ spread, components of the player-1 half, and erosion thickness
  (the same method as `diag_m5_partition.py`).
- **check 9:** topology with the $R$ mask or the target exclusion relaxed (as `diag_m5_fields.py`).
- **check 8:** the six old far-flip states on both pole grids.
- **near face:** the $W_1$ share at $0.45\le R<1$ on all five grids.
- **old vs pole:** the old fine field interpolated in $R$ onto the pole rows; sign disagreements by
  $R$ band, and those more than 2 cells from either zero set.

The old-grid numbers it quotes come from `m5_out/m5_out_V0/`, the original M5 outputs.

---

## 7. Files and reproducing

```
layer1/M5/run_m5_pole.py                      the driver (InnerFace Sec. 9); logs to m5_out/pole_run/
layer1/M5/diag/diag_pole_rerun.py             Sec. 6 diagnostics
layer1/M5/m5_out/m5_out_V1_pole/
    pole_run/01_smoke.log ... 12_final_check13.log, done.txt
    m5_<grid>_T6[_single]_pole_fields.npz     V (float32), tRA, R, phi1, phi2 -- ghost rows included
    m5_<grid>_T*[_single]_pole.json           solve diagnostics, R_nodes
    VRA_ / tRA_<grid>_..._pole.npy            the same float32 values stored as float64 (68 MB fine)
    VRAsnap_ / Vsnap_RA_<grid>_..._pole.npz   snapshot stacks (849 MB fine) and visualization snapshots
    test_m5_T6_pole.json, test_m5_T6_pole_fields.json, converse_m5_T6_pole.json
    diag_pole_rerun.log
layer1/M5/m5_out/m5_out_V0/                   the original R_min = 0.2 M5 outputs
```

From `layer1/M5/`:

```
python run_m5_pole.py                                   # the whole sequence (~23 h here)
python diag/diag_pole_rerun.py                          # Sec. 6 (~15 s); defaults to the two folders above
```

`test_m5.py` and `converse_m5.py` read `m5_out/` directly. To rescore, move the pole outputs back
there, or point `OUT` at `m5_out/m5_out_V1_pole`.
