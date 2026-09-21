/* bup_curves.js -- ordered seed curves along the boundary of the usable part.
 *
 * Twin of bup_curves.py.  Same algorithm, same constants, same results: the two
 * are cross-checked point by point by test_viz.py, because the explorer and the
 * static figures must be drawing the same object.
 *
 * Integrating retrograde from the (BUP) needs more than a set of seed points.
 * To render the bundle as a SURFACE rather than a pile of curves, the seeds must
 * be ordered along the boundary, so that neighbouring seeds are genuinely
 * neighbours on the barrier.  Sweeping phi_2 and taking whatever roots come back
 * does not do that: where Eq. (32) or Eq. (46) has several roots the naive order
 * jumps between sheets; where a family's admissible interval is disconnected in
 * phi_2 it jumps across the gap; and where two roots merge at a fold the two
 * halves of one smooth curve come back as unrelated lists.
 *
 * Fixed here by continuation:
 *   1. march phi_2 on a fine grid, solving for the roots at each station;
 *   2. match each root to the branch it continues, by linear prediction;
 *   3. join the two branches that die together at a fold;
 *   4. merge runs meeting across the phi_2 = +/- pi seam, which bounds the
 *      coordinate, not the problem;
 *   5. resample at equal arclength, then SNAP back onto the root -- linear
 *      interpolation lands slightly off the (BUP), which shows up as H* ~ 1e-5
 *      at the seed, and a seed that is not semipermeable is not a barrier point.
 *
 * Runs in node (module.exports) and in the browser (window.BupCurves).
 * Requires barrier.js.
 */
'use strict';

(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('../barrier.js'));
  } else {
    root.BupCurves = factory(root.Barrier);
  }
}(typeof self !== 'undefined' ? self : this, function (B) {

  var TWO_PI = 2 * Math.PI;

  // -- continuation ---------------------------------------------------------

  function predict(br) {
    if (br.length === 1) return br[br.length - 1][1];
    var a = br[br.length - 2], b = br[br.length - 1];
    return b[1] + (b[1] - a[1]);
  }

  /* Root set of rootFn continued along p2Grid.  A root continues the branch
     whose linear prediction it is nearest to, if within jumpTol; otherwise it
     opens a new branch.  Greedy on the closest pair, so two branches that
     approach without merging keep their identities. */
  function traceBranches(rootFn, p2Grid, jumpTol) {
    var active = [], done = [];
    p2Grid.forEach(function (q) {
      var rs = rootFn(q);
      if (!rs.length) { done = done.concat(active); active = []; return; }

      var pairs = [];
      active.forEach(function (br, bi) {
        var p = predict(br);
        rs.forEach(function (r, ri) { pairs.push([Math.abs(r - p), bi, ri]); });
      });
      pairs.sort(function (x, y) { return x[0] - y[0]; });

      var usedB = {}, usedR = {};
      pairs.forEach(function (t) {
        if (t[0] > jumpTol || usedB[t[1]] || usedR[t[2]]) return;
        active[t[1]].push([q, rs[t[2]]]);
        usedB[t[1]] = usedR[t[2]] = true;
      });

      var still = [];
      active.forEach(function (br, bi) {
        if (usedB[bi]) still.push(br); else done.push(br);
      });
      rs.forEach(function (r, ri) { if (!usedR[ri]) still.push([[q, r]]); });
      active = still;
    });
    return done.concat(active).filter(function (b) { return b.length > 2; });
  }

  /* The exact point where two roots merge and the curve turns.
     Continuation can only follow a branch to the last phi_2 station where the
     grid still resolves two separate roots; past that the branch simply stops,
     leaving the two sheets a short distance apart at the tip.  Near a fold the
     roots separate like sqrt(phi_2* - phi_2), so that gap is far larger in phi_1
     than the phi_2 step suggests -- on the maximum-range lens it leaves the tip
     about half a degree short of d_1.  Bisecting on "do two roots still exist"
     closes it; at the limit the merged root is the mean of the pair. */
  function refineFold(rootFn, qIn, qOut, iters) {
    iters = iters || 200;
    var lo = qIn, hi = qOut, best = rootFn(qIn);
    for (var i = 0; i < iters; i++) {
      var mid = 0.5 * (lo + hi), rs = rootFn(mid);
      if (rs.length >= 2) { lo = mid; best = rs; } else { hi = mid; }
    }
    return [lo, 0.5 * (Math.min.apply(null, best) + Math.max.apply(null, best))];
  }

  /* Splice the refined fold point into every branch that dies at one, so the tip
     of the curve is the fold itself rather than the last resolved station. */
  function closeFoldTips(branches, rootFn, tol) {
    tol = tol || 6e-2;
    return branches.map(function (br) {
      var b = br.slice();
      [0, -1].forEach(function (end) {
        var at = end === 0 ? b[0] : b[b.length - 1];
        var step = end === 0 ? b[1][0] - b[0][0] : b[b.length - 1][0] - b[b.length - 2][0];
        var qOut = at[0] + 12 * (end === 0 ? -step : step);
        if (rootFn(qOut).length >= 2) return;
        var f = refineFold(rootFn, at[0], qOut);
        if (Math.abs(f[1] - at[1]) > tol) return;
        if (end === 0) b.unshift([f[0], f[1]]); else b.push([f[0], f[1]]);
      });
      return b;
    });
  }

  function near(a, b, tol) {
    return Math.abs(a[0] - b[0]) < tol && Math.abs(a[1] - b[1]) < tol;
  }

  /* Two branches that die at the same place died at a fold: the two sheets of
     one smooth curve meeting where the roots merge.  Splice them so the fold is
     an interior point rather than two loose ends. */
  function joinFolds(branches, tol) {
    tol = tol || 2e-2;
    var out = branches.slice(), changed = true;
    while (changed) {
      changed = false;
      outer:
      for (var i = 0; i < out.length; i++) {
        for (var j = 0; j < out.length; j++) {
          if (i === j) continue;
          var a = out[i], b = out[j];
          var ends = [[-1, -1], [-1, 0], [0, -1], [0, 0]];
          for (var e = 0; e < ends.length; e++) {
            var ae = ends[e][0], be = ends[e][1];
            var pa = ae === -1 ? a[a.length - 1] : a[0];
            var pb = be === -1 ? b[b.length - 1] : b[0];
            if (!near(pa, pb, tol)) continue;
            var aa = ae === -1 ? a : a.slice().reverse();
            var bb = be === 0 ? b : b.slice().reverse();
            var merged = aa.concat(bb.slice(1));
            out = out.filter(function (_, k) { return k !== i && k !== j; });
            out.push(merged);
            changed = true;
            break outer;
          }
        }
      }
    }
    return out;
  }

  /* phi_2 = +pi and -pi are the same aspect angle.  The joined branch carries
     phi_2 UNWRAPPED across the seam so arclength and the drawn polyline stay
     continuous; wrap only when evaluating the equations (seedState does). */
  function mergeSeam(branches, tol) {
    tol = tol || 2e-2;
    var out = branches.slice();
    for (var pass = 0; pass < branches.length; pass++) {
      var joined = false;
      outer:
      for (var i = 0; i < out.length; i++) {
        for (var j = 0; j < out.length; j++) {
          if (i === j) continue;
          var a = out[i], b = out[j];
          var ae = a[a.length - 1], bs = b[0];
          if (Math.abs(Math.abs(ae[0]) - Math.PI) < 0.05 &&
              Math.abs(Math.abs(bs[0]) - Math.PI) < 0.05 &&
              ae[0] * bs[0] < 0 && Math.abs(ae[1] - bs[1]) < tol) {
            var shift = TWO_PI * Math.sign(ae[0] - bs[0]);
            var bb = b.map(function (p) { return [p[0] + shift, p[1]]; });
            out = out.filter(function (_, k) { return k !== i && k !== j; });
            out.push(a.concat(bb));
            joined = true;
            break outer;
          }
        }
      }
      if (!joined) break;
    }
    return out;
  }

  // -- the four families ----------------------------------------------------

  function grid(lo, hi, n) {
    var g = [];
    for (var i = 0; i < n; i++) g.push(lo + (hi - lo) * i / (n - 1));
    return g;
  }

  /* sign(phi_2) in Eq. (32) makes phi_2 = 0 a genuine discontinuity of the root
     set, so the two lobes are traced separately; each is a closed lens folding
     at d_1. */
  function branchesMaxrange(n) {
    n = n || 900;
    var out = [];
    [-1, +1].forEach(function (sgn) {
      var g = grid(2e-4, 0.25, n).map(function (q) { return sgn * q; });
      var br = closeFoldTips(traceBranches(B.bupMaxrange, g, 0.05), B.bupMaxrange);
      out = out.concat(joinFolds(br));
    });
    return out;
  }

  function branchesMinrange(n) {
    n = n || 1600;
    var g = grid(-Math.PI + 1e-3, Math.PI - 1e-3, n);
    var br = closeFoldTips(traceBranches(B.bupMinrange, g, 0.05), B.bupMinrange);
    return mergeSeam(joinFolds(br));
  }

  /* phi_1 is fixed on phi_1 = sgn*beta, so there is no root to trace: the curve
     is R(phi_2) from Eq. (62), defined where that R lies inside the target
     set's range band.  Only the contiguous runs and the seam need handling. */
  function branchesBoresight(sgn, n) {
    n = n || 1600;
    var p1 = sgn * B.PARAMS.beta;
    var runs = [], cur = [];
    grid(-Math.PI, Math.PI, n).forEach(function (q) {
      if (B.bupBoresight(q, sgn) === null) {
        if (cur.length > 2) runs.push(cur);
        cur = [];
      } else {
        cur.push([q, p1]);
      }
    });
    if (cur.length > 2) runs.push(cur);
    return mergeSeam(runs);
  }

  var FAMILIES = {
    'max':   { label: 'maximum range — Eq. (32)',        fn: branchesMaxrange },
    'min':   { label: 'minimum range — Eq. (46)',        fn: branchesMinrange },
    'bore+': { label: 'off-boresight φ₁ = +β — Eq. (62)',
               fn: function (n) { return branchesBoresight(+1, n); } },
    'bore-': { label: 'off-boresight φ₁ = −β — Eq. (62)',
               fn: function (n) { return branchesBoresight(-1, n); } }
  };

  // -- seeds ----------------------------------------------------------------

  /* State + transversality costate at one (BUP) point, Eq. (20).  phi_2 may
     arrive unwrapped past +/- pi (see mergeSeam) and is wrapped here, because
     Eq. (9)'s R_hi uses phi_2 + sin phi_2 unwrapped and is not periodic. */
  function seedState(family, p1, p2) {
    p2 = B.wrap(p2);
    var l;
    if (family === 'max') { l = B.lamMaxrange(p2); return [B.Rhi(p2), p1, p2, l[0], l[1], l[2]]; }
    if (family === 'min') { l = B.lamMinrange(p2); return [B.Rlo(p2), p1, p2, l[0], l[1], l[2]]; }
    var R = B.bupBoresight(p2, p1 > 0 ? +1 : -1);
    l = B.lamBoresight(R, p1);
    return [R, p1, p2, l[0], l[1], l[2]];
  }

  /* Equal arclength in (phi_2, phi_1): continuation crowds points near a fold,
     where the curve turns, and even spacing keeps the sheet's quad strips well
     shaped. */
  function resampleBranch(br, m) {
    if (br.length < 2) return br;
    var d = [0], i;
    for (i = 1; i < br.length; i++) {
      d.push(d[i - 1] + Math.hypot(br[i][0] - br[i - 1][0], br[i][1] - br[i - 1][1]));
    }
    var total = d[d.length - 1];
    if (total <= 0) return br.slice(0, 1);
    var out = [], k = 0;
    for (i = 0; i < m; i++) {
      var t = total * i / (m - 1);
      while (k < d.length - 2 && d[k + 1] < t) k++;
      var f = (t - d[k]) / Math.max(d[k + 1] - d[k], 1e-15);
      out.push([br[k][0] + f * (br[k + 1][0] - br[k][0]),
                br[k][1] + f * (br[k + 1][1] - br[k][1])]);
    }
    return out;
  }

  var ROOT_FN = { 'max': function (q) { return B.bupMaxrange(q); },
                  'min': function (q) { return B.bupMinrange(q); } };

  /* Put resampled points back exactly on the (BUP).  Linear interpolation lands
     slightly off the root of Eq. (32) / Eq. (46) -- enough to leave H* at 1e-5
     at the seed instead of 1e-16.  The boresight families are already exact:
     Eq. (62) gives R in closed form, with no root to solve. */
  function snapToBup(family, pts) {
    var fn = ROOT_FN[family];
    if (!fn) return pts;
    return pts.map(function (p) {
      var rs = fn(B.wrap(p[0]));
      if (!rs.length) return p;
      var best = rs[0];
      rs.forEach(function (r) {
        if (Math.abs(r - p[1]) < Math.abs(best - p[1])) best = r;
      });
      return [p[0], best];
    });
  }

  /* Ordered seed states, one array per connected component of the (BUP). */
  function seeds(family, nseed, n) {
    nseed = nseed || 60;
    var F = FAMILIES[family];
    return {
      label: F.label,
      branches: F.fn(n).map(function (b) {
        return snapToBup(family, resampleBranch(b, nseed)).map(function (p) {
          return seedState(family, p[1], p[0]);
        });
      })
    };
  }

  // -- maximum-range extras: corner edge O-e_1 and the d_1 universal line ----
  //
  // Neither is a root of Eq. (32), so neither comes out of the continuation
  // above. The corner edge is where Rbar has its slope jump at phi_2 = 0; its
  // costate is the corner combination of Eqs. (38)-(41). The universal line of
  // player 1 starts at d_1 (lambda_1 = lambda_1-dot = 0) and is flown with the
  // singular control sigma_1 = 0 (Table 3) to c_1, where it meets the corner
  // sheet. Twin of the same block in bup_curves.py.

  var E1 = 2 * Math.atan(2 / B.PARAMS.Rbar0);          // e_1: 36.0755 deg

  function lamCornerEdge(p1) {                          // Eqs. (39)-(41)
    var R0 = B.PARAMS.Rbar0, s = Math.abs(Math.sin(p1));
    var q = 1 / Math.hypot(Math.cos(p1) + 1, R0 + s);
    return [q * (R0 + s), 0, q * R0 * (Math.cos(p1) + 1) * Math.sign(p1)];
  }

  /* Two ordered seed lists on the corner edge: O -> e_1 and O -> e_1'. */
  function cornerSeeds(nseed) {
    nseed = nseed || 60;
    var R0 = B.PARAMS.Rbar0;
    return [+1, -1].map(function (g) {
      return grid(2e-3, E1 - 1e-4, nseed).map(function (x) {
        var l = lamCornerEdge(g * x);
        return [R0, g * x, 0, l[0], l[1], l[2]];
      });
    });
  }

  function mirror(y) { return [y[0], -y[1], -y[2], y[3], -y[4], -y[5]]; }

  function solve(J, b) {                                // Gaussian elimination
    var n = b.length, A = J.map(function (r, i) { return r.concat([b[i]]); });
    for (var c = 0; c < n; c++) {
      var p = c;
      for (var r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      var t = A[c]; A[c] = A[p]; A[p] = t;
      for (r = c + 1; r < n; r++) {
        var f = A[r][c] / A[c][c];
        for (var k = c; k <= n; k++) A[r][k] -= f * A[c][k];
      }
    }
    var x = new Array(n);
    for (var i = n - 1; i >= 0; i--) {
      var sum = A[i][n];
      for (var j = i + 1; j < n; j++) sum -= A[i][j] * x[j];
      x[i] = sum / A[i][i];
    }
    return x;
  }

  /* Newton with a forward-difference Jacobian; h[k] is the step for x[k]. */
  function newton(F, x, h, iters, tol) {
    for (var it = 0; it < iters; it++) {
      var f = F(x), J = f.map(function () { return []; });
      for (var k = 0; k < x.length; k++) {
        var xp = x.slice(); xp[k] += h[k];
        var fp = F(xp);
        for (var i = 0; i < f.length; i++) J[i][k] = (fp[i] - f[i]) / h[k];
      }
      var dx = solve(J, f.map(function (v) { return -v; }));
      var big = 0;
      for (k = 0; k < x.length; k++) { x[k] += dx[k]; big = Math.max(big, Math.abs(dx[k])); }
      if (big < tol) break;
    }
    return x;
  }

  function l1dotOnBup(p1, p2) {
    var l = B.lamMaxrange(p2);
    return B.costateDot(B.Rhi(p2), p1, p2, l[0], l[1], l[2])[1];
  }

  /* d_1: Eq. (32) = 0 and lambda_1-dot = 0 on the phi_2 < 0 lobe. */
  function d1Seed() {
    var x = newton(function (v) {
      return [B.upMaxrange(v[0], v[1]), l1dotOnBup(v[0], v[1])];
    }, [18.88 * Math.PI / 180, -9.57 * Math.PI / 180], [1e-7, 1e-7], 40, 1e-15);
    var l = B.lamMaxrange(x[1]);
    return [B.Rhi(x[1]), x[0], x[1], l[0], l[1], l[2]];
  }

  function flow(y, sigma, tau, n) {
    for (var i = 0; i < n; i++) y = B.rk4Retro(y, tau / n, sigma);
    return y;
  }

  /* Retrograde time at which the d_1 universal line meets the corner sheet,
     i.e. c_1.  Newton on corner(s, tau_C) = universal(tau_U), states only. */
  function c1Tau(yd) {
    yd = yd || d1Seed();
    var R0 = B.PARAMS.Rbar0;
    var x = newton(function (v) {
      var l = lamCornerEdge(v[0]);
      var a = flow([R0, v[0], 0, l[0], l[1], l[2]], [-1, 1], v[1], 20);
      var b = flow(yd, [0, -1], v[2], 400);
      return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    }, [18.43 * Math.PI / 180, 1.1e-3, 0.1727], [1e-7, 1e-8, 1e-7], 30, 1e-13);
    return x[2];
  }

  /* The singular arc: retrograde RK4 with sigma = (0, sign lambda_2) held.
     Returns the same shape as Barrier.integrateRetrograde. */
  function integrateUniversal(y0, tauMax, dt) {
    dt = dt || 2e-3;
    var sig = [0, Math.sign(y0[5])], n = Math.max(Math.ceil(tauMax / dt), 1);
    var y = y0.slice(), path = [{ tau: 0, y: y.slice() }], fiErr = 0, hErr = 0;
    for (var i = 0; i < n; i++) {
      y = B.rk4Retro(y, tauMax / n, sig);
      path.push({ tau: (i + 1) * tauMax / n, y: y.slice() });
      fiErr = Math.max(fiErr, Math.abs(B.firstIntegral(y[0], y[3], y[4], y[5]) - 1));
      hErr = Math.max(hErr, Math.abs(B.hamiltonianStar(y[0], y[1], y[2], y[3], y[4], y[5])));
    }
    return { path: path, switches: [], fiErr: fiErr, hErr: hErr, sigma: sig };
  }

  /* The d_1 and d_1' universal lines, each flown to c_1 (c_1'). */
  function universalLines(dt) {
    var yd = d1Seed(), tc = c1Tau(yd);
    return [yd, mirror(yd)].map(function (y) { return integrateUniversal(y, tc, dt); });
  }

  // -- off-boresight extras: the two corners of the phi_1 = +/-beta wall -----
  //
  // Twin of the same block in bup_curves.py, which carries the full note.
  //   max-range corner A_1-B_1-A_1: Eqs. (66)-(67) with Eq. (68) CORRECTED
  //     (it is mu-bar_2, and the sign is sign phi_1, not sign phi_2).  Terminal
  //     pair (-s, +sign phi_2), not Eq. (70)'s -sign(sin phi_2).
  //   min-range corner N_1-Z_1-m_1: Eqs. (53)-(56) with both mu's times -1.
  //     Terminal pair Eqs. (57)-(58), switching at Z_1.

  var EPS_VERTEX = 2e-3, EPS_JOIN = 1e-4;

  /* phi_2 of m_1 and N_1 on phi_1 = sgn*beta, closed form.  Returns [m_1, N_1]. */
  function minCornerEnds(sgn) {
    sgn = sgn || 1;
    var P = B.PARAMS, k = Math.hypot(1, P.b), dlt = Math.atan2(1, P.b);
    var c = Math.acos((Math.sin(P.beta) - P.a) / k);
    return [sgn * (c - dlt), sgn * (-c - dlt)];
  }

  function lamCornerMax(p2, sgn) {                      // Eqs. (66)-(68), corrected
    var p1 = sgn * B.PARAMS.beta, R = B.Rhi(p2);
    var L = Math.sin(p1) + Math.sin(p2), s2 = Math.sign(p2);
    var mb1 = (1 - Math.cos(p1)) * R + L * (1 + Math.cos(p2)) * s2;
    var mb2 = R - L * sgn;
    var l = [mb2, mb1 * sgn, mb2 * (1 + Math.cos(p2)) * s2];
    var n = Math.sqrt(B.firstIntegral(R, l[0], l[1], l[2]));
    return [l[0] / n, l[1] / n, l[2] / n];
  }

  function lamCornerMin(p2, sgn) {                      // Eqs. (53)-(56)
    var P = B.PARAMS, p1 = sgn * P.beta, R = B.Rlo(p2);
    var L = Math.sin(p1) + Math.sin(p2), Cc = Math.cos(p1) + Math.cos(p2);
    var ss = Math.sign(Math.sin(p2));
    var m1 = -Cc * R + P.b * Math.sin(p2) * (L - R * ss);
    var m2 = L * sgn - R;
    var qt = 1 / Math.hypot(Cc - P.b * Math.sin(p2) * (sgn - ss), m2);
    var flip = m2 < 0 ? -1 : 1, mu1 = flip * qt * m1, mu2 = flip * qt * m2;
    return [-mu2, mu1 * sgn, -mu2 * P.b * Math.sin(p2)];
  }

  var BORE_PIECES = ['max+', 'max-', 'min-', 'min+'];

  /* [{piece, seeds}] in BORE_PIECES order; each list starts at B_1 or Z_1. */
  function boresightCornerSeeds(sgn, nseed) {
    nseed = nseed || 60;
    var p1 = sgn * B.PARAMS.beta, out = [];
    [+1, -1].forEach(function (g) {
      out.push({ piece: g > 0 ? 'max+' : 'max-',
                 seeds: grid(EPS_VERTEX, Math.PI - EPS_VERTEX, nseed).map(function (x) {
                   var q = g * x, l = lamCornerMax(q, sgn);
                   return [B.Rhi(q), p1, q, l[0], l[1], l[2]];
                 }) });
    });
    var e = minCornerEnds(sgn), span = {};
    span[+1] = Math.abs(Math.max(e[0], e[1]));
    span[-1] = Math.abs(Math.min(e[0], e[1]));
    var longest = Math.max(span[1], span[-1]);
    [-1, +1].forEach(function (g) {
      var n = span[g] === longest ? nseed
                                  : Math.max(9, Math.round(nseed * span[g] / longest));
      out.push({ piece: g > 0 ? 'min+' : 'min-',
                 seeds: grid(EPS_VERTEX, span[g] - EPS_JOIN, n).map(function (x) {
                   var q = g * x, l = lamCornerMin(q, sgn);
                   return [B.Rlo(q), p1, q, l[0], l[1], l[2]];
                 }) });
    });
    return out;
  }

  return {
    FAMILIES: FAMILIES, traceBranches: traceBranches, joinFolds: joinFolds,
    mergeSeam: mergeSeam, resampleBranch: resampleBranch, snapToBup: snapToBup,
    refineFold: refineFold, closeFoldTips: closeFoldTips,
    branchesMaxrange: branchesMaxrange, branchesMinrange: branchesMinrange,
    branchesBoresight: branchesBoresight, seedState: seedState, seeds: seeds,
    E1: E1, lamCornerEdge: lamCornerEdge, cornerSeeds: cornerSeeds, mirror: mirror,
    d1Seed: d1Seed, c1Tau: c1Tau, integrateUniversal: integrateUniversal,
    universalLines: universalLines,
    minCornerEnds: minCornerEnds, lamCornerMax: lamCornerMax,
    lamCornerMin: lamCornerMin, BORE_PIECES: BORE_PIECES,
    boresightCornerSeeds: boresightCornerSeeds
  };
}));
