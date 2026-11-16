const $=id=>document.getElementById(id);
function monitor(){
  const ws=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/monitor`);
  ws.onmessage=event=>{const state=JSON.parse(event.data);$('host-status').textContent=`Phone: ${state.connected?'connected':'disconnected'} · Output: ${state.output_mode} ${state.armed?'ON':'off'} · Xbox device: ${state.gamepad.connected?'connected':'not connected'}`;$('host-report').textContent=JSON.stringify({buttons:state.buttons,axes:state.axes,steering:state.steering,desired_xbox_report:state.gamepad_report},null,2);};
  ws.onclose=()=>{$('host-status').textContent='NONA server offline';setTimeout(monitor,1500);};
}
function poll(){
  const pads=navigator.getGamepads?[...navigator.getGamepads()].filter(Boolean):[];
  $('os-status').textContent=pads.length?`${pads.length} controller(s) detected by this browser`:'No controller detected yet.';
  $('os-report').textContent=pads.length?JSON.stringify(pads.map(pad=>({id:pad.id,index:pad.index,mapping:pad.mapping,axes:[...pad.axes].map(x=>Number(x.toFixed(3))),buttons:pad.buttons.map((b,index)=>({index,value:Number(b.value.toFixed(3))})).filter(b=>b.value>0)})),null,2):'The phone transport can work before an OS controller exists.';
  requestAnimationFrame(poll);
}
monitor();requestAnimationFrame(poll);
