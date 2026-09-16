/* render.js — canvas drawing: axes, beta lines, T1/T2/T1∩T2 shading,
 * trajectory trail, outcome label, and the R(t) time-series readout.
 *
 * Pure drawing + geometry. No simulation state lives here; index.html owns the
 * run loop and passes in what to draw. Angles arrive in RADIANS (spec §1);
 * only the axis tick labels are in degrees.
 */
;(function (root, factory) {
  'use strict';
  var R = factory(root.Sim);
  if (typeof module === 'object' && module.exports) module.exports = R;
  else root.Render = R;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Sim) {
  'use strict';

  var PI = Math.PI, TWO_PI = 2 * PI;

  var C = {
    bg: '#0d1117',
    panel: '#11161d',
    grid: '#1e2630',
    gridMajor: '#2b3542',
    axis: '#3d4a5c',
    text: '#8b98a9',
    textDim: '#5d6875',
    t1Fill: 'rgba(76, 141, 255, 0.20)',
    t1Line: 'rgba(76, 141, 255, 0.60)',
    t2Fill: 'rgba(255, 165, 61, 0.20)',
    t2Line: 'rgba(255, 165, 61, 0.60)',
    bothFill: 'rgba(255, 84, 112, 0.42)',
    bothLine: 'rgba(255, 84, 112, 0.85)',
    beta: 'rgba(255, 255, 255, 0.22)',
    trail: '#5fe3c0',
    trailGhost: 'rgba(95, 227, 192, 0.16)',
    head: '#ffffff',
    start: '#e6edf3',
    hover: 'rgba(230, 237, 243, 0.35)',
    rcurve: '#5fe3c0',
    // plan view
    ac1: '#4c8dff',
    ac2: '#ffa53d',
    ac1Env: 'rgba(76, 141, 255, 0.06)',
    ac2Env: 'rgba(255, 165, 61, 0.06)',
    ac1EnvHot: 'rgba(76, 141, 255, 0.17)',
    ac2EnvHot: 'rgba(255, 165, 61, 0.17)',
    los: 'rgba(230, 237, 243, 0.30)',
    ground: '#171d26',
    kill: '#ff5470'
  };

  var MARGIN = { l: 52, r: 14, t: 14, b: 38 };

  // --- canvas plumbing ------------------------------------------------------

  // Size the backing store to the device pixel ratio and return a context whose
  // user units are CSS px.
  function prepare(canvas) {
    var dpr = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    var w = Math.max(1, Math.round(rect.width));
    var h = Math.max(1, Math.round(rect.height));
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    }
    var ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    return { ctx: ctx, w: w, h: h };
  }

  // Plot-area geometry in CSS px, plus the angle<->pixel maps.
  // phi1 runs left->right, phi2 runs bottom->top, both over [-180deg, 180deg].
  function geom(canvas) {
    var rect = canvas.getBoundingClientRect();
    var w = Math.max(1, Math.round(rect.width));
    var h = Math.max(1, Math.round(rect.height));
    var g = {
      x0: MARGIN.l,
      y0: MARGIN.t,
      w: Math.max(1, w - MARGIN.l - MARGIN.r),
      h: Math.max(1, h - MARGIN.t - MARGIN.b)
    };
    g.x1 = g.x0 + g.w;
    g.y1 = g.y0 + g.h;
    g.mapX = function (phi1) { return g.x0 + ((phi1 + PI) / TWO_PI) * g.w; };
    g.mapY = function (phi2) { return g.y1 - ((phi2 + PI) / TWO_PI) * g.h; };
    g.invX = function (px) { return ((px - g.x0) / g.w) * TWO_PI - PI; };
    g.invY = function (py) { return ((g.y1 - py) / g.h) * TWO_PI - PI; };
    g.contains = function (px, py) {
      return px >= g.x0 && px <= g.x1 && py >= g.y0 && py <= g.y1;
    };
    return g;
  }

  // --- interval helpers for the analytic target-set shading -----------------

  function clip(iv, lo, hi) {
    var out = [];
    for (var i = 0; i < iv.length; i++) {
      var a = Math.max(iv[i][0], lo), b = Math.min(iv[i][1], hi);
      if (b > a) out.push([a, b]);
    }
    return out;
  }

  // The T1/T2 projections at a fixed R are products of intervals (spec §3), so
  // they shade exactly as rectangles — no per-pixel masking needed.
  //   T1 = { |phi1| <= beta } x { phi2 in band(R) }
  //   T2 = { phi1 in band(R) } x { |phi2| <= beta }
  function regions(R0, params) {
    var p = params || Sim.PARAMS;
    var band = Sim.opponentBand(R0, p);
    var own = [[-p.beta, p.beta]];
    return {
      band: band,
      own: own,
      t1: { x: own, y: band },
      t2: { x: band, y: own },
      both: { x: clip(band, -p.beta, p.beta), y: clip(band, -p.beta, p.beta) }
    };
  }

  function fillProduct(ctx, g, reg, fill, stroke) {
    for (var i = 0; i < reg.x.length; i++) {
      for (var j = 0; j < reg.y.length; j++) {
        var xa = g.mapX(reg.x[i][0]), xb = g.mapX(reg.x[i][1]);
        var yb = g.mapY(reg.y[j][0]), ya = g.mapY(reg.y[j][1]);
        ctx.fillStyle = fill;
        ctx.fillRect(xa, ya, xb - xa, yb - ya);
        if (stroke) {
          ctx.strokeStyle = stroke;
          ctx.lineWidth = 1;
          ctx.strokeRect(xa + 0.5, ya + 0.5, xb - xa - 1, yb - ya - 1);
        }
      }
    }
  }

  // --- main phase plot ------------------------------------------------------

  function drawPlot(canvas, o) {
    o = o || {};
    var p = o.params || Sim.PARAMS;
    var s = prepare(canvas), ctx = s.ctx, g = geom(canvas);

    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, s.w, s.h);
    ctx.fillStyle = C.panel;
    ctx.fillRect(g.x0, g.y0, g.w, g.h);

    // shaded target-set projections at the current R0
    var reg = regions(o.R0, p);
    fillProduct(ctx, g, reg.t1, C.t1Fill, C.t1Line);
    fillProduct(ctx, g, reg.t2, C.t2Fill, C.t2Line);
    fillProduct(ctx, g, reg.both, C.bothFill, C.bothLine);

    drawGrid(ctx, g);
    drawBetaLines(ctx, g, p.beta);

    // completed runs, faded
    var ghosts = o.ghosts || [];
    for (var i = 0; i < ghosts.length; i++) drawTrail(ctx, g, ghosts[i], C.trailGhost, 1.2);

    if (o.path && o.path.length) {
      drawTrail(ctx, g, o.path, C.trail, 1.8);
      drawStart(ctx, g, o.path[0]);
      drawHead(ctx, g, o.path[o.path.length - 1], o.outcome);
      if (o.outcome) drawOutcomeLabel(ctx, g, o.path[o.path.length - 1], o.outcome);
    } else if (o.start) {
      drawStart(ctx, g, o.start);
    }

    if (o.hover && g.contains(o.hover.px, o.hover.py)) drawHover(ctx, g, o.hover);
    drawAxes(ctx, g);
  }

  function drawGrid(ctx, g) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(g.x0, g.y0, g.w, g.h);
    ctx.clip();
    for (var d = -180; d <= 180; d += 45) {
      var phi = (d * PI) / 180;
      var major = (d % 90 === 0);
      ctx.strokeStyle = major ? C.gridMajor : C.grid;
      ctx.lineWidth = 1;
      var x = Math.round(g.mapX(phi)) + 0.5, y = Math.round(g.mapY(phi)) + 0.5;
      ctx.beginPath(); ctx.moveTo(x, g.y0); ctx.lineTo(x, g.y1); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(g.x0, y); ctx.lineTo(g.x1, y); ctx.stroke();
    }
    ctx.restore();
  }

  function drawBetaLines(ctx, g, beta) {
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = C.beta;
    ctx.lineWidth = 1;
    var vals = [-beta, beta];
    for (var i = 0; i < 2; i++) {
      var x = Math.round(g.mapX(vals[i])) + 0.5, y = Math.round(g.mapY(vals[i])) + 0.5;
      ctx.beginPath(); ctx.moveTo(x, g.y0); ctx.lineTo(x, g.y1); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(g.x0, y); ctx.lineTo(g.x1, y); ctx.stroke();
    }
    ctx.restore();
  }

  function drawAxes(ctx, g) {
    ctx.save();
    ctx.strokeStyle = C.axis;
    ctx.lineWidth = 1;
    ctx.strokeRect(g.x0 + 0.5, g.y0 + 0.5, g.w - 1, g.h - 1);

    ctx.fillStyle = C.text;
    ctx.font = '11px ui-monospace, SFMono-Regular, Consolas, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (var d = -180; d <= 180; d += 90) {
      var phi = (d * PI) / 180;
      ctx.fillText(d + '°', g.mapX(phi), g.y1 + 6);
    }
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (var e = -180; e <= 180; e += 90) {
      var phe = (e * PI) / 180;
      ctx.fillText(e + '°', g.x0 - 8, g.mapY(phe));
    }

    ctx.fillStyle = C.textDim;
    ctx.font = '11px system-ui, -apple-system, Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('φ₁  (player 1 off-boresight angle)', g.x0 + g.w / 2, g.y1 + 34);
    ctx.save();
    ctx.translate(12, g.y0 + g.h / 2);
    ctx.rotate(-PI / 2);
    ctx.textBaseline = 'top';
    ctx.fillText('φ₂  (player 2 off-boresight angle)', 0, 0);
    ctx.restore();
    ctx.restore();
  }

  // Trail segments are broken wherever an angle wrapped across +/-pi, so the
  // path does not draw a false line straight across the plot.
  function drawTrail(ctx, g, path, color, width) {
    if (!path || path.length < 2) return;
    ctx.save();
    ctx.beginPath();
    ctx.rect(g.x0, g.y0, g.w, g.h);
    ctx.clip();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(g.mapX(path[0].phi1), g.mapY(path[0].phi2));
    for (var i = 1; i < path.length; i++) {
      var a = path[i - 1], b = path[i];
      if (Math.abs(b.phi1 - a.phi1) > PI || Math.abs(b.phi2 - a.phi2) > PI) {
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(g.mapX(b.phi1), g.mapY(b.phi2));
      } else {
        ctx.lineTo(g.mapX(b.phi1), g.mapY(b.phi2));
      }
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawStart(ctx, g, pt) {
    var x = g.mapX(pt.phi1), y = g.mapY(pt.phi2);
    ctx.save();
    ctx.strokeStyle = C.start;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(x, y, 4.5, 0, TWO_PI);
    ctx.stroke();
    ctx.restore();
  }

  function drawHead(ctx, g, pt, outcome) {
    var x = g.mapX(pt.phi1), y = g.mapY(pt.phi2);
    ctx.save();
    if (outcome === 'mutual' || outcome === 'p1' || outcome === 'p2') {
      ctx.strokeStyle = outcome === 'mutual' ? C.bothLine : C.head;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x - 5, y - 5); ctx.lineTo(x + 5, y + 5);
      ctx.moveTo(x + 5, y - 5); ctx.lineTo(x - 5, y + 5);
      ctx.stroke();
    } else {
      ctx.fillStyle = C.head;
      ctx.beginPath();
      ctx.arc(x, y, 3.5, 0, TWO_PI);
      ctx.fill();
    }
    ctx.restore();
  }

  var SHORT = {
    terminal0: 'terminal at t=0',
    p1: 'Player 1 wins',
    p2: 'Player 2 wins',
    mutual: 'Mutual kill',
    draw: 'Draw',
    numerical: 'R→0'
  };

  function drawOutcomeLabel(ctx, g, pt, outcome) {
    var label = SHORT[outcome];
    if (!label) return;
    ctx.save();
    ctx.font = '11px ui-monospace, SFMono-Regular, Consolas, monospace';
    var w = ctx.measureText(label).width + 10;
    var x = g.mapX(pt.phi1) + 9, y = g.mapY(pt.phi2) - 9;
    if (x + w > g.x1) x = g.mapX(pt.phi1) - 9 - w;
    if (y - 16 < g.y0) y = g.mapY(pt.phi2) + 24;
    ctx.fillStyle = 'rgba(13, 17, 23, 0.85)';
    ctx.fillRect(x, y - 13, w, 17);
    ctx.strokeStyle = outcome === 'mutual' ? C.bothLine : C.axis;
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, y - 12.5, w - 1, 16);
    ctx.fillStyle = '#e6edf3';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText(label, x + 5, y);
    ctx.restore();
  }

  function drawHover(ctx, g, hov) {
    ctx.save();
    ctx.strokeStyle = C.hover;
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 3]);
    ctx.beginPath();
    ctx.moveTo(hov.px, g.y0); ctx.lineTo(hov.px, g.y1);
    ctx.moveTo(g.x0, hov.py); ctx.lineTo(g.x1, hov.py);
    ctx.stroke();
    ctx.restore();
  }

  // --- R(t) time series -----------------------------------------------------

  function drawRPlot(canvas, o) {
    o = o || {};
    var p = o.params || Sim.PARAMS;
    var s = prepare(canvas), ctx = s.ctx;
    var m = { l: 34, r: 10, t: 10, b: 20 };
    var x0 = m.l, y0 = m.t, w = Math.max(1, s.w - m.l - m.r), h = Math.max(1, s.h - m.t - m.b);
    var y1 = y0 + h, x1 = x0 + w;

    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, s.w, s.h);
    ctx.fillStyle = C.panel;
    ctx.fillRect(x0, y0, w, h);

    var path = o.path || [];
    var rMax = Math.max(o.R0 || 1, 1);
    for (var i = 0; i < path.length; i++) if (isFinite(path[i].R) && path[i].R > rMax) rMax = path[i].R;
    rMax = Math.ceil(rMax * 1.1);
    var tMax = p.tMax;

    var mx = function (t) { return x0 + (t / tMax) * w; };
    var my = function (R) { return y1 - (Math.max(0, Math.min(R, rMax)) / rMax) * h; };

    ctx.strokeStyle = C.grid;
    ctx.lineWidth = 1;
    ctx.fillStyle = C.textDim;
    ctx.font = '10px ui-monospace, SFMono-Regular, Consolas, monospace';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    var stepR = rMax <= 4 ? 1 : (rMax <= 8 ? 2 : 4);
    for (var r = 0; r <= rMax; r += stepR) {
      var yy = Math.round(my(r)) + 0.5;
      ctx.beginPath(); ctx.moveTo(x0, yy); ctx.lineTo(x1, yy); ctx.stroke();
      ctx.fillText(String(r), x0 - 6, my(r));
    }
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (var t = 0; t <= tMax; t += 10) {
      var xx = Math.round(mx(t)) + 0.5;
      ctx.beginPath(); ctx.moveTo(xx, y0); ctx.lineTo(xx, y1); ctx.stroke();
      ctx.fillText(String(t), mx(t), y1 + 5);
    }

    if (path.length > 1) {
      ctx.save();
      ctx.beginPath(); ctx.rect(x0, y0, w, h); ctx.clip();
      ctx.strokeStyle = C.rcurve;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      var started = false;
      for (var k = 0; k < path.length; k++) {
        if (!isFinite(path[k].R)) break;
        var X = mx(path[k].t), Y = my(path[k].R);
        if (!started) { ctx.moveTo(X, Y); started = true; } else ctx.lineTo(X, Y);
      }
      ctx.stroke();
      var last = path[path.length - 1];
      if (isFinite(last.R)) {
        ctx.fillStyle = C.head;
        ctx.beginPath();
        ctx.arc(mx(last.t), my(last.R), 2.5, 0, TWO_PI);
        ctx.fill();
      }
      ctx.restore();
    }

    ctx.strokeStyle = C.axis;
    ctx.strokeRect(x0 + 0.5, y0 + 0.5, w - 1, h - 1);
    ctx.fillStyle = C.textDim;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('R', x0 + 4, y0 + 3);
    ctx.textAlign = 'right';
    ctx.fillText('t', x1 - 4, y1 + 5);
  }

  // --- plan view (ground coordinates) --------------------------------------
  //
  // Draws the same run in x-y, so a viewer who has not internalized the
  // (R, phi1, phi2) reduction can simply see two aircraft flying. Angles are in
  // radians; 1 world unit = one turn radius (rho = 2200 m).

  var MIN_EXTENT = 3;      // world units; keeps a 2-step run from filling the frame
  var CAM_PAD = 1.15;
  var ENV_ZOOM_CAP = 4;    // how far the envelopes may pull the camera back

  // One camera for the whole precomputed run, so the frame never drifts during
  // playback.
  //
  // Framing has to reconcile two very different scales. At short range the
  // aircraft may be 1.7 units apart while their no-escape envelopes reach out
  // nearly 5 -- fit only the aircraft and the wedges flood the panel; fit the
  // wedges outright and the engagement shrinks to nothing. So: centre on the
  // aircraft, and let the envelopes pull the view back only up to
  // ENV_ZOOM_CAP times the extent of the flight paths themselves.
  function fitCamera(path, params) {
    var p = params || Sim.PARAMS;
    if (!path || !path.length || path[0].x1 === undefined) {
      return { cx: 0, cy: 0, ext: MIN_EXTENT };
    }
    var minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
    var eminx = Infinity, emaxx = -Infinity, eminy = Infinity, emaxy = -Infinity;

    function addEnv(x, y, th, rmax) {
      if (!isFinite(rmax) || rmax <= 0) return;
      for (var q = 0; q <= 6; q++) {
        var a = th - p.beta + (2 * p.beta) * (q / 6);
        var ex = x + rmax * Math.cos(a), ey = y + rmax * Math.sin(a);
        eminx = Math.min(eminx, ex); emaxx = Math.max(emaxx, ex);
        eminy = Math.min(eminy, ey); emaxy = Math.max(emaxy, ey);
      }
    }

    for (var i = 0; i < path.length; i++) {
      var r = path[i];
      if (!isFinite(r.x1) || !isFinite(r.x2) || !isFinite(r.y1) || !isFinite(r.y2)) continue;
      minx = Math.min(minx, r.x1, r.x2); maxx = Math.max(maxx, r.x1, r.x2);
      miny = Math.min(miny, r.y1, r.y2); maxy = Math.max(maxy, r.y1, r.y2);
      // Each aircraft's envelope radius comes from the OPPONENT's aspect angle.
      addEnv(r.x1, r.y1, r.th1, Sim.RmaxOf(r.phi2, p));
      addEnv(r.x2, r.y2, r.th2, Sim.RmaxOf(r.phi1, p));
    }
    if (!isFinite(minx)) return { cx: 0, cy: 0, ext: MIN_EXTENT };

    var cx = 0.5 * (minx + maxx), cy = 0.5 * (miny + maxy);
    var pathExt = Math.max(maxx - minx, maxy - miny);

    // Envelope extent measured about the same centre, so the engagement stays
    // in the middle of the frame.
    var envExt = 0;
    if (isFinite(eminx)) {
      envExt = 2 * Math.max(
        Math.abs(emaxx - cx), Math.abs(cx - eminx),
        Math.abs(emaxy - cy), Math.abs(cy - eminy));
    }

    var ext = Math.max(
      pathExt * CAM_PAD,
      Math.min(envExt * CAM_PAD, pathExt * ENV_ZOOM_CAP),
      MIN_EXTENT);
    return { cx: cx, cy: cy, ext: ext };
  }

  function planGeom(canvas, cam) {
    var rect = canvas.getBoundingClientRect();
    var w = Math.max(1, Math.round(rect.width)), h = Math.max(1, Math.round(rect.height));
    var M = 10;
    var size = Math.max(1, Math.min(w, h) - 2 * M);
    var ox = (w - size) / 2, oy = (h - size) / 2;
    var k = size / cam.ext;
    return {
      w: w, h: h, size: size, k: k,
      x0: ox, y0: oy, x1: ox + size, y1: oy + size,
      X: function (x) { return ox + size / 2 + (x - cam.cx) * k; },
      Y: function (y) { return oy + size / 2 - (y - cam.cy) * k; },
      invX: function (px) { return cam.cx + (px - ox - size / 2) / k; },
      invY: function (py) { return cam.cy - (py - oy - size / 2) / k; },
      contains: function (px, py) {
        return px >= ox && px <= ox + size && py >= oy && py <= oy + size;
      }
    };
  }

  // Screen point at world angle `a`, `rpx` pixels from a screen origin. World y
  // is up and screen y is down, hence the negated sine.
  function polar(px, py, rpx, a) {
    return [px + rpx * Math.cos(a), py - rpx * Math.sin(a)];
  }

  function arcPath(ctx, px, py, rpx, a0, a1, move) {
    var n = Math.max(6, Math.ceil(Math.abs(a1 - a0) / 0.12));
    for (var i = 0; i <= n; i++) {
      var p = polar(px, py, rpx, a0 + (a1 - a0) * (i / n));
      if (i === 0 && move) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
    }
  }

  // Annulus sector: a shooter's live firing envelope. Its radii come from the
  // OPPONENT's aspect angle (Eqs. 8-9), which is why it visibly breathes as the
  // opponent maneuvers -- the paper's counterintuitive result, made literal.
  function envelopeSector(ctx, g, x, y, th, beta, rmin, rmax) {
    var px = g.X(x), py = g.Y(y);
    ctx.beginPath();
    arcPath(ctx, px, py, rmax * g.k, th - beta, th + beta, true);
    arcPath(ctx, px, py, rmin * g.k, th + beta, th - beta, false);
    ctx.closePath();
  }

  function drawAircraft(ctx, g, x, y, th, color, label) {
    var px = g.X(x), py = g.Y(y), L = 11;
    var nose = polar(px, py, L, th);
    var bl = polar(px, py, L * 0.85, th + 2.55);
    var br = polar(px, py, L * 0.85, th - 2.55);
    var tail = polar(px, py, L * 0.28, th + PI);
    ctx.beginPath();
    ctx.moveTo(nose[0], nose[1]);
    ctx.lineTo(bl[0], bl[1]);
    ctx.lineTo(tail[0], tail[1]);
    ctx.lineTo(br[0], br[1]);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = 'rgba(13,17,23,0.9)';
    ctx.lineWidth = 1;
    ctx.stroke();
    if (label) {
      ctx.fillStyle = color;
      ctx.font = '10px ui-monospace, SFMono-Regular, Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(label, px, py - 15);
    }
  }

  // Drag affordances: a ring on the body (move) and a stalk with a knob along
  // the nose (rotate). Both are sized in pixels so they stay grabbable at any
  // zoom; HANDLE_PX is exported so the hit-testing in index.html agrees.
  var HANDLE_PX = { body: 15, stalk: 36, knob: 5.5 };

  function drawHandles(ctx, g, x, y, th, color) {
    var px = g.X(x), py = g.Y(y);
    var tip = polar(px, py, HANDLE_PX.stalk, th);
    ctx.save();
    ctx.strokeStyle = color;
    ctx.globalAlpha = 0.55;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.arc(px, py, HANDLE_PX.body, 0, TWO_PI);
    ctx.stroke();
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(tip[0], tip[1]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(tip[0], tip[1], HANDLE_PX.knob, 0, TWO_PI);
    ctx.fill();
    ctx.strokeStyle = 'rgba(13,17,23,0.9)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();
  }

  function planTrail(ctx, g, path, upto, kx, ky, color) {
    if (upto < 1) return;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.6;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(g.X(path[0][kx]), g.Y(path[0][ky]));
    for (var i = 1; i <= upto; i++) ctx.lineTo(g.X(path[i][kx]), g.Y(path[i][ky]));
    ctx.stroke();
  }

  function fmtDeg(rad) {
    var d = (rad * 180 / PI).toFixed(0);
    return (d.charAt(0) === '-' ? '−' + d.slice(1) : d) + '°';
  }

  function drawAngleArc(ctx, px, py, from, to, color, label) {
    var d = Sim.wrap(to - from);
    if (Math.abs(d) < 0.03) return;
    var r = 30;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.globalAlpha = 0.75;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    arcPath(ctx, px, py, r, from, from + d, true);
    ctx.stroke();
    var mid = polar(px, py, r + 15, from + d / 2);
    ctx.globalAlpha = 1;
    ctx.fillStyle = color;
    ctx.font = '10px ui-monospace, SFMono-Regular, Consolas, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, mid[0], mid[1]);
    ctx.restore();
  }

  // 1 normalized unit = the turn radius rho = 2200 m (Section 4 of the paper),
  // so the scale bar can carry a physical length as well.
  function drawScaleBar(ctx, g) {
    var unit = 1, len = g.k;
    while (len < 42) { unit *= 2; len = unit * g.k; }
    var bx = g.x0 + 12, by = g.y1 - 14;
    ctx.strokeStyle = C.text;
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(bx, by); ctx.lineTo(bx + len, by);
    ctx.moveTo(bx, by - 4); ctx.lineTo(bx, by + 4);
    ctx.moveTo(bx + len, by - 4); ctx.lineTo(bx + len, by + 4);
    ctx.stroke();
    ctx.fillStyle = C.text;
    ctx.font = '10px ui-monospace, SFMono-Regular, Consolas, monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText(unit + ' ρ = ' + (unit * 2.2).toFixed(1) + ' km', bx, by - 6);
  }

  function drawPlanView(canvas, o) {
    o = o || {};
    var p = o.params || Sim.PARAMS;
    var path = o.path || [];
    var s = prepare(canvas), ctx = s.ctx;

    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, s.w, s.h);

    if (!path.length || path[0].x1 === undefined) {
      ctx.fillStyle = C.textDim;
      ctx.font = '12px system-ui, -apple-system, Segoe UI, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('Click the phase plot to fly an engagement', s.w / 2, s.h / 2);
      return;
    }

    var cam = o.camera || fitCamera(path);
    var g = planGeom(canvas, cam);
    var cursor = Math.max(0, Math.min(o.cursor == null ? path.length - 1 : o.cursor, path.length - 1));
    var rec = path[cursor];

    ctx.save();
    ctx.beginPath();
    ctx.rect(g.x0, g.y0, g.size, g.size);
    ctx.clip();
    ctx.fillStyle = C.ground;
    ctx.fillRect(g.x0, g.y0, g.size, g.size);

    // 1-unit ground grid
    ctx.strokeStyle = C.grid;
    ctx.lineWidth = 1;
    var lo = Math.floor(cam.cx - cam.ext / 2), hi = Math.ceil(cam.cx + cam.ext / 2);
    for (var gx = lo; gx <= hi; gx++) {
      var sx = Math.round(g.X(gx)) + 0.5;
      ctx.beginPath(); ctx.moveTo(sx, g.y0); ctx.lineTo(sx, g.y1); ctx.stroke();
    }
    var lo2 = Math.floor(cam.cy - cam.ext / 2), hi2 = Math.ceil(cam.cy + cam.ext / 2);
    for (var gy = lo2; gy <= hi2; gy++) {
      var sy = Math.round(g.Y(gy)) + 0.5;
      ctx.beginPath(); ctx.moveTo(g.x0, sy); ctx.lineTo(g.x1, sy); ctx.stroke();
    }

    var st = { R: rec.R, phi1: rec.phi1, phi2: rec.phi2 };
    var hot1 = Sim.inT1(st, p), hot2 = Sim.inT2(st, p);

    // firing envelopes (Eqs. 7-9): radii set by the OPPONENT's aspect angle
    envelopeSector(ctx, g, rec.x1, rec.y1, rec.th1, p.beta,
      Sim.RminOf(rec.phi2, p), Sim.RmaxOf(rec.phi2, p));
    ctx.fillStyle = hot1 ? C.ac1EnvHot : C.ac1Env;
    ctx.fill();
    ctx.strokeStyle = hot1 ? C.ac1 : 'rgba(76,141,255,0.34)';
    ctx.lineWidth = hot1 ? 2.2 : 1;
    ctx.stroke();

    envelopeSector(ctx, g, rec.x2, rec.y2, rec.th2, p.beta,
      Sim.RminOf(rec.phi1, p), Sim.RmaxOf(rec.phi1, p));
    ctx.fillStyle = hot2 ? C.ac2EnvHot : C.ac2Env;
    ctx.fill();
    ctx.strokeStyle = hot2 ? C.ac2 : 'rgba(255,165,61,0.34)';
    ctx.lineWidth = hot2 ? 2.2 : 1;
    ctx.stroke();

    planTrail(ctx, g, path, cursor, 'x1', 'y1', C.ac1);
    planTrail(ctx, g, path, cursor, 'x2', 'y2', C.ac2);

    // line of sight
    var p1x = g.X(rec.x1), p1y = g.Y(rec.y1), p2x = g.X(rec.x2), p2y = g.Y(rec.y2);
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = C.los;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(p1x, p1y); ctx.lineTo(p2x, p2y); ctx.stroke();
    ctx.restore();

    // phi arcs, each measured from that aircraft's nose to the line of sight
    var psi = Math.atan2(rec.y2 - rec.y1, rec.x2 - rec.x1);
    drawAngleArc(ctx, p1x, p1y, rec.th1, psi, C.ac1, 'φ₁ ' + fmtDeg(rec.phi1));
    drawAngleArc(ctx, p2x, p2y, rec.th2, psi + PI, C.ac2, 'φ₂ ' + fmtDeg(rec.phi2));

    if (o.editable) {
      drawHandles(ctx, g, rec.x1, rec.y1, rec.th1, C.ac1);
      drawHandles(ctx, g, rec.x2, rec.y2, rec.th2, C.ac2);
    }

    drawAircraft(ctx, g, rec.x1, rec.y1, rec.th1, C.ac1, '1');
    drawAircraft(ctx, g, rec.x2, rec.y2, rec.th2, C.ac2, '2');

    // kill marker, only once playback has actually reached the end
    var atEnd = cursor === path.length - 1;
    if (atEnd && (o.outcome === 'p1' || o.outcome === 'p2' || o.outcome === 'mutual')) {
      ctx.strokeStyle = C.kill;
      ctx.lineWidth = 1.8;
      ctx.setLineDash([2, 3]);
      ctx.beginPath(); ctx.moveTo(p1x, p1y); ctx.lineTo(p2x, p2y); ctx.stroke();
      ctx.setLineDash([]);
      var victims = o.outcome === 'mutual' ? [[p1x, p1y], [p2x, p2y]]
                  : o.outcome === 'p1' ? [[p2x, p2y]] : [[p1x, p1y]];
      for (var v = 0; v < victims.length; v++) {
        var vx = victims[v][0], vy = victims[v][1];
        ctx.beginPath();
        ctx.moveTo(vx - 8, vy - 8); ctx.lineTo(vx + 8, vy + 8);
        ctx.moveTo(vx + 8, vy - 8); ctx.lineTo(vx - 8, vy + 8);
        ctx.stroke();
      }
    }
    ctx.restore();

    drawScaleBar(ctx, g);

    // corner HUD, clear of the aircraft and their angle arcs
    ctx.fillStyle = C.text;
    ctx.font = '12px ui-monospace, SFMono-Regular, Consolas, monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('t = ' + (rec.t || 0).toFixed(2) + '    R = ' + rec.R.toFixed(2), g.x0 + 11, g.y0 + 9);

    ctx.strokeStyle = C.axis;
    ctx.lineWidth = 1;
    ctx.strokeRect(g.x0 + 0.5, g.y0 + 0.5, g.size - 1, g.size - 1);
  }

  return {
    COLORS: C,
    prepare: prepare,
    geom: geom,
    regions: regions,
    fitCamera: fitCamera,
    planGeom: planGeom,
    HANDLE_PX: HANDLE_PX,
    drawPlanView: drawPlanView,
    drawPlot: drawPlot,
    drawRPlot: drawRPlot
  };
});
