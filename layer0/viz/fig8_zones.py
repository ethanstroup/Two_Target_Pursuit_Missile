"""
fig8_zones.py -- the two small closed maximum-range capture zones, D&S Fig. 8.

Fig. 8 is a (phi_2, phi_1) projection of the head-on region. There is no R axis
on it: the "two small closed capture zones" are closed *in that projection*.
That is why they are invisible in a 3-D view of the bundle, and doubly invisible
at a large retrograde time -- by tau = 6 the trajectories have wound through
several hundred degrees and the structure Fig. 8 shows is 19 degrees wide.

Each zone is bounded by

    the (BUP) lens   e_1 - d_1 - O    Eq. (32) = 0, solved
    the corner edge  O - f_1 - e_1    phi_2 = 0, where Rbar has its slope jump

and the region they enclose is exactly {Eq. (32) < 0} -- the usable part of the
maximum-range surface on that lobe. So the zone is filled here by solving, at
each phi_2, for the two roots of Eq. (32) and shading between them. Exact, not a
pixel test.

What Fig. 8 has that this does not: the dispersal line e_1 c_1 O where the two
trajectory families meet, the two universal lines of player 1 terminating at d_1
and f_1, and their junction c_1. The corner family is now seeded -- see
corner_family.py -- but the two families touch only at their shared endpoints O
and e_1, so the dispersal line is still not there. f_1 is marked below only
because Table 2 lists it: on the paper's own corner costate lambda_1-dot never
vanishes on this segment, and 18.5 deg is reproduced exactly by Eq. (42) read
with its sign(phi_1) misplaced. See Finding 6 of
claude/Layer0_MaxRangeAudit_2026-09-17.md. Nothing is sketched in.

Usage:  python3 layer0/viz/fig8_zones.py [out.png] [--tau 0.40]
"""

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import barrier as B
import bup_curves as C

D = np.pi / 180.0
BLUE, RED, GREEN = '#1f5fa8', '#c1442a', '#1a7f4b'

plt.rcParams.update({'font.size': 9, 'figure.dpi': 140, 'savefig.dpi': 140,
                     'axes.grid': True, 'grid.alpha': 0.30, 'grid.color': '0.74',
                     'axes.edgecolor': '0.22', 'axes.linewidth': 1.2,
                     'axes.labelcolor': '0.06', 'axes.labelweight': 'semibold',
                     'xtick.color': '0.16', 'ytick.color': '0.16',
                     'xtick.major.width': 1.1, 'ytick.major.width': 1.1})


def zone_band(sgn, n=400):
    """The two Eq. (32) roots at each phi_2 on one lobe: the zone's extent."""
    xs, lo, hi = [], [], []
    for i in range(n + 1):
        q = sgn * (1e-4 + 0.1675 * i / n)
        r = B.bup_maxrange(q)
        if len(r) < 2:
            continue
        xs.append(q / D)
        lo.append(min(r) / D)
        hi.append(max(r) / D)
    return np.array(xs), np.array(lo), np.array(hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out', nargs='?', default=os.path.join(HERE, 'figs',
                                                           'fig8_capture_zones.png'))
    ap.add_argument('--tau', type=float, default=0.40)
    ap.add_argument('--nseed', type=int, default=55)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    seeds, _ = C.seeds('max', nseed=a.nseed)
    fig, ax = plt.subplots(figsize=(7.4, 6.6))

    for sgn, col in ((-1, BLUE), (+1, RED)):
        xs, lo, hi = zone_band(sgn)
        ax.fill_between(xs, lo, hi, color=col, alpha=0.18, lw=0, zorder=2)

    # barrier trajectories, at the retrograde length Fig. 8 is drawn at
    for bi, br in enumerate(seeds):
        col = BLUE if br[0][2] < 0 else RED
        for y in br:
            tr = B.integrate_retrograde(np.asarray(y), tau_max=a.tau, dt=5e-4)
            ax.plot(tr['phi2'] / D, tr['phi1'] / D, lw=0.6, color=col,
                    alpha=0.55, zorder=3)

    for br in seeds:
        ax.plot([y[2] / D for y in br], [y[1] / D for y in br],
                lw=2.6, color='#111', zorder=6)

    ax.plot([0, 0], [0, 36.07], color=GREEN, lw=2.6, ls=(0, (6, 3)), zorder=7)
    ax.plot([0, 0], [0, -36.07], color=GREEN, lw=2.6, ls=(0, (6, 3)), zorder=7)

    pts = [('$O$', 0.0, 0.0, '#111'), ('$e_1$', 0.0, 36.07, '#111'),
           ('$e_1\'$', 0.0, -36.07, '#111'),
           ('$d_1$', -9.56, 18.88, '#111'), ('$d_1\'$', 9.56, -18.88, '#111'),
           ('$f_1$', 0.0, 18.50, GREEN), ('$f_1\'$', 0.0, -18.50, GREEN)]
    for nm, q, p1, col in pts:
        ax.plot(q, p1, 'o', ms=6, mfc=col, mec='w', mew=1.0, zorder=9)
        ax.annotate(nm, (q, p1), textcoords='offset points', xytext=(7, 5),
                    fontsize=10, color=col, zorder=10)

    ax.axhline(45, color='0.45', lw=0.9)
    ax.axhline(-45, color='0.45', lw=0.9)
    ax.annotate(r'$B_1$:  $\phi_1=\beta$', (-11.6, 45), textcoords='offset points',
                xytext=(0, 4), fontsize=8.5, color='0.35', ha='left')

    ax.set_xlim(12, -12)
    ax.set_ylim(-50, 50)
    ax.set_xlabel(r'$\phi_2$  [deg]   (increasing to the left, as printed)')
    ax.set_ylabel(r'$\phi_1$  [deg]')
    ax.set_title('The two small closed maximum-range capture zones\n'
                 'D&S Fig. 8, head-on region, '
                 r'$\tau \leq %.2f$' % a.tau, fontsize=10.5)

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Line2D([], [], color='#111', lw=2.6, label=r'(BUP)$_1$ lens, Eq. (32) = 0'),
        Line2D([], [], color=GREEN, lw=2.6, ls=(0, (6, 3)),
               label=r'$\phi_2=0$ corner edge $O$–$f_1$–$e_1$'),
        Patch(facecolor=BLUE, alpha=0.30, label=r'capture zone, $\phi_2<0$'),
        Patch(facecolor=RED, alpha=0.30, label=r'capture zone, $\phi_2>0$'),
        Line2D([], [], color=BLUE, lw=0.9, label='barrier trajectories'),
    ], fontsize=8, loc='lower left', framealpha=0.94)

    ax.text(0.985, 0.014,
            'not drawn, because not computed:\nthe dispersal line $e_1c_1O$, the '
            'universal lines\nat $d_1$ and $f_1$, and $c_1$\n'
            r'$f_1$ is Table 2 only — see audit Finding 6',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=7.5,
            color='0.42', linespacing=1.5)

    fig.tight_layout()
    fig.savefig(a.out)
    print('wrote %s' % os.path.abspath(a.out))


if __name__ == '__main__':
    main()
