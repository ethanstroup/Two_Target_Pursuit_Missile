"""
diag_check8_interp.py -- report only.  Can check 8 run on grids whose R rows don't nest?

Pole grids are staggered, R = (i + 1/2) dR, so the fine grid's rows never land on the coarse
grid's rows, and check 8's exact subsampling Vf[::2, ::2, ::2] is not available.  (The angles
still nest: fine node 2k is coarse node k.)  The replacement is to interpolate the fine field
linearly in R onto the coarse rows.

This tests that replacement on the R_min = 0.2 grids, where the rows do nest and check 8's
answer is known.  It scores check 8 twice, with the same metric as test_m5.check_grid:
    exact    the fine value at the coarse node (Vf[2i]), as scored in M5
    interp   the fine value rebuilt from the two fine rows either side, 2i - 1 and 2i + 1,
             ignoring the coincident row (midway, across two fine cells)
The interp case is harsher than the pole grids need: there the two bracketing fine rows are
one fine cell apart, and the coarse node sits between them at a fraction from 0 (R = 12) to
about 1/2 (near the face).  Linear-interpolation error scales with the bracket squared, so
this case has about 4 times the pole grids' worst error.

Usage:  python diag_check8_interp.py
"""

import numpy as np
from scipy import ndimage

import ell as E
import hji
import test_m5 as TM

R_MARGIN = 0.45


def grid_metric(Vc, Vf_at_coarse, Rc):
    """test_m5.check_grid's numbers for a given fine-at-coarse field: displacement in coarse
    cells, flips more than 3 cells from the coarse barrier, all flips, and the far-flip mask."""
    ok = Rc[:, None, None] >= R_MARGIN
    inc, inf_ = (Vc <= 0) & ok, (Vf_at_coarse <= 0) & ok
    bc = TM.surface_mask(inc)
    dis = int(np.count_nonzero(inc != inf_))
    disp = dis / max(int(bc.sum()), 1) * 6
    far = (inc != inf_) & ~ndimage.binary_dilation(bc, iterations=3)
    return disp, int(far.sum()), dis, far


def fine_exact(Vf):
    return Vf[::2, ::2, ::2]


def fine_interp_skip(Vf):
    """Coarse row i from fine rows 2i - 1 and 2i + 1 (midway); the end rows use the coincident row."""
    a = Vf[:, ::2, ::2]
    out = a[::2].copy()
    out[1:-1] = 0.5 * (a[1:-2:2] + a[3::2])
    return out


def main():
    Vc = np.load('m5_out/VRA_101x102_T6.npy')
    Vf = np.load('m5_out/VRA_201x204_T6.npy')
    Rc = np.linspace(0.2, 12.0, Vc.shape[0])
    ex, ip = fine_exact(Vf), fine_interp_skip(Vf)
    print('=' * 96)
    print('Check 8 with the fine field interpolated in R vs exactly subsampled (R_min = 0.2 grids, T = 6)')
    print('=' * 96)
    res = {}
    for name, sub in (('exact  (as scored in M5)', ex), ('interp (rows 2i +/- 1)  ', ip)):
        disp, far, dis, mask = grid_metric(Vc, sub, Rc)
        res[name] = mask
        print('   %s  displacement %.3f coarse cells (bar 0.5);  far flips %d;  all flips %d'
              % (name, disp, far, dis))
    m = np.broadcast_to(Rc[:, None, None] >= R_MARGIN, Vc.shape)
    sign_diff = ((ex <= 0) != (ip <= 0)) & m
    near = ndimage.binary_dilation(TM.surface_mask((ex <= 0) & m), iterations=1)
    print('-' * 96)
    print('   nodes where the interpolated fine sign differs from the exact one: %d of %d (R >= 0.45)'
          % (int(sign_diff.sum()), int(m.sum())))
    print('      of those, more than 1 coarse cell from the fine zero set: %d' % int((sign_diff & ~near).sum()))
    a, b = list(res.values())
    print('   far-flip sets identical: %s' % bool(np.array_equal(a, b)))
    print('   max |interp - exact| at R >= 0.45: %.4f   (coarse delta = %.4f)'
          % (float(np.max(np.abs(ip - ex)[m])), E.value_scale(hji.make_grid(n_R=101, n_phi=102))))
    print('=' * 96)


if __name__ == '__main__':
    main()
