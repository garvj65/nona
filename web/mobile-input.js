/* Screen-space input math, without browser globals or network side effects. */
(function(root){
  'use strict';
  const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  function floatingStick(x,y,originX,originY,radius,deadzone=.08){
    let dx=(x-originX)/radius,dy=(y-originY)/radius;
    const length=Math.hypot(dx,dy);
    if(length<=deadzone)return{x:0,y:0};
    const magnitude=clamp((length-deadzone)/(1-deadzone),0,1);
    return{x:dx/length*magnitude,y:dy/length*magnitude};
  }
  class GyroLook{
    constructor(){this.sensitivity=3;this.deadzone=.6;this.stop();}
    stop(){this.enabled=false;this.lastSample=null;this.screenAngle=null;this.filtered={x:0,y:0};}
    enable(){this.stop();this.enabled=true;}
    sample(rate,screenAngle,now,active){
      const zero={dx:0,dy:0};
      if(!this.enabled||!rate||![rate.alpha,rate.beta,screenAngle,now].every(v=>typeof v==='number'&&Number.isFinite(v)))return zero;
      const elapsed=this.lastSample===null?0:now-this.lastSample;
      const changed=this.screenAngle!==null&&screenAngle!==this.screenAngle;
      this.lastSample=now;this.screenAngle=screenAngle;
      if(!active||elapsed<=0||elapsed>150||changed){this.filtered={x:0,y:0};return zero;}
      const s=screenAngle*Math.PI/180;
      // rotationRate uses alpha=X, beta=Y, gamma=Z (unlike orientation Euler angles).
      const yaw=-rate.alpha*Math.sin(s)+rate.beta*Math.cos(s);
      const pitch=rate.alpha*Math.cos(s)+rate.beta*Math.sin(s);
      const clean=v=>Math.abs(v)<=this.deadzone?0:clamp(v,-360,360);
      const weight=1-Math.exp(-elapsed/25);
      this.filtered.x+=(clean(yaw)-this.filtered.x)*weight;
      this.filtered.y+=(clean(pitch)-this.filtered.y)*weight;
      const dt=Math.min(elapsed,50)/1000*this.sensitivity;
      return{dx:clamp(this.filtered.x*dt,-48,48),dy:clamp(this.filtered.y*dt,-48,48)};
    }
    stale(now){return this.enabled&&this.lastSample!==null&&now-this.lastSample>750;}
  }
  const api={floatingStick,GyroLook,clamp};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NonaMobile=api;
})(typeof globalThis==='undefined'?this:globalThis);
