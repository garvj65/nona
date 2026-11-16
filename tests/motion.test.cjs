const {test}=require('node:test'),assert=require('node:assert/strict');
const {rollFromOrientation,delta,TiltSteering}=require('../web/motion.js');
function orientation(roll,screenAngle=0){
 const r=roll*Math.PI/180,s=screenAngle*Math.PI/180;
 const x=.8*Math.sin(r),y=.8*Math.cos(r),gx=x*Math.cos(s)-y*Math.sin(s),gy=x*Math.sin(s)+y*Math.cos(s);
 const beta=Math.asin(gy),gamma=Math.asin(-gx/Math.cos(beta));
 return{beta:beta*180/Math.PI,gamma:gamma*180/Math.PI,screenAngle};
}
function sample(tilt,roll,time=0,angle=0){const o=orientation(roll,angle);return tilt.sample(o.beta,o.gamma,angle,time);}
test('gravity roll maps consistently in portrait and both landscape orientations',()=>{
 for(const angle of [0,90,180,270])for(const roll of [-35,0,25]){
  const o=orientation(roll,angle);assert.ok(Math.abs(delta(rollFromOrientation(o.beta,o.gamma,angle),roll))<1e-8);
 }
});
test('invalid readings and a flat phone cannot create steering',()=>{
 assert.equal(rollFromOrientation(null,0),null);assert.equal(rollFromOrientation(NaN,20),null);
 assert.equal(rollFromOrientation(0,0),null);assert.equal(rollFromOrientation(0,Infinity),null);
});
test('sensor input remains neutral until explicitly calibrated',()=>{
 const tilt=new TiltSteering();tilt.enable();assert.equal(sample(tilt,15,0).state,'calibrate');
 assert.equal(tilt.filtered,0);assert.equal(tilt.calibrate(),true);assert.equal(sample(tilt,15,16).value,0);
});
test('neutral position, dead zone and full-turn clamping work',()=>{
 const tilt=new TiltSteering();tilt.smoothingMs=0;tilt.enable();sample(tilt,10,0);tilt.calibrate();
 assert.equal(sample(tilt,11,16).value,0);assert.equal(sample(tilt,60,32).value,1);
 assert.equal(sample(tilt,-40,48).value,-1);
});
test('smoothing is time based, bounded, and converges without overshoot',()=>{
 const tilt=new TiltSteering();tilt.enable();sample(tilt,0,0);tilt.calibrate();
 const first=sample(tilt,30,16).value;assert.ok(first>0&&first<1);
 for(let now=32;now<600;now+=16)sample(tilt,30,now);
 assert.ok(tilt.filtered>.99&&tilt.filtered<=1);
});
test('inversion and runtime recalibration are explicit',()=>{
 const tilt=new TiltSteering();tilt.smoothingMs=0;tilt.invert=true;tilt.enable();sample(tilt,0,0);tilt.calibrate();
 assert.ok(sample(tilt,20,16).value<0);assert.equal(tilt.calibrate(),true);assert.equal(sample(tilt,20,32).value,0);
});
test('screen rotation invalidates calibration and stale sensors are detected',()=>{
 const tilt=new TiltSteering();tilt.enable();sample(tilt,0,0);tilt.calibrate();sample(tilt,20,20);
 assert.equal(sample(tilt,20,40,90).state,'calibrate');assert.equal(tilt.filtered,0);
 assert.equal(tilt.stale(900),true);tilt.stop();assert.equal(tilt.stale(1000),false);
});
test('angular wraparound takes the small turn across the boundary',()=>{
 assert.ok(Math.abs(delta(-179,179)-2)<1e-8);assert.ok(Math.abs(delta(179,-179)+2)<1e-8);
});
