/* Export model/controller checks. Canvas and DOM doubles do not verify visual layout. */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const X = require('./barrier_export.js');
const E = require('./gif_encoder.js');

function context2d() {
  return {font:'12px sans-serif', measureText(text) { return {width:text.length * parseFloat(this.font.replace(/^600 /,'')) * .55}; },
    setTransform(){}, fillRect(){}, fillText(){}, drawImage(){}, strokeRect(){},
    getImageData() { return {data:new Uint8ClampedArray(64 * 64 * 4).fill(255)}; }};
}
test('appearance recovers invalid storage, clamps scales, and preserves font weight', () => {
  assert.deepEqual(X.appearance(null), {text:1,line:1,transparency:.5});
  assert.deepEqual(X.appearance({text:Infinity,line:'2'}), {text:1,line:1,transparency:.5});
  assert.deepEqual(X.appearance({text:8,line:-1}), {text:3,line:1,transparency:.5});
  assert.equal(X.font('600 10.5px Segoe UI',2), '600 21.00px Segoe UI');
});
test('growth frames include both endpoints, exact requested duration, and final hold', () => {
  for (const count of [60,90,120,180]) {
    const frames = X.timeline(6,count,6,6);
    assert.equal(frames[0].tau,0); assert.equal(frames.at(-1).tau,6);
    assert.equal(frames.reduce((sum,f)=>sum+f.delay,0),700);
    assert.ok(frames.at(-1).delay >= 102);
    frames.forEach((f,i)=>{ assert.ok(Number.isInteger(f.delay) && f.delay>=2); if(i) assert.ok(f.tau>frames[i-1].tau); });
  }
  for (const tau of [0,-1,6.01,NaN]) assert.throws(()=>X.timeline(tau,90,6,6),/Maximum/);
  assert.throws(()=>X.timeline(1,180,2,6),/fewer frames/);
  assert.throws(()=>X.timeline(1,1,6,6),/frames/);
  assert.throws(()=>X.timeline(1,90,21,6),/duration/);
});
test('compositions accommodate uneven docked panels without clipping or overlap', () => {
  const panels = ['c3d','cA','cB','cG','cI'].map((id,i)=>({id,cv:{},w:320+i*61,h:160+i*47,title:'Long descriptive panel title '+id}));
  for (const count of [1,2,3,4,5]) for (const scale of [1,3]) {
    const L = X.layout(panels.slice(0,count),1600,scale,context2d(),'Maximum range · τ = 6.00 / 6.00');
    assert.equal(L.width,1600);
    for (const b of L.boxes) {
      assert.ok((b.x+b.w)*L.factor<=L.width);
      assert.ok((b.y+b.head+b.h)*L.factor<L.height);
      for (const other of L.boxes) if(other!==b) {
        assert.ok(b.x+b.w<=other.x || other.x+other.w<=b.x || b.y+b.head+b.h<=other.y || other.y+other.head+other.h<=b.y);
      }
    }
    if(count===3) { assert.equal(L.boxes[1].x,L.boxes[2].x); assert.ok(L.boxes[2].y>L.boxes[1].y); }
  }
  assert.throws(()=>X.layout([],1600,1,context2d(),''),/at least one/);
  assert.throws(()=>X.layout([{w:0,h:10,title:'Hidden'}],1600,1,context2d(),''),/visible size/);
  assert.throws(()=>X.layout([{w:100,h:20000,title:'Tall'}],2400,1,context2d(),''),/too tall/);
});
test('GIF encoder yields between frames and stops when cancelled', async () => {
  let cancel=false, renders=0, progresses=0;
  await assert.rejects(X.encode({encoder:E,width:2,height:2,frames:X.timeline(1,60,6,6),
    cancelled:()=>cancel,render:()=>{renders++; return new Uint8Array(16).fill(255);},
    progress:()=>{progresses++;cancel=true;},yieldFrame:async()=>{}}),{name:'AbortError'});
  assert.equal(progresses,1); assert.equal(renders,5); // four palette samples, then first frame
});

function fixture(options={}) {
  const els={}, stored={}, downloads=[], calls=[];
  const ids=['barrierExportDialog','barrierTextSize','barrierTextOut','barrierLineSize','barrierLineOut','barrierStyleReset','barrierTransparency','barrierTransparencyOut',
    'barrierExportStatus','barrierExportCancel','barrierExportProgress','barrierExportTitle','barrierExportMeter',
    'barrierPng','barrierGif','barrierMaxTau','barrierGifSeconds','barrierGifFrames','barrierExportWidth','c3d'];
  for(const id of ids) els[id]={value:'',listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},
    fire(type,event={}){return this.listeners[type]?.call(this,event);},reportValidity(){return true;},
    showModal(){this.open=true;},close(){this.open=false;}};
  els.barrierMaxTau.value='1.5';els.barrierGifSeconds.value='6';els.barrierGifFrames.value='60';els.barrierExportWidth.value='64';
  let tau=.75, restored=0;
  const doc={getElementById:id=>els[id],querySelectorAll:()=>options.empty?[]:[{getAttribute:()=> 'c3d'}],
    body:{appendChild(){}},createElement(tag){return tag==='canvas'?{getContext:context2d,toBlob(fn){fn(options.nullBlob?null:new Blob(['png'],{type:'image/png'}));}}:
      {click(){downloads.push(this.download);},remove(){}};}};
  const sandbox={document:doc,Blob,ExplorerGif:E,URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},
    localStorage:{getItem:()=> options.saved || null,setItem(k,v){if(options.blockedStorage)throw Error('blocked'); stored[k]=v;}},
    setTimeout:fn=>setImmediate(fn)};
  sandbox.window=sandbox;vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(__dirname+'/barrier_export.js','utf8'),sandbox);
  const adapter={horizon:6,family:()=> 'max',label:()=> 'Maximum range',tau:()=>tau,setStyle(v){calls.push(['style',v.text,v.line,v.transparency]);},
    size:()=>({w:64,h:40}),begin(max){calls.push(['begin',max]);const keep=tau;return()=>{tau=keep;restored++;};},
    render(t){tau=t;calls.push(['render',t]);if(options.failRender)throw Error('render failure');if(options.cancel)els.barrierExportCancel.fire('click');}};
  const api=sandbox.BarrierExport.create(adapter);
  return {els,api,sandbox,downloads,calls,stored,get tau(){return tau;},get restored(){return restored;}};
}
test('PNG uses selected appearance and restores current state after downloading',async()=>{
  const f=fixture({saved:'{"text":2,"line":1.5}'});
  await f.api.png();
  assert.deepEqual(f.calls[0],['style',2,1.5,.5]);
  assert.equal(f.downloads.length,1);assert.match(f.downloads[0],/tau0.75_\d+\.png$/);
  assert.equal(f.restored,1);assert.equal(f.tau,.75);assert.equal(f.sandbox.BarrierExportBusy,false);
  assert.equal(f.els.barrierExportDialog.open,false);assert.match(f.els.barrierExportStatus.textContent,/Saved PNG/);
});
test('GIF cancellation restores tau and releases export lock without downloading',async()=>{
  const f=fixture({cancel:true});await f.els.barrierGif.fire('click');
  assert.equal(f.restored,1);assert.equal(f.tau,.75);assert.equal(f.downloads.length,0);
  assert.equal(f.sandbox.BarrierExportBusy,false);assert.equal(f.els.barrierExportDialog.open,false);
  assert.match(f.els.barrierExportStatus.textContent,/cancelled/);
});
test('render failures and failed PNG creation restore state and report errors',async()=>{
  for(const options of [{failRender:true},{nullBlob:true}]) {
    const f=fixture(options);await f.api.png();
    assert.equal(f.restored,1);assert.equal(f.tau,.75);assert.equal(f.downloads.length,0);
    assert.equal(f.sandbox.BarrierExportBusy,false);assert.equal(f.els.barrierExportDialog.open,false);
    assert.match(f.els.barrierExportStatus.textContent,/Export failed/);
  }
});
test('validation precedes state changes; blocked storage still allows appearance edits',async()=>{
  const f=fixture({empty:true,saved:'invalid',blockedStorage:true});await f.api.png();
  assert.equal(f.restored,0);assert.equal(f.downloads.length,0);assert.match(f.els.barrierExportStatus.textContent,/at least one/);
  f.els.barrierTextSize.value=220;f.els.barrierTextSize.fire('input');
  assert.deepEqual(f.calls.at(-1),['style',2.2,1,.5]);assert.equal(f.els.barrierTextOut.textContent,'220%');
  f.els.barrierTransparency.value=85;f.els.barrierTransparency.fire('input');
  assert.deepEqual(f.calls.at(-1),['style',2.2,1,.85]);assert.equal(f.els.barrierTransparencyOut.textContent,'85%');
  f.els.barrierLineSize.value=150;f.els.barrierLineSize.fire('input');assert.deepEqual(f.calls.at(-1),['style',2.2,1.5,.85]);
  f.els.barrierTextSize.value=180;f.els.barrierTextSize.fire('input');assert.deepEqual(f.calls.at(-1),['style',1.8,1.5,.85]);
  f.els.barrierStyleReset.fire('click');assert.deepEqual(f.calls.at(-1),['style',1,1,.5]);
  const saved=fixture({saved:'{"text":1.5,"line":2,"transparency":0.8}'});
  assert.deepEqual(saved.calls[0],['style',1.5,2,.8]);
  assert.equal(JSON.parse(Object.values(saved.stored)[0]).transparency,.8);
  assert.equal(saved.els.barrierTransparency.value,80);
  const g=fixture();g.els.barrierMaxTau.value='7';await g.els.barrierGif.fire('click');
  assert.equal(g.restored,0);assert.equal(g.calls.length,1);assert.match(g.els.barrierExportStatus.textContent,/Maximum/);
});
