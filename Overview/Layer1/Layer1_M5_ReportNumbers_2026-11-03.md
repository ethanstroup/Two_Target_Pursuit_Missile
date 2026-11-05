# Layer 1 — M5 numbers for the report, recomputed on the pole grids

**AE 8900 · 2026-11-03 · Ethan Stroup**
Parent records: `Overview/Layer1/Layer1_M5_2026-10-11.md` (the original M5, on the $R_{\min}=0.2$
grids) and `Overview/Layer1/Layer1_M5_PoleRerun_2026-10-15.md` (the rerun on the pole grids, of
record).

This record is written to be read cold.
- **Why it exists.** A few numbers in the final report's M5 section were measured only on the
  $R_{\min}=0.2$ grids: where the sets sit, the size of the contested set's player-1 half, and the
  retreat runs. They were recomputed on the pole fields of record so that the report quotes one
  field throughout.
- **Status.** Report only. Nothing here was pre-registered, and no check's score changes. The laws,
  seeds, start pools and sample sizes are the originals', so the numbers compare one for one.
- **Code:** `layer1/M5/diag/diag_pole_report.py`. It replaces `diag_m5_fields.py`,
  `diag_m5_partition.py`, `diag_negctl.py` and `diag_retreat.py` for the pole fields.
- **Logs:** `layer1/M5/m5_out/m5_out_V1_pole/diag_pole_report_201x204.log` (all three parts) and
  `…_101x102.log` (all three parts). Like every solver output, they are not tracked by git; §4
  regenerates them.

---

## 1. Where the sets sit (part `extents`)

Domain $\Omega=\{R\ge0.45,\ \ell_1>0,\ \ell_2>0\}$, fields at $\tau=6$.

**$W_1$ outside the target sets.**

| | $101\times102^2$ | $201\times204^2$ |
|---|---|---|
| components outside the target sets, no $R$ mask (check 9) | 3 | 3 |
| the same, with the $R\ge0.45$ mask | 4 | 4 |
| min-range region, share of $W_1\cap\Omega$ | 97.1 % | 97.1 % |
| off-boresight zones, $R$ | 4.84 to 6.03 | **4.70 to 6.07** |
| off-boresight zones, $\lvert\phi_1\rvert$ | $46°$ to $71°$ | **$46°$ to $74°$** |
| off-boresight zones, $\lvert\phi_2\rvert$ | $\le35°$ | **$\le41°$** |

- Without the mask the min-range region is one $Rf$-invariant component, so $W_1$ has D&S's three
  subregions outside the target sets. The mask cuts it at $R=0.45$ into two $Rf$-mirror halves.
- The two off-boresight zones are $Rf$ mirrors of each other, 3,626 nodes each on the fine grid.

**The contested set $C$.**

| | $101\times102^2$ | $201\times204^2$ |
|---|---|---|
| $C$, share of $\Omega$ | 1.157 % | **1.060 %** |
| both players can force a kill, share of $C$ | 9.21 % (948 nodes) | **0.21 % (160 nodes)** |
| naive set $\{V_1\le0<V_2\}$, share of $\Omega$ | 3.633 % | 3.574 % |
| player-1 half of $C$, share of $\Omega$ | 0.525 % | **0.529 %** |
| player-1 half of $C$, share of the naive set | 14.5 % | **14.8 %** |
| player-1 half of $C$ inside the naive set | 100 % | 100 % |

- **Where the player-1 half sits.** On the fine grid it is two mirror components of 18,600 nodes
  each, at $R$ from 3.20 to 5.72, with $\lvert\phi_1\rvert$ from $46°$ to $111°$ and
  $\lvert\phi_2\rvert\le76°$. The node medians are $R=4.46$, $\lvert\phi_1\rvert=74°$ and
  $\lvert\phi_2\rvert=18°$, so player 2 points roughly at player 1.
- The player-1 half of $C$ is exactly the part of the naive set that $W_1$ excludes.
- The "both can force a kill" share falls 40-fold under refinement. It is D&S's mutual-kill set,
  which has no volume.

## 2. The simulator can register a loss (part `harness`)

This is an internal check on the harness, not a result. From 400 starts at least one cell deep in
$W_1$ ($V^{RA}_1\le-\delta$) and 400 shallow ones ($-\delta<V^{RA}_1\le0$), player 1 flew laws
that should lose, against the reach-avoid adversary and against the trading player 2.

- **Bad laws lose.** Coasting ($\sigma_1=0$), turning away ($+\operatorname{sign}\phi_1$) and random
  bang-bang lose 108 to 335 of 400 runs, so the harness records losses.
- **Deep starts.** The reach-avoid law and the heuristic win all 400 on both grids.
- **Shallow starts.** On the fine grid the reach-avoid law loses 4 and trades 41 of 400 against each
  player-2 law, and the heuristic trades 41. These starts sit within a cell of $\partial W_1$, so
  the guarantee is not tested there. That is why the guarantee runs use starts at least one cell
  deep.

## 3. Retreat from the player-1 half of $C$ (part `retreat`)

From check 13's 2,000 starts in the player-1 half of $C$, player 1 flew the evader law of the mirror
game, $\sigma_1=+\operatorname{sign}(\partial V_2/\partial\phi_1)$, against five player-2 laws.

| player 2 | exits through $R=12$ (fine) | median closest approach (fine) |
|---|---|---|
| reach-avoid adversary | 1,289 | 3.42 |
| avoid ($V_1$) | 1,916 | 3.40 |
| trade ($t_2^*$) | 0 | 3.84 |
| pursuit heuristic | 0 | 3.61 |
| random bang-bang | 47 | 3.76 |

- **Player 1 is killed, alone or mutually, in 0 of 10,000 runs on each grid.** Every run ends with
  no kill or with an exit through $R=12$.
- So a player 1 who prefers a draw to dying alone can always retreat from the player-1 half of $C$.
  Together with check 13 (he cannot win alone there), that half is a draw for him, as the M5 record's
  §4.8 found on the $R_{\min}=0.2$ grids.

## 4. Reproducing

From `layer1/M5/`, in cmd:

```
python diag\diag_pole_report.py all 201x204 > m5_out\m5_out_V1_pole\diag_pole_report_201x204.log
python diag\diag_pole_report.py all 101x102 > m5_out\m5_out_V1_pole\diag_pole_report_101x102.log
```

- **Parts:** `extents`, `harness`, `retreat` or `all`. The grid tag defaults to 201x204, the
  horizon to 6.
- **Inputs:** the pole fields in `m5_out/m5_out_V1_pole/`. Set `M5_POLE_DIR` if they move.
- **Time:** about 3 min on the fine grid.
