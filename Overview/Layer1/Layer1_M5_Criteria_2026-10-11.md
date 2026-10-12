# Layer 1 — M5: pre-registered criteria

**AE 8900 · 2026-10-11 · Ethan Stroup**

This file is written to be read cold. It fixes M5's method, checks and numbers **before any
reach-avoid solve has run**. Nothing below was chosen with an M5 result visible. If a number
is changed later, the change goes in the M5 record with its reason, and this file stays as written.

**Plan of record:** `claude/Layer1_Plan.md` §4 (M5) and §5 (test F), as revised 2026-10-01.
**Inputs carried in:** `claude/Layer1_M4_2026-10-06.md` §6 and the M3 fields in `layer1/m3_out/`.

---

## 1. What M5 computes

One reach-avoid value on the M3 grid pair, $101\times102^2$ and $201\times204^2$, plus a third
grid, $51\times51^2$, for the convergence fit (§4.3). The `sdist` weighting of $\ell$ is used throughout.

$$V^{RA}_1(x,\tau)=\min_{\sigma_1}\max_{\sigma_2}\ \min_{t\in[0,\tau]}\ \max\Big\{\ell_1\big(x(t)\big),\ \max_{s\in[0,t]}\big[-\ell_2\big(x(s)\big)\big]\Big\}$$

Player 1 reaches $T_{1\to2}$ without having entered $T_{2\to1}$ on the way, against every
player-2 behavior. Here $\ell_2=\ell_1\circ S$.

**Partition.** $\Omega$ is the region where play is still live: $R\ge0.45$, $\ell_1>0$ and $\ell_2>0$.

- $W_1=\{V^{RA}_1\le0\}$ and $W_2=W_1\circ S$, which is an axis transpose.
- $D=\{V_1>0\}\cap\{V_2>0\}$, from the single-target fields at the same horizon.
- The contested set is $C=\Omega\setminus(W_1\cup W_2\cup D)$.
- Every volume fraction is a node count over $\Omega$. The terminal sets
  $T'_1$, $T'_2$ and $T_{1\to2}\cap T_{2\to1}$ are reported separately.

---

## 2. The update, derived from Fisac et al. (arXiv:1410.6445)

**The value is Fisac's Eq. (4)** with payoff $l=\ell_1$ and discriminator $g=-\ell_2$. The
constraint set is $K=\{g\le0\}=\{\ell_2\ge0\}$. Player 1 is their player I, the attacker,
who minimizes. Their Eq. (4) ignores any constraint violation after the target is reached, which
is the stopped game: play ends at the first kill.

**Their variational inequality.** Theorem 1, Eq. (17), is written in forward time $t$ with a
terminal condition. In time remaining $\tau$ it reads

$$\max\Big\{\min\big\{-\partial_\tau V+H(x,\nabla V),\ \ell_1-V\big\},\ -\ell_2-V\Big\}=0,\qquad V(x,0)=\max\{\ell_1,-\ell_2\}.$$

Their Algorithm 1 discretizes this in three steps:

1. $V\leftarrow V+\Delta\tau\,\hat H$;
2. $V\leftarrow\min(V,\ell_1)$;
3. $V\leftarrow\max(V,-\ell_2)$.

**What `hj_reachability` 0.7.0 does.** This was read from the installed source on 2026-10-11.
- `backwards_reachable_tube` clamps the numerical Hamiltonian, $\min(0,\hat H)$, at every
  Runge–Kutta stage.
- `static_obstacle(-ell_2)` applies $\max(\cdot,-\ell_2)$ once, after the full TVD-RK3 step.

Per step, then:

$$V\leftarrow\max\big(V+\Delta\tau\,\min(0,\hat H),\,-\ell_2\big)=\max\big(\min(V,\,V+\Delta\tau\hat H),\,-\ell_2\big).$$

The only difference from Algorithm 1 is that step 2 takes the min with the previous $V$
instead of with $\ell_1$.

**The two forms are the same dynamic-programming step.**
1. Fisac's Lemma 2 gives, to first order, $V(x,\tau+\delta)=\max\{g,\ \min\{l,\ W\}\}$. Here $W$
   is the min-max of $V(x(\delta),\tau)$, and $g$, $l$ are evaluated at $x$.
2. The library's step instead gives $\max\{g,\ \min\{V(x,\tau),\ W\}\}$.
3. With time-invariant $l$, $g$ and $f$, the min over $[0,\tau]$ can only fall as $\tau$ grows,
   so $V$ is non-increasing in $\tau$. Write $V(x,\tau)=\max\{g,a\}$ with $a=\min\{l,W'\}$, where
   $W'$ is the same min-max taken one step earlier. Monotonicity gives $W\le W'$. Then

$$\max\{g,\min\{\max\{g,a\},W\}\}=\max\{g,\min\{a,W\}\}=\max\{g,\min\{l,W\}\},$$

using $\min\{\max\{g,a\},W\}=\max\{\min\{g,W\},\min\{a,W\}\}$ and $\min\{g,W\}\le g$.

So the library form is a consistent discretization of the same inequality. Check 1b compares
the two forms numerically on a small grid.

**Further points.**

- **Isaacs condition.** The Hamiltonian is the M1 one, $H=\min_{\sigma_1}\max_{\sigma_2}\nabla V\cdot f$.
  The controls separate into $-|V_1|+|V_2|$, so $\min\max=\max\min$ and Fisac's upper and lower
  values coincide. No information-pattern caveat applies.
- **Runge–Kutta stages.** The obstacle is applied after the full step, not at the intermediate
  stages; the library's own TODO says so. Algorithm 1 also applies steps 2 and 3 after the full
  integral of step 1, so the placement matches the reference.
- **Boundary convention.** $\{V^{RA}_1\le0\}$ is closed, and $K=\{\ell_2\ge0\}$ allows the path
  to touch $\partial T_{2\to1}$. That differs from "avoid $\bar T_{2\to1}$" only on a measure-zero
  set. No grid set changes, and the simulations classify exact ties themselves (§3.3).

---

## 3. Settings

### 3.1 Tolerance

$\delta$ is one cell's value change, `ell.value_scale(grid)`: 0.118 at $101\times102^2$ and 0.059
at $201\times204^2$, the same values as M4. At $61\times62^2$ and $51\times51^2$ it is whatever
`value_scale` returns, which is recorded in the log.

### 3.2 Horizon

- **Coarse.** Solve $101\times102^2$ to $\tau=10$, measuring motion every 0.25.
- **Choosing $T_{RA}$.** It is the smallest integer $\tau\ge6$ such that every 0.25-step from
  there to $\tau=10$ moves less than 0.5 % of $\{V^{RA}_1=0\}$.
- **Fine.** Solve $201\times204^2$ to $T_{RA}$.
- **$D$.** Uses $V_1$ at $T_{RA}$. If $T_{RA}>6$ and the fine single-target solve is not extended,
  $D$ on the fine grid uses M3's $\tau=6$ field. The size of that effect is then measured on the
  coarse grid and reported.
- **Snapshots.** $V^{RA}_1(\cdot,\tau)$ is saved every 0.25 for the remaining-horizon policy.

### 3.3 Simulations

- **Integration.** RK4 with $\Delta t=2\times10^{-3}$. Controls are frozen within a step, as in
  `hji.forward_sim`.
- **Player 1's law.** $\sigma_1=-\operatorname{sign}(\partial V^{RA}_1/\partial\phi_1)$, read at
  the remaining horizon from the nearest snapshot. This is `hji.make_policy`'s rule, vectorized,
  and asserted to give the same controls as `make_policy` on a sample of states before use.
- **Kill events.** First entry into $T_{1\to2}$ is $\ell_1\le0$; first entry into $T_{2\to1}$ is
  $\ell_2\le0$. Each is located within its step by bisection to $10^{-9}$ in time.
- **Outcome rule.** This is the 2026-10-11 decision.
  - Kill times within $10^{-6}$ of each other: **mutual kill**, never a win.
  - Player 1 first by more than that: **win alone**.
  - Player 2 first: **player-2 kill**.
  - No entry by $T_{RA}$: **no kill**.
  - Leaving $0.2<R<12$: **exited**.
- **What counts as a failure.** In checks 3, 11 and 12, everything except "win alone" is a failure.

### 3.4 Player-2 laws for checks 11 and 12

1. **Reach-avoid adversary:** $+\operatorname{sign}(\partial V^{RA}_1/\partial\phi_2)$ at the remaining horizon.
2. **Avoid:** $+\operatorname{sign}(\partial V_1/\partial\phi_2)$ at the remaining horizon, from
   M3's snapshots. Remaining horizons beyond the last snapshot read the last one.
3. **Trade.** Player 2 heads toward $T_{2\to1}$ as fast as he can, $\sigma_2=-\operatorname{sign}(\partial t_2^*/\partial\phi_2)$.
   - On the level set where $t_2^*$ equals some value $c$, $V_2(x,c)=0$. So $\nabla t_2^*$ has the
     direction of $\nabla V_2(\cdot,c)$.
   - The law is therefore $-\operatorname{sign}(\partial V_2/\partial\phi_2)$, read at the first
     snapshot $\tau_k\ge t_2^*(x)$. The last snapshot is used where $t_2^*=\infty$.
   - $V_2=V_1\circ S$ and $t_2^*=t_1^*\circ S$, both from M3.
4. **Heuristic:** $-\operatorname{sign}(\phi_2)$.
5. **Random bang-bang:** $\sigma_2=\pm1$ with equal probability, redrawn every 0.25. The seed is fixed per run.

---

## 4. Checks

### 4.1 Pass/fail

| # | Check | Grid | Criterion |
|---|---|---|---|
| 1 | Pre-flight: $\ell_2$ written out independently vs $\ell_1\circ S$ | all | $\max\lvert\cdot\rvert\le10^{-6}\,\delta$ |
| 1b | Library form vs Algorithm 1 form (§2) | $61\times62^2$ | 0 sign disagreements more than 2 cells from either zero set |
| 2 | Smoke test, both controls frozen at $(0,0)$ and at $(+1,-1)$. Exact truth from forward integration from every node | $61\times62^2$ | 0 sign disagreements more than 2 cells from the exact zero set |
| 3 | Smoke test, $\sigma_2\equiv0$. Rollouts of player 1's grid law from 500 nodes with $V^{RA}_1\le-\delta$, in $\Omega$ | $61\times62^2$ | every rollout wins alone |
| 4 | Reflection | 101, 201 | $\max\lvert V^{RA}_1-V^{RA}_1\circ Rf\rvert<0.01\,\delta$ |
| 5 | Ordering (exact in the continuum, since $\max\{a,b\}\ge a$) | 101, 201 | $V^{RA}_1\ge V_1-0.01\,\delta$ on every masked node, and $W_1\subseteq\{V_1\le0\}$ node for node |
| 6 | Disjointness | 101, 201 | $W_1\cap W_2$ and $W_1\cap D$: 0 nodes in $\Omega$ |
| 7 | Horizon | 101, 201 | final 0.25-step moves $<0.5\,\%$ of $\{V^{RA}_1=0\}$ |
| 8 | Grid convergence of $\partial W_1$, using the M3 metric (`grid_study.py`) | 101 vs 201 | displacement $\le0.5$ coarse cells, and 0 disagreements beyond 3 cells |
| 9 | Test F topology, see below | 201 | 3 components above 0.01 % of $\Omega$: one $Rf$-invariant, two $Rf$-mirrors |
| 10 | Test F, Table 2 points (§5) | 201 | off-$\partial T_{1\to2}$ set: at most **2** misses of $\lvert V^{RA}_1\rvert\le\delta$; on-$\partial T_{1\to2}$ set: at most **1** miss of $V^{RA}_1\ge-\delta$. Every miss listed |
| 11 | Test F, guarantee, see below | 201 | **0** failures over all starts and all five laws |
| 12 | Negative control: player 1 flies $-\operatorname{sign}(\phi_1)$ from the same starts | 201 | at least **20** starts fail, where a start fails if any of the five laws beats it |

**Check 9.**
- **What's counted.** Components of $W_1\cap\Omega$, face-connected and periodic in both angles.
- **Why three.** D&S's two max-range zones lie on $T_{1\to2}$ itself (M4 §4.2), so they are not
  expected in $\Omega$. The three expected are D&S's min-range subregion and the two off-boresight
  zones above the $\beta\delta$ intersection lines (Fig. 14).
- **When it's "unresolved" rather than a fail.** If the count comes out at 2 or 1 because
  components merge, and every merging node is within 2 cells of the target-intersection lines
  through $\beta$ or $\delta$, the check is scored **unresolved at this grid**. D&S's zones touch
  only at those points.
- **Other reports.** The count is also reported with 26-connectivity and on the coarse grid.

**Check 11.**
- **Starts.** 2000 nodes drawn uniformly (seed 0) from $\{V^{RA}_1\le-\delta\}\cap\Omega$, topped
  up so every component from check 9 has at least 200 starts.
- **Not scored.** Starts in the band $-\delta<V^{RA}_1\le0$.
- **The coarse grid** is run the same way and reported, not scored.

**Check 12's bar.** It is set at 20 failed starts (1 %), as the minimum that shows the guarantee
test can catch a wrong player-1 law. The heuristic's actual failure rate is reported separately,
as a statement about the heuristic.

### 4.2 Report only (the rules are fixed now)

- **Volume fractions** over $\Omega$ of $W_1$, $W_2$, $D$ and $C$, plus the terminal sets, on all
  three grids.
- **Old vs new.**
  - Compare $W_1$ with M3's $\{V_1\le0\}\setminus\{V_2\le0\}$ (the old 7.17 %), as both set
    differences.
  - Compare $C$ with the 4.53 % $\{V_1\le0\}\cap\{V_2\le0\}$.
- **Where $C$ is.** The share of contested nodes within one coarse cell of $|\phi_1|=|\phi_2|$.
- **C2 in the contested set**, labeled as assumption-dependent.
  - 1000 contested starts, with both players racing.
  - Player 1 uses the $t_1^*$ analogue of law 3.
  - Player 2 uses law 3.
  - Report the outcome distribution.
- **Long range.** The C2 inversion check at $R\ge8$ stays with C2. $W_1$ has no states there,
  because $W_1\subseteq\{V_1\le0\}$ and that set ends at $R=6.100$.

### 4.3 Thin or fat contested set

Let $v(h)$ be the contested fraction of $\Omega$ on grids 51, 101 and 201, with $h$ halving each
time.

- **Fit.** Solve $v(h)=v_0+c\,h^p$ exactly through the three points.
- **Fit valid:** $0.25\le p\le2$ and $v$ monotone in $h$.
  - $v_0/v_{201}\le0.2$: **thin**.
  - $v_0/v_{201}\ge0.6$: **fat**.
  - Otherwise: **inconclusive**.
- **Fit not valid** (the 51 grid is pre-asymptotic): fall back to $r=v_{201}/v_{101}$.
  - $r\le0.6$: thin.
  - $r\ge0.85$: fat.
  - Otherwise: inconclusive.
- **Both rules** are reported whichever one decides.

---

## 5. Table 2 points for check 10, tagged from the paper only

**Candidates.** Every Table 2 point named in D&S Sec. 5 (the modified-target game) or drawn in
Fig. 13 (barriers with the modified target set) or Fig. 14 (two-target solution). Read from the
paper, p. 154–159, on 2026-10-11:

> $\alpha,\beta,\gamma,\delta,\varepsilon,\zeta_1,\eta,\rho_1,\tau$, $A_1,B_1,E_1,F_1,H_1,I_1,K_1,P_1,\tilde Q_1,S_1,U_1,V_1,\tilde W_1,a_1,b_1,h_1,q_1$

**Excluded, by rule.**

| reason | points |
|---|---|
| below the $R\ge0.45$ mask | $V_1$ (0.412), $\tilde W_1$ (0.148), $q_1$ (0.381) |
| row flagged inconsistent as printed (`layer0/table3.py`: $I_1P_1$) | $I_1$, $P_1$ |
| on $\partial T_{1\to2}\cap\partial T_{2\to1}$, where $V^{RA}_1=0$ exactly by construction | $\beta,\gamma,\delta,\eta$ |

**Scored.** "On $\partial T_{1\to2}$" means $|\ell_1|\le2.5\times10^{-3}$, the `validate_table2.py`
tolerance. Values are computed with `sdist`.

| set | points | $n$ | allowed misses |
|---|---|---|---|
| off $\partial T_{1\to2}$ (two-sided, $\lvert V^{RA}_1\rvert\le\delta$) | $\alpha,\varepsilon,\zeta_1,\rho_1,\tau$; $E_1,F_1,H_1,S_1,U_1,a_1,b_1$ | 12 | 2 |
| on $\partial T_{1\to2}$, outside $T_{2\to1}$ (one-sided, $V^{RA}_1\ge-\delta$) | $A_1,B_1,K_1,\tilde Q_1,h_1$ | 5 | 1 |

**Why the second set is one-sided.** On $\partial T_{1\to2}$ outside $T_{2\to1}$, the initial value
already gives $V^{RA}_1\le\max(\ell_1,-\ell_2)=0$. So $|V^{RA}_1|\le\delta$ can only fail from below.

**What check 10 actually tests.** The first five off-target points are the ones the corrected
construction creates: $\alpha,\varepsilon,\rho_1$ are where Sec. 5's new barriers meet the original
barrier, and $\zeta_1,\tau$ appear only in Fig. 13. The other seven are original barrier points that
D&S keep on the corrected boundary.

---

## 6. Files

```
layer1/reach_avoid.py   the solve: obstacle setup, march with snapshots, partition
layer1/smoke_m5.py      checks 1, 1b, 2, 3 at 61x62^2
layer1/sim_m5.py        vectorized rollouts, the five player-2 laws, event location
layer1/test_m5.py       checks 4-12 and the report-only quantities
layer1/converse_m5.py   check 13 (addendum, Sec. 7)
layer1/m5_out/          V_RA fields, snapshots, json diagnostics, logs
```

---

## 7. Addendum 2026-10-12: check 13, the converse guarantee

This was added after checks 1–12 were scored, and fixed **before check 13 ran**. Sections 1–6
are unchanged.

**Why it was added.** Check 12 found that inside $W_1$ the old heuristic plays as well as the
reach-avoid law (M5 record §4.5). So check 11 shows $W_1$ is not too big, but nothing yet shows it
is not too small. This check tests the other side of the boundary.

**The claim.** Where $V^{RA}_1>0$, reach-avoid theory says player 2 has a feedback strategy that
stops player 1 from winning alone, whatever player 1 does. That strategy is
$+\operatorname{sign}(\partial V^{RA}_1/\partial\phi_2)$, read at the remaining horizon (§3.4,
law 1).

**Starts.** Fine grid, nodes in $\Omega$ with all three of:
- $V_1\le-\delta$, so player 1 can force a kill against an avoiding player 2, by a margin of a cell;
- $V_2>0$, so player 2 cannot do the same;
- $V^{RA}_1\ge+\delta$, so $W_1$ denies player 1 by a margin of a cell.

These are the states M3's old "win-alone" set claimed for player 1 and $W_1$ does not: the
player-1 half of the contested set, one cell in from its edges. 2000 are drawn uniformly
(seed 0), or all of them if there are fewer.

**Player 1 flies each of five laws:**
1. the reach-avoid law, $-\operatorname{sign}(\partial V^{RA}_1/\partial\phi_1)$ at the remaining horizon;
2. the single-target law, $-\operatorname{sign}(\partial V_1/\partial\phi_1)$ at the remaining
   horizon from M3's snapshots. This is the law the old claim rests on;
3. the time-optimal law, $-\operatorname{sign}(\partial V_1/\partial\phi_1)$ read at the first
   snapshot $\tau_k\ge t_1^*(x)$;
4. the heuristic, $-\operatorname{sign}(\phi_1)$;
5. random bang-bang, with a fixed seed.

**Player 2.** Each player-1 law is run against all five laws of §3.4. Only law 1, the
reach-avoid adversary, is scored.

**Settings.** Integration, event location, the outcome rule and the horizon $T_{RA}=6$ are
exactly as in §3.3.

**Scoring.**

| result | condition |
|---|---|
| **PASS** | against the reach-avoid adversary, **0** runs end with player 1 winning alone, over all starts and all five player-1 laws |
| **FAIL** | any such run |
| **UNINFORMATIVE** (instead of PASS) | player 1's single-target law wins alone from fewer than **20** starts against the avoiding player 2 (§3.4, law 2), meaning the starts are not winnable even against a weak opponent |

Every run that is not a win alone (player-2 kill, mutual kill, no kill, exit) counts as player 2
stopping the win. Each kind is reported separately.

**Report only.**
- the full outcome table, all five player-1 laws against all five player-2 laws;
- the coarse grid, run the same way;
- the pool size on each grid.

**What each side controls.** Check 11 is this test's control: from inside $W_1$ the same adversary
lost every run. The informativeness condition is the other control: these starts must be
winnable when player 2 does not use the reach-avoid strategy.
