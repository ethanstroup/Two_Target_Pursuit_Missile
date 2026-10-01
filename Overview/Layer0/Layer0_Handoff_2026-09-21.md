# Layer 0 Handoff — Max-Range Barrier & Explorer (2026-09-21)

**AE 8900 · Ethan Stroup.** A summary for starting a new chat. It reconstructs D&S (1989) Sec. 4.1, the maximum-range barrier and the two small closed capture zones of Fig. 8.
Full detail: `claude/Layer0_MaxRangeAudit_2026-09-17.md` (Findings 1–8).

Repo: `C:\Users\estro\Projects\AE8900\Two_Target_Pursuit_Missile\layer0` (files use CRLF line endings).

## Settled results

- **Max-range BUP.** It is two closed lenses, one on each side of φ₂ = 0, each folding at d₁ = (5.80833, 18.8775°, −9.5695°). The σ₁ switch on the lens is exactly that fold, because ∂(Eq. 32)/∂φ₁ ≡ −λ̇₁/ρ.
- **Lens control pairs** (these match Fig. 4):
  - e₁–d₁: (−1,−1)
  - d₁–O: (+1,−1)
  - e₁′–d₁′: (+1,+1)
  - d₁′–O: (−1,+1)
- **φ₂ = 0 corner edge O–e₁ is also BUP.** It is the slope-jump crease of R̄.
  - e₁ satisfies R̄₀ tan(φ₁/2) = 2, so e₁ = 36.0755°.
  - The corner costate is Eqs. (39)–(41); λ₁ ≡ 0 along the edge.
- **Corner control pairs have no switch.** O–e₁ is (−1,+1) throughout and O–e₁′ is (+1,−1). This is forced: σ₂ = +1 ⇒ λ₂ > 0 ⇒ λ̇₁ < 0 ⇒ σ₁ = −1.
  - Fig. 4's corner labels, (1,1) on f₁O and (−1,1) on Of₁′, contradict Eqs. (40), (18) and (33), and they break the figure's own mirror symmetry.
  - Eq. (42) has sgn φ₁ misplaced; it belongs outside the bracket.
- **f₁ is real, as a universal-line point.** It satisfies R̄₀ tan(φ₁/2) = 1, so f₁ = 18.496°. At f₁ the universal-line costate λ = (cos φ₁, 0, −R sin φ₁) gives H\* = R̄₀ sin φ₁ − 1 − cos φ₁ = 0.
  - That costate is 2.7% outside the corner normal cone.
  - Read literally, Eq. (42) has this same bracket, which is why it reproduces 18.5.
- **Universal line from d₁ (`universal_d1.py`).**
  - The singular control is exactly σ₁ = 0, since λ̈₁ = A·σ₁ with A ≡ −1 and no σ-free term.
  - The pair is (0,−1), not the (0,+1) Table 3 gives for f₁c₁.
  - It skims just above the surface and passes within 2e−3 of f₁.
- **Dispersal line e₁c₁O is solved exactly (`dispersal_e1c1O.py`).**
  - The missing piece was the peel-off trajectories: they leave the universal line with σ₁ = ±1.
  - e₁→c₁ is the intersection of (−1,−1) with (−1,+1); O→c₁ is the intersection of (+1,−1) with (−1,+1). The crossing is transversal, at about 55°.
  - The whole line stays within 2.2e−3 in R and 0.07° in φ₂ of the corner edge.
- **c₁ = (6.14377, 18.4861°, −0.0672°).** This is where the universal line meets the corner sheet, which is 2.5e−3 from f₁ and at retrograde time τ = 0.17268 from d₁.
  - Table 2's c₁, (5.925, 18.7, +4.78), lies *inside* T₁.
  - Retrograde R strictly increases here, so any point involving the corner family has R ≥ R̄₀.
- **Universal lines end at c₁** because they meet the dispersal line there, not because they reach the corner.

## Files added or changed (layer0/viz)

| file | what it does |
|---|---|
| `corner_family.py` | Corner-edge family, plus `f1_diagnostic()` (Eq. 42 analysis and the cone scan) |
| `universal_d1.py` | Derives the singular control, flies the d₁ universal line, runs the f₁ checks, makes the figure |
| `dispersal_e1c1O.py` | Exact 3×3 solve for the dispersal line and c₁, plus the figure |
| `fig8_zones.py` | Fig. 8 capture zones (f₁ note updated) |
| `bup_curves.py` / `.js` | New (identical twins): `corner_seeds`, `lam_corner_edge`, `d1_seed`, `c1_tau`, `integrate_universal`, `universal_lines`, `mirror` |
| `test_viz.py` | 32/32 pass; JS and Python agree to about 1e−15 |
| `barrier_explorer.html` | See below |
| `README.md` | Updated for the new explorer features |

## barrier_explorer.html features

- **corner + universal** (on by default): green trajectories from the O–e₁ and O–e₁′ edges, and thick amber universal lines from d₁ and d₁′ that stop at c₁ (labelled). The readout shows "σ₁ = 0 (singular)".
- **Segment chips**: click a chip to hide or show that piece. Lenses are split at d₁, and each chip shows its control pair. **All on** resets them, and hidden state survives rebuilds.
- **Target set** (on by default): a semi-transparent T₁ box like Fig. 3, with the φ₂ = 0 ridge edge drawn. Usable parts are shaded from Eq. (32) on the top, Eq. (46) on the bottom and Eq. (62) on the walls. The family currently shown is drawn darker. Turning it on reframes the 3-D view.

## Open items

1. Build the closed zone as a mesh and check that it is watertight.
2. Recompute the mirror zone explicitly rather than taking it on symmetry.
3. Optionally show the peel-off sheets and the dispersal line in the explorer.
4. Explain the paper's Table 2 c₁ and Table 3 entries (f₁c₁ as (0,+1); c₁O as (+1,−1)(+1,+1)).
5. Apply the same treatment to the min-range and boresight families (so far only max range has been touched).

## Working notes

- After committing to the device, check the file size on the device. One commit wrote a stale file.
- `diag_maxrange.py` uses D = 180/π, while `visualize.py` and the explorer use D = π/180.
