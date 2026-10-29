# Layer 1 — Test C2 at long range: the heuristic's inversion against Layer 1's laws

**AE 8900 · criteria fixed 2026-10-15, before any long-range run · Ethan Stroup**

This record is written to be read cold.
- **§1–§5 were fixed before the run.** They were written to Ethan's machine before
  `c2_longrange.py` was first executed.
- **Results are in §6,** appended after the run. Nothing in §1–§5 was changed afterward.

**What was seen before writing.** Only results already on record:
- M3's winning-zone edge at $R=6.100$;
- M4's long-range band table ($V=\ell$ on most nodes beyond $R\approx6$);
- the Layer 0 simulator's acceptance table;
- the pole-grid M5 results.

**One harness check was run first.** `converse_m5.py` reproduced Ethan's logged coarse check 13
(`pole_run/12_final_check13.log`) line for line. That run involves no long-range state.

**Plan of record:** `Overview/Layer1/Layer1_Plan.md` §5, test C2, third bullet: *"no long-range
inversion of the angular-advantage result beyond $R\approx8$, which is the §4 criterion proper and
the heuristic's known failure."*

---

## 1. Why this test, and why now

**ProblemStatement §4 gives this as the first reason Layer 1 exists.**
- The Layer 0 simulator flies the pursuit heuristic $\sigma_i=-\operatorname{sign}(\phi_i)$.
- From long range it inverts the paper's angular-advantage result.
- A Layer 2 built the same way would make the same error with no published answer to catch it.

**The check was deferred twice and never run.**
- M4 scored it SKIP: no retained Layer 0 point reaches $R=8$ (M4 §3.5).
- M5's criteria said it "stays with C2" (M5 criteria §4.2).
- It is the last scored item Layer 1 owes before close-out.

---

## 2. What "the inversion" is

**Source.** `heuristic_simulator/two_target_game_demo_SPEC_v2.md` §9 and
`Overview/Layer0/Layer0_CloseOut_2026-09-11.md` §5.3.

**The setup.** Both players fly the heuristic.
- Starts: a $73\times73$ grid of $(\phi_1,\phi_2)\in[-180°,180°]$ at fixed $R_0$.
- Integration: horizon 30, step 0.01.

**What it measured.** Among decisive outcomes with $|\phi_1|\ne|\phi_2|$, the player with the
smaller $|\phi|$ wins:

| $R_0$ | smaller $\lvert\phi\rvert$ wins | mutual kill |
|---|---|---|
| $\le2$ | about 100 % | — |
| 5 | about 87 % | — |
| 8 | about 1 % | 17.7 % (after the $\bar R_0=3+\pi$ correction) |
| 12 | — | 85.3 % |

**What the game says at that range.** This was known before this test.
- $W_1\subseteq\{V_1\le0\}$, and that set ends at $R=6.100$ (M3). So from $R\ge8$ neither player can
  guarantee a kill.
- D&S's winning zones also end inside $\bar R(0)=6.14$.
- So at long range the answer is a **draw**, and there is no decisive outcome for the
  angular-advantage rule to get right or wrong.
- The inversion is the heuristic manufacturing decisive outcomes, with the wrong winner, where
  the game has none.

**The test therefore asks four things:**
1. **Field.** Does Layer 1's partition put every live state at $R\ge8$ in $D$?
2. **Guarantee.** Is a player who flies Layer 1's avoid law from those states never killed,
   whatever the opponent flies, the heuristic and the trader included?
3. **Decision 2's model.** Outside the winning zones Plan §2.3 has both players avoid. In that
   pairing, is nobody killed?
4. **Controls.** Does the same harness register kills when player 1 flies the heuristic
   instead? And does it reproduce the inversion itself when both fly the heuristic?

---

## 3. Settings

**Fields.** The coarse pole grid, $101\times102^2$ at $T=6$, from `m5_out/m5_out_V1_pole/`:
- $V^{RA}_1$ and $V_1$ snapshot stacks every 0.25 (`VRAsnap_101x102_T6[_single]_pole.npz`);
- $t_1^*$ from `tRA_101x102_T6_single_pole.npy`.

**Why the coarse grid.**
- The fine stacks are 849 MB each, over the limit for moving files off Ethan's machine to where
  this runs.
- On the coarse pole grid every M5 simulation check came out as on the fine grid.
  - Check 11 had 0 failures in 10,130 runs.
  - Check 13 had 0 wins against the adversary in 10,000 runs, with 270 informative starts against
    the fine grid's 346.
- Its check 13 was reproduced here exactly before this file was written.

**LR-1** uses the field files of both pole grids (`m5_<grid>_T6[_single]_pole_fields.npz`).

**Starts.**
- $(\phi_1,\phi_2)$ on the spec §9 grid: 73 values each in $[-180°,180°]$, endpoints included.
  That is 5329 starts per range.
- Ranges $R_0=8$ and $R_0=10$, so 10,658 starts.
- $R_0=12$ is not used for LR-2 to LR-4. It is the grid's outer row, where opening states leave on
  the first step (InnerFace §5.5).

**Integration and outcomes.** Exactly M5 criteria §3.3:
- RK4 with $\Delta t=2\times10^{-3}$ and the pole stepper;
- kill events located by bisection; a mutual kill means both within $10^{-6}$;
- exit through $R=12$ scores as "exited";
- horizon $T=6$.

**Player 1's avoid law.** $\sigma_1=+\operatorname{sign}(\partial V_2/\partial\phi_1)$ at the
remaining horizon, with $V_2=V_1\circ S$ and the read capped at the last snapshot. This is
`diag_retreat.py`'s law, unchanged.

**Player 2's laws.** The five of M5 criteria §3.4, unchanged: `test_m5.player2_laws`, with random
bang-bang on seed 12345.
1. reach-avoid adversary;
2. avoid ($V_1$);
3. trade ($t_2^*$);
4. heuristic;
5. random bang-bang.

**Symmetry.** The laws and the start grid are symmetric under the index swap $S$. So whatever
holds for player 1 here holds for player 2 with indices exchanged, and player 2's side is not run
separately.

---

## 4. Checks

| # | Check | Grid | Criterion |
|---|---|---|---|
| LR-1 | Field | 101 and 201 pole | Over $\Omega\cap\{R\ge8\}$: $W_1\cup W_2$ has **0** nodes, and **every** node is in $D$ |
| LR-2 | Avoid guarantee | 101 pole | Player 1 on the avoid law, 10,658 starts × 5 player-2 laws: **0** runs end with player 1 killed (player-2 kill or mutual kill) |
| LR-3 | Decision 2's model at long range | 101 pole | The (avoid, avoid ($V_1$)) pairing from LR-2's runs: **0** kills of either player (no win, no player-2 kill, no mutual kill) |
| LR-4 | Negative control | 101 pole | Player 1 flies the heuristic from the same starts against the same five laws: at least **20** starts end with player 1 killed by some law (check 12's bar) |
| LR-5 | Harness control: the inversion reproduced | none (no field is read) | Both fly the heuristic. Same 73×73 grid at $R_0=2$ and $R_0=8$; horizon 30; no outer exit; same stepper and outcome rule. Among decisive outcomes (win or player-2 kill, not terminal at $t=0$) with $\lvert\phi_1\rvert\ne\lvert\phi_2\rvert$ at the start, the smaller-$\lvert\phi\rvert$ player wins **≥ 80 %** at $R_0=2$ and **≤ 20 %** at $R_0=8$ |

**How the test is scored.**
- **PASS:** LR-1 to LR-5 all pass.
- **FAIL:** LR-1, LR-2 or LR-3 fails. Every failing run is then listed with its start and law.
- **UNINFORMATIVE** (instead of PASS): LR-4 or LR-5 fails. A suite that cannot register a kill, or
  cannot see the inversion, cannot show its absence.

**Why LR-5's bars are wide.** The Layer 0 simulator measured about 100 % and 1 %. This harness
integrates and classifies differently: RK4 at $2\times10^{-3}$ with bisected events, against a
fixed 0.01 step that calls any same-step entry mutual. The bars only require the qualitative
inversion.

---

## 5. Report only (rules fixed now)

- The full outcome tables for LR-2 and LR-4, by range and by player-2 law.
- **Engagement:** the share of LR-2 and LR-4 runs whose range falls below $\bar R(0)=3+\pi$ at some
  point. These are runs that came within weapons range at all.
- **Margin at long range:** $\min V_1$ and $\min V_2$ over $\Omega\cap\{R\ge8\}$, in units of $\delta$,
  on both pole grids.
- **LR-5 outcome fractions** at $R_0=2$, 8 and 12 (12 is fine here, since no field is read and no
  outer exit applies). Mutual-kill fractions are not comparable with the Layer 0 table, because the
  two harnesses classify ties differently.
- **The angular-advantage share inside $W_1$** (fine pole grid): the share of $W_1\cap\Omega$ nodes
  with $|\phi_1|<|\phi_2|$, by $R$ band ($[0.45,1)$, $[1,2)$, $[2,4)$, $[4,6.2)$). This is the short-range
  half of the paper's statement in Layer 1's own terms.

**What this test cannot show.**
- It does not test optimal play at long range. There is no winning zone there, so there is no
  interior play to be optimal about.
- It does not test horizons beyond 6. The value is converged in horizon (M3; M5 check 7), but each
  run stops at $T=6$.

---

## 6. Results

*(Appended 2026-10-15 after the run. Log: `layer1/M5/m5_out/m5_out_V1_pole/c2_longrange.log`,
with numbers in `c2_longrange.json`. Run time 3.2 min.)*

**Test C2 at long range: PASS.** All five checks pass, and both controls work.

| # | Check | Result | Numbers |
|---|---|---|---|
| LR-1 | long range is all $D$ | **PASS** | 353,736 coarse and 2,788,272 fine nodes in $\Omega\cap\{R\ge8\}$; $W_1\cup W_2$: 0 and 0; outside $D$: 0 and 0 |
| LR-2 | avoid guarantee | **PASS** | player 1 killed in 0 of 53,290 runs |
| LR-3 | (avoid, avoid) | **PASS** | 0 kills in 10,658 runs |
| LR-4 | negative control | **PASS** | the heuristic player 1 is killed by some law from 10,350 of 10,658 starts (bar 20) |
| LR-5 | the inversion reproduced | **PASS** | smaller $\lvert\phi\rvert$ wins 100.0 % of 2296 decisive outcomes at $R_0=2$ (bar ≥ 80 %), and 7.5 % of 5184 at $R_0=8$ (bar ≤ 20 %) |

### 6.1 What the runs show

**The margin is physical.** Over $\Omega\cap\{R\ge8\}$, $\min V_1=\min V_2=7.2\,\delta$ on the coarse
grid and $14.3\,\delta$ on the fine. Both are about 0.86 in $V$. The draw at long range holds by many
cells, not by one.

**The avoid law refuses the engagement.** Over LR-2's 53,290 runs, 17,305 end with no kill and
35,985 exit through $R=12$. Range opens, and play never comes back.

| player 2 law | $R_0=8$: none / exit / engaged | $R_0=10$: none / exit / engaged |
|---|---|---|
| reach-avoid adversary | 4 / 5325 / 0.0 % | 0 / 5329 / 0.0 % |
| avoid ($V_1$) | 4 / 5325 / 0.0 % | 0 / 5329 / 0.0 % |
| trade ($t_2^*$) | 2836 / 2493 / 2.4 % | 1428 / 3901 / 0.0 % |
| heuristic | 5329 / 0 / 7.4 % | 4685 / 644 / 0.0 % |
| random bang-bang | 1793 / 3536 / 3.1 % | 1226 / 4103 / 0.0 % |

"Engaged" means the range fell below $\bar R(0)=6.14$ at some point. So LR-2 is a **weak test at
$R_0=10$**: within $T=6$, no pursuer even gets inside maximum range. Its informative part is
$R_0=8$ against the laws that pursue, together with LR-4.

**The heuristic's long-range kills need both players to press.** The negative control flies the
same starts with player 1 on the heuristic:

| player 2 law | $R_0=8$: win / p2-kill / mutual / none | $R_0=10$: win / p2-kill / mutual / none / exit |
|---|---|---|
| reach-avoid adversary | 0 / 0 / 0 / 5329 | 0 / 0 / 0 / 4685 / 644 |
| avoid ($V_1$) | 0 / 0 / 0 / 5329 | 0 / 0 / 0 / 4685 / 644 |
| trade ($t_2^*$) | 41 / 5263 / 21 / 4 | 0 / 4573 / 0 / 536 / 220 |
| heuristic | 2592 / 2592 / 145 / 0 | 2582 / 2582 / 153 / 0 / 12 |
| random bang-bang | 768 / 1311 / 0 / 3250 | 271 / 1481 / 0 / 3281 / 296 |

- **Against the two laws that don't press** (the reach-avoid adversary and the avoider), the
  heuristic player 1 is never killed, and never wins either.
- **Kills happen only when player 2 presses too:** the trader, the heuristic, and sometimes
  random turns.
- **Together with LR-2 and LR-3:** from $R\ge8$, either player can refuse and force a draw. A
  decisive outcome there is something both players chose, not something the game forces.

**The harness reproduces the Layer 0 simulator** (LR-5, report-only fractions):

| $R_0$ | terminal at 0 | P1 | P2 | mutual | draw | smaller $\lvert\phi\rvert$ wins | Layer 0 simulator (spec §9) |
|---|---|---|---|---|---|---|---|
| 1.5 † | 45.3 % | 21.2 % | 21.2 % | 1.4 % | 10.8 % | 100.0 % | 45.3 / 21.2 / 21.2 / 1.4 / 10.8 % |
| 2 | 45.3 % | 21.5 % | 21.5 % | 1.4 % | 10.2 % | 100.0 % | no row; agreement about 100 % at $R_0\le2$ |
| 8 | 0 | 48.6 % | 48.6 % | 2.7 % | 0 | **7.5 %** | 0 / 40.5 / 40.5 / 18.9 / 0 %; agreement about 1 % |
| 12 | 0 | 48.6 % | 48.6 % | 2.8 % | 0 | 48.6 % | 0 / 6.5 / 6.5 / 86.9 / 0 % |

The spec's rows use $\bar R_0=6.14$; with $3+\pi$ its mutual kill is 17.7 % at $R_0=8$ and 85.3 % at
$R_0=12$ (Layer 0 close-out §5.3).

† $R_0=1.5$ was run after the scored run, as a like-for-like comparison with the spec's nearest row.
It is not part of LR-5.

- **Short range:** it matches the Layer 0 simulator's $R_0=1.5$ row exactly.
- **$R_0=8$:** the inversion is there, at 7.5 % against about 1 %.
- **Mutual kill is where the harnesses differ.**
  - This harness locates each entry by bisection and calls a mutual kill only within $10^{-6}$.
  - The Layer 0 simulator calls any two entries inside the same 0.01 step mutual.
  - So most of its long-range "mutual kills" (85 % at $R_0=12$) are near-simultaneous one-sided
    kills. That is a fact about the heuristic's trades being close in time, not about the game.
    *(Report only; §5 said the mutual-kill fractions would not be comparable.)*

**Inside $W_1$ the angular-advantage rule holds where D&S say it should** (fine pole grid, share of
$W_1\cap\Omega$ with $|\phi_1|<|\phi_2|$):

| $R$ band | share | $W_1$ nodes |
|---|---|---|
| $[0.45,1)$ | 99.9 % | 46,314 |
| $[1,2)$ | 98.9 % | 97,472 |
| $[2,4)$ | 97.7 % | 99,844 |
| $[4,6.2)$ | 8.5 % | 8,116 |

- **Below $R=4$** is the min-range subregion, D&S's "governed by angular advantage".
- **From 4 to 6.2** are the off-boresight zones, with $|\phi_1|$ from 46° to 74° and $|\phi_2|\le41°$. They
  are the paper's own exception to the rule.

### 6.2 What this establishes

**ProblemStatement §4's criterion is met.**
- Layer 1 does not invert the angular-advantage result at long range.
- It produces no decisive outcome there at all: every live state at $R\ge8$ is a guaranteed draw
  (LR-1), and a player on the avoid law is never killed (LR-2, LR-3).
- At short range its winning set follows the angular-advantage rule wherever D&S say it applies.
- The heuristic's inversion is reproduced in the same harness (LR-5), and the negative control
  registers it (LR-4). The test can see what it says is absent.

**Limits.**
- It ran on the coarse grid only (§3).
- The horizon is 6.
- LR-2 is uninformative at $R_0=10$, where nothing engages within the horizon.
