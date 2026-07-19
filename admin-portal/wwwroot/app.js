const $ = id => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const text = await response.text();
  if (!response.ok) {
    let message = text || response.statusText;
    try {
      const problem = JSON.parse(text);
      message = problem.error || problem.title || message;
    } catch { }
    throw new Error(message);
  }
  return response.status === 204 || !text ? null : JSON.parse(text);
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = value ?? "";
  return element.innerHTML;
}

async function status() {
  const state = await api("/api/vault/status");
  $("unlock").hidden = state.isUnlocked;
  $("dashboard").hidden = false;
  $("credentialContent").hidden = !state.isUnlocked;
  $("lock").hidden = !state.isUnlocked;
  $("export").hidden = !state.isUnlocked;
  $("createButton").hidden = state.exists;
  $("unlockButton").hidden = !state.exists;
  $("master").autocomplete = state.exists ? "current-password" : "new-password";
  $("master").placeholder = state.exists ? "Enter existing master password" : "Choose master password (14+ characters)";
  if (state.isUnlocked) await Promise.all([households(), loadDevices()]);
  else await loadDevices();
}

async function unlock(create) {
  $("unlockError").textContent = "";
  try {
    await api(`/api/vault/${create ? "create" : "unlock"}`, { method: "POST", body: JSON.stringify({ password: $("master").value }) });
    $("master").value = "";
    await status();
  } catch (error) {
    $("unlockError").textContent = error.message;
    await status();
  }
}

async function households() {
  const items = await api("/api/households");
  $("householdList").innerHTML = items.length
    ? items.map(item => `<div class="household" data-id="${item.id}"><strong>${escapeHtml(item.displayName)}</strong><span>Consent: ${item.consentAt ? "yes" : "no"} &middot; Handoff: ${item.handoffAt ? "yes" : "no"}</span></div>`).join("")
    : '<p class="empty-state">No encrypted credential records yet. Cloud pairing households are shown under Devices &amp; ADB.</p>';
  document.querySelectorAll("#householdList .household").forEach(element => element.onclick = () => edit(element.dataset.id));
}

async function edit(id) {
  const item = await api(`/api/households/${id}/secret`);
  $("householdId").value = item.id;
  $("displayName").value = item.displayName;
  $("protonUsername").value = item.protonUsername || "";
  $("protonPassword").value = item.protonPassword || "";
  $("rdUsername").value = item.realDebridUsername || "";
  $("rdPassword").value = item.realDebridPassword || "";
  $("consent").checked = !!item.consentAt;
  $("handoff").checked = !!item.handoffAt;
}

$("householdForm").onsubmit = async event => {
  event.preventDefault();
  const id = $("householdId").value;
  const body = {
    displayName: $("displayName").value,
    protonUsername: $("protonUsername").value,
    protonPassword: $("protonPassword").value,
    realDebridUsername: $("rdUsername").value,
    realDebridPassword: $("rdPassword").value,
    recordConsent: $("consent").checked,
    recordHandoff: $("handoff").checked
  };
  await api(id ? `/api/households/${id}` : "/api/households", { method: id ? "PUT" : "POST", body: JSON.stringify(body) });
  event.target.reset();
  $("householdId").value = "";
  await households();
};

$("generate").onclick = async () => {
  const generated = await api("/api/generate");
  $("protonUsername").value = generated.username;
  $("protonPassword").value = generated.password;
};
$("unlockButton").onclick = () => unlock(false);
$("createButton").onclick = () => unlock(true);
$("lock").onclick = async () => { await api("/api/vault/lock", { method: "POST" }); await status(); };

document.querySelectorAll("nav button").forEach(button => button.onclick = async () => {
  document.querySelectorAll("nav button").forEach(item => item.classList.toggle("active", item === button));
  document.querySelectorAll(".tab").forEach(item => item.hidden = item.id !== button.dataset.tab);
  if (button.dataset.tab === "devices") await loadDevices();
  if (button.dataset.tab === "audit") {
    const items = await api("/api/audit");
    $("auditList").innerHTML = items.map(item => `<div class="audit"><time>${new Date(item.at).toLocaleString()}</time>${escapeHtml(item.action)} &mdash; ${escapeHtml(item.detail)}</div>`).join("");
  }
});

async function adb(path, body) {
  try {
    $("adbOutput").textContent = "Working\u2026";
    const result = await api(path, { method: body ? "POST" : "GET", body: body ? JSON.stringify(body) : undefined });
    $("adbOutput").textContent = result.output;
  } catch (error) {
    $("adbOutput").textContent = error.message;
  }
}
$("adbList").onclick = () => adb("/api/adb/devices");
$("adbConnect").onclick = () => adb("/api/adb/connect", { deviceAddress: $("deviceAddress").value });
$("adbInstall").onclick = () => adb("/api/adb/install", { deviceAddress: $("deviceAddress").value, apkPath: $("apkPath").value });
$("adbBootstrap").onclick = () => adb("/api/adb/bootstrap", { deviceAddress: $("deviceAddress").value, bootstrapPath: $("bootstrapPath").value });

const setupActions = [
  ["START_SETUP", "Start or resume full setup"],
  ["INSTALL_KODI", "Install Kodi"],
  ["INSTALL_PROTON", "Install Proton VPN"],
  ["PREPARE_BOOTSTRAP", "Prepare Kodi bootstrap"],
  ["OPEN_KODI", "Open Kodi"],
  ["BEGIN_REAL_DEBRID_AUTH", "Begin Real-Debrid link"],
  ["SYNC_CONFIG", "Sync configuration"],
  ["RETRY_CURRENT_STEP", "Retry current step"]
];

let deviceLoadPromise;
async function loadDevices() {
  if (deviceLoadPromise) return deviceLoadPromise;
  deviceLoadPromise = loadDevicesCore();
  try { return await deviceLoadPromise; }
  finally { deviceLoadPromise = null; }
}

async function loadDevicesCore() {
  const refresh = $("deviceRefresh");
  refresh.disabled = true;
  $("deviceList").innerHTML = '<p class="empty-state">Loading cloud households and devices&hellip;</p>';
  try {
    const result = await api("/api/control/devices");
    const devices = result.devices || [];
    if (!devices.length) {
      $("deviceList").innerHTML = '<p class="empty-state">No cloud households or paired devices yet.</p>';
      return;
    }

    const householdsById = new Map();
    for (const device of devices) {
      const key = device.householdId || `alias:${device.householdAlias}`;
      if (!householdsById.has(key)) householdsById.set(key, { id: device.householdId, alias: device.householdAlias, devices: [] });
      householdsById.get(key).devices.push(device);
    }

    $("deviceList").innerHTML = Array.from(householdsById.values()).map(household => `
      <section class="cloud-household">
        <div class="cloud-household-header">
          <div><strong>${escapeHtml(household.alias)}</strong><span>Cloud pairing record &middot; ${household.devices.length} paired device${household.devices.length === 1 ? "" : "s"}</span></div>
          ${household.id ? `<button class="secondary" data-household-delete="${household.id}">Delete cloud household</button>` : ""}
        </div>
        ${household.devices.map(renderDevice).join("")}
      </section>`).join("");
    bindDeviceActions();
  } catch (error) {
    $("deviceList").innerHTML = `<p class="error cloud-load-error">${escapeHtml(error.message)}</p>`;
  } finally {
    refresh.disabled = false;
  }
}

function renderDevice(device) {
  return `<div class="device-card">
    <strong>${escapeHtml(device.model)}</strong>
    <span>${escapeHtml(device.setupStep || "not started")} &middot; Config ${escapeHtml(device.configVersion || "none")} &middot; App ${escapeHtml(device.appVersion ?? "unknown")} &middot; Last seen ${device.lastSeenAt ? new Date(device.lastSeenAt * 1000).toLocaleString() : "never"}</span>
    ${device.errorCode ? `<span class="error">Error: ${escapeHtml(device.errorCode)}</span>` : ""}
    <div class="actions device-actions">
      <select aria-label="Remote setup action" data-action-choice="${device.id}">${setupActions.map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}</select>
      <button data-action-run="${device.id}">Send action</button>
      <button class="secondary" data-device-delete="${device.id}">Remove device</button>
    </div>
    <p class="command-result" data-command-result="${device.id}" aria-live="polite"></p>
  </div>`;
}

function bindDeviceActions() {
  document.querySelectorAll("[data-action-run]").forEach(button => button.onclick = async () => {
    const device = button.dataset.actionRun;
    const choice = document.querySelector(`[data-action-choice="${device}"]`);
    const result = document.querySelector(`[data-command-result="${device}"]`);
    button.disabled = true;
    result.textContent = "Sending\u2026";
    try {
      await api(`/api/control/devices/${device}/commands/${choice.value}`, { method: "POST" });
      result.textContent = "Action queued. The TV will collect it within about 30 seconds.";
      result.classList.remove("error");
    } catch (error) {
      result.textContent = error.message;
      result.classList.add("error");
    } finally { button.disabled = false; }
  });
  document.querySelectorAll("[data-device-delete]").forEach(button => button.onclick = async () => {
    if (!confirm("Permanently revoke this device and delete its cloud status and pending commands?")) return;
    await api(`/api/control/devices/${button.dataset.deviceDelete}`, { method: "DELETE" });
    await loadDevices();
  });
  document.querySelectorAll("[data-household-delete]").forEach(button => button.onclick = async () => {
    if (!confirm("Permanently delete this cloud household and all of its paired-device status? Local credential-vault records are not affected.")) return;
    await api(`/api/control/households/${button.dataset.householdDelete}`, { method: "DELETE" });
    await loadDevices();
  });
}

$("deviceRefresh").onclick = loadDevices;
$("pairingCreate").onclick = async () => {
  try {
    const result = await api("/api/control/pairing", { method: "POST", body: JSON.stringify({ householdAlias: $("pairingAlias").value }) });
    $("pairingCode").textContent = `Pairing code: ${result.code}`;
  } catch (error) { $("pairingCode").textContent = error.message; }
};

status();
