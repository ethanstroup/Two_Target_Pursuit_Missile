# Layer 1 — M3 Explainer

**AE 8900 · reference doc, written 2026-10-02**
Companion to `Overview/Layer1/Layer1_M1_Explainer.md`, `Overview/Layer1/Layer1_M2_Explainer.md`,
`Overview/Layer1/Layer1_M3_2026-09-18.md` (the record of the results) and `Overview/Layer1/Layer1_Plan.md`.
Code: `layer1/M3/solve_m3.py`, `grid_study.py`, `zone_structure.py`,
`win_alone.py`, `sym_test.py`.

A plain-language walkthrough of what M3 does and why each check exists, in the same style as the
M1 and M2 explainers. Notation follows the project docs: $\nabla V$ has components $V_R, V_1,
V_2$, $\tau$ is the time remaining, $T$ is the horizon.

> **Source note.** Written from the M3 record, the Plan, and the M1/M2 explainers. The M3
> scripts themselves were not open when this was written, so no code is quoted, and a few
> statements about *how* a quantity is computed are marked as inferred. Section 10 lists them.

---

## 1. What M3 is, and why it exists

M1 verified the ingredients. M2 verified the machinery against a one-player game, where a plain
forward simulation gives an independent answer. **M3 is the real game: both players on, the
solution kept.** It produces the field everything later reads, $V(x,\tau)$ and the arrival time
$t_1^*(x)$.

There is no independent answer to compare the two-player $V$ against, which is why M2 existed. M3
therefore checks **internal consistency**:

- is the solution **converged** in the horizon and in the grid, so the field is a property of the
  game and not of the numerical settings;
- does it obey the **exact symmetries** the game has, so numerical error shows up as a measurable
  violation;
- is the grid free of **alignment defects** that would corrupt the later milestones.

Consistency is not correctness. M3 says the solve is stable and self-consistent; whether it is
*right* is M4, which compares it with Layer 0's independently derived barriers (§10).

---

## 2. The math M3 is protecting

**Same PDE as M2, with the evader switched back on:**

$$\frac{\partial V}{\partial\tau}=\min\big[0,\ H(x,\nabla V)\big],\qquad V(x,0)=\ell(x),$$

$$H=-V_R\,C+(V_1+V_2)\frac{L}{R}-|V_1|+|V_2|,\qquad C=\cos\phi_1+\cos\phi_2,\quad L=\sin\phi_1+\sin\phi_2.$$

The $+|V_2|$ term is the whole difference from M2's frozen $H$: player 2 maximizes, so his best
response is taken instead of being set to $\sigma_2\equiv0$. The value is

$$V(x,\tau)=\min_{\sigma_1(\cdot)}\ \max_{\sigma_2(\cdot)}\ \min_{t\in[0,\tau]}\ \ell\big(x(t)\big).$$

The Lax–Friedrichs dissipation coefficients are $\alpha_R=|C|$ and
$\alpha_{\phi_1}=\alpha_{\phi_2}=|L|/R+1$ (M2 §3). The CFL step is set by the largest
$\sum_i\alpha_i/\Delta_i$, and the worst case is the inner face, where $|L|/R+1\le 2/R_{\min}+1=11$.

**Winning zone.** $\{V\le0\}$ is the set of states from which player 1 can force the state into
$T_{1\to2}$ within $\tau$, against *any* player-2 behavior, **in the single-target game**: the one
that ignores that play would stop if $T_{2\to1}$ were entered first. That qualifier is what the
2026-10-01 revision added, and §9 returns to it.

**Arrival time.** $t_1^*(x)=\min\{\tau: V(x,\tau)\le0\}$, the first remaining-horizon at which the
state is in the winning zone. It is a derived field: the solver optimizes $V$, not time.

**The two symmetries.** Let $S:(R,\phi_1,\phi_2)\mapsto(R,\phi_2,\phi_1)$ swap the players and
$Rf:(R,\phi_1,\phi_2)\mapsto(R,-\phi_1,-\phi_2)$ reflect the geometry. Both are exact identities of
the model (Plan §2.5):

$$\ell_2=\ell_1\circ S,\qquad \ell_1\circ Rf=\ell_1,\qquad V(R,-\phi_1,-\phi_2)=V(R,\phi_1,\phi_2).$$

The first gives $V_2=V_1\circ S$ and $t_2^*=t_1^*\circ S$, so the second player's field is an axis
transpose and not a second solve. The second is the free check that §6 turns into a measurement.

---

## 3. What was solved

Four grids, all $R\in[0.2,12]$ with both ends included and angles uniform on $[-\pi,\pi)$ with no
duplicated $+\pi$ node. A grid named $n_R\times n_\phi$ has $n_R\times n_\phi\times n_\phi$ nodes.

| grid | nodes | horizon | role |
|---|---|---|---|
| $101\times100$ | 1.01 M | $\tau=10$ | horizon study; coarse member of the first pair |
| $201\times200$ | 8.04 M | $\tau=6$ | fine member of the first pair (has the defect, §6) |
| $101\times102$ | 1.05 M | $\tau=6$ | coarse member of the clean pair |
| $201\times204$ | 8.36 M | $\tau=6$ | fine member of the clean pair |

Stored in `layer1/M3/m3_out/`: `m3_<grid>_fields.npz` ($V$ and $t_1^*$ in float32; the sign of $V$ is exact
and the round-trip error is $4.7\times10^{-7}$, far below the 0.059 cell scale),
`Vsnap_101x102_T6.npz` ($V(\cdot,\tau)$ every 0.5, for M4's test C1), and `m3_<grid>.json`
(convergence diagnostics).

---

## 4. Check 1 — the transpose identity, verified rather than assumed

Plan §10 step 2 says to assert $V_2=V_1\circ S$ on the grid. M3 does it the expensive way on
purpose. `solve_m3.py` builds the **mirror game from scratch**: player 2 minimizing, player 1
maximizing, and $\ell_2$ written out independently from the index asymmetry (boresight bound on the
shooter's own angle, range bounds on the target's aspect angle) instead of calling $\ell_1$ with
swapped arguments. It solves that game and compares.

| grid | $\max\lvert V_2-V_1\circ S\rvert$ | winning-zone disagreement |
|---|---|---|
| $51\times50$ | $1.8\times10^{-14}$ | 0 nodes |
| $101\times100$ | $6.5\times10^{-13}$ | 0 nodes |

**Why from scratch.** Calling $\ell_1$ with swapped arguments would pass for any $\ell_1$, right or
wrong, because it is the same code. An independent construction of $\ell_2$ can fail, so passing
means something. Agreement at round-off level is what an exact identity should give, and it is why
M5's second field is an axis transpose.

---

## 5. Check 2 — convergence in the horizon

The question: as $\tau$ grows, does $\{V\le0\}$ stop changing? Marched to $\tau=10$ at $101\times100$
and $\tau=6$ elsewhere, reporting every 0.25.

**The criterion had to be fixed first.** "How much did the zero level set move?" normalized by the
whole grid is meaningless: the grid is mostly empty space, so any converged surface scores well.
Normalized by the **zero level set's own node count**, the number is a statement about the surface:

| $\tau$ | motion, as a fraction of the surface itself |
|---|---|
| 0.25 | 48.8 % |
| 2.00 | 4.90 % |
| 4.00 | 1.30 % |
| 6.00 | 0.24 % |
| 10.00 | 0.038 % |

(Presumably the number of nodes whose sign changed between successive reports, divided by the
surface node count. The record does not spell out the numerator; check `solve_m3.py`.)

**Extrapolating.** A fit $f(\tau)=L-Ae^{-k\tau}$ to the winning-zone fraction on the tail, using
data from $\tau\le6$, puts the infinite-horizon zone at $L=12.0236\,\%$ of the grid. An independent
march to $\tau=10$ gave $12.0271\,\%$. The extrapolation predicted the long run to 0.004 % of grid
volume, which is the real test of whether "converged" is a fact or a hope. Note the sign: the
measured value is slightly *above* the fitted limit, so $L$ is a small underestimate. At this size
it does not matter.

**The outer edge** in $R$ is 6.100 on every grid, inside $\bar R(0)=3+\pi=6.1416$. This is Davidovitz
& Shinar's bounded winning zone, and it is the two-player counterpart of M2's front moving at speed
2 until it ran out of domain. Against a maneuvering evader the edge does not advance (M2 §5,
Section 5, Check 2).

**Why $\tau=6$ is enough for the grid study.** At $\tau=6$ the surface is still moving at 0.24 %,
so the horizon is not fully converged there. The grid pairs are compared at the *same* $\tau$, so
that remaining motion is common to both members and cancels in the comparison. That is a statement
about a comparison, not about the infinite-horizon answer.

---

## 6. Check 3 — convergence in the grid

**The grids nest on purpose.** $n_R$ goes $101\to201$ with endpoints included, and $n_\phi$ goes
$n\to2n$ with `endpoint=False`. Every coarse node is then a fine node, and the comparison is exact
subsampling, $V_{\text{fine}}[::2,::2,::2]$. A $101\to201$ pair in the periodic angles would not
nest ($2\pi/101$ against $2\pi/201$), and the study would be measuring its own interpolant as much
as the solver.

**The criterion is displacement, not a node count.** A count of flipped nodes grows with the
surface's area whatever the solver does. Spread the symmetric-difference volume over the surface
area instead and the result is a thickness, which converts to cells:

$$d\;\approx\;\frac{\lvert\{V_c\le0\}\,\triangle\,\{V_f\le0\}\rvert}{\text{area}(\{V=0\})}\;\Big/\;\Delta_{\text{coarse}}.$$

| | $101\times100\ /\ 201\times200$ | $101\times102\ /\ 201\times204$ (clean) |
|---|---|---|
| barrier displacement under refinement | 0.154 coarse cells | **0.159 coarse cells** |
| disagreements further than 3 cells from the barrier | 0 | **0** |
| $t_1^*$ between grids | median 0.000, 95th 0.000 | **median 0.000, 95th 0.000** |
| $t_1^*$ reflection mismatch, fine grid | 21 642 nodes | **0 nodes** |
| M5 smoke test, fine grid, raw | 98.8407 % | **100.0000 %** |

**Reading it.** 0.159 coarse cells is about $0.019$ in $\ell$ units (cell 0.118 at $101$ nodes in
$R$). The second row says there is no disagreement away from the barrier, which is what a
clean solve looks like: all the difference is the surface sliding a fraction of a cell. The
bottom two rows are the symmetry checks of the next section.

*(Inferred.)* A median and 95th percentile of exactly 0.000 for $t_1^*$ suggest it is stored at a
coarse time resolution, so agreement partly reflects that quantization and is a weaker statement
than agreement of a continuous field. Worth confirming before quoting it as sharp.

---

## 7. The one defect: $n_\phi$ a multiple of 8 puts grid nodes on $|\phi_1|=\beta$

**The mechanism.** Node $k$ sits at $\phi=-\pi+2\pi k/n_\phi$, so $\phi=\beta=\pi/4$ is node index
$0.625\,n_\phi$. That is an integer whenever $n_\phi$ is a multiple of 8. $|\phi_1|=\beta$ is the
target set's own kink, where the max in $\ell$ switches between the boresight term and the range
terms. A whole *line* of nodes then sits exactly on a kink and pays Lax–Friedrichs dissipation
there every step (M1 §5). For $n_\phi=102$ the index is 63.75, and for $204$ it is 127.5: off-node,
and still nesting, since $204=2\times102$.

**Why it is findable at all.** Reflection invariance is exact in the continuum: $\ell$ is
$Rf$-invariant to $4\times10^{-15}$ and the dynamics are $Rf$-equivariant with the controls
negated, so $V(R,-\phi_1,-\phi_2)=V(R,\phi_1,\phi_2)$ identically. **Any residual is numerical
error.** That makes the symmetry a free, sharp check on an expensive computation.

| grid | $\beta$ on a node? | $\max\lvert V-V\circ Rf\rvert$ | $t_1^*$ mirror mismatch | M5 smoke test (raw) |
|---|---|---|---|---|
| $101\times100$ | no | $3.6\times10^{-9}$ | 0 nodes | 100.0000 % |
| $201\times200$ | **yes** | $9.9\times10^{-4}$ | **21 642 nodes** (2.2 % of the zone) | 98.8407 % |
| $101\times102$ | no | $4.5\times10^{-10}$ | 0 nodes | 100.0000 % |
| $201\times204$ | no | $2.8\times10^{-4}$ | **0 nodes** | **100.0000 %** |

The error grows with $\tau$ ($6\times10^{-8}$ at $\tau=2$, $5\times10^{-7}$ at $3$,
$9.9\times10^{-4}$ at $6$) and with resolution. An isolated experiment at $n_R=31$ with
$n_\phi=104$ ($\beta$ on-node) against $102$ (off-node) shows the on-node grid 55× worse at
$\tau=6$, which pins the cause on the node alignment. It also shows the defect needs the fine $R$
grid and the long horizon to reach $10^{-3}$.

**Why it mattered when M3's own criteria did not see it.** M3's criteria are about the barrier,
where the residual is 1.7 % of one cell. But the symmetry is the thing M5 builds on. The smoke test
is the identity $t_1^*=t_2^*$ on $|\phi_1|=|\phi_2|$, which reduces exactly to $Rf$-invariance of
$t_1^*$ there (because $Sx=Rf\,x$ on that surface). A 2.2 % symmetry error is noise injected
straight into the field M5 reads.

**Why it was not patched.** Projecting onto the symmetry, $\min(t,\,t\circ Rf)$, restores the smoke
test to exactly 100 % and the residual to 0. That is a legitimate operation: it removes numerical
error from an exact symmetry. It is the wrong thing to *measure on*, because projection can equally
hide a genuine asymmetric component or manufacture one. `grid_study.py` reports the smoke test raw
and projected, never only projected. The fix is a grid choice, $n_\phi=102\to204$, solved and green
on every check with no projection.

**Still worth watching.** Even off-node, the residual in $V$ itself is $2.8\times10^{-4}$: a
shock-ridge effect at $\phi_1\approx\pm\pi$ that grows with resolution. It passes the "< 1 % of a
cell" bar, but if M4's test B (gradient direction) misbehaves near the ridge, look here first. M2
flagged the same ridge as the source of its tail.

---

## 8. Structural findings

### The single-target winning zone is connected

D&S report five disconnected closed subregions. The converged $\{V\le0\}$ is **one** component
(99.96 % of the zone) at both resolutions, and connected in every $R$ section. **This is not a
discrepancy.** Layer 1's $V$ is the *uncorrected single-target* reach problem, the same one Layer 0's
barriers are seeded from (Plan §6). D&S's five subregions belong to the *corrected* zone,
$T_1'=T_1\setminus\overline{T_2}$ (Appendix B), a different object. Whether the correction is what
disconnects it is Layer 2's question and the reason M5 (now a reach-avoid solve) is the test: test F
checks $W_1$ against the five subregions.

### $\{V_1\le0\}\setminus\{V_2\le0\}$ has three components, not five

*(Retitled 2026-10-01; the set used to be called the "win-alone set".)* It is not one. Player 1's
reach strategy does not steer around $T_{2\to1}$, so "player 2 cannot force a kill against an
avoiding player 1" says nothing about a player 1 who is not avoiding. The true win-alone set is M5's
reach-avoid set. The name `W_1` is kept as it appears in `win_alone.py`.

It is **7.17 %** of the grid (7.05 % coarse), in 3 components: 91.0 %, 4.46 %, 4.46 %, the last two
exact $Rf$ mirrors. Stable under refinement.

**It briefly counted five, and that is the part worth recording.** Two of the five were 23-node
blobs at the inner $R$ face with $|V|<0.015$, about 12 % of one cell, which would have matched D&S
exactly. Forward simulation from them under the grid's own policy gives $\min\ell=+0.41$ to $+0.54$:
they are not reachable states. They are leakage from the `extrapolate` condition at the singular
$R\to0$ face (Plan §3, trap 2), at $R=0.200$ and $0.318$, and they are the only grid-study
disagreements not adjacent to the barrier. An inner-boundary mask $R\ge0.45$ removes them, and the
count is a stable 3 from $R\ge0.45$ through $R\ge0.80$.

The lesson is about being pleased by agreement: a result that matched the reference was the one
that turned out to be wrong, and the check that caught it was a forward simulation, not a count.

**This is the same inner-face problem as M2 §7**, in a milder form. M2's frozen field blows up
there because nothing bounds $V$ from below. M3 does not: its $\min V=-0.802$ against the bound
$-\beta=-0.785$ (M2 §7). The mask is the standing rule: **$\{V\le0\}$ is never quoted without it**,
and it applies to M4's tests A–E. It supports results on the retained domain; it does not establish
that the masked region is correct.

### The 4.53 % "both can force a kill" volume

$\{V_1\le0\}\cap\{V_2\le0\}$ is **4.53 %** of the grid, stable between $101\times100$ (4.5185 %) and
$201\times204$ (4.5276 %), so it is a real volume and not resolution noise. Only 9 % of it lies
within one cell of $|\phi_1|=|\phi_2|$. **It is not the mutual-kill set.** Each player has a
guarantee against a purely *avoiding* opponent, and both guarantees cannot be realized at once.
After the revision it is also not an upper bound on M5's contested set (the two are defined in
different games), only a comparison figure: Plan §4 M5 step 4 reports how far apart they are.

---

## 9. What M3 does and does not establish

**Established**

- The solve is converged in the horizon (extrapolation predicts the long run to 0.004 %) and in the
  grid (barrier moves 0.16 coarse cells under $2\times$ refinement).
- The reflection and player-swap symmetries hold to round-off or to a stated, small residual on the
  clean grid pair, with no projection.
- $V$ stays within 0.017 of the lower bound $-\beta$ (M2 §7), so M3 is free of the failure that
  invalidates the frozen field near $R=0.2$.

**Not established**

- **Correctness against Layer 0.** Convergence says nothing about whether the converged answer is
  the right one. A wrong sign convention converges just as well. M1 and M2 guard the formulation;
  M4 is the external check.
- **The two-target game.** $\{V\le0\}$ guarantees entry to $T_{1\to2}$ in the single-target game.
  It is *not* a guarantee of winning alone, and $t_1^*$ and $t_2^*$ come from different games, so
  comparing them does not decide an outcome. Both corrections are in the 2026-10-01 revision; the
  solve and every number stand.
- **That the masked region is correct.** The mask excludes the leakage; it does not repair it.

---

## 10. Items to confirm against the scripts

Statements above that come from the record without the code in front of me:

- how motion in §5 is computed (the numerator), and the time resolution of the stored $t_1^*$;
- whether the grid-study table in §6 is computed with the $R\ge0.45$ mask (`grid_study.py` honors
  `R_MARGIN`; the record does not say what the table used);
- **an unreconciled sum:** $7.17\,\%+4.53\,\%=11.70\,\%$ for $\{V_1\le0\}$, against a winning-zone
  fraction of $12.02\,\%$ at $\tau=10$. The gap is probably the mask or $\tau=6$ against $\tau=10$,
  but the record does not say.

---

## 11. Concepts worth having straight

**Two meanings of "converged."** Converged in the horizon means the *answer to the game* stopped
changing as $\tau$ grew. Converged in the grid means the *numerical approximation* stopped changing
as the grid refined. They are separate and M3 tests both, at different resolutions.

**Normalize a criterion by the thing it describes.** Motion divided by the grid is dominated by empty
space, a node count grows with surface area, and a relative error divided by a quantity that is
supposed to be zero reports rounding. Each of M3's two convergence criteria was repaired by dividing
by the right object: the surface's own nodes, and the surface's area. (Same lesson as M1's
Hamiltonian check, from the other side.)

**Use exact symmetries as a free test.** Where the continuum answer is known to be invariant,
any asymmetry in the computed field is a pure numerical-error measurement, with no reference
solution required. That is how a $10^{-3}$ defect on an eight-million-node, four-hour solve became
visible, and it is also why raw and projected numbers are both reported.

**Alignment hazards recur.** M1 chose 181 nodes to avoid $\beta$; M3 found 200 lands on it. A grid
resolution that divides the circle into eighths aligns with $\pi/4$. Any later grid needs the same
check: $n_\phi$ not a multiple of 8.

**An agreement can be the bug.** The five-component count matched D&S, and was leakage.

---

## 12. Hand-off

- **Grid for M4 and M5:** $101\times102$ for development, $201\times204$ for the study. Never
  $n_\phi$ a multiple of 8.
- **Mask:** $R\ge0.45$ on every acceptance test and every quoted volume.
- **M4, test C1** reads `Vsnap_101x102_T6.npz` through `hji.make_policy`, at the remaining horizon.
  *(Inferred.)* The snapshots are 0.5 apart, so a nearest-snapshot read can be off by up to 0.25 in
  $\tau$, ten times coarser than M2's 0.05. C1 must match controls *at the located switches*, so if
  the switch times disagree by a fraction of 0.25, check the snapshot spacing before suspecting $V$.
- **M4, test B** should be scored by the angle between $\nabla V$ and $\lambda$, or against the
  summed-term magnitude, never relative to $V$ or $H$. Watch the ridge at $\phi_1\approx\pm\pi$
  (§7).
- **M5** is a reach-avoid solve: $V^{RA}_1$ with initial value $\max(\ell_1,-\ell_2)$, $\ell_2=\ell_1\circ S$,
  and `static_obstacle(-ell_2)`. It reuses M3's transpose identity for $W_2=W_1\circ S$, and takes
  $D=\{V_1>0\}\cap\{V_2>0\}$ from these fields. Cost: one solve per grid, about 13 min at
  $101\times102^2$ and 4 h at $201\times204^2$.

### Cost, measured

| grid | nodes | wall, $\tau=6$ |
|---|---|---|
| $101\times100\times100$ | 1.01 M | 724 s |
| $101\times102\times102$ | 1.05 M | 777 s |
| $201\times200\times200$ | 8.04 M | 13 815 s (3.8 h) |
| $201\times204\times204$ | 8.36 M | 14 731 s (4.1 h) |

Memory peaked near 2.9 GB. Doubling the resolution cost $19\times$ in time (nodes $\times8$, and the
CFL step roughly halves, so steps $\times2$ and a bit more). By the CFL bound at $101\times102^2$,
$\Delta\tau\approx0.0020$, so about 3000 steps to $\tau=6$ (my estimate from M2's formula, not a
logged count). The step is set by the singular $R\to0$ trap, $2/R_{\min}+1=11$, not by the resolution
one would naively pick.

---

## 13. Quick file map

```
layer1/M3/solve_m3.py        the march: pre-flight, horizon convergence, V and t_1*
layer1/M3/grid_study.py      nested-grid comparison + the symmetry checks (COARSE/FINE via env)
layer1/M3/zone_structure.py  connected components of {V<=0}, phi-periodic
layer1/M3/win_alone.py       components of W_1, with the inner-boundary mask
layer1/M3/sym_test.py        the beta-on-node isolation experiment
layer1/M3/m3_out/            fields .npz, Vsnap_101x102_T6.npz, diagnostics .json
```

`solve_m3.py` honors `M3_PREFLIGHT=0` and `M3_SNAP_EVERY`; `win_alone.py` and `grid_study.py` honor
`R_MARGIN`; `grid_study.py` honors `COARSE` and `FINE`.
