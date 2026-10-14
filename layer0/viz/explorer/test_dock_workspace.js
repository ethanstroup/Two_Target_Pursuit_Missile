/* Controller checks use DOM/event doubles, not a browser renderer. They cover
   reparenting, gesture commits/cancellation, storage, and redraw notifications. */
'use strict';
const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
const M = require('./dock_layout.js');
const script = fs.readFileSync(__dirname + '/dock_workspace.js', 'utf8');

class Events {
  constructor() { this.listeners = {}; }
  addEventListener(type, fn) { (this.listeners[type] ||= new Set()).add(fn); }
  removeEventListener(type, fn) { this.listeners[type]?.delete(fn); }
  fire(type, init = {}) {
    const event = { target: this, button: 0, pointerId: 1, clientX: 0, clientY: 0, preventDefault() { this.defaultPrevented = true; }, ...init };
    for (const fn of [...(this.listeners[type] || [])]) fn.call(this, event);
    return event;
  }
}
class Element extends Events {
  constructor(tag, doc) {
    super(); this.tag = tag; this.doc = doc; this.children = []; this.parentElement = null;
    this.className = ''; this.attributes = {}; this.style = {setProperty(k,v) {this[k]=v;}};
    this.classList = { contains: v => this.className.split(' ').includes(v),
      add: v => { if (!this.classList.contains(v)) this.className += ' ' + v; },
      remove: v => { this.className = this.className.split(' ').filter(x => x !== v).join(' '); },
      toggle: (v,on) => { if (on) this.classList.add(v); else this.classList.remove(v); } };
    this.rect = {left:0,top:0,width:1400,height:900}; this.scrollLeft = 0;
  }
  append(...nodes) { nodes.forEach(node => this.appendChild(node)); }
  appendChild(node) {
    if (node.parentElement) node.parentElement.children = node.parentElement.children.filter(x => x !== node);
    node.parentElement = this; this.children.push(node); return node;
  }
  insertBefore(node, before) { this.appendChild(node); this.children.pop(); this.children.splice(this.children.indexOf(before),0,node); }
  replaceChildren(...nodes) { this.children.forEach(n => n.parentElement = null); this.children = []; this.append(...nodes); }
  setAttribute(k,v) { this.attributes[k] = v; }
  get firstChild() { return this.children[0]; }
  get firstElementChild() { return this.children[0]; }
  matches(selector) { return selector.startsWith('.') ? this.classList.contains(selector.slice(1)) : this.tag === selector; }
  querySelector(selector) {
    for (const child of this.children) { if (child.matches(selector)) return child; const found = child.querySelector(selector); if (found) return found; }
    return null;
  }
  closest(selector) { return this.matches(selector) ? this : this.parentElement?.closest(selector) || null; }
  focus() { this.doc.activeElement = this; }
  setPointerCapture(id) { this.capture = id; }
  hasPointerCapture(id) { return this.capture === id; }
  releasePointerCapture() { this.capture = null; this.fire('lostpointercapture'); }
  getBoundingClientRect() { return {...this.rect,right:this.rect.left+this.rect.width,bottom:this.rect.top+this.rect.height}; }
  showModal() { this.open = true; }
  close() { this.open = false; this.fire('close'); }
}
function fixture(saved, blockedStorage = false) {
  const doc = new Events(), win = new Events(), els = {}, frames = new Map(), store = {};
  let frameId = 0, redraws = 0;
  if (saved) store['layer0.barrierExplorer.docking.v1'] = saved;
  doc.createElement = tag => new Element(tag, doc);
  doc.getElementById = id => els[id]; doc.body = doc.createElement('body');
  for (const id of ['dockWorkspace','dockViewport','dockAnnouncement','dockHint','dockPreset','dockHeightHandle','dockMoveDialog','dockMoveTarget','dockMovePosition','dockMoveTitle','dockMoveApply','dockMoveCancel','resetLayout']) {
    els[id] = doc.createElement(id === 'dockMoveDialog' ? 'dialog' : 'div'); doc.body.append(els[id]);
  }
  const canvases = {};
  for (const id of M.IDS) {
    const card = els[id] = doc.createElement('div'), h2 = doc.createElement('h2'), text = doc.createElement('text'), cv = doc.createElement('div');
    text.textContent = id; h2.append(text); cv.className = 'cv'; canvases[id] = doc.createElement('canvas'); cv.append(canvases[id]);
    card.append(h2, cv); els.dockWorkspace.append(card);
  }
  els.k3d.rect = {left:0,top:0,width:800,height:500};
  els.kA.rect = {left:810,top:0,width:590,height:240};
  els.kB.rect = {left:810,top:250,width:590,height:250};
  els.kG.rect = {left:0,top:510,width:450,height:350};
  els.kI.rect = {left:460,top:510,width:470,height:350};
  els.kR.rect = {left:940,top:510,width:460,height:350};
  const media = new Events(); media.matches = false;
  Object.assign(win,{DockLayout:M,innerHeight:1000,innerWidth:1450,matchMedia:()=>media,scrollBy(){}});
  const ctx = {window:win,document:doc,localStorage:{
    getItem:k=>{if(blockedStorage) throw Error('blocked'); return store[k] || null;},
    setItem:(k,v)=>{if(blockedStorage) throw Error('blocked'); store[k]=v;}
  },requestAnimationFrame:fn=>{frames.set(++frameId,fn);return frameId;},cancelAnimationFrame:id=>frames.delete(id)};
  vm.runInNewContext(script, ctx);
  const api = win.DockWorkspace.create({root:els.dockWorkspace,viewport:els.dockViewport,reset:els.resetLayout,onChange:()=>redraws++});
  return {doc,win,els,canvases,store,api,media,frames,redraws:()=>redraws,
    save:()=>store['layer0.barrierExplorer.docking.v1'],
    move: (source,target,zone) => {
      els[source].querySelector('.dock-move-button').fire('click'); els.dockMoveTarget.value=target; els.dockMovePosition.value=zone; els.dockMoveApply.fire('click');
    }};
}
function snapshot(f) { return JSON.stringify(f.api.state()); }

test('Move dialog reparents the actual cards and canvases, saves, and requests redraw', () => {
  const f = fixture(), initial = f.redraws();
  f.move('kI','k3d','right');
  assert.equal(M.valid(f.api.state().tree),true);
  assert.equal(f.els.kI.parentElement, f.els.k3d.parentElement);
  for (const id of M.IDS) assert.equal(f.els[id].querySelector('canvas'),f.canvases[id]);
  assert.equal(f.els.dockMoveDialog.open,false);
  assert(f.redraws() > initial); assert(f.save());
  const loaded = fixture(f.save()); assert.equal(snapshot(loaded),snapshot(f));
});

test('header drag commits an edge dock; Escape and outside release leave layout untouched', () => {
  const f = fixture(), before = snapshot(f), bar = f.els.kI.querySelector('.dock-titlebar');
  bar.fire('pointerdown',{clientX:650,clientY:530});
  bar.fire('pointermove',{clientX:795,clientY:250});
  assert(f.doc.body.classList.contains('dock-dragging'));
  const escape = f.doc.fire('keydown',{key:'Escape'});
  assert(escape.defaultPrevented); assert.equal(snapshot(f),before); assert.equal(f.frames.size,0);
  bar.fire('pointerdown',{clientX:650,clientY:530});
  bar.fire('pointermove',{clientX:1500,clientY:950});
  bar.fire('pointerup',{clientX:1500,clientY:950});
  assert.equal(snapshot(f),before);
  bar.fire('pointerdown',{clientX:650,clientY:530});
  bar.fire('pointermove',{clientX:795,clientY:250});
  bar.fire('pointerup',{clientX:795,clientY:250});
  assert.notEqual(snapshot(f),before);
  assert.equal(f.els.kI.parentElement,f.els.k3d.parentElement);
  assert.equal(f.frames.size,0); assert(!f.doc.body.classList.contains('dock-dragging'));
});

test('pointer cancellation and blur remove ghost state without saving a move', () => {
  for (const kind of ['pointercancel','blur']) {
    const f=fixture(), before=snapshot(f), bar=f.els.kG.querySelector('.dock-titlebar');
    bar.fire('pointerdown',{clientX:50,clientY:530}); bar.fire('pointermove',{clientX:400,clientY:250});
    (kind==='blur' ? f.win : bar).fire(kind);
    assert.equal(snapshot(f),before); assert(!f.doc.body.classList.contains('dock-dragging')); assert.equal(f.frames.size,0);
  }
});

test('divider resize commits on release and restores its ratio on cancellation', () => {
  const f=fixture(), split=f.els.dockWorkspace.firstElementChild, divider=split.children[1], before=snapshot(f);
  divider.fire('pointerdown',{clientY:500}); divider.fire('pointermove',{clientY:550});
  assert.notEqual(snapshot(f),before);
  divider.fire('pointercancel'); assert.equal(snapshot(f),before);
  divider.fire('pointerdown',{clientY:500}); divider.fire('pointermove',{clientY:550}); divider.fire('pointerup',{clientY:550});
  assert.notEqual(snapshot(f),before); assert(f.save()); assert(!f.doc.body.classList.contains('dock-resizing'));
});

test('workspace height and presets work; narrow mode preserves the desktop layout', () => {
  const f=fixture(), before=f.api.state().height;
  f.els.dockHeightHandle.fire('keydown',{key:'ArrowDown',shiftKey:true});
  assert.notEqual(f.api.state().height,before);
  f.els.dockPreset.value='analysis'; f.els.dockPreset.fire('change');
  assert.equal(f.els.kI.parentElement,f.els.k3d.parentElement);
  const desktop=snapshot(f); f.media.matches=true; f.media.fire('change');
  assert(f.els.dockWorkspace.classList.contains('dock-compact')); assert.equal(snapshot(f),desktop);
  f.media.matches=false; f.media.fire('change'); assert.equal(snapshot(f),desktop);
  f.els.resetLayout.fire('click'); assert.equal(JSON.stringify(f.api.state().tree),JSON.stringify(M.preset('default')));
});

test('storage denial does not prevent docking', () => {
  const f=fixture(null,true); f.move('kR','k3d','center');
  assert.equal(M.valid(f.api.state().tree),true);
  assert.match(f.els.dockAnnouncement.textContent,/cannot save/);
});
