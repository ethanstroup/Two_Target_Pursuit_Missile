/* Shared local GIF encoder, extracted unchanged from the coordinate export. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ExplorerGif = factory();
}(typeof window !== 'undefined' ? window : globalThis, function () {
'use strict';
function gifHistogram(data, H) {
  for (var i = 0; i < data.length; i += 4) {
    var key = ((data[i] >> 3) << 10) | ((data[i + 1] >> 3) << 5) | (data[i + 2] >> 3);
    H.n[key]++; H.r[key] += data[i]; H.g[key] += data[i + 1]; H.b[key] += data[i + 2];
  }
}
function gifPalette(H) {
  var bins = [], i, k, out = [];
  for (k = 0; k < 32768; k++) if (H.n[k]) bins.push({ n: H.n[k], r: H.r[k] / H.n[k], g: H.g[k] / H.n[k], b: H.b[k] / H.n[k] });
  bins.sort(function (a, b) { return b.n - a.n; });
  [40, 24, 12, 0].forEach(function (d) {
    var d2 = d * d;
    for (i = 0; i < bins.length && out.length < 255; i++) {
      var c = bins[i]; if (c.used) continue;
      var ok = out.every(function (o) { var dr = o[0] - c.r, dg = o[1] - c.g, db = o[2] - c.b; return dr * dr + dg * dg + db * db > d2; });
      if (ok) { c.used = true; out.push([c.r, c.g, c.b]); }
    }
  });
  var pal = new Uint8Array(768);
  out.forEach(function (c, j) { pal[3 * j] = Math.round(c[0]); pal[3 * j + 1] = Math.round(c[1]); pal[3 * j + 2] = Math.round(c[2]); });
  return { bytes: pal, n: out.length };
}
function gifQuantize(data, P, map, out) {
  for (var i = 0, j = 0; i < data.length; i += 4, j++) {
    var key = ((data[i] >> 3) << 10) | ((data[i + 1] >> 3) << 5) | (data[i + 2] >> 3), m = map[key];
    if (m < 0) {
      var r = (key >> 10) * 8 + 4, g = ((key >> 5) & 31) * 8 + 4, b = (key & 31) * 8 + 4, best = 1e9;
      for (var q = 0; q < P.n; q++) {
        var dr = P.bytes[3 * q] - r, dg = P.bytes[3 * q + 1] - g, db = P.bytes[3 * q + 2] - b, e = dr * dr + dg * dg + db * db;
        if (e < best) { best = e; m = q; }
      }
      map[key] = m;
    }
    out[j] = m;
  }
}

/* LZW for GIF image data (the same scheme as omggif's encoder).  The code table is a
   flat Int32Array keyed by (prefix << 8 | k); a generation stamp in the high bits
   makes "clear" free. */
var LZW_TABLE = null, LZW_GEN = 0;
function gifLzw(idx, n, out) {
  if (!LZW_TABLE) LZW_TABLE = new Int32Array(1 << 20);
  var T = LZW_TABLE, min = 8, clear = 256, eoi = 257, next = 258, size = 9, p = 0, cur = 0, shift = 0, gen = ++LZW_GEN;
  function emit(c) { cur |= c << shift; shift += size; while (shift >= 8) { out[p++] = cur & 255; cur >>>= 8; shift -= 8; } }
  emit(clear);
  var ib = idx[0];
  for (var i = 1; i < n; i++) {
    var k = idx[i], key = (ib << 8) | k, e = T[key];
    if ((e >>> 12) === gen) { ib = e & 4095; continue; }
    emit(ib);
    if (next === 4096) { emit(clear); next = eoi + 1; size = min + 1; gen = ++LZW_GEN; }
    else { if (next >= (1 << size)) size++; T[key] = (gen << 12) | next; next++; }
    ib = k;
  }
  emit(ib); emit(eoi);
  if (shift > 0) out[p++] = cur & 255;
  return p;
}
function GifWriter(w, h, palette, delayCs) {
  this.parts = []; this.w = w; this.h = h; this.delay = delayCs;
  var head = [71, 73, 70, 56, 57, 97, w & 255, w >> 8, h & 255, h >> 8, 0xF7, 0, 0];
  this.parts.push(new Uint8Array(head), palette);
  this.parts.push(new Uint8Array([0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1, 0, 0, 0]));  // loop forever
}
GifWriter.prototype.frame = function (x, y, w, h, idx, transparent) {
  var d = this.delay;
  this.parts.push(new Uint8Array([0x21, 0xF9, 4, (1 << 2) | (transparent ? 1 : 0), d & 255, d >> 8, 255, 0,
                                  0x2C, x & 255, x >> 8, y & 255, y >> 8, w & 255, w >> 8, h & 255, h >> 8, 0, 8]));
  var raw = new Uint8Array(Math.ceil(w * h * 1.6) + 64), n = gifLzw(idx, w * h, raw);
  var blocks = new Uint8Array(n + Math.ceil(n / 255) + 1), q = 0;
  for (var i = 0; i < n; i += 255) {
    var len = Math.min(255, n - i); blocks[q++] = len; blocks.set(raw.subarray(i, i + len), q); q += len;
  }
  blocks[q++] = 0;
  this.parts.push(blocks.subarray(0, q));
};
GifWriter.prototype.finish = function () { this.parts.push(new Uint8Array([0x3B])); return new Blob(this.parts, { type: 'image/gif' }); };

return { histogram: gifHistogram, palette: gifPalette, quantize: gifQuantize, Writer: GifWriter };
}));
