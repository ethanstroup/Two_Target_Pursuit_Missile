/**
 * los_coords.js -- world frame (x, y, heading) <-> the reduced state (R, phi1, phi2).
 *
 * Drives the "coordinates" and "phi2 sweep" tabs of barrier_explorer.html. The target
 * set itself (Eqs. 6-9) is not redefined here: Rlo, Rhi and beta all come from
 * ../barrier.js, so the tabs draw exactly the T1 the reconstruction uses.
 *
 * Conventions -- the same as heuristic_simulator/sim.js (physInit / recoverReduced):
 *   psi   = direction of the line of sight from player 1 to player 2
 *   phi1  = psi - th1            phi1 = 0: player 1 pointed straight at player 2
 *   phi2  = psi + pi - th2       phi2 = 0: player 2 pointed straight at player 1
 *   dth_i/dt = -sigma_i          (sigma = +1 is a right turn)
 * phi1 > 0 puts player 2 to player 1's left. Angles are wrapped to [-pi, pi). With unit
 * speeds these give dR/dt = -(cos phi1 + cos phi2) and
 * dphi_i/dt = (sin phi1 + sin phi2)/R + sigma_i, i.e. Barrier.stateDot. The mirror-image
 * choice (angles counterclockwise, dth/dt = +sigma) satisfies the same equations, so
 * test_los_coords.js pins this one against sim.js directly.
 *
 * Usable as a browser global (`LosCoords`, after barrier.js) or a CommonJS module.
 */
;(function (root, factory) {
  'use strict';
  var isNode = typeof module === 'object' && module.exports;
  var B = isNode ? require('../barrier.js') : root.Barrier;
  var L = factory(B);
  if (isNode) module.exports = L;
  else root.LosCoords = L;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (B) {
  'use strict';

  var PI = Math.PI;
  var wrap = B.wrap;

  // --- the reduction --------------------------------------------------------

  /** World state {p1, th1, p2, th2} -> {R, phi1, phi2, psi}. psi is the gauge the reduction drops. */
  function worldToLos(w) {
    var dx = w.p2[0] - w.p1[0], dy = w.p2[1] - w.p1[1];
    var psi = Math.atan2(dy, dx);
    return { R: Math.hypot(dx, dy), psi: psi, phi1: wrap(psi - w.th1), phi2: wrap(psi + PI - w.th2) };
  }

  /** Inverse of worldToLos, given back the gauge (p1, psi) that it discards. */
  function losToWorld(s, p1, psi) {
    return {
      p1: [p1[0], p1[1]],
      th1: wrap(psi - s.phi1),
      p2: [p1[0] + s.R * Math.cos(psi), p1[1] + s.R * Math.sin(psi)],
      th2: wrap(psi + PI - s.phi2)
    };
  }

  /** Player 1's position in player 2's body frame (player 2 at the origin, nose along +y). */
  function attackerInTargetFrame(R, phi2) {
    return [-R * Math.sin(phi2), R * Math.cos(phi2)];
  }

  /** The same position computed from world coordinates -- the check on the line above. */
  function worldToTargetFrame(p, p2, th2) {
    var a = PI / 2 - th2, c = Math.cos(a), s = Math.sin(a);
    var dx = p[0] - p2[0], dy = p[1] - p2[1];
    return [c * dx - s * dy, s * dx + c * dy];
  }

  /** World direction from player 2 toward player 1: the ray along which R-bar(phi2) is measured. */
  function losDirFromTarget(th2, phi2) {
    return th2 + phi2;
  }

  // --- the target set, from barrier.js ---------------------------------------

  function rHi(phi2) { return B.Rhi(wrap(phi2)); }
  function rLo(phi2) { return B.Rlo(wrap(phi2)); }

  /** The three T1 predicates separately -- same inequalities as the explorer's canFire. */
  function t1Checks(s) {
    return {
      bore: Math.abs(s.phi1) <= B.PARAMS.beta,
      min: s.R >= rLo(s.phi2),
      max: s.R < rHi(s.phi2)
    };
  }

  function inT1(s) {
    var c = t1Checks(s);
    return c.bore && c.min && c.max;
  }

  /** Layer 1's l(x), un-normalized: < 0 inside T1, > 0 outside. */
  function margin(s) {
    return Math.max(Math.abs(s.phi1) - B.PARAMS.beta, rLo(s.phi2) - s.R, s.R - rHi(s.phi2));
  }

  // --- world kinematics --------------------------------------------------------

  function toVec(w) { return [w.p1[0], w.p1[1], w.th1, w.p2[0], w.p2[1], w.th2]; }
  function fromVec(v) { return { p1: [v[0], v[1]], th1: wrap(v[2]), p2: [v[3], v[4]], th2: wrap(v[5]) }; }

  function worldDeriv(v, s1, s2) {
    return [Math.cos(v[2]), Math.sin(v[2]), -s1, Math.cos(v[5]), Math.sin(v[5]), -s2];
  }

  /** One RK4 step of unit-speed kinematics (dth_i/dt = -sigma_i), turn rates held over the step. */
  function rk4World(w, s1, s2, dt) {
    var v = toVec(w);
    function add(a, k, h) { return a.map(function (x, i) { return x + h * k[i]; }); }
    var k1 = worldDeriv(v, s1, s2);
    var k2 = worldDeriv(add(v, k1, dt / 2), s1, s2);
    var k3 = worldDeriv(add(v, k2, dt / 2), s1, s2);
    var k4 = worldDeriv(add(v, k3, dt), s1, s2);
    return fromVec(v.map(function (x, i) { return x + dt / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]); }));
  }

  /** Rotate the whole world about the origin by rot, then translate by (tx, ty). */
  function rigidMotion(w, rot, tx, ty) {
    var c = Math.cos(rot), s = Math.sin(rot);
    function f(p) { return [c * p[0] - s * p[1] + tx, s * p[0] + c * p[1] + ty]; }
    return { p1: f(w.p1), th1: wrap(w.th1 + rot), p2: f(w.p2), th2: wrap(w.th2 + rot) };
  }

  /** Largest component-wise difference between two reduced states, angles wrapped. */
  function stateDiff(a, b) {
    return Math.max(Math.abs(a.R - b.R), Math.abs(wrap(a.phi1 - b.phi1)), Math.abs(wrap(a.phi2 - b.phi2)));
  }

  return {
    worldToLos: worldToLos, losToWorld: losToWorld,
    attackerInTargetFrame: attackerInTargetFrame, worldToTargetFrame: worldToTargetFrame,
    losDirFromTarget: losDirFromTarget,
    rHi: rHi, rLo: rLo, t1Checks: t1Checks, inT1: inT1, margin: margin,
    rk4World: rk4World, rigidMotion: rigidMotion, stateDiff: stateDiff
  };
});
