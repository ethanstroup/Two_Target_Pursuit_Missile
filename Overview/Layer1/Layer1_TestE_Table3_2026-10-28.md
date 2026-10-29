# Layer 1 — Test E against D&S Table 3

**AE 8900 · criteria fixed 2026-10-28, before any comparison was computed · Ethan Stroup**

This record is written to be read cold.
- **§1–§5 were fixed before the run.** They were written to Ethan's machine before
  `test_e_table3.py` first read a value of $V$.
- **Results are in §6,** appended after the run. Nothing in §1–§5 was changed afterward.

**What was seen before writing.** No value of $V$ at any Table 3 point, or along any line, was
computed. Only these were looked at:
- the Table 3 transcription (`layer0/singular_lines/table3.py`) and where each endpoint sits relative
  to $\partial T_{1\to2}$, from $\ell_1$ alone;
- Layer 0's construction of the commuting line $S_1U_1$ (`commuting_s1u1.py`);
- results already on record: M4's test E fractions and its §4.2–4.3 findings.

**Plan of record:** `Overview/Layer1/Layer1_Plan.md` §5, test E. The comparison with Table 3 is
M4's open item 1 (`Overview/Layer1/Layer1_M4_2026-10-06.md` §5) and the close-out's open item 1
(`Overview/Layer1/Layer1_CloseOut_2026-10-15.md` §6).

---

## 1. What is tested, and why this way

**Which game.** Table 3 is D&S's list of singular lines of the **single-target** game. Its points are
the subscript-1 points of Figs. 8–12, and none of the modified-target points ($\alpha$, $\varepsilon$,
$\rho_1$, $\zeta_1$, $\tau$) appear in it. So the test uses the single-target value. It is written $V$ here,
as in M3 and M4 (M5 calls it $V_1$), and it is not $V^{RA}_1$.

**Which field.** $V$ on the fine pole grid, $201\times204^2$ at $\tau=6$, which is of record
(`m5_201x204_T6_single_pole_fields.npz`). The horizon is converged (M3; M5 check 7).

**What a singular line is, in terms of $V$.** On the barrier the costate is $\lambda=\nabla V$,
and every scored kind of Table 3 line is a place where one player's control is singular or
switches:

| kind | player | what happens on the line | so on the line |
|---|---|---|---|
| universal $(-1,0)$ | evader | $\sigma_2=0$, so $\lambda_2\equiv0$ | $V_2=0$ |
| universal $(0,\pm1)$, commuting $(0,-1)$ | pursuer | $\sigma_1=0$, so $\lambda_1\equiv0$ | $V_1=0$ |
| dispersal, semidispersal | evader | two families with $\sigma_2=-1$ and $+1$ meet | $V_2$ changes sign across it |
| switch | the player whose control changes | that player's $\lambda_i$ crosses zero | $V_i$ changes sign across it |

Here $V_1=\partial V/\partial\phi_1$ and $V_2=\partial V/\partial\phi_2$, the project's usual
notation for the components of $\nabla V$.

So **every scored line lies on the barrier $\{V=0\}$ and on $Z_p$**, the set where the player's
gradient component $V_p$ changes sign ($p=1$ pursuer, $p=2$ evader). That is where the player's
bang-bang law from $\nabla V$ is undefined.

**Not scored, by kind.**
- **Equivocal lines** do not reduce to a sign change of one component.
- **Switch trajectories** are trajectories, not surfaces where a component vanishes.

Both are reported only, and all four equivocal rows lie below the mask anyway.

**Lines are mostly known only by their endpoints.**
- $S_1U_1$ is constructed exactly in Layer 0, and it is scored along its length (§2).
- $e_1c_1O$ and the $d_1$ universal line are constructed too. But they lie on the max-range lens,
  within a fraction of a cell of the target boundary. M4 §4.2 found that structure below grid
  resolution, and every one of their endpoints is on $\partial T_{1\to2}$. They are not scored.

---

## 2. What is scored

**Points.** An endpoint $P$ of a Table 3 row is scored for player $p$ if all three hold:
- $R(P)\ge0.45$. Points below the mask are out of scope (Ethan, 2026-10-07).
- $\ell_1(P)\ge2\delta$, two cells off $\partial T_{1\to2}$. On the boundary, $\ell$'s own kinks and
  the target surface would decide the result.
- At least one row of player $p$ ending at $P$ is of a scored kind and is not one of the four rows
  `table3.py` notes as contradicted by Layer 0 or inconsistent as printed: $f_1c_1$, $c_1O_1$,
  $M_1n_1$, $I_1P_1$. The other notes don't disqualify a row: $S_1U_1$'s only records its
  construction, and $k_1^2k_1$'s a missing Table 2 entry.

That gives 9 (point, player) pairs at 8 points:

| point | $(R,\ \phi_1,\ \phi_2)$ | $\ell_1/\delta$ | player | its scored rows |
|---|---|---|---|---|
| $E_1$ | $(2.233,\ 85.5°,\ 129.7°)$ | 11.8 | evader | $a_1E_1$ universal; $E_1b_1$ semidispersal |
| $b_1$ | $(2.440,\ 79.6°,\ 123.4°)$ | 10.1 | evader | $b_1G_1$ dispersal; $E_1b_1$ semidispersal |
| $G_1$ | $(3.437,\ 74.5°,\ 47.2°)$ | 8.6 | evader | $b_1G_1$ dispersal; $G_1D_1$ semidispersal |
| $D_1$ | $(3.724,\ 83.9°,\ 23.7°)$ | 11.3 | evader | $J_1D_1$ universal; $G_1D_1$ semidispersal |
| $C_1$ | $(4.300,\ 113.9°,\ -25.3°)$ | 20.1 | evader | $C_1H_1$, $C_1B_1$ dispersal |
| $H_1$ | $(0.550,\ 128.5°,\ -143.8°)$ | 24.4 | evader | $C_1H_1$ dispersal |
| $H_1$ | the same | 24.4 | pursuer | $H_1u_1$ switch |
| $I_1$ | $(0.550,\ -36.2°,\ 51.3°)$ | 3.1 | evader | $u_1I_1$ switch |
| $U_1$ | $(1.721,\ 91.1°,\ 135.0°)$ | 13.5 | pursuer | $S_1U_1$ commuting |

**Excluded by rule:**

| reason | points |
|---|---|
| within 2 cells of $\partial T_{1\to2}$ | $a_1$ ($1.36\,\delta$), $S_1$ ($0.65\,\delta$) |
| on $\partial T_{1\to2}$ | $J_1$, $\tilde Q_1$, $m_1$, $Z_1$, $A_1$, $d_1$, $e_1$, $f_1$, $O_1$, $B_1$ |
| inside $T_{1\to2}$ as printed (`table3.py` point note) | $c_1$ |
| only on an excluded row ($I_1P_1$) | $P_1$ |
| below $R=0.45$ | every $k_1$ point, $u_1$, $g_1$, $M_1$, $n_1$, $w_1$, $\tilde W_1$ |

**The line $S_1U_1$.**
- **The curve.** Layer 0 flies the forward $(0,-1)$ arc from the stagnation point at
  $\phi_1(S_1)=47.24°$ until its closest approach to Table 2's $U_1$: $t=0.727$, a miss of
  $3.6\times10^{-4}$.
- **The samples.** 41 samples, equally spaced in $t$.
- **Which are scored.** Those with $\ell_1\ge2\delta$, which is 36 of the 41. The line is about 25
  fine cells long.

---

## 3. Settings

- **$\delta$** is one cell's value change, 0.05985 on the fine grid.
- **The barrier** is $B=\{|V|\le\delta\}$.
- **The gradient component $V_p$** is the central difference of $V$ in $\phi_p$, periodic.
- **$Z_p$, as a node set.** A node is in $Z_p$ if either:
  - $V_p$ changes sign to any of its six face neighbors (zero counts as its own sign); or
  - the two one-sided differences of $V$ along $\phi_p$ have opposite signs, or one is zero.
- **A hit.** Within Chebyshev distance 2 of the point's nearest node, in index units (angles
  periodic, $R$ clipped), there is a node of $Z_p\cap B$.
- **The nearest node.** Pole rows sit at $R_i=(i+\tfrac12)\Delta R$. The angle index is
  $\operatorname{round}((\phi+\pi)/\Delta\phi)\bmod n_\phi$.
- **The null $p_0^{(p)}$.** Over barrier nodes with $\ell_1\ge2\delta$ and $0.45\le R\le4.5$, the
  fraction that are hits by the same rule. This is how often a random barrier point near the scored
  ones lands within 2 cells of $Z_p\cap B$ by chance.

---

## 4. Checks

| # | check | criterion |
|---|---|---|
| T3-1 | **level:** the 8 scored points lie on the barrier | $\lvert V\rvert\le\delta$ at each; at most **1** miss of 8 |
| T3-2 | **locus:** the 9 pairs lie on their player's $Z_p$ | at least **7** hits of 9, **and** $P(\text{hits}\ge\text{observed})<0.01$ under the null (independent hits, each with probability $p_0^{(p)}$ for its player) |
| T3-3 | **the line $S_1U_1$** | of its 36 scored samples, at least **80 %** have $\lvert V\rvert\le\delta$, and at least **80 %** are hits on $Z_1$ |

**Informativeness.** T3-2 and T3-3 count only if $p_0^{(p)}\le0.5$ for every player they use.
Otherwise they are scored **UNINFORMATIVE**: if half the barrier is near $Z_p$, landing near it shows
nothing.

**The test as a whole.**
- **PASS:** T3-1, T3-2 and T3-3 all pass.
- **FAIL:** every miss is listed with its $V$ value and its distance to $Z_p\cap B$ in cells.

---

## 5. Report only (rules fixed now)

- **The coarse grid** ($101\times102^2$, $\delta=0.1194$): the same three checks, with the
  $2\delta$ threshold at the coarse $\delta$.
- **Every Table 3 row:** whether it is scored, or why it is excluded; $V$ at both endpoints; and
  hit or miss for both players.
- **M4's own detector:** the excess locus. That is the WENO5 one-sided sign change along any axis,
  for $V$ minus the same for $\ell$. For each scored point, whether a node of it lies
  within 2 cells.
- **Table 2 points this test places:** every point `validate_table2.py` lists as unplaced that
  passes both T3-1 and T3-2.

**What this test cannot show.**
- the interiors of lines known only by their endpoints;
- the max-range lens lines;
- structure below $R=0.45$;
- equivocal lines and switch trajectories;
- whether D&S's strategy *labels* are right. A hit says the right player's control is singular or
  switches there, not which way.

---

## 6. Results

*(Appended 2026-10-28 after the run.)*
- Log: `layer1/M4/m4_out/test_e_table3.log`. Numbers: `test_e_table3.json` beside the pole fields.
- Run time: 24 s. A dry run on a stand-in field ($V:=\ell$) checked the mechanics first; it read no
  value of $V$.

**Test E against Table 3: FAIL, by one hit.** The level check and the line check pass. The locus
check reaches 6 of 9 against a bar of 7, though that is far above chance.

| # | check | result | numbers |
|---|---|---|---|
| T3-1 | level | **PASS** | 7 of 8 points within $\delta$ of the barrier; $I_1$ misses at $V=+2.73\,\delta$ (allowed 1) |
| T3-2 | locus | **FAIL** | 6 of 9 pairs hit (bar 7). The null hit rate is $p_0=0.028$ (pursuer) and $0.153$ (evader), so $P(\ge6)=1.6\times10^{-4}$ (bar $10^{-2}$). Informative |
| T3-3 | $S_1U_1$ | **PASS** | all 36 scored samples within $\delta$ of the barrier ($V$ from $-0.005$ to $+0.033$); 30 of 36 (83 %) on $Z_1$ (bar 80 % each) |

### 6.1 The nine pairs

| point | player | $V/\delta$ | hit | cells to $Z_p\cap B$ |
|---|---|---|---|---|
| $H_1$ | pursuer | $+0.19$ | yes | 1 |
| $H_1$ | evader | $+0.19$ | yes | 0 |
| $C_1$ | evader | $+0.59$ | yes | 0 |
| $E_1$ | evader | $+0.38$ | yes | 1 |
| $b_1$ | evader | $+0.27$ | yes | 1 |
| $G_1$ | evader | $+0.25$ | yes | 1 |
| $D_1$ | evader | $+0.44$ | **no** | 4 |
| $U_1$ | pursuer | $+0.56$ | **no** | 6 |
| $I_1$ | evader | $+2.73$ | **no** | 4 |

**The coarse grid (report only) shows the same pattern.**
- **Level:** 0 misses. $I_1$ is not scored there, since it sits only $1.5$ coarse $\delta$ off the
  target.
- **Locus:** 6 of 8 hit, with $P=2.5\times10^{-3}$. The same two points miss: $D_1$ by 3 coarse
  cells and $U_1$ by 5.
- **$S_1U_1$:** 100 % on the barrier and 73 % on $Z_1$.

So the misses are not grid noise; they recur at both resolutions.

### 6.2 Where the misses are (report only, after scoring)

*(Script `layer1/M4/diag/diag_table3_misses.py`; log `layer1/M4/m4_out/diag_table3_misses.log`.)*

**$S_1U_1$ and $U_1$: the grid's commuting line stops short of $U_1$.**
- **Where it follows the line.** From $\phi_1\approx52°$ to $85°$, all 30 samples are on the
  pursuer's switch locus: 23 at 0 cells, 6 at 1 cell and 1 at 2 cells. $V$ stays between
  $-0.08\,\delta$ and $-0.02\,\delta$ there.
- **Where it leaves.** Over the last six samples, $\phi_1$ from $86°$ to $91°$, the line leaves the
  locus: 3, 3, 4, 4, 5, then 6 cells. $V$ rises from $0$ to $+0.55\,\delta$.
- **The offset at $U_1$.** The nearest locus node is $(-1,-6,0)$ cells away: $-0.06$ in $R$ and
  $-10.6°$ in $\phi_1$.
- **A possible connection.** M4 §4.3 found that Layer 0's $\lambda_1$ switch locus turns from a
  crossing into a touch of this line between $\phi_1=86°$ and $92°$. That is the same stretch where
  the grid's locus peels away. This is an observation, not a tested link.

**$D_1$.** The nearest evader-locus node is $(-4,-3,3)$ cells away: $-0.24$ in $R$, $-5.3°$ and
$+5.3°$. $D_1$ is the junction of the universal line $J_1D_1$ and the semidispersal line $G_1D_1$.

**$I_1$.** It is off the barrier by $2.7\,\delta$, and the nearest evader-locus node is $(3,-4,1)$
cells away. Its scored row $u_1I_1$ runs to $u_1$ at $R=0.244$, below the mask.

**Hit radius.** The scored radius is 2; these are for reading only.

| radius | hits | null (pursuer / evader) | $P(\ge\text{hits})$ |
|---|---|---|---|
| 1 | 6 of 9 | 0.017 / 0.098 | $1.2\times10^{-5}$ |
| 2 | 6 of 9 | 0.028 / 0.153 | $1.6\times10^{-4}$ |
| 3 | 6 of 9 | 0.052 / 0.208 | $1.1\times10^{-3}$ |
| 4 | 8 of 9 | 0.083 / 0.263 | $2.6\times10^{-5}$ |

The six hits are tight: every one is within 1 cell. The three misses sit 4 to 6 cells out, not at
the edge of the radius.

### 6.3 Report-only items from §5

- **Every row.** The full per-row table, with $V$ at both endpoints, is in the log.
- **M4's detector.** Its excess locus (the WENO5 sign change for $V$, minus the same for $\ell$)
  covers 0.57 % of nodes at $R\ge0.45$. Seven of the 8 scored points lie within 2 cells of it; $U_1$
  does not.
- **Table 2 points placed.** Five of `validate_table2.py`'s 32 unplaced points now pass both level
  and locus: $b_1$, $C_1$, $E_1$, $G_1$ and $H_1$.
  - $U_1$ (with $S_1$) was already placed in Layer 0 by constructing $S_1U_1$ (M4 §4.3). Here the
    grid's version of that line ends about $10°$ short of it.

### 6.4 What this establishes

**Established.**
- **The grid's single-target value carries D&S's singular structure.** Six of nine scored endpoints
  sit within 1 cell of the right player's switch locus on the barrier, against a chance rate of 3 %
  to 15 %.
- **The commuting line is there.** Five-sixths of $S_1U_1$ lies on the barrier and on the pursuer's
  locus, to 0–1 cells.
- **Five more Table 2 points are placed:** $b_1$, $C_1$, $E_1$, $G_1$, $H_1$.

**Not established.**
- **$U_1$'s end of the commuting line.** The grid's line ends about $10°$ of $\phi_1$ before Table
  2's $U_1$.
- **$D_1$ and $I_1$.** Each is 4 cells from its locus, and $I_1$ is off the barrier. Which side is
  off — the grid, or the printed coordinates — is not decided here.
- **Everything §5 says the test cannot show:** interiors of endpoint-only lines, the max-range
  lens, below-mask structure, equivocal lines, and strategy labels.

**Score.** FAIL as pre-registered, and it stays so.
