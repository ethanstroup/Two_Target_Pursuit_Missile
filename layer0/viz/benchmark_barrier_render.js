/* CPU/draw-command benchmark with no-op canvas calls, not a browser FPS test.
   --baseline reads the committed HTML for a same-process before/after comparison. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),cp=require('node:child_process');
function fixture(html, n=45) {
  const source=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(s=>s.trim());
  const els={},counts={lineTo:0,fill:0,resize:0},queue=[];
  function element(id){
    const g={};
    for(const name of ['arc','clearRect','lineTo','moveTo','rect','setTransform','strokeRect','beginPath','clip','closePath','fill','restore','save','setLineDash','stroke','fillText'])
      g[name]=()=>{if(name in counts)counts[name]++;};
    const e={id,clientWidth:id==='c3d'?960:640,clientHeight:id==='c3d'?600:300,style:{},value:id==='ns'?String(n):'max',
      classList:{contains:()=>true,toggle(){},add(){},remove(){}},getContext:()=>g,setAttribute(){},addEventListener(){},querySelectorAll:()=>[],appendChild(){},click(){this.onclick?.call(this);}};
    for(const key of ['width','height'])Object.defineProperty(e,key,{get(){return this['_'+key];},set(v){counts.resize++;this['_'+key]=v;}});
    return e;
  }
  const doc={getElementById:id=>els[id]||(els[id]=element(id)),querySelectorAll:()=>[],addEventListener(){},createElement:()=>element('')};
  const ctx={document:doc,performance,console,Barrier:require('../barrier.js'),BupCurves:require('./bup_curves.js'),
    BarrierExport:require('./barrier_export.js'),addEventListener(){},requestAnimationFrame(fn){queue.push(fn);},devicePixelRatio:1};
  const cache=__dirname+'/barrier_render_cache.js';if(fs.existsSync(cache))ctx.BarrierRenderCache=require(cache);
  ctx.window=ctx;vm.createContext(ctx);vm.runInContext(source.slice(0,source.indexOf('(function init()')),ctx);
  return {ctx,els,counts,queue};
}
function benchmark(html){
  const f=fixture(html);const start=performance.now();f.ctx.rebuild();const buildMs=performance.now()-start;
  for(const tau of [1.5,3,6])f.ctx.setTau(tau); // warm caches/JIT
  const frames=[];
  for(const tau of [1.5,3,6]){
    const ms=[];let operations;
    for(let repeat=0;repeat<3;repeat++){
      Object.keys(f.counts).forEach(k=>f.counts[k]=0);
      const t=performance.now();f.ctx.setTau(tau);ms.push(performance.now()-t);operations={...f.counts};
    }
    frames.push({tau,cpuMs:+ms.sort((a,b)=>a-b)[1].toFixed(1),...operations});
  }
  return {trajectories:f.ctx.S.flat.length,samples:f.ctx.S.flat.reduce((n,t)=>n+t.tau.length,0),buildMs:Math.round(buildMs),frames};
}
if(require.main===module){
  const html=process.argv.includes('--baseline')?cp.execFileSync('git',['show','HEAD:layer0/viz/barrier_explorer.html'],{cwd:__dirname,encoding:'utf8'}):fs.readFileSync(__dirname+'/barrier_explorer.html','utf8');
  console.log(JSON.stringify(benchmark(html),null,2));
}
module.exports={fixture};
