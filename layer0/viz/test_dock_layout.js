'use strict';
const assert = require('node:assert/strict');
const { test } = require('node:test');
const M = require('./dock_layout.js');

function samePanels(tree) {
  assert.equal(M.valid(tree), true);
  assert.deepEqual(M.panels(tree).slice().sort(), M.IDS.slice().sort());
}
function parentOf(node, id) {
  if (node.panel) return null;
  if (node.first.panel === id || node.second.panel === id) return node;
  return parentOf(node.first, id) || parentOf(node.second, id);
}

test('overview and analysis include all six panels exactly once', () => {
  samePanels(M.preset('default')); samePanels(M.preset('analysis'));
  const analysis = M.preset('analysis');
  assert.equal(parentOf(analysis, 'kI').first.panel, 'k3d');
  assert.equal(parentOf(analysis, 'kI').axis, 'x');
});

test('costates can dock on every edge of the 3D panel without losing other panels', () => {
  for (const zone of ['left', 'right', 'top', 'bottom']) {
    const original = M.preset('default'), snapshot = JSON.stringify(original);
    const moved = M.move(original, 'kI', 'k3d', zone);
    samePanels(moved);
    const parent = parentOf(moved, 'kI');
    assert.equal(parent.axis, ['left', 'right'].includes(zone) ? 'x' : 'y');
    assert.equal(parent[['left', 'top'].includes(zone) ? 'first' : 'second'].panel, 'kI');
    assert.equal(JSON.stringify(original), snapshot, 'preview/move must not mutate the previous layout');
  }
});

test('center drop swaps slots and preserves split geometry', () => {
  const initial = M.preset('default');
  const moved = M.move(initial, 'kI', 'kA', 'center');
  assert.equal(moved.first.second.first.panel, 'kI');
  assert.equal(moved.second.second.first.panel, 'kA');
  assert.equal(moved.first.ratio, initial.first.ratio);
  assert.equal(moved.ratio, initial.ratio);
  assert.deepEqual(M.move(moved, 'kI', 'kA', 'center'), initial);
});

test('moving between sibling slots collapses empty parents correctly', () => {
  const moved = M.move(M.preset('default'), 'kA', 'kB', 'left');
  samePanels(moved);
  assert.deepEqual(moved.first.second, {axis: 'x', ratio: 0.5, first: {panel: 'kA'}, second: {panel: 'kB'}});
});

test('repeated arbitrary docks preserve panel identity, valid ratios and finite minimum sizes', () => {
  let tree = M.preset('default'), seed = 891;
  const next = n => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed % n; };
  for (let i = 0; i < 2000; i++) {
    tree = M.move(tree, M.IDS[next(6)], M.IDS[next(6)], ['left','right','top','bottom','center'][next(5)]);
    samePanels(tree);
    const size = M.minimum(tree);
    assert(size.width >= 300 && size.width <= 1550);
    assert(size.height >= 270 && size.height <= 1420);
  }
});

test('self-drop is harmless and unsupported targets are rejected', () => {
  const tree = M.preset('default');
  assert.deepEqual(M.move(tree, 'kI', 'kI', 'left'), tree);
  assert.throws(() => M.move(tree, 'missing', 'k3d', 'right'));
  assert.throws(() => M.move(tree, 'kI', 'k3d', 'float'));
});

test('divider constraints reserve the minimum sizes of both subtrees', () => {
  assert.equal(M.resizeRatio(-500, 1000, 300, 240), 0.3);
  assert.equal(M.resizeRatio(1800, 1000, 300, 240), 0.76);
  assert.equal(M.resizeRatio(510, 1000, 300, 240), 0.51);
  assert.equal(M.resizeRatio(50, 0, 300, 240), 0.5);
  const min = M.minimum(M.preset('default'));
  assert.deepEqual(min, {width: 740, height: 680});
});

test('edge, center, and outside hit testing use the current panel rectangle', () => {
  const rect = {left: 100, top: 200, width: 500, height: 300};
  assert.equal(M.dropZone(rect, 350, 350), 'center');
  assert.equal(M.dropZone(rect, 105, 350), 'left');
  assert.equal(M.dropZone(rect, 595, 350), 'right');
  assert.equal(M.dropZone(rect, 350, 205), 'top');
  assert.equal(M.dropZone(rect, 350, 495), 'bottom');
  assert.equal(M.dropZone(rect, 350, 501), null);
});

test('saved layouts round-trip, with corrupt or obsolete data falling back safely', () => {
  const state = {version: 1, height: 900, tree: M.move(M.preset('default'), 'kI', 'k3d', 'right')};
  assert.deepEqual(M.restore(JSON.stringify(state)), state);
  for (const text of [null, '', 'bad json', '{}', '{"version":2}', JSON.stringify({...state,height:-5}), JSON.stringify({...state,height:Infinity})]) assert.equal(M.restore(text), null);
  const duplicate = M.preset('default'); duplicate.second.second.first.panel = 'k3d';
  assert.equal(M.restore(JSON.stringify({...state,tree:duplicate})), null);
  const missing = M.preset('default'); missing.second = missing.second.first;
  assert.equal(M.valid(missing), false);
  const ratio = M.preset('default'); ratio.ratio = NaN;
  assert.equal(M.valid(ratio), false);
});
