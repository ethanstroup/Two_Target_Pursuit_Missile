import sys, time
import numpy as np, jax.numpy as jnp
import hji, ell as E, hj_reachability as hj

def reflect(a):
    n1,n2=a.shape[1],a.shape[2]
    return a[:, (-np.arange(n1))%n1][:, :, (-np.arange(n2))%n2]

nR=31; T=6.0
for nP in (104, 102):
    g=hji.make_grid(n_R=nR,n_phi=nP)
    pg=np.asarray(g.coordinate_vectors[1])
    on = np.min(np.abs(np.abs(pg)-E.BETA)) < 1e-12
    L=E.ell_on_grid(g)
    t0=time.time()
    V=np.asarray(hji.solve_backward(hji.TwoTargetPursuit(), g, jnp.asarray([0.0,-T]), L))[-1]
    r=np.abs(V-reflect(V))
    print("n_phi=%3d  beta %s node   Rf-residual: max %.3e   nodes>1e-9: %6d (%.4f%%)   [%.0f s]"
          %(nP, "ON " if on else "OFF", r.max(), (r>1e-9).sum(), 100*(r>1e-9).mean(), time.time()-t0))
    if (r>1e-9).any():
        i=np.argwhere(r>1e-9)
        print("           those nodes' |phi_1|: min %.2f deg, max %.2f deg  (beta = 45 deg)"
              %(np.degrees(np.abs(pg[i[:,1]])).min(), np.degrees(np.abs(pg[i[:,1]])).max()))
