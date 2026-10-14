"""
validate_table2.py -- acceptance test of the Layer 0 reconstruction against
Table 2 of Davidovitz & Shinar (1989), "Coordinates of significant points".

Table 2 is the only hard numerical ground truth the paper publishes.  Many of
its points lie on surfaces or curves that the equations determine exactly; those
are a genuine acceptance test.  The rest are interior features (universal-line
endpoints, dispersal-line junctions, switch-line crossings) that only fall out
of the full barrier construction, and are reported as unplaced rather than
quietly ignored.

Usage:  python3 validate_table2.py
"""

import numpy as np
import barrier as B

D = np.pi / 180.0

# ---------------------------------------------------------------------------
# Table 2, transcribed from p. 155.  (R, phi_1 deg, phi_2 deg)
# ---------------------------------------------------------------------------
TABLE2 = [
    ('A_1',  3.0,    45.0,   180.0),
    ('B_1',  6.1420, 45.0,     0.0),
    ('C_1',  4.3,   113.87,  -25.27),
    ('D_1',  3.724,  83.86,   23.71),
    ('E_1',  2.233,  85.45,  129.74),
    ('F_1',  2.69,   69.8,   157.07),
    ('G_1',  3.437,  74.5,    47.16),
    ('H_1',  0.55,  128.52, -143.79),
    ('I_1',  0.55,  -36.21,   51.28),
    ('J_1',  1.7214, 45.01,   88.87),
    ('K_1',  0.7213, 45.0,   -55.17),
    ('M_1',  0.25,   45.0,   180.0),
    ('N_1',  0.279,  45.0,  -154.6),
    ('O_1',  6.1416,  0.0,     0.0),
    ('P_1',  2.628,  72.75,  153.96),
    ('Q_1',  1.707,  45.0,    90.0),
    ('Qt_1', 1.705,  45.0,    89.5),
    ('S_1',  1.468,  47.24,  132.76),
    ('U_1',  1.721,  91.14,  134.99),
    ('V_1',  0.412,  45.0,   117.43),
    ('Wt_1', 0.148,  49.49,  130.51),
    ('Y_1',  3.01,   45.0,   174.5),
    ('Z_1',  0.85,   45.0,     0.0),
    ('a_1',  2.98,   49.68,  171.4),
    ('b_1',  2.44,   79.58,  123.43),
    ('c_1',  5.925,  18.7,     4.78),
    ('d_1',  5.808,  18.88,   -9.56),
    ('e_1',  6.142,  36.07,    0.0),
    ('f_1',  6.142,  18.5,     0.0),
    ('g_1',  0.267,  45.0,  -160.9),
    ('h_1',  0.535,  45.0,    92.92),
    ('k_1^0', 0.238, 40.03,  175.05),
    ('k_1^1', 0.228, 30.76,  163.08),
    ('k_1^2', 0.244, 35.9,   154.58),
    ('k_1^3', 0.244, 25.45,  144.14),
    ('k_1^4', 0.227, 17.1,   149.42),
    ('k_1^5', 0.254, 10.46,  135.4),
    ('k_1^6', 0.257,  2.63,  132.6),
    ('k_1^7', 0.267, -19.08, 135.0),
    ('k_1^8', 0.2503, 45.0,  177.37),
    ('m_1',  0.847,  45.0,     8.05),
    ('n_1',  0.255,  45.0,   179.15),
    ('p_1',  0.721, -31.81,   55.46),
    ('q_1',  0.381,  45.0,  -124.34),
    ('u_1',  0.244,  33.5,   146.5),
    ('v_1',  0.543,  19.31,   91.28),
    ('w_1',  0.227,  24.1,   155.9),
    ('alpha', 3.29,  63.12,   69.12),
    ('beta',  4.649, 45.0,    45.0),
    ('gamma', 1.414, 45.0,    45.0),
    ('delta', 4.649, 45.0,   -45.0),
    ('eps',   0.79, 131.94, -131.94),
    ('zeta_1',5.149, 59.19,   20.19),
    ('eta',   0.762, 45.0,   -45.0),
    ('mu_1',  4.649, 45.0,    24.63),
    ('rho_1', 5.686, 77.03,   -6.86),
    ('nu',    0.762, 45.0,    45.0),
    ('beta_0',0.85,   0.0,     0.0),
    ('tau',   2.495, 53.34,   53.34),
]


# ---------------------------------------------------------------------------
# Candidate surfaces / curves a Table 2 point may lie on.  Each returns the
# residual in R (or in the natural units of the defining equation).
# ---------------------------------------------------------------------------

def tests(R, p1, p2):
    L = np.sin(p1) + np.sin(p2)
    out = {}
    out['max-range surface  R = Rbar(phi_2), Eq. (9)'] = R - B.R_hi(p2)
    out['min-range surface  R = Runder(phi_2), Eq. (8)'] = R - B.R_lo(p2)
    if abs(abs(p1) - B.BETA) < 1e-3:
        out['boresight BUP  R = (sin p1 + sin p2) sign p1, Eq. (62)'] = R - L * np.sign(p1)
    # BUP equalities are conditions on the angles alone.  Both are meaningless
    # at phi_2 = 0, where sign(phi_2) is undefined and the outer normal is
    # genuinely discontinuous (the paper flags this in Sec. 3.1 and handles it
    # with the corner conditions Eqs. 38-42), so exclude that line.
    if abs(p2) > 1e-4:
        out['max-range BUP, Eq. (32) = 0'] = B.up_maxrange(p1, p2) / max(B.R_hi(p2), 1e-6)
        out['min-range BUP, Eq. (46) = 0'] = B.up_minrange(p1, p2) / max(B.R_lo(p2), 1e-6)
    out['R = 2 sin(phi_1), Sec. 3.4 (line beta-nu)'] = R - 2 * np.sin(p1)
    return out


def main():
    print('=' * 96)
    print('Table 2 acceptance test   (Rbar_0 = 3 + pi = %.6f)' % B.RBAR0)
    print('=' * 96)
    print('%-8s %8s %8s %8s   %-52s %10s' %
          ('point', 'R', 'phi_1', 'phi_2', 'lies on', 'residual'))
    print('-' * 96)

    placed, unplaced = [], []
    # Table 2 prints 1-4 decimals on R and 1-2 on the angles; a point is taken
    # as lying on a surface if the residual is within what that rounding, plus
    # the angular rounding propagated through the surface, can explain.
    for name, R, d1, d2 in TABLE2:
        p1, p2 = d1 * D, d2 * D
        res = tests(R, p1, p2)
        best = min(res.items(), key=lambda kv: abs(kv[1]))
        # tolerance: 5e-4 in R from the table's own printing, plus the angular
        # 0.005 deg rounding pushed through a slope of at most ~2.
        tol = 2.5e-3
        if abs(best[1]) <= tol:
            placed.append((name, best[0], best[1]))
            print('%-8s %8.4f %8.2f %8.2f   %-52s %10.2e' %
                  (name, R, d1, d2, best[0], best[1]))
        else:
            unplaced.append((name, best[0], best[1]))
            print('%-8s %8.4f %8.2f %8.2f   %-52s %10.2e' %
                  (name, R, d1, d2, '(interior feature - not on a target surface)', best[1]))

    print('-' * 96)
    print('%d of %d Table 2 points lie on a surface the equations determine, '
          'to within table precision.' % (len(placed), len(TABLE2)))
    print()

    # ---------------------------------------------------------------------
    # Points determined by a SYSTEM of two equations -- the sharpest tests,
    # because nothing is being fitted: solve, then compare.
    # ---------------------------------------------------------------------
    print('=' * 96)
    print('Points determined by solving the equations, compared with Table 2')
    print('=' * 96)

    checks = []

    # d_1: on the maximum-range BUP, Eq. (32) = 0, where lambdadot_1f = 0, Eq. (37) = 0.
    def sys_d1(v):
        p1, p2 = v
        Rb = B.R_hi(p2)
        e32 = B.up_maxrange(p1, p2)
        e37 = Rb * np.sin(p1) + (1 + np.cos(p2)) * np.cos(p1) * np.sign(np.sin(p2))
        return np.array([e32, e37])

    from scipy.optimize import fsolve
    sol = fsolve(sys_d1, [20 * D, -10 * D], full_output=False)
    checks.append(('d_1  (Eq. 32 = 0 and Eq. 37 = 0)',
                   (B.R_hi(sol[1]), sol[0] / D, sol[1] / D), (5.808, 18.88, -9.56)))

    # Q_1: on the off-boresight BUP where Eq. (65) changes sign, cos phi_2 = 0.
    p2 = np.pi / 2
    checks.append(('Q_1  (boresight BUP at cos phi_2 = 0)',
                   (np.sin(B.BETA) + np.sin(p2), 45.0, 90.0), (1.707, 45.0, 90.0)))

    # N_1, g_1: minimum-range BUP, Eq. (46) = 0, at the boresight limit phi_1 = beta.
    f = lambda x: B.up_minrange(B.BETA, x)
    grid = np.linspace(-np.pi + 1e-6, np.pi - 1e-6, 4001)
    vals = f(grid)
    roots = [B._bisect(f, grid[i], grid[i + 1]) for i in range(len(grid) - 1)
             if vals[i] * vals[i + 1] < 0]
    roots = sorted(r for r in roots if r is not None)
    for r in roots:
        for nm, want in (('N_1', (0.279, 45.0, -154.6)), ('g_1', (0.267, 45.0, -160.9)),
                         ('h_1', (0.535, 45.0, 92.92))):
            if abs(r / D - want[2]) < 3.0:
                checks.append(('%s  (Eq. 46 = 0 at phi_1 = beta)' % nm,
                               (B.R_lo(r), 45.0, r / D), want))

    # e_1: limit of the maximum-range BUP as phi_2 -> 0^-.
    r = B.bup_maxrange(-1e-7)
    if r:
        checks.append(('e_1  (max-range BUP, phi_2 -> 0)',
                       (B.R_hi(0.0), max(abs(x) for x in r) / D, 0.0), (6.142, 36.07, 0.0)))

    # gamma: phi_1 = phi_2 = beta on the line beta-nu, R = 2 sin beta (Sec. 3.4).
    checks.append(('gamma  (Sec. 3.4: phi_1 = phi_2 = beta, R = 2 sin beta)',
                   (2 * np.sin(B.BETA), 45.0, 45.0), (1.414, 45.0, 45.0)))

    print('%-46s %-26s %-26s' % ('point (defining conditions)', 'solved', 'Table 2'))
    print('-' * 96)
    worst = 0.0
    for nm, got, want in checks:
        dR = abs(got[0] - want[0])
        d1 = abs(got[1] - want[1])
        d2 = abs(got[2] - want[2])
        worst = max(worst, dR)
        print('%-46s %7.4f %8.2f %8.2f   %7.4f %8.2f %8.2f   dR=%.1e dphi=%.2f deg'
              % (nm, got[0], got[1], got[2], want[0], want[1], want[2],
                 dR, max(d1, d2)))
    print('-' * 96)
    print('worst |dR| over the solved points: %.2e' % worst)
    print()

    print('Unplaced (%d) -- interior barrier features, reachable only from the full'
          % len(unplaced))
    print('construction, not from the target-set equations alone:')
    print('   ' + ', '.join(n for n, _, _ in unplaced))


if __name__ == '__main__':
    main()
