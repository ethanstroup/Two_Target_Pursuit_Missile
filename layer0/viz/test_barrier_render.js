/* Run the actual barrier drawing code with canvas/DOM doubles. This catches
   runtime and numeric errors, but does not replace visual browser testing. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

test('barrier plots use appearance scales and hold capture bounds and canvas dimensions',()=>{
  const html=fs.readFileSync(__dirname+'/barrier_explorer.html','utf8');
  const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).filter(s=>s.trim());
  scripts.forEach(s=>new vm.Script(s));
  const els={}, ink={fonts:[],widths:[],arcs:[]};
  function canvasContext(){
    const ctx={};
    for(const name of ['arc','clearRect','lineTo','moveTo','rect','setTransform','strokeRect'])ctx[name]=(...args)=>{
      args.filter(v=>typeof v==='number').forEach(v=>assert.ok(Number.isFinite(v),name+' received a non-finite coordinate'));
      if(name==='arc'){assert.ok(args[2]>0);ink.arcs.push(args[2]);}
    };
    for(const name of ['beginPath','clip','closePath','fill','restore','save','setLineDash','stroke'])ctx[name]=()=>{};
    ctx.fillText=(text,x,y)=>{assert.ok(Number.isFinite(x)&&Number.isFinite(y));ink.fonts.push(ctx.font);};
    Object.defineProperty(ctx,'lineWidth',{set(v){assert.ok(v>0&&Number.isFinite(v));ink.widths.push(v);}});
    return ctx;
  }
  function element(id){
    const g=canvasContext();return {id,clientWidth:640,clientHeight:360,style:{},value:id==='ns'?'3':'max',
      classList:{contains:()=>true,toggle(){},add(){},remove(){}},
      getContext:()=>g,setAttribute(){},addEventListener(){},querySelectorAll:()=>[],appendChild(){},
      click(){this.onclick?.call(this);}};
  }
  const doc={getElementById:id=>els[id]||(els[id]=element(id)),querySelectorAll:()=>[],addEventListener(){},createElement:()=>element('')};
  const ctx={document:doc,performance,console,Barrier:require('../barrier.js'),BupCurves:require('./bup_curves.js'),
    BarrierExport:require('./barrier_export.js'),BarrierRenderCache:require('./barrier_render_cache.js'),addEventListener(){},requestAnimationFrame(){},devicePixelRatio:1};
  ctx.window=ctx;vm.createContext(ctx);
  // Initialization of controls is exercised in separate controller tests.
  vm.runInContext(scripts[0].slice(0,scripts[0].indexOf('(function init()')),ctx);
  ctx.rebuild();
  assert.ok(ctx.S.flat.length>0);
  ctx.S.pinned=0;ctx.S.mark=.4;ctx.S.views.cA={dom:[20,-20,50,-50],k:1,dx:0,dy:0};
  ctx.setTau(.3);
  const baseFonts=[...ink.fonts],baseWidths=[...ink.widths];ink.fonts=[];ink.widths=[];ink.arcs=[];
  ctx.BUI={text:3,line:2.5,transparency:.5};ctx.draw();
  assert.ok(Math.max(...ink.widths)>Math.max(...baseWidths));
  assert.ok(ink.fonts.includes(ctx.BarrierExport.font(ctx.AX_NAME_FONT,3)));
  assert.ok(baseFonts.includes(ctx.AX_NAME_FONT.replace('13px','13.00px')));
  const sizes={};for(const id of ['c3d','cA','cB','cG','cI'])sizes[id]={w:640,h:360};
  ctx.BARRIER_CAPTURE={maxTau:1.5,sizes};
  let bounds;
  for(const tau of [0,.5,1.5]){
    ctx.setTau(tau);
    const b=JSON.stringify(ctx.autoBounds('phi2','R'));
    if(bounds)assert.equal(b,bounds);bounds=b;
    assert.deepEqual(Array.from(ctx.faceFrame('cA',els.cA,null).domain()),[20,-20,50,-50]);
    assert.equal(ctx.S.mark,.4);assert.equal(ctx.S.pinned,0);
  }
  els.c3d.clientWidth=900;ctx.draw();assert.equal(els.c3d.width,1280);
  ctx.BARRIER_CAPTURE.ratios={c3d:3.5};ctx.draw();assert.equal(els.c3d.width,2240);assert.equal(els.cA.width,1280);
  ctx.BARRIER_CAPTURE=null;ctx.setTau(.3);assert.equal(els.c3d.width,900);
  assert.notEqual(JSON.stringify(ctx.autoBounds('phi2','R')),bounds);

  // Surface transparency must not fade strokes, including in captures.
  const g=els.c3d.getContext('2d'),fills=[],strokes=[];
  g.fill=()=>fills.push({color:g.fillStyle,alpha:g.globalAlpha});
  g.stroke=()=>strokes.push({color:g.strokeStyle,alpha:g.globalAlpha});
  for(const capture of [false,true])for(const transparency of [.5,.8,1]){
    ctx.BARRIER_CAPTURE=capture?{maxTau:.3,sizes}:null;
    ctx.BUI.transparency=transparency;fills.length=0;strokes.length=0;ctx.draw3d();
    const shading=fills.filter(f=>/^rgba?\(/.test(f.color));
    if(transparency===1)assert.equal(shading.length,0);
    else {assert.ok(shading.length>0);assert.ok(shading.every(f=>Math.abs(f.alpha-(1-transparency))<1e-12));}
    assert.ok(strokes.some(s=>s.alpha===.85));assert.ok(strokes.every(s=>s.alpha>=.85));
    assert.ok(fills.some(f=>f.color==='#000'&&f.alpha===1));
  }
  ctx.BARRIER_CAPTURE=null;ctx.BUI.transparency=.5;
  els.fam.value='bore-';ctx.rebuild();
  const nq=ctx.S.branches.find(b=>b.name.startsWith('wall (BUP) N₁′–Q₁′'));
  const qm=ctx.S.branches.find(b=>b.name.startsWith('wall (BUP) Q₁′–m₁′'));
  assert.equal(nq.color,'#c52b35');assert.equal(qm.color,'#e27d83');
  const faceColors=[],poly=ctx.Frame.prototype.poly;
  ctx.Frame.prototype.poly=function(...args){faceColors.push(args[2]);return poly.apply(this,args);};
  strokes.length=0;ctx.setTau(0);
  assert.ok(strokes.some(s=>s.color===ctx.BUP));assert.ok(faceColors.includes(ctx.BUP));
  for(const color of [nq.color,qm.color]){
    assert.ok(!strokes.some(s=>s.color===color));assert.ok(!faceColors.includes(color));
  }
});
