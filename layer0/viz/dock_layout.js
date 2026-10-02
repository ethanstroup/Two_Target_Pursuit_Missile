/* Docking tree operations, independent of the DOM and the numerical model. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DockLayout = factory();
}(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  var IDS = ['k3d', 'kA', 'kB', 'kG', 'kI', 'kR'];
  var GAP = 10;
  function leaf(id) { return { panel: id }; }
  function split(axis, ratio, first, second) { return { axis: axis, ratio: ratio, first: first, second: second }; }
  function preset(name) {
    if (name === 'analysis') return split('y', 0.65,
      split('x', 0.62, leaf('k3d'), leaf('kI')),
      split('x', 0.28, leaf('kG'), split('x', 0.34, leaf('kA'), split('x', 0.5, leaf('kB'), leaf('kR')))));
    return split('y', 0.65,
      split('x', 0.62, leaf('k3d'), split('y', 0.5, leaf('kA'), leaf('kB'))),
      split('x', 0.34, leaf('kG'), split('x', 0.5, leaf('kI'), leaf('kR'))));
  }
  function panels(node) { return node.panel ? [node.panel] : panels(node.first).concat(panels(node.second)); }
  function valid(tree) {
    var seen = new Set();
    function visit(node, depth) {
      if (!node || typeof node !== 'object' || depth > IDS.length) return false;
      if (Object.prototype.hasOwnProperty.call(node, 'panel')) {
        if (IDS.indexOf(node.panel) < 0 || seen.has(node.panel) || node.first || node.second) return false;
        seen.add(node.panel); return true;
      }
      return (node.axis === 'x' || node.axis === 'y') && Number.isFinite(node.ratio) &&
        node.ratio >= 0.02 && node.ratio <= 0.98 && visit(node.first, depth + 1) && visit(node.second, depth + 1);
    }
    return visit(tree, 0) && seen.size === IDS.length;
  }
  function map(node, fn) {
    return node.panel ? fn(node.panel) : split(node.axis, node.ratio, map(node.first, fn), map(node.second, fn));
  }
  function remove(node, id) {
    if (node.panel) return node.panel === id ? null : leaf(node.panel);
    var a = remove(node.first, id), b = remove(node.second, id);
    return !a ? b : !b ? a : split(node.axis, node.ratio, a, b);
  }
  function move(tree, source, target, zone) {
    if (!valid(tree) || IDS.indexOf(source) < 0 || IDS.indexOf(target) < 0 ||
        ['left', 'right', 'top', 'bottom', 'center'].indexOf(zone) < 0) throw new Error('Invalid docking operation');
    if (source === target) return map(tree, leaf);
    if (zone === 'center') return map(tree, function (id) { return leaf(id === source ? target : id === target ? source : id); });
    var axis = zone === 'left' || zone === 'right' ? 'x' : 'y';
    var before = zone === 'left' || zone === 'top';
    return map(remove(tree, source), function (id) {
      return id !== target ? leaf(id) : split(axis, 0.5, leaf(before ? source : target), leaf(before ? target : source));
    });
  }
  function minimum(node) {
    if (node.panel) return { width: node.panel === 'k3d' ? 300 : 240, height: node.panel === 'k3d' ? 270 : 220 };
    var a = minimum(node.first), b = minimum(node.second);
    return node.axis === 'x' ? { width: a.width + b.width + GAP, height: Math.max(a.height, b.height) }
      : { width: Math.max(a.width, b.width), height: a.height + b.height + GAP };
  }
  function resizeRatio(pixels, available, firstMin, secondMin) {
    if (available <= 0 || available < firstMin + secondMin) return 0.5;
    return Math.max(0.02, Math.min(0.98, Math.max(firstMin, Math.min(available - secondMin, pixels)) / available));
  }
  function dropZone(rect, x, y) {
    var u = (x - rect.left) / rect.width, v = (y - rect.top) / rect.height;
    if (u < 0 || u > 1 || v < 0 || v > 1 || !Number.isFinite(u + v)) return null;
    if (u > 0.27 && u < 0.73 && v > 0.27 && v < 0.73) return 'center';
    var distances = [u, 1 - u, v, 1 - v];
    return ['left', 'right', 'top', 'bottom'][distances.indexOf(Math.min.apply(null, distances))];
  }
  function restore(text) {
    try {
      var state = JSON.parse(text);
      if (state.version !== 1 || !valid(state.tree) || !Number.isFinite(state.height) || state.height < 400 || state.height > 4000) return null;
      return state;
    } catch (e) { return null; }
  }
  return { IDS: IDS, GAP: GAP, preset: preset, panels: panels, valid: valid, move: move,
    minimum: minimum, resizeRatio: resizeRatio, dropZone: dropZone, restore: restore };
}));
