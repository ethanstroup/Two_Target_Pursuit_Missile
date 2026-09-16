/* test_acceptance.js — reproduces the spec §9 acceptance-check table, the §2
 * Table-2 sanity checks, and the two structural invariants of §9.
 *
 * Runs in either environment against the same sim.js:
 *   node test_acceptance.js
 *   <open or headless-dump test_acceptance.html>
 */
(function () {
  'use strict';

  var isNode = (typeof module === 'object' && module.exports) || typeof process !== 'undefined' && process.versions && process.versions.node;
  var Sim = isNode ? require('./sim.js') : (typeof globalThis !== 'undefined' ? globalThis : window).Sim;
  var O = Sim.OUTCOMES;

  var lines = [];
  var log = function (s) { lines.push(s === undefined ? '' : String(s)); };

  var failures = 0;
  var pass = function (ok, msg) { if (!ok) failures++; log('  ' + (ok ? 'PASS' : 'FAIL') + '  ' + msg); };
  var pct = function (x) { return (100 * x).toFixed(1) + '%'; };
  var near = function (a, b, tol) { return Math.abs(a - b) <= tol; };

  var t0 = Date.now();

  // -------------------------------------------------------------------------
  // §2 target-set parameters vs. the paper's Table 2
  // -------------------------------------------------------------------------
  log('');
  log('§2 target-set parameters vs. paper Table 2');
  pass(near(Sim.RminOf(0), 0.85, 5e-3),        'R_min(0deg)    = ' + Sim.RminOf(0).toFixed(4) + '   expected 0.85');
  pass(near(Sim.RminOf(Math.PI), 0.25, 5e-3),  'R_min(180deg)  = ' + Sim.RminOf(Math.PI).toFixed(4) + '   expected 0.25');
  pass(near(Sim.RminOf(-Math.PI), 0.25, 5e-3), 'R_min(-180deg) = ' + Sim.RminOf(-Math.PI).toFixed(4) + '   expected 0.25');
  // Table 2 prints O_1 = Rbar(0) as 6.1416 and A_1 = Rbar(pi) as 3.0 exactly.
  // Both are met only by Rbar_0 = 3 + pi; the tolerances below are tight enough
  // to fail if someone puts 6.14 back. See layer0/LAYER0_CLOSEOUT.md.
  pass(near(Sim.RmaxOf(0), 6.1416, 5e-5),      'R_max(0deg)    = ' + Sim.RmaxOf(0).toFixed(4) + '   Table 2 O_1 = 6.1416');
  pass(near(Sim.RmaxOf(Math.PI), 3.00, 5e-4),  'R_max(180deg)  = ' + Sim.RmaxOf(Math.PI).toFixed(4) + '   Table 2 A_1 = 3.0');
  pass(near(Sim.RmaxOf(-Math.PI), 3.00, 5e-4), 'R_max(-180deg) = ' + Sim.RmaxOf(-Math.PI).toFixed(4) + '   Table 2 A_1 = 3.0');
  pass(near(Sim.RmaxOf(Math.PI / 4), 4.649, 5e-4), 'R_max(45deg)   = ' + Sim.RmaxOf(Math.PI / 4).toFixed(4) + '   Table 2 beta = 4.649');

  // -------------------------------------------------------------------------
  // §1 wrapping
  // -------------------------------------------------------------------------
  log('');
  log('§1 angle wrapping into [-pi, pi]');
  pass(near(Sim.wrap(3 * Math.PI), -Math.PI, 1e-12), 'wrap(3pi)    = ' + Sim.wrap(3 * Math.PI).toFixed(6) + '   expected -pi');
  pass(near(Sim.wrap(-3.5 * Math.PI), 0.5 * Math.PI, 1e-12), 'wrap(-3.5pi) = ' + Sim.wrap(-3.5 * Math.PI).toFixed(6) + '   expected +pi/2');
  pass(Math.abs(Sim.wrap(1234.5)) <= Math.PI, 'wrap(1234.5) stays in [-pi, pi]');
  // Must be exact on in-range values, or states on the boresight boundary
  // (|phi| = beta, which the §9 grid lands on) drop out of the target set.
  pass(Sim.wrap(Sim.PARAMS.beta) === Sim.PARAMS.beta && Sim.wrap(-Sim.PARAMS.beta) === -Sim.PARAMS.beta,
    'wrap is exactly the identity on in-range values (wrap(beta) === beta)');
  // Eq. (9) is only meaningful on wrapped angles: unwrapped, R_max goes negative.
  pass(Sim.RmaxOf(3 * Math.PI) < 0 && Sim.RmaxOf(Sim.wrap(3 * Math.PI)) > 0,
    'unwrapped phi drives R_max negative (' + Sim.RmaxOf(3 * Math.PI).toFixed(2) +
    '), wrapped it does not (' + Sim.RmaxOf(Sim.wrap(3 * Math.PI)).toFixed(2) + ')');

  // -------------------------------------------------------------------------
  // §2 index asymmetry: boresight on own phi, both range bounds on opponent phi
  // -------------------------------------------------------------------------
  log('');
  log('§2 index asymmetry (boresight uses own phi_i, range bounds use opponent phi_j)');
  pass(Sim.inTarget(0, 0, 5.0) === true, 'own=0deg, opp=0deg, R=5 -> in target set');
  pass(Sim.inTarget(Sim.toRad(80), 0, 5.0) === false, 'own=80deg > beta -> false');
  pass(Sim.inTarget(0, Sim.toRad(80), 5.0) === false, 'opp=80deg puts R=5 beyond R_max -> false');
  pass(Sim.inTarget(Sim.toRad(80), Sim.toRad(80), 5.0) === false, 'both 80deg -> false');
  pass(Sim.inTarget(0, 0, 0.5) === false, 'R=0.5 below R_min(0deg)=0.85 -> false');
  pass(Sim.inTarget(0, 0, Sim.RminOf(0)) === true, 'Eq. (7) lower bound non-strict: R = R_min -> true');
  pass(Sim.inTarget(0, 0, Sim.RmaxOf(0)) === false, 'Eq. (7) upper bound strict: R = R_max -> false');
  pass(Sim.inTarget(Sim.PARAMS.beta, 0, 5.0) === true && Sim.inTarget(-Sim.PARAMS.beta, 0, 5.0) === true,
    'Eq. (6) boresight bound non-strict: own phi = +/-beta -> true');

  // -------------------------------------------------------------------------
  // §9 acceptance grid: 73x73 over [-180deg, 180deg] inclusive
  // -------------------------------------------------------------------------
  var N = 73;
  var gridDeg = [];
  for (var gi = 0; gi < N; gi++) gridDeg.push(-180 + (360 * gi) / (N - 1));

  function runGrid(R0) {
    var c = { terminal0: 0, p1: 0, p2: 0, mutual: 0, draw: 0, numerical: 0 };
    var advDecisive = 0, advAgree = 0;
    for (var i = 0; i < N; i++) {
      for (var j = 0; j < N; j++) {
        var d1 = gridDeg[i], d2 = gridDeg[j];
        var r = Sim.simulate(Sim.toRad(d1), Sim.toRad(d2), R0);
        c[r.outcome]++;
        if ((r.outcome === O.P1 || r.outcome === O.P2) && Math.abs(d1) !== Math.abs(d2)) {
          advDecisive++;
          var smallerIsP1 = Math.abs(d1) < Math.abs(d2);
          if (smallerIsP1 === (r.outcome === O.P1)) advAgree++;
        }
      }
    }
    return {
      c: c, total: N * N, advDecisive: advDecisive, advAgree: advAgree,
      advFrac: advDecisive ? advAgree / advDecisive : NaN
    };
  }

  // The spec §9 table, RE-BASELINED for Rbar_0 = 3 + pi (see sim.js and
  // layer0/LAYER0_CLOSEOUT.md). The spec's original numbers were measured with
  // Rbar_0 = 6.14; the two long-range rows moved when the constant was
  // corrected. Superseded values, for the record:
  //     R0 = 8 : p1 = p2 = 0.405, mutual = 0.189
  //     R0 = 12: p1 = p2 = 0.065, mutual = 0.869
  // The short-range rows did not move at all, which is the point: run
  // layer0/sens.js and a 0.026% change in Rbar_0 shifts the R0 = 8 mutual-kill
  // fraction by 1.3 points and the R0 = 12 one by 1.7, NON-MONOTONICALLY, while
  // R0 = 5 moves by 0.15. The long-range fractions under the pure-pursuit
  // heuristic are not a stable quantity to three digits, so they are a weak
  // regression baseline — independent support for ProblemStatement §4's
  // argument that Layer 1 is needed before any long-range claim is trusted.
  var expected = [
    { R0: 1.5,  terminal0: 0.453, p1: 0.212, p2: 0.212, mutual: 0.014, draw: 0.108 },
    { R0: 5.0,  terminal0: 0.061, p1: 0.450, p2: 0.450, mutual: 0.038, draw: 0.000 },
    { R0: 8.0,  terminal0: 0.000, p1: 0.412, p2: 0.412, mutual: 0.177, draw: 0.000 },
    { R0: 12.0, terminal0: 0.000, p1: 0.074, p2: 0.074, mutual: 0.853, draw: 0.000 }
  ];

  var results = {};
  for (var e = 0; e < expected.length; e++) results[expected[e].R0] = runGrid(expected[e].R0);

  function padEnd(s, n) { s = String(s); while (s.length < n) s += ' '; return s; }
  var W = [7, 17, 17, 17, 17, 17, 6];
  var HDR = ['R0', 'terminal t=0', 'P1 wins', 'P2 wins', 'mutual kill', 'draw', 'R->0'];

  log('');
  log('§9 acceptance table   (73x73 grid, dt = 0.01, horizon t = 30)');
  log('cells are:  observed (spec §9 expected)');
  log('');
  var hdrLine = '', sepLine = '';
  for (var h = 0; h < HDR.length; h++) { hdrLine += padEnd(HDR[h], W[h]); sepLine += padEnd(new Array(W[h]).join('-'), W[h]); }
  log(hdrLine);
  log(sepLine);
  for (var k = 0; k < expected.length; k++) {
    var ex = expected[k], rr = results[ex.R0], row = padEnd(ex.R0.toFixed(1), W[0]);
    var keys = ['terminal0', 'p1', 'p2', 'mutual', 'draw'];
    for (var q = 0; q < keys.length; q++) {
      row += padEnd(pct(rr.c[keys[q]] / rr.total) + ' (' + pct(ex[keys[q]]) + ')', W[q + 1]);
    }
    log(row + padEnd(rr.c.numerical, W[6]));
  }

  var TOL = 0.015; // 1.5 percentage points
  log('');
  log('§9 fraction agreement (tolerance +/- 1.5 percentage points)');
  for (var m = 0; m < expected.length; m++) {
    var exm = expected[m], rm = results[exm.R0];
    var kk = ['terminal0', 'p1', 'p2', 'mutual', 'draw'];
    for (var z = 0; z < kk.length; z++) {
      var obs = rm.c[kk[z]] / rm.total;
      pass(Math.abs(obs - exm[kk[z]]) <= TOL,
        'R0=' + exm.R0 + ' ' + padEnd(kk[z] + ':', 11) + ' obs ' + padEnd(pct(obs), 7) + ' exp ' + pct(exm[kk[z]]));
    }
  }

  // §9 invariant 1 — exact symmetry
  log('');
  log('§9 invariant 1 — exact P1/P2 symmetry (any inequality means a phi_i/phi_j indexing bug)');
  for (var s1 = 0; s1 < expected.length; s1++) {
    var rs = results[expected[s1].R0];
    pass(rs.c.p1 === rs.c.p2, 'R0=' + expected[s1].R0 + ': P1 wins ' + rs.c.p1 + ' === P2 wins ' + rs.c.p2);
  }

  // §9 invariant 2 — angular-advantage agreement
  log('');
  log('§9 invariant 2 — angular-advantage agreement (winner is the player with smaller |phi|)');
  var advExpect = [
    { R0: 1.5, lo: 0.97, hi: 1.001, note: 'spec: ~100% at R0 <= 2' },
    { R0: 2.0, lo: 0.97, hi: 1.001, note: 'spec: ~100% at R0 <= 2' },
    { R0: 5.0, lo: 0.82, hi: 0.92,  note: 'spec: ~87% at R0 = 5' },
    { R0: 8.0, lo: 0.00, hi: 0.06,  note: 'spec: ~1% at R0 = 8' }
  ];
  for (var a = 0; a < advExpect.length; a++) {
    var ae = advExpect[a];
    if (!results[ae.R0]) results[ae.R0] = runGrid(ae.R0);
    var ra = results[ae.R0];
    pass(ra.advFrac >= ae.lo && ra.advFrac <= ae.hi,
      'R0=' + padEnd(ae.R0, 5) + padEnd(pct(ra.advFrac), 8) + 'of ' + padEnd(ra.advDecisive, 6) + 'decisive cases   (' + ae.note + ')');
  }

  // -------------------------------------------------------------------------
  // Plan-view cross-check. The ground-coordinate integration is independent of
  // the reduced one -- aircraft 2's position is integrated, not derived from R
  // and psi -- so agreement is a real check on both. A sign error in
  // thdot_i = -sigma_i fails this immediately.
  // -------------------------------------------------------------------------
  log('');
  log('plan view - ground-coordinate reconstruction vs. reduced state');
  var reconCases = [
    { d1: -120, d2: 60,   R0: 1.75, note: 'default demo case' },
    { d1: 0,    d2: 0,    R0: 8.0,  note: 'head-on, sigma = 0 throughout' },
    { d1: 175,  d2: -170, R0: 3.0,  note: 'wraps past +/-pi' },
    { d1: 30,   d2: -90,  R0: 8.0,  note: 'long range, phi crosses zero' },
    { d1: 150,  d2: 150,  R0: 12.0, note: 'both tail-on, long range' },
    { d1: -5,   d2: 5,    R0: 7.0,  note: 'both near phi = 0 (control chatter)' }
  ];
  for (var rc = 0; rc < reconCases.length; rc++) {
    var c = reconCases[rc];
    var run = Sim.createRun(Sim.toRad(c.d1), Sim.toRad(c.d2), c.R0);
    while (!run.done) run.step();
    var maxR = 0, maxAng = 0, bad = 0;
    for (var pj = 0; pj < run.path.length; pj++) {
      var rec = run.path[pj];
      if (!isFinite(rec.x1) || !isFinite(rec.y1) || !isFinite(rec.th1) ||
          !isFinite(rec.x2) || !isFinite(rec.y2) || !isFinite(rec.th2)) { bad++; continue; }
      var back = Sim.recoverReduced(rec);
      maxR = Math.max(maxR, Math.abs(back.R - rec.R));
      maxAng = Math.max(maxAng,
        Math.abs(Sim.wrap(back.phi1 - rec.phi1)),
        Math.abs(Sim.wrap(back.phi2 - rec.phi2)));
    }
    pass(bad === 0 && maxR < 1e-6 && maxAng < 1e-6,
      padEnd('(' + c.d1 + ', ' + c.d2 + ') R0=' + c.R0, 25) +
      'max |dR| ' + maxR.toExponential(1) + ', max |dphi| ' + maxAng.toExponential(1) +
      ', ' + padEnd(run.path.length, 6) + '(' + c.note + ')');
  }

  // sigma = 0 head-on: both aircraft must fly straight down the y = 0 line.
  var straight = Sim.createRun(0, 0, 8.0);
  while (!straight.done) straight.step();
  var sf = straight.path[straight.path.length - 1];
  pass(straight.outcome === O.MUTUAL, 'head-on closure at R0=8 ends in a mutual kill');
  pass(Math.abs(sf.y1) < 1e-9 && Math.abs(sf.y2) < 1e-9,
    'head-on: sigma = 0 keeps both aircraft on y = 0 (y1 = ' +
    sf.y1.toExponential(1) + ', y2 = ' + sf.y2.toExponential(1) + ')');

  // Pure pursuit must turn each aircraft TOWARD its opponent, not away. This is
  // the check that catches a mirrored-but-self-consistent sign convention.
  var turn = Sim.createRun(Sim.toRad(40), Sim.toRad(-40), 6.0);
  turn.step();
  var a0 = turn.path[0], a1 = turn.path[1];
  pass(Math.abs(a1.phi1) < Math.abs(a0.phi1),
    'pure pursuit reduces |phi1| on the first step (' +
    Sim.toDeg(a0.phi1).toFixed(3) + 'deg -> ' + Sim.toDeg(a1.phi1).toFixed(3) + 'deg)');
  pass(a1.th1 > a0.th1,
    'phi1 > 0 (opponent to the left) turns aircraft 1 left: th1 increases');

  // numerical edge cases near R0 = 1.0 — expected, and must not be counted as draws
  log('');
  log('§9 note — "numerical edge case (R->0)" near R0 ~ 1.0');
  var r10 = runGrid(1.0);
  log('  R0=1.0: ' + r10.c.numerical + ' of ' + r10.total + ' grid points (' + pct(r10.c.numerical / r10.total) +
      '), draws ' + r10.c.draw + ', terminal-at-0 ' + r10.c.terminal0);
  pass(r10.c.numerical > 0 && r10.c.numerical / r10.total < 0.05, 'present but rare, and reported separately from draws');

  log('');
  log(failures === 0 ? 'All checks passed. (' + ((Date.now() - t0) / 1000).toFixed(1) + ' s)'
                     : failures + ' check(s) FAILED. (' + ((Date.now() - t0) / 1000).toFixed(1) + ' s)');
  log('');

  var text = lines.join('\n');
  if (typeof document !== 'undefined') {
    var pre = document.getElementById('out');
    if (pre) pre.textContent = text;
    document.title = (failures === 0 ? 'PASS' : 'FAIL') + ' — acceptance checks';
  } else {
    console.log(text);
    if (typeof process !== 'undefined' && process.exit) process.exit(failures === 0 ? 0 : 1);
  }
})();
