'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const R=require('./barrier_render_cache.js');
const {fixture}=require('./benchmark_barrier_render.js');
const html=fs.readFileSync(__dirname+'/barrier_explorer.html','utf8');
function path(n){
  const t={tau:[],a1:[],a2:[],R:[]};
  for(let i=0;i<n;i++){const s=i/(n-1);t.tau.push(s*6);t.a1.push(Math.sin(s*13));t.a2.push(s*4+.1*Math.sin(s*79));t.R.push(2+Math.cos(s*11));}
  return t;
}
function distance(t,i,a,b){
  const keys=['a2','a1','R'],p=keys.map(k=>t[k][i]-t[k][a]),d=keys.map(k=>t[k][b]-t[k][a]);
  const den=d.reduce((s,v)=>s+v*v,0),u=den?Math.max(0,Math.min(1,p.reduce((s,v,k)=>s+v*d[k],0)/den)):0;
  return Math.hypot(...p.map((v,k)=>v-u*d[k]));
}
function verify(t,m,tolerance){
  const indices=R.curve(t,m,tolerance);assert.equal(indices[0],0);assert.equal(indices.at(-1),m);
  for(let j=1;j<indices.length;j++){
    const a=indices[j-1],b=indices[j];assert.ok(b>a);
    for(let i=a+1;i<b;i++)assert.ok(distance(t,i,a,b)<=tolerance+1e-12);
  }
  return indices;
}
test('cached bounds exactly match the complete prefix, across block edges and backwards scrubs',()=>{
  const t=path(1027),before=JSON.stringify(t);
  for(const m of [0,1,62,63,64,127,128,1000,1026,89,13]){
    const expected=['a2','a1','R'].flatMap(k=>[Math.min(...t[k].slice(0,m+1)),Math.max(...t[k].slice(0,m+1))]);
    assert.deepEqual(R.bounds(t,m),expected);
  }
  assert.equal(JSON.stringify(t),before);
});
test('simplified curves obey their error bound and retain exact partial-growth endpoints',()=>{
  const t=path(1801),before=JSON.stringify(t);
  for(const tolerance of [.1,.01,.001])for(const m of [0,1,77,499,1359,1800,601])verify(t,m,tolerance);
  const straight={tau:[0,1,2,3],a1:[0,0,0,0],a2:[0,1,2,3],R:[2,2,2,2]};
  verify(straight,2,.01);
  const loop={tau:[0,1,2,3],a1:[0,1,-1,0],a2:[0,1,-1,0],R:[2,2,2,2]};verify(loop,3,.01);
  assert.deepEqual(R.curve(t,13,0),Array.from({length:14},(_,i)=>i));
  assert.ok(R.curve(t,1800,.01).length<1801/5);assert.equal(JSON.stringify(t),before);
});
test('real-family caches preserve extrema, numerical state, zoom error, and visibility changes',()=>{
  const f=fixture(html,3),c=f.ctx;
  for(const family of ['max','min','bore+','bore-']){
    f.els.fam.value=family;c.rebuild();
    const t=c.S.flat[Math.floor(c.S.flat.length/2)],before=JSON.stringify(t);
    const m=c.cut(t,1.3);verify(t,m,.0002);assert.equal(JSON.stringify(t),before);
    const q=R.bounds(t,m);assert.equal(q[5],Math.max(...t.R.slice(0,m+1)));
    c.setTau(1.3);
    const P=c.make3d({w:960,h:600});verify(t,m,.35/P.pixelScale);
    c.S.focus=true;c.S.sel=c.S.flat.indexOf(t);
    assert.deepEqual(Array.from(c.bundleBounds()),q);
    c.S.hidden[c.S.branches[t.bi].name]=true;assert.equal(c.bundleBounds()[0],Infinity);
    c.S.hidden={};c.S.focus=false;
  }
});
test('unchanged live canvases are reused; exports retain original geometry and high resolution',()=>{
  const f=fixture(html,9),c=f.ctx;c.rebuild();c.setTau(4);
  Object.keys(f.counts).forEach(k=>f.counts[k]=0);c.draw();
  const live=f.counts.lineTo;assert.equal(f.counts.resize,0);assert.equal(f.els.c3d.width,960);
  c.BARRIER_CAPTURE={maxTau:4,sizes:{c3d:{w:960,h:600}}};f.counts.lineTo=0;c.draw();
  assert.ok(f.counts.lineTo>live*3);assert.equal(f.els.c3d.width,1920);
  c.BARRIER_CAPTURE=null;c.draw();assert.equal(f.els.c3d.width,960);
  f.counts.resize=0;c.draw();assert.equal(f.counts.resize,0);
});
test('slider bursts coalesce and playback follows frame timestamps without changing export tau',()=>{
  const f=fixture(html,3),c=f.ctx;c.rebuild();
  let draws=0;c.draw=()=>{draws++;};
  for(const tau of [.1,.2,.3,.4])c.setTau(tau,true);
  assert.equal(f.queue.length,1);assert.equal(draws,0);f.queue.shift()(0);assert.equal(draws,1);assert.equal(c.S.tau,.4);
  f.els.play.click();assert.equal(c.playing,true);assert.equal(f.queue.length,1);
  f.queue.shift()(100);f.queue.shift()(145);assert.ok(Math.abs(c.S.tau-.45)<1e-12);
  c.redrawSoon();assert.equal(f.queue.length,1);
  f.els.play.click();const paused=c.S.tau;f.queue.shift()(190);assert.equal(c.S.tau,paused);assert.equal(f.queue.length,0);
  c.setTau(1.23);assert.equal(c.S.tau,1.23);
  c.redrawSoon();c.BARRIER_CAPTURE={maxTau:2};const prev=draws;f.queue.shift()(200);assert.equal(draws,prev);
  c.setTau(2);assert.equal(draws,prev+1);assert.equal(c.S.tau,2);
});
