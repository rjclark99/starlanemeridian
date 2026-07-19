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
    const error = new Error(message);
    error.status = response.status;
    throw error;
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
  $("dashboard").hidden = !state.isUnlocked;
  $("credentialContent").hidden = !state.isUnlocked;
  $("lock").hidden = !state.isUnlocked;
  $("export").hidden = !state.isUnlocked;
  $("createButton").hidden = state.exists;
  $("unlockButton").hidden = !state.exists;
  $("master").autocomplete = state.exists ? "current-password" : "new-password";
  $("master").placeholder = state.exists ? "Enter existing master password" : "Choose master password (14+ characters)";
  if (state.isUnlocked) await Promise.all([households(), loadDevices()]);
  else $("deviceList").innerHTML = "";
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
    if (error.status === 401) { setTimeout(status, 0); return; }
    $("deviceList").innerHTML = `<p class="error cloud-load-error">${escapeHtml(error.message)}</p>`;
  } finally {
    refresh.disabled = false;
  }
}

function renderDevice(device) {
  const progress = device.progressPercent ?? fallbackProgress(device.setupStep);
  const lastSeen = device.lastSeenAt ? new Date(device.lastSeenAt * 1000) : null;
  const ageSeconds = device.lastSeenAt ? Math.max(0, Math.floor(Date.now() / 1000) - device.lastSeenAt) : Infinity;
  const presence = ageSeconds <= 90 ? "online" : ageSeconds <= 600 ? "idle" : "offline";
  const statusLabel = phaseLabel(device.setupPhase || device.setupStep || "READY");
  const storage = device.totalStorageMb ? Math.round((device.freeStorageMb || 0) / device.totalStorageMb * 100) : null;
  return `<article class="device-card">
    <div class="device-title-row">
      <div><div class="device-name"><i class="presence ${presence}"></i><strong>${escapeHtml(device.model)}</strong></div><span>${escapeHtml(device.manufacturer || "Unknown maker")} ${escapeHtml(device.product || "")} &middot; ${escapeHtml(device.architecture || "ABI pending")}</span></div>
      <div class="device-progress-value"><strong>${progress}%</strong><span>${escapeHtml(statusLabel)}</span></div>
    </div>
    <div class="progress-track" role="progressbar" aria-label="Installation progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}"><i style="width:${progress}%"></i></div>
    ${renderStepRail(device.setupStep)}
    <div class="status-callout ${device.errorCode ? "has-error" : ""}">
      <strong>${device.busy ? "In progress" : device.errorCode ? "Attention needed" : "Latest update"}</strong>
      <span>${escapeHtml(device.statusMessage || "Waiting for the next signed device update")}</span>
      ${device.errorCode ? `<span class="error">${escapeHtml(device.errorCode)}</span>` : ""}
    </div>
    ${renderTimeline(device.events || [])}
    <dl class="device-facts">
      ${fact("Last seen", lastSeen ? `${relativeTime(ageSeconds)} - ${lastSeen.toLocaleString()}` : "Never")}
      ${fact("Android / Fire OS", `${device.osVersion || "Unknown"}${device.apiLevel ? ` - API ${device.apiLevel}` : ""}`)}
      ${fact("Security patch", device.securityPatch || "Not reported")}
      ${fact("Setup app", device.appVersion ? `Build ${device.appVersion}` : "Not reported")}
      ${fact("Configuration", device.configVersion || "Not loaded")}
      ${fact("Kodi", device.kodiVersion || "Not detected")}
      ${fact("Proton VPN", device.protonVersion || "Not detected")}
      ${fact("Storage", device.totalStorageMb ? `${formatMb(device.freeStorageMb)} free of ${formatMb(device.totalStorageMb)}${storage !== null ? ` - ${storage}% free` : ""}` : "Not reported")}
      ${fact("Memory", device.totalMemoryMb ? formatMb(device.totalMemoryMb) : "Not reported")}
      ${fact("APK permission", flagLabel(device.installPermission, "Allowed", "Needs approval"), device.installPermission ? "good" : "warn")}
      ${fact("Bootstrap ZIP", flagLabel(device.bootstrapReady, "Ready", "Not prepared"), device.bootstrapReady ? "good" : "neutral")}
      ${fact("Automation", flagLabel(device.automaticSetup, "Running", "Inactive"), device.automaticSetup ? "good" : "neutral")}
      ${fact("Real-Debrid", device.debridExpiry ? `Premium until ${new Date(device.debridExpiry).toLocaleDateString()}` : "Not linked or not reported")}
    </dl>
    <div class="actions device-actions">
      <select aria-label="Remote setup action" data-action-choice="${device.id}">${setupActions.map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}</select>
      <button data-action-run="${device.id}">Send action</button>
      <button class="secondary" data-device-delete="${device.id}">Remove device</button>
    </div>
    <p class="command-result" data-command-result="${device.id}" aria-live="polite"></p>
  </article>`;
}

const setupStepOrder = ["CONFIGURATION", "KODI", "PROTON", "BOOTSTRAP", "ACCOUNT_LINK"];
const setupStepNames = { CONFIGURATION: "Config", KODI: "Kodi", PROTON: "VPN", BOOTSTRAP: "Bootstrap", ACCOUNT_LINK: "Account" };
const setupPhaseNames = {
  READY: "Ready to begin", PAIRING: "Pairing device", VERIFYING_CONFIGURATION: "Verifying configuration", CONFIGURATION_VERIFIED: "Configuration verified",
  DOWNLOADING_KODI: "Downloading Kodi", WAITING_INSTALL_CONFIRMATION: "Waiting for TV confirmation", KODI_READY: "Kodi ready",
  WAITING_PROTON_STORE: "Waiting for Proton VPN", DOWNLOADING_PROTON: "Downloading Proton VPN", PROTON_READY: "Proton VPN ready",
  DOWNLOADING_BOOTSTRAP: "Preparing bootstrap", BOOTSTRAP_READY: "Bootstrap ready", WAITING_KODI_BOOTSTRAP: "Waiting for Kodi bootstrap",
  REQUESTING_REAL_DEBRID_AUTH: "Requesting authorization", WAITING_REAL_DEBRID_AUTH: "Waiting for Real-Debrid", ACCOUNT_LINKED: "Account linked",
  COMPLETE: "Installation complete", ERROR: "Setup needs attention"
};

function phaseLabel(value) { return setupPhaseNames[value] || value.replaceAll("_", " ").toLowerCase().replace(/^./, letter => letter.toUpperCase()); }
function fallbackProgress(step) { return ({ WELCOME: 0, CONFIGURATION: 15, KODI: 45, PROTON: 65, BOOTSTRAP: 80, ACCOUNT_LINK: 94, COMPLETE: 100 })[step] ?? 0; }
function renderStepRail(current) {
  const currentIndex = current === "COMPLETE" ? setupStepOrder.length : setupStepOrder.indexOf(current);
  return `<ol class="step-rail">${setupStepOrder.map((step, index) => `<li class="${index < currentIndex ? "done" : index === currentIndex ? "current" : ""}"><i></i><span>${setupStepNames[step]}</span></li>`).join("")}</ol>`;
}
function renderTimeline(events) {
  if (!events.length) return '<div class="event-empty">Detailed installation events will appear after setup app 0.3.0 reports its next change.</div>';
  return `<details class="event-timeline" ${events.some(event => event.errorCode) ? "open" : ""}>
    <summary>Installation activity <span>${events.length} event${events.length === 1 ? "" : "s"}</span></summary>
    <ol>${events.slice(-10).reverse().map(event => `<li class="${event.errorCode ? "event-error" : ""}">
      <i></i><div><strong>${escapeHtml(phaseLabel(event.setupPhase || event.setupStep))}</strong><span>${escapeHtml(event.statusMessage || "Status changed")}</span><time>${event.createdAt ? new Date(event.createdAt * 1000).toLocaleString() : ""}</time>${event.errorCode ? `<code>${escapeHtml(event.errorCode)}</code>` : ""}</div>
    </li>`).join("")}</ol>
  </details>`;
}
function fact(label, value, tone = "") { return `<div><dt>${escapeHtml(label)}</dt><dd class="${tone}">${escapeHtml(value)}</dd></div>`; }
function flagLabel(value, yes, no) { return value === 1 || value === true ? yes : no; }
function formatMb(value) { if (value === null || value === undefined) return "Unknown"; return value >= 1024 ? `${(value / 1024).toFixed(1)} GB` : `${value} MB`; }
function relativeTime(seconds) {
  if (seconds < 15) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
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

setInterval(() => {
  const devicesTab = $("devices");
  if (!$("dashboard").hidden && !devicesTab.hidden && document.visibilityState === "visible") loadDevices();
}, 30_000);

status();
