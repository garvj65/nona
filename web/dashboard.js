const $=id=>document.getElementById(id);
let admin='',urls=[],socket,keyOptions=[],padOptions=[],currentProfile='',catalogue='',lastMapping='',lastPad='',lastTuning='';
const names={up:'↑',down:'↓',left:'←',right:'→',a:'A / Gas',b:'B / Brake',x:'X',y:'Y',lb:'LB',rb:'RB',lt:'LT',rt:'RT',start:'Start',select:'Select',handbrake:'Handbrake',nitro:'Nitro'};
function editor(container,mapping,options){
  const complete={...Object.fromEntries(Object.keys(names).map(key=>[key,''])),...mapping};
  $(container).replaceChildren(...Object.entries(complete).map(([action,target])=>{
    const label=document.createElement('label'),select=document.createElement('select');label.textContent=names[action];
    select.dataset.action=action;select.setAttribute('aria-label',`${names[action]} binding`);
    for(const value of ['',...options]){const option=document.createElement('option');option.value=value;option.textContent=value||'Disabled';select.append(option);}
    select.value=target;label.append(select);return label;
  }));
}
function showError(text=''){$('error').textContent=text;$('error').classList.toggle('hidden',!text);}
function display(status){
  $('https-status').textContent=status.transport==='https'?'HTTPS running. The phone still needs to trust its certificate.':'HTTP running. Touch controls work; use the HTTPS launcher for phone motion.';
  $('ca-fingerprint').textContent=status.motion_https.prepared?`Public CA SHA-256: ${status.motion_https.sha256}`:'Local motion certificate not prepared yet.';
  $('connection').classList.toggle('connected',status.connected);$('connection-text').textContent=status.connected?'Phone connected':'Waiting for phone';
  const signature=JSON.stringify(status.profiles);
  if(catalogue!==signature){catalogue=signature;$('profile').replaceChildren(...status.profiles.map(profile=>{const option=document.createElement('option');option.value=profile.id;option.textContent=profile.name;return option;}));}
  currentProfile=status.profile;$('profile').value=status.profile;$('output-mode').value=status.output_mode;
  const mapping=JSON.stringify(status.mapping),pad=JSON.stringify(status.pad_mapping),tuning=JSON.stringify(status.tuning);
  if(mapping!==lastMapping){lastMapping=mapping;editor('mapping-fields',status.mapping,keyOptions);}
  if(pad!==lastPad){lastPad=pad;editor('pad-fields',status.pad_mapping,padOptions);}
  if(tuning!==lastTuning){lastTuning=tuning;$('deadzone').value=status.tuning.deadzone;$('sensitivity').value=status.tuning.sensitivity;$('invert-y').checked=status.tuning.invert_y;}
  $('enable').disabled=!status.connected||!status.output_ready||!!status.countdown||status.armed;
  $('keyboard-state').textContent=status.countdown?`Select game · ${Math.ceil(status.countdown)}s`:status.armed?`${status.output_mode==='gamepad'?'Xbox':'Keys'} ON`:'Output off';
  $('note').textContent=status.note+(status.target?` Target: ${status.target}`:'');
  $('pad-status').textContent=status.gamepad.connected?'Xbox virtual device connected. Verify it in Controller test or joy.cpl.':status.gamepad.error||(status.gamepad.package_installed?'Xbox adapter present; connect to check the driver.':'Xbox output is optional. See setup below; keyboard mode is ready without it.');
  $('pad-connect').disabled=!status.gamepad.supported||status.gamepad.connected;$('pad-disconnect').disabled=!status.gamepad.connected;
  const active=status.output_mode==='gamepad'?status.pad_mapping:status.mapping;
  $('keys').replaceChildren(...Object.entries(active).map(([action,key])=>{const el=document.createElement('span');el.className='key'+(status.buttons.includes(action)?' on':'');el.textContent=`${names[action]} → ${key||'off'}`;return el;}));
  if(status.error||status.profile_error)showError(status.error||status.profile_error);
}
async function post(path,data){
  showError();try{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-PocketPad-Admin':admin},body:JSON.stringify(data)});const result=await response.json();if(!response.ok)throw new Error(result.detail||'Request failed');display(result);return result;}catch(error){showError(error.message);return null;}
}
function bindings(id){return Object.fromEntries([...document.querySelectorAll(`#${id} select`)].map(el=>[el.dataset.action,el.value]));}
function selectNetwork(index){$('pair-url').value=urls[index]||'';$('qr').src=`/api/qr?index=${index}`;}
function monitor(){socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/monitor`);socket.onmessage=event=>display(JSON.parse(event.data));socket.onclose=()=>{$('connection').classList.remove('connected');$('connection-text').textContent='Laptop server offline';$('enable').disabled=true;setTimeout(monitor,1500);};}
$('enable').onclick=()=>post('/api/output/arm',{enabled:true});$('disable').onclick=()=>post('/api/output/arm',{enabled:false});
$('profile').onchange=()=>post('/api/profile',{profile:$('profile').value});
$('output-mode').onchange=()=>post('/api/output',{mode:$('output-mode').value});
$('pad-connect').onclick=()=>post('/api/gamepad',{action:'connect'});$('pad-disconnect').onclick=()=>post('/api/gamepad',{action:'disconnect'});
$('save-mapping').onclick=()=>post('/api/mapping',{mapping:bindings('mapping-fields')});
$('save-pad-mapping').onclick=()=>post('/api/pad-mapping',{mapping:bindings('pad-fields')});
$('save-tuning').onclick=()=>post('/api/tuning',{deadzone:Number($('deadzone').value),sensitivity:Number($('sensitivity').value),invert_y:$('invert-y').checked});
function saveProfile(copy){const name=$('profile-name').value.trim();if(!name){showError('Enter a game/profile name first.');return;}post('/api/profiles',{name,...(!copy&&currentProfile.startsWith('saved_')?{replace_id:currentProfile}:{})});}
$('save-profile').onclick=()=>saveProfile(false);$('copy-profile').onclick=()=>saveProfile(true);
$('export-profile').onclick=async()=>{try{const response=await fetch('/api/current-profile');if(!response.ok)throw new Error('Could not export profile.');const profile=await response.json(),url=URL.createObjectURL(new Blob([JSON.stringify(profile,null,2)],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='NONA_game_profile.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){showError(error.message);}};
$('import-profile').onchange=async()=>{const file=$('import-profile').files[0];if(!file)return;try{if(file.size>65536)throw new Error('Profile JSON must be smaller than 64 KB.');const data=JSON.parse(await file.text());if(data.version!==1)throw new Error('Unsupported profile format.');await post('/api/profiles',{profile:data.profile});}catch(error){showError(error.message);}finally{$('import-profile').value='';}};
$('network').onchange=()=>selectNetwork(Number($('network').value));
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('pair-url').value);$('copy').textContent='Copied';setTimeout(()=>$('copy').textContent='Copy',1400);}catch{$('pair-url').select();$('copy').textContent='Select + copy';}};
$('qr').onerror=()=>{$('pair-error').textContent='QR unavailable. Copy or type the pairing address on your phone.';$('pair-error').classList.remove('hidden');};
fetch('/api/session').then(async response=>{if(!response.ok)throw new Error('Could not load pairing details.');return response.json();}).then(data=>{admin=data.admin;urls=data.urls;keyOptions=data.key_options;padOptions=data.pad_options;display(data);if(urls.length){selectNetwork(0);if(urls.length>1){$('network').classList.remove('hidden');urls.forEach((url,index)=>{const option=document.createElement('option');option.value=index;option.textContent=new URL(url).hostname;$('network').append(option);});}}else{$('pair-error').textContent='No network address found. Connect Wi-Fi and restart NONA.';$('pair-error').classList.remove('hidden');$('qr').classList.add('hidden');}monitor();}).catch(error=>showError(error.message));
