const $ = id => document.getElementById(id), canvas = $('track'), ctx = canvas.getContext('2d');
const { TRACK, createRace, step } = NonaRace;
let race = createRace(), remote = new Set(), remoteSteering = 0, physical = new Set();
let previous = new Set(), edges = new Set(), connected = false, last = 0, best = null;
try { const saved = Number(localStorage.getItem('nona-sprint-best')); if (saved > 0 && Number.isFinite(saved)) best = saved; } catch {}
const keys = { ArrowLeft: 'left', KeyA: 'left', ArrowRight: 'right', KeyD: 'right',
  ArrowUp: 'a', KeyW: 'a', ArrowDown: 'b', KeyS: 'b', Space: 'handbrake',
  ShiftLeft: 'nitro', ShiftRight: 'nitro', Enter: 'start', KeyR: 'select' };
function input() { return new Set([...remote, ...[...physical].map(key => keys[key])]); }
function captureEdges() { const next = input(); for (const key of next) if (!previous.has(key)) edges.add(key); previous = next; }
function overlay(title, text, button = 'Resume') {
  $('overlay-title').textContent = title; $('overlay-text').textContent = text; $('play').textContent = button;
  $('overlay').classList.remove('hidden');
}
function pause(reason) { if (race.running) { race.paused = true; overlay('Engine on. Run paused.', reason); } }
function play() {
  if (!race.running) race.running = true;
  race.paused = false; $('overlay').classList.add('hidden');
}
function reset() { race = createRace(); previous = input(); edges.clear(); overlay('A fresh starting line.', 'Hold Gas or press Start on your phone to start a new run.', 'Start engine'); }
window.addEventListener('keydown', event => { if (keys[event.code]) { event.preventDefault(); physical.add(event.code); captureEdges(); } });
window.addEventListener('keyup', event => { physical.delete(event.code); captureEdges(); });
window.addEventListener('blur', () => { physical.clear(); captureEdges(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) { physical.clear(); captureEdges(); pause('Return to the track and press Start to resume.'); } });
$('play').onclick = play; $('reset').onclick = reset;
$('racing-profile').onclick = async () => {
  try {
    const response = await fetch('/api/session'); if (!response.ok) throw new Error('Open the game on the laptop.');
    const session = await response.json();
    const saved = await fetch('/api/profile', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-PocketPad-Admin': session.admin }, body: JSON.stringify({ profile: 'racing_arrows' }) });
    if (!saved.ok) throw new Error('Could not select racing controls.');
    $('mode-note').textContent = 'Racing controls selected on your phone. Keyboard is off; the demo uses direct input.';
  } catch (error) { $('mode-note').textContent = error.message; }
};
function monitor() {
  const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/monitor`);
  ws.onmessage = event => {
    const state = JSON.parse(event.data), wasConnected = connected;
    connected = state.connected; remote = new Set(state.buttons); remoteSteering = state.steering || 0; captureEdges();
    $('connection').classList.toggle('connected', connected); $('phone-status').textContent = connected ? 'Phone connected' : 'Waiting for phone';
    if (wasConnected && !connected) pause('Phone disconnected. Reconnect, then press Start.');
  };
  ws.onclose = () => { remote.clear(); remoteSteering = 0; connected = false; captureEdges(); $('connection').classList.remove('connected'); $('phone-status').textContent = 'Server offline'; pause('Restart NONA and reconnect your phone.'); setTimeout(monitor, 1500); };
}
function update(dt) {
  const active = input();
  if (edges.has('select')) reset();
  else if (edges.has('start')) { if (race.running && !race.paused) pause('Press Start to resume.'); else play(); }
  else if (edges.has('a') && !race.running) play();
  edges.clear();
  const keyboardSteer = Number([...physical].some(key => keys[key] === 'right')) - Number([...physical].some(key => keys[key] === 'left'));
  const buttonSteer = Number(remote.has('right')) - Number(remote.has('left'));
  const steering = keyboardSteer || remoteSteering || buttonSteer;
  step(race, { steering, gas: active.has('a') || active.has('up'), brake: active.has('b') || active.has('down'),
    handbrake: active.has('handbrake'), nitro: active.has('nitro') }, dt);
  if (race.bestLap !== null && (best === null || race.bestLap < best)) {
    best = race.bestLap; try { localStorage.setItem('nona-sprint-best', String(best)); } catch {}
  }
  $('speed').textContent = String(Math.round(race.speed * 0.7)); $('lap-time').textContent = race.lapTime.toFixed(2);
  $('best-lap').textContent = best === null ? '—' : best.toFixed(2); $('laps').textContent = String(race.laps);
  $('boost').textContent = `${Math.round(race.boost)}%`; $('surface').textContent = race.offroad ? 'Grass · reduced grip' : `Checkpoint ${race.checkpoint || 4} / 4`;
}
function ellipse(rx, ry) { ctx.beginPath(); ctx.ellipse(TRACK.cx, TRACK.cy, rx, ry, 0, 0, Math.PI * 2); }
function drawCar(x, y, heading, color) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(heading); ctx.fillStyle = '#0a0e13';
  ctx.fillRect(-14, -12, 9, 5); ctx.fillRect(6, -12, 9, 5); ctx.fillRect(-14, 7, 9, 5); ctx.fillRect(6, 7, 9, 5);
  ctx.fillStyle = color; ctx.fillRect(-18, -9, 36, 18); ctx.fillStyle = '#20323d'; ctx.fillRect(-3, -7, 12, 14);
  ctx.fillStyle = '#f0f9d6'; ctx.fillRect(14, -7, 3, 4); ctx.fillRect(14, 3, 3, 4); ctx.restore();
}
function draw() {
  ctx.fillStyle = '#1b3026'; ctx.fillRect(0, 0, 1200, 700);
  ctx.fillStyle = '#223a2d'; for (let x = 0; x < 1200; x += 60) for (let y = 0; y < 700; y += 60) if ((x + y) % 120 === 0) ctx.fillRect(x, y, 60, 60);
  ellipse(TRACK.rx, TRACK.ry); ctx.lineWidth = TRACK.width + 14; ctx.strokeStyle = '#e5dfc4'; ctx.stroke();
  ellipse(TRACK.rx, TRACK.ry); ctx.lineWidth = TRACK.width + 6; ctx.strokeStyle = '#bd6b63'; ctx.setLineDash([16, 16]); ctx.stroke(); ctx.setLineDash([]);
  ellipse(TRACK.rx, TRACK.ry); ctx.lineWidth = TRACK.width; ctx.strokeStyle = '#303a42'; ctx.stroke();
  ellipse(TRACK.rx, TRACK.ry); ctx.lineWidth = 2; ctx.strokeStyle = '#727a73'; ctx.setLineDash([20, 24]); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = '#a9bf9b'; ctx.textAlign = 'center'; ctx.font = '700 54px system-ui'; ctx.fillText('NONA', 600, 342);
  ctx.font = '12px system-ui'; ctx.fillStyle = '#849d7d'; ctx.fillText('SPRINT / LOCAL TIME ATTACK', 600, 372);
  for (let row = 0; row < 10; row++) for (let col = 0; col < 2; col++) { ctx.fillStyle = (row + col) % 2 ? '#111921' : '#e5ecdf'; ctx.fillRect(580 + col * 9, 514 + row * 11, 9, 11); }
  // Course arrows: left at the top, right at the bottom (counterclockwise).
  ctx.fillStyle = '#d6e0ce'; ctx.font = '28px system-ui'; ctx.fillText('←', 600, 132); ctx.fillText('→', 720, 580); ctx.fillText('↑', 1040, 350); ctx.fillText('↓', 160, 350);
  const ghostAngle = Math.PI / 2 - race.elapsed * 0.32;
  drawCar(TRACK.cx + Math.cos(ghostAngle) * TRACK.rx, TRACK.cy + Math.sin(ghostAngle) * TRACK.ry,
    Math.atan2(-TRACK.ry * Math.cos(ghostAngle), TRACK.rx * Math.sin(ghostAngle)), '#a79be4');
  drawCar(race.x, race.y, race.heading, '#c0f974');
  ctx.fillStyle = '#becbb7'; ctx.font = '10px system-ui'; ctx.textAlign = 'left'; ctx.fillText('VIOLET CAR = PACER / NO COLLISIONS', 30, 675);
}
function frame(now) { const dt = Math.min((now - last) / 1000 || 0, 0.05); last = now; update(dt); draw(); requestAnimationFrame(frame); }
monitor(); requestAnimationFrame(frame);
