const $ = id => document.getElementById(id);
const fromHash = location.hash.slice(1);
let token = fromHash;
try {
  if (fromHash) sessionStorage.setItem('pocketpad-token', fromHash);
  else token = sessionStorage.getItem('pocketpad-token') || '';
} catch {}
if (fromHash) history.replaceState(null, '', location.pathname);
let socket = null, seq = 0, retry = null, backoff = 1200, wakeLock = null, stopped = false;
let steering = 0, wheelPointer = null, profile = null, revision = null, catalogue = "";
const axes = {lx:0,ly:0,rx:0,ry:0,lt:0,rt:0};
const tilt=new NonaMotion.TiltSteering();
const gyro=new NonaMobile.GyroLook();
let mobileLook=false,lookPointer=null,lookDX=0,lookDY=0,gyroStarted=0,gyroNote='Swipe to look. Gyro assist works while touching the look area.';
let dirty=false,lastSent=0;
const stickOrigins=new Map();
let motionStarted=0,motionNote='Touch steering selected.';
const sticks = new Map();
const pointers = new Map(), pending = new Map();
const wsScheme = location.protocol === 'https:' ? 'wss' : 'ws';
function buttons() { return [...new Set(pointers.values())]; }
function render() {
  document.querySelectorAll('[data-button]').forEach(el => el.classList.toggle('pressed', buttons().includes(el.dataset.button)));
  $('wheel-face').style.transform = `rotate(${steering * 65}deg)`;
  $('wheel').setAttribute('aria-valuenow', String(Math.round(steering * 100)));
}
function send(extra = {}) {
  if (socket?.readyState !== WebSocket.OPEN) return;
  if(socket.bufferedAmount>4096){stopped=true;clearInputs();socket.close();return;}
  const packet = { seq: seq++, buttons: buttons(), steering, axes: {...axes},
    pointer:{dx:lookDX,dy:lookDY,active:mobileLook&&lookPointer!==null}, ...extra };
  lookDX=lookDY=0;dirty=false;lastSent=performance.now();
  pending.set(packet.seq, performance.now());
  if (pending.size > 40) pending.delete(pending.keys().next().value);
  socket.send(JSON.stringify(packet));
}
function queueSend(){dirty=true;}
function addLook(dx,dy){lookDX=NonaMobile.clamp(lookDX+dx,-96,96);lookDY=NonaMobile.clamp(lookDY+dy,-96,96);queueSend();}
function clearInputs() { stopMotion(); stopGyro(); pointers.clear(); lookPointer=null;lookDX=lookDY=0;steering = 0; wheelPointer = null; sticks.clear();stickOrigins.clear(); for(const key of Object.keys(axes)) axes[key]=0; document.querySelectorAll('[data-trigger]').forEach(el=>el.value='0'); for(const id of ['left-stick','right-stick']) {$(id).querySelector('.stick-thumb').style.transform='translate(0px, 0px)';$(id).style.removeProperty('--stick-x');$(id).style.removeProperty('--stick-y');} render(); }
function release() { clearInputs(); send(); }
function configure(config) {
  if (!config.profile) return;
  const signature=JSON.stringify(config.profiles);
  if(catalogue!==signature){catalogue=signature;$('controller-profile').replaceChildren(...config.profiles.map(item=>{const option=document.createElement('option');option.value=item.id;option.textContent=item.name;return option;}));}
  if (profile !== config.profile || revision !== config.revision) {
    clearInputs(); profile = config.profile; revision=config.revision;
    $('controller-profile').value = profile;
    const racing = config.layout === 'racing', dual = config.layout === 'dualstick';
    mobileLook=dual&&config.output_mode==='keyboard'&&!!config.look?.enabled;
    document.body.classList.toggle('mobile-look',mobileLook);
    $('look-settings').classList.toggle('hidden',!mobileLook);
    $('move-label').textContent=mobileLook?'TOUCH + DRAG TO MOVE':'MOVE / LEFT STICK';
    $('look-label').textContent=mobileLook?'SWIPE TO LOOK':'LOOK / RIGHT STICK';
    document.body.classList.toggle('racing-layout', racing);
    document.body.classList.toggle('dualstick-layout', dual);
    $('gamepad-controls').classList.toggle('hidden', racing||dual);
    $('racing-controls').classList.toggle('hidden', !racing);
    $('dualstick-controls').classList.toggle('hidden', !dual);
    $('shoulders').classList.toggle('hidden', racing||mobileLook);
    $('motion-panel').classList.toggle('hidden', !racing);
    $('controller-help').textContent=mobileLook?'Left thumb moves; swipe the right area to look. A jumps. Gyro assist adds camera motion while holding the look area.':racing?'Choose touch or tilt steering. Gas and Brake stay under your thumbs.':'Use both thumbs for simultaneous controls. Load a saved game profile to recall its bindings.';
  }
  const mapping=config.output_mode==='gamepad'?config.pad_mapping:config.mapping;
  document.querySelectorAll('[data-button]').forEach(el=>{const hint=el.querySelector('span');if(hint)hint.textContent=mapping[el.dataset.button]||'Unmapped';});
  if(mobileLook){
    const labels={a:'Jump',b:'Run',x:'Use',y:'Action'};
    document.querySelectorAll('#dualstick-controls [data-button]').forEach(el=>{const hint=el.querySelector('span');if(hint)hint.textContent=labels[el.dataset.button]||'';});
  }
  $('bridge-status').textContent = `${config.output_mode==='gamepad'?'Xbox':'Keys'} ${config.armed?'ON':'off'}`;
}

function state(connected, text) {
  document.body.classList.toggle('offline', !connected);
  $('connection').classList.toggle('connected', connected); $('status').textContent = text;
}
async function awake() {
  try {
    if ('wakeLock' in navigator && !wakeLock) {
      wakeLock = await navigator.wakeLock.request('screen');
      wakeLock.addEventListener('release', () => wakeLock = null);
    }
  } catch {}
}
function connect() {
  clearTimeout(retry);
  if (!token) { state(false, 'Not paired'); $('message').textContent = 'Scan the QR code on your laptop dashboard to pair this phone.'; return; }
  if (socket && socket.readyState < 2) return;
  stopped = false; seq = 0; pending.clear(); clearInputs(); state(false, 'Connecting…');
  const current = new WebSocket(`${wsScheme}://${location.host}/ws/controller?token=${encodeURIComponent(token)}`); socket = current;
  current.onopen = () => {
    if (socket !== current) return;
    state(true, 'Connected'); $('message').textContent = 'Ready. Select the game profile you want and keep this page visible.';
    backoff = 1200; send(); awake();
  };
  current.onmessage = event => {
    const packet = JSON.parse(event.data);
    if (packet.type === 'ack') {
      configure(packet);
      if (pending.has(packet.seq)) {
        $('latency').textContent = `RTT ${Math.round(performance.now() - pending.get(packet.seq))} ms`;
        pending.delete(packet.seq);
      }
    }
  };
  current.onclose = event => {
    if (socket !== current) return;
    clearInputs(); state(false, 'Disconnected'); $('latency').textContent = 'RTT —';
    $('message').textContent = event.code === 1008 ? 'Pairing unavailable. Close other controller tabs and scan the current laptop QR code.' : 'Connection interrupted or pairing link expired. Check NONA is running, close other controller tabs, and scan its current QR code.';
    if (!stopped && !document.hidden && event.code !== 1008) {
      retry = setTimeout(connect, backoff); backoff = Math.min(backoff * 1.5, 6000);
    }
  };
  current.onerror = () => {};
}
document.querySelectorAll('[data-button]').forEach(el => {
  el.addEventListener('contextmenu', event => event.preventDefault());
  el.addEventListener('pointerdown', event => {
    if (socket?.readyState !== WebSocket.OPEN) return;
    event.preventDefault(); el.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, el.dataset.button); render(); send(); awake();
    if (navigator.vibrate) navigator.vibrate(8);
  });
  const end = event => { if (pointers.delete(event.pointerId)) { render(); send(); } };
  el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end); el.addEventListener('lostpointercapture', end);
  el.addEventListener('pointermove', event => {
    if (!pointers.has(event.pointerId)) return;
    const rect = el.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) end(event);
  });
});
const wheel = $('wheel');
function moveWheel(event, force = false) {
  const rect = wheel.getBoundingClientRect();
  steering = Math.max(-1, Math.min(1, (event.clientX - (rect.left + rect.width / 2)) / (rect.width * 0.43)));
  render();
  if(force)send();else queueSend();
}
wheel.addEventListener('pointerdown', event => {
  if (socket?.readyState !== WebSocket.OPEN || wheelPointer !== null || tilt.enabled) return;
  event.preventDefault(); wheelPointer = event.pointerId; wheel.setPointerCapture(event.pointerId); moveWheel(event, true); awake();
});
wheel.addEventListener('pointermove', event => { if (wheelPointer === event.pointerId) moveWheel(event); });
function centreWheel(event) { if (wheelPointer === event.pointerId) { wheelPointer = null; steering = 0; render(); send(); } }
for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) wheel.addEventListener(type, centreWheel);
wheel.addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight', 'Home'].includes(event.key)) return;
  event.preventDefault(); steering = event.key === 'Home' ? 0 : event.key === 'ArrowLeft' ? -1 : 1; render(); send();
});
wheel.addEventListener('keyup', event => { if (['ArrowLeft', 'ArrowRight'].includes(event.key)) { steering = 0; render(); send(); } });
for(const [id,x,y] of [['left-stick','lx','ly'],['right-stick','rx','ry']]){
  const el=$(id);
  el.addEventListener('contextmenu',event=>event.preventDefault());
  const move=event=>{
    if(mobileLook&&id==='right-stick'){
      if(!lookPointer||lookPointer.id!==event.pointerId)return;
      const gain=Number($('look-gain').value);
      addLook((event.clientX-lookPointer.x)*gain,(event.clientY-lookPointer.y)*gain);
      lookPointer.x=event.clientX;lookPointer.y=event.clientY;return;
    }
    const rect=el.getBoundingClientRect(),radius=rect.width*.38;
    let dx=(event.clientX-rect.left-rect.width/2)/radius,dy=(event.clientY-rect.top-rect.height/2)/radius;
    if(mobileLook&&id==='left-stick'){
      const origin=stickOrigins.get(id);if(!origin)return;
      const value=NonaMobile.floatingStick(event.clientX,event.clientY,origin.x,origin.y,Math.min(rect.width,rect.height)*.34);
      dx=value.x;dy=value.y;
    }else{const length=Math.hypot(dx,dy);if(length>1){dx/=length;dy/=length;}}
    axes[x]=dx;axes[y]=dy;el.querySelector('.stick-thumb').style.transform=`translate(${dx*radius*.6}px, ${dy*radius*.6}px)`;
    queueSend();
  };
  el.addEventListener('pointerdown',event=>{
    if(socket?.readyState!==WebSocket.OPEN||sticks.has(id))return;
    event.preventDefault();sticks.set(id,event.pointerId);el.setPointerCapture(event.pointerId);
    if(mobileLook){
      if(id==='right-stick')lookPointer={id:event.pointerId,x:event.clientX,y:event.clientY};
      else{const rect=el.getBoundingClientRect();stickOrigins.set(id,{x:event.clientX,y:event.clientY});el.style.setProperty('--stick-x',`${event.clientX-rect.left}px`);el.style.setProperty('--stick-y',`${event.clientY-rect.top}px`);}
    }
    move(event);send();awake();
  });
  el.addEventListener('pointermove',event=>{if(sticks.get(id)===event.pointerId)move(event);});
  const end=event=>{if(sticks.get(id)!==event.pointerId)return;sticks.delete(id);stickOrigins.delete(id);if(id==='right-stick'){lookPointer=null;lookDX=lookDY=0;}axes[x]=axes[y]=0;el.querySelector('.stick-thumb').style.transform='translate(0px, 0px)';el.style.removeProperty('--stick-x');el.style.removeProperty('--stick-y');send();};
  for(const type of ['pointerup','pointercancel','lostpointercapture'])el.addEventListener(type,end);
  el.addEventListener('keydown',event=>{const values={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};if(!values[event.key])return;event.preventDefault();[axes[x],axes[y]]=values[event.key];send();});
  el.addEventListener('keyup',event=>{if(event.key.startsWith('Arrow')){axes[x]=axes[y]=0;send();}});
}
document.querySelectorAll('[data-trigger]').forEach(el=>{
  el.addEventListener('input',()=>{axes[el.dataset.trigger]=Number(el.value);queueSend();});
  for(const type of ['pointerup','pointercancel','blur','keyup'])el.addEventListener(type,()=>{axes[el.dataset.trigger]=0;el.value='0';send();});
});
function screenAngle(){return Number(screen.orientation?.angle ?? window.orientation ?? 0);}
function motionUI(){
  document.body.classList.toggle('motion-active',tilt.enabled);
  $('enable-motion').disabled=tilt.enabled;
  $('calibrate-motion').disabled=!tilt.enabled||tilt.angle===null;
  $('motion-status').textContent=motionNote;
}
function stopMotion(note='Touch steering selected.'){
  window.removeEventListener('deviceorientation',onMotion);
  tilt.stop();motionNote=note;motionUI();
}
function motionFault(note){release();motionNote=note;motionUI();send({disarm:true});}
function onMotion(event){
  if(!tilt.enabled)return;
  const wasCalibrated=tilt.calibrated;
  const result=tilt.sample(event.beta,event.gamma,screenAngle(),performance.now());
  if(wasCalibrated&&!tilt.calibrated){motionFault('Motion changed or became unstable. Hold the phone upright, enable tilt, then recalibrate.');return;}
  steering=result.value;render();
  motionNote=result.state==='hold-upright'?'Hold the screen more upright, facing you.':result.state==='calibrate'?'Hold your neutral position and tap Calibrate.':`Tilt active · ${result.offset.toFixed(1)}° · steering ${Math.round(steering*100)}%`;
  motionUI();
  queueSend();
}
$('enable-motion').onclick=async()=>{
  release();send({disarm:true});
  if(!window.isSecureContext){motionNote='Tilt needs trusted HTTPS on the phone. Open the setup instructions below.';motionUI();return;}
  if(!window.DeviceOrientationEvent){motionNote='This browser does not expose orientation sensors. Touch controls remain available.';motionUI();return;}
  try{
    if(typeof DeviceOrientationEvent.requestPermission==='function'){
      const permission=await DeviceOrientationEvent.requestPermission();
      if(permission!=='granted')throw new Error('Motion permission was not granted. Use touch or enable sensor access in browser settings.');
    }
    tilt.enable();motionStarted=performance.now();motionNote='Waiting for a sensor reading…';motionUI();
    window.addEventListener('deviceorientation',onMotion);awake();
  }catch(error){motionNote=error.message;motionUI();}
};
$('calibrate-motion').onclick=()=>{
  if(!tilt.calibrate())return;
  pointers.clear();for(const key of Object.keys(axes))axes[key]=0;
  steering=0;render();send({disarm:true});
  motionNote='Calibrated. Tilt to steer. Re-enable laptop output for an external game.';motionUI();
};
$('disable-motion').onclick=()=>{release();send({disarm:true});};
$('invert-motion').onchange=()=>{tilt.invert=$('invert-motion').checked;steering=0;tilt.filtered=0;send();};
$('motion-range').onchange=()=>{tilt.range=Number($('motion-range').value);tilt.filtered=0;steering=0;send();};
function gyroUI(){
  $('enable-gyro').disabled=gyro.enabled;
  $('gyro-status').textContent=gyroNote;
  document.body.classList.toggle('gyro-active',gyro.enabled);
}
function stopGyro(note='Swipe to look. Gyro assist works while touching the look area.'){
  window.removeEventListener('devicemotion',onGyro);gyro.stop();gyroNote=note;gyroUI();
}
function onGyro(event){
  if(!gyro.enabled)return;
  const delta=gyro.sample(event.rotationRate,screenAngle(),performance.now(),lookPointer!==null);
  if(lookPointer){const invert=$('gyro-invert').checked?-1:1;addLook(delta.dx,delta.dy*invert);}
  if(gyro.lastSample!==null){gyroNote=lookPointer?'Gyro assist active · swipe and motion combine.':'Gyro ready · hold the look area to aim.';gyroUI();}
}
$('enable-gyro').onclick=async()=>{
  release();send({disarm:true});
  if(!window.isSecureContext){gyroNote='Gyro needs trusted HTTPS. Swipe look works without motion sensors.';gyroUI();return;}
  if(!window.DeviceMotionEvent){gyroNote='Gyroscope unavailable in this browser. Swipe look remains available.';gyroUI();return;}
  try{
    if(typeof DeviceMotionEvent.requestPermission==='function'&&await DeviceMotionEvent.requestPermission()!=='granted')throw new Error('Gyro permission was not granted. Swipe look remains available.');
    if(!mobileLook||socket?.readyState!==WebSocket.OPEN)return;
    gyro.enable();gyroStarted=performance.now();gyroNote='Waiting for gyroscope…';gyroUI();window.addEventListener('devicemotion',onGyro);awake();
  }catch(error){gyroNote=error.message;gyroUI();}
};
$('disable-gyro').onclick=()=>{release();send({disarm:true});};
$('gyro-invert').onchange=()=>{gyro.filtered={x:0,y:0};lookDX=lookDY=0;};
setInterval(()=>{
  if(gyro.enabled&&(gyro.stale(performance.now())||(gyro.lastSample===null&&performance.now()-gyroStarted>4000))){
    release();send({disarm:true});gyroNote='Gyro readings stopped. Inputs released; use touch or enable gyro again.';gyroUI();
  }
  if(!tilt.enabled)return;
  if(tilt.stale(performance.now()))motionFault('Motion sensor stopped. Inputs released; use touch or enable tilt again.');
  else if(tilt.lastSample===null&&performance.now()-motionStarted>4000)motionFault('No usable sensor readings. Check sensor support, permission, and how you hold the phone.');
},100);
$('controller-profile').onchange = () => { release(); send({ profile: $('controller-profile').value }); };
// Coalesce continuous input into 50 Hz packets; button down/up still send immediately.
setInterval(() => { if (!document.hidden&&(dirty||performance.now()-lastSent>=100)) send(); }, 20);
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { release(); stopped = true; clearTimeout(retry); socket?.close(); }
  else { connect(); awake(); }
});
window.addEventListener('pagehide', () => { release(); stopped = true; socket?.close(); });
window.addEventListener('blur', release); window.addEventListener('orientationchange', release);
$('release').onclick = () => {release();send({disarm:true});};
$('reconnect').onclick = () => { release(); stopped = true; clearTimeout(retry); const old = socket; socket = null; old?.close(); setTimeout(connect, 250); };
$('fullscreen').onclick = async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen();
    $('fullscreen').textContent = document.fullscreenElement ? 'Exit fullscreen' : 'Fullscreen';
  } catch { $('message').textContent = 'Fullscreen is unavailable. Turn your phone sideways for the wider layout.'; }
};
state(false, 'Connecting…'); connect();
