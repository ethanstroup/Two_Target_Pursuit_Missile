// test_los_coords.js -- checks for los_coords.js (the explorer's coordinates tabs).
// Run: node layer0/viz/test_los_coords.js      (also run by test_viz.py §10)
'use strict';
var B = require('../barrier.js');
var L = require('./los_coords.js');
var Sim = require('../../heuristic_simulator/sim.js');

var PI = Math.PI, D = PI / 180, wrap = B.wrap;
var pass = 0, fail = 0;
function check(ok, msg) {
  if (ok) pass++; else fail++;
  console.log('  ' + (ok ? 'PASS' : 'FAIL') + '  ' + msg);
}

var seed = 12345;                       // deterministic, so a failure reproduces
function rnd() { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; }
function randWorld() {
  return { p1: [8 * rnd() - 4, 8 * rnd() - 4], th1: 2 * PI * rnd() - PI,
           p2: [8 * rnd() - 4, 8 * rnd() - 4], th2: 2 * PI * rnd() - PI };
}
function wdiff(a, b) {
  return Math.max(Math.hypot(a.p1[0] - b.p1[0], a.p1[1] - b.p1[1]),
                  Math.hypot(a.p2[0] - b.p2[0], a.p2[1] - b.p2[1]),
                  Math.abs(wrap(a.th1 - b.th1)), Math.abs(wrap(a.th2 - b.th2)));
}
function worst(n, f) { var m = 0; for (var i = 0; i < n; i++) m = Math.max(m, f()); return m; }

var e;
e = worst(2000, function () {
  var w = randWorld(), s = L.worldToLos(w);
  return wdiff(w, L.losToWorld(s, w.p1, s.psi));
});
check(e < 1e-12, 'world -> (R, phi1, phi2) -> world round trip: max err ' + e.toExponential(2));

e = worst(2000, function () {
  var w = randWorld();
  var w2 = L.rigidMotion(w, 2 * PI * rnd(), 10 * rnd() - 5, 10 * rnd() - 5);
  return L.stateDiff(L.worldToLos(w), L.worldToLos(w2));
});
check(e < 1e-12, '(R, phi1, phi2) unchanged by rotation + translation: max err ' + e.toExponential(2));

// Finite differences of the world kinematics against barrier.js's own reduced dynamics.
var h = 1e-4;
e = worst(500, function () {
  var w = randWorld(), s = L.worldToLos(w);
  if (s.R < 0.5) return 0;
  var s1 = 2 * rnd() - 1, s2 = 2 * rnd() - 1;
  var f = L.worldToLos(L.rk4World(w, s1, s2, h)), b = L.worldToLos(L.rk4World(w, s1, s2, -h));
  var d = B.stateDot(s.R, s.phi1, s.phi2, s1, s2);
  return Math.max(Math.abs((f.R - b.R) / (2 * h) - d[0]),
                  Math.abs(wrap(f.phi1 - b.phi1) / (2 * h) - d[1]),
                  Math.abs(wrap(f.phi2 - b.phi2) / (2 * h) - d[2]));
});
check(e < 1e-6, 'finite differences of world motion match Barrier.stateDot: max err ' + e.toExponential(2));

e = worst(2000, function () {
  var w = randWorld(), s = L.worldToLos(w);
  var a = L.worldToTargetFrame(w.p1, w.p2, w.th2), b = L.attackerInTargetFrame(s.R, s.phi2);
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
});
check(e < 1e-12, 'target-frame position from world == from (R, phi2) alone: max err ' + e.toExponential(2));

e = worst(2000, function () {
  var w = randWorld(), s = L.worldToLos(w);
  var dir = Math.atan2(w.p1[1] - w.p2[1], w.p1[0] - w.p2[0]);
  return Math.abs(wrap(dir - L.losDirFromTarget(w.th2, s.phi2)));
});
check(e < 1e-12, 'direction from player 2 to player 1 is th2 + phi2: max err ' + e.toExponential(2));

e = worst(500, function () {
  var w = randWorld(), s = L.worldToLos(w), dth = 2 * PI * rnd() - PI;
  var a = L.worldToLos({ p1: w.p1, th1: w.th1 + dth, p2: w.p2, th2: w.th2 });
  var b = L.worldToLos({ p1: w.p1, th1: w.th1, p2: w.p2, th2: w.th2 + dth });
  return Math.max(Math.abs(a.R - s.R), Math.abs(wrap(a.phi2 - s.phi2)), Math.abs(wrap(a.phi1 - s.phi1 + dth)),
                  Math.abs(b.R - s.R), Math.abs(wrap(b.phi1 - s.phi1)), Math.abs(wrap(b.phi2 - s.phi2 + dth)));
});
check(e < 1e-12, 'turning player i changes phi_i only: max err ' + e.toExponential(2));

// Same convention as the heuristic simulator's ground-frame reconstruction.
e = worst(2000, function () {
  var w = randWorld(), s = L.worldToLos(w);
  var r = Sim.recoverReduced({ x1: w.p1[0], y1: w.p1[1], th1: w.th1, x2: w.p2[0], y2: w.p2[1], th2: w.th2 });
  return Math.max(Math.abs(r.R - s.R), Math.abs(wrap(r.phi1 - s.phi1)), Math.abs(wrap(r.phi2 - s.phi2)));
});
check(e < 1e-12, 'worldToLos == sim.js recoverReduced: max err ' + e.toExponential(2));

e = worst(500, function () {
  var s = { R: 0.5 + 6 * rnd(), phi1: 2 * PI * rnd() - PI, phi2: 2 * PI * rnd() - PI };
  var ph = Sim.physInit(s.R, s.phi1, s.phi2);
  var w = L.losToWorld(s, [ph.x1, ph.y1], 0);
  var s1 = 2 * rnd() - 1, s2 = 2 * rnd() - 1, dt = 0.05;
  var q = Sim.physDeriv(ph, { s1: s1, s2: s2 });
  var a = L.rk4World(w, s1, s2, dt);
  // straight-line check of the turn-rate sign: dth/dt must be sim.js's -sigma
  return Math.max(wdiff(w, { p1: [ph.x1, ph.y1], th1: ph.th1, p2: [ph.x2, ph.y2], th2: ph.th2 }),
                  Math.abs(wrap(a.th1 - w.th1 - q.th1 * dt)), Math.abs(wrap(a.th2 - w.th2 - q.th2 * dt)));
});
check(e < 1e-12, 'losToWorld matches sim.js physInit, and turn rates match physDeriv (dth/dt = -sigma): max err ' + e.toExponential(2));

// T1 predicates agree with the explorer's canFire(own, tgt, R) on player 1 -> 2.
var agree = true;
for (var i = 0; i < 5000; i++) {
  var s = { R: 7 * rnd(), phi1: 2 * PI * rnd() - PI, phi2: 2 * PI * rnd() - PI };
  var cf = Math.abs(s.phi1) <= B.PARAMS.beta && s.R >= B.Rlo(s.phi2) && s.R < B.Rhi(s.phi2);
  var m = L.margin(s);
  if (cf !== L.inT1(s)) agree = false;
  if (Math.abs(m) > 1e-12 && (m < 0) !== cf) agree = false;      // boundary itself excepted
}
check(agree, 'inT1 and sign of margin agree with canFire over 5000 random states');

var mono = true, prev = Infinity, sym = 0;
for (var d = 0; d <= 180; d += 0.5) {
  var r = L.rHi(d * D);
  if (r > prev + 1e-15) mono = false;
  prev = r; sym = Math.max(sym, Math.abs(r - L.rHi(-d * D)));
}
check(mono && sym < 1e-12, 'R-bar(phi2) falls monotonically from nose (' + L.rHi(0).toFixed(4) +
      ') to tail (' + L.rHi(PI).toFixed(4) + '), symmetric in phi2');

function W(p1, th1, p2, th2) { return L.worldToLos({ p1: p1, th1: th1, p2: p2, th2: th2 }); }
check(L.inT1(W([-2, 0], 0, [2, 0], PI)) && L.inT1(W([-1.5, 0], 0, [1.5, 0], PI / 2)) &&
      L.inT1(W([-1.25, 0], 0, [1.25, 0], 0)) && !L.inT1(W([-2, 0], 0, [2, 0], 0)) &&
      !L.inT1(W([-2, 0], 60 * D, [2, 0], PI)),
      'tab presets: head-on, beam, tail chase in T1; tail too far and nose off not');

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
