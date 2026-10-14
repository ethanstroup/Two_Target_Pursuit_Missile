"""
diag_pole_check8.py -- report only (added after V1-V4 ran; not pre-registered).

Check 8 failed on 6 coarse/fine sign flips more than 3 cells from the barrier, all at R = 0.554
(claude/Layer1_M5_2026-10-11.md Sec. 4.4).  This asks what the coarse POLE grid says at those
same states, and puts the near-face W_1 share of every grid side by side.

    old coarse   m5_out/VRA_101x102_T6.npy        R_min = 0.2, 101 rows
    old fine     m5_out/VRA_201x204_T6.npy        R_min = 0.2, 201 rows
    pole coarse  m5_out/VRA_101x102_T6_pole.npy   pole, 101 real rows (+3 ghost)

Usage:  python diag_pole_check8.py
"""

import numpy as np
from scipy import ndimage

import pole
import test_m5 as TM
import verify_pole as VP

R_MASK = 0.45


def old_flips(Vc, Vf):
    """check_grid's six far flips: coarse-node indices where coarse and subsampled fine disagree in
    sign more than 3 cells from the coarse barrier, R >= 0.45."""
    Rc = VP.old_R(101)
    sub = Vf[::2, ::2, ::2]
    ok = (Rc >= R_MASK)[:, None, None]
    inc, inf_ = (Vc <= 0) & ok, (sub <= 0) & ok
    near = ndimage.binary_dilation(TM.surface_mask(inc), iterations=3)
    return np.argwhere((inc != inf_) & ~near), sub


def pole_at(Vp_real, Rp, R, j, k):
    """Pole coarse value at (R, phi_j, phi_k): linear in R, angles coincide with the old coarse grid."""
    return float(VP.interp_R(Vp_real[:, j:j + 1, k:k + 1], Rp, np.array([R]))[0, 0, 0])


def near_face_share(V, R, n_phi, lo=R_MASK, hi=1.0):
    Rg, P1, P2 = VP.mesh(R, n_phi)
    m = VP.omega_on(Rg, P1, P2) & (Rg >= lo) & (Rg < hi)
    return 100 * float(np.mean(V[m] <= 0)), int(m.sum())


def main():
    Vc = np.load('m5_out/VRA_101x102_T6.npy')
    Vf = np.load('m5_out/VRA_201x204_T6.npy')
    Vp = pole.strip(np.load('m5_out/VRA_101x102_T6_pole.npy'))
    Rp = np.asarray(pole.make_grid(101, 102).coordinate_vectors[0])[pole.N_GHOST:]
    Rc = VP.old_R(101)
    P = np.degrees(-np.pi + np.arange(102) * 2 * np.pi / 102)

    flips, sub = old_flips(Vc, Vf)
    print('=' * 96)
    print('Check 8 far flips (old coarse vs old fine), and the coarse pole grid at the same states')
    print('=' * 96)
    print('   %d far flips' % len(flips))
    print('      R      phi1     phi2    old coarse   old fine   pole coarse')
    agree = 0
    for i, j, k in flips:
        vp = pole_at(Vp, Rp, Rc[i], j, k)
        agree += int((vp <= 0) == (sub[i, j, k] <= 0))
        print('   %6.3f  %+7.2f  %+7.2f    %+8.4f   %+8.4f    %+8.4f'
              % (Rc[i], P[j], P[k], Vc[i, j, k], sub[i, j, k], vp))
    print('   pole coarse agrees in sign with the old fine grid at %d of %d' % (agree, len(flips)))

    print('-' * 96)
    print('W_1 share of Omega at 0.45 <= R < 1')
    for label, V, R, n in (('old coarse  (R_min 0.2, 101 rows)', Vc, Rc, 102),
                           ('old fine    (R_min 0.2, 201 rows)', Vf, VP.old_R(201), 204),
                           ('pole coarse (101 rows)           ', Vp, Rp, 102)):
        f, m = near_face_share(V, R, n)
        print('   %s  %7.4f%% of %d nodes' % (label, f, m))
    Vp51 = pole.strip(np.load('m5_out/VRA_51x52_T6_pole.npy'))
    R51 = np.asarray(pole.make_grid(51, 52).coordinate_vectors[0])[pole.N_GHOST:]
    f, m = near_face_share(Vp51, R51, 52)
    print('   pole third  (51 rows)            %7.4f%% of %d nodes' % (f, m))
    print('=' * 96)


if __name__ == '__main__':
    main()
