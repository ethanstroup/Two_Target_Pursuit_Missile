/* barrier.js — Davidovitz & Shinar (1989) barrier reconstruction.
 *
 * Davidovitz, A., and Shinar, J., "Two-Target Game Model of an Air Combat with
 * Fire-and-Forget All-Aspect Missiles", JOTA 63(2), 133-165.
 *
 * This is the piece sim.js does not have. sim.js integrates the STATE under a
 * pure-pursuit heuristic; this module integrates the coupled STATE-COSTATE
 * system backward from the boundary of the usable part under the paper's own
 * barrier strategies,
 *
 *     sigma_1* = -sign(lambda_1),   sigma_2* = +sign(lambda_2)     Eqs. (21)-(22)
 *
 * with the costate seeded by transversality, Eq. (20). The result is the actual
 * semipermeable surface, i.e. ground truth, rather than a plausible-looking
 * trajectory.
 *
 * Port of layer0/barrier.py, which carries the derivations and the test suite.
 * ALL INTERNAL MATH IS IN RADIANS, as in sim.js.
 *
 * Two invariants are carried and are the integrator's own error estimate:
 *     FI = (l1+l2)^2/R^2 + lR^2 == 1     Eq. (23) with C = 1
 *     H* = min_s1 max_s2 lambda.f == 0   Eq. (15)
 * H* is the sharper of the two: it is not automatically preserved by the
 * costate ODEs, so a mishandled control switch shows up there first.
 *
 * Usable as a browser global (`Barrier`) or a CommonJS module.
 */
;(function (root, factory) {
  'use strict';
  var Barrier = factory(typeof require === 'function' ? require('./sim.js') : root.Sim);
  if (typeof module === 'object' && module.exports) module.exports = Barrier;
  else root.Barrier = Barrier;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Sim) {
  'use strict';

  var PI = Math.PI;

  // Parameters. NOTE on Rbar0 — Sec. 4 of the paper quotes 6.14, but Appendix A
  // Eq. (96) defines Rbar_0 = (R_tc)max/rho + pi and Table 2 pins
  // (R_tc)max/rho = 3.0 exactly (point A_1 = Rbar at phi_2 = pi is printed as
  // 3.0). 3 + pi = 6.14159 reproduces A_1 = 3.0, O_1 = 6.1416, beta = 4.649 and
  // delta = 4.649 to Table 2's printed precision; 6.14 reproduces none of them.
  // 6.14 is the rounded quotation, not the value used.
  var PARAMS = {
    beta: PI / 4,
    Rbar0: 3 + PI,
    a: 0.55,
    b: 0.30
  };

  var TOL_ZERO = 1e-9;

  function wrap(a) {
    if (a >= -PI && a < PI) return a;
    return ((a + PI) % (2 * PI) + 2 * PI) % (2 * PI) - PI;
  }

  // --- target set, Eqs. (8)-(9) --------------------------------------------

  function Rlo(p2, P) { P = P || PARAMS; return P.a + P.b * Math.cos(p2); }
  function Rhi(p2, P) { P = P || PARAMS; return P.Rbar0 - Math.abs(p2 + Math.sin(p2)); }
  function dRlo(p2, P) { P = P || PARAMS; return -P.b * Math.sin(p2); }
  function dRhi(p2) { return -(1 + Math.cos(p2)) * Math.sign(p2); }

  // --- dynamics and costates, Eqs. (1)-(3), (17)-(19) ----------------------

  function stateDot(R, p1, p2, s1, s2) {
    var L = Math.sin(p1) + Math.sin(p2);
    return [-(Math.cos(p1) + Math.cos(p2)), L / R + s1, L / R + s2];
  }

  function costateDot(R, p1, p2, lR, l1, l2) {
    var L = Math.sin(p1) + Math.sin(p2), S = l1 + l2;
    return [L * S / (R * R),
            -(lR * Math.sin(p1) + Math.cos(p1) * S / R),
            -(lR * Math.sin(p2) + Math.cos(p2) * S / R)];
  }

  function firstIntegral(R, lR, l1, l2) {
    var S = l1 + l2;
    return S * S / (R * R) + lR * lR;            // Eq. (23)
  }

  function hamiltonianStar(R, p1, p2, lR, l1, l2) {
    var L = Math.sin(p1) + Math.sin(p2), C = Math.cos(p1) + Math.cos(p2);
    return -lR * C + (l1 + l2) * L / R - Math.abs(l1) + Math.abs(l2);   // Eq. (15)
  }

  // Eqs. (21)-(22), with the retrograde first-order tie-break where a costate
  // component vanishes (it does at every BUP). Going backward,
  // lambda ~ -tau*lambdadot_f, so sign(lambda) = -sign(lambdadot). That
  // reproduces the paper's Eqs. (33) and (65) instead of assuming them.
  function controls(y) {
    var R = y[0], p1 = y[1], p2 = y[2], lR = y[3], l1 = y[4], l2 = y[5];
    var d = costateDot(R, p1, p2, lR, l1, l2);
    var s1 = Math.abs(l1) > TOL_ZERO ? -Math.sign(l1) : Math.sign(d[1]);
    var s2 = Math.abs(l2) > TOL_ZERO ? Math.sign(l2) : -Math.sign(d[2]);
    return [s1, s2];
  }

  function field(y, sigma) {
    var R = y[0], p1 = y[1], p2 = y[2], lR = y[3], l1 = y[4], l2 = y[5];
    var s = sigma || controls(y);
    var f = stateDot(R, p1, p2, s[0], s[1]);
    var g = costateDot(R, p1, p2, lR, l1, l2);
    return [f[0], f[1], f[2], g[0], g[1], g[2]];
  }

  // --- retrograde RK4 with the control FROZEN over a step ------------------
  //
  // The barrier control is piecewise constant. Letting each RK4 stage re-read
  // sign(lambda) smears every switch over a whole step, and the error lands on
  // H*, the semipermeability invariant the whole construction rests on.

  function axpy(y, k, h) {
    var o = new Array(6);
    for (var i = 0; i < 6; i++) o[i] = y[i] - h * k[i];   // minus: retrograde
    return o;
  }

  function rk4Retro(y, h, sigma) {
    var k1 = field(y, sigma);
    var k2 = field(axpy(y, k1, h / 2), sigma);
    var k3 = field(axpy(y, k2, h / 2), sigma);
    var k4 = field(axpy(y, k3, h), sigma);
    var o = new Array(6);
    for (var i = 0; i < 6; i++) {
      o[i] = y[i] - (h / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
    }
    o[1] = wrap(o[1]);
    o[2] = wrap(o[2]);
    return o;
  }

  /**
   * Integrate a barrier trajectory backward from a BUP point.
   * @param {number[]} y0  [R, phi1, phi2, lambdaR, lambda1, lambda2]
   * @param {object} opt   {tauMax, dt, Rmin, Rmax}
   * @returns {{path:Array, switches:Array, fiErr:number, hErr:number}}
   */
  function integrateRetrograde(y0, opt) {
    opt = opt || {};
    var tauMax = opt.tauMax != null ? opt.tauMax : 6.0;
    var dt = opt.dt != null ? opt.dt : 1e-3;
    var Rmin = opt.Rmin != null ? opt.Rmin : 0.02;
    var Rmax = opt.Rmax != null ? opt.Rmax : 12.0;

    var y = y0.slice(), tau = 0, path = [{ tau: 0, y: y.slice() }], switches = [];
    var fiErr = 0, hErr = 0, guard = 0, maxSteps = Math.floor(4 * tauMax / dt) + 1000;

    while (tau < tauMax && guard++ < maxSteps) {
      var h = Math.min(dt, tauMax - tau);
      if (h <= 0) break;
      var sigma = controls(y);
      var z = rk4Retro(y, h, sigma);
      if (!z.every(isFinite)) break;

      // locate the earliest costate sign change inside this step
      var ev = null;
      for (var k = 4; k <= 5; k++) {
        if (y[k] * z[k] < 0) {
          var lo = 0, hi = h;
          for (var it = 0; it < 60; it++) {
            var mid = 0.5 * (lo + hi);
            if (y[k] * rk4Retro(y, mid, sigma)[k] <= 0) hi = mid; else lo = mid;
          }
          var hs = 0.5 * (lo + hi);
          if (ev === null || hs < ev[0]) ev = [hs, k];
        }
      }

      if (ev !== null && ev[0] > 1e-13) {
        y = rk4Retro(y, ev[0], sigma);
        y[ev[1]] = 0;                       // snap onto the switching surface
        tau += ev[0];
        switches.push({ tau: tau, which: ev[1] - 3 });
      } else if (ev !== null) {
        y[ev[1]] = 0;
        y = rk4Retro(y, h, controls(y));
        tau += h;
      } else {
        y = z;
        tau += h;
      }

      path.push({ tau: tau, y: y.slice() });
      fiErr = Math.max(fiErr, Math.abs(firstIntegral(y[0], y[3], y[4], y[5]) - 1));
      hErr = Math.max(hErr, Math.abs(hamiltonianStar(y[0], y[1], y[2], y[3], y[4], y[5])));
      if (!(y[0] > Rmin && y[0] < Rmax)) break;
    }
    return { path: path, switches: switches, fiErr: fiErr, hErr: hErr };
  }

  // --- usable parts and their boundaries -----------------------------------

  function upMaxrange(p1, p2, P) {                       // Eq. (32) residual
    var L = Math.sin(p1) + Math.sin(p2);
    return Rhi(p2, P) * (1 - Math.cos(p1)) + L * (1 + Math.cos(p2)) * Math.sign(p2);
  }

  function upMinrange(p1, p2, P) {                       // Eq. (46) residual
    P = P || PARAMS;
    var L = Math.sin(p1) + Math.sin(p2);
    return Rlo(p2, P) * (Math.cos(p1) + Math.cos(p2) + P.b * Math.abs(Math.sin(p2)))
           - P.b * Math.sin(p2) * L;
  }

  function upBoresight(R, p1, p2) {                      // Eq. (62) residual
    return (Math.sin(p1) + Math.sin(p2)) * Math.sign(p1) - R;
  }

  function bisect(f, lo, hi) {
    if (f(lo) * f(hi) > 0) return null;
    for (var i = 0; i < 200; i++) {
      var mid = 0.5 * (lo + hi);
      if (f(lo) * f(mid) <= 0) hi = mid; else lo = mid;
    }
    return 0.5 * (lo + hi);
  }

  function rootsIn(f, lo, hi, n) {
    n = n || 800;
    var out = [], prev = f(lo), x, cur;
    for (var i = 1; i <= n; i++) {
      x = lo + (hi - lo) * i / n;
      cur = f(x);
      if (prev * cur < 0) {
        var r = bisect(f, lo + (hi - lo) * (i - 1) / n, x);
        if (r !== null) out.push(r);
      }
      prev = cur;
    }
    return out;
  }

  function bupMaxrange(p2, P) {
    P = P || PARAMS;
    return rootsIn(function (x) { return upMaxrange(x, p2, P); }, -P.beta, P.beta);
  }

  function bupMinrange(p2, P) {
    P = P || PARAMS;
    return rootsIn(function (x) { return upMinrange(x, p2, P); }, -P.beta, P.beta);
  }

  function bupBoresight(p2, sgn, P) {
    P = P || PARAMS;
    var p1 = sgn * P.beta;
    var R = (Math.sin(p1) + Math.sin(p2)) * Math.sign(p1);
    if (R <= 0) return null;
    if (!(R >= Rlo(p2, P) && R < Rhi(p2, P))) return null;
    return R;
  }

  // --- terminal costates from transversality, Eq. (20), normalized to C = 1 -

  function lamMaxrange(p2, P) {                          // Eqs. (34)-(36)
    var Rb = Rhi(p2, P);
    var p = 1 / Math.sqrt(Rb * Rb + Math.pow(1 + Math.cos(p2), 2));
    return [p * Rb, 0, p * Rb * (1 + Math.cos(p2)) * Math.sign(Math.sin(p2))];
  }

  function lamMinrange(p2, P) {                          // Eqs. (47)-(50)
    P = P || PARAMS;
    var Rl = Rlo(p2, P);
    var pu = 1 / Math.sqrt(P.a * P.a + P.b * P.b + 2 * P.a * P.b * Math.cos(p2));
    return [-pu * Rl, 0, -pu * Rl * P.b * Math.sin(p2)];
  }

  // Transversality on phi_1 = +/- beta. The outer normal is (0, sign phi_1, 0),
  // so lambda = mu (0, sign phi_1, 0) and the first integral forces mu = R:
  //     lambda_1f = R sign(phi_1) = sin phi_1 + sin phi_2  on the BUP.
  //
  // NOTE — Eq. (63) as PRINTED gives (sin phi_1 + sin phi_2) sign(phi_1), one
  // factor of sign(phi_1) more. The paper's own Eq. (64),
  // lambdadot_2f = -(cos phi_2) sign(phi_1), follows from the expression below
  // and NOT from Eq. (63) as printed. The difference is invisible at
  // phi_1 = +beta and flips the whole strategy pair at phi_1 = -beta.
  function lamBoresight(R, p1) {
    return [0, R * Math.sign(p1), 0];
  }

  // --- convenience: seed a barrier trajectory from each BUP family ---------

  function seedMaxrange(p2, P) {
    var out = [];
    bupMaxrange(p2, P).forEach(function (p1) {
      var l = lamMaxrange(p2, P);
      out.push([Rhi(p2, P), p1, p2, l[0], l[1], l[2]]);
    });
    return out;
  }

  function seedMinrange(p2, P) {
    var out = [];
    bupMinrange(p2, P).forEach(function (p1) {
      var l = lamMinrange(p2, P);
      out.push([Rlo(p2, P), p1, p2, l[0], l[1], l[2]]);
    });
    return out;
  }

  function seedBoresight(p2, sgn, P) {
    P = P || PARAMS;
    var R = bupBoresight(p2, sgn, P);
    if (R === null) return [];
    var p1 = sgn * P.beta, l = lamBoresight(R, p1);
    return [[R, p1, p2, l[0], l[1], l[2]]];
  }

  return {
    PARAMS: PARAMS,
    wrap: wrap,
    Rlo: Rlo, Rhi: Rhi, dRlo: dRlo, dRhi: dRhi,
    stateDot: stateDot, costateDot: costateDot,
    firstIntegral: firstIntegral, hamiltonianStar: hamiltonianStar,
    controls: controls, field: field,
    rk4Retro: rk4Retro, integrateRetrograde: integrateRetrograde,
    upMaxrange: upMaxrange, upMinrange: upMinrange, upBoresight: upBoresight,
    bupMaxrange: bupMaxrange, bupMinrange: bupMinrange, bupBoresight: bupBoresight,
    lamMaxrange: lamMaxrange, lamMinrange: lamMinrange, lamBoresight: lamBoresight,
    seedMaxrange: seedMaxrange, seedMinrange: seedMinrange, seedBoresight: seedBoresight
  };
});
