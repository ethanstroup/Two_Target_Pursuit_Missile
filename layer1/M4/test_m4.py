"""
test_m4.py -- Layer 1, Milestone M4.  Acceptance against Layer 0.

Record: Overview/Layer1/Layer1_M4_2026-10-06.md.  Plain-language walkthrough:
Overview/Layer1/Layer1_M4_Explainer.md.  Why each design choice below exists:
Overview/Layer1/Layer1_M4_Audit_2026-10-06.md.

Layer1_Plan.md Sec. 5, as scoped by the 2026-10-01 revision:

    "The 122 trajectories are correct *local* characteristics seeded from the
     single-target BUP.  Layer 0 never did the global assembly that decides which
     parts of each trajectory are actually on the winning-zone boundary. [...] So
     score A-C on each trajectory up to the first point where it leaves {V = 0} by
     more than grid tolerance, report the fraction of trajectory length that
     passes, and list each departure point as a candidate inactive-segment
     junction to check against Table 3, rather than as a failure.
     The R >= 0.45 mask from M3 applies throughout."

WHICH HORIZON TO READ.  V(x, T) is non-increasing in T (the min[0, H] clamp only ever
lowers it).  A point at retrograde time tau on the ACTIVE barrier can graze the target
in time tau and no sooner, so V(x, T) = 0 for every T >= tau and V(x, T) > 0 for T < tau.
The level and gradient tests must therefore read a horizon AT OR ABOVE tau:

    M4_READ=ceil      first snapshot with tau_k >= tau                    (default)
    M4_READ=conv      the converged V(., T_max) everywhere -- the infinite-horizon test

The two agree.  Reading the NEAREST snapshot instead rounds below tau for half the
points, biases V outward, and makes a stack with coarser snapshot spacing look worse.
The M2 rule -- read a feedback law at the REMAINING horizon -- still governs forward
simulation through hji.make_policy; it is not a reason to read below tau here.

WHAT "DEPARTURE SIDE" MEANS:
  * V < -tol  strictly INSIDE the winning zone: the characteristic has crossed into the
    interior, which is what an inactive segment past a junction looks like.
  * V > +tol  OUTSIDE: the grid says player 1 cannot reach from there at all.

DESIGN RULES (each one is in the audit, with the evidence):
  * trajectories with no point above the R mask are UNTESTED and excluded from the
    family statistics, never counted as agreeing
  * pass criteria: C1 aggregate > 90 %; off-boresight median length >= 1.0 at this
    grid's own tolerance.  Resolvable-set rates are printed for information only
  * every headline number has a null beside it: grad ell for test B, the old
    heuristic for C1, ell's own kinks for test E
  * the plan's negative control (heuristic fails C at long range) is SKIPPED, not
    replaced, while no retained point reaches R = 8; the range-band table drops nodes
    where dV/dphi_1 is exactly 0, where the grid law is only a tie-break
  * switches are compared on BOTH sides of each located switch
  * max-range departures are printed next to their phi_2 = 0 (Rbar corner) crossing
  * every number in a printed note is measured in the run

WHICH FIELD.  By default the M3 snapshot stacks on the R_min = 0.2 grid (m3_out/).  With
LAYER1_POLE=1, M5's single-target V_1 on the pole grids, of record since 2026-10-15, read by
pole_source.py (every 0.25 in tau, mirror rows kept).  The pole rerun's criteria were fixed before
it ran: Overview/Layer1/Layer1_M4_PoleRerun_Criteria_2026-10-29.md.

THE ELL NULL AND FORCED DEPARTURES (report only; criteria doc Sec. 4).  The same walk with V
replaced by ell on this grid (the tau = 0 snapshot) gives the agreement length owed to the target
set alone.  V <= ell node for node (V is non-increasing in tau), so where the grid's ell is below
-tol at a departure point, V had to be too: the trajectory is inside T_1 there and the departure
says nothing about the solve.  Each departure is printed as forced, own (V < -tol <= ell) or outside.

MIN-RANGE ON THE POLE GRID (pole runs only; criteria doc Sec. 5).  The min-range family is walked at
R >= 0.20 and classified by its ell null: enters T_1, stays within a cell of it, or leaves it
outward.  Only the outward ones can show the solve's own work; with fewer than 10 of them the
family is NOT TESTABLE.

Usage:  python3 test_m4.py [grid_tag]
        LAYER1_POLE=1 python3 test_m4.py [101x102_T6_single_pole | 201x204_T6_single_pole]
Env:    M4_READ (ceil|conv), M4_TOL (pin the tolerance), R_MARGIN (default 0.45),
        LAYER1_ELL_SCALING (raw|plan|sdist), LAYER1_POLE (0|1), M4_POLE_DIR (pole_source.py).
"""

import os
import sys
import textwrap

import numpy as np
import jax.numpy as jnp

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))

import hji                      # must come first: puts layer0/ on sys.path, enables x64
import ell as E
import barrier as B
import l0_traj

POLE = os.environ.get('LAYER1_POLE', '0').strip() == '1'
TAG = sys.argv[1] if len(sys.argv) > 1 else ('101x102_T6_single_pole' if POLE else '101x102_T6')
R_MARGIN = float(os.environ.get('R_MARGIN', '0.45'))
READ = os.environ.get('M4_READ', 'ceil')
M3 = '../M3/m3_out'
D = 180.0 / np.pi
GCUT = 0.15          # |dV/dphi_i| below which a bang-bang sign is reported as unresolvable
FAMILIES = ('max-range', 'min-range', 'boresight')
PER_TRAJ = 240       # samples per trajectory (every 0.025 in tau)

# Min-range on the pole grid, fixed in the criteria doc Sec. 5 before the run
R_MINRANGE = 0.20    # every min-range sample (lowest R 0.242); above the rows M5 check 4 flagged
MR_MIN_INFORMATIVE = 10
MR_EXCESS = 0.5      # median of (V agreement length - ell-null length) over informative trajectories

FAILS = []
SKIPS = []
NOT_TESTABLE = []
NOTES = []


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(name, ok, msg=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + msg) if msg else ''))
    if not ok:
        FAILS.append(name)


def skip(name, why):
    print('  SKIP  ' + name + '   ' + why)
    SKIPS.append(name)


def not_testable(name, why):
    print('  NOT TESTABLE  ' + name + '   ' + why)
    NOT_TESTABLE.append(name)


def section(title):
    print()
    print('-' * 94)
    print(title)
    print('-' * 94)


def pct(k, n):
    return 100.0 * k / max(n, 1)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_snapshots(tag):
    """
    V(.,tau) stack and its tau axis, from the M3 run.

    Two on-disk forms are accepted.  solve_m3.py writes one archive,
    m3_out/Vsnap_<tag>.npz.  At 201x204^2 that is 69 MB, over the 20 MB per-file
    limit of the desktop bridge, so the fine-grid stack also exists split one
    snapshot per file under m3_out/Vsnap_<tag>_parts/tau_<value>.npz (each ~12 MB).
    """
    mono = M3 + '/Vsnap_%s.npz' % tag
    if os.path.exists(mono):
        z = np.load(mono)
        taus = np.array(sorted(float(k) for k in z.files))
        return np.stack([z['%.3f' % t].astype(np.float64) for t in taus]), taus
    import glob
    parts = sorted(glob.glob(M3 + '/Vsnap_%s_parts/tau_*.npz' % tag),
                   key=lambda p: float(os.path.basename(p)[4:-4]))
    if not parts:
        raise FileNotFoundError(
            'need %s/Vsnap_%s.npz or %s/Vsnap_%s_parts/. Regenerate with '
            '"python3 solve_m3.py <n_R> <n_phi> 6.0" (about 13 min at 101x102, 4 h at '
            '201x204, run in M3/).' % (M3, tag, M3, tag))
    taus = np.array([float(os.path.basename(p)[4:-4]) for p in parts])
    return np.stack([np.load(p)['V'].astype(np.float64) for p in parts]), taus


def grid_for(tag):
    nR, rest = tag.split('x')
    nphi = rest.split('_')[0]
    return hji.make_grid(n_R=int(nR), n_phi=int(nphi))


def load_field(tag):
    """(grid, V(., tau) stack, taus, one-line description) for the field this run reads."""
    if POLE:
        import pole_source
        grid, Vs, taus, info = pole_source.load(tag)
        return grid, Vs, taus, ('pole single-target V_1 (%d mirror rows, first real row R = %.4f, '
                                'dR = %.4f) in %s' % (info['n_mirror'], info['first_real_R'],
                                                      info['dR'], info['dir']))
    Vs, taus = load_snapshots(tag)
    return grid_for(tag), Vs, taus, 'M3 snapshots on the R_min = 0.2 grid in %s' % M3


# ---------------------------------------------------------------------------
# Reading V and grad V
# ---------------------------------------------------------------------------

def snapshot_index(taus, tau, rule=READ):
    """Which snapshot a point at retrograde time tau is read from (see the docstring)."""
    if rule == 'ceil':
        return int(min(np.searchsorted(taus, tau - 1e-9), len(taus) - 1))
    if rule == 'conv':
        return len(taus) - 1
    raise ValueError('M4_READ must be ceil or conv, got %r' % rule)


class Field:
    """
    V and grad V at sampled (x, tau).

    MEMORY.  One interpolator pair per snapshot is 1.9 GB at 201x204^2 and gets the
    process killed.  So every sample point is collected first, grouped by the snapshot
    it reads, and the snapshots are visited ONE AT A TIME.  Peak memory is one
    snapshot's gradient field.
    """

    def __init__(self, grid, Vs, taus, rule=READ):
        self.grid, self.Vs, self.taus, self.rule = grid, Vs, taus, rule

    def evaluate(self, pts, k=None):
        """
        pts: list of (key, x, tau).  Returns {key: (V, gradV)}.
        k, if given, forces every point onto that one snapshot (k=0 reads ell itself).
        """
        by_k = {}
        for key, x, tau in pts:
            kk = snapshot_index(self.taus, tau, self.rule) if k is None else k
            by_k.setdefault(kk, []).append((key, x))
        out = {}
        for kk in sorted(by_k):
            vi = hji.make_interp(self.grid, jnp.asarray(self.Vs[kk]))
            gi = hji.make_interp(self.grid, hji.grad_field(self.grid, jnp.asarray(self.Vs[kk])))
            for key, x in by_k[kk]:
                out[key] = (float(vi(x)), np.asarray(gi(x)))
            del vi, gi
        return out


# ---------------------------------------------------------------------------
# Trajectory helpers
# ---------------------------------------------------------------------------

def state(tr, i):
    return np.array([tr['R'][i], tr['phi1'][i], tr['phi2'][i]])


def costate(tr, i):
    return np.array([tr['lR'][i], tr['l1'][i], tr['l2'][i]])


def l0_control(tr, i):
    """barrier.py's (sigma_1, sigma_2) at sample i of a Layer 0 trajectory."""
    return B.barrier_controls(tr['R'][i], tr['phi1'][i], tr['phi2'][i],
                              tr['lR'][i], tr['l1'][i], tr['l2'][i])


def heuristic_control(phi):
    """The old pursuit heuristic sigma = -sign(phi), with sign(0) broken to +1."""
    return -float(np.sign(phi)) or 1.0


def angle_deg(g, lam):
    """Angle between two vectors in degrees, or None if either is ~0."""
    ng, nl = np.linalg.norm(g), np.linalg.norm(lam)
    if ng < 1e-12 or nl < 1e-12:
        return None
    return D * float(np.arccos(np.clip(np.dot(g, lam) / (ng * nl), -1.0, 1.0)))


def kink_crossing_tau(tr):
    """First retrograde time at which phi_2 crosses 0 (the corner of Rbar(phi_2)), or None."""
    p2 = np.asarray(tr['phi2'])
    s = np.sign(p2)
    cross = np.where((s[:-1] * s[1:] < 0) & (np.abs(p2[:-1]) < np.pi / 2))[0]
    return float(tr['tau'][cross[0] + 1]) if len(cross) else None


# ---------------------------------------------------------------------------
# The scoped walk: how far does each trajectory stay on {V = 0}?
# ---------------------------------------------------------------------------

def sample_points(trs, per_traj=PER_TRAJ, r_min=R_MARGIN, fams=FAMILIES):
    """Every (trajectory, index) pair to look at: families `fams`, at R >= r_min."""
    pts = []
    for j, (fam, tr) in enumerate(trs):
        if fam not in fams:
            continue
        n = len(tr['tau'])
        step = max(1, n // per_traj)
        for i in range(0, n, step):
            if tr['R'][i] < r_min:
                continue
            pts.append(((j, i), state(tr, i), float(tr['tau'][i])))
    return pts


def walk(j, tr, vals, tol):
    """
    Walk trajectory j from tau = 0 and stop at the first sampled point, inside the
    R mask, where |V| > tol.

    `tested` is False when the trajectory has NO sampled point above the R mask.  Such a
    trajectory was never compared with anything and must not be counted as agreeing.
    """
    keep = []
    dep_tau = dep_side = dep_state = dep_V = dep_i = None
    n_tested = 0
    idx = sorted(i for (jj, i) in vals if jj == j)
    for i in idx:
        v = vals[(j, i)][0]
        if not np.isfinite(v):
            continue
        n_tested += 1
        if abs(v) <= tol:
            keep.append(i)
        else:
            dep_tau = float(tr['tau'][i])
            dep_side = 'inside' if v < 0 else 'outside'
            dep_state = state(tr, i)
            dep_V = v
            dep_i = i
            break
    return dict(keep=keep, dep_tau=dep_tau, dep_side=dep_side, dep_state=dep_state,
                dep_V=dep_V, dep_i=dep_i, tau_end=float(tr['tau'][-1]),
                tested=n_tested > 0, n_tested=n_tested)


def length(w):
    """Agreement length of one walk: its departure time, or the trajectory's end if it never left."""
    return w['dep_tau'] if w['dep_tau'] is not None else w['tau_end']


def departure_kind(w, j, lvals, tol):
    """
    never | outside | forced | own.  'forced': V < -tol where the grid's ell is also below -tol, so
    the point is inside T_1 and V <= ell made the departure; 'own': V < -tol <= ell, the solve's own.
    """
    if w['dep_tau'] is None:
        return 'never'
    if w['dep_side'] == 'outside':
        return 'outside'
    return 'forced' if lvals[(j, w['dep_i'])][0] < -tol else 'own'


def family_stats(walks, fam):
    """Agreement length and departure sides over the TESTED trajectories of one family."""
    sel = [w for f, _, w in walks if f == fam]
    tested = [w for w in sel if w['tested']]
    lengths = np.array([w['dep_tau'] if w['dep_tau'] is not None else w['tau_end']
                        for w in tested])
    sides = [w['dep_side'] for w in tested if w['dep_side']]
    return dict(n=len(sel), n_tested=len(tested),
                median=float(np.median(lengths)) if len(lengths) else np.nan,
                max=float(lengths.max()) if len(lengths) else np.nan,
                inside=sides.count('inside'), outside=sides.count('outside'),
                never=sum(1 for w in tested if w['dep_tau'] is None))


# ---------------------------------------------------------------------------
# Test A
# ---------------------------------------------------------------------------

def test_A(walks, fld, tol, own_cell):
    section('A.  Level test  --  |V(x(tau), T)| with T >= tau, scored to first departure')
    print('   %-11s %9s  %-26s  %s' % ('family', 'tested/n', 'agreement length in tau',
                                       'departure side (tested only)'))
    stats = {}
    for fam in FAMILIES:
        s = family_stats(walks, fam)
        stats[fam] = s
        print('   %-11s %4d/%-4d  median %.2f, max %.2f         %d inside / %d outside / %d never left'
              % (fam, s['n_tested'], s['n'], s['median'], s['max'], s['inside'], s['outside'],
                 s['never']))
    untested = sum(s['n'] - s['n_tested'] for s in stats.values())
    if untested:
        NOTES.append('%d trajectories have no sampled point above R = %.2f and are excluded from '
                     'the family statistics (by family: %s). They were never compared with V.'
                     % (untested, R_MARGIN, ', '.join('%s %d' % (f, s['n'] - s['n_tested'])
                                                      for f, s in stats.items()
                                                      if s['n'] > s['n_tested'])))
    print()

    # The seeds are on dT_1 by construction and the tau = 0 snapshot IS ell, so this checks
    # the grid's interpolation of ell, not the solve.  The converged value is printed beside
    # it for information only.
    seedpts = [(('seed', jj), state(tr, 0), 0.0)
               for jj, (fam, tr, w) in enumerate(walks) if tr['R'][0] >= R_MARGIN]
    seed0 = np.array([abs(v[0]) for v in fld.evaluate(seedpts, k=0).values()])
    seedc = np.array([v[0] for v in fld.evaluate(seedpts, k=len(fld.taus) - 1).values()])
    report('BUP seeds interpolate to ell = 0 on the tau = 0 snapshot (checks ell, not the solve)',
           seed0.max() <= tol, 'max |ell| = %.2e over %d masked seeds' % (seed0.max(), len(seed0)))
    print('         converged V at the same seeds: median %+.4f, min %+.4f, max %+.4f  (report only)'
          % (np.median(seedc), seedc.min(), seedc.max()))

    bore = stats['boresight']
    report('the off-boresight family agrees over a usable stretch (median >= 1.0)',
           bore['n_tested'] > 0 and bore['median'] >= 1.0,
           'median agreement length tau = %.2f over %d tested, tolerance %.4f%s'
           % (bore['median'], bore['n_tested'], tol,
              '' if abs(tol - own_cell) < 1e-12 else ' (PINNED; own cell %.4f)' % own_cell))
    return stats


def maxrange_diagnostics(walks):
    """Departure of each max-range trajectory against its crossing of phi_2 = 0."""
    rows = []
    for f, tr, w in walks:
        if f != 'max-range' or not w['tested']:
            continue
        rows.append((D * float(tr['phi2'][0]), kink_crossing_tau(tr), w['dep_tau'], w['dep_side']))
    if not rows:
        return
    print()
    print('   max-range: seed phi_2, crossing of phi_2 = 0 (the Rbar corner), departure')
    for p2, tk, td, side in rows:
        print('     seed phi_2 %+7.2f deg   crosses phi_2 = 0 at tau %s   departs at tau %s (%s)'
              % (p2, '%.3f' % tk if tk is not None else '  -  ',
                 '%.3f' % td if td is not None else '  -  ', side or 'never'))
    gaps = [td - tk for _, tk, td, _ in rows if tk is not None and td is not None]
    if gaps:
        NOTES.append('max-range: %d of %d tested trajectories cross phi_2 = 0, the corner of '
                     'Rbar(phi_2), and depart; %d of those depart AFTER the crossing. Departure '
                     'minus crossing time: median %.3f, range %.3f to %.3f. Past that corner the '
                     'costate still carries the other face\'s normal '
                     '(Overview/Layer1/Layer1_M4_Audit_2026-10-06.md item 4).'
                     % (len(gaps), len(rows), sum(1 for g in gaps if g > 0), np.median(gaps),
                        min(gaps), max(gaps)))


def null_report(walks, nulls):
    """Report only: the ell-null length beside V's, and what made each departure (criteria Sec. 4)."""
    print()
    print('   report only -- the ell null (V replaced by ell on this grid) and what made each departure')
    print('   %-11s %7s   %-24s %-16s %s' % ('family', 'tested', 'ell-null length', 'V minus null',
                                           'departures: inside forced / own, outside, never'))
    for fam in FAMILIES:
        sel = [(w, w0) for (f, tr, w), w0 in zip(walks, nulls) if f == fam and w['tested']]
        if not sel:
            continue
        L = np.array([length(w) for w, _ in sel])
        L0 = np.array([length(w0) for _, w0 in sel])
        kinds = [w['kind'] for w, _ in sel]
        print('   %-11s %7d   median %.3f (max %.2f)   median %+.3f    %3d / %3d, %3d, %3d'
              % (fam, len(sel), np.median(L0), L0.max(), np.median(L - L0), kinds.count('forced'),
                 kinds.count('own'), kinds.count('outside'), kinds.count('never')))


# ---------------------------------------------------------------------------
# Test B
# ---------------------------------------------------------------------------

def test_B(walks, vals, fld):
    section('B.  Gradient test  --  angle between grad V and the Layer 0 costate  (the test to trust)')
    # Scored as an ANGLE, never as a relative error (Plan Sec. 5's trap, carried from M1).
    # NULL: the same angle with grad ell (the tau = 0 snapshot) in place of grad V.  Near a
    # seed the costate IS the face normal by transversality, so agreement there is owed to
    # the seeding, not to the solve; the null shows how much of each number that is.
    retained = [((jj, i), state(tr, i), 0.0) for jj, (f, tr, w) in enumerate(walks) for i in w['keep']]
    nullvals = fld.evaluate(retained, k=0) if retained else {}
    angs = {}
    for fam in FAMILIES:
        a, a0 = [], []
        for jj, (f, tr, w) in enumerate(walks):
            if f != fam:
                continue
            for i in w['keep']:
                lam = costate(tr, i)
                x = angle_deg(vals[(jj, i)][1], lam)
                x0 = angle_deg(nullvals[(jj, i)][1], lam)
                if x is not None and x0 is not None:
                    a.append(x)
                    a0.append(x0)
        angs[fam] = np.array(a)
        if a:
            print('   %-11s n = %5d   median %6.2f deg   90th %6.2f   %% within 10 deg: %5.1f%%'
                  '   [null, grad ell: median %6.2f]'
                  % (fam, len(a), np.median(a), np.percentile(a, 90),
                     100 * np.mean(np.array(a) < 10), np.median(a0)))
        else:
            print('   %-11s no retained points' % fam)
    ab = angs['boresight']
    report('grad V is parallel to the Layer 0 costate on the retained boresight segments',
           len(ab) > 0 and np.median(ab) < 15.0,
           'median angle %.2f deg over %d points' % (np.median(ab) if len(ab) else np.nan, len(ab)))
    allang = np.concatenate([v for v in angs.values() if len(v)]) if any(len(v) for v in angs.values()) \
        else np.array([])
    report('direction agreement is not a coin flip (median well under 90 deg)',
           len(allang) > 0 and np.median(allang) < 45.0,
           'median %.2f deg over %d retained points' % (np.median(allang) if len(allang) else np.nan,
                                                        len(allang)))


# ---------------------------------------------------------------------------
# Test C1
# ---------------------------------------------------------------------------

def c1_rates(walks, vals):
    """sigma* from grad V vs barrier.py on the retained points: totals and resolvable subset."""
    tot = {1: [0, 0], 2: [0, 0]}
    res = {1: [0, 0], 2: [0, 0]}
    for jj, (f, tr, w) in enumerate(walks):
        for i in w['keep']:
            g = vals[(jj, i)][1]
            sg = hji.feedback(g)
            sb = l0_control(tr, i)
            for p in (1, 2):
                ok = int(float(sg[p - 1]) == sb[p - 1])
                tot[p][0] += 1
                tot[p][1] += ok
                if abs(g[p]) >= GCUT:
                    res[p][0] += 1
                    res[p][1] += ok
    return tot, res


def switch_rows(walks, fld):
    """Every located switch above the R mask, with the grid control and Layer 0's on both sides."""
    rows, pts = [], []
    for jj, (f, tr, w) in enumerate(walks):
        if not w['keep']:
            continue
        tmax = tr['tau'][max(w['keep'])]
        for tsw, which in tr['switches']:
            i = int(np.argmin(np.abs(tr['tau'] - tsw)))
            if tr['R'][i] < R_MARGIN or i == 0 or i + 1 >= len(tr['tau']):
                continue
            key = ('sw', jj, i, which)
            pts.append((key, state(tr, i), float(tr['tau'][i])))
            rows.append(dict(key=key, jj=jj, i=i, which=which, tsw=float(tsw),
                             retained=bool(tsw <= tmax)))
    swvals = fld.evaluate(pts) if pts else {}
    for r in rows:
        f, tr, w = walks[r['jj']]
        p = r['which']
        r['grid'] = float(hji.feedback(swvals[r['key']][1])[p - 1])
        r['l0_at'] = l0_control(tr, r['i'])[p - 1]          # by construction, the post-switch side
        r['l0_pre'] = l0_control(tr, r['i'] - 1)[p - 1]     # tau just below the switch
        r['l0_post'] = l0_control(tr, r['i'] + 1)[p - 1]    # tau just above the switch
        r['gap'] = (w['dep_tau'] - r['tsw']) if w['dep_tau'] is not None else None
        r['dep_side'] = w['dep_side']
        r['dep_kind'] = w['kind']
        r['seed_abs_phi2'] = round(abs(float(tr['phi2'][0])), 6)
    return rows


def print_switches(rows):
    ret = [r for r in rows if r['retained']]
    agree = lambda sel, k: (sum(r['grid'] == r[k] for r in sel), len(sel))
    for lab, sel in (('inside the retained segments', ret), ('every masked switch', rows)):
        k_at, n = agree(sel, 'l0_at')
        k_pre, _ = agree(sel, 'l0_pre')
        k_post, _ = agree(sel, 'l0_post')
        print('   switches, %-29s n = %3d   grid = L0 at the switch %5.1f%%   pre-side %5.1f%%   '
              'post-side %5.1f%%' % (lab, n, pct(k_at, n), pct(k_pre, n), pct(k_post, n)))
    if not ret:
        return
    gaps = [r['gap'] for r in ret if r['gap'] is not None]
    sides = [r['dep_side'] for r in ret if r['dep_side']]
    nseed = len(set(r['seed_abs_phi2'] for r in ret))
    print('   retained switches: %d distinct |seed phi_2| (mirror images share one), '
          'departure follows at gap median %s, max %s; sides %d inside (%d forced) / %d outside'
          % (nseed, '%.3f' % np.median(gaps) if gaps else '-', '%.3f' % max(gaps) if gaps else '-',
             sides.count('inside'), sum(1 for r in ret if r['dep_kind'] == 'forced'),
             sides.count('outside')))
    NOTES.append('Located switches inside retained segments: the grid matches barrier.py on the '
                 'pre-switch side at %d of %d and at the switch itself at %d of %d '
                 '(barrier_controls returns the post-switch control at a snapped zero). They come '
                 'from %d distinct |seed phi_2| values, so they are not independent draws.'
                 % (agree(ret, 'l0_pre')[0], len(ret), agree(ret, 'l0_at')[0], len(ret), nseed))


def test_C1(walks, vals, fld):
    section('C1. Feedback law on the barrier  --  sigma* from grad V vs barrier.py, incl. switches')
    tot, res = c1_rates(walks, vals)
    for p in (1, 2):
        n, k = tot[p]
        rn, rk = res[p]
        print('   sigma_%d*  all retained points: %5d of %5d  (%.1f%%)   '
              '|dV/dphi_%d| >= %.2f: %5d of %5d  (%.1f%%)  [report only]'
              % (p, k, n, pct(k, n), p, GCUT, rk, rn, pct(rk, rn)))
    rows = switch_rows(walks, fld)
    print_switches(rows)
    # Pass criterion: aggregate agreement > 90 %, fixed before the run.
    for p in (1, 2):
        n, k = tot[p]
        report('sigma_%d* reproduces barrier.py on the retained segments (> 90%%)' % p,
               n > 0 and k / n > 0.90, '%.1f%% of %d points' % (pct(k, n), n))
    return res


# ---------------------------------------------------------------------------
# Negative control
# ---------------------------------------------------------------------------

def heuristic_on_c1(walks, vals):
    """Heuristic vs grad V against barrier.py, on the resolvable C1 points.  {p: (n, grid_ok, heur_ok)}"""
    out = {}
    for p in (1, 2):
        n = kg = kh = 0
        for jj, (f, tr, w) in enumerate(walks):
            for i in w['keep']:
                g = vals[(jj, i)][1]
                if abs(g[p]) < GCUT:
                    continue
                sb = l0_control(tr, i)[p - 1]
                n += 1
                kg += int(float(hji.feedback(g)[p - 1]) == sb)
                kh += int(heuristic_control(tr['phi1' if p == 1 else 'phi2'][i]) == sb)
        out[p] = (n, kg, kh)
    return out


def range_band_disagreement(grid, Vconv, bands):
    """
    Grid law vs heuristic for sigma_1 over the whole domain, by R band.  Nodes where
    dV/dphi_1 is EXACTLY zero are excluded and counted: there V = ell does not depend on
    phi_1, the grid law is the tie-break constant, and half-grid disagreement is forced.
    """
    G1 = np.ascontiguousarray(np.asarray(hji.grad_field(grid, jnp.asarray(Vconv)))[..., 1])
    Rg = np.asarray(grid.coordinate_vectors[0])
    pg = np.asarray(grid.coordinate_vectors[1])
    s_grid = np.where(G1 >= 0, -1.0, 1.0)
    s_heur = np.broadcast_to(np.where(pg > 0, -1.0, 1.0)[None, :, None], G1.shape)
    out = []
    for lo, hi in bands:
        band = np.broadcast_to(((Rg >= lo) & (Rg < hi))[:, None, None], G1.shape)
        flat = band & (G1 == 0)
        live = band & (G1 != 0)
        dis = float((s_grid[live] != s_heur[live]).mean()) if live.any() else np.nan
        out.append((lo, hi, float(flat.sum()) / max(int(band.sum()), 1), dis))
    del G1
    return out


def negative_control(walks, vals, grid, Vconv):
    section('Negative control  --  the old pursuit heuristic sigma_i = -sign(phi_i)')
    hc = heuristic_on_c1(walks, vals)
    for p in (1, 2):
        n, kg, kh = hc[p]
        print('   sigma_%d on the resolvable C1 points (n = %d):  grad V %.1f%%   heuristic %.1f%%'
              % (p, n, pct(kg, n), pct(kh, n)))
    rmax = max([tr['R'][i] for _, tr, w in walks for i in w['keep']] or [np.nan])
    far = [(jj, i) for jj, (f, tr, w) in enumerate(walks) for i in w['keep'] if tr['R'][i] >= 8.0]
    if not far:
        skip('heuristic fails test C at long range (Plan Sec. 5)',
             'no retained Layer 0 point reaches R = 8 (max retained R = %.2f); needs long-range '
             'ground truth, e.g. the test F simulations' % rmax)
    else:
        n = sum(1 for jj, i in far)
        k = sum(int(heuristic_control(walks[jj][1]['phi1'][i]) == l0_control(walks[jj][1], i)[0])
                for jj, i in far)
        report('heuristic fails test C at long range (below the 90% bar)', k / n < 0.90,
               '%.1f%% of %d points beyond R = 8' % (pct(k, n), n))
    print()
    print('   grid law vs heuristic over the whole domain, by R band (report only):')
    print('     %-11s  %-26s  %s' % ('R band', 'nodes with dV/dphi_1 == 0', 'disagreement on the rest'))
    bands = ((R_MARGIN, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 12))
    for lo, hi, flat, dis in range_band_disagreement(grid, Vconv, bands):
        print('     %4.1f - %4.1f   %6.2f%%                     %s'
              % (lo, hi, 100 * flat, '%6.2f%%' % (100 * dis) if np.isfinite(dis) else '   -'))


# ---------------------------------------------------------------------------
# Min-range on the pole grid (criteria doc Sec. 5)
# ---------------------------------------------------------------------------

MR_CLASS = {'inside': 'enters T_1', 'outside': 'outward', None: 'within a cell'}


def reexit_value(j, tr, idx, vals, lvals, w0, tol):
    """V at the first sample after the null's inside departure where the grid's ell >= 2 tol, or None."""
    if w0['dep_side'] != 'inside':
        return None
    for i in idx:
        if tr['tau'][i] > w0['dep_tau'] and lvals[(j, i)][0] >= 2 * tol:
            return vals[(j, i)][0]
    return None


def minrange_rows(trs, fld, tol):
    """Each tested min-range trajectory at R >= R_MINRANGE: V's walk, the ell null's walk, its class."""
    pts = sample_points(trs, r_min=R_MINRANGE, fams=('min-range',))
    vals = fld.evaluate(pts)
    lvals = fld.evaluate(pts, k=0)
    rows = []
    for j, (fam, tr) in enumerate(trs):
        if fam != 'min-range':
            continue
        w, w0 = walk(j, tr, vals, tol), walk(j, tr, lvals, tol)
        if not w['tested']:
            continue
        idx = sorted(i for (jj, i) in vals if jj == j)
        rows.append(dict(j=j, w=w, w0=w0, cls=MR_CLASS[w0['dep_side']],
                         kind=departure_kind(w, j, lvals, tol),
                         after=reexit_value(j, tr, idx, vals, lvals, w0, tol)))
    return rows


def minrange_block(trs, fld, tol):
    section('MR. Min-range on the pole grid  --  R >= %.2f, against the ell null (criteria doc Sec. 5)'
            % R_MINRANGE)
    rows = minrange_rows(trs, fld, tol)
    print('   %d of %d min-range trajectories have a sample at R >= %.2f'
          % (len(rows), sum(1 for f, _ in trs if f == 'min-range'), R_MINRANGE))
    for cls in ('enters T_1', 'within a cell', 'outward'):
        kinds = [r['kind'] for r in rows if r['cls'] == cls]
        print('   %-14s %3d   V departs: inside forced %d / own %d, outside %d, never %d'
              % (cls, len(kinds), kinds.count('forced'), kinds.count('own'), kinds.count('outside'),
                 kinds.count('never')))
    ent = [r for r in rows if r['cls'] == 'enters T_1']
    early = sum(1 for r in ent if r['w']['dep_side'] == 'inside'
                and r['w']['dep_tau'] <= r['w0']['dep_tau'] + 1e-9)
    print('   enters T_1: V departs inside at or before the null in %d of %d (V <= ell: expected all)'
          % (early, len(ent)))
    after = np.array([r['after'] for r in ent if r['after'] is not None])
    if after.size:
        print('   enters T_1, then climbs to ell >= 2 tol: %d;  V at that first sample: %d within tol, '
              '%d below -tol, %d above +tol  (report only)'
              % (after.size, int((np.abs(after) <= tol).sum()), int((after < -tol).sum()),
                 int((after > tol).sum())))
    inf = [r for r in rows if r['cls'] == 'outward']
    for r in inf:
        tr = trs[r['j']][1]
        print('     outward: seed phi_1 %+6.2f deg, phi_2 %+7.2f deg   V length %.3f   null %.3f   (%s)'
              % (D * tr['phi1'][0], D * tr['phi2'][0], length(r['w']), length(r['w0']), r['kind']))
    if len(inf) < MR_MIN_INFORMATIVE:
        not_testable('min-range family (criteria doc Sec. 5)',
                     '%d outward trajectories, %d needed; on the rest ell alone decides |V| <= tol'
                     % (len(inf), MR_MIN_INFORMATIVE))
        return
    ex = float(np.median([length(r['w']) - length(r['w0']) for r in inf]))
    report('min-range: V agrees beyond the ell null (median excess >= %.1f)' % MR_EXCESS,
           ex >= MR_EXCESS, 'median excess %.3f over %d outward trajectories' % (ex, len(inf)))


# ---------------------------------------------------------------------------
# Test D
# ---------------------------------------------------------------------------

def load_table2():
    """TABLE2 and the surface-residual function from layer0/validate_table2.py, without running it."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'layer0', 'common',
                        'validate_table2.py')
    src = open(path).read()
    ns = {'np': np, 'B': B, 'D': np.pi / 180.0}
    exec(compile(src.split('def main()')[0], 'vt_head', 'exec'), ns)
    return ns['TABLE2'], ns['tests']


def test_D(fld):
    section('D.  Table 2  --  the published significant points  (checks ell, not the solve)')
    TABLE2, tests_fn = load_table2()
    placed = []
    for name, R, d1, d2 in TABLE2:
        resid = tests_fn(R, d1 * np.pi / 180, d2 * np.pi / 180)
        best = min(resid.items(), key=lambda kv: abs(kv[1]))
        if abs(best[1]) <= 2.5e-3:
            placed.append((name, R, d1 * np.pi / 180, d2 * np.pi / 180, best[0]))
    print('   %d of %d Table 2 points lie on a surface the equations determine'
          % (len(placed), len(TABLE2)))
    # T_1 is the intersection of three constraints, so a point can sit on one surface while
    # violating another -- on an extension of that surface, outside dT_1.  Only points on
    # dT_1 itself are eligible for an ell test.
    elig, inelig = [], []
    for rec in placed:
        name, R, p1, p2, surf = rec
        gb, gn, gx = [float(v) for v in E.components(R, p1, p2)]
        (elig if max(gb, gn, gx) < 5e-3 else inelig).append((rec, (gb, gn, gx)))
    print('   of those, %d are on dT_1 itself and %d only on a surface extension outside it'
          % (len(elig), len(inelig)))
    for rec, g in inelig:
        print('     excluded: %-6s on "%s" -- g_bore %+.3f, g_min %+.3f, g_max %+.3f'
              % (rec[0], rec[4][:44], g[0], g[1], g[2]))
    onbd = [rec for rec, _ in elig if rec[1] >= R_MARGIN]
    le = [abs(float(E.ell(R, p1, p2))) for name, R, p1, p2, surf in onbd]
    report('analytic ell vanishes at the eligible Table 2 points (to table precision)',
           len(le) > 0 and max(le) < 5e-3,
           'max |ell| = %.2e over %d masked points on dT_1' % (max(le) if le else np.nan, len(le)))
    pts = [(('t2', name), np.array([R, p1, p2]), float(fld.taus[-1])) for name, R, p1, p2, _ in onbd]
    sgn = np.array([v[0] for v in fld.evaluate(pts, k=len(fld.taus) - 1).values()]) if pts else np.array([0.0])
    print('   under the converged V these points sit at median %+.4f (%d of %d with V <= 0)'
          % (np.median(sgn), int((sgn <= 0).sum()), len(sgn)))
    NOTES.append('Test D checks the analytic ell at points selected because they satisfy the '
                 'same surface equations, so it tests the target geometry, not the solve. The '
                 'points a barrier should genuinely pass through are the UNPLACED interior ones, '
                 'and those belong to test E.')


# ---------------------------------------------------------------------------
# Test E
# ---------------------------------------------------------------------------

def kink_locus(grid, V, mask):
    """Nodes where a one-sided WENO5 derivative changes sign along any axis, inside mask."""
    import hj_reachability as hj
    gl, gr = grid.upwind_grad_values(hj.finite_differences.upwind_first.WENO5, jnp.asarray(V))
    gl, gr = np.asarray(gl), np.asarray(gr)
    jump = np.zeros(V.shape, bool)
    for d in range(3):
        jump |= (gl[..., d] * gr[..., d] < 0)
    del gl, gr
    return jump & mask


def test_E(grid, Vs):
    section('E.  Singular structure  --  where V is non-differentiable')
    Rg = np.asarray(grid.coordinate_vectors[0])
    pg = np.asarray(grid.coordinate_vectors[1])
    mask = np.broadcast_to((Rg >= R_MARGIN)[:, None, None], tuple(grid.shape))
    nmask = int(mask.sum())
    out = {}
    for lab, V in (('ell (null)', Vs[0]), ('converged V', Vs[-1])):
        jump = kink_locus(grid, V, mask)
        top1 = np.argsort(-jump.mean(axis=(0, 2)))[:4]
        top2 = np.argsort(-jump.mean(axis=(0, 1)))[:4]
        out[lab] = jump.sum() / max(nmask, 1)
        print('   %-12s flagged %7.3f%% of masked nodes;  top phi_1 %s deg;  top phi_2 %s deg'
              % (lab, 100 * out[lab], ', '.join('%.0f' % (D * pg[i]) for i in top1),
                 ', '.join('%.0f' % (D * pg[i]) for i in top2)))
        del jump
    frac = out['converged V']
    print('   excess over the ell null: %.3f%% of masked nodes' % (100 * (frac - out['ell (null)'])))
    report('a non-differentiability locus exists and is localized, not diffuse',
           0 < frac < 0.05, '%.3f%% of masked nodes' % (100 * frac))
    NOTES.append('The test E detector also flags smooth extrema and the kinks of ell itself (see the '
                 'null line). Its comparison with D&S Table 3 is test_e_table3.py '
                 '(Overview/Layer1/Layer1_TestE_Table3_2026-10-28.md).')


# ---------------------------------------------------------------------------

def main():
    grid, Vs, taus, field = load_field(TAG)
    fld = Field(grid, Vs, taus, READ)
    own_cell = E.value_scale(grid)
    tol = float(os.environ['M4_TOL']) if 'M4_TOL' in os.environ else own_cell
    dt = np.diff(taus)

    print('=' * 94)
    print('M4  acceptance against Layer 0   grid %s   ell scaling %s   read %s' % (TAG, E.SCALING, READ))
    print('=' * 94)
    print('   field     = %s' % field)
    print('   tolerance = %.5f  (%s; this grid\'s own cell is %.5f)'
          % (tol, 'pinned via M4_TOL' if 'M4_TOL' in os.environ else 'one-cell value change', own_cell))
    print('   R mask    = %.2f   (%s)' % (R_MARGIN, 'as in the M3 run, so the gate reruns unchanged; '
                                         'min-range block at R >= %.2f' % R_MINRANGE if POLE else
                                         'M3: the inner face leaks; results hold on the retained domain'))
    print('   snapshots = %d, spacing %.2f to %.2f in retrograde time' % (len(taus), dt.min(), dt.max()))
    print()

    print('   regenerating Layer 0 trajectories ...', flush=True)
    trs = l0_traj.trajectories()
    fi = max(t['fi_err'].max() for _, t in trs)
    hs = max(t['h_err'].max() for _, t in trs)
    report('Layer 0 bundle reproduces its own invariants',
           fi < 1e-6 and hs < 1e-6, '%d trajectories, max |FI-1| = %.1e, max |H*| = %.1e'
           % (len(trs), fi, hs))
    print()

    pts = sample_points(trs)
    print('   evaluating V and grad V at %d trajectory points, one snapshot at a time ...'
          % len(pts), flush=True)
    vals = fld.evaluate(pts)
    lvals = fld.evaluate(pts, k=0)                      # ell on this grid: the null for test A
    walks = [(fam, tr, walk(j, tr, vals, tol)) for j, (fam, tr) in enumerate(trs)]
    nulls = [walk(j, tr, lvals, tol) for j, (fam, tr) in enumerate(trs)]
    for j, (fam, tr, w) in enumerate(walks):
        w['kind'] = departure_kind(w, j, lvals, tol)

    test_A(walks, fld, tol, own_cell)
    null_report(walks, nulls)
    maxrange_diagnostics(walks)
    test_B(walks, vals, fld)
    test_C1(walks, vals, fld)
    negative_control(walks, vals, grid, Vs[-1])
    if POLE:
        minrange_block(trs, fld, tol)
    test_D(fld)
    test_E(grid, Vs)

    section('Notes carried out of this run (every number below was measured in this run)')
    for i, n in enumerate(NOTES, 1):
        for j, line in enumerate(textwrap.wrap(n, 88)):
            print(('   %d. ' % i if j == 0 else '      ') + line)
    print()
    print('=' * 94)
    extra = (['%d SKIPPED: %s' % (len(SKIPS), ', '.join(SKIPS))] if SKIPS else []) + \
            (['%d NOT TESTABLE: %s' % (len(NOT_TESTABLE), ', '.join(NOT_TESTABLE))] if NOT_TESTABLE else [])
    if FAILS:
        print('M4: %d check(s) FAILED: %s' % (len(FAILS), ', '.join(FAILS))
              + ''.join('; ' + e for e in extra))
    elif extra:
        print('M4 COMPLETE -- every asserted check passed; ' + '; '.join(extra))
    else:
        print('M4 COMPLETE -- all checks passed')
    print('=' * 94)


if __name__ == '__main__':
    main()
