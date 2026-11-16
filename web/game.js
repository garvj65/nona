const $=id=>document.getElementById(id),canvas=$('game'),ctx=canvas.getContext('2d');
const W=960,H=480,ship={x:480,y:390,r:14};
let remote=new Set(),physical=new Set(),previous=new Set(),pressed=new Set(),connected=false,started=false,paused=false,over=false;
let elapsed=0,best=0,last=0,spawn=0,blocks=[],gridOffset=0;
try{best=Number(localStorage.getItem('pocketpad-neon-best')||0);if(!Number.isFinite(best))best=0;}catch{}
$('best').textContent=`${best.toFixed(1)}s`;
const keyMap={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',KeyW:'up',KeyS:'down',KeyA:'left',KeyD:'right',Space:'a',KeyX:'b',Enter:'start',KeyP:'select'};
window.addEventListener('keydown',event=>{if(keyMap[event.code]){event.preventDefault();physical.add(event.code);captureEdges();}});
window.addEventListener('keyup',event=>{physical.delete(event.code);captureEdges();});
window.addEventListener('blur',()=>{physical.clear();captureEdges();});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&started&&!over){paused=true;physical.clear();overlay('Run paused','Return to the game and press Start to resume.','Resume');}});
function input(){return new Set([...remote,...[...physical].map(code=>keyMap[code])]);}
function captureEdges(){const next=input();for(const button of next)if(!previous.has(button))pressed.add(button);previous=next;}
function overlay(title,text,button){$('overlay').classList.remove('hidden');$('overlay-title').textContent=title;$('overlay-text').textContent=text;$('play').textContent=button;}
function reset(){elapsed=0;spawn=0;blocks=[];ship.x=W/2;ship.y=H-80;started=true;paused=false;over=false;$('overlay').classList.add('hidden');}
function play(){if(!started||over)reset();else{paused=!paused;if(paused)overlay('Run paused','Press Start on your phone to keep going.','Resume');else $('overlay').classList.add('hidden');}}
$('play').onclick=play;
function finish(){over=true;best=Math.max(best,elapsed);$('best').textContent=`${best.toFixed(1)}s`;try{localStorage.setItem('pocketpad-neon-best',String(best));}catch{}overlay('One more run?',`You survived ${elapsed.toFixed(1)} seconds. Press A or Start to try again.`,'Play again');}
function monitor(){
  const ws=new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/monitor`);
  ws.onmessage=event=>{const data=JSON.parse(event.data),wasConnected=connected;connected=data.connected;remote=new Set(data.buttons);captureEdges();$('connection').classList.toggle('connected',connected);$('phone-status').textContent=connected?'Phone connected':'Waiting for phone';if(wasConnected&&!connected&&started&&!over){paused=true;overlay('Phone disconnected','Reconnect your phone, then press Start to resume.','Resume');}};
  ws.onclose=()=>{remote.clear();connected=false;$('connection').classList.remove('connected');$('phone-status').textContent='Laptop server offline';if(started&&!over){paused=true;overlay('Connection paused','Restart PocketPad, reconnect the phone, then resume.','Resume');}setTimeout(monitor,1500);};
}
function update(dt){
  const active=input();
  if(pressed.has('select'))reset();
  else if(pressed.has('start'))play();
  else if(pressed.has('a')&&(!started||over))reset();
  pressed.clear();
  if(!started||paused||over)return;
  elapsed+=dt;gridOffset=(gridOffset+dt*90)%40;spawn+=dt;
  let dx=Number(active.has('right'))-Number(active.has('left')),dy=Number(active.has('down'))-Number(active.has('up'));
  const length=Math.hypot(dx,dy)||1,speed=active.has('b')?155:active.has('a')?440:275;
  ship.x=Math.max(34,Math.min(W-34,ship.x+dx/length*speed*dt));ship.y=Math.max(35,Math.min(H-30,ship.y+dy/length*speed*dt));
  if(spawn>Math.max(.26,.85-elapsed*.006)){spawn=0;blocks.push({x:30+Math.random()*(W-100),y:-50,w:35+Math.random()*55,h:25+Math.random()*25,speed:125+Math.min(elapsed*3,180)});}
  for(const block of blocks){block.y+=block.speed*dt;const nx=Math.max(block.x,Math.min(ship.x,block.x+block.w)),ny=Math.max(block.y,Math.min(ship.y,block.y+block.h));if(Math.hypot(ship.x-nx,ship.y-ny)<ship.r-2){finish();break;}}
  blocks=blocks.filter(block=>block.y<H+60);$('score').textContent=`${elapsed.toFixed(1)}s`;
}
function draw(){
  ctx.fillStyle='#101b22';ctx.fillRect(0,0,W,H);ctx.lineWidth=1;ctx.strokeStyle='#20333b';
  for(let x=0;x<=W;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
  for(let y=gridOffset-40;y<=H;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  ctx.fillStyle='#c0f974';ctx.globalAlpha=.18;ctx.fillRect(17,0,2,H);ctx.fillRect(W-19,0,2,H);ctx.globalAlpha=1;
  ctx.fillStyle='#b2a0ff';for(const block of blocks){ctx.fillRect(block.x,block.y,block.w,block.h);ctx.fillStyle='#d6ceff';ctx.fillRect(block.x,block.y,block.w,3);ctx.fillStyle='#b2a0ff';}
  ctx.save();ctx.translate(ship.x,ship.y);ctx.fillStyle='#c0f974';ctx.shadowColor='#c0f974';ctx.shadowBlur=18;ctx.beginPath();ctx.moveTo(0,-19);ctx.lineTo(15,14);ctx.lineTo(0,7);ctx.lineTo(-15,14);ctx.closePath();ctx.fill();ctx.shadowBlur=0;ctx.fillStyle='#304921';ctx.fillRect(-3,-4,6,10);ctx.restore();
}
function frame(now){const dt=Math.min((now-last)/1000||0,.04);last=now;update(dt);draw();requestAnimationFrame(frame);}
monitor();requestAnimationFrame(frame);
