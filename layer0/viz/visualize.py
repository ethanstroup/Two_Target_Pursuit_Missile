"""
visualize.py -- Layer 0: the barrier as a swept surface.

reproduce_figures.py redraws the printed figures.  This file does the other
job: it shows HOW the barrier is built -- the boundary of the usable part is a
curve, every point of it seeds a retrograde trajectory, and the bundle of those
trajectories IS the semipermeable sheet.

Starts with the MAXIMUM-RANGE family, which is the one to verify first: its
(BUP)_1 is a closed lens in (phi_2, phi_1) with a fold at d_1, the two Table 2
points e_1 and d_1 sit on it, and the whole thing lives in |phi_2| < 10 deg,
so the geometry is small enough to check by eye.

    phi_2 < 0 lobe : blue      phi_2 > 0 lobe : red      switch points : purple

Figures
    maxrange_1_bup.png           the (BUP)_1 lens, in both projections
    maxrange_2_bundle3d.png      the retrograde trajectory bundle in (phi_2, phi_1, R)
    maxrange_3_sheet3d.png       the same bundle rendered as the barrier sheet
    maxrange_4_projections.png   three orthogonal views of the bundle
    maxrange_5_diagnostics.png   one trajectory: states, costates, controls, invariants

Lives in layer0/viz/ and imports layer0/barrier.py from the parent directory,
so the verified module stays the single source of the maths.

Usage:  python3 layer0/viz/visualize.py [outdir] [--tau 1.5] [--nseed 41]
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
import barrier as B

D = np.pi / 180.0

# Categorical hues, validated for CVD separation against a light surface.
C_NEG = '#1f5fa8'      # phi_2 < 0 lobe
C_POS = '#c1442a'      # phi_2 > 0 lobe
C_SW = '#8a5cc7'       # control switches
C_BUP = '#111111'      # the (BUP)_1 itself
C_T2 = '#111111'       # Table 2 overlay

CMAP_NEG = LinearSegmentedColormap.from_list('neg', ['#cfe0f3', C_NEG, '#0d2d52'])
CMAP_POS = LinearSegmentedColormap.from_list('pos', ['#f3d5cd', C_POS, '#5e1d11'])

plt.rcParams.update({'font.size': 9, 'figure.dpi': 130, 'savefig.dpi': 130,
                     'axes.grid': True, 'grid.alpha': 0.22,
                     'axes.edgecolor': '0.5', 'axes.labelcolor': '0.15',
                     'text.color': '0.15', 'xtick.color': '0.35',
                     'ytick.color': '0.35'})

# Table 2, the two published points on this family (p. 155).
T2 = {'e_1': (6.1416, 36.08, 0.00),
      'd_1': (5.8083, 18.88, -9.56)}


# ---------------------------------------------------------------------------
# The (BUP)_1 lens
# ---------------------------------------------------------------------------

def fold_phi2(lo=-0.25, hi=-1e-4, iters=80):
    """
    Locate d_1: the phi_2 at which the two Eq. (32) roots merge and the
    maximum-range (BUP)_1 ends.  Bisect on "does a root exist".
    """
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if B.bup_maxrange(mid):
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def bup_curve(n=41, eps=2e-4, sign=-1):
    """
    Ordered polyline along one lobe of the maximum-range (BUP)_1.

    Walks the lower branch from phi_2 -> 0 out to the fold, then returns along
    the upper branch, so arclength runs monotonically and the fold is not a
    seam.  Returns (phi1, phi2, R), each length <= 2n.
    """
    fold = fold_phi2()
    # cosine spacing: the branches merge at the fold, so cluster samples there
    t = 0.5 * (1 - np.cos(np.linspace(0, np.pi, n)))
    p2s = eps + t * (abs(fold) * (1 - 1e-3) - eps)

    lower, upper = [], []
    for q in p2s:
        roots = B.bup_maxrange(sign * q)
        if len(roots) < 2:
            continue
        lower.append((min(roots, key=abs), sign * q))
        upper.append((max(roots, key=abs), sign * q))

    pts = lower + upper[::-1]
    p1 = np.array([p for p, _ in pts])
    p2 = np.array([q for _, q in pts])
    return p1, p2, B.R_hi(p2)


def seed_state(p1, p2):
    """Terminal state-costate vector on the maximum-range (BUP)_1, Eqs. (34)-(36)."""
    return np.array([B.R_hi(p2), p1, p2, *B.lam_maxrange(p2)])


# ---------------------------------------------------------------------------
# The bundle
# ---------------------------------------------------------------------------

def unwrapped(tr):
    """Angles without the [-pi, pi) seam, so a trajectory plots as one curve."""
    return np.unwrap(tr['phi1']), np.unwrap(tr['phi2'])


def bundle(p1s, p2s, tau_max=1.5, dt=5e-4):
    """Integrate retrograde from every seed on the lens.  One dict per trajectory."""
    out = []
    for p1, p2 in zip(p1s, p2s):
        tr = B.integrate_retrograde(seed_state(p1, p2), tau_max=tau_max, dt=dt)
        a1, a2 = unwrapped(tr)
        out.append(dict(tau=tr['tau'], R=tr['R'], a1=a1, a2=a2, raw=tr,
                        switches=tr['switches'],
                        fi=tr['fi_err'].max(), h=tr['h_err'].max()))
    return out


def resample(trajs, tau_max, m=240):
    """
    Put every trajectory on a common tau grid so the bundle becomes a (s, tau)
    surface.  Switch-located steps make the raw grids ragged; this only affects
    rendering, never the integration.
    """
    tg = np.linspace(0.0, tau_max, m)
    R = np.array([np.interp(tg, t['tau'], t['R']) for t in trajs])
    A1 = np.array([np.interp(tg, t['tau'], t['a1']) for t in trajs])
    A2 = np.array([np.interp(tg, t['tau'], t['a2']) for t in trajs])
    return tg, R, A1, A2


def shade(cmap, k, n):
    """Position along the lens, light at phi_2 -> 0, dark at the fold."""
    return cmap(0.18 + 0.72 * k / max(n - 1, 1))


def mark_t2(ax, xkey, ykey, dy=6):
    """Overlay e_1 and d_1.  Keys in {'phi1', 'phi2', 'R'}."""
    get = {'R': lambda p: p[0], 'phi1': lambda p: p[1], 'phi2': lambda p: p[2]}
    for name, p in T2.items():
        ax.plot(get[xkey](p), get[ykey](p), 'o', ms=5, mfc='none',
                mec=C_T2, mew=1.2, zorder=9)
        ax.annotate('$%s$' % name.replace('_', '_'), (get[xkey](p), get[ykey](p)),
                    textcoords='offset points', xytext=(5, dy), fontsize=8,
                    color=C_T2, zorder=9)


def switch_points(trajs):
    """(phi_2, phi_1, R) of every located control switch in a bundle."""
    xs, ys, zs = [], [], []
    for t in trajs:
        for tau, _idx in t['switches']:
            xs.append(np.interp(tau, t['tau'], t['a2']) / D)
            ys.append(np.interp(tau, t['tau'], t['a1']) / D)
            zs.append(np.interp(tau, t['tau'], t['R']))
    return np.array(xs), np.array(ys), np.array(zs)


# ---------------------------------------------------------------------------
# Figure 1 -- the lens
# ---------------------------------------------------------------------------

def fig_bup(lobes, out):
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.0))
    for (p1, p2, R), c, lab in lobes:
        axes[0].plot(p2 / D, p1 / D, '-', lw=2.0, color=c, label=lab)
        axes[1].plot(p2 / D, R, '-', lw=2.0, color=c, label=lab)

    q = np.linspace(-0.22, 0.22, 801)
    axes[1].plot(q / D, B.R_hi(q), '--', lw=1.0, color='0.45',
                 label=r'$\bar{R}_1(\phi_2)$, Eq. (9)')

    mark_t2(axes[0], 'phi2', 'phi1')
    mark_t2(axes[1], 'phi2', 'R')

    axes[0].set_ylabel(r'$\phi_1$  [deg]')
    axes[0].set_title(r'(BUP)$_1$ in the $(\phi_2,\phi_1)$ face')
    axes[1].set_ylabel(r'$R$')
    axes[1].set_title(r'(BUP)$_1$ lies on the surface $R=\bar{R}_1(\phi_2)$')
    for a in axes:
        a.set_xlabel(r'$\phi_2$  [deg]   (increasing to the left, as printed)')
        a.set_xlim(12, -12)
        a.legend(fontsize=7.5, framealpha=0.92, loc='lower center')

    fig.suptitle('Maximum-range (BUP)$_1$, Eq. (32) with equality — a closed lens '
                 'folding at $d_1$, with $e_1$ the $\\phi_2\\to0$ limit', fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(out, 'maxrange_1_bup.png'))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 -- the bundle in 3D
# ---------------------------------------------------------------------------

def fig_bundle3d(lobes, bundles, out, tau_max):
    """Left: the whole bundle.  Right: the first moments off the (BUP)_1."""
    tau_zoom = min(0.35, 0.25 * tau_max)
    fig = plt.figure(figsize=(9.2, 4.6))
    panels = [(tau_max, 22, -58, r'the bundle, $\tau \leq %.2f$' % tau_max),
              (tau_zoom, 24, -64,
               r'leaving the (BUP)$_1$: $\tau \leq %.2f$' % tau_zoom)]

    for j, (tcut, elev, azim, ttl) in enumerate(panels):
        ax = fig.add_subplot(1, 2, j + 1, projection='3d')
        for ((p1b, p2b, Rb), c, lab), (trajs, cmap) in zip(lobes, bundles):
            for k, t in enumerate(trajs):
                m = t['tau'] <= tcut
                ax.plot(t['a2'][m] / D, t['a1'][m] / D, t['R'][m], lw=0.7,
                        color=shade(cmap, k, len(trajs)), alpha=0.85)
            ax.plot(p2b / D, p1b / D, Rb, lw=2.4, color=C_BUP, zorder=10)
        xs, ys, zs = switch_points(bundles[0][0] + bundles[1][0])
        if len(xs):
            ax.plot(xs, ys, zs, '.', ms=2.4, color=C_SW, zorder=11)
        ax.set_xlabel(r'$\phi_2$ [deg]', labelpad=2)
        ax.set_ylabel(r'$\phi_1$ [deg]', labelpad=2)
        ax.set_zlabel(r'$R$', labelpad=2)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(ttl, fontsize=9)
        ax.grid(alpha=0.2)

    nsw = sum(len(t['switches']) for b in bundles for t in b[0])
    key = 'black = the (BUP)$_1$ seed curve'
    key += (' · purple = %d located control switches' % nsw) if nsw else \
           r' · no control switch occurs before $\tau \approx 3.1$'
    fig.suptitle('Barrier trajectories integrated retrograde from the maximum-range '
                 '(BUP)$_1$\n' + key, fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(os.path.join(out, 'maxrange_2_bundle3d.png'))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 -- the swept sheet
# ---------------------------------------------------------------------------

def fig_sheet3d(lobes, bundles, out, tau_max):
    fig = plt.figure(figsize=(7.4, 5.6))
    ax = fig.add_subplot(111, projection='3d')
    for ((p1b, p2b, Rb), c, lab), (trajs, cmap) in zip(lobes, bundles):
        tg, R, A1, A2 = resample(trajs, tau_max)
        S = np.tile(np.linspace(0, 1, len(trajs))[:, None], (1, len(tg)))
        ax.plot_surface(A2 / D, A1 / D, R, facecolors=cmap(0.18 + 0.72 * S),
                        rstride=1, cstride=6, linewidth=0, antialiased=True,
                        shade=False, alpha=0.9)
        ax.plot(p2b / D, p1b / D, Rb, lw=2.4, color=C_BUP, zorder=10)

    ax.set_xlabel(r'$\phi_2$ [deg]')
    ax.set_ylabel(r'$\phi_1$ [deg]')
    ax.set_zlabel(r'$R$')
    ax.view_init(elev=20, azim=-62)
    ax.grid(alpha=0.2)
    ax.set_title('The maximum-range barrier sheet, swept by the trajectory bundle\n'
                 r'surface parametrized by (arclength along (BUP)$_1$, retrograde time $\tau$)',
                 fontsize=9.5)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'maxrange_3_sheet3d.png'))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4 -- orthogonal projections
# ---------------------------------------------------------------------------

def fig_projections(lobes, bundles, out, tau_max):
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.8))
    views = [('a2', 'a1', r'$\phi_2$ [deg]', r'$\phi_1$ [deg]', 'phi2', 'phi1'),
             ('a2', 'R', r'$\phi_2$ [deg]', r'$R$', 'phi2', 'R'),
             ('a1', 'R', r'$\phi_1$ [deg]', r'$R$', 'phi1', 'R')]

    for ax, (xk, yk, xl, yl, t2x, t2y) in zip(axes, views):
        for ((p1b, p2b, Rb), c, lab), (trajs, cmap) in zip(lobes, bundles):
            for k, t in enumerate(trajs):
                x = t[xk] / D if xk != 'R' else t[xk]
                y = t[yk] / D if yk != 'R' else t[yk]
                ax.plot(x, y, lw=0.6, color=shade(cmap, k, len(trajs)), alpha=0.8)
            bx = {'a1': p1b / D, 'a2': p2b / D, 'R': Rb}[xk]
            by = {'a1': p1b / D, 'a2': p2b / D, 'R': Rb}[yk]
            ax.plot(bx, by, lw=2.2, color=C_BUP, zorder=10)
        xs, ys, zs = switch_points(bundles[0][0] + bundles[1][0])
        sel = {'a2': xs, 'a1': ys, 'R': zs}
        if len(xs):
            ax.plot(sel[xk], sel[yk], '.', ms=2.2, color=C_SW, zorder=11)
        mark_t2(ax, t2x, t2y)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)

    axes[0].invert_xaxis()
    axes[1].invert_xaxis()
    axes[1].invert_yaxis()
    axes[2].invert_yaxis()
    for ax, t in zip(axes, ['face $(\\phi_2,\\phi_1)$', 'face $(\\phi_2,R)$',
                            'face $(\\phi_1,R)$']):
        ax.set_title(t, fontsize=9)
    fig.suptitle(r'Three faces of the same bundle ($\tau \leq %.2f$).  '
                 r'Colour runs light $\to$ dark along the (BUP)$_1$ from '
                 r'$\phi_2\to0$ to the fold at $d_1$.' % tau_max, fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(os.path.join(out, 'maxrange_4_projections.png'))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 -- one trajectory, in full
# ---------------------------------------------------------------------------

def pick_switching_seed(p1s, p2s, tau_max=5.0, dt=2e-3):
    """
    Choose the seed whose trajectory shows the most control switches -- the
    interesting one to plot, because a switch is what H* is sensitive to and
    what the frozen-control / bisected-switch machinery exists for.
    """
    best, best_n = 0, -1
    for k, (p1, p2) in enumerate(zip(p1s, p2s)):
        tr = B.integrate_retrograde(seed_state(p1, p2), tau_max=tau_max, dt=dt)
        if len(tr['switches']) > best_n:
            best, best_n = k, len(tr['switches'])
    return best, best_n


def fig_diagnostics(p1, p2, out, tau_max=5.0, dt=5e-4):
    tr = B.integrate_retrograde(seed_state(p1, p2), tau_max=tau_max, dt=dt)
    a1, a2 = unwrapped(tr)
    tau = tr['tau']
    sw = [t for t, _ in tr['switches']]

    fig, axes = plt.subplots(2, 2, figsize=(9.4, 5.6))

    ax = axes[0, 0]
    ax.plot(tau, tr['R'], lw=1.6, color=C_NEG, label=r'$R$')
    ax2 = ax.twinx()
    ax2.grid(False)
    ax2.plot(tau, a1 / D, lw=1.4, color=C_POS, label=r'$\phi_1$')
    ax2.plot(tau, a2 / D, lw=1.4, color=C_SW, ls='--', label=r'$\phi_2$')
    ax2.set_ylabel('angles [deg]')
    ax.set_ylabel(r'$R$', color=C_NEG)
    ax.set_title('state')
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7.5, loc='upper left', framealpha=0.9)

    ax = axes[0, 1]
    ax.plot(tau, tr['lR'], lw=1.4, color=C_NEG, label=r'$\lambda_R$')
    ax.plot(tau, tr['l1'], lw=1.4, color=C_POS, label=r'$\lambda_1$')
    ax.plot(tau, tr['l2'], lw=1.4, color=C_SW, label=r'$\lambda_2$')
    ax.axhline(0, lw=0.8, color='0.55')
    ax.set_title(r'costates — a switch is a zero crossing of $\lambda_1$ or $\lambda_2$')
    ax.legend(fontsize=7.5, framealpha=0.9)

    ax = axes[1, 0]
    if len(tr['sigma']):
        ax.step(tau[1:], tr['sigma'][:, 0], where='post', lw=1.4, color=C_POS,
                label=r'$\sigma_1^*=-\mathrm{sign}\,\lambda_1$')
        ax.step(tau[1:], tr['sigma'][:, 1] * 0.96, where='post', lw=1.4, color=C_SW,
                label=r'$\sigma_2^*=+\mathrm{sign}\,\lambda_2$')
    ax.set_ylim(-1.35, 1.35)
    ax.set_yticks([-1, 0, 1])
    ax.set_title('barrier strategies, Eqs. (21)-(22) — frozen over each RK4 step')
    ax.legend(fontsize=7.5, loc='center right', framealpha=0.9)

    ax = axes[1, 1]
    ax.semilogy(tau, np.maximum(tr['fi_err'], 1e-18), lw=1.2, color=C_NEG,
                label=r'$|FI-1|$, Eq. (23)')
    ax.semilogy(tau, np.maximum(tr['h_err'], 1e-18), lw=1.2, color=C_POS,
                label=r'$|H^*|$, Eq. (15)')
    ax.set_ylim(1e-18, 1e-8)
    ax.set_title('invariants — the integration\'s own error estimate')
    ax.legend(fontsize=7.5, loc='lower right', framealpha=0.9)

    for ax in axes.ravel():
        for s in sw:
            ax.axvline(s, lw=0.8, color=C_SW, alpha=0.5, ls=':')
        ax.set_xlabel(r'retrograde time $\tau$')

    fig.suptitle(r'One maximum-range barrier trajectory, seeded at '
                 r'$\phi_2=%.2f°,\ \phi_1=%.2f°,\ R=\bar{R}_1=%.4f$   '
                 r'(%d switches located)' % (p2 / D, p1 / D, B.R_hi(p2), len(sw)),
                 fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(out, 'maxrange_5_diagnostics.png'))
    plt.close(fig)
    return tr


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir', nargs='?', default=os.path.join(HERE, 'figs'))
    ap.add_argument('--tau', type=float, default=1.5,
                    help='retrograde length of the bundle (default 1.5)')
    ap.add_argument('--nseed', type=int, default=41,
                    help='seeds per branch per lobe (default 41)')
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    fold = fold_phi2()
    print('fold (d_1) at phi_2 = %.4f deg   Table 2: -9.56' % (fold / D))

    lobes = [(bup_curve(args.nseed, sign=-1), C_NEG, r'$\phi_2<0$ lobe'),
             (bup_curve(args.nseed, sign=+1), C_POS, r'$\phi_2>0$ lobe')]
    bundles = [(bundle(p1, p2, tau_max=args.tau), cmap)
               for ((p1, p2, _), _, _), cmap in zip(lobes, (CMAP_NEG, CMAP_POS))]

    n = sum(len(b[0]) for b in bundles)
    fi = max(t['fi'] for b in bundles for t in b[0])
    h = max(t['h'] for b in bundles for t in b[0])
    nsw = sum(len(t['switches']) for b in bundles for t in b[0])
    print('%d trajectories, %d switches located' % (n, nsw))
    print('max |FI-1| = %.1e     max |H*| = %.1e' % (fi, h))

    fig_bup(lobes, args.outdir)
    fig_bundle3d(lobes, bundles, args.outdir, args.tau)
    fig_sheet3d(lobes, bundles, args.outdir, args.tau)
    fig_projections(lobes, bundles, args.outdir, args.tau)

    p1c, p2c, _ = bup_curve(args.nseed, sign=-1)
    k, nsw_k = pick_switching_seed(p1c, p2c)
    print('diagnostics seed: phi_2 = %.2f deg, phi_1 = %.2f deg (%d switches)'
          % (p2c[k] / D, p1c[k] / D, nsw_k))
    fig_diagnostics(p1c[k], p2c[k], args.outdir)

    print('wrote figures to %s' % os.path.abspath(args.outdir))
    for f in sorted(os.listdir(args.outdir)):
        if f.startswith('maxrange_'):
            print('   ', f)


if __name__ == '__main__':
    main()
