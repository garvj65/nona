const $ = id => document.getElementById(id);
const fromHash = location.hash.slice(1);
let token = fromHash;
try {
  if (fromHash) sessionStorage.setItem('pocketpad-token', fromHash);
  else token = sessionStorage.getItem('pocketpad-token') || '';
} catch {}
if (fromHash) history.replaceState(null, '', location.pathname);
let socket = null, seq = 0, retry = null, backoff = 1200, wakeLock = null, stopped = false;
let steering = 0, wheelPointer = null, lastWheelSend = 0, profile = null;
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
  const packet = { seq: seq++, buttons: buttons(), steering, ...extra };
  pending.set(packet.seq, performance.now());
  if (pending.size > 40) pending.delete(pending.keys().next().value);
  socket.send(JSON.stringify(packet));
}
function clearInputs() { pointers.clear(); steering = 0; wheelPointer = null; render(); }
function release() { clearInputs(); send(); }
function configure(config) {
  if (!config.profile) return;
  if (profile !== config.profile) {
    clearInputs(); profile = config.profile;
    $('controller-profile').value = profile;
    const racing = config.layout === 'racing';
    document.body.classList.toggle('racing-layout', racing);
    $('gamepad-controls').classList.toggle('hidden', racing);
    $('racing-controls').classList.toggle('hidden', !racing);
  }
  $('select-hint').textContent = `${config.mapping?.select || 'off'} / Reset demo`;
  $('start-hint').textContent = `${config.mapping?.start || 'off'} / Pause`;
  $('bridge-status').textContent = config.armed ? 'Desktop keys ON' : 'Desktop keys off';
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
    state(true, 'Connected'); $('message').textContent = 'Ready. Choose Racing for the wheel and pedals. Keep this page open.';
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
    $('message').textContent = event.code === 1008 ? 'Pairing unavailable. Close any other controller tab, or rescan the laptop QR code.' : 'Connection lost. Keep both devices on the same Wi-Fi.';
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
  if (force || performance.now() - lastWheelSend > 25) { lastWheelSend = performance.now(); send(); }
}
wheel.addEventListener('pointerdown', event => {
  if (socket?.readyState !== WebSocket.OPEN || wheelPointer !== null) return;
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
$('controller-profile').onchange = () => { release(); send({ profile: $('controller-profile').value }); };
setInterval(() => { if (!document.hidden) send(); }, 100);
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { release(); stopped = true; clearTimeout(retry); socket?.close(); }
  else { connect(); awake(); }
});
window.addEventListener('pagehide', () => { release(); stopped = true; socket?.close(); });
window.addEventListener('blur', release); window.addEventListener('orientationchange', release);
$('release').onclick = release;
$('reconnect').onclick = () => { release(); stopped = true; clearTimeout(retry); const old = socket; socket = null; old?.close(); setTimeout(connect, 250); };
$('fullscreen').onclick = async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen();
    $('fullscreen').textContent = document.fullscreenElement ? 'Exit fullscreen' : 'Fullscreen';
  } catch { $('message').textContent = 'Fullscreen is unavailable. Turn your phone sideways for the wider layout.'; }
};
state(false, 'Connecting…'); connect();
