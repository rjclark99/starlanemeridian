const $=id=>document.getElementById(id);const api=async(path,options={})=>{const r=await fetch(path,{headers:{'Content-Type':'application/json'},...options}),text=await r.text();if(!r.ok){let message=text||r.statusText;try{const problem=JSON.parse(text);message=problem.error||problem.title||message}catch{}throw new Error(message)}return r.status===204||!text?null:JSON.parse(text)};
async function status(){const s=await api('/api/vault/status');$('unlock').hidden=s.isUnlocked;$('dashboard').hidden=!s.isUnlocked;$('lock').hidden=!s.isUnlocked;$('export').hidden=!s.isUnlocked;$('createButton').hidden=s.exists;$('unlockButton').hidden=!s.exists;$('master').autocomplete=s.exists?'current-password':'new-password';$('master').placeholder=s.exists?'Enter existing master password':'Choose master password (14+ characters)';if(s.isUnlocked)await households()}
async function unlock(create){$('unlockError').textContent='';try{await api(`/api/vault/${create?'create':'unlock'}`,{method:'POST',body:JSON.stringify({password:$('master').value})});$('master').value='';await status()}catch(e){$('unlockError').textContent=e.message;await status()}}
async function households(){const items=await api('/api/households');$('householdList').innerHTML=items.map(x=>`<div class="household" data-id="${x.id}"><strong>${escapeHtml(x.displayName)}</strong><span>Consent: ${x.consentAt?'yes':'no'} · Handoff: ${x.handoffAt?'yes':'no'}</span></div>`).join('');document.querySelectorAll('.household').forEach(el=>el.onclick=()=>edit(el.dataset.id))}
async function edit(id){const x=await api(`/api/households/${id}/secret`);$('householdId').value=x.id;$('displayName').value=x.displayName;$('protonUsername').value=x.protonUsername||'';$('protonPassword').value=x.protonPassword||'';$('rdUsername').value=x.realDebridUsername||'';$('rdPassword').value=x.realDebridPassword||'';$('consent').checked=!!x.consentAt;$('handoff').checked=!!x.handoffAt}
$('householdForm').onsubmit=async e=>{e.preventDefault();const id=$('householdId').value,body={displayName:$('displayName').value,protonUsername:$('protonUsername').value,protonPassword:$('protonPassword').value,realDebridUsername:$('rdUsername').value,realDebridPassword:$('rdPassword').value,recordConsent:$('consent').checked,recordHandoff:$('handoff').checked};await api(id?`/api/households/${id}`:'/api/households',{method:id?'PUT':'POST',body:JSON.stringify(body)});e.target.reset();$('householdId').value='';await households()};
$('generate').onclick=async()=>{const x=await api('/api/generate');$('protonUsername').value=x.username;$('protonPassword').value=x.password};$('unlockButton').onclick=()=>unlock(false);$('createButton').onclick=()=>unlock(true);$('lock').onclick=async()=>{await api('/api/vault/lock',{method:'POST'});await status()};
document.querySelectorAll('nav button').forEach(b=>b.onclick=async()=>{document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.tab').forEach(x=>x.hidden=x.id!==b.dataset.tab);if(b.dataset.tab==='audit'){const items=await api('/api/audit');$('auditList').innerHTML=items.map(x=>`<div class="audit"><time>${new Date(x.at).toLocaleString()}</time>${escapeHtml(x.action)} — ${escapeHtml(x.detail)}</div>`).join('')}});
async function adb(path,body){try{$('adbOutput').textContent='Working…';const x=await api(path,{method:body?'POST':'GET',body:body?JSON.stringify(body):undefined});$('adbOutput').textContent=x.output}catch(e){$('adbOutput').textContent=e.message}}$('adbList').onclick=()=>adb('/api/adb/devices');$('adbConnect').onclick=()=>adb('/api/adb/connect',{deviceAddress:$('deviceAddress').value});$('adbInstall').onclick=()=>adb('/api/adb/install',{deviceAddress:$('deviceAddress').value,apkPath:$('apkPath').value});$('adbBootstrap').onclick=()=>adb('/api/adb/bootstrap',{deviceAddress:$('deviceAddress').value,bootstrapPath:$('bootstrapPath').value});
function escapeHtml(v){const d=document.createElement('div');d.textContent=v??'';return d.innerHTML}status();
const setupActions=[
  ['START_SETUP','Start or resume full setup'],
  ['INSTALL_KODI','Install Kodi'],
  ['INSTALL_PROTON','Install Proton VPN'],
  ['PREPARE_BOOTSTRAP','Prepare Kodi bootstrap'],
  ['OPEN_KODI','Open Kodi'],
  ['BEGIN_REAL_DEBRID_AUTH','Begin Real-Debrid link'],
  ['SYNC_CONFIG','Sync configuration'],
  ['RETRY_CURRENT_STEP','Retry current step']
];
async function loadDevices(){
  try{
    const x=await api('/api/control/devices');
    $('deviceList').innerHTML=(x.devices||[]).map(d=>`<div class="household device-card"><strong>${escapeHtml(d.householdAlias)} — ${escapeHtml(d.model)}</strong><span>${escapeHtml(d.setupStep||'not started')} · Config ${escapeHtml(d.configVersion||'none')} · Last seen ${d.lastSeenAt?new Date(d.lastSeenAt*1000).toLocaleString():'never'}</span>${d.errorCode?`<span class="error">Error: ${escapeHtml(d.errorCode)}</span>`:''}<div class="actions device-actions"><select aria-label="Remote setup action" data-action-choice="${d.id}">${setupActions.map(([value,label])=>`<option value="${value}">${label}</option>`).join('')}</select><button data-action-run="${d.id}">Send action</button><button class="secondary" data-device-delete="${d.id}">Remove device</button><button class="secondary" data-household-delete="${d.householdId}">Delete cloud household</button></div><p class="command-result" data-command-result="${d.id}" aria-live="polite"></p></div>`).join('')||'<p>No paired devices yet.</p>';
    document.querySelectorAll('[data-action-run]').forEach(button=>button.onclick=async()=>{
      const device=button.dataset.actionRun,choice=document.querySelector(`[data-action-choice="${device}"]`),result=document.querySelector(`[data-command-result="${device}"]`);
      button.disabled=true;result.textContent='Sending…';
      try{await api(`/api/control/devices/${device}/commands/${choice.value}`,{method:'POST'});result.textContent='Action queued. The TV will collect it within about 30 seconds.'}
      catch(e){result.textContent=e.message;result.classList.add('error')}
      finally{button.disabled=false}
    });
    document.querySelectorAll('[data-device-delete]').forEach(button=>button.onclick=async()=>{if(!confirm('Permanently revoke this device and delete its cloud status and pending commands?'))return;await api(`/api/control/devices/${button.dataset.deviceDelete}`,{method:'DELETE'});await loadDevices()});
    document.querySelectorAll('[data-household-delete]').forEach(button=>button.onclick=async()=>{if(!confirm('Permanently delete this household and all of its paired-device cloud data? Local vault records are not affected.'))return;await api(`/api/control/households/${button.dataset.householdDelete}`,{method:'DELETE'});await loadDevices()});
  }catch(e){$('deviceList').innerHTML=`<p class="error">${escapeHtml(e.message)}</p>`}
}
$('deviceRefresh').onclick=loadDevices;
$('pairingCreate').onclick=async()=>{try{const x=await api('/api/control/pairing',{method:'POST',body:JSON.stringify({householdAlias:$('pairingAlias').value})});$('pairingCode').textContent=`Pairing code: ${x.code}`}catch(e){$('pairingCode').textContent=e.message}};
