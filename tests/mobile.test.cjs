const {test}=require('node:test'),assert=require('node:assert/strict');
const {floatingStick,GyroLook}=require('../web/mobile-input.js');
test('floating stick is neutral at its touch origin and clamps diagonals to a circle',()=>{
 assert.deepEqual(floatingStick(120,90,120,90,50),{x:0,y:0});
 assert.deepEqual(floatingStick(122,91,120,90,50),{x:0,y:0});
 const diagonal=floatingStick(220,-10,120,90,50);
 assert.ok(diagonal.x>0&&diagonal.y<0);assert.ok(Math.abs(Math.hypot(diagonal.x,diagonal.y)-1)<1e-9);
});
test('floating origin gives the same response anywhere on the surface',()=>{
 assert.deepEqual(floatingStick(25,40,10,20,50),floatingStick(225,340,210,320,50));
});
test('gyro is neutral unless explicitly enabled and the look clutch is held',()=>{
 const gyro=new GyroLook();const rate={alpha:30,beta:60};
 assert.deepEqual(gyro.sample(rate,0,10,true),{dx:0,dy:0});
 gyro.enable();gyro.sample(rate,0,20,false);
 assert.deepEqual(gyro.sample(rate,0,40,false),{dx:0,dy:0});
 const active=gyro.sample(rate,0,60,true);assert.ok(active.dx>0&&active.dy>0);
 gyro.sample(rate,0,80,false);assert.deepEqual(gyro.filtered,{x:0,y:0});
});
test('gyro rotates angular velocity into the display axes in both landscapes',()=>{
 const outputs=[];
 for(const angle of [0,90,270]){
  const s=angle*Math.PI/180,rate={alpha:-60*Math.sin(s),beta:60*Math.cos(s)};
  const gyro=new GyroLook();gyro.enable();gyro.sample(rate,angle,0,true);
  outputs.push(gyro.sample(rate,angle,20,true));
 }
 for(const value of outputs){assert.ok(Math.abs(value.dx-outputs[0].dx)<1e-9);assert.ok(Math.abs(value.dy)<1e-9);}
});
test('gyro rejects null/invalid readings and neutral noise',()=>{
 const gyro=new GyroLook();gyro.enable();
 for(const rate of [null,{alpha:null,beta:0},{alpha:Infinity,beta:3},{alpha:NaN,beta:0}]){
  assert.deepEqual(gyro.sample(rate,0,10,true),{dx:0,dy:0});assert.equal(gyro.lastSample,null);
 }
 gyro.sample({alpha:0,beta:0},0,0,true);
 assert.deepEqual(gyro.sample({alpha:.2,beta:-.3},0,20,true),{dx:0,dy:0});
});
test('gyro cannot jump on a frame gap or screen rotation and is bounded at extreme rates',()=>{
 const gyro=new GyroLook();gyro.enable();const rate={alpha:1e9,beta:-1e9};
 gyro.sample(rate,0,0,true);assert.deepEqual(gyro.sample(rate,0,1000,true),{dx:0,dy:0});
 assert.deepEqual(gyro.sample(rate,90,1020,true),{dx:0,dy:0});
 const next=gyro.sample(rate,90,1040,true);assert.ok(Math.abs(next.dx)<=48&&Math.abs(next.dy)<=48);
 assert.equal(gyro.stale(2000),true);gyro.stop();assert.equal(gyro.stale(2000),false);
});
