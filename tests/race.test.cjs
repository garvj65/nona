const {test}=require('node:test'),assert=require('node:assert/strict');
const {TRACK,createRace,trackPosition,checkpoint,step}=require('../web/race-physics.js');
function run(state,controls,seconds){for(let t=0;t<seconds;t+=1/60)step(state,controls,1/60);return state;}
test('parked, unstarted and paused races do not move or advance lap time',()=>{
 const race=createRace();run(race,{gas:true},1);assert.equal(race.speed,0);assert.equal(race.elapsed,0);
 race.running=true;race.paused=true;run(race,{gas:true},1);assert.equal(race.x,600);assert.equal(race.lapTime,0);
});
test('gas accelerates and combined gas/brake gives braking priority',()=>{
 const race=createRace();race.running=true;run(race,{gas:true},1);assert.ok(race.speed>100);
 const speed=race.speed;run(race,{gas:true,brake:true},.25);assert.ok(race.speed<speed);
});
test('nitro consumes a finite reserve and accelerates faster',()=>{
 const normal=createRace(),boost=createRace();normal.running=boost.running=true;
 run(normal,{gas:true},1);run(boost,{gas:true,nitro:true},1);
 assert.ok(boost.speed>normal.speed);assert.ok(boost.boost<75);assert.ok(boost.boost>=0);
 run(boost,{brake:true},1);assert.ok(boost.boost>70);
});
test('steering is proportional and wheel return stops angular change',()=>{
 const full=createRace(),half=createRace();full.running=half.running=true;full.speed=half.speed=100;
 step(full,{steering:1},.1);step(half,{steering:.5},.1);
 assert.ok(Math.abs(full.heading-half.heading*2)<1e-8);
 const heading=full.heading;step(full,{steering:0},.1);assert.equal(full.heading,heading);
});
test('grass reduces speed and returning to asphalt removes offroad flag',()=>{
 const race=createRace();race.running=true;race.x=600;race.y=350;race.speed=260;
 step(race,{gas:true},.1);assert.equal(race.offroad,true);assert.ok(race.speed<=105);
 race.x=600;race.y=570;step(race,{},.01);assert.equal(race.offroad,false);
});
test('crossing finish without ordered checkpoints cannot count a lap',()=>{
 const race=createRace();race.x=610;race.y=570;race.lapTime=30;checkpoint(race);
 assert.equal(race.laps,0);assert.equal(race.checkpoint,1);
 race.x=600;race.y=350;checkpoint(race);assert.equal(race.laps,0);
});
test('all four ordered checkpoints count one lap and preserve best time',()=>{
 const race=createRace();race.lapTime=24;
 for(const progress of [Math.PI/2+.01,Math.PI+.01,Math.PI*1.5+.01,.01]){
  const angle=Math.PI/2-progress;race.x=TRACK.cx+Math.cos(angle)*TRACK.rx;race.y=TRACK.cy+Math.sin(angle)*TRACK.ry;checkpoint(race);
 }
 assert.equal(race.laps,1);assert.equal(race.lastLap,24);assert.equal(race.bestLap,24);assert.equal(race.lapTime,0);
});
test('large or invalid frame gaps cannot teleport the car',()=>{
 const race=createRace();race.running=true;race.speed=200;const before=race.x;
 step(race,{gas:true},100);assert.ok(race.x-before<35);assert.ok(race.elapsed<=.101);
 const snapshot=JSON.stringify(race);step(race,{gas:true},NaN);assert.equal(JSON.stringify(race),snapshot);
});
test('reset creates a fresh race without sharing mutable state',()=>{
 const a=createRace(),b=createRace();a.speed=200;a.laps=3;assert.equal(b.speed,0);assert.equal(b.laps,0);
 assert.ok(trackPosition(600,570).distance<1);assert.ok(trackPosition(600,350).distance>100);
});
