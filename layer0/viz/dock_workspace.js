/* Pointer/keyboard docking. Cards are reparented, never cloned: canvas state,
   selection, and existing controls survive every layout change. */
(function () {
  'use strict';
  window.DockWorkspace = { create: create };
  function create(options) {
    var M = window.DockLayout, root = options.root, viewport = options.viewport;
    var KEY = 'layer0.barrierExplorer.docking.v1';
    var cards = {}, names = {}, activeGesture = null, observer;
    var compact = window.matchMedia('(max-width: 760px)');
    var state = null;
    try { state = M.restore(localStorage.getItem(KEY)); } catch (e) { /* local storage unavailable */ }
    if (!state) state = { version: 1, tree: M.preset('default'), height: Math.max(800, Math.min(1100, window.innerHeight)) };
    var live = document.getElementById('dockAnnouncement');
    var hint = document.getElementById('dockHint');
    var presetSelect = document.getElementById('dockPreset');
    var heightHandle = document.getElementById('dockHeightHandle');
    var dialog = document.getElementById('dockMoveDialog');
    var moveTarget = document.getElementById('dockMoveTarget');
    var movePosition = document.getElementById('dockMovePosition');
    var movingPanel = null;
    var preview = document.createElement('div'); preview.className = 'dock-preview'; preview.hidden = true; preview.setAttribute('aria-hidden', 'true');
    var ghost = document.createElement('div'); ghost.className = 'dock-ghost'; ghost.hidden = true; ghost.setAttribute('aria-hidden', 'true');
    document.body.append(preview, ghost);

    M.IDS.forEach(function (id) {
      var card = cards[id] = document.getElementById(id), title = card.querySelector('h2');
      names[id] = title.firstChild.textContent.trim();
      card.classList.add('dock-leaf');
      var bar = document.createElement('div'); bar.className = 'dock-titlebar';
      var grip = document.createElement('span'); grip.className = 'dock-grip'; grip.textContent = '⠿'; grip.setAttribute('aria-hidden', 'true');
      card.insertBefore(bar, title); bar.append(grip, title);
      var menu = document.createElement('button'); menu.type = 'button'; menu.className = 'dock-move-button';
      menu.textContent = 'Move'; menu.setAttribute('aria-label', 'Move ' + names[id]); menu.setAttribute('aria-haspopup', 'dialog');
      menu.addEventListener('click', function () { openMove(id); }); bar.appendChild(menu);
      bar.title = 'Drag to dock this panel. Drop on an edge to split, or in the center to swap.';
      bar.addEventListener('pointerdown', function (e) { startDrag(e, id, bar); });
    });

    function save() {
      try { localStorage.setItem(KEY, JSON.stringify(state)); }
      catch (e) { live.textContent = 'Layout changed. This browser cannot save the layout between visits.'; }
    }
    function announce(text) { live.textContent = text; }
    function updateSize() {
      var min = M.minimum(state.tree);
      root.classList.toggle('dock-compact', compact.matches);
      root.style.minWidth = compact.matches ? '' : min.width + 'px';
      root.style.height = compact.matches ? '' : Math.max(min.height, state.height) + 'px';
      heightHandle.hidden = compact.matches;
      heightHandle.setAttribute('aria-valuemin', String(min.height));
      heightHandle.setAttribute('aria-valuemax', String(Math.max(4000, min.height)));
      heightHandle.setAttribute('aria-valuenow', String(Math.max(min.height, state.height)));
      hint.textContent = compact.matches ? 'Use each panel’s Move button to rearrange this stacked view.'
        : 'Drag a panel header to an edge to dock, or to the center to swap. Drag dividers to resize.';
      if (options.onChange) options.onChange();
    }
    function applySplit(node, el, handle) {
      var a = M.minimum(node.first), b = M.minimum(node.second), key = node.axis === 'x' ? 'width' : 'height';
      el.style[node.axis === 'x' ? 'gridTemplateColumns' : 'gridTemplateRows'] =
        'minmax(' + a[key] + 'px,' + node.ratio + 'fr) ' + M.GAP + 'px minmax(' + b[key] + 'px,' + (1 - node.ratio) + 'fr)';
      handle.setAttribute('aria-valuenow', String(Math.round(node.ratio * 100)));
    }
    function makeNode(node) {
      if (node.panel) return cards[node.panel];
      var el = document.createElement('div'); el.className = 'dock-split dock-axis-' + node.axis;
      var handle = document.createElement('div'); handle.className = 'dock-divider'; handle.tabIndex = 0;
      handle.setAttribute('role', 'separator');
      handle.setAttribute('aria-orientation', node.axis === 'x' ? 'vertical' : 'horizontal');
      handle.setAttribute('aria-label', 'Resize between ' + M.panels(node.first).map(function (id) { return names[id]; }).join(', ') + ' and ' + M.panels(node.second).map(function (id) { return names[id]; }).join(', '));
      handle.setAttribute('aria-valuemin', '2'); handle.setAttribute('aria-valuemax', '98');
      handle.title = 'Drag to resize. Arrow keys adjust; Shift + arrow makes a larger adjustment.';
      el.append(makeNode(node.first), handle, makeNode(node.second));
      applySplit(node, el, handle);
      handle.addEventListener('pointerdown', function (e) {
        if (compact.matches) return;
        var rect = el.getBoundingClientRect(), first = el.firstElementChild.getBoundingClientRect();
        var key = node.axis === 'x' ? 'width' : 'height', available = rect[key] - M.GAP, old = node.ratio;
        beginResize(e, handle, node.axis, function (delta) {
          node.ratio = M.resizeRatio(first[key] + delta, available, M.minimum(node.first)[key], M.minimum(node.second)[key]);
          applySplit(node, el, handle);
        }, function () { node.ratio = old; applySplit(node, el, handle); });
      });
      handle.addEventListener('keydown', function (e) {
        var minus = node.axis === 'x' ? 'ArrowLeft' : 'ArrowUp', plus = node.axis === 'x' ? 'ArrowRight' : 'ArrowDown';
        if (e.key !== minus && e.key !== plus) return;
        e.preventDefault();
        var key = node.axis === 'x' ? 'width' : 'height', available = el.getBoundingClientRect()[key] - M.GAP;
        var pixels = el.firstElementChild.getBoundingClientRect()[key] + (e.key === minus ? -1 : 1) * (e.shiftKey ? 40 : 12);
        node.ratio = M.resizeRatio(pixels, available, M.minimum(node.first)[key], M.minimum(node.second)[key]);
        applySplit(node, el, handle); changedSize();
      });
      return el;
    }
    function render() {
      // makeNode moves all six existing cards before the obsolete split DOM is removed.
      var node = makeNode(state.tree); root.replaceChildren(node);
      var shape = JSON.stringify(state.tree);
      presetSelect.value = shape === JSON.stringify(M.preset('default')) ? 'default'
        : shape === JSON.stringify(M.preset('analysis')) ? 'analysis' : 'custom';
      updateSize();
    }
    function changedSize() { presetSelect.value = 'custom'; save(); if (options.onChange) options.onChange(); }
    function beginResize(e, handle, axis, update, rollback) {
      if (e.button !== 0 || activeGesture) return;
      e.preventDefault(); handle.setPointerCapture(e.pointerId);
      var origin = axis === 'x' ? e.clientX : e.clientY;
      document.body.classList.add('dock-resizing'); document.body.style.setProperty('--dock-cursor', axis === 'x' ? 'col-resize' : 'row-resize');
      handle.classList.add('is-resizing');
      function move(ev) { if (ev.pointerId === e.pointerId) { update((axis === 'x' ? ev.clientX : ev.clientY) - origin); if (options.onChange) options.onChange(); } }
      function finish(cancel) {
        if (cancel) rollback();
        handle.removeEventListener('pointermove', move); handle.removeEventListener('pointerup', up); handle.removeEventListener('pointercancel', abort); handle.removeEventListener('lostpointercapture', abort);
        document.removeEventListener('keydown', keydown); window.removeEventListener('blur', abort);
        if (handle.hasPointerCapture(e.pointerId)) handle.releasePointerCapture(e.pointerId);
        handle.classList.remove('is-resizing'); document.body.classList.remove('dock-resizing');
        activeGesture = null; if (!cancel) changedSize(); else if (options.onChange) options.onChange();
      }
      function up(ev) { if (ev.pointerId === e.pointerId) finish(false); }
      function abort() { finish(true); }
      function keydown(ev) { if (ev.key === 'Escape') { ev.preventDefault(); abort(); } }
      activeGesture = abort;
      handle.addEventListener('pointermove', move); handle.addEventListener('pointerup', up); handle.addEventListener('pointercancel', abort); handle.addEventListener('lostpointercapture', abort);
      document.addEventListener('keydown', keydown); window.addEventListener('blur', abort);
    }
    function dock(source, target, zone) {
      state.tree = M.move(state.tree, source, target, zone); render();
      announce(names[source] + (zone === 'center' ? ' swapped with ' : ' docked ' + zone + ' of ') + names[target] + '.'); save();
      cards[source].querySelector('.dock-move-button').focus({ preventScroll: true });
    }
    function startDrag(e, source, bar) {
      if (e.button !== 0 || compact.matches || activeGesture || e.target.closest('button')) return;
      e.preventDefault(); bar.setPointerCapture(e.pointerId);
      var x = e.clientX, y = e.clientY, started = false, drop = null, frame = null;
      function locate() {
        drop = null;
        M.IDS.some(function (id) {
          if (id === source) return false;
          var rect = cards[id].getBoundingClientRect(), vr = viewport.getBoundingClientRect();
          if (x < vr.left || x > vr.right || y < vr.top || y > vr.bottom || y < 0 || y > window.innerHeight) return false;
          var zone = M.dropZone(rect, x, y); if (!zone) return false;
          drop = { target: id, zone: zone };
          var left = rect.left, top = rect.top, width = rect.width, height = rect.height;
          if (zone === 'left' || zone === 'right') { width /= 2; if (zone === 'right') left += width; }
          if (zone === 'top' || zone === 'bottom') { height /= 2; if (zone === 'bottom') top += height; }
          Object.assign(preview.style, { left: left + 4 + 'px', top: top + 4 + 'px', width: width - 8 + 'px', height: height - 8 + 'px' });
          preview.textContent = zone === 'center' ? 'Swap with ' + names[id] : 'Dock ' + (zone === 'top' ? 'above' : zone === 'bottom' ? 'below' : 'to the ' + zone);
          return true;
        });
        preview.hidden = !drop;
      }
      function tick() {
        if (!started) return;
        var scroll = y < 75 ? -16 : y > window.innerHeight - 75 ? 16 : 0;
        if (scroll) window.scrollBy(0, scroll);
        var r = viewport.getBoundingClientRect();
        if (y > r.top && y < r.bottom) {
          if (x < r.left + 40) viewport.scrollLeft -= 14;
          else if (x > r.right - 40) viewport.scrollLeft += 14;
        }
        locate(); frame = requestAnimationFrame(tick);
      }
      function move(ev) {
        if (ev.pointerId !== e.pointerId) return;
        x = ev.clientX; y = ev.clientY;
        if (!started && Math.hypot(x - e.clientX, y - e.clientY) < 6) return;
        if (!started) {
          started = true; document.body.classList.add('dock-dragging'); cards[source].classList.add('dock-source');
          ghost.hidden = false; ghost.textContent = names[source]; frame = requestAnimationFrame(tick);
        }
        ghost.style.left = Math.min(x + 18, window.innerWidth - 220) + 'px'; ghost.style.top = Math.max(8, y - 42) + 'px'; locate();
      }
      function finish(cancel) {
        if (frame !== null) cancelAnimationFrame(frame);
        bar.removeEventListener('pointermove', move); bar.removeEventListener('pointerup', up); bar.removeEventListener('pointercancel', abort); bar.removeEventListener('lostpointercapture', abort);
        document.removeEventListener('keydown', keydown); window.removeEventListener('blur', abort);
        if (bar.hasPointerCapture(e.pointerId)) bar.releasePointerCapture(e.pointerId);
        document.body.classList.remove('dock-dragging'); cards[source].classList.remove('dock-source');
        ghost.hidden = true; preview.hidden = true; activeGesture = null;
        if (!cancel && started && drop) dock(source, drop.target, drop.zone);
        else if (started) announce('Move cancelled. Layout unchanged.');
      }
      function up(ev) { if (ev.pointerId === e.pointerId) { x = ev.clientX; y = ev.clientY; if (started) locate(); finish(false); } }
      function abort() { finish(true); }
      function keydown(ev) { if (ev.key === 'Escape') { ev.preventDefault(); abort(); } }
      activeGesture = abort;
      bar.addEventListener('pointermove', move); bar.addEventListener('pointerup', up); bar.addEventListener('pointercancel', abort); bar.addEventListener('lostpointercapture', abort);
      document.addEventListener('keydown', keydown); window.addEventListener('blur', abort);
    }
    function openMove(id) {
      movingPanel = id; document.getElementById('dockMoveTitle').textContent = 'Move ' + names[id];
      moveTarget.replaceChildren();
      M.IDS.filter(function (target) { return target !== id; }).forEach(function (target) {
        var option = document.createElement('option'); option.value = target; option.textContent = names[target]; moveTarget.appendChild(option);
      });
      moveTarget.value = id === 'k3d' ? 'kI' : 'k3d'; movePosition.value = 'right'; dialog.showModal();
    }
    document.getElementById('dockMoveApply').addEventListener('click', function () {
      var source = movingPanel; dialog.close(); dock(source, moveTarget.value, movePosition.value);
    });
    document.getElementById('dockMoveCancel').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('close', function () { if (movingPanel) cards[movingPanel].querySelector('.dock-move-button').focus({ preventScroll: true }); });
    heightHandle.addEventListener('pointerdown', function (e) {
      var old = state.height, start = root.getBoundingClientRect().height;
      beginResize(e, heightHandle, 'y', function (delta) {
        state.height = Math.max(M.minimum(state.tree).height, Math.min(4000, start + delta)); updateSize();
      }, function () { state.height = old; updateSize(); });
    });
    heightHandle.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
      e.preventDefault(); state.height = Math.max(M.minimum(state.tree).height, Math.min(4000,
        root.getBoundingClientRect().height + (e.key === 'ArrowUp' ? -1 : 1) * (e.shiftKey ? 80 : 20)));
      updateSize(); changedSize();
    });
    function setPreset(name) {
      if (activeGesture) activeGesture();
      state.tree = M.preset(name); state.height = Math.max(800, Math.min(1100, window.innerHeight));
      viewport.scrollLeft = 0; render(); presetSelect.value = name; announce('Applied ' + name + ' layout.'); save();
    }
    presetSelect.addEventListener('change', function () { if (this.value !== 'custom') setPreset(this.value); });
    options.reset.addEventListener('click', function () { setPreset('default'); });
    compact.addEventListener('change', function () { if (activeGesture) activeGesture(); updateSize(); });
    if (window.ResizeObserver) {
      observer = new ResizeObserver(function () { if (options.onChange) options.onChange(); });
      M.IDS.forEach(function (id) { var cv = cards[id].querySelector('.cv'); if (cv) observer.observe(cv); });
    }
    render();
    // Resizing the window keeps the saved ratios; CSS enforces recursive minimum sizes.
    return { cancel: function () { if (activeGesture) activeGesture(); }, state: function () { return JSON.parse(JSON.stringify(state)); } };
  }
}());
