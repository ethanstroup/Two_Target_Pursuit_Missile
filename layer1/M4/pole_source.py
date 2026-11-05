"""
pole_source.py -- the field test_m4.py reads when LAYER1_POLE=1: the single-target value V_1 on
the pole grids, solved by M5 and of record since 2026-10-15
(Overview/Layer1/Layer1_M5_PoleRerun_2026-10-15.md, decision 1).

Criteria for the M4 rerun on this field: Overview/Layer1/Layer1_M4_PoleRerun_Criteria_2026-10-29.md.

WHAT IS READ.  VRAsnap_<tag>.npz, written by M5/reach_avoid.py: V(., tau) every 0.25 in tau, as
float32, on the FULL pole grid -- pole.N_GHOST mirror rows below R = 0, then the real rows at
R_i = (i + 1/2) dR.  The mirror rows are kept, so interpolation and gradients just above R = 0 see
the values the solve itself used.  m5_<tag>.json supplies the tau axis, R_nodes and the cell.
Vsnap_RA_<tag>.npz is NOT used: it is every 0.5 and drops the mirror rows.

CHECKED ON LOAD, before anything is returned (any failure stops the run):
  * the solve is single-target on the pole grid (json kind 'single', pole true): M4 tests V_1,
    never the reach-avoid V_RA
  * the solve used the ell weighting this run uses (json scaling == ell.SCALING)
  * pole.make_grid(n_R, n_phi) reproduces every row of the json's R_nodes, mirror rows included
  * the archive's tau keys start at 0, end at T_max and are among the json's march times
  * the tau = 0 snapshot has this grid's shape and its mirror rows equal the mirrored real rows
  * the one-cell value change on this grid equals the json's cell

MEMORY.  The fine archive is 849 MB of float32.  It is stored uncompressed, so np.load opens it
lazily: Stack reads one snapshot, as float64, each time test_m4.Field indexes it.

Usage: from test_m4.py only, e.g.   LAYER1_POLE=1 python test_m4.py 201x204_T6_single_pole
Env:   M4_POLE_DIR   folder holding the pole outputs (default ../M5/m5_out/m5_out_V1_pole)
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'M5'))          # pole.py imports sim_m5 from there

import ell as E                                              # test_m4 put layer1/common on the path
import pole

DIR = os.environ.get('M4_POLE_DIR', os.path.join(HERE, '..', 'M5', 'm5_out', 'm5_out_V1_pole'))
SUFFIX = '_single_pole'


class Stack:
    """V(., tau_k), k = 0 .. K-1, read from the archive on demand as float64."""

    def __init__(self, z, keys):
        self.z, self.keys = z, keys

    def __len__(self):
        return len(self.keys)

    def __getitem__(self, k):
        return self.z[self.keys[k]].astype(np.float64)


def fail(msg):
    raise SystemExit('pole_source: ' + msg)


def read_meta(d, tag):
    """The solve's json, refused unless it is the single-target pole field under this ell weighting."""
    if not tag.endswith(SUFFIX):
        fail('LAYER1_POLE=1 reads single-target pole solves; the tag must end in %s, got %r'
             % (SUFFIX, tag))
    meta = json.load(open(os.path.join(d, 'm5_%s.json' % tag)))
    if meta.get('kind') != 'single' or not meta.get('pole'):
        fail('m5_%s.json is kind %r, pole %r: not the single-target pole field'
             % (tag, meta.get('kind'), meta.get('pole')))
    if meta.get('scaling') != E.SCALING:
        fail('the solve used ell scaling %r but this run uses %r (LAYER1_ELL_SCALING)'
             % (meta.get('scaling'), E.SCALING))
    return meta


def check_rows(grid, meta):
    """Every row of the grid, mirror rows included, sits where the solve put it."""
    R = np.asarray(grid.coordinate_vectors[0])
    Rf = np.asarray(meta['R_nodes'], float)
    if R.size != Rf.size:
        fail('pole.make_grid gives %d rows, the file lists %d' % (R.size, Rf.size))
    off = float(np.max(np.abs(R - Rf)))
    if off > 1e-9:
        fail('pole.make_grid rows differ from the file by up to %.2e' % off)
    return R


def check_taus(keys, meta):
    taus = np.array([float(k) for k in keys])
    march = np.asarray(meta['taus'], float)
    unknown = [t for t in taus if np.min(np.abs(march - t)) > 1e-9]
    if taus[0] != 0.0 or abs(taus[-1] - meta['T_max']) > 1e-9 or unknown:
        fail('snapshot taus %s do not run from 0 to T_max = %g on the march times'
             % (', '.join('%g' % t for t in taus), meta['T_max']))
    return taus


def check_first(v0, grid):
    if tuple(v0.shape) != tuple(grid.shape):
        fail('snapshot shape %s, grid shape %s' % (v0.shape, tuple(grid.shape)))
    res = pole.ghost_residual(v0)
    if res != 0.0:
        fail('tau = 0 mirror rows differ from the mirrored real rows by %.2e' % res)


def load(tag, d=DIR):
    """(grid, Stack, taus, info) for the pole solve <tag>, after every check in the docstring."""
    meta = read_meta(d, tag)
    grid = pole.make_grid(meta['n_R'], meta['n_phi'])
    R = check_rows(grid, meta)
    z = np.load(os.path.join(d, 'VRAsnap_%s.npz' % tag))
    keys = sorted(z.files, key=float)
    taus = check_taus(keys, meta)
    check_first(z[keys[0]], grid)
    cell = E.value_scale(grid)
    if abs(cell - meta['cell']) > 1e-9 * max(1.0, cell):
        fail('one-cell value change %.12f here, %.12f in the file' % (cell, meta['cell']))
    info = dict(dir=os.path.abspath(d), n_mirror=pole.N_GHOST, first_real_R=float(R[pole.N_GHOST]),
                dR=float(R[1] - R[0]), cell=cell, n_snap=len(keys))
    return grid, Stack(z, keys), taus, info
