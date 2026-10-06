# Layer 1 — M2 Explainer

**AE 8900 · reference doc, written 2026-10-02; revised after the section-by-section walkthrough**
Companion to `claude/Layer1_M1_Explainer.md`, `claude/Layer1_Plan.md` and
`claude/Layer1_Progress_2026-09-14.md`. Code: `Two_Target_Pursuit_Missile/layer1/hji.py`,
`ell.py`, `test_m2.py`.

A plain-language walkthrough of what M2 checks and why, section by section, in the same style
as the M1 explainer. Notation follows the project docs: $\nabla V$ has components
$V_R, V_1, V_2$, $\tau$ is the time remaining, and $T$ is the horizon.

---

## 1. What M2 is, and why it exists

M1 verified the *ingredients* (the target function $\ell$, the dynamics, the Hamiltonian)
without solving anything. M2 is the first time `hj_reachability` actually integrates the PDE,
so it is the first place a wrong sign convention, a wrong player minimizing, or a missing
periodic boundary can corrupt a solution.

The two-player solve is hard to check, because nobody can say independently what the right
answer is. M2 removes that difficulty by **freezing the evader**: $\sigma_2\equiv 0$. Player 1
is then the only decision maker, and the answer can be checked by direct forward simulation of
the aircraft. A plain simulation is a reference that does not share any code with the solver.
Plan §4: *"Get this exactly right before turning player 2 on."*

---

## 2. The math M2 is protecting

**State and dynamics.** $x=(R,\phi_1,\phi_2)$ with

$$\dot R=-(\cos\phi_1+\cos\phi_2),\qquad \dot\phi_1=\frac{L}{R}+\sigma_1,\qquad \dot\phi_2=\frac{L}{R}+\sigma_2,$$

$L=\sin\phi_1+\sin\phi_2$, and $|\sigma_i|\le 1$. Freezing the evader sets $\sigma_2=0$. Note
that $\phi_2$ still moves, through the $L/R$ term: the evader does not turn, but the line of
sight rotates.

**The value.** With nobody maximizing, the game collapses to a one-player minimum:

$$V(x,\tau)=\min_{\sigma_1(\cdot)}\ \min_{t\in[0,\tau]}\ \ell\big(x(t)\big).$$

$V$ is the best (lowest) margin $\ell$ that player 1 can reach at any moment within the
remaining time $\tau$. The **winning zone** is $\{V\le 0\}$: the states from which player 1 can
touch the target set $T_{1\to2}$ within $\tau$.

**The PDE.** Marching in $\tau$ (time remaining), starting from $V(x,0)=\ell(x)$:

$$\frac{\partial V}{\partial\tau}=\min\big[0,\ H(x,\nabla V)\big].$$

For the two-player game, $H=-V_R C+(V_1+V_2)\dfrac{L}{R}-|V_1|+|V_2|$ with $C=\cos\phi_1+\cos\phi_2$.
Freezing player 2 removes the $+|V_2|$ term (the evader's best response is no longer taken):

$$H_{\text{frozen}}=H-|V_2|=-V_R C+(V_1+V_2)\frac{L}{R}-|V_1|.$$

(`FrozenEvader` in `hji.py` does this by zeroing the disturbance Jacobian. The rest of the
solver is untouched, which is the point: it is the same machine with one input switched off.)

> **Sign note.** Earlier versions of the Plan and the M1 explainer wrote the PDE as
> $\partial V/\partial\tau+\min[0,H]=0$, which is the $t$-form with a $\tau$ label. In $\tau$
> (time remaining) the equation is the one above, $\partial V/\partial\tau=\min[0,H]$. The
> library marches in $t=-\tau$, where the step reads $dV/dt=-\min(0,H)$. The M1 explainer's
> Lax–Friedrichs dissipation also carried a minus sign; §3 gives the correct one. All three
> were corrected 2026-10-02.

### Why $\min(0,H)$, in one picture

Give player 1 one more step $\Delta\tau$ of time. Then
$V(x,\tau+\Delta\tau)\approx\min\{V(x,\tau),\ V(x+f\Delta\tau,\tau)\}$: either the extra time
buys nothing and the value stays at $V(x,\tau)$, or player 1 moves along $f$ for one step and
plays the remaining $\tau$ from the new state. Expanding the second term gives
$V(x,\tau)+\Delta\tau\,\nabla V\cdot f$, so

$$V_{\text{new}}=V+\Delta\tau\,\min(0,H).$$

If $H>0$ the move would make things *worse*, so the first branch wins and $V$ stays put. $V$
cannot grow with $\tau$, which is the structural fact behind "a longer window can only help
the running minimum".

### What the numbers mean

- $\ell\ge |\phi_1|-\beta\ge-\beta$ under the default `sdist` weighting (the boresight term has
  weight 1), so $\min\ell=-\pi/4\approx-0.785$ (fine-grid minimum $-0.78540$ at
  $R\approx1.04$, $\phi_1=0$, $\phi_2=\pm\pi$).
- $V$ is a minimum of $\ell$ along a path, so **$-\beta\le V\le\ell$ at every node and every
  $\tau$.** The upper bound is "waiting is allowed"; the lower bound will matter in §7.

### The $\tau$ convention

$T$ is the horizon (the dial you set, 3 in `test_m2.py`). $\tau$ is how much time is left.
The solver marches $\tau$ from 0 up to $T$; the stored snapshot at $\tau$ is $V(\cdot,\tau)$.
A trajectory at elapsed time $t$ has $\tau=T-t$ left, so it must read the snapshot
$V(\cdot,T-t)$. (Both visualization explorers use $\tau$ as time remaining.)

---

## 3. How the PDE is actually stepped

Per node, per step, with a $101^3$ grid (library 0.7.0):

1. **One-sided derivatives.** WENO5 gives a backward $D^-$ and a forward $D^+$ estimate of
   $\nabla V$ at every node. Two estimates, not one, because $V$ has real kinks.
2. **Numerical Hamiltonian** (global Lax–Friedrichs, $\tau$-form):
   $$\hat H=H\!\Big(x,\tfrac{D^-+D^+}{2}\Big)+\sum_i\frac{\alpha_i}{2}\big(D_i^+-D_i^-\big),$$
   with dissipation coefficients $\alpha_R=|C|$ and $\alpha_{\phi_1}=|L|/R+1$; $\alpha_{\phi_2}=|L|/R$
   for the frozen game (no $\sigma_2$ term) and $|L|/R+1$ for the two-player game. The $\alpha$s
   depend only on the state, which is what "global" means. The $+$ sign gives positive diffusion
   when $\tau$ is marched forward (equivalently, $t=-\tau$ marched backward), so $\hat H$ is the
   same function of $D^\pm$ in either labeling. The textbook $-$ sign is for
   $\partial V/\partial t+H=0$ marched forward in $t$; used here it drives $V$ below $\min\ell$ at
   the kinks of $V$ (checked on a 1D test, 2026-10-02).
3. **Update with the clamp:** $V\leftarrow V+\Delta\tau\,\min(0,\hat H)$, applied inside each
   stage of a 3rd-order TVD Runge–Kutta step (`very_high` accuracy = WENO5 + RK3).
4. **Time step.** CFL: $\Delta\tau=0.75/\max\sum_i\alpha_i/\Delta_i$. At $101^3$ this is about
   0.0022 for the frozen game, about 1350 steps to reach $\tau=3$.
5. **Boundaries.** Angles are periodic (no duplicated $+\pi$ node). The two $R$ faces use
   `extrapolate`: ghost values are filled by continuing the end slope linearly.

---

## 4. `hji.py` — the pieces M2 uses

- `FrozenEvader` — as above; the solver's only change versus the two-player problem.
- `make_grid(n_R, n_phi)` — $R\in[0.2,12]$ with both ends included, angles uniform on
  $[-\pi,\pi)$.
- `solve_backward` — marches and returns a stack of snapshots, one per requested $\tau$ (61
  outputs, $\tau=0,\dots,T$).
- `grad_field`, `make_interp` — $\nabla V$ on the grid and a trilinear interpolant of $V$ for
  evaluating $V(x_0)$ at an arbitrary start state.
- `make_policy` — the feedback law. At time $t$, with state $x$, it reads the stored snapshot
  nearest $\tau=T-t$ and returns
  $$\sigma_1^*=-\operatorname{sign}\!\Big(\frac{\partial V}{\partial\phi_1}(x,\tau)\Big)$$
  (ties go to $\sigma_1=-1$). It keeps a subset of the 61 snapshots (`k_max=31`) with the
  angular partials in float32 to bound memory.
- `make_static_policy` — the same law reading one snapshot, $V(\cdot,T)$, at all times. This is
  the *stale read*, kept on purpose as a control experiment (§5, Section 3).
- `forward_sim` — RK4 integration of `barrier.state_dot`, control held constant over each step,
  angles wrapped, and a flag when the trajectory leaves the $R$ domain.

---

## 5. `test_m2.py`, section by section

Usage: `python3 test_m2.py [n_grid] [T]` (defaults 101 and 3.0, with $K=61$ output times).

### The weighting of $\ell$, and the "cell"

Every tolerance below is quoted in **cells**, and a cell depends on how $\ell$ is weighted, so
the weighting comes first. $\ell$ is a max of three terms, each multiplied by a positive weight:

$$\ell(x)=\max\big(w_b\,g_{\text{bore}},\ w_n\,g_{\min},\ w_x\,g_{\max}\big),$$

with $g_{\text{bore}}=|\phi_1|-\beta$, $g_{\min}=\underline R(\phi_2)-R$, $g_{\max}=R-\bar R(\phi_2)$.
**The weights never change the sign of $\ell$ or its zero set**, so the target set, the barrier and
every acceptance test are the same under all three choices. They change only how steep $\ell$ is,
which is a numerical conditioning question.

- **`raw`:** all weights 1. What M1 and M2 first ran with. The terms mix a radian with two lengths,
  but their gradients are already close to 1 near the surface.
- **`plan`:** $w_b=1/\beta$, $w_n=w_x=1/\bar R_0$. Plan §2.1 as written, meant to make the terms
  dimensionless margins.
- **`sdist`** (the current default): each term is divided by the size of its own gradient in
  $(R,\phi_1,\phi_2)$, so each has $|\nabla|=1$ exactly and is roughly a signed distance to its own
  surface. For example $w_x=1/\sqrt{1+(1+\cos\phi_2)^2}$.

Measured $|\nabla\ell|$ on nodes within 1.0 of the zero level set (from `ell.py`):

| scaling | p05 | median | p95 | p95/p05 |
|---|---|---|---|---|
| raw | 1.000 | 1.000 | 1.864 | 1.9 |
| plan | 0.163 | 0.330 | 1.273 | 7.8 |
| sdist | 0.861 | 1.000 | 1.188 | 1.4 |

**Why $|\nabla\ell|\approx1$ is the goal.** A level-set value should behave like a distance to its
surface. (1) A numerical error $\delta V$ moves the computed zero set by about
$\delta V/|\nabla V|$, so a flat direction makes the barrier sensitive to small errors. (2) The grid
spacing is fixed, so a steep direction jumps a lot between nodes (more smearing from the
Lax–Friedrichs term) while a flat direction pins the zero crossing poorly. (3) Tolerances such as
"one cell" and M4's "$|V|<$ grid tolerance" only convert to a position tolerance when
$|\nabla V|\approx1$ at the surface. This is a statement about the initial $\ell$, since $V$ develops
its own kinks and plateaus as $\tau$ grows; the weighting buys a well-conditioned start. Even
`sdist` is a Euclidean distance mixing radians and lengths, so a value is a weapon-envelope margin
and not a physical distance.

**Why `plan` flattens $\ell$.** Along $R$, $\partial g_{\min}/\partial R=-1$, so dividing by
$\bar R_0=6.14$ leaves $|\partial(w_n g_{\min})/\partial R|=1/\bar R_0=0.163$, six times shallower, wherever a range
term is active. The boresight term goes the other way, $1/\beta=1.273$. Those two numbers are
exactly the table's p05 and p95 for `plan`. Dividing by a constant makes the terms comparable in
magnitude, not in gradient.

**Effect on the answer.** Discretization error and not a different barrier. At $101^3$ the computed
$\{V\le0\}$ differs between `raw` and `sdist` on 0.005% of the grid and between `plan` and `raw` on
0.12%, with `plan` consistently a bit smaller (11.577% vs 11.631%). `sdist` is a deviation from Plan
§2.1 as written, flagged as proposed, and reverting is one string (`LAYER1_ELL_SCALING=plan`).
The decision has been open for Ethan since 2026-09-15.

**The cell.** One cell is `E.value_scale(grid, V0)`: the largest change in $\ell$ when stepping one
node along any axis, taken over nodes within $|\ell|\le1$ of the zero set. It is 0.1967 at $61^3$ and
0.1180 at $101^3$, which equal $\Delta R$ ($11.8/60$ and $11.8/100$): $|\nabla\ell|\approx1$ under
`sdist` and the range axis has the coarsest spacing. It replaced "compare against $dR$", which was
only meaningful while $\ell$ was unscaled, because a length and a value are not interchangeable once
the terms carry weights.

It is measured *near* $\{\ell=0\}$ because the grid is uniform but $\ell$ is not. Far out, a
$\phi_2$-dependent weight multiplies a large residual, $w_x'(\phi_2)\,(R-\bar R(\phi_2))$, so one
angle step changes $\ell$ by a few tenths. A whole-domain maximum inflates the unit by roughly two
to three times (the records say 0.13 to 0.39 in `ell.py` and 0.118 to 0.239 in the Amendment, not
recomputed here) and loosens every tolerance for no reason. "0.57 cell" means a bit over half the
change in $\ell$ you get by moving one node near the boundary.

### Section 1 — structure of the solution

Four cheap invariants on the full stack of snapshots:

- $V$ is finite everywhere;
- $V\le\ell$ everywhere (waiting is always an option);
- $V$ is non-increasing in the horizon;
- the winning zone $\{V\le 0\}$ grows monotonically with the horizon.

These catch gross failures (NaNs, wrong marching direction) but they are all *upper-side*
properties. **Nothing here bounds $V$ from below**, which is the gap discussed in §7.

### Section 2 — the reach front travels at the maximum closing speed

Against a frozen evader the winning zone is **range-limited**: its outer edge in $R$ can advance
no faster than the largest closing speed $\max|\dot R|=\max(\cos\phi_1+\cos\phi_2)=2$, and with
both aircraft nose-on it moves at exactly that. The edge is the largest grid $R$ having any
node with $V\le 0$:

```python
edge = np.array([Rg[np.where((v <= 0).any(axis=(1, 2)))[0].max()] for v in Vs])
unsat = edge < Rg[-1] - 2*dR          # drop snapshots that ran into the R = 12 face
sp = np.polyfit(taus[unsat], edge[unsat], 1)[0]
```

Asserted: measured slope within 0.10 of 2, and the edge never advances faster than the closing
speed (plus about one $dR$). Measured **2.016** at $61^3$ and **2.003** at $101^3$; a front moving
at exactly 2, read off the grid's $R$ nodes, would show 2.015 and 1.999, so the small excess is
quantization and nothing else.
This is a physical check that the solver cannot pass by accident. It replaced "has the zero
level set stopped moving?", which is an M3 criterion: against a frozen evader the zone never
stops, it runs out of domain.

*Odd-$N$ detail:* an odd number of angle nodes has no $\phi_2=0$ node, so the edge at $\tau=0$
reads 5.903 ($61^3$) or 5.982 ($101^3$) rather than 6.1416.

### Section 3 — (a) the value function's own law ACHIEVES $V$

The claim: **$V$ is not too low.** If $V$ says "player 1 can reach margin $V(x_0,T)$", then
flying the feedback law from $x_0$ must actually reach it.

240 random start states with $R_0\in[1,8]$, $\phi_1,\phi_2$ uniform, and $\ell(x_0)>0$ (outside
the target at the start). For each, simulate the law and compare:

$$\text{gap}=\min_t\ell\big(x(t)\big)-V(x_0,T).$$

The gap is a **shortfall**: positive means the law did worse than $V$ promised. Asserted
(in cells): median $|\text{gap}|<0.1$, 90th percentile $<1$, maximum $<3$. Trajectories that
exit the $R$ domain are dropped (232 of 240 at $61^3$, 230 at $101^3$ stay in).

A second assertion: the sign of $V(x_0,T)$ agrees with the sign of the simulated $\min_t\ell$
for at least 98% of the samples (it was 232/232 and 230/230).

**Why both a value and a control test exist.** $V$ and the law are built from the same
snapshots, but not the same *numbers*: $V$ is read at a state, the law needs a *gradient sign*
at the right $\tau$. $V$ can be perfect while the law is wrong, which is the stale-read test.

**The stale read.** Reading $V(\cdot,T)$ at every time (instead of $V(\cdot,T-t)$) gave a worst
shortfall of **2.04 versus 0.13**. The reason: the clamp $\min(0,\hat H)$ freezes $V$ on large
plateaus of $V(\cdot,T)$, so $\partial V/\partial\phi_1=0$ there, the sign is undefined, and the
bang-bang law degenerates into coasting. The test asserts the stale read is
more than $5\times$ worse than the correct one. It exists so a future session cannot reintroduce
the stale read and then blame the value function. It was originally mistaken for a shock ridge at
$\phi_1=\pm\pi$ (a real feature, 0.85% of nodes), but a one-step-lookahead policy did not help and
brute force showed a constant $\sigma_1=-1$ reaching $-0.783$ against $V=-0.719$: $V$ was right and
slightly conservative, the control read was the defect.

### Section 4 — (b) NO other control beats $V$

The claim: **$V$ is not too high.** $V$ is a *minimum over all controls*, so no control can
produce a smaller $\min_t\ell$ than $V(x_0,T)$ (up to discretization). The test computes

$$\text{beat}=V(x_0,T)-\min_t\ell\big(x(t)\big),$$

and **positive means the other control beat $V$**: $V$ claims the best reachable margin is
$V(x_0,T)$, yet a simple control reached a lower one, so $V$ is too high (it understates what
player 1 can do). A wrong sign convention, the wrong player minimizing, or a
missing periodic boundary typically produces a $V$ that some simple control beats, which is why
this half is called the sharp one.

**Sign flip from Section 3.** Section 3's gap was $\min_t\ell-V$ (positive means the law fell
short). Section 4's beat is $V-\min_t\ell$ (positive means $V$ was beaten): the same difference
with the opposite sign, so read the printed "worst $V-\min_t\ell$" lines with that in mind.

**Why Section 3 cannot replace this.** Section 3 only tests the one control that $V$'s own gradient
recommends. Its assertion uses $|\text{gap}|$, so it would also flag a law that does better than
$V$ promised, but the law steers by $V$'s gradient and need not find a better path. A $V$ that is
too high can therefore pass (a) while a direct search finds the lower path.

Adversaries, each on 120 of the sample states, each required to stay under one cell:

- constant $\sigma_1=+1$, $-1$, and $0$;
- the pursuit heuristic $\sigma_1=-\operatorname{sign}(\phi_1)$ (the law used in the Layer 0 sim);
- three random bang-bang laws (random sign, switching every 0.05–0.8 time units);
- a **brute-force single-switch sweep**: for each of 40 states, both signs and 21 switch times
  (42 controls), keeping the best. This is a far stronger adversary than any fixed law. It is a
  search, not a proof, since it only covers one-switch controls.

Result: the worst was the pursuit heuristic, and even it did not beat $V$ by one cell. Worst
violation of optimality under `sdist`: **+0.116** at $61^3$ (0.59 cell) and **+0.067** at
$101^3$ (0.57 cell), within one cell at both resolutions and smaller in absolute terms
at the finer grid, as discretization error should be. A small positive violation is the
signature of the Lax–Friedrichs dissipation making $V$ slightly conservative: in the earlier
brute-force case a constant $\sigma_1=-1$ reached $-0.783$ against $V=-0.719$. As a fraction of one
cell it stays near 0.6 at both resolutions, so it scales with the cell.

### Section 5 — player 2 really is frozen

Contrast against a two-player solve on the same grid, with the same $V_0$ and the same $\tau$
values. **This is a throwaway solve for contrast, not the real two-player result.** The real one is
M3: $101\times102^2$ then $201\times204^2$, to $\tau=6$, with horizon and grid convergence studies
and the fields kept in `m3_out/`. Both use `TwoTargetPursuit`; M2's run has no convergence study
and saves nothing.

**Check 1: $V_{\text{frozen}}\le V_{\text{two-player}}+2$ cells everywhere.** Freezing $\sigma_2=0$
is one particular thing a maximizing evader could do, so the two-player value, which takes the best
response, can only be at least as high:

$$V_{\text{two}}=\min_{\sigma_1}\max_{\sigma_2}\min_t\ell\ \ge\ \min_{\sigma_1}\min_t\ell\Big|_{\sigma_2=0}=V_{\text{frozen}}.$$

The 2 cells of slack are there because the two solves use different dissipation
($\alpha_{\phi_2}=|L|/R$ frozen, $|L|/R+1$ two-player). The test also prints the share of the grid in
$\{V\le0\}$ at $T$ for each game. This check only fails if $V_{\text{frozen}}$ is too *high*, so it
cannot see the inner-face failure of §7, which drives the frozen $V$ far too low and passes it
trivially.

**Check 2: a maneuvering evader keeps the winning zone bounded in $R$.** The outer edge of
$\{V_{\text{two}}\le0\}$ at $T$ must lie below $\bar R(0)+2\,dR$ with $\bar R(0)=3+\pi=6.1416$. The
recorded edge is about 5.98 on the odd $101^3$ grid, the same as its $\tau=0$ edge, so against a
maneuvering evader the range edge does not advance at all. The frozen front, by contrast, advances
at speed 2 to the domain edge at $R=12$. It is an $R$ bound, so $dR$ is the right tolerance unit.

Two points of care in reading it. The set that stops growing is the winning zone $\{V\le0\}$, not
$\{\ell<0\}$, which is the target set and never changes. And what is bounded is the **outer edge in
$R$**: the zone's volume can still grow with $\tau$ in the angular directions and the interior, but
levels off (growth per step decaying from 0.21% to 0.03% of the grid in the earlier record). The
test asserts the edge bound only at the final horizon; showing that the zone stops growing is the
M3 convergence test.

**How it connects to the usable part on the maximum-range face.** The usable part of a target
boundary is the portion through which player 1 can force entry against any evader behavior, and its
edge, the BUP, seeds the Layer 0 barrier. On the maximum-range face the BUP exists only for
$|\phi_2|<9.57^\circ$, the lens $O_1,d_1,e_1$ near the tip where $\bar R$ peaks at $\bar R(0)$;
elsewhere an evader can prevent entry. The winning zone's boundary is made of that usable part plus
the barrier sheets that start at its BUP, and the Layer 0 audit finds the dispersal line closing the
maximum-range zone stays within about $2\times10^{-3}$ in $R$ of the $\phi_2=0$ corner edge. So the
zone reaches only about 0.002 beyond $\bar R(0)$, below one cell, which fits M3's edge at 6.100. A
frozen evader does not evade, the face is not limited to a small usable patch, and the zone keeps
extending outward. This link is a reading of the Layer 0 and M3 records and M2 does not test it
directly; M4's tests A and E check the zero level set near that tip.

**What it shows and does not show.** Check 2 is a behavioral confirmation of what M1 verified
algebraically, that player 2 maximizes: if the evader minimized by mistake, the zone would grow with
$\tau$ instead of staying bounded. It does not show the two-player $V$ is correct to the digit; that
is M3 (convergence) and M4 (comparison with Layer 0), and it is why horizon convergence is an M3
test and not an M2 one.

---

## 6. Results at a glance

| | 61³ (cell 0.1967) | 101³ (cell 0.1180) |
|---|---|---|
| reach-front speed vs. analytic 2 | 2.016 | **2.003** |
| median shortfall of the feedback law | +0.00028 | **+0.00022** |
| 90th percentile shortfall | +0.037 | **+0.018** |
| max shortfall | +0.116 | +0.124 |
| sign of $V$ vs. simulated outcome | 232 / 232 | **230 / 230** |
| worst violation of optimality | +0.116 | **+0.067** |
| — as a fraction of one cell | 0.59 | **0.57** |

**Honest caveat on the tail.** At $101^3$ the *max* shortfall (0.124) is just above one cell
(0.118), while the median is about 500× smaller. That is why the suite asserts "max $<3$ cells"
and not "$<1$". The tail is a few trajectories near the $\phi_1=\pm\pi$ shock ridge, and it does
not shrink with refinement. If M4's test C1 shows the same trajectories failing, look at the ridge
first.

---

## 7. Known limitation: the frozen field is invalid near the inner face

Found on 2026-10-01 while building the M2 field for the explorer; recorded in
`claude/Layer1_M1_Explorer_2026-09-30.md`.

**The bound.** $V\ge-\beta=-0.785$ everywhere (§2). The frozen solve violates it:

| $\tau$ | $\min V$ | nodes > 1 cell below $-\beta$ | out to $R$ |
|---|---|---|---|
| 0.75 | $-2.6$ | 152 | 0.55 |
| 1 | $-11$ | 802 | 1.03 |
| 3 | $-7.0\times10^{3}$ | 33,630 (3.2%) | 5.16 |

(101×102² grid; table from the explorer record.) On `test_m2.py`'s own $101^3$, $T=3$
configuration: $\min V=-1.45\times10^4$, 3.3% of nodes more than 0.05 below the bound, out to
$R\approx5.3$. At $61^3$ there is no blow-up, but 7% of nodes still sit more than 0.05 below
(worst $-0.94$). M3 is unaffected ($\min V=-0.802$, within 0.017 of the bound).

**Where and why.** It starts at the inner face $R=0.2$ near $\phi_1=\phi_2=0$: nose-on, closing at
speed 2, so these states leave the domain through that face. Marching in $\tau$, that face is
effectively an *inflow* boundary (the true value there is $V(R-2\tau,0)$, from outside the
domain), and the `extrapolate` condition supplies the missing outside values by continuing the end
slope. The first error is small (about 0.125 at $\tau=0.1$), but then:

1. at the failing node $H_{\text{frozen}}=-V_R C-|V_1|+\dots$ and $\min(0,\hat H)$ is negative, so
   $V$ drops;
2. the clamp only allows decreases, so nothing pulls the value back up;
3. a lower $V$ steepens the gradient, which makes $H$ more negative, and the node keeps falling
   (positive feedback);
4. the contamination spreads outward at about the closing speed.

Diagnostic evidence: replacing the inner-face condition with a copy of the edge value kept
$\min V=-0.794$ through $\tau=1.5$ with no violations (not run to $T=3$, and not run against the
other M2 checks). Why extrapolation produces the first 0.125 is not proven.

**Why M2's tests do not see it.** No check bounds $V$ from below, and the trajectory tests drop
every sample that exits the $R$ domain, which is exactly where these states go.

**Decision (2026-10-02): M2 is left unchanged.** It is a smoke test, the failure is confined to
the frozen game near $R=0.2$, and M3 is unaffected. A lower-bound check would fail at $101^3$.

**What this means for reading the M2 field.** The explorer draws the violating nodes **grey**
and keeps them out of the color scale. Their numerical $V$ is negative, so they lie inside
$\{V\le 0\}$, and many of them are plausibly real wins (nose-on, close, frozen target). But their
values are wrong by orders of magnitude, not by a cell, so the **sign there is not certified** by
the solve. Treat the grey region as "not validated", not as "won with a slightly wrong number".

---

## 8. Concepts worth having straight

**Value is not control.** $V$ says how good the state is. The law says which way to turn.
They come from the same snapshots but the law needs $\partial V/\partial\phi_1$ at the *right
$\tau$*. A correct $V$ read at the wrong $\tau$ gave a control about 16× worse (2.04 vs 0.13).

**Two-sided checking.** (a) shows $V$ is achievable (not too low); (b) shows nothing does
better (not too high). Either half alone misses something: (a) is a weak detector of a $V$ that is
too high, because the law steers by $V$'s own gradient and may never find the lower path, while
(b) searches independently; (b) alone cannot see a $V$ that is too low, because nothing beats a
promise nobody tried to keep.

**Why $\min(0,H)$ and not $H$.** $H>0$ means following the dynamics would raise the margin, but
player 1 can always stay with what it has. $V$ therefore never increases with $\tau$.

**Why the tolerances are in cells.** A mismatch of less than one cell is below what the grid can
express, so the 90th-percentile and optimality checks are held to one cell. The median is held to
a tenth of a cell and in practice sits around 0.002 of one. See "The weighting of $\ell$, and the
cell" in §5 for what a cell is and why it is measured near $\ell=0$.

---

## 9. Hand-off

- **M4, test C1** reuses `make_policy` and the remaining-horizon read: the same trap, now with a
  maneuvering player 2.
- **M4, test B** compares $\nabla V$ with the Layer 0 costate near $H=0$, where the relative-error
  trap from M1 returns (score against the summed-term magnitude, not against $H$).
- **M5** is now a two-target reach-avoid solve (2026-10-01 decision), not the $t_1^*/t_2^*$
  arrival-time comparison.
- Grid rule from M3 for all later solves: $n_\phi$ must not be a multiple of 8
  (use 101×102 or 201×204).

---

## 10. Quick file map

```
layer1/hji.py          FrozenEvader, make_grid, solve_backward, make_policy, forward_sim
layer1/ell.py          ell, value_scale (the "cell")
layer1/test_m2.py      this file: five sections, usage test_m2.py [n_grid] [T]
layer1/solve_m2_snap.py  frozen-evader re-solve on M3's grid to tau = 6 (explorer field)
layer1/viz/ell_explorer.html   explorer with M2 and M3 fields; grey = invalid nodes
```
