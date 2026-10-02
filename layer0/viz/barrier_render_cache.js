/* Display-only acceleration. Original integration samples remain untouched.
   Bounds are exact; simplified polylines have a caller-specified error bound
   in (phi2 radians, phi1 radians, R). Exports may request every original point. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.BarrierRenderCache=factory();
}(typeof window!=='undefined'?window:globalThis,function(){
  'use strict';
  var cache=new WeakMap(), BLOCK=64;
  function prepare(t){
    var old=cache.get(t);if(old)return old;
    var n=t.tau.length, prefix=new Float64Array(Math.floor(n/BLOCK)*6);
    var b=[Infinity,-Infinity,Infinity,-Infinity,Infinity,-Infinity];
    for(var i=0;i<n;i++){
      extend(b,t,i);
      if((i+1)%BLOCK===0)prefix.set(b,((i+1)/BLOCK-1)*6);
    }
    var item={prefix:prefix,tree:null};cache.set(t,item);return item;
  }
  function extend(b,t,i){
    var x=t.a2[i],y=t.a1[i],z=t.R[i];
    if(x<b[0])b[0]=x;if(x>b[1])b[1]=x;
    if(y<b[2])b[2]=y;if(y>b[3])b[3]=y;
    if(z<b[4])b[4]=z;if(z>b[5])b[5]=z;
  }
  function bounds(t,m){
    var item=prepare(t), count=Math.floor((m+1)/BLOCK), start=count*BLOCK;
    var b=count?Array.from(item.prefix.subarray((count-1)*6,count*6)):[Infinity,-Infinity,Infinity,-Infinity,Infinity,-Infinity];
    for(var i=start;i<=m;i++)extend(b,t,i);
    return b;
  }
  function node(t,lo,hi){
    var x=t.a2[lo],y=t.a1[lo],z=t.R[lo];
    var dx=t.a2[hi]-x,dy=t.a1[hi]-y,dz=t.R[hi]-z,den=dx*dx+dy*dy+dz*dz;
    var error=0,split=(lo+hi)>>1;
    for(var i=lo+1;i<hi;i++){
      var px=t.a2[i]-x,py=t.a1[i]-y,pz=t.R[i]-z;
      var u=den?Math.max(0,Math.min(1,(px*dx+py*dy+pz*dz)/den)):0;
      var ex=px-u*dx,ey=py-u*dy,ez=pz-u*dz,d=ex*ex+ey*ey+ez*ez;
      if(d>error){error=d;split=i;}
    }
    return {lo:lo,hi:hi,error:error,split:split,left:null,right:null};
  }
  function curve(t,m,tolerance){
    if(m<=0)return [0];
    if(!(tolerance>0))return Array.from({length:m+1},function(_,i){return i;});
    var item=prepare(t);if(!item.tree)item.tree=node(t,0,t.tau.length-1);
    var out=[0],stack=[item.tree],error=tolerance*tolerance;
    while(stack.length){
      var n=stack.pop();if(n.lo>=m)continue;
      if(n.hi<=m&&(n.error<=error||n.hi-n.lo===1)){out.push(n.hi);continue;}
      // A node straddling the growth endpoint must be split, even when its
      // entire curve is flat enough. This bounds the error of partial curves too.
      if(!n.left){n.left=node(t,n.lo,n.split);n.right=node(t,n.split,n.hi);}
      if(n.split<m)stack.push(n.right);stack.push(n.left);
    }
    return out;
  }
  return {prepare:prepare,bounds:bounds,curve:curve};
}));
