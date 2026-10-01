# The Two Small Maximum-Range Capture Zones — how to see them

**AE 8900 · Layer 0 · 2026-09-17 · Ethan Stroup**
Completes `claude/Layer0_MaxRangeAudit_2026-09-17.md`. The audit concluded the zones
"cannot be bounded". That is true of the full three-dimensional winning-zone boundary and
**not** true of what Fig. 8 actually shows — read against the paper itself (p. 149), the
zones are computable now, and are.

---

## 1. Fig. 8 has no R axis

Read from the source page: Fig. 8's axes are φ₁ (vertical) and φ₂ (horizontal, increasing
to the left), both spanning ±π/4. **It is a pure (φ₂, φ₁) projection of the head-on
region.** The "two small closed capture zones" are closed *in that projection*.

Two consequences:

- They will never appear as a closed thing in a 3-D view of the bundle, because the object
  that closes is a projected region, not a surface in (R, φ₁, φ₂).
- The region is only ~19° wide in φ₂ and ~72° tall in φ₁, at τ of order 0.4. At **τ = 6**
  the trajectories have wound through several hundred degrees — the explorer's own axes
  were reading to φ₁ = 524° — so the structure is three orders of magnitude off-scale. That
  alone explains an apparently empty picture.

## 2. What bounds each zone, and why it is computable

| piece | status |
|---|---|
| the (BUP)₁ lens **e₁ – d₁ – O**, Eq. (32) = 0 | solved exactly |
| the corner edge **O – f₁ – e₁**, φ₂ = 0 | known in closed form: it is where R̄ = R̄₀ − \|φ₂ + sin φ₂\| has its slope jump, ±2 |

Those two arcs share both endpoints and enclose the zone. And the region they enclose is
exactly the usable part of the maximum-range surface on that lobe — verified by sign test:

```
Eq. (32) at (φ₂ = −5°, φ₁ = 18°), inside  : −0.1508   (usable)
Eq. (32) at (φ₂ = −5°, φ₁ = 40°), outside : +0.2869   (not usable)
```

Projected area of one zone: **231 deg²**.

So the zone is filled by solving, at each φ₂, for the two roots of Eq. (32) and shading
between them. Exact, not a pixel test. Everything needed was already in `barrier.py`.

## 3. What is still genuinely missing

Fig. 8 also carries the **dispersal line e₁c₁O** where the two trajectory families meet, the
two **universal lines of player 1** terminating at d₁ and f₁, and their junction **c₁**.
Those still require the φ₂ = 0 corner family, which is not seeded — the audit's finding
stands unchanged.

A test tightened since the audit confirms this rather than assuming it. Sweeping the
tolerance on the 3-D intersection of the two lens lobes:

| tol | points | φ₁ span | \|φ₂\| max | R span |
|---|---|---|---|---|
| 0.020 | 1489 | [−3.84°, 4.37°] | 0.546° | 6.066 – 6.264 |
| 0.010 | 577 | [−2.00°, 2.54°] | 0.266° | 6.103 – 6.203 |
| 0.005 | 215 | [−0.95°, 1.30°] | 0.138° | 6.123 – 6.172 |
| 0.002 | 56 | [−0.32°, 0.45°] | 0.057° | 6.135 – 6.153 |

The set **collapses onto a point** as the tolerance shrinks — φ₁ → 0, R → 6.14, which is O₁,
the endpoint the two mirror lenses already share. It does not converge onto a curve
spanning φ₁ = 0 → 36.07°, which is what the dispersal line e₁c₁O would be. The two lens
families do not meet along a dispersal line; the missing corner family is the other half of
that intersection.

Those pieces are therefore left **off** the figure rather than sketched in.

## 4. How to look at it

**In the explorer** — a `Fig. 8 view` button now sets family = max range, τ = 0.40, frames
the (φ₂, φ₁) face to ±12° × ±45° with φ₁ increasing upward as printed, and turns the zone
shading on. A `capture zones` toggle controls the shading independently; it draws only for
the maximum-range family, since that is the only one these zones belong to.

**As a figure** — `python3 layer0/viz/fig8_zones.py` → `layer0/viz/figs/fig8_capture_zones.png`.
Both zones shaded, the BUP lens, the φ₂ = 0 corner edge, barrier trajectories at τ ≤ 0.40,
and O, e₁, e₁′, d₁, d₁′, f₁, f₁′ marked. The points land where Table 2 puts them.

## 5. Why this was not obvious from the audit

The audit asked whether the *pieces* of the construction exist and correctly found that half
of them do not. It did not ask what Fig. 8 draws. Reading the figure settles that the picture
is a projection, and a projection needs far less than the full assembly: two arcs that share
their endpoints, both of which were already exact. The audit's warning about projection
artefacts still applies to *intersection tests* — 102 apparent contacts in projection versus
0 in full 3-D — but drawing a projected region is not an intersection test.
