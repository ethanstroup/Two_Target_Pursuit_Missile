/* test_barrier_js.js — acceptance tests for barrier.js.
 *
 * Mirrors layer0/test_barrier.py. The two invariants ARE the test: a genuine
 * barrier trajectory carries FI = 1 (Eq. 23) and H* = 0 (Eq. 15) all the way
 * back from the BUP, and H* is the one that catches a mishandled switch.
 *
 * Run:  node test_barrier_js.js
 */
'use strict';

var Bar = require('../layer1/barrier.js');

var nPass = 0, nFail = 0;
function pass(ok, msg) {
  if (ok) { nPass++; console.log('  PASS  ' + msg); }
  else { nFail++; console.log('  FAIL  ' + msg); }
}
function near(a, b, tol) { return Math.abs(a - b) <= tol; }

var D = Math.PI / 180;
var P = Bar.PARAMS;

console.log('='.repeat(78));
console.log('barrier.js — Davidovitz & Shinar (1989) barrier reconstruction');
console.log('='.repeat(78));

// -- 1. parameters against Table 2 -----------------------------------------
console.log('\n1. Table 2 range coordinates');
pass(near(Bar.Rhi(Math.PI), 3.0, 5e-4),
     'A_1  Rbar(pi)     = ' + Bar.Rhi(Math.PI).toFixed(5) + '   Table 2  3.0');
pass(near(Bar.Rhi(0), 6.1416, 5e-5),
     'O_1  Rbar(0)      = ' + Bar.Rhi(0).toFixed(5) + '   Table 2  6.1416');
pass(near(Bar.Rhi(P.beta), 4.649, 5e-4),
     'beta Rbar(beta)   = ' + Bar.Rhi(P.beta).toFixed(5) + '   Table 2  4.649');
pass(near(Bar.Rlo(Math.PI), 0.25, 5e-3),
     'M_1  Rmin(pi)     = ' + Bar.Rlo(Math.PI).toFixed(5) + '   Table 2  0.25');
pass(near(Bar.Rlo(0), 0.85, 5e-3),
     'Z_1  Rmin(0)      = ' + Bar.Rlo(0).toFixed(5) + '   Table 2  0.85');
pass(near(Bar.Rlo(P.beta), 0.762, 5e-4),
     'nu   Rmin(beta)   = ' + Bar.Rlo(P.beta).toFixed(5) + '   Table 2  0.762');
pass(near(Math.sin(P.beta) + Math.sin(Math.PI / 2), 1.707, 5e-4),
     'Q_1  boresight BUP at cos phi_2 = 0 = '
       + (Math.sin(P.beta) + 1).toFixed(5) + '   Table 2  1.707');

// -- 2. seeds satisfy the invariants exactly -------------------------------
console.log('\n2. Terminal costates at the BUP');
var seeds = [];
for (var i = 0; i < 120; i++) {
  var p2 = -Math.PI + 0.05 + (2 * Math.PI - 0.1) * i / 119;
  if (Math.abs(p2) > 0.02) seeds = seeds.concat(Bar.seedMaxrange(p2));
  if (Math.abs(Math.sin(p2)) > 0.02) seeds = seeds.concat(Bar.seedMinrange(p2));
  seeds = seeds.concat(Bar.seedBoresight(p2, +1));
  seeds = seeds.concat(Bar.seedBoresight(p2, -1));
}
console.log('        ' + seeds.length + ' BUP seeds');
var fi0 = 0, h0 = 0;
seeds.forEach(function (y) {
  fi0 = Math.max(fi0, Math.abs(Bar.firstIntegral(y[0], y[3], y[4], y[5]) - 1));
  h0 = Math.max(h0, Math.abs(Bar.hamiltonianStar(y[0], y[1], y[2], y[3], y[4], y[5])));
});
pass(fi0 < 1e-12, 'first integral = 1 at every seed   max |FI-1| = ' + fi0.toExponential(2));
pass(h0 < 1e-12, 'semipermeability H* = 0 at every seed   max |H*| = ' + h0.toExponential(2));

// -- 3. invariants along retrograde trajectories ---------------------------
console.log('\n3. Invariants along retrograde barrier trajectories (tau up to 6)');
var fiMax = 0, hMax = 0, nSw = 0;
var sample = seeds.filter(function (_, k) { return k % 4 === 0; });
sample.forEach(function (y0) {
  var tr = Bar.integrateRetrograde(y0, { tauMax: 6.0, dt: 1e-3 });
  fiMax = Math.max(fiMax, tr.fiErr);
  hMax = Math.max(hMax, tr.hErr);
  nSw += tr.switches.length;
});
console.log('        ' + sample.length + ' trajectories, ' + nSw + ' control switches located');
pass(fiMax < 1e-8, 'first integral drift   max |FI-1| = ' + fiMax.toExponential(2));
pass(hMax < 1e-8, 'semipermeability drift max |H*|   = ' + hMax.toExponential(2));

// -- 4. printed control laws ------------------------------------------------
console.log('\n4. Barrier strategies reproduce the paper\'s printed control laws');
var ok = true;
for (var j = 0; j < 200; j++) {
  var q2 = -Math.PI + 0.03 + (2 * Math.PI - 0.06) * j / 199;
  Bar.seedMinrange(q2).forEach(function (y) {
    var s = Bar.controls(y);
    if (Math.abs(Math.sin(y[1])) > 1e-6 && s[0] !== Math.sign(Math.sin(y[1]))) ok = false;
    if (Math.abs(Math.sin(y[2])) > 1e-6 && s[1] !== -Math.sign(Math.sin(y[2]))) ok = false;
  });
}
pass(ok, 'Eqs. (45), (52) on the minimum-range BUP');

ok = true;
for (j = 0; j < 200; j++) {
  q2 = -0.9 + 1.8 * j / 199;
  if (Math.abs(q2) < 0.02) continue;
  Bar.seedMaxrange(q2).forEach(function (y) {
    if (Bar.controls(y)[1] !== Math.sign(y[2])) ok = false;
  });
}
pass(ok, 'Eq. (31)  sigma_2* = sign(phi_2) on the maximum-range BUP');

ok = true;
var okPrinted = true, nPrintedBad = 0, nBore = 0;
for (j = 0; j < 200; j++) {
  q2 = -Math.PI + 0.02 + (2 * Math.PI - 0.04) * j / 199;
  [+1, -1].forEach(function (sg) {
    Bar.seedBoresight(q2, sg).forEach(function (y) {
      nBore++;
      var s = Bar.controls(y);
      if (s[0] !== -Math.sign(y[1])) ok = false;
      var want = Math.sign(Math.cos(y[2])) * Math.sign(y[1]);
      if (Math.abs(Math.cos(y[2])) > 1e-6 && s[1] !== want) ok = false;
      // Eq. (63) exactly as printed, for comparison
      var l1p = (Math.sin(y[1]) + Math.sin(y[2])) * Math.sign(y[1]);
      var sp = Bar.controls([y[0], y[1], y[2], 0, l1p, 0]);
      if (Math.abs(Math.cos(y[2])) > 1e-6 && sp[1] !== want) { okPrinted = false; nPrintedBad++; }
    });
  });
}
pass(ok, 'Eqs. (61), (65) on the off-boresight BUP');
console.log('        seeding with Eq. (63) exactly as printed instead: '
            + nPrintedBad + ' of ' + nBore + ' seeds then contradict Eq. (65)');
console.log('        (all at phi_1 = -beta — the spurious sign(phi_1) flips the pair)');

console.log('\n' + '='.repeat(78));
console.log(nPass + ' passed, ' + nFail + ' failed');
console.log('='.repeat(78));
process.exit(nFail ? 1 : 0);
