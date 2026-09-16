"""
visualize.py -- Layer 0: the barrier as a swept surface.

reproduce_figures.py redraws the figures the paper prints.  This does the other
job: it shows how the barrier is *built*.  The boundary of the usable part is a
curve; every point of it is a terminal condition; integrating the state-costate
system retrograde from each one gives a barrier trajectory, and the bundle of
those trajectories IS the semipermeable sheet.

All four (BUP) families are covered -- maximum range, minimum range, and the two
off-boresight limit surfaces -- with the seeds ordered along each curve by
bup_curves.py, so every bundle renders as a surface rather than a pile of curves.

Figures, per family:
    <fam>_1_bup.png      the (BUP) alone, in both printed faces, over the
                         target-set boundaries with the Table 2 points overlaid
    <fam>_2_sheet.png    the retrograde bundle and the sheet it sweeps
and once over all four:
    all_bup.png          the whole boundary of the usable part in one picture
    diagnostics.png      one trajectory in full: states, costates, controls,
                         invariants, with the located switches marked
    invariants.png       invariant residuals by family -- the error certificate

Usage:  python3 layer0/viz/visualize.py [outdir] [--tau 1.5] [--nseed 45]
        (outdir defaults to layer0/viz/figs, beside this file)
"""

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # layer0/
sys.path.insert(0, HERE)

import barrier as B
import bup_curves as C

D = np.pi / 180.0
FAMILIES = ('max', 'min', 'bore+', 'bore-')

# Categorical hues, validated for CVD separation against a light surface.
HUE = ['#1f5fa8', '#c1442a', '#8a5cc7']
C_SW = '#8a5cc7'
C_BUP = '#111111'
C_REF = '#8d959e'
C_OK = '#1a7f4b'
AX_LINE = '#3f4750'
AX_TICK = '#2c333a'

RAMP = [LinearSegmentedColormap.from_list('h0', ['#cfe0f3', '#1f5fa8', '#0d2d52']),
        LinearSegmentedColormap.from_list('h1', ['#f3d5cd', '#c1442a', '#5e1d11']),
        LinearSegmentedColormap.from_list('h2', ['#e2d6f2', '#8a5cc7', '#3d2359'])]

# Axis furniture is deliberately dark and weighted; the grid stays recessive.
plt.rcParams.update({'font.size': 9, 'figure.dpi': 130, 'savefig.dpi': 130,
                     'axes.grid': True, 'grid.alpha': 0.30, 'grid.color': '0.74',
                     'axes.edgecolor': '0.22', 'axes.linewidth': 1.2,
                     'axes.labelcolor': '0.06', 'axes.labelweight': 'semibold',
                     'axes.labelsize': 9.5, 'axes.titlecolor': '0.08',
                     'text.color': '0.12',
                     'xtick.color': '0.16', 'ytick.color': '0.16',
                     'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5,
                     'xtick.major.width': 1.1, 'ytick.major.width': 1.1,
                     'xtick.major.size': 4.0, 'ytick.major.size': 4.0})

TITLE = {'max': 'maximum range, Eq. (32)',
         'min': 'minimum range, Eq. (46)',
         'bore+': r'off-boresight $\phi_1=+\beta$, Eq. (62)',
         'bore-': r'off-boresight $\phi_1=-\beta$, Eq. (62)'}


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def load_table2():
    """Table 2, p. 155 -- the paper's only published numerical ground truth."""
    from validate_table2 import TABLE2
    return [(n, R, p1, p2) for n, R, p1, p2 in TABLE2]


TABLE2 = load_table2()


def on_curve(branches, tol=0.02):
    """Which Table 2 points lie on these (BUP) branches, to within tol."""
    out = []
    for name, R, p1, p2 in TABLE2:
        best = 1e9
        for br in branches:
            for y in br:
                best = min(best, max(abs(y[0] - R),
                                     abs(B.wrap(y[1] - p1 * D)),
                                     abs(B.wrap(y[2] - p2 * D))))
        out.append((name, R, p1, p2, best < tol))
    return out


def unwrapped(tr):
    return np.unwrap(tr['phi1']), np.unwrap(tr['phi2'])


def bundle(seeds, tau_max, dt=5e-4):
    """Integrate retrograde from every seed on one branch."""
    out = []
    for y0 in seeds:
        tr = B.integrate_retrograde(y0, tau_max=tau_max, dt=dt)
        a1, a2 = unwrapped(tr)
        out.append(dict(tau=tr['tau'], R=tr['R'], a1=a1, a2=a2, raw=tr,
                        switches=tr['switches'], seed=np.asarray(y0),
                        fi=tr['fi_err'].max(), h=tr['h_err'].max()))
    return out


def build(family, nseed, tau_max):
    seeds, label = C.seeds(family, nseed=nseed)
    return dict(key=family, label=label, seeds=seeds,
                bundles=[bundle(s, tau_max) for s in seeds],
                t2=on_curve(seeds))


def resample(trajs, tau_max, m=220):
    """Common tau grid, so a bundle becomes an (arclength, tau) surface."""
    tg = np.linspace(0.0, tau_max, m)
    R = np.array([np.interp(tg, t['tau'], t['R']) for t in trajs])
    A1 = np.array([np.interp(tg, t['tau'], t['a1']) for t in trajs])
    A2 = np.array([np.interp(tg, t['tau'], t['a2']) for t in trajs])
    return tg, R, A1, A2


def shade(cmap, k, n):
    return cmap(0.18 + 0.72 * k / max(n - 1, 1))


# ---------------------------------------------------------------------------
# shared drawing pieces
# ---------------------------------------------------------------------------

def draw_reference(ax, kind):
    """The target-set boundaries the printed figures are drawn over."""
    q = np.linspace(-np.pi, np.pi, 1201)
    if kind == 'phi1':
        for b in (B.BETA, -B.BETA):
            ax.axhline(b / D, color=C_REF, lw=0.9, ls='--', zorder=1)
    else:
        ax.plot(q / D, B.R_hi(q), color=C_REF, lw=0.9, ls='--', zorder=1,
                label=r'$\bar{R}_1(\phi_2)$, Eq. (9)')
        ax.plot(q / D, B.R_lo(q), color=C_REF, lw=0.9, ls=':', zorder=1,
                label=r'$R_{\min}(\phi_2)$, Eq. (8)')


def draw_table2(ax, t2, xk, yk, label_on=True):
    """
    Published points: filled and named if they lie on the family being drawn,
    faint and hollow otherwise.

    Labels are placed greedily and a label is dropped when it would land on one
    already placed -- a cluster of overlapping names is less use than the marker
    alone, and the point is still visibly there.
    """
    get = {'R': lambda p: p[1], 'phi1': lambda p: p[2], 'phi2': lambda p: p[3]}
    xlo, xhi = sorted(ax.get_xlim())
    ylo, yhi = sorted(ax.get_ylim())
    minx = 0.045 * (xhi - xlo)
    miny = 0.055 * (yhi - ylo)
    placed = []
    for p in t2:
        x, y, on = get[xk](p), get[yk](p), p[4]
        if not (xlo <= x <= xhi and ylo <= y <= yhi):
            continue
        if not on:
            ax.plot(x, y, 'o', ms=3.0, mfc='none', mec='#b8c0c9', mew=0.9, zorder=8)
            continue
        ax.plot(x, y, 'o', ms=4.6, mfc='#111', mec='w', mew=0.7, zorder=9)
        if not label_on:
            continue
        if any(abs(x - px) < minx and abs(y - py) < miny for px, py in placed):
            continue
        placed.append((x, y))
        ax.annotate('$%s$' % p[0], (x, y), textcoords='offset points',
                    xytext=(5, 4), fontsize=7.5, color='#111', zorder=10)


def seed_xy(seeds, xk, yk):
    """
    A branch's coordinates for plotting, broken at the phi_2 = +/- pi seam.

    Branches are continuous through that seam -- it bounds the coordinate, not
    the problem -- but the plotted phi_2 is wrapped, so consecutive points can
    jump from +179.7 to -179.7.  Drawn as-is that is a straight line clear
    across the axes.  A NaN in the gap lifts the pen instead.
    """
    get = {'R': lambda y: y[0], 'phi1': lambda y: y[1] / D, 'phi2': lambda y: y[2] / D}
    xs, ys = [], []
    prev = None
    for y in seeds:
        q = y[2] / D
        if prev is not None and abs(q - prev) > 180.0:
            xs.append(np.nan)
            ys.append(np.nan)
        xs.append(get[xk](y))
        ys.append(get[yk](y))
        prev = q
    return xs, ys


def seed_z(seeds):
    """Matching R values, with the same seam breaks as seed_xy."""
    out, prev = [], None
    for y in seeds:
        q = y[2] / D
        if prev is not None and abs(q - prev) > 180.0:
            out.append(np.nan)
        out.append(y[0])
        prev = q
    return out


def switch_points(trajs):
    xs, ys, zs = [], [], []
    for t in trajs:
        for tau, _ in t['switches']:
            xs.append(np.interp(tau, t['tau'], t['a2']) / D)
            ys.append(np.interp(tau, t['tau'], t['a1']) / D)
            zs.append(np.interp(tau, t['tau'], t['R']))
    return np.array(xs), np.array(ys), np.array(zs)


# ---------------------------------------------------------------------------
# figure 1 -- the (BUP) alone
# ---------------------------------------------------------------------------

def fig_bup(F, out):
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.1))
    for k, (ax, (xk, yk, xl, yl, ref)) in enumerate(zip(
            axes, [('phi2', 'phi1', r'$\phi_2$  [deg]', r'$\phi_1$  [deg]', 'phi1'),
                   ('phi2', 'R', r'$\phi_2$  [deg]', r'$R$', 'R')])):
        draw_reference(ax, ref)
        for bi, seeds in enumerate(F['seeds']):
            xs, ys = seed_xy(seeds, xk, yk)
            ax.plot(xs, ys, '-', lw=2.2, color=C_BUP, zorder=6)
            ax.plot(xs, ys, '-', lw=4.0, color=HUE[bi % 3], alpha=0.30, zorder=5,
                    label='branch %d' % (bi + 1))
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.invert_xaxis()
        if yk == 'R':
            ax.invert_yaxis()
        draw_table2(ax, F['t2'], xk, yk)
        ax.legend(fontsize=7, framealpha=0.92, loc='best')

    fig.suptitle('(BUP)$_1$ — %s\nfilled points are the Table 2 entries this curve '
                 'reproduces; hollow ones belong elsewhere in the construction'
                 % TITLE[F['key']], fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(os.path.join(out, '%s_1_bup.png' % slug(F['key'])))
    plt.close(fig)


# ---------------------------------------------------------------------------
# figure 2 -- the bundle and the sheet
# ---------------------------------------------------------------------------

def fig_sheet(F, out, tau_max):
    fig = plt.figure(figsize=(10.6, 4.8))

    ax = fig.add_subplot(1, 2, 1, projection='3d')
    for bi, trajs in enumerate(F['bundles']):
        cmap = RAMP[bi % 3]
        for k, t in enumerate(trajs):
            ax.plot(t['a2'] / D, t['a1'] / D, t['R'], lw=0.6,
                    color=shade(cmap, k, len(trajs)), alpha=0.85)
        xs, ys = seed_xy(F['seeds'][bi], 'phi2', 'phi1')
        ax.plot(xs, ys, seed_z(F['seeds'][bi]), lw=2.2, color=C_BUP, zorder=10)
    xs, ys, zs = switch_points([t for b in F['bundles'] for t in b])
    if len(xs):
        ax.plot(xs, ys, zs, '.', ms=1.8, color=C_SW, zorder=11)
    style3d(ax, 'the trajectory bundle')

    ax = fig.add_subplot(1, 2, 2, projection='3d')
    for bi, trajs in enumerate(F['bundles']):
        cmap = RAMP[bi % 3]
        tg, R, A1, A2 = resample(trajs, tau_max)
        S = np.tile(np.linspace(0, 1, len(trajs))[:, None], (1, len(tg)))
        ax.plot_surface(A2 / D, A1 / D, R, facecolors=cmap(0.18 + 0.72 * S),
                        rstride=1, cstride=6, linewidth=0, antialiased=True,
                        shade=False, alpha=0.92)
        xs, ys = seed_xy(F['seeds'][bi], 'phi2', 'phi1')
        ax.plot(xs, ys, seed_z(F['seeds'][bi]), lw=2.2, color=C_BUP, zorder=10)
    style3d(ax, 'the sheet it sweeps')

    nsw = sum(len(t['switches']) for b in F['bundles'] for t in b)
    fi = max(t['fi'] for b in F['bundles'] for t in b)
    h = max(t['h'] for b in F['bundles'] for t in b)
    fig.suptitle(r'Retrograde bundle from the (BUP)$_1$ — %s   ($\tau \leq %.2f$)'
                 % (TITLE[F['key']], tau_max) + '\n'
                 '%d trajectories · %d switches located · max $|FI-1|$ = %.1e · '
                 'max $|H^*|$ = %.1e'
                 % (sum(len(b) for b in F['bundles']), nsw, fi, h), fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    fig.savefig(os.path.join(out, '%s_2_sheet.png' % slug(F['key'])))
    plt.close(fig)


def style3d(ax, title):
    """
    Dark, weighted axis lines and ticks on the 3-D views.

    Matplotlib's 3-D default is a pale grey line on a pale grey pane, which
    disappears under a shaded surface -- the axes end up harder to read than the
    data they frame.  The panes are cleared and the three axis lines and their
    ticks drawn in the same ink as the 2-D frames.
    """
    ax.set_xlabel(r'$\phi_2$ [deg]', labelpad=4)
    ax.set_ylabel(r'$\phi_1$ [deg]', labelpad=4)
    ax.set_zlabel(r'$R$', labelpad=4)
    ax.view_init(elev=21, azim=-60)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.line.set_color(AX_LINE)
        axis.line.set_linewidth(1.5)
        axis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        axis._axinfo['grid'].update(color='0.80', linewidth=0.8)
    ax.tick_params(colors=AX_TICK, labelsize=8.5, width=1.1, length=3.5)
    ax.set_title(title, fontsize=9.5, color='0.08')


# ---------------------------------------------------------------------------
# the whole boundary in one picture
# ---------------------------------------------------------------------------

def fig_all_bup(Fs, out):
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
    styles = {'max': ('-', HUE[0]), 'min': ('-', HUE[1]),
              'bore+': ('--', HUE[2]), 'bore-': (':', HUE[2])}
    for ax, (xk, yk, xl, yl, ref) in zip(
            axes, [('phi2', 'phi1', r'$\phi_2$  [deg]', r'$\phi_1$  [deg]', 'phi1'),
                   ('phi2', 'R', r'$\phi_2$  [deg]', r'$R$', 'R')]):
        draw_reference(ax, ref)
        for F in Fs:
            ls, col = styles[F['key']]
            for bi, seeds in enumerate(F['seeds']):
                xs, ys = seed_xy(seeds, xk, yk)
                ax.plot(xs, ys, ls, lw=1.8, color=col,
                        label=TITLE[F['key']] if bi == 0 else None)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.set_xlim(190, -190)
        ax.set_xticks([180, 90, 0, -90, -180])
        if yk == 'R':
            ax.set_ylim(6.6, 0)
        else:
            ax.set_ylim(-50, 50)
        all_t2 = merge_t2(Fs)
        draw_table2(ax, all_t2, xk, yk, label_on=(yk == 'R'))
    axes[0].legend(fontsize=7, framealpha=0.92, loc='lower left', ncol=2)
    fig.suptitle('The whole boundary of the usable part — all four surface families,\n'
                 'seeds ordered along every branch', fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(os.path.join(out, 'all_bup.png'))
    plt.close(fig)


def merge_t2(Fs):
    """A Table 2 point counts as placed if any family's (BUP) carries it."""
    out = []
    for i, p in enumerate(TABLE2):
        on = any(F['t2'][i][4] for F in Fs)
        out.append((p[0], p[1], p[2], p[3], on))
    return out


# ---------------------------------------------------------------------------
# one trajectory, in full
# ---------------------------------------------------------------------------

def fig_diagnostics(Fs, out, tau_max=5.0, dt=5e-4):
    best = None
    for F in Fs:
        for bi, trajs in enumerate(F['bundles']):
            for t in trajs:
                n = len(t['switches'])
                if best is None or n > best[0]:
                    best = (n, F['key'], t['seed'])
    _, key, y0 = best

    tr = B.integrate_retrograde(y0, tau_max=tau_max, dt=dt)
    a1, a2 = unwrapped(tr)
    tau = tr['tau']
    sw = [t for t, _ in tr['switches']]

    fig, axes = plt.subplots(2, 2, figsize=(9.6, 5.8))

    ax = axes[0, 0]
    ax.plot(tau, tr['R'], lw=1.6, color=HUE[0], label=r'$R$')
    ax2 = ax.twinx()
    ax2.grid(False)
    ax2.plot(tau, a1 / D, lw=1.3, color=HUE[1], label=r'$\phi_1$')
    ax2.plot(tau, a2 / D, lw=1.3, color=HUE[2], ls='--', label=r'$\phi_2$')
    ax2.set_ylabel('angles [deg]')
    ax.set_ylabel(r'$R$', color=HUE[0])
    ax.set_title('state')
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7.5, loc='upper left', framealpha=0.9)

    ax = axes[0, 1]
    ax.plot(tau, tr['lR'], lw=1.3, color=HUE[0], label=r'$\lambda_R$')
    ax.plot(tau, tr['l1'], lw=1.3, color=HUE[1], label=r'$\lambda_1$')
    ax.plot(tau, tr['l2'], lw=1.3, color=HUE[2], label=r'$\lambda_2$')
    ax.axhline(0, lw=0.8, color='0.55')
    ax.set_title(r'costates — a switch is a zero crossing of $\lambda_1$ or $\lambda_2$')
    ax.legend(fontsize=7.5, framealpha=0.9)

    ax = axes[1, 0]
    if len(tr['sigma']):
        ax.step(tau[1:], tr['sigma'][:, 0], where='post', lw=1.3, color=HUE[1],
                label=r'$\sigma_1^*=-\mathrm{sign}\,\lambda_1$')
        ax.step(tau[1:], tr['sigma'][:, 1] * 0.95, where='post', lw=1.3, color=HUE[2],
                label=r'$\sigma_2^*=+\mathrm{sign}\,\lambda_2$')
    ax.set_ylim(-1.35, 1.35)
    ax.set_yticks([-1, 0, 1])
    ax.set_title('barrier strategies, Eqs. (21)-(22) — frozen over each RK4 step')
    ax.legend(fontsize=7.5, loc='center right', framealpha=0.9)

    ax = axes[1, 1]
    ax.semilogy(tau, np.maximum(tr['fi_err'], 1e-18), lw=1.1, color=HUE[0],
                label=r'$|FI-1|$, Eq. (23)')
    ax.semilogy(tau, np.maximum(tr['h_err'], 1e-18), lw=1.1, color=C_OK,
                label=r'$|H^*|$, Eq. (15)')
    ax.set_ylim(1e-18, 1e-8)
    ax.set_title("invariants — the integration's own error estimate")
    ax.legend(fontsize=7.5, loc='lower right', framealpha=0.9)

    for ax in axes.ravel():
        for s in sw:
            ax.axvline(s, lw=0.8, color=C_SW, alpha=0.5, ls=':')
        ax.set_xlabel(r'retrograde time $\tau$')

    fig.suptitle('One barrier trajectory in full — %s, seeded at '
                 r'$\phi_2=%.2f°,\ \phi_1=%.2f°,\ R=%.4f$   '
                 '(%d switches located, dotted)'
                 % (TITLE[key], y0[2] / D, y0[1] / D, y0[0], len(sw)), fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(out, 'diagnostics.png'))
    plt.close(fig)
    return key, len(sw)


# ---------------------------------------------------------------------------
# invariant residuals by family
# ---------------------------------------------------------------------------

def fig_invariants(Fs, out, tau_max):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4))
    pos = np.arange(len(Fs))
    for j, key in enumerate(('fi', 'h')):
        ax = axes[j]
        for i, F in enumerate(Fs):
            v = np.array([t[key] for b in F['bundles'] for t in b])
            v = np.maximum(v, 1e-18)
            ax.scatter(np.full(len(v), i) + np.random.uniform(-0.16, 0.16, len(v)),
                       v, s=7, color=HUE[i % 3], alpha=0.55, linewidths=0)
            ax.plot([i - 0.28, i + 0.28], [v.max()] * 2, color='#111', lw=1.4)
            ax.annotate('%.1e' % v.max(), (i, v.max()), textcoords='offset points',
                        xytext=(0, 6), ha='center', fontsize=7.5)
        ax.set_yscale('log')
        ax.set_xticks(pos)
        ax.set_xticklabels([F['key'] for F in Fs])
        ax.set_ylim(1e-18, 1e-7)
        ax.set_title(r'$|FI-1|$, Eq. (23)' if key == 'fi' else r'$|H^*|$, Eq. (15)')
    fig.suptitle(r'Invariant residuals over every trajectory, $\tau \leq %.2f$ — '
                 'the bar is the worst case in each family' % tau_max, fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(os.path.join(out, 'invariants.png'))
    plt.close(fig)


# ---------------------------------------------------------------------------

def slug(key):
    return key.replace('+', 'p').replace('-', 'm')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir', nargs='?', default=os.path.join(HERE, 'figs'))
    ap.add_argument('--tau', type=float, default=1.5,
                    help='retrograde length of the bundles (default 1.5)')
    ap.add_argument('--nseed', type=int, default=45,
                    help='seeds per branch (default 45)')
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    np.random.seed(0)

    Fs = []
    for key in FAMILIES:
        F = build(key, args.nseed, args.tau)
        n = sum(len(b) for b in F['bundles'])
        nsw = sum(len(t['switches']) for b in F['bundles'] for t in b)
        fi = max(t['fi'] for b in F['bundles'] for t in b)
        h = max(t['h'] for b in F['bundles'] for t in b)
        placed = sum(1 for p in F['t2'] if p[4])
        print('%-6s %d branch(es)  %3d trajectories  %5d switches  '
              'max|FI-1| %.1e  max|H*| %.1e  %2d Table 2 points on the curve'
              % (key, len(F['seeds']), n, nsw, fi, h, placed))
        fig_bup(F, args.outdir)
        fig_sheet(F, args.outdir, args.tau)
        Fs.append(F)

    fig_all_bup(Fs, args.outdir)
    key, nsw = fig_diagnostics(Fs, args.outdir)
    print('diagnostics trajectory: %s family, %d switches' % (key, nsw))
    fig_invariants(Fs, args.outdir, args.tau)

    placed = sum(1 for p in merge_t2(Fs) if p[4])
    print('%d of %d Table 2 points lie on a (BUP) curve' % (placed, len(TABLE2)))
    print('wrote figures to %s' % os.path.abspath(args.outdir))
    for f in sorted(os.listdir(args.outdir)):
        if f.endswith('.png'):
            print('   ', f)


if __name__ == '__main__':
    main()
