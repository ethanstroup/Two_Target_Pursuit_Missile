/* sens.js — how sensitive are the spec §9 long-range outcome fractions to Rbar_0?
 * Run from the repo root: node layer0/sens.js
 */
var Sim = require('../sim.js');
var N = 73;
function grid(R0, rbar0) {
  var saved = Sim.PARAMS.Rbar0;
  Sim.PARAMS.Rbar0 = rbar0;
  var c = { terminal0: 0, p1: 0, p2: 0, mutual: 0, draw: 0, numerical: 0 };
  for (var i = 0; i < N; i++) for (var j = 0; j < N; j++) {
    var d1 = -180 + 360 * i / (N - 1), d2 = -180 + 360 * j / (N - 1);
    c[Sim.simulate(Sim.toRad(d1), Sim.toRad(d2), R0).outcome]++;
  }
  Sim.PARAMS.Rbar0 = saved;
  var n = N * N;
  return { p1: 100 * c.p1 / n, mutual: 100 * c.mutual / n };
}
console.log('Rbar_0      R0=5  P1 / mutual        R0=8  P1 / mutual       R0=12  P1 / mutual');
[6.1400, 6.1408, 3 + Math.PI, 6.1424, 6.1432, 6.1500].forEach(function (v) {
  var a = grid(5, v), b = grid(8, v), c = grid(12, v);
  console.log(v.toFixed(6) + '    ' +
    a.p1.toFixed(2) + ' / ' + a.mutual.toFixed(2) + '        ' +
    b.p1.toFixed(2) + ' / ' + b.mutual.toFixed(2) + '        ' +
    c.p1.toFixed(2) + ' / ' + c.mutual.toFixed(2));
});
