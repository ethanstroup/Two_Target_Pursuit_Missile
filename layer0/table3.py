"""
table3.py -- Table 3 of Davidovitz & Shinar (1989), "Singular lines of the pursuit-evasion
game (1 = pursuer)".

Transcribed 2026-10-07 from p. 156 of the paper
(Overview/A. Davidovitz and J. Shinar, Two-target game model ... 1989.pdf).
This module holds the data plus lookups against validate_table2.TABLE2; nothing in it is
derived.  ProblemStatement Sec. 9 applies: every row is a claim to re-derive, not ground truth.
Rows that Layer 0 has already contradicted, or that are inconsistent as printed, carry a flag.

ROW FORMAT   (a, b, kind, strategies, player, flag)
  a, b        endpoint names, spelled as in validate_table2.TABLE2
              ('Qt_1' is Q-bar_1, 'Wt_1' is W-bar_1, 'k_1^n' is k_1 with superscript n)
  kind        'universal' | 'dispersal' | 'semidispersal' | 'switch' |
              'switch trajectory' | 'equivocal' | 'commuting'
  strategies  (sigma_1, sigma_2) pairs as printed:
                universal, commuting      ((s1, s2),)            0 marks the singular control
                dispersal, semidispersal  ((s1, s2), (s1, s2))   the two families that meet
                switch, switch trajectory ((before), (after))    printed with an arrow
                equivocal                 (('hat', +1),) ...     'hat' is the printed sigma-hat
  player      the Remarks column: 'pursuer' or 'evader'
  flag        '' or a note

The paper prints two consecutive blocks both titled "Switch lines"; the second block
(m_1 Z_1, a_1 A_1, M_1 n_1) is kept in order after the first.  Only unprimed lines are
printed; the primed (mirror) lines follow from (R, phi_1, phi_2) -> (R, -phi_1, -phi_2) with
both controls negated.

Usage:  python3 layer0/table3.py [--r-mask 0.45]
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_table2 as VT                  # noqa: E402  (guarded main; safe to import)

D = np.pi / 180.0

TABLE3 = [
    # ---- universal lines
    ('a_1', 'E_1', 'universal', ((-1, 0),), 'evader', ''),
    ('J_1', 'D_1', 'universal', ((-1, 0),), 'evader', ''),
    ('f_1', 'c_1', 'universal', ((0, +1),), 'pursuer',
     'Layer 0 (viz/universal_d1.py) finds (0,-1) here; Layer0_Handoff_2026-09-21 open item 4'),
    ('c_1', 'd_1', 'universal', ((0, -1),), 'pursuer', ''),
    # ---- dispersal lines
    ('b_1', 'G_1', 'dispersal', ((-1, -1), (-1, +1)), 'evader', ''),
    ('C_1', 'H_1', 'dispersal', ((-1, -1), (-1, +1)), 'evader', ''),
    ('C_1', 'B_1', 'dispersal', ((-1, -1), (-1, +1)), 'evader', ''),
    ('e_1', 'c_1', 'dispersal', ((-1, -1), (-1, +1)), 'evader', ''),
    ('c_1', 'O_1', 'dispersal', ((+1, -1), (+1, +1)), 'evader',
     'printed "c_1 0", read as c_1 O_1 (Fig. 8 dispersal line e_1 c_1 O); Layer 0 '
     '(viz/dispersal_e1c1O.py) finds (+1,-1) with (-1,+1) on O-c_1; Handoff open item 4'),
    ('k_1^1', 'k_1^0', 'dispersal', ((-1, -1), (-1, +1)), 'evader', ''),
    # ---- semidispersal lines
    ('E_1', 'b_1', 'semidispersal', ((-1, -1), (-1, +1)), 'evader', ''),
    ('G_1', 'D_1', 'semidispersal', ((-1, +1), (-1, -1)), 'evader', ''),
    ('k_1^5', 'k_1^3', 'semidispersal', ((+1, -1), (+1, +1)), 'evader', ''),
    ('k_1^0', 'M_1', 'semidispersal', ((-1, -1), (-1, +1)), 'evader', ''),
    # ---- switch lines, first block
    ('H_1', 'u_1', 'switch', ((+1, +1), (-1, +1)), 'pursuer', ''),
    ('u_1', 'k_1^3', 'switch', ((+1, -1), (-1, -1)), 'pursuer', ''),
    ('k_1^5', 'k_1^6', 'switch', ((+1, -1), (-1, -1)), 'pursuer', ''),
    ('k_1^1', 'g_1', 'switch', ((+1, +1), (-1, +1)), 'pursuer', ''),
    ('Qt_1', 'J_1', 'switch', ((-1, +1), (-1, -1)), 'evader', ''),
    ('u_1', 'I_1', 'switch', ((+1, -1), (+1, +1)), 'evader', ''),
    ('u_1', 'k_1^2', 'switch', ((-1, -1), (-1, +1)), 'evader', ''),
    ('k_1^4', 'k_1^7', 'switch', ((+1, -1), (+1, +1)), 'evader', ''),
    ('k_1^2', 'k_1', 'switch', ((+1, -1), (+1, +1)), 'evader',
     'k_1 = (0.25, 0.0, +/-180) is in Table 2 but missing from validate_table2.TABLE2; '
     'supplied by EXTRA_POINTS'),
    # ---- switch lines, second block
    ('m_1', 'Z_1', 'switch', ((-1, +1), (-1, -1)), 'evader', ''),
    ('a_1', 'A_1', 'switch', ((-1, -1), (-1, +1)), 'evader', ''),
    ('M_1', 'n_1', 'switch', ((+1, -1), (-1, +1)), 'evader',
     'as printed BOTH components change, though the row is labeled evader; check Figs. 11-12'),
    # ---- switch trajectories
    ('k_1^6', 'k_1^4', 'switch trajectory', ((+1, -1), (-1, -1)), 'pursuer', ''),
    ('k_1^7', 'n_1', 'switch trajectory', ((-1, -1), (-1, +1)), 'evader', ''),
    ('I_1', 'P_1', 'switch trajectory', ((+1, -1), (-1, -1)), 'evader',
     'as printed sigma_1 changes, though the row is labeled evader; check Fig. 10'),
    # ---- equivocal lines
    ('H_1', 'Wt_1', 'equivocal', (('hat', +1),), 'pursuer', ''),
    ('k_1^1', 'w_1', 'equivocal', (('hat', +1),), 'pursuer', ''),
    ('Wt_1', 'I_1', 'equivocal', ((+1, 'hat'),), 'evader', ''),
    ('w_1', 'k_1^4', 'equivocal', ((+1, 'hat'),), 'evader', ''),
    # ---- commuting line
    ('S_1', 'U_1', 'commuting', ((0, -1),), 'pursuer', 'constructed in viz/commuting_s1u1.py'),
]

# Table 2 prints k_1 = (0.25, 0.0, +/-180.0) between h_1 and k_1^0; validate_table2.TABLE2
# omits it.  It is supplied here rather than edited into validate_table2.py so that
# file's 59-point counts, quoted throughout the records, stay valid.
EXTRA_POINTS = {'k_1': (0.25, 0.0, 180.0)}

# Table 2 entries that Layer 0 has found to be off.
POINT_FLAGS = {
    'c_1': 'Table 2 c_1 lies inside T_1; Layer 0 places c_1 at (6.14377, 18.4861, -0.0672) '
           '(Layer0_Handoff_2026-09-21)',
}


def points():
    """name -> (R, phi_1, phi_2), angles in radians, for Table 2 plus EXTRA_POINTS."""
    pts = {n: (R, a1 * D, a2 * D) for n, R, a1, a2 in VT.TABLE2}
    for n, (R, a1, a2) in EXTRA_POINTS.items():
        pts.setdefault(n, (R, a1 * D, a2 * D))
    return pts


def unresolved():
    """Endpoint names that are not Table 2 points.  Should be empty."""
    pts = points()
    return sorted({n for row in TABLE3 for n in row[:2] if n not in pts})


def endpoints(row, pts=None):
    """The two endpoint coordinates of a row."""
    pts = points() if pts is None else pts
    return pts[row[0]], pts[row[1]]


def above_mask(row, r_mask=0.45, pts=None):
    """True if BOTH endpoints lie at R >= r_mask (the M3/M4 retained domain)."""
    a, b = endpoints(row, pts)
    return a[0] >= r_mask and b[0] >= r_mask


def select(kind=None, player=None):
    """Rows of one kind and/or one player."""
    return [r for r in TABLE3
            if (kind is None or r[2] == kind) and (player is None or r[4] == player)]


def fmt_strategies(kind, s):
    """Strategies back in the printed form, e.g. '(+1,-1) -> (-1,-1)' or '(-1,-1)(-1,+1)'."""
    def pair(p):
        return '(%s)' % ','.join(v if isinstance(v, str) else ('%+d' % v if v else '0') for v in p)
    sep = ' -> ' if kind in ('switch', 'switch trajectory') else ''
    return sep.join(pair(p) for p in s)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--r-mask', type=float, default=0.45)
    a = ap.parse_args()
    pts = points()
    miss = unresolved()
    print('Table 3: %d rows; unresolved endpoint names: %s' % (len(TABLE3), miss or 'none'))
    print('%-14s %-18s %-22s %-8s %-36s %s' % ('line', 'kind', 'strategies', 'player',
                                                 'endpoints (R, phi_1, phi_2 deg)', 'R>=mask'))
    n_in = 0
    for row in TABLE3:
        if row[0] in miss or row[1] in miss:
            continue
        pa, pb = endpoints(row, pts)
        ok = above_mask(row, a.r_mask, pts)
        n_in += ok
        print('%-14s %-18s %-22s %-8s (%.3f,%.1f,%.1f)-(%.3f,%.1f,%.1f)  %s'
              % (row[0] + ' ' + row[1], row[2], fmt_strategies(row[2], row[3]), row[4],
                 pa[0], pa[1] / D, pa[2] / D, pb[0], pb[1] / D, pb[2] / D, 'yes' if ok else '-'))
        if row[5]:
            print('%14s   note: %s' % ('', row[5]))
    print('\n%d of %d rows have both endpoints at R >= %.2f' % (n_in, len(TABLE3), a.r_mask))
    for n, f in POINT_FLAGS.items():
        print('point flag  %s: %s' % (n, f))


if __name__ == '__main__':
    main()
