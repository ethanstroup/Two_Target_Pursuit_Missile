/* sim.js — two-target game: dynamics, wrapping, target sets, RK4, control law.
 *
 * Davidovitz & Shinar (1989), "Two-Target Game Model of an Air Combat with
 * Fire-and-Forget All-Aspect Missiles", JOTA 63(2), 133-165.
 *
 * ALL INTERNAL MATH IS IN RADIANS (spec §1). Degrees exist only at the UI boundary.
 * Usable as a browser global (`Sim`) or a CommonJS module.
 */
;(function (root, factory) {
  'use strict';
  var Sim = factory();
  if (typeof module === 'object' && module.exports) module.exports = Sim;
  else root.Sim = Sim;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var PI = Math.PI;

  // Worked-example parameters, Section 4 of the paper (spec §2).
  // Do NOT "correct" a and b against Appendix A — see the v2 note in the spec.
  var PARAMS = {
    beta: PI / 4,   // 45deg boresight limit, Eq. (6)
    // Rbar0 = 3 + pi. Sec. 4 of the paper QUOTES 6.14, but Appendix A Eq. (96)
    // defines Rbar_0 = (R_tc)max/rho + pi, and Table 2 pins (R_tc)max/rho = 3.0
    // exactly: its point A_1 is Rbar at phi_2 = pi and is printed as 3.0. With
    // 3 + pi = 6.141593 the table's A_1 = 3.0, O_1 = 6.1416, beta = 4.649 and
    // delta = 4.649 all come out to their printed precision; with 6.14 none of
    // them do (2.99841, 6.14000, 4.64750). 6.14 is the rounded quotation, not
    // the value the figures were computed with. See layer0/LAYER0_CLOSEOUT.md.
    Rbar0: 3 + Math.PI,   // no-escape range at phi_j = 0, Eq. (9)
    a: 0.55,        // Eq. (8)
    b: 0.30,        // Eq. (8)
    dt: 0.01,       // fixed RK4 step, normalized time
    tMax: 30,       // draw horizon
    Rmin: 0.01      // numerical guard on the 1/R term
  };

  // --- angles ---------------------------------------------------------------

  // Wrap into [-pi, pi). Required after every step, before any target-set or
  // termination check (spec §1): Eq. (9) uses |phi + sin phi| unwrapped, so an
  // unwrapped phi drives Rbar negative and manufactures spurious draws.
  //
  // The in-range short-circuit matters. The spec's bare one-liner is not exact
  // on values already inside [-pi, pi): the +pi / -pi round trip perturbs by an
  // ulp, so wrap(pi/4) comes back just ABOVE beta and states exactly on the
  // boresight boundary (|phi| = 45deg, which the §9 grid hits) fall out of the
  // target set. That alone moves the R0=1.5 terminal-at-t=0 fraction from the
  // spec's 45.3% to 41.2%.
  function wrap(a) {
    if (a >= -PI && a < PI) return a;
    return ((a + PI) % (2 * PI) + 2 * PI) % (2 * PI) - PI;
  }

  var DEG = 180 / PI;
  function toDeg(r) { return r * DEG; }
  function toRad(d) { return d / DEG; }

  // --- target sets (Eqs. 6-9) ----------------------------------------------
  //
  // Index asymmetry (spec §2): the boresight bound is on player i's OWN angle,
  // both range bounds depend on the OPPONENT's aspect angle phi_j.

  function RminOf(phiOpp, p) {                 // Eq. (8)
    p = p || PARAMS;
    return p.a + p.b * Math.cos(phiOpp);
  }

  function RmaxOf(phiOpp, p) {                 // Eq. (9)
    p = p || PARAMS;
    return p.Rbar0 - Math.abs(phiOpp + Math.sin(phiOpp));
  }

  // Is player i (own angle phiOwn, opponent angle phiOpp) in his target set?
  // Eq. (7): non-strict lower bound, strict upper bound.
  function inTarget(phiOwn, phiOpp, R, p) {
    p = p || PARAMS;
    if (Math.abs(phiOwn) > p.beta) return false;
    return R >= RminOf(phiOpp, p) && R < RmaxOf(phiOpp, p);
  }

  function inT1(s, p) { return inTarget(s.phi1, s.phi2, s.R, p); }
  function inT2(s, p) { return inTarget(s.phi2, s.phi1, s.R, p); }

  // The phi_j values for which the range bounds admit a kill at this R.
  // Both bounds are even and monotone in |phi_j| on [0, pi], so the admissible
  // opponent-angle set is the symmetric band lo <= |phi_j| < hi. Returned as
  // explicit intervals so the renderer can shade T1/T2 analytically.
  function opponentBand(R, p) {
    p = p || PARAMS;
    // R >= a + b cos(phi)  <=>  cos(phi) <= (R - a)/b  <=>  |phi| >= acos(...)
    var c = (R - p.a) / p.b, lo;
    if (c >= 1) lo = 0;
    else if (c < -1) return [];               // R below R_min for every phi
    else lo = Math.acos(c);
    // R < Rbar0 - |phi + sin phi|  <=>  |phi + sin phi| < Rbar0 - R
    var g = p.Rbar0 - R, hi;
    if (g <= 0) return [];                     // beyond no-escape range everywhere
    if (g >= PI) hi = PI;                      // g(pi) = pi, so all phi qualify
    else hi = solveG(g);
    if (!(lo < hi)) return [];
    return lo === 0 ? [[-hi, hi]] : [[-hi, -lo], [lo, hi]];
  }

  // Invert g(x) = x + sin(x) on [0, pi] (monotone, g' = 1 + cos x >= 0).
  function solveG(y) {
    var xa = 0, xb = PI, xm;
    for (var i = 0; i < 60; i++) {
      xm = 0.5 * (xa + xb);
      if (xm + Math.sin(xm) < y) xa = xm; else xb = xm;
    }
    return 0.5 * (xa + xb);
  }

  // --- control law (spec §4) ------------------------------------------------
  // Pure-pursuit heuristic, NOT the paper's optimal law. sigma_i = 0 at phi_i = 0
  // avoids sign-function chatter.
  function control(s) {
    return { s1: -Math.sign(s.phi1), s2: -Math.sign(s.phi2) };
  }

  // --- dynamics (Eqs. 1-3) --------------------------------------------------
  function deriv(s) {
    var los = (Math.sin(s.phi1) + Math.sin(s.phi2)) / s.R;   // Eq. (5)
    var u = control(s);
    return {
      R: -(Math.cos(s.phi1) + Math.cos(s.phi2)),
      phi1: los + u.s1,
      phi2: los + u.s2
    };
  }

  function axpy(s, k, h) {
    return { R: s.R + h * k.R, phi1: s.phi1 + h * k.phi1, phi2: s.phi2 + h * k.phi2 };
  }

  function rk4Step(s, dt) {
    var k1 = deriv(s);
    var k2 = deriv(axpy(s, k1, dt / 2));
    var k3 = deriv(axpy(s, k2, dt / 2));
    var k4 = deriv(axpy(s, k3, dt));
    var out = {
      R:    s.R    + (dt / 6) * (k1.R    + 2 * k2.R    + 2 * k3.R    + k4.R),
      phi1: s.phi1 + (dt / 6) * (k1.phi1 + 2 * k2.phi1 + 2 * k3.phi1 + k4.phi1),
      phi2: s.phi2 + (dt / 6) * (k1.phi2 + 2 * k2.phi2 + 2 * k3.phi2 + k4.phi2)
    };
    // Wrap immediately, before anything looks at the state (spec §1).
    out.phi1 = wrap(out.phi1);
    out.phi2 = wrap(out.phi2);
    return out;
  }

  // --- physical reconstruction (presentation only) --------------------------
  //
  // The reduced state remains the single source of truth for every outcome.
  // This is a second, independent integration of the same engagement in ground
  // coordinates, used to draw the plan view and to cross-check the reduced
  // integration (|p2 - p1| must track R).
  //
  // With psi the line-of-sight direction from aircraft 1 to aircraft 2, and
  // th_i the absolute headings:
  //
  //   phi1 = psi - th1                    phi2 = psi + pi - th2
  //   xdot_i = cos(th_i)    ydot_i = sin(th_i)    thdot_i = -sigma_i
  //
  // Those conventions are what make Eqs. (1) and (5) come out right:
  //   Rdot = (v2 - v1).u_hat = -cos(phi1) - cos(phi2)
  //   psidot = (v2 - v1).n_hat / R = (sin(phi1) + sin(phi2)) / R
  // and thdot_i = -sigma_i then follows from phidot_i = psidot + sigma_i.
  // Sanity: phi1 > 0 puts the opponent to the left, so sigma1 = -1 and
  // thdot1 = +1 -- a left turn toward the opponent, i.e. pure pursuit.

  // Anchored with psi = 0 and the pair's midpoint at the origin, which fixes
  // the translation and rotation freedom the reduced state discards.
  function physInit(R0, phi1, phi2) {
    return {
      x1: -R0 / 2, y1: 0, th1: -phi1,
      x2:  R0 / 2, y2: 0, th2: PI - phi2
    };
  }

  function physDeriv(ph, u) {
    return {
      x1: Math.cos(ph.th1), y1: Math.sin(ph.th1), th1: -u.s1,
      x2: Math.cos(ph.th2), y2: Math.sin(ph.th2), th2: -u.s2
    };
  }

  function physAxpy(ph, k, h) {
    return {
      x1: ph.x1 + h * k.x1, y1: ph.y1 + h * k.y1, th1: ph.th1 + h * k.th1,
      x2: ph.x2 + h * k.x2, y2: ph.y2 + h * k.y2, th2: ph.th2 + h * k.th2
    };
  }

  // Physical RK4 step. It recomputes the reduced RK4 stages purely to recover
  // the same stage-wise sigma the reduced integrator saw: the control is
  // discontinuous at phi = 0, so reusing one frozen sigma across the step would
  // let the two integrations disagree on any step where phi crosses zero.
  // rk4Step itself is left untouched, so the reduced trajectory stays
  // bit-identical to what the §9 acceptance grid validates.
  function rk4StepPhys(s, ph, dt) {
    var d1 = deriv(s),              q1 = physDeriv(ph, control(s));
    var s2 = axpy(s, d1, dt / 2),   h2 = physAxpy(ph, q1, dt / 2);
    var d2 = deriv(s2),             q2 = physDeriv(h2, control(s2));
    var s3 = axpy(s, d2, dt / 2),   h3 = physAxpy(ph, q2, dt / 2);
    var d3 = deriv(s3),             q3 = physDeriv(h3, control(s3));
    var s4 = axpy(s, d3, dt),       h4 = physAxpy(ph, q3, dt);
    var q4 = physDeriv(h4, control(s4));
    var w = dt / 6;
    return {
      x1:  ph.x1  + w * (q1.x1  + 2 * q2.x1  + 2 * q3.x1  + q4.x1),
      y1:  ph.y1  + w * (q1.y1  + 2 * q2.y1  + 2 * q3.y1  + q4.y1),
      th1: ph.th1 + w * (q1.th1 + 2 * q2.th1 + 2 * q3.th1 + q4.th1),
      x2:  ph.x2  + w * (q1.x2  + 2 * q2.x2  + 2 * q3.x2  + q4.x2),
      y2:  ph.y2  + w * (q1.y2  + 2 * q2.y2  + 2 * q3.y2  + q4.y2),
      th2: ph.th2 + w * (q1.th2 + 2 * q2.th2 + 2 * q3.th2 + q4.th2)
    };
  }

  // Invert the reconstruction: ground coordinates -> reduced state. Headings
  // are deliberately left unwrapped during integration (cos/sin do not care),
  // so the recovered angles are wrapped here.
  function recoverReduced(ph) {
    var dx = ph.x2 - ph.x1, dy = ph.y2 - ph.y1;
    var psi = Math.atan2(dy, dx);
    return {
      R: Math.sqrt(dx * dx + dy * dy),
      phi1: wrap(psi - ph.th1),
      phi2: wrap(psi + PI - ph.th2)
    };
  }

  // --- termination (Eqs. 10-11, spec §2) ------------------------------------
  var OUTCOMES = {
    TERMINAL0: 'terminal0',   // already in T1 u T2 at t=0 -> inadmissible IC (spec §3)
    P1: 'p1',
    P2: 'p2',
    MUTUAL: 'mutual',
    DRAW: 'draw',
    NUMERICAL: 'numerical'    // R -> 0; NOT a game outcome
  };

  var LABELS = {
    terminal0: 'Initial state already terminal — not an admissible initial condition',
    p1: 'Player 1 wins',
    p2: 'Player 2 wins',
    mutual: 'Mutual kill',
    draw: 'Draw (no termination)',
    numerical: 'Numerical edge case (R→0)'
  };

  // Intersection first, so simultaneous entry is a mutual kill rather than
  // being assigned to a player by check order.
  function classify(s, p) {
    var t1 = inT1(s, p), t2 = inT2(s, p);
    if (t1 && t2) return OUTCOMES.MUTUAL;
    if (t1) return OUTCOMES.P1;
    if (t2) return OUTCOMES.P2;
    // NaN-safe: !(R >= Rmin) is true for NaN as well as for R below the guard.
    if (!(s.R >= (p || PARAMS).Rmin)) return OUTCOMES.NUMERICAL;
    return null;
  }

  // --- runs -----------------------------------------------------------------

  // Stepwise run object, for the animation loop. Carries the ground-coordinate
  // reconstruction by default (opts.physics === false opts out); simulate()
  // deliberately does not, so the acceptance grid never pays for it.
  function createRun(phi1_0, phi2_0, R0, opts) {
    opts = opts || {};
    var p = opts.params || PARAMS;
    var dt = opts.dt || p.dt;
    var wantPhys = opts.physics !== false;
    var run = {
      params: p,
      dt: dt,
      t: 0,
      state: { R: R0, phi1: wrap(phi1_0), phi2: wrap(phi2_0) },
      done: false,
      outcome: null,
      path: []
    };
    // t = 0 admissibility check (spec §3).
    var pre = classify(run.state, p);
    if (pre === OUTCOMES.MUTUAL || pre === OUTCOMES.P1 || pre === OUTCOMES.P2) {
      run.done = true;
      run.outcome = OUTCOMES.TERMINAL0;
      run.terminal0Kind = pre;
    }
    // opts.phys0 lets the caller supply the absolute ground frame (the plan
    // view's arrangement), so a run flown from a dragged setup animates in the
    // pose the user built rather than snapping to the canonical one. It is
    // presentation-only: the reduced state, and therefore every outcome, is
    // unaffected by which frame the pair is drawn in.
    run.phys = wantPhys
      ? (opts.phys0 ? {
          x1: opts.phys0.x1, y1: opts.phys0.y1, th1: opts.phys0.th1,
          x2: opts.phys0.x2, y2: opts.phys0.y2, th2: opts.phys0.th2
        } : physInit(R0, run.state.phi1, run.state.phi2))
      : null;

    function record(t, s, ph) {
      var rec = { t: t, R: s.R, phi1: s.phi1, phi2: s.phi2 };
      if (ph) {
        rec.x1 = ph.x1; rec.y1 = ph.y1; rec.th1 = ph.th1;
        rec.x2 = ph.x2; rec.y2 = ph.y2; rec.th2 = ph.th2;
      }
      return rec;
    }
    run.path.push(record(0, run.state, run.phys));

    run.step = function () {
      if (run.done) return run.outcome;
      // Physical step first: it needs the pre-step reduced state to recover the
      // stage-wise controls.
      if (run.phys) run.phys = rk4StepPhys(run.state, run.phys, dt);
      run.state = rk4Step(run.state, dt);
      run.t += dt;
      run.path.push(record(run.t, run.state, run.phys));
      var o = classify(run.state, p);
      if (o) { run.done = true; run.outcome = o; return o; }
      if (run.t >= p.tMax - 1e-9) { run.done = true; run.outcome = OUTCOMES.DRAW; }
      return run.outcome;
    };
    return run;
  }

  // Batch run. record:false keeps it allocation-light for the acceptance grid.
  function simulate(phi1_0, phi2_0, R0, opts) {
    opts = opts || {};
    var p = opts.params || PARAMS;
    var dt = opts.dt || p.dt;
    var record = !!opts.record;

    var s = { R: R0, phi1: wrap(phi1_0), phi2: wrap(phi2_0) };
    var path = record ? [{ t: 0, R: s.R, phi1: s.phi1, phi2: s.phi2 }] : null;

    var pre = classify(s, p);
    if (pre === OUTCOMES.MUTUAL || pre === OUTCOMES.P1 || pre === OUTCOMES.P2) {
      return { outcome: OUTCOMES.TERMINAL0, terminal0Kind: pre, t: 0, state: s, path: path };
    }

    var nSteps = Math.round(p.tMax / dt), t = 0;
    for (var i = 0; i < nSteps; i++) {
      s = rk4Step(s, dt);
      t += dt;
      if (record) path.push({ t: t, R: s.R, phi1: s.phi1, phi2: s.phi2 });
      var o = classify(s, p);
      if (o) return { outcome: o, t: t, state: s, path: path };
    }
    return { outcome: OUTCOMES.DRAW, t: t, state: s, path: path };
  }

  return {
    PARAMS: PARAMS,
    OUTCOMES: OUTCOMES,
    LABELS: LABELS,
    wrap: wrap,
    toDeg: toDeg,
    toRad: toRad,
    RminOf: RminOf,
    RmaxOf: RmaxOf,
    inTarget: inTarget,
    inT1: inT1,
    inT2: inT2,
    opponentBand: opponentBand,
    control: control,
    deriv: deriv,
    rk4Step: rk4Step,
    physInit: physInit,
    physDeriv: physDeriv,
    rk4StepPhys: rk4StepPhys,
    recoverReduced: recoverReduced,
    classify: classify,
    createRun: createRun,
    simulate: simulate
  };
});
