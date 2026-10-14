/* Drawer focus, keyboard ownership, and view-switch tests using DOM doubles. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function fixture(){
  const els={},buttons=[],panels=[],names=['display','export','layout','help'];
  const doc={activeElement:null,modal:null,listeners:{},getElementById:id=>els[id],
    querySelector:()=>doc.modal,querySelectorAll:s=>s==='[data-workspace-tool]'?buttons:panels,
    addEventListener(type,fn){this.listeners[type]=fn;}};
  function node(attributes={}){
    const classes=new Set();
    return {attributes,listeners:{},hidden:false,scrollTop:0,
      setAttribute(k,v){this.attributes[k]=v;},getAttribute(k){return this.attributes[k];},
      classList:{contains:k=>classes.has(k),toggle(k,v){if(v)classes.add(k);else classes.delete(k);}},
      addEventListener(type,fn){this.listeners[type]=fn;},click(){this.listeners.click?.();},focus(){doc.activeElement=this;}};
  }
  for(const id of ['workspaceDrawer','workspaceTools','drawerClose','drawerTitle'])els[id]=node();
  const scroll=node();
  els.workspaceDrawer.contains=n=>n.inside;els.workspaceDrawer.querySelector=()=>scroll;
  doc.body=node();
  for(const inside of [false,true])for(const name of names){const b=node({'data-workspace-tool':name});b.inside=inside;buttons.push(b);}
  for(const name of names)panels.push(node({'data-drawer-panel':name}));
  const win={document:doc};win.window=win;vm.createContext(win);
  vm.runInContext(fs.readFileSync(__dirname+'/workspace_chrome.js','utf8'),win);
  const controller=win.WorkspaceChrome.create();
  function escape(init={}){const e={key:'Escape',defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},...init};doc.listeners.keydown(e);return e;}
  return {els,buttons,panels,doc,win,controller,escape,scroll};
}
test('drawer sections share one panel, retain focus origin, and toggle accessibly',()=>{
  const f=fixture();assert.equal(f.els.workspaceDrawer.hidden,true);
  f.buttons[0].click();assert.equal(f.els.workspaceDrawer.hidden,false);
  assert.equal(f.doc.activeElement,f.els.drawerClose);
  assert.equal(f.panels.filter(p=>!p.hidden).length,1);
  assert.equal(f.buttons[0].attributes['aria-expanded'],'true');
  assert.equal(f.buttons[4].attributes['aria-expanded'],'true');
  f.scroll.scrollTop=500;f.buttons[5].click(); // internal Export switch
  assert.equal(f.els.drawerTitle.textContent,'Export & appearance');assert.equal(f.scroll.scrollTop,0);
  assert.equal(f.panels[0].hidden,true);assert.equal(f.panels[1].hidden,false);
  f.buttons[5].click();assert.equal(f.els.workspaceDrawer.hidden,false); // active internal button stays open
  f.els.drawerClose.click();assert.equal(f.doc.activeElement,f.buttons[0]);
  assert.ok(f.buttons.every(b=>b.attributes['aria-expanded']==='false'));
  f.buttons[2].click();f.buttons[2].click();assert.equal(f.els.workspaceDrawer.hidden,true);
});
test('Escape closes settings without unpinning and yields to modal dialogs and docking gestures',()=>{
  const f=fixture();f.buttons[3].click();
  f.doc.modal={open:true};assert.equal(f.escape().defaultPrevented,false);assert.equal(f.els.workspaceDrawer.hidden,false);
  f.doc.modal=null;
  for(const cls of ['dock-dragging','dock-resizing']){
    f.doc.body.classList.toggle(cls,true);assert.equal(f.escape().defaultPrevented,false);assert.equal(f.els.workspaceDrawer.hidden,false);
    f.doc.body.classList.toggle(cls,false);
  }
  assert.equal(f.escape().defaultPrevented,true);assert.equal(f.els.workspaceDrawer.hidden,true);assert.equal(f.doc.activeElement,f.buttons[3]);
  assert.equal(f.escape().defaultPrevented,false);
});
test('switching views closes barrier settings without stealing tab focus; returning starts closed',()=>{
  const f=fixture();f.buttons[1].click();const tab={};f.doc.activeElement=tab;
  f.controller.setView('coords');assert.equal(f.els.workspaceDrawer.hidden,true);assert.equal(f.els.workspaceTools.hidden,true);
  assert.equal(f.doc.activeElement,tab);f.buttons[0].click();assert.equal(f.els.workspaceDrawer.hidden,true);
  f.controller.setView('barrier');assert.equal(f.els.workspaceTools.hidden,false);assert.equal(f.els.workspaceDrawer.hidden,true);
  f.win.BarrierExportBusy=true;f.buttons[0].click();assert.equal(f.els.workspaceDrawer.hidden,true);
  f.win.BarrierExportBusy=false;f.buttons[0].click();assert.equal(f.els.workspaceDrawer.hidden,false);
});
