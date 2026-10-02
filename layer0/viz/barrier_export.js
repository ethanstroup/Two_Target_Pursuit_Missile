/* Barrier capture controls and composition. Rendering is supplied by the page;
   no dynamics or trajectory integration is performed here. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.BarrierExport = factory();
}(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  var PANELS = { c3d: 'Barrier surface', cA: 'Angle projection', cB: 'Range projection', cG: 'Engagement geometry', cI: 'Costates & invariants' };
  function appearance(value) {
    return { text: value && Number.isFinite(value.text) ? Math.max(1, Math.min(3, value.text)) : 1,
      line: value && Number.isFinite(value.line) ? Math.max(1, Math.min(2.5, value.line)) : 1,
      transparency: value && Number.isFinite(value.transparency) ? Math.max(0, Math.min(1, value.transparency)) : 0.5 };
  }
  function font(value, scale) { return value.replace(/([\d.]+)px/, function (_, size) { return (+size * scale).toFixed(2) + 'px'; }); }
  function timeline(maxTau, count, seconds, horizon) {
    if (!Number.isFinite(maxTau) || maxTau <= 0 || maxTau > horizon) throw new Error('Maximum τ must be greater than 0 and no more than ' + horizon + '.');
    if (!Number.isInteger(count) || count < 2 || count > 180) throw new Error('Choose 2–180 GIF frames.');
    if (!Number.isFinite(seconds) || seconds < 2 || seconds > 20) throw new Error('Growth duration must be 2–20 seconds.');
    if (seconds * 100 < count * 2) throw new Error('Use at least ' + (count / 50).toFixed(1) + ' seconds for ' + count + ' frames, or choose fewer frames.');
    // GIF delays are integer centiseconds. Rounding cumulative time distributes
    // quantization error and makes the requested total duration exact to 0.01 s.
    return Array.from({ length: count }, function (_, i) {
      return { tau: maxTau * i / (count - 1), delay: Math.round((i + 1) * seconds * 100 / count) - Math.round(i * seconds * 100 / count) + (i === count - 1 ? 100 : 0) };
    });
  }
  function wrap(ctx, text, width) {
    var lines = [], line = '';
    text.split(/\s+/).forEach(function (word) {
      var next = line ? line + ' ' + word : word;
      if (line && ctx.measureText(next).width > width) { lines.push(line); line = word; } else line = next;
    });
    if (line) lines.push(line);
    return lines;
  }
  function layout(panels, width, scale, ctx, caption) {
    if (!panels.length) throw new Error('Select at least one panel to export.');
    var pad = 18, gap = 14, titleSize = 14 * scale, line = titleSize * 1.35;
    ctx.font = '600 ' + titleSize + 'px Segoe UI, sans-serif';
    var boxes = panels.map(function (p) {
      if (!(p.w > 0 && p.h > 0)) throw new Error('A selected panel has no visible size. Open the Barrier surface tab and try again.');
      var lines = wrap(ctx, p.title, p.w - 12);
      return { id: p.id, cv: p.cv, w: p.w, h: p.h, lines: lines, head: Math.ceil(lines.length * line + 12) };
    });
    var special = panels.length === 3 && panels[0].id === 'c3d' && panels[1].id === 'cA' && panels[2].id === 'cB';
    var naturalWidth, contentHeight;
    if (special) {
      boxes[0].x = pad; boxes[0].y = pad;
      boxes[1].x = boxes[2].x = pad + boxes[0].w + gap;
      boxes[1].y = pad; boxes[2].y = pad + boxes[1].head + boxes[1].h + gap;
      naturalWidth = boxes[0].w + Math.max(boxes[1].w, boxes[2].w) + gap + pad * 2;
      contentHeight = Math.max(boxes[0].head + boxes[0].h, boxes[1].head + boxes[1].h + gap + boxes[2].head + boxes[2].h);
    } else {
      var columns = boxes.length === 1 ? 1 : 2, colWidth = Math.max.apply(null, boxes.map(function (p) { return p.w; }));
      var y = pad;
      for (var i = 0; i < boxes.length; i += columns) {
        var rowHeight = 0;
        boxes.slice(i, i + columns).forEach(function (b, col) {
          b.x = pad + col * (colWidth + gap); b.y = y;
          rowHeight = Math.max(rowHeight, b.head + b.h);
        });
        y += rowHeight + gap;
      }
      naturalWidth = columns * colWidth + (columns - 1) * gap + pad * 2;
      contentHeight = y - pad - gap;
    }
    var footerSize = 12 * scale;
    ctx.font = footerSize + 'px Segoe UI, sans-serif';
    var footerLines = wrap(ctx, caption, naturalWidth - pad * 2);
    var footerY = pad + contentHeight + 22;
    var naturalHeight = footerY + footerLines.length * footerSize * 1.4 + pad;
    var factor = width / naturalWidth, height = Math.ceil(naturalHeight * factor);
    if (height > 8192 || width * height > 24000000) throw new Error('This export is too tall. Select fewer panels or reduce the image width.');
    return { boxes: boxes, width: width, height: height, factor: factor, titleSize: titleSize, line: line,
      footerSize: footerSize, footerY: footerY, footerWidth: naturalWidth - pad * 2, pad: pad };
  }
  function composite(ctx, L, caption) {
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, L.width, L.height);
    ctx.setTransform(L.factor, 0, 0, L.factor, 0, 0);
    L.boxes.forEach(function (b) {
      ctx.font = '600 ' + L.titleSize + 'px Segoe UI, sans-serif'; ctx.fillStyle = '#1d2e40'; ctx.textBaseline = 'top'; ctx.textAlign = 'left';
      b.lines.forEach(function (text, i) { ctx.fillText(text, b.x + 4, b.y + i * L.line); });
      ctx.drawImage(b.cv, b.x, b.y + b.head, b.w, b.h);
      ctx.strokeStyle = '#dce3e9'; ctx.lineWidth = 1; ctx.strokeRect(b.x, b.y + b.head, b.w, b.h);
    });
    ctx.font = L.footerSize + 'px Segoe UI, sans-serif'; ctx.fillStyle = '#526376';
    wrap(ctx, caption, L.footerWidth).forEach(function (text, i) { ctx.fillText(text, L.pad, L.footerY + i * L.footerSize * 1.4); });
  }
  async function encode(options) {
    var E = options.encoder, W = options.width, H = options.height, frames = options.frames;
    var histogram = { n: new Uint32Array(32768), r: new Float64Array(32768), g: new Float64Array(32768), b: new Float64Array(32768) };
    function check() { if (options.cancelled()) { var e = new Error('Export cancelled.'); e.name = 'AbortError'; throw e; } }
    var pause = options.yieldFrame || function () { return new Promise(function (resolve) { setTimeout(resolve, 0); }); };
    for (var k of [0, Math.floor(frames.length / 3), Math.floor(2 * frames.length / 3), frames.length - 1]) {
      check(); E.histogram(options.render(k), histogram); await pause();
    }
    var P = E.palette(histogram), map = new Int16Array(32768).fill(-1);
    var gif = new E.Writer(W, H, P.bytes, frames[0].delay);
    var prev = new Uint8Array(W * H), cur = new Uint8Array(W * H);
    for (var f = 0; f < frames.length; f++) {
      check(); E.quantize(options.render(f), P, map, cur); gif.delay = frames[f].delay;
      if (f === 0) { gif.frame(0, 0, W, H, cur, false); prev.set(cur); }
      else {
        var x0 = W, y0 = H, x1 = -1, y1 = -1, i, x, y;
        for (y = 0; y < H; y++) for (x = 0, i = y * W; x < W; x++, i++) {
          if (cur[i] !== prev[i]) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
        }
        if (x1 < 0) gif.frame(0, 0, 1, 1, new Uint8Array([255]), true);
        else {
          var w = x1 - x0 + 1, h = y1 - y0 + 1, sub = new Uint8Array(w * h), j = 0;
          for (y = y0; y <= y1; y++) for (x = x0, i = y * W + x0; x <= x1; x++, i++, j++) {
            sub[j] = cur[i] === prev[i] ? 255 : cur[i]; prev[i] = cur[i];
          }
          gif.frame(x0, y0, w, h, sub, true);
        }
      }
      options.progress(f + 1, frames.length); await pause();
    }
    check(); return gif.finish();
  }
  function create(adapter) {
    function $(id) { return document.getElementById(id); }
    var STYLE_KEY = 'layer0.barrierExplorer.appearance.v1', busy = false, cancelled = false;
    var style = appearance(null), dialog = $('barrierExportDialog');
    try { style = appearance(JSON.parse(localStorage.getItem(STYLE_KEY))); } catch (e) { /* defaults */ }
    function setStyle(value) {
      style = appearance(value); adapter.setStyle(style);
      $('barrierTextSize').value = Math.round(style.text * 100); $('barrierTextOut').textContent = Math.round(style.text * 100) + '%';
      $('barrierLineSize').value = Math.round(style.line * 100); $('barrierLineOut').textContent = Math.round(style.line * 100) + '%';
      $('barrierTransparency').value = Math.round(style.transparency * 100); $('barrierTransparencyOut').textContent = Math.round(style.transparency * 100) + '%';
      try { localStorage.setItem(STYLE_KEY, JSON.stringify(style)); } catch (e) { /* session only */ }
    }
    $('barrierTextSize').addEventListener('input', function () { setStyle({text: +this.value / 100, line: style.line, transparency: style.transparency}); });
    $('barrierLineSize').addEventListener('input', function () { setStyle({text: style.text, line: +this.value / 100, transparency: style.transparency}); });
    $('barrierTransparency').addEventListener('input', function () { setStyle({text: style.text, line: style.line, transparency: +this.value / 100}); });
    $('barrierStyleReset').addEventListener('click', function () { setStyle({text: 1, line: 1}); });
    function status(text) { $('barrierExportStatus').textContent = text; }
    function cancel() { cancelled = true; $('barrierExportProgress').textContent = 'Cancelling…'; }
    $('barrierExportCancel').addEventListener('click', cancel);
    dialog.addEventListener('cancel', function (e) { e.preventDefault(); cancel(); });
    dialog.addEventListener('keydown', function (e) { e.stopPropagation(); });
    function download(blob, ext, tau) {
      if (!blob) throw new Error('The browser could not create the image.');
      var a = document.createElement('a'), url = URL.createObjectURL(blob);
      a.href = url; a.download = 'layer0_' + adapter.family() + '_tau' + tau.toFixed(2) + '_' + Date.now() + '.' + ext;
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    }
    async function run(kind) {
      if (busy) return;
      var selected = Array.from(document.querySelectorAll('[data-barrier-panel]:checked'));
      if (!selected.length) { status('Select at least one panel to export.'); return; }
      var frames, maxTau = adapter.tau(), restore = null;
      try {
        if (kind === 'gif') {
          for (var id of ['barrierMaxTau','barrierGifSeconds']) if (!$(id).reportValidity()) return;
          maxTau = +$('barrierMaxTau').value;
          frames = timeline(maxTau, +$('barrierGifFrames').value, +$('barrierGifSeconds').value, adapter.horizon);
        }
        busy = true; cancelled = false; window.BarrierExportBusy = true;
        $('barrierExportTitle').textContent = kind === 'gif' ? 'Rendering surface growth' : 'Rendering PNG';
        $('barrierExportProgress').textContent = 'Preparing panels…'; $('barrierExportMeter').value = 0;
        restore = adapter.begin(maxTau); dialog.showModal();
        await new Promise(function (resolve) { setTimeout(resolve, 0); });
        var width = +$('barrierExportWidth').value;
        var panels = selected.map(function (box) {
          var id = box.getAttribute('data-barrier-panel'), cv = $(id), size = adapter.size(id);
          return {id:id,cv:cv,w:size.w,h:size.h,title:PANELS[id]};
        });
        var canvas = document.createElement('canvas'), ctx = canvas.getContext('2d', {willReadFrequently:kind === 'gif'});
        function caption(tau) { return adapter.label() + ' · τ = ' + tau.toFixed(2) + (kind === 'gif' ? ' / ' + maxTau.toFixed(2) : ''); }
        var L = layout(panels, width, style.text, ctx, caption(maxTau)); canvas.width = L.width; canvas.height = L.height;
        if (adapter.resolution) adapter.resolution(L.factor, panels.map(function (panel) { return panel.id; }));
        function render(tau) { adapter.render(tau); composite(ctx, L, caption(tau)); }
        if (kind === 'png') {
          render(maxTau);
          var png = await new Promise(function (resolve) { canvas.toBlob(resolve, 'image/png'); });
          if (!cancelled) { download(png, 'png', maxTau); status('Saved PNG · ' + L.width + ' × ' + L.height + ' px.'); }
          else status('Export cancelled. Your view has been restored.');
        } else {
          var blob = await encode({encoder:window.ExplorerGif,width:L.width,height:L.height,frames:frames,
            cancelled:function () {return cancelled;}, render:function (index) {render(frames[index].tau);return ctx.getImageData(0,0,L.width,L.height).data;},
            progress:function (done,total) {$('barrierExportProgress').textContent='Frame '+done+' of '+total; $('barrierExportMeter').value=100*done/total;}});
          download(blob, 'gif', maxTau);
          status('Saved GIF · τ 0–' + maxTau.toFixed(2) + ' · ' + L.width + ' × ' + L.height + ' px · ' + (blob.size / 1048576).toFixed(1) + ' MB.');
        }
      } catch (e) { status(e.name === 'AbortError' ? 'Export cancelled. Your view has been restored.' : 'Export failed: ' + e.message); }
      finally {
        try { if (restore) restore(); }
        finally { busy = false; window.BarrierExportBusy = false; if (dialog.open) dialog.close(); }
      }
    }
    $('barrierPng').addEventListener('click', function () { return run('png'); });
    $('barrierGif').addEventListener('click', function () { return run('gif'); });
    setStyle(style);
    return { png: function () { return run('png'); } };
  }
  return { create: create, appearance: appearance, font: font, timeline: timeline, layout: layout, composite: composite, encode: encode };
}));
