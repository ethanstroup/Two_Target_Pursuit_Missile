/* A non-modal settings drawer. Existing controls keep their IDs and handlers;
   opening settings does not reparent, resize, or rebuild any plot. */
(function () {
  'use strict';
  window.WorkspaceChrome = { create: create };
  function create() {
    var drawer = document.getElementById('workspaceDrawer');
    var tools = document.getElementById('workspaceTools');
    var closeButton = document.getElementById('drawerClose');
    var title = document.getElementById('drawerTitle');
    var buttons = Array.from(document.querySelectorAll('[data-workspace-tool]'));
    var panels = Array.from(document.querySelectorAll('[data-drawer-panel]'));
    var titles = { display: 'Display & sampling', export: 'Export & appearance', layout: 'Workspace layout', help: 'How to read this view' };
    var current = null, returnFocus = null, activeView = 'barrier';
    function sync() {
      drawer.hidden = !current;
      panels.forEach(function (panel) { panel.hidden = panel.getAttribute('data-drawer-panel') !== current; });
      buttons.forEach(function (button) {
        var active = button.getAttribute('data-workspace-tool') === current;
        button.setAttribute('aria-expanded', String(active));
        button.classList.toggle('on', active);
      });
    }
    function close(restoreFocus) {
      current = null; sync();
      if (restoreFocus && returnFocus && !tools.hidden) returnFocus.focus({ preventScroll: true });
    }
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        if (activeView !== 'barrier' || window.BarrierExportBusy) return;
        var name = button.getAttribute('data-workspace-tool');
        if (!titles[name]) return;
        var inside = drawer.contains(button);
        if (current === name && !inside) { close(true); return; }
        if (!inside) returnFocus = button;
        current = name; title.textContent = titles[name]; sync();
        drawer.querySelector('.drawer-content').scrollTop = 0;
        if (!inside) closeButton.focus({ preventScroll: true });
      });
    });
    closeButton.addEventListener('click', function () { close(true); });
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape' || !current || event.defaultPrevented) return;
      // A capture or panel-move dialog owns Escape while it is open. A docking
      // gesture owns Escape until it ends, so closing settings cannot swallow it.
      if (document.querySelector('dialog[open]') || document.body.classList.contains('dock-dragging') || document.body.classList.contains('dock-resizing')) return;
      event.preventDefault(); // keep the selected trajectory pinned
      close(true);
    }, true);
    sync();
    return {
      setView: function (name) {
        activeView = name;
        if (name !== 'barrier') close(false);
        tools.hidden = name !== 'barrier';
      }
    };
  }
}());
