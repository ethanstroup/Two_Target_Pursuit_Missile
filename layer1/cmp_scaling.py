"""
cmp_scaling.py -- does the choice of ell weighting move the COMPUTED zero level set?

In exact arithmetic it cannot: the weights are positive, so {ell <= 0} and hence
{V <= 0} are weight-invariant (Plan Sec. 2.1).  Numerically it can, because the
weighting changes how well the scheme resolves the surface.  That difference is
the whole practical content of the Sec. 2.1 conditioning argument, so measure it
rather than reasoning about it.
"""
import sys, os, time
import numpy as np

N = int(sys.argv[1]) if len(sys.argv) > 1 else 61
T = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0

res = {}
for s in ('raw', 'plan', 'sdist'):
    os.environ['LAYER1_ELL_SCALING'] = s
    for m in ('ell', 'hji'):
        sys.modules.pop(m, None)
    import ell as E, hji, jax.numpy as jnp
    assert E.SCALING == s
    grid = hji.make_grid(n_R=N, n_phi=N)
    V0 = E.ell_on_grid(grid)
    t0 = time.time()
    V = np.asarray(hji.solve_backward(hji.TwoTargetPursuit(), grid, jnp.asarray([0.0, -T]), V0))[-1]
    res[s] = (V <= 0)
    Rg = np.asarray(grid.coordinate_vectors[0])
    edge = Rg[np.where(res[s].any(axis=(1, 2)))[0].max()]
    print('%-6s  solve %5.1f s   {V<=0} = %6.3f%% of grid   outer edge R = %.3f'
          % (s, time.time() - t0, 100 * res[s].mean(), edge))

print()
print('pairwise disagreement of the computed winning zone, %% of grid nodes:')
ks = ('raw', 'plan', 'sdist')
print('        ' + ''.join('%10s' % k for k in ks))
for a in ks:
    print('%-8s' % a + ''.join('%9.4f%%' % (100 * np.mean(res[a] != res[b])) for b in ks))
