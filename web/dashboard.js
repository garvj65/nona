const $ = id => document.getElementById(id);
let admin = '', urls = [], socket, keyOptions = [], lastMapping = '';
const names = {up:'↑',down:'↓',left:'←',right:'→',a:'A / Gas',b:'B / Brake',start:'Start',select:'Select',handbrake:'Handbrake',nitro:'Nitro'};
function mappingEditor(mapping) {
  const signature=JSON.stringify(mapping);
  if(signature===lastMapping)return;
  lastMapping=signature;
  $('mapping-fields').replaceChildren(...Object.entries(mapping).map(([button,key])=>{
    const label=document.createElement('label'),select=document.createElement('select');
    label.textContent=names[button];select.dataset.action=button;select.setAttribute('aria-label',`${names[button]} key`);
    for(const value of ['',...keyOptions]){const option=document.createElement('option');option.value=value;option.textContent=value||'Disabled';select.append(option);}
    select.value=key;label.append(select);return label;
  }));
}
function showError(text='') { $('error').textContent=text; $('error').classList.toggle('hidden',!text); }
function display(status) {
  $('connection').classList.toggle('connected',status.connected);
  $('connection-text').textContent=status.connected?'Phone connected':'Waiting for phone';
  $('profile').value=status.profile;
  mappingEditor(status.mapping);
  $('enable').disabled=!status.connected || !status.keyboard_available || !!status.countdown || status.armed;
  $('keyboard-state').textContent=status.countdown?`Select your game · ${Math.ceil(status.countdown)}s`:status.armed?'Keyboard ON':'Desktop keyboard off';
  $('note').textContent=status.note+(status.target?` Target: ${status.target}`:'');
  if(!status.keyboard_available) $('note').textContent='Demo mode is available here. Desktop keyboard mode requires Windows.';
  $('keys').replaceChildren(...Object.entries(status.mapping).map(([button,key])=>{
    const el=document.createElement('span');el.className='key'+(status.buttons.includes(button)?' on':'');el.textContent=`${names[button]} → ${key||'off'}`;return el;
  }));
  if(status.error) showError(status.error);
}
function selectNetwork(index) { $('pair-url').value=urls[index]||''; $('qr').src=`/api/qr?index=${index}`; }
async function post(path,data) {
  showError();
  try {
    const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-PocketPad-Admin':admin},body:JSON.stringify(data)});
    const body=await response.json();
    if(!response.ok) throw new Error(body.detail||'Request failed');
    display(body);
  } catch(error) { showError(error.message); }
}
function monitor() {
  socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/monitor`);
  socket.onmessage=event=>display(JSON.parse(event.data));
  socket.onclose=()=>{
    $('connection').classList.remove('connected');$('connection-text').textContent='Laptop server offline';
    $('enable').disabled=true;setTimeout(monitor,1500);
  };
}
$('enable').onclick=()=>post('/api/keyboard',{enabled:true});
$('disable').onclick=()=>post('/api/keyboard',{enabled:false});
$('profile').onchange=()=>post('/api/profile',{profile:$('profile').value});
$('save-mapping').onclick=()=>{
  const mapping=Object.fromEntries([...document.querySelectorAll('#mapping-fields select')].map(el=>[el.dataset.action,el.value]));
  post('/api/mapping',{mapping});
};
$('network').onchange=()=>selectNetwork(Number($('network').value));
$('copy').onclick=async()=>{
  try { await navigator.clipboard.writeText($('pair-url').value);$('copy').textContent='Copied';setTimeout(()=>$('copy').textContent='Copy',1400); }
  catch { $('pair-url').select();$('copy').textContent='Select + copy'; }
};
$('qr').onerror=()=>{ $('pair-error').textContent='QR unavailable. Copy or type the pairing address into Chrome on your phone.';$('pair-error').classList.remove('hidden'); };
fetch('/api/session').then(async r=>{if(!r.ok)throw new Error('Could not load pairing details.');return r.json();}).then(data=>{
  admin=data.admin;urls=data.urls;keyOptions=data.key_options;display(data);
  if(urls.length) {
    selectNetwork(0);
    if(urls.length>1){$('network').classList.remove('hidden');urls.forEach((url,index)=>{const option=document.createElement('option');option.value=index;option.textContent=new URL(url).hostname;$('network').append(option);});}
  } else { $('pair-error').textContent='No network address found. Connect the laptop to Wi-Fi and restart PocketPad.';$('pair-error').classList.remove('hidden');$('qr').classList.add('hidden'); }
  monitor();
}).catch(error=>showError(error.message));
