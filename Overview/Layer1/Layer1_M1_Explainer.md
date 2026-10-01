# Layer 1 — M1 Explainer

**AE 8900 · reference doc, written 2026-09-30**
Companion to `claude/Layer1_Plan.md` and `claude/Layer1_Progress_2026-09-14.md`. Code:
`Two_Target_Pursuit_Missile/layer1/ell.py`, `hji.py`, `test_m1.py`.

This is a plain-language walkthrough of what M1 actually checks and why, section by section,
with the real code alongside. Written to be read cold, without re-deriving anything.

---

## 1. What M1 is, and why it exists

`hj_reachability` (the JAX library doing the actual PDE solve) has never seen this specific
problem before. M1's whole job is to verify every piece handed to it — the target-set
geometry, the equations of motion, the game-theoretic Hamiltonian — against Layer 0's code,
which was independently derived and already verified straight from the Davidovitz & Shinar
paper. **Nothing in M1 integrates a PDE.** If M1 fails, a setup bug (wrong sign convention,
mis-transcribed constant, swapped min/max) is caught for free, instead of surfacing three
hours into an expensive solve as a barrier that's mysteriously wrong.

The guiding discipline: cross-check everything against an independent reference, at machine
precision where the two things being compared are supposed to be *identical*, and with a
principled tolerance only where they're allowed to differ (e.g. different summation order).

---

## 2. The math M1 is protecting

**The target set**, $T_{1\to2}$, is where player 1 can kill player 2. Its implicit surface
function:

$$\ell(x) = \max\big(|\phi_1|-\beta,\ \ \underline R(\phi_2)-R,\ \ R-\bar R(\phi_2)\big)$$

Negative inside $T_{1\to2}$, zero on its boundary, positive outside — because a max of several
terms is $\le0$ exactly when *every* term is $\le0$.

**The value function** (reachability, not a terminal-payoff game):

$$V(x,T) = \min_{\sigma_1}\max_{\sigma_2}\min_{t\in[0,T]}\ell\big(x(t)\big)$$

The inner $\min_{t}$ converts "does the trajectory ever touch the target set" into a number
(the running minimum of $\ell$ along the path is $\le0$ iff the path touches the target at
some point). The outer min-max is the ordinary adversarial game on top of that.

**The Hamiltonian** — what $\nabla V\cdot f$ reduces to once the inner min/max over the
(linear-in-control) dynamics is solved analytically:

$$H(x,\nabla V) = -V_R(\cos\phi_1+\cos\phi_2) + (V_1+V_2)\frac{L}{R} - |V_1| + |V_2|,
\qquad L=\sin\phi_1+\sin\phi_2$$

with $V_R,V_1,V_2 \equiv \partial V/\partial R, \partial V/\partial\phi_1, \partial V/\partial\phi_2$.
The $\pm|V_i|$ terms come from each player picking $\sigma_i^*=\mp\text{sign}(V_i)$ to
minimize/maximize a linear term over $|\sigma_i|\le1$.

**The PDE actually marched:**

$$\frac{\partial V}{\partial\tau} + \min\big[0, H(x,\nabla V)\big] = 0, \qquad V(x,0)=\ell(x)$$

$\tau$ is *time remaining*, not elapsed time — $\tau=0$ means no time left to maneuver, so
$V$ just equals the current margin $\ell(x)$, unimproved.

---

## 3. `ell.py` — the implementation M1 checks

```python
def _terms(xp, R, phi1, phi2):
    g_bore = xp.abs(phi1) - BETA                    # |phi_1| <= beta
    R_lo = A1 + B1 * xp.cos(phi2)                    # Eq. (8)
    R_hi = RBAR0 - xp.abs(phi2 + xp.sin(phi2))        # Eq. (9)
    g_min = R_lo - R
    g_max = R - R_hi
    w_b, w_n, w_x = _weights(xp, phi2)
    return w_b * g_bore, w_n * g_min, w_x * g_max

def _ell(xp, R, phi1, phi2):
    a, b, c = _terms(xp, R, phi1, phi2)
    return xp.maximum(a, xp.maximum(b, c))
```

- `BETA, A1, B1, RBAR0` are **imported from `layer0/barrier.py`**, never re-typed — this is
  the guard against silently losing the $\bar R_0 = 3+\pi$ (not 6.14) correction.
- The `w_b, w_n, w_x` weights (`raw` / `plan` / `sdist`) only rescale conditioning
  (how well-behaved $|\nabla\ell|$ is for the solver) — since the weights are strictly
  positive, **the sign and zero level set are mathematically untouched by the choice**. This
  is a separate, lower-stakes decision from anything M1 checks for correctness.
- Written once against a generic array module `xp`, exposed as both `ell()` (numpy, for
  testing) and `ell_jax()` (JAX, for the solver) — so the two paths cannot drift apart.

---

## 4. `test_m1.py`, section by section

### Section 0 — Environment sanity checks

Confirms `jax_enable_x64` is actually on (float32 would make every machine-precision
comparison below meaningless), that `RBAR0` really is $3+\pi$, and that `ell.py`'s constants
are literally the *same objects* as `barrier.py`'s (`is`, not `==`) — proof nothing was
re-declared.

### Section 1 — ell sign vs. `barrier.in_target`

Two sampling strategies, checked against Layer 0's already-verified `in_target` function:

- **A dense structured grid**, $181^3 = 5{,}929{,}741$ nodes (181 values each of $R,\phi_1,\phi_2$,
  every combination). 181 is deliberately *not* a multiple of 8, so $\phi_1$ never lands
  exactly on $\beta=\pi/4$ — the same alignment hazard that later caused a real bug at M3.
  Zero mismatches.
- **4,000,000 random points**, drawn uniformly. Continuous random draws land on a zero-measure
  boundary surface with ~zero probability, so this check needs no boundary-convention
  exception — a clean `mis_rand == 0`.

The one place the two are *allowed* to disagree is exactly on the boundary itself
($\ell\le0$ is the closed set; `in_target` is half-open per D&S Eq. 7) — the test explicitly
confirms every disagreement sits on an active constraint, not a real bug.

### Section 2 — ell on the target-set boundary itself

Checks something Section 1 doesn't: that $\ell$ hits **exactly zero** (to $10^{-12}$) right on
each of the three analytic boundary curves ($\underline R(\phi_2)$, $\bar R(\phi_2)$,
$\phi_1=\pm\beta$) individually, one at a time (each check isolates a single constraint, away
from corners), and that $\ell$'s sign actually flips the correct direction crossing each one.
This is what "the barrier is the zero level set" and $V(x,0)=\ell(x)$ actually rest on.

### Section 3 — Dynamics vs. `barrier.state_dot`

```python
dyn = hji.TwoTargetPursuit()
want = np.array(B.state_dot(R0, p1, p2, s1, s2))
got = np.asarray(dyn(jnp.array([R0, p1, p2]), jnp.array([s1]), jnp.array([s2]), 0.0))
```

Raw equations of motion, checked **bit-identical** (not just close) on 20,000 random points
across the full continuous control range $\sigma\in[-1,1]$ (not just the eventual bang-bang
extremes). No optimization involved yet — this is pure "did the equations get copied right."

### Section 4 — Hamiltonian vs. `barrier.hamiltonian_star` (**the M1 gate**)

The deepest check. 200,000 random $(x,\nabla V)$ pairs — with $\nabla V$ drawn from a normal
distribution, i.e. *arbitrary* gradients, not just ones a real solve would produce — comparing
Layer 0's hand-derived closed-form $H$ against the new solver's own optimization machinery
(`dyn.hamiltonian`, which internally has to *find* the optimal controls and plug back in, not
just re-evaluate a formula).

Scored correctly: not relative to $H$ itself (which vanishes identically on the barrier by
construction — dividing by that reports rounding noise as if it were a real error), but
relative to the magnitude of the summed terms:

```python
termscale = np.abs(LR * Ct) + np.abs((L1 + L2) * Lt / Rr) + np.abs(L1) + np.abs(L2)
ulps = abserr / np.spacing(termscale)
report('H == barrier.hamiltonian_star  (2e5 random (x, grad V))', ulps.max() <= 4.0, ...)
```

Max 4 ulp of disagreement — exactly what two algebraically-identical expressions summed in a
different order should produce. Bit-identical at ~91k/200k points.

**Degenerate gradients tested separately**, at tighter tolerance ($<10^{-13}$): $\lambda_1=0$,
$\lambda_2=0$, $\lambda_R=0$, $\lambda=0$ entirely. These aren't arbitrary edge cases — they're
exactly where Layer 0's BUP (boundary-of-usable-part) seeds live (range-surface seeds at
$\lambda_1=0$, boresight seeds at $\lambda_2=0$), i.e. precisely the states the Layer 0 vs.
Layer 1 cross-validation strategy depends on agreeing.

### Section 5 — Optimal feedback law vs. D&S Eqs. (21)–(22)

Checks the solver's own control-extraction (`dyn.optimal_control_and_disturbance`) actually
*finds* $\sigma_1^*=-\text{sign}(\lambda_1)$, $\sigma_2^*=+\text{sign}(\lambda_2)$ exactly
(bitwise) — this is a different, more concrete claim than Section 4's "the Hamiltonian *value*
matches." Then closes the loop:

```python
fvals = dyn(x, u, d, 0.0)                        # raw dynamics, the Section-3 call again
e = |sum(fvals * grad) - want|                    # should reproduce the closed-form H
report('H is attained at (sigma_1*, sigma_2*)', e < 1e-13, ...)
```

Plugs the extracted controls back into the raw dynamics (reusing the exact Section 3 call) and
confirms $\nabla V\cdot f$ at those controls really does equal the independently-computed $H$
— proof the pieces are correctly *wired together*, not just individually correct.

### Section 6 — The four grid traps of Plan §3

Each asserted directly against the actual solver grid object, not just hoped for:

1. **Periodicity** — `g.boundary_conditions == [False, True, True]` for $(R,\phi_1,\phi_2)$;
   confirmed the periodic angle grids run $[-\pi,\pi)$ without duplicating $+\pi$.
2. **$R\to0$ singularity** — $R_{\min}$ confirmed below the smallest possible
   $\underline R(\phi_2)$, $R_{\max}$ above the largest $\bar R(\phi_2)$, and the inner
   boundary condition confirmed to literally be `extrapolate`, not periodic/Dirichlet.
   $\ell$ confirmed continuous across both periodic seams to $<10^{-8}$.
3. **Real kinks are asserted to *exist*** — e.g. $\bar R$'s corner at $\phi_2=0$: one-sided
   slopes checked to differ by $>1.0$. A smooth $\bar R$ here would mean the target set had
   been accidentally rounded off.
4. **Dissipation bounds** — the solver's own Lax–Friedrichs coefficients checked against the
   analytic bounds ($\le2$ for $R$, $=|L|/R+1$ per angle, capped by $2/R_{\min}+1$).

### Section 7 — ell on an actual solver grid

Builds a real $101\times100\times100$ grid (the literal style M3 will use) and evaluates
$\ell$ on every node — i.e. generates the actual $V(x,0)$ array. Confirms float64, finite
everywhere, JAX and numpy versions bit-identical on this real grid, both signs present (target
set actually resolved at this resolution), and the measured Lipschitz constant in $R$ matches
the analytic value for whichever weighting is active.

### Section 8 — Conditioning of ell

Measures $|\nabla\ell|$ near the zero level set under all three weightings (`raw`/`plan`/`sdist`),
reporting the table that motivated defaulting to `sdist` (see `claude/Layer1_Amendment_2026-09-15.md`).
Not a correctness gate — the zero level set is weight-invariant by construction — this is
purely "does the chosen weighting actually achieve Plan §2.1's own stated goal of
$|\nabla\ell|\approx1$."

---

## 5. Concepts worth having straight

**Structured grid vs. random sampling — why both.** A regular grid is exhaustive at the
specific resolution-like locations that mirror the real solver, but its evenly-spaced
coordinates can *accidentally align* with special values in the problem (e.g. $\beta=\pi/4$
is exactly $1/8$ of a circle, so a grid resolution that's a multiple of 8 lands a node exactly
there). Random sampling can't accidentally align with anything — it checks correctness
generically, at arbitrary positions, and it also sidesteps the boundary-convention ambiguity
(a continuous random draw essentially never lands exactly on a zero-measure surface).

**Why kinks are a real problem, and how the solver handles them.** $\ell$ has genuine
corners (not smoothed) wherever the max() switches which constraint is active. At a kink, a
finite-difference stencil that straddles it (like a centered difference through $|x|$ at
$x=0$) can compute a systematically *wrong* slope, not just a noisy one. The fix: compute
both one-sided differences $D^-,D^+$ separately, and combine them via a Lax–Friedrichs
numerical Hamiltonian that explicitly penalizes disagreement between the two sides:

$$\hat H \approx H\Big(x,\tfrac{D^-+D^+}{2}\Big) - \tfrac12\sum_i\alpha_i(D_i^+-D_i^-)$$

This is provably convergent to the correct **viscosity solution** even where no classical
derivative exists — but the injected dissipation is a real (small) cost, paid every step, at
every node exactly on a kink. A whole *line* of nodes landing on a kink (the $n_\phi$
multiple-of-8 bug) pays that cost systematically, which is why it compounded into a
measurable error at M3 rather than averaging out.

**Why "relative to $H$" is the wrong error metric.** $H$ vanishes identically on the
semipermeable surface — that's the barrier this whole layer exists to find. Dividing an
ordinary rounding-level absolute error by a value that's supposed to be exactly zero produces
a huge, meaningless relative number. Score against the magnitude of the summed terms instead.
This trap bit M1's own Hamiltonian test on the first attempt (3.6e-12 relative error, 1.4e-14
absolute — a completely normal rounding error, misread as a bug), and it's flagged again at
M4's test B for exactly the same reason.

---

## 6. Quick file map

```
layer1/ell.py       implicit surface function T_{1->2}; raw/plan/sdist weighting
layer1/hji.py        hj_reachability setup: TwoTargetPursuit dynamics, make_grid, make_policy
layer1/test_m1.py    this file — formulation gate, sections 0-8, now with header comments
layer1/test_m2.py    one-player smoke test (M2)
```
