"""
reproduce_figures.py -- redraw the Davidovitz & Shinar (1989) figures from the
reconstructed barrier, for side-by-side comparison with the printed article.

Axis orientation follows the paper: phi_2 increases to the LEFT, and in the
(phi_2, R) views R increases DOWNWARD.  Table 2 points are overlaid so the
agreement (or not) is visible rather than asserted.

Outputs  fig04_up_maxrange.png, fig05_up_minrange.png, fig06_up_boresight.png,
         fig08_barriers_headon.png, fig10_barrier_boresight.png,
         fig11_barriers_minrange.png, fig_invariants.png

Usage:  python3 reproduce_figures.py [outdir]
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import barrier as B
from validate_table2 import TABLE2

D = np.pi / 180.0
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({'font.size': 9, 'figure.dpi': 130, 'savefig.dpi': 130,
                     'axes.grid': True, 'grid.alpha': 0.25})


def t2(name):
    for n, R, d1, d2 in TABLE2:
        if n == name:
            return R, d1, d2
    return None


def mark(ax, names, xkey, ykey, color='crimson'):
    """Overlay Table 2 points.  xkey/ykey in {'phi1','phi2','R'} (degrees for angles)."""
    get = {'phi1': lambda p: p[1], 'phi2': lambda p: p[2], 'R': lambda p: p[0]}
    xs, ys, ls = [], [], []
    for nm in names:
        p = t2(nm)
        if p is None:
            continue
        xs.append(get[xkey](p))
        ys.append(get[ykey](p))
        ls.append(nm)
    ax.plot(xs, ys, 'o', ms=4, color=color, zorder=6, mec='k', mew=0.4)
    for x, y, l in zip(xs, ys, ls):
        ax.annotate(l, (x, y), textcoords='offset points', xytext=(4, 3),
                    fontsize=7, color=color, zorder=7)


# ===========================================================================
# Fig. 4 -- maximum-range (UP)_1 region, beta = 45 deg
# ===========================================================================
fig, ax = plt.subplots(figsize=(5.2, 4.6))
p2 = np.linspace(-0.9, 0.9, 1201)
p1 = np.linspace(-B.BETA, B.BETA, 801)
P2, P1 = np.meshgrid(p2, p1)
U = B.up_maxrange(P1, P2)
ax.contourf(P2 / D, P1 / D, (U < 0).astype(float), levels=[0.5, 1.5],
            colors=['#cfe3f7'])
ax.contour(P2 / D, P1 / D, U, levels=[0.0], colors=['k'], linewidths=1.2)
ax.axhline(B.BETA / D, color='0.4', lw=0.8, ls='--')
ax.axhline(-B.BETA / D, color='0.4', lw=0.8, ls='--')
ax.axhline(0, color='0.7', lw=0.6)
ax.axvline(0, color='0.7', lw=0.6)
mark(ax, ['e_1', 'f_1', 'd_1'], 'phi2', 'phi1')
ax.set_xlim(45, -45)
ax.set_xlabel(r'$\phi_2$  [deg]   (increasing to the left, as printed)')
ax.set_ylabel(r'$\phi_1$  [deg]')
ax.set_title('Fig. 4 reconstructed — maximum-range (UP)$_1$, Eq. (32)\n'
             'shaded = usable part, curve = (BUP)$_1$')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig04_up_maxrange.png'))
plt.close(fig)

# ===========================================================================
# Fig. 5 -- minimum-range (UP)_1 region
# ===========================================================================
fig, ax = plt.subplots(figsize=(6.4, 4.2))
p2 = np.linspace(-np.pi, np.pi, 1601)
p1 = np.linspace(-B.BETA, B.BETA, 801)
P2, P1 = np.meshgrid(p2, p1)
U = B.up_minrange(P1, P2)
ax.contourf(P2 / D, P1 / D, (U < 0).astype(float), levels=[0.5, 1.5],
            colors=['#cfe3f7'])
ax.contour(P2 / D, P1 / D, U, levels=[0.0], colors=['k'], linewidths=1.2)
ax.axhline(0, color='0.7', lw=0.6)
mark(ax, ['g_1', 'h_1', 'M_1', 'N_1'], 'phi2', 'phi1')
ax.set_xlim(180, -180)
ax.set_xticks([180, 90, 0, -90, -180])
ax.set_xlabel(r'$\phi_2$  [deg]')
ax.set_ylabel(r'$\phi_1$  [deg]')
ax.set_title('Fig. 5 reconstructed — minimum-range (UP)$_1$, Eq. (46)')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig05_up_minrange.png'))
plt.close(fig)

# ===========================================================================
# Fig. 6 -- off-boresight limit (UP)_1 on phi_1 = beta, in (phi_2, R)
# ===========================================================================
fig, ax = plt.subplots(figsize=(6.4, 4.6))
p2 = np.linspace(-np.pi, np.pi, 1601)
Rg = np.linspace(0.0, 6.6, 1201)
P2, RR = np.meshgrid(p2, Rg)
p1 = B.BETA
inT = B.in_target(p1, P2, RR)
usable = inT & (B.up_boresight(RR, p1, P2) < 0)
ax.contourf(P2 / D, RR, usable.astype(float), levels=[0.5, 1.5], colors=['#cfe3f7'])
ax.contourf(P2 / D, RR, (inT & ~usable).astype(float), levels=[0.5, 1.5],
            colors=['#f6d6d6'])
ax.plot(p2 / D, B.R_hi(p2), 'k-', lw=1.2, label=r'$\bar{R}_1(\phi_2)$, Eq. (9)')
ax.plot(p2 / D, B.R_lo(p2), 'k-', lw=1.2, label=r'$R_{\min}(\phi_2)$, Eq. (8)')
Lb = (np.sin(p1) + np.sin(p2)) * np.sign(p1)
ax.plot(p2 / D, np.where(Lb > 0, Lb, np.nan), 'b--', lw=1.3,
        label=r'(BUP)$_1$: $R=(\sin\phi_1+\sin\phi_2)\,$sign$\,\phi_1$, Eq. (62)')
mark(ax, ['A_1', 'B_1', 'Q_1', 'M_1', 'Z_1', 'gamma', 'beta', 'nu', 'Y_1'], 'phi2', 'R')
ax.set_xlim(180, -180)
ax.set_ylim(6.6, 0)
ax.set_xticks([180, 90, 0, -90, -180])
ax.set_xlabel(r'$\phi_2$  [deg]')
ax.set_ylabel(r'$R$   (increasing downward, as printed)')
ax.set_title(r'Fig. 6 reconstructed — off-boresight limit surface $\phi_1=\beta=45°$'
             '\nblue = usable part, pink = target set but not usable')
ax.legend(loc='lower left', fontsize=7, framealpha=0.9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig06_up_boresight.png'))
plt.close(fig)

# ===========================================================================
# Fig. 8 -- maximum-range barrier trajectories, head-on region
# ===========================================================================
fig, ax = plt.subplots(figsize=(5.4, 5.0))
seeds = []
for q2 in np.concatenate([np.linspace(-0.35, -0.003, 200),
                          np.linspace(0.003, 0.35, 200)]):
    for q1 in B.bup_maxrange(q2):
        seeds.append((q1, q2))
ntraj = 0
for q1, q2 in seeds:
    y0 = np.array([B.R_hi(q2), q1, q2, *B.lam_maxrange(q2)])
    tr = B.integrate_retrograde(y0, tau_max=0.42, dt=5e-4)
    # colour by which family the seed belongs to -- the two families terminating
    # on e_1 f_1 0 and on e_1' d_1' 0 are what intersect along the evader's
    # dispersal line in the printed figure.
    c = '#1f5fa8' if q2 > 0 else '#c1442a'
    ax.plot(tr['phi2'] / D, tr['phi1'] / D, '-', lw=0.5, color=c, alpha=0.55)
    ntraj += 1
qq = np.linspace(-0.35, 0.35, 901)
bup_x, bup_y = [], []
for q2 in qq:
    if abs(q2) < 1e-3:
        continue
    for q1 in B.bup_maxrange(q2):
        bup_x.append(q2 / D)
        bup_y.append(q1 / D)
ax.plot(bup_x, bup_y, 'k.', ms=1.2)
mark(ax, ['e_1', 'f_1', 'd_1', 'c_1'], 'phi2', 'phi1')
ax.set_xlim(20, -20)
ax.set_ylim(-45, 45)
ax.set_xlabel(r'$\phi_2$  [deg]')
ax.set_ylabel(r'$\phi_1$  [deg]')
ax.set_title('Fig. 8 reconstructed — maximum-range barrier trajectories,\n'
             'head-on region (%d retrograde trajectories from the (BUP)$_1$)' % ntraj)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig08_barriers_headon.png'))
plt.close(fig)

# ===========================================================================
# Fig. 10 -- barrier supported by the off-boresight limit surface phi_1 = beta
# ===========================================================================
fig, ax = plt.subplots(figsize=(6.6, 5.0))
p2 = np.linspace(-np.pi, np.pi, 1601)
ax.plot(p2 / D, B.R_hi(p2), 'k-', lw=1.0)
ax.plot(p2 / D, B.R_lo(p2), 'k-', lw=1.0)
n_ok = 0
for q2 in np.linspace(-np.pi + 0.01, np.pi - 0.01, 240):
    R0 = B.bup_boresight(q2, +1)
    if R0 is None:
        continue
    y0 = np.array([R0, B.BETA, q2, *B.lam_boresight(R0, B.BETA, q2)])
    tr = B.integrate_retrograde(y0, tau_max=2.5, dt=1e-3)
    ax.plot(tr['phi2'] / D, tr['R'], '-', lw=0.6, color='#1f5fa8', alpha=0.8)
    n_ok += 1
Lb = (np.sin(B.BETA) + np.sin(p2))
ax.plot(p2 / D, np.where(Lb > 0, Lb, np.nan), 'b--', lw=1.4)
mark(ax, ['A_1', 'B_1', 'Q_1', 'Qt_1', 'J_1', 'M_1', 'K_1', 'N_1', 'Z_1',
          'h_1', 'g_1', 'V_1', 'q_1', 'm_1', 'Y_1'], 'phi2', 'R')
ax.set_xlim(180, -180)
ax.set_ylim(6.6, 0)
ax.set_xticks([180, 90, 0, -90, -180])
ax.set_xlabel(r'$\phi_2$  [deg]')
ax.set_ylabel(r'$R$')
ax.set_title(r'Fig. 10 reconstructed — barrier supported by $\phi_1=\beta$'
             '\n(%d retrograde trajectories, projected on the $\\phi_1=\\beta$ plane)' % n_ok)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig10_barrier_boresight.png'))
plt.close(fig)

# ===========================================================================
# Fig. 11 -- minimum-range barriers, viewed from infinite R
# ===========================================================================
fig, ax = plt.subplots(figsize=(6.6, 4.4))
n_ok = 0
for q2 in np.linspace(-np.pi + 0.02, np.pi - 0.02, 300):
    if abs(np.sin(q2)) < 0.02:
        continue
    for q1 in B.bup_minrange(q2):
        y0 = np.array([B.R_lo(q2), q1, q2, *B.lam_minrange(q2)])
        tr = B.integrate_retrograde(y0, tau_max=3.0, dt=1e-3)
        ax.plot(tr['phi2'] / D, tr['phi1'] / D, '-', lw=0.5,
                color='#1f5fa8', alpha=0.6)
        n_ok += 1
mark(ax, ['g_1', 'h_1', 'M_1', 'N_1', 'K_1', 'V_1', 'q_1', 'm_1', 'I_1', 'p_1', 'v_1'],
     'phi2', 'phi1')
ax.axhline(B.BETA / D, color='0.4', lw=0.8, ls='--')
ax.axhline(-B.BETA / D, color='0.4', lw=0.8, ls='--')
ax.set_xlim(180, -180)
ax.set_ylim(-180, 180)
ax.set_xticks([180, 90, 0, -90, -180])
ax.set_yticks([-180, -90, 0, 90, 180])
ax.set_xlabel(r'$\phi_2$  [deg]')
ax.set_ylabel(r'$\phi_1$  [deg]')
ax.set_title('Fig. 11 reconstructed — minimum-range barrier trajectories,\n'
             'viewed from infinite $R$ (%d trajectories)' % n_ok)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig11_barriers_minrange.png'))
plt.close(fig)

# ===========================================================================
# Invariant drift -- the integration's own error certificate
# ===========================================================================
fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.2))
for q2 in np.linspace(-np.pi + 0.1, np.pi - 0.1, 25):
    if abs(np.sin(q2)) < 0.05:
        continue
    for q1 in B.bup_minrange(q2):
        y0 = np.array([B.R_lo(q2), q1, q2, *B.lam_minrange(q2)])
        tr = B.integrate_retrograde(y0, tau_max=6.0, dt=1e-3)
        axes[0].semilogy(tr['tau'], np.maximum(tr['fi_err'], 1e-18), lw=0.5, alpha=0.6)
        axes[1].semilogy(tr['tau'], np.maximum(tr['h_err'], 1e-18), lw=0.5, alpha=0.6)
axes[0].set_title(r'first integral, Eq. (23):  $|(\lambda_1+\lambda_2)^2/R^2+\lambda_R^2-1|$')
axes[1].set_title(r'semipermeability, Eq. (15):  $|H^*|$')
for a in axes:
    a.set_xlabel(r'retrograde time $\tau$')
    a.set_ylim(1e-18, 1e-6)
fig.suptitle('Invariant drift along minimum-range barrier trajectories '
             '(RK4, dt = 1e-3, switches located)', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_invariants.png'))
plt.close(fig)

print('wrote figures to %s' % os.path.abspath(OUT))
for f in sorted(os.listdir(OUT)):
    if f.endswith('.png'):
        print('   ', f)
