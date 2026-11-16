/* Sensor math/lifecycle shared by the controller and deterministic tests. */
(function(root){
  'use strict';
  const degrees = radians => radians * 180 / Math.PI;
  const radians = angle => angle * Math.PI / 180;
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const delta = (angle, centre) => degrees(Math.atan2(Math.sin(radians(angle-centre)), Math.cos(radians(angle-centre))));

  function rollFromOrientation(beta, gamma, screenAngle=0){
    if(![beta,gamma,screenAngle].every(value=>typeof value==='number'&&Number.isFinite(value)))return null;
    const b=radians(beta),g=radians(gamma),s=radians(screenAngle);
    // Gravity projected into the display plane. Alpha/magnetic heading is not needed.
    const gx=-Math.cos(b)*Math.sin(g),gy=Math.sin(b);
    const x=gx*Math.cos(s)+gy*Math.sin(s),y=-gx*Math.sin(s)+gy*Math.cos(s);
    if(Math.hypot(x,y)<.2)return null; // A nearly flat screen has an unstable roll.
    return degrees(Math.atan2(x,y));
  }

  class TiltSteering{
    constructor(){this.range=30;this.deadzone=2;this.smoothingMs=60;this.invert=false;this.stop();}
    stop(){this.enabled=false;this.calibrated=false;this.centre=0;this.angle=null;this.filtered=0;this.lastSample=null;this.screenAngle=null;}
    enable(){this.stop();this.enabled=true;}
    calibrate(){if(!this.enabled||this.angle===null)return false;this.centre=this.angle;this.filtered=0;this.calibrated=true;return true;}
    sample(beta,gamma,screenAngle,now){
      if(!this.enabled)return{value:0,state:'off'};
      if(this.screenAngle!==null&&screenAngle!==this.screenAngle){this.calibrated=false;this.filtered=0;}
      this.screenAngle=screenAngle;
      const angle=rollFromOrientation(beta,gamma,screenAngle);
      if(angle===null){this.calibrated=false;this.angle=null;this.filtered=0;return{value:0,state:'hold-upright'};}
      const dt=this.lastSample===null?0:Math.max(0,Math.min(250,now-this.lastSample));
      this.angle=angle;this.lastSample=now;
      if(!this.calibrated)return{value:0,state:'calibrate',angle};
      let offset=delta(angle,this.centre);
      const magnitude=Math.max(0,Math.abs(offset)-this.deadzone);
      let desired=clamp(magnitude/Math.max(1,this.range-this.deadzone),0,1)*Math.sign(offset)*(this.invert?-1:1);
      const weight=this.smoothingMs===0?1:1-Math.exp(-dt/this.smoothingMs);
      this.filtered+=(desired-this.filtered)*weight;
      if(desired===0&&Math.abs(this.filtered)<.005)this.filtered=0;
      return{value:this.filtered,state:'active',angle,offset};
    }
    stale(now,timeout=750){return this.enabled&&this.lastSample!==null&&now-this.lastSample>timeout;}
  }
  const api={rollFromOrientation,delta,TiltSteering};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NonaMotion=api;
})(typeof globalThis==='undefined'?this:globalThis);
