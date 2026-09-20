// =============================================================================
// CORE MODULE: Icons, Escaping, Toasts, Confirmation Modal, Theme & Tabs
// =============================================================================

// --- SVG Icon Templates ---
const SVG_PLAY = `<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
const SVG_PAUSE = `<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
const SVG_PLUS = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;
const SVG_LIST = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`;
const SVG_HIDE = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
const SVG_UNHIDE = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
const SVG_TRASH = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`;
const SVG_CHEVRON_UP = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>`;
const SVG_CHEVRON_DOWN = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`;
const SVG_CHEVRON_LEFT = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>`;
const SVG_CHEVRON_RIGHT = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>`;
const SVG_FOLDER = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`;
const SVG_SPARKLES = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`;
const SVG_SYNC = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`;
const SVG_CHECK = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`;
const SVG_ALERT = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
const SVG_WAVEFORM = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`;
const SVG_CONVERT = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`;
const SVG_HEART = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;
const SVG_HEART_FILLED = `<svg class="icon-svg" viewBox="0 0 24 24" fill="#ff0055" stroke="#ff0055" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;

// --- String & HTML Escaping Helpers ---
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeJs(str) {
  if (str === null || str === undefined) return '';
  return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function escHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Terminal line classifier and updater
function _dupTerminalLineClass(msg) {
  if (!msg) return '';
  const lower = msg.toLowerCase();
  if (lower.includes('error') || lower.includes('fail')) return 'dup-line-error';
  if (lower.includes('warning') || lower.includes('warn') || lower.includes('skip')) return 'dup-line-warn';
  if (lower.includes('complete') || lower.includes('saved') || lower.includes('success') || lower.includes('found') || lower.includes('done')) return 'dup-line-success';
  if (lower.startsWith('---') || lower.startsWith('===')) return 'dup-line-header';
  return 'dup-line-info';
}

function pushTermLine(logEl, msg) {
  if (!logEl) return;
  const line = document.createElement('span');
  line.className = 'dup-terminal-line ' + _dupTerminalLineClass(msg);
  line.textContent = msg;
  logEl.appendChild(line);
  logEl.appendChild(document.createTextNode('\n'));
  while (logEl.childElementCount > 250) {
    logEl.removeChild(logEl.firstElementChild);
  }
  if (logEl._scrollFrame == null) {
    logEl._scrollFrame = requestAnimationFrame(() => {
      logEl._scrollFrame = null;
      logEl.scrollTop = logEl.scrollHeight;
    });
  }
}

// --- Toast Notifications System ---
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let icon = SVG_ALERT;
  if (type === 'success') {
    icon = SVG_CHECK;
  } else if (type === 'error') {
    icon = SVG_ALERT;
  }

  toast.innerHTML = `
    <div class="toast-message">
      <span style="display: inline-flex; align-items: center; flex-shrink: 0;">${icon}</span>
      <span>${escapeHtml(message)}</span>
    </div>
    <button class="toast-close-btn" title="Dismiss">×</button>
  `;

  const closeBtn = toast.querySelector('.toast-close-btn');
  const dismiss = () => {
    toast.classList.add('toast-fade-out');
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 220);
  };

  if (closeBtn) {
    closeBtn.addEventListener('click', dismiss);
  }

  container.appendChild(toast);

  if (duration > 0) {
    setTimeout(dismiss, duration);
  }
}

// --- Generic Confirmation Modal System ---
let pendingConfirmCallback = null;

function showConfirmModal({ title = 'Confirm Action', message = 'Are you sure?', details = null, confirmText = 'Confirm', confirmClass = 'btn', onConfirm = null }) {
  const modal = document.getElementById('modal-confirm-action');
  const titleEl = document.getElementById('confirm-modal-title');
  const msgEl = document.getElementById('confirm-modal-message');
  const detailsEl = document.getElementById('confirm-modal-details');
  const okBtn = document.getElementById('confirm-modal-ok-btn');

  if (!modal) {
    if (confirm(message)) {
      if (onConfirm) onConfirm();
    }
    return;
  }

  if (titleEl) titleEl.textContent = title;
  if (msgEl) msgEl.textContent = message;

  if (detailsEl) {
    if (details) {
      detailsEl.style.display = 'block';
      if (Array.isArray(details)) {
        detailsEl.innerHTML = details.map(d => `<div style="padding: 2px 0;">${escapeHtml(d)}</div>`).join('');
      } else {
        detailsEl.textContent = details;
      }
    } else {
      detailsEl.style.display = 'none';
      detailsEl.innerHTML = '';
    }
  }

  if (okBtn) {
    okBtn.textContent = confirmText;
    okBtn.className = confirmClass || 'btn';
  }

  pendingConfirmCallback = onConfirm;
  modal.style.display = 'flex';
}

function closeConfirmModal(confirmed = false) {
  const modal = document.getElementById('modal-confirm-action');
  if (modal) modal.style.display = 'none';

  if (confirmed && typeof pendingConfirmCallback === 'function') {
    const cb = pendingConfirmCallback;
    pendingConfirmCallback = null;
    cb();
  } else {
    pendingConfirmCallback = null;
  }
}

// --- Theme Management System ---
function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  applyTheme(saved);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  const sunIcon = document.getElementById('theme-icon-sun');
  const moonIcon = document.getElementById('theme-icon-moon');
  const label = document.getElementById('theme-toggle-text');

  if (theme === 'dark') {
    if (sunIcon) sunIcon.style.display = 'inline-block';
    if (moonIcon) moonIcon.style.display = 'none';
    if (label) label.textContent = 'Dark';
  } else {
    if (sunIcon) sunIcon.style.display = 'none';
    if (moonIcon) moonIcon.style.display = 'inline-block';
    if (label) label.textContent = 'Light';
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const newTheme = current === 'dark' ? 'light' : 'dark';
  applyTheme(newTheme);
}

// --- Shared Global State ---
var allSongs = [];
var filteredSongs = [];
var libPage = 1;
var libPageSize = 15;
var currentFormatFilter = 'all';
var selectedSongPaths = new Set();

var allClusters = [];
var filteredClusters = [];
var dupPage = 1;
var dupPageSize = 5;
var useAudioFingerprinting = localStorage.getItem('antigravity_use_audio_fingerprint') === 'true';
var dupEventSource = null;

var currentTrackPath = null;
var isPlaying = false;
var isScrubbing = false;
var isPlayerLooping = false;
var isShuffled = false;
var originalQueue = [];
var activeQueue = [];
var queueIndex = 0;

var allPlaylists = [];
var selectedPlaylist = null;
var currentPlaylistTracks = [];
var targetTrackForPlaylist = null;

var likedPlaylistId = null;
var likedSongPaths = new Set();

var currentDeviceId = 'local';
var currentDeviceName = 'Local Music Folders';
var currentDeviceType = 'Local Storage';
var currentSortCriteria = 'ctime_desc';
var availableDevicesList = [];

var playerTabSongs = [];
var playerTabFiltered = [];
var playerTabDeviceId = 'local';

// --- Tab Navigation Router ---
function initTabs() {
  const btns = document.querySelectorAll('.tab-btn');

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      switchTab(targetId);
    });
  });
}

function switchTab(tabId) {
  let activeTabId = tabId;
  let activeBtnTab = tabId;

  // Map legacy/sub-tabs gracefully
  if (tabId === 'tab-devices') {
    activeTabId = 'tab-overview';
    activeBtnTab = 'tab-overview';
  } else if (tabId === 'tab-hidden') {
    activeTabId = 'tab-hidden';
    activeBtnTab = 'tab-deleted';
  }

  const btns = document.querySelectorAll('.tab-btn');
  const sections = document.querySelectorAll('.tab-content');

  btns.forEach(b => {
    if (b.getAttribute('data-tab') === activeBtnTab) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  sections.forEach(s => {
    s.style.display = (s.id === activeTabId) ? 'block' : 'none';
  });

  if (activeTabId === 'tab-library') {
    if (allSongs && allSongs.length > 0) {
      if (typeof renderLibraryPage === 'function') renderLibraryPage();
    } else {
      if (typeof loadDeviceSongs === 'function') loadDeviceSongs(currentDeviceId, false);
    }
  }

  if (activeTabId === 'tab-player') {
    if (typeof refreshPlayerLibraryList === 'function') {
      refreshPlayerLibraryList(false).then(() => {
        const sel = document.getElementById('player-library-select');
        const devId = (sel && sel.value) ? sel.value : (playerTabDeviceId || 'local');
        if (!playerTabSongs || playerTabSongs.length === 0 || playerTabDeviceId !== devId) {
          if (typeof loadPlayerLibrary === 'function') loadPlayerLibrary(devId);
        }
      });
    }
    if (typeof renderQueuePanel === 'function') renderQueuePanel();
  }
}
// =============================================================================
// OVERVIEW MODULE: Dashboard Metric Stats, Devices Breakdown, Over-IP Peers
// =============================================================================

async function loadDashboardStats() {
  try {
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();

    document.getElementById('stat-total-songs').textContent = data.total_local_songs || 0;
    document.getElementById('stat-synced-count').textContent = data.synced_count || 0;
    document.getElementById('stat-hidden-count').textContent = data.hidden_count || 0;
    document.getElementById('stat-duplicates-count').textContent = data.duplicates_count || 0;

    // Update dynamic duplicate badge in nav bar
    const dupBadge = document.getElementById('nav-badge-duplicates');
    if (dupBadge) {
      const dupCount = data.duplicates_count || 0;
      dupBadge.textContent = dupCount;
      dupBadge.style.display = dupCount > 0 ? 'inline-flex' : 'none';
    }

    // Update trash badge in nav bar
    try {
      const delRes = await fetch('/api/deleted');
      const delSongs = await delRes.json();
      const trashBadge = document.getElementById('nav-badge-trash');
      if (trashBadge) {
        const trashCount = Array.isArray(delSongs) ? delSongs.length : 0;
        trashBadge.textContent = trashCount;
        trashBadge.style.display = trashCount > 0 ? 'inline-flex' : 'none';
      }
    } catch (_) {}

    renderDeviceBreakdown(data.device_counts || []);
  } catch (err) {
    console.error('Error fetching dashboard stats:', err);
  }
}

function renderDeviceBreakdown(devices) {
  availableDevicesList = devices || [];
  updateLibraryDeviceSelectOptions();

  const container = document.getElementById('device-list');
  const fullContainer = document.getElementById('devices-full-list');

  if (!devices || devices.length === 0) {
    if (container) container.innerHTML = '<p class="text-muted">No devices connected.</p>';
    if (fullContainer) fullContainer.innerHTML = '<p class="text-muted">No available devices.</p>';
    return;
  }

  let html = `
    <table>
      <thead>
        <tr>
          <th style="min-width: 220px;">Device / Source</th>
          <th style="width: 130px;">Type</th>
          <th style="width: 140px;" class="col-center">Song Count</th>
          <th style="width: 120px;" class="col-center">Status</th>
          <th style="width: 150px;" class="col-right">Action</th>
        </tr>
      </thead>
      <tbody>
  `;

  devices.forEach(d => {
    const isOnline = d.status === 'online' || d.status === 'active';
    const statusBadge = isOnline 
      ? '<span class="badge badge-online">ONLINE</span>' 
      : '<span class="badge badge-offline">OFFLINE</span>';
    
    html += `
      <tr onclick="openDeviceLibrary('${escapeJs(d.id)}', '${escapeJs(d.name)}')" style="cursor: pointer;" title="Click to open ${escapeHtml(d.name)} Song Library">
        <td>
          <strong style="color: var(--accent-orange); font-size: 0.92rem;">${escapeHtml(d.name)}</strong>
          <br><small class="text-muted">${escapeHtml(d.details || d.serial || '')}</small>
        </td>
        <td><span class="badge badge-purple">${escapeHtml(d.type)}</span></td>
        <td class="col-center text-tabular"><strong>${d.count}</strong> songs</td>
        <td class="col-center">${statusBadge}</td>
        <td class="col-right">
          <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); openDeviceLibrary('${escapeJs(d.id)}', '${escapeJs(d.name)}')" title="View Library">
            View Library ${SVG_CHEVRON_RIGHT}
          </button>
        </td>
      </tr>
    `;
  });
  html += '</tbody></table>';

  if (container) container.innerHTML = html;
  if (fullContainer) fullContainer.innerHTML = html;
}

function updateLibraryDeviceSelectOptions() {
  const sel = document.getElementById('library-device-select');
  if (!sel || availableDevicesList.length === 0) return;
  sel.innerHTML = availableDevicesList.map(d => 
    `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${d.count} songs)</option>`
  ).join('');
  sel.value = currentDeviceId;
}

function openDeviceLibrary(deviceId, deviceName) {
  currentDeviceId = deviceId || 'local';
  if (deviceName) currentDeviceName = deviceName;
  switchTab('tab-library');
  loadDeviceSongs(currentDeviceId);
}

function onLibraryDeviceSelectChange(deviceId) {
  currentDeviceId = deviceId;
  loadDeviceSongs(deviceId);
}


async function scanAdbDevices() {
  const statusEl = document.getElementById('ip-add-status');
  if (statusEl) statusEl.textContent = 'Scanning connected ADB devices...';
  try {
    const res = await fetch('/api/devices/scan-adb', { method: 'POST' });
    const data = await res.json();
    if (statusEl) statusEl.textContent = `Scanned ${data.devices ? data.devices.length : 0} ADB devices.`;
    loadDashboardStats();
  } catch (err) {
    console.error('Error scanning ADB devices:', err);
    if (statusEl) statusEl.textContent = 'Error scanning ADB devices.';
  }
}

async function scanIpHosts() {
  const statusEl = document.getElementById('ip-add-status');
  if (statusEl) statusEl.textContent = 'Pinging saved Over-IP peer devices...';
  try {
    const res = await fetch('/api/devices/scan-ip', { method: 'POST' });
    const data = await res.json();
    if (statusEl) statusEl.textContent = `Pings complete. ${data.devices ? data.devices.length : 0} Over-IP peers processed.`;
    loadDashboardStats();
  } catch (err) {
    console.error('Error pinging Over-IP hosts:', err);
    if (statusEl) statusEl.textContent = 'Error pinging Over-IP devices.';
  }
}

async function addOverIpDevice() {
  const ipInput = document.getElementById('input-ip-addr');
  const portInput = document.getElementById('input-ip-port');
  const statusEl = document.getElementById('ip-add-status');

  const ip = ipInput ? ipInput.value.trim() : '';
  const port = portInput ? parseInt(portInput.value) || 5000 : 5000;

  if (!ip) {
    if (statusEl) statusEl.textContent = 'Please enter a valid IP address!';
    return;
  }

  if (statusEl) statusEl.textContent = `Adding and pinging Over-IP peer ${ip}:${port}...`;

  try {
    const res = await fetch('/api/devices/add-ip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip: ip, port: port })
    });
    const data = await res.json();
    if (data.status === 'success') {
      if (statusEl) statusEl.textContent = `Successfully added and probed ${ip}:${port}.`;
      if (ipInput) ipInput.value = '';
      loadDashboardStats();
    } else {
      if (statusEl) statusEl.textContent = `Error: ${data.error || 'Failed to add IP'}`;
    }
  } catch (err) {
    console.error('Error adding Over-IP device:', err);
    if (statusEl) statusEl.textContent = 'Error adding Over-IP peer host.';
  }
}

// =============================================================================
// PLAYER MODULE: Audio Engine, Bottom Bar, Queue Panel, Liked Songs & Player Tab
// =============================================================================

// --- BESPOKE AUDIO PLAYER ENGINE ---

function formatDuration(sec) {
  if (isNaN(sec) || !isFinite(sec) || sec < 0) return '0:00';
  const minutes = Math.floor(sec / 60);
  const seconds = Math.floor(sec % 60);
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

const SVG_VOL_HIGH = `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>`;
const SVG_VOL_MUTED = `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>`;

function initAudioPlayer() {
  const player = document.getElementById('audio-player');
  const scrubber = document.getElementById('player-scrubber');
  const curTimeEl = document.getElementById('player-current-time');
  const totalTimeEl = document.getElementById('player-total-time');
  const volSlider = document.getElementById('player-volume');
  if (!player) return;

  // Restore saved volume
  const savedVol = localStorage.getItem('antigravity_player_volume');
  if (savedVol !== null) {
    const v = parseFloat(savedVol);
    player.volume = isNaN(v) ? 1 : Math.max(0, Math.min(1, v));
    if (volSlider) volSlider.value = player.volume;
  }
  updatePlayerVolumeIcon();

  player.onplay = () => setPlayerPlayState(true);
  player.onpause = () => setPlayerPlayState(false);
  player.onended = () => handleTrackEnded();

  player.ontimeupdate = () => {
    if (!isScrubbing && scrubber && player.duration) {
      scrubber.value = player.currentTime;
      if (curTimeEl) curTimeEl.textContent = formatDuration(player.currentTime);
      updateScrubberProgress(player.currentTime, player.duration);
    }
  };

  player.onloadedmetadata = () => {
    if (scrubber) {
      scrubber.min = 0;
      scrubber.max = player.duration || 100;
      scrubber.value = player.currentTime || 0;
    }
    if (totalTimeEl) {
      totalTimeEl.textContent = formatDuration(player.duration);
    }
    updateScrubberProgress(player.currentTime || 0, player.duration || 100);
  };

  player.onvolumechange = () => {
    if (volSlider) volSlider.value = player.muted ? 0 : player.volume;
    updatePlayerVolumeIcon();
  };

  setupPlayerKeyboardHotkeys();
}

function updateScrubberProgress(current, total) {
  const scrubber = document.getElementById('player-scrubber');
  if (!scrubber || !total) return;
  const pct = Math.min(100, Math.max(0, (current / total) * 100));
  scrubber.style.background = `linear-gradient(to right, var(--accent-yellow) ${pct}%, #262626 ${pct}%)`;
}

function onScrubberInput(val) {
  isScrubbing = true;
  const player = document.getElementById('audio-player');
  const curTimeEl = document.getElementById('player-current-time');
  const v = parseFloat(val);
  if (curTimeEl) curTimeEl.textContent = formatDuration(v);
  if (player && player.duration) {
    updateScrubberProgress(v, player.duration);
  }
}

function onScrubberChange(val) {
  const player = document.getElementById('audio-player');
  if (player) {
    player.currentTime = parseFloat(val);
  }
  isScrubbing = false;
}

function onVolumeInput(val) {
  const player = document.getElementById('audio-player');
  if (!player) return;
  const v = parseFloat(val);
  player.volume = isNaN(v) ? 1 : Math.max(0, Math.min(1, v));
  player.muted = false;
  localStorage.setItem('antigravity_player_volume', player.volume);
  updatePlayerVolumeIcon();
}

function togglePlayerMute() {
  const player = document.getElementById('audio-player');
  const volSlider = document.getElementById('player-volume');
  if (!player) return;
  player.muted = !player.muted;
  if (volSlider) {
    volSlider.value = player.muted ? 0 : player.volume;
  }
  updatePlayerVolumeIcon();
}

function updatePlayerVolumeIcon() {
  const player = document.getElementById('audio-player');
  const icon = document.getElementById('player-vol-icon');
  if (!player || !icon) return;
  const isMuted = player.muted || player.volume === 0;
  icon.innerHTML = isMuted ? SVG_VOL_MUTED : SVG_VOL_HIGH;
}

function togglePlayerLoop() {
  isPlayerLooping = !isPlayerLooping;
  const player = document.getElementById('audio-player');
  if (player) player.loop = isPlayerLooping;
  const loopBtn = document.getElementById('btn-player-loop');
  if (loopBtn) {
    if (isPlayerLooping) {
      loopBtn.style.color = 'var(--accent-yellow)';
      loopBtn.title = 'Repeat Mode: Active (Loop)';
    } else {
      loopBtn.style.color = '';
      loopBtn.title = 'Toggle Repeat Mode';
    }
  }
}

function toggleShuffle() {
  const shuffleBtn = document.getElementById('btn-player-shuffle');
  if (isShuffled) {
    // Restore original order and find current track's new position
    const currentPath = currentTrackPath;
    activeQueue = [...originalQueue];
    queueIndex = activeQueue.findIndex(t => t.filepath === currentPath);
    if (queueIndex < 0) queueIndex = 0;
    isShuffled = false;
    if (shuffleBtn) shuffleBtn.classList.remove('shuffle-on');
    if (shuffleBtn) shuffleBtn.title = 'Shuffle Off';
  } else {
    // Save original and shuffle
    originalQueue = [...activeQueue];
    const currentTrack = activeQueue[queueIndex];
    const rest = activeQueue.filter((_, i) => i !== queueIndex);
    for (let i = rest.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [rest[i], rest[j]] = [rest[j], rest[i]];
    }
    activeQueue = [currentTrack, ...rest];
    queueIndex = 0;
    isShuffled = true;
    if (shuffleBtn) shuffleBtn.classList.add('shuffle-on');
    if (shuffleBtn) shuffleBtn.title = 'Shuffle On — click to disable';
  }
  renderQueuePanel();
}

function seekRelative(sec) {
  const player = document.getElementById('audio-player');
  if (!player || !player.duration) return;
  player.currentTime = Math.max(0, Math.min(player.duration, player.currentTime + sec));
}

function playPreviousTrack() {
  const player = document.getElementById('audio-player');
  if (player && player.currentTime > 3) {
    player.currentTime = 0;
    return;
  }
  if (activeQueue && activeQueue.length > 0) {
    if (queueIndex > 0) {
      queueIndex--;
      const prevTrack = activeQueue[queueIndex];
      playAudio(prevTrack.filepath, prevTrack.title, prevTrack.artist, activeQueue, queueIndex, prevTrack.bitrate_kbps, prevTrack.device_id);
    } else if (isPlayerLooping) {
      queueIndex = activeQueue.length - 1;
      const lastTrack = activeQueue[queueIndex];
      playAudio(lastTrack.filepath, lastTrack.title, lastTrack.artist, activeQueue, queueIndex, lastTrack.bitrate_kbps, lastTrack.device_id);
    } else if (player) {
      player.currentTime = 0;
    }
  }
}

function playNextTrack() {
  if (activeQueue && activeQueue.length > 0) {
    if (queueIndex + 1 < activeQueue.length) {
      queueIndex++;
      const nextTrack = activeQueue[queueIndex];
      playAudio(nextTrack.filepath, nextTrack.title, nextTrack.artist, activeQueue, queueIndex, nextTrack.bitrate_kbps, nextTrack.device_id);
    } else if (isPlayerLooping) {
      queueIndex = 0;
      const firstTrack = activeQueue[0];
      playAudio(firstTrack.filepath, firstTrack.title, firstTrack.artist, activeQueue, 0, firstTrack.bitrate_kbps, firstTrack.device_id);
    } else {
      setPlayerPlayState(false);
    }
  } else {
    setPlayerPlayState(false);
  }
}

function closeAudioPlayer() {
  const player = document.getElementById('audio-player');
  const playerBar = document.getElementById('audio-player-bar');
  if (player) {
    player.pause();
    player.src = '';
  }
  if (playerBar) {
    playerBar.style.display = 'none';
  }
  currentTrackPath = null;
  setPlayerPlayState(false);
}

function setupPlayerKeyboardHotkeys() {
  document.addEventListener('keydown', (e) => {
    const active = document.activeElement;
    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT' || active.isContentEditable)) {
      if (e.key === 'Escape') {
        active.blur();
      }
      return;
    }

    if (e.key === ' ' || e.code === 'Space') {
      e.preventDefault();
      togglePlayPause();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      seekRelative(-5);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      seekRelative(5);
    } else if (e.key === 'j' || e.key === 'J') {
      e.preventDefault();
      playPreviousTrack();
    } else if (e.key === 'k' || e.key === 'K') {
      e.preventDefault();
      playNextTrack();
    } else if (e.key === 'm' || e.key === 'M') {
      e.preventDefault();
      togglePlayerMute();
    } else if (e.key === 'l' || e.key === 'L') {
      e.preventDefault();
      toggleCurrentTrackLike();
    } else if (e.key === 'Escape') {
      closeConfirmModal(false);
      hideAddToPlaylistModal();
      hideCreatePlaylistModal();
      hideBatchDeleteDuplicatesModal();
      hideDeviceUploadModal();
      hideTranscodeModal();
      hideSyncSongModal();
      closeAudioPlayer();
    } else if (e.key === '/') {
      const searchInput = document.getElementById('lib-search');
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
    }
  });
}

function setPlayerPlayState(playing) {
  isPlaying = playing;
  const playPauseBtn = document.getElementById('btn-player-playpause');
  if (playPauseBtn) {
    playPauseBtn.innerHTML = isPlaying ? SVG_PAUSE : SVG_PLAY;
    playPauseBtn.title = isPlaying ? 'Pause (Space)' : 'Play (Space)';
  }
  renderLibraryPage();
  if (selectedPlaylist) {
    renderPlaylistTracks();
  }
}

function togglePlayPause() {
  const player = document.getElementById('audio-player');
  if (!player || !player.src) return;

  if (player.paused) {
    player.play().catch(err => console.warn('Play error:', err));
  } else {
    player.pause();
  }
}

function playOrToggleAudio(filepath, title, artist, index = -1, bitrate = '', deviceId = null) {
  const targetDev = deviceId || currentDeviceId || 'local';
  const player = document.getElementById('audio-player');
  if (currentTrackPath === filepath && player && player.src) {
    togglePlayPause();
  } else {
    let queue = null;
    let qIdx = 0;
    if (index >= 0 && filteredSongs && filteredSongs.length > 0) {
      queue = filteredSongs.map(s => ({ ...s, device_id: s.device_id || targetDev }));
      qIdx = index;
    }
    playAudio(filepath, title, artist, queue, qIdx, bitrate, targetDev);
  }
}

function playAudio(filepath, title, artist, queue = null, index = 0, bitrate = null, deviceId = null) {
  const player = document.getElementById('audio-player');
  const playerBar = document.getElementById('audio-player-bar');
  const titleEl = document.getElementById('player-title');
  const artistEl = document.getElementById('player-artist');
  const badgeEl = document.getElementById('player-quality-badge');

  if (player && playerBar) {
    const trackDeviceId = deviceId || (queue && queue[index] && queue[index].device_id) || currentDeviceId || 'local';
    currentTrackPath = filepath;
    if (queue && queue.length > 0) {
      activeQueue = queue.map(item => ({ ...item, device_id: item.device_id || trackDeviceId }));
      queueIndex = index;
    } else {
      activeQueue = [{ filepath, title, artist, bitrate_kbps: bitrate, device_id: trackDeviceId }];
      queueIndex = 0;
    }

    const streamUrl = `/api/song/stream?filepath=${encodeURIComponent(filepath)}` +
      (trackDeviceId && trackDeviceId !== 'local' ? `&device_id=${encodeURIComponent(trackDeviceId)}` : '');
    player.src = streamUrl;
    if (titleEl) titleEl.textContent = title || 'Unknown Title';
    if (artistEl) {
      artistEl.textContent = (trackDeviceId && trackDeviceId !== 'local')
        ? `${artist || 'Unknown Artist'} • (${currentDeviceName || trackDeviceId})`
        : (artist || 'Unknown Artist');
    }

    const bVal = bitrate || (activeQueue[queueIndex] && activeQueue[queueIndex].bitrate_kbps);
    if (badgeEl) {
      if (bVal && bVal !== 'Unknown') {
        badgeEl.textContent = bVal;
        badgeEl.style.display = 'inline-block';
      } else {
        badgeEl.style.display = 'none';
      }
    }

    playerBar.style.display = 'flex';
    player.play().catch(err => console.warn('Playback error:', err));

    // Update queue panel and player-tab song row highlights
    renderQueuePanel();
    updatePlayerTabRowHighlight();
    updateAllLikeButtonsUI();
  }
}

function handleTrackEnded() {
  if (activeQueue && queueIndex + 1 < activeQueue.length) {
    playNextTrack();
  } else if (isPlayerLooping && activeQueue && activeQueue.length > 0) {
    playNextTrack();
  } else {
    setPlayerPlayState(false);
  }
}

// --- LIKED MUSIC SYSTEM JS LOGIC ---

async function loadLikedMusicSet() {
  try {
    const res = await fetch('/api/playlists');
    if (!res.ok) return;
    const playlists = await res.json() || [];
    let likedPl = playlists.find(p => p.name === 'Liked Music');
    if (likedPl) {
      likedPlaylistId = likedPl.id;
      const trRes = await fetch(`/api/playlists/${likedPl.id}/tracks`);
      if (trRes.ok) {
        const tracks = await trRes.json() || [];
        likedSongPaths = new Set(tracks.map(t => t.filepath));
        updateAllLikeButtonsUI();
      }
    }
  } catch (e) {
    console.warn('Failed to load liked music set:', e);
  }
}

async function toggleLikeTrack(filepath, title, artist) {
  if (!filepath) return;
  try {
    if (!likedPlaylistId) {
      const plRes = await fetch('/api/playlists');
      const playlists = await plRes.json() || [];
      let likedPl = playlists.find(p => p.name === 'Liked Music');
      if (!likedPl) {
        const createRes = await fetch('/api/playlists/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Liked Music' })
        });
        const created = await createRes.json();
        likedPl = created.playlist;
      }
      if (likedPl) likedPlaylistId = likedPl.id;
    }

    const isLiked = likedSongPaths.has(filepath);
    if (isLiked) {
      await fetch(`/api/playlists/${likedPlaylistId}/remove-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath })
      });
      likedSongPaths.delete(filepath);
      showToast(`Removed "${title || 'Track'}" from Liked Music`, 'info', 2000);
    } else {
      await fetch(`/api/playlists/${likedPlaylistId}/add-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath })
      });
      likedSongPaths.add(filepath);
      showToast(`Added "${title || 'Track'}" to Liked Music ❤️`, 'success', 2000);
    }

    updateAllLikeButtonsUI();

    if (selectedPlaylist && selectedPlaylist.id === likedPlaylistId) {
      selectPlaylist(likedPlaylistId, 'Liked Music');
    }
    if (currentFormatFilter === 'liked') {
      applyLibraryFilterAndSort();
    }
    loadPlaylists();
  } catch (err) {
    console.error('Error toggling like:', err);
    showToast('Failed to update liked state: ' + err.message, 'error', 3000);
  }
}

function toggleCurrentTrackLike() {
  if (!currentTrackPath) {
    showToast('No track is currently playing', 'info', 2000);
    return;
  }
  const curTrack = activeQueue && activeQueue[queueIndex] ? activeQueue[queueIndex] : null;
  const title = curTrack ? curTrack.title : '';
  const artist = curTrack ? curTrack.artist : '';
  toggleLikeTrack(currentTrackPath, title, artist);
}

function updateAllLikeButtonsUI() {
  // Update player bar like button
  const playerLikeBtn = document.getElementById('btn-player-like');
  const playerLikeIcon = document.getElementById('player-like-icon');
  if (playerLikeBtn) {
    const isLiked = Boolean(currentTrackPath && likedSongPaths.has(currentTrackPath));
    playerLikeBtn.classList.toggle('liked', isLiked);
    if (playerLikeIcon) {
      playerLikeIcon.innerHTML = isLiked
        ? '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" fill="#ff0055" stroke="#ff0055"/>'
        : '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>';
    }
  }

  // Update library table rows & player rows
  document.querySelectorAll('.btn-song-like').forEach(btn => {
    const fp = btn.dataset.filepath;
    if (fp) {
      const isLiked = likedSongPaths.has(fp);
      btn.classList.toggle('btn-liked', isLiked);
      btn.innerHTML = isLiked ? SVG_HEART_FILLED : SVG_HEART;
      btn.title = isLiked ? 'Unlike' : 'Like';
    }
  });
}


// MUSIC PLAYER TAB — Library Picker, Song List, Queue Panel, Shuffle
// =============================================================================

// Player-tab internal state
var _playerLibRefreshTimer = null;

/**
 * Called once on DOMContentLoaded. Populates the library dropdown and
 * loads the initial player library songs.
 */
async function initPlayerTab() {
  await refreshPlayerLibraryList(false);
  const sel = document.getElementById('player-library-select');
  const devId = sel ? sel.value : 'local';
  if (!playerTabSongs || playerTabSongs.length === 0) {
    loadPlayerLibrary(devId, false);
  }
}

/**
 * Fetch /api/devices and rebuild the library picker <select>.
 * If reloadSongs is true or songs are not yet loaded, also loads the songs for the selected library.
 */
async function refreshPlayerLibraryList(reloadSongs = false) {
  const sel = document.getElementById('player-library-select');
  const status = document.getElementById('player-lib-status');
  if (!sel) return;

  try {
    const res = await fetch('/api/devices');
    if (!res.ok) throw new Error('Failed to fetch devices');
    const devices = await res.json();

    // Keep current selection
    const prev = sel.value || playerTabDeviceId || 'local';

    // Rebuild options
    let html = '<option value="local">🏠 Local Storage</option>';
    if (Array.isArray(devices)) {
      devices.forEach(d => {
        const val = d.device_id || d.serial || d.ip_port;
        if (!val || val === 'local') return;
        const icon = d.device_type === 'Over-IP' ? '🌐' : '📱';
        const label = d.device_name || d.description || val;
        const online = d.is_online !== false ? '' : ' (offline)';
        html += `<option value="${escHtml(val)}">${icon} ${escHtml(label)}${online}</option>`;
      });
    }
    sel.innerHTML = html;

    // Restore previous selection if still available, else fallback to 'local'
    const opts = Array.from(sel.options).map(o => o.value);
    sel.value = opts.includes(prev) ? prev : 'local';

    if (status) {
      const cnt = sel.options.length - 1;
      status.textContent = cnt > 0 ? `${cnt} device${cnt !== 1 ? 's' : ''} found` : 'No remote devices';
    }

    if (reloadSongs || !playerTabSongs || playerTabSongs.length === 0) {
      await loadPlayerLibrary(sel.value, reloadSongs);
    }
  } catch (err) {
    console.warn('[PlayerTab] Could not refresh device list:', err);
    if (status) status.textContent = 'Could not load devices';
  }
}

/**
 * Load songs for the selected library into the player-tab song table.
 */
async function loadPlayerLibrary(deviceId, forceRefresh = false) {
  if (!deviceId) deviceId = 'local';
  playerTabDeviceId = deviceId;

  const tbody = document.getElementById('player-songs-tbody');
  const countEl = document.getElementById('player-song-count');
  if (!tbody) return;

  // Fast path: if device is 'local' and allSongs already loaded, reuse immediately without network wait
  if (deviceId === 'local' && allSongs && allSongs.length > 0 && !forceRefresh) {
    playerTabSongs = allSongs;
    playerTabFiltered = [...allSongs];
    renderPlayerSongTable(playerTabFiltered, deviceId);
    if (countEl) countEl.textContent = `${allSongs.length.toLocaleString()} songs`;
    return;
  }

  tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">⏳ Loading songs…</td></tr>';
  if (countEl) countEl.textContent = '';

  try {
    const url = `/api/devices/${encodeURIComponent(deviceId)}/songs${forceRefresh ? '?refresh=true' : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const songs = data.songs || [];

    playerTabSongs = songs;
    playerTabFiltered = [...songs];

    // If local library is loaded and allSongs is empty, also share with allSongs
    if (deviceId === 'local' && (!allSongs || allSongs.length === 0)) {
      allSongs = songs;
    }

    if (songs.length === 0) {
      if (deviceId === 'local') {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">No local songs indexed yet. Go to <strong>Music Library → Scan / Refresh</strong> to scan your library first.</td></tr>';
      } else {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">No songs found on this device.</td></tr>';
      }
      if (countEl) countEl.textContent = '0 songs';
      return;
    }

    renderPlayerSongTable(playerTabFiltered, deviceId);
    if (countEl) countEl.textContent = `${songs.length.toLocaleString()} songs`;
  } catch (err) {
    console.error('[PlayerTab] Failed to load songs:', err);
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--status-offline);text-align:center;padding:2rem;">❌ Failed to load songs: ${escHtml(String(err))}</td></tr>`;
  }
}

/**
 * Render the player-tab song table from a song array.
 */
function renderPlayerSongTable(songs, deviceId) {
  const tbody = document.getElementById('player-songs-tbody');
  if (!tbody) return;

  if (!songs || songs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">No songs found.</td></tr>';
    return;
  }

  const rows = songs.map((s, i) => {
    const fp = s.filepath || s._data || '';
    const title = escHtml(s.title || s.filename || fp.split('/').pop() || 'Unknown');
    const artist = escHtml(s.artist || 'Unknown');
    const album = escHtml(s.album || '—');
    const bitrate = s.bitrate_kbps && s.bitrate_kbps !== 'Unknown' ? `<span class="badge badge-yellow" style="font-size:0.7rem;">${escHtml(String(s.bitrate_kbps))}</span>` : '—';
    const isActive = fp && fp === currentTrackPath;
    const rowClass = isActive ? ' class="player-row-active"' : '';
    const btnClass = isActive ? ' playing' : '';
    const btnIcon = isActive && isPlaying
      ? '<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px;"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
      : '<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px;"><polygon points="5 3 19 12 5 21 5 3"/></svg>';

    return `<tr data-filepath="${escHtml(fp)}"${rowClass}>
      <td style="color:var(--text-muted);font-size:0.75rem;">${i + 1}</td>
      <td title="${title}">${title}</td>
      <td class="col-hide-sm" title="${artist}">${artist}</td>
      <td class="col-hide-md" title="${album}">${album}</td>
      <td class="col-right col-hide-sm">${bitrate}</td>
      <td class="col-center" style="white-space:nowrap;">
        <button class="btn btn-secondary btn-sm btn-song-like ${likedSongPaths.has(fp) ? 'btn-liked' : ''}" data-filepath="${escHtml(fp)}" onclick="toggleLikeTrack('${escapeJs(fp)}', '${escapeJs(s.title || s.filename || '')}', '${escapeJs(s.artist || '')}')" title="${likedSongPaths.has(fp) ? 'Unlike' : 'Like'}" style="padding:0.25rem 0.4rem;margin-right:0.35rem;border-radius:6px;">${likedSongPaths.has(fp) ? SVG_HEART_FILLED : SVG_HEART}</button>
        <button class="player-row-play-btn${btnClass}" title="Play ${title}"
          onclick="playerTabPlaySong('${escapeJs(fp)}', ${i}, '${escapeJs(deviceId)}')">${btnIcon}</button>
      </td>
    </tr>`;
  });

  tbody.innerHTML = rows.join('');
}

/**
 * Play a song from the player tab, loading all filtered songs as the queue.
 */
function playerTabPlaySong(filepath, index, deviceId) {
  if (!playerTabFiltered || playerTabFiltered.length === 0) return;

  // Build queue with device_id on each entry
  const queue = playerTabFiltered.map(s => ({ ...s, device_id: deviceId || 'local' }));
  const track = queue[index] || queue[0];
  if (!track) return;

  // If shuffle was active, reset it since we're starting a new queue
  if (isShuffled) {
    isShuffled = false;
    originalQueue = [];
    const shuffleBtn = document.getElementById('btn-player-shuffle');
    if (shuffleBtn) shuffleBtn.classList.remove('shuffle-on');
  }

  playAudio(
    track.filepath || track._data,
    track.title,
    track.artist,
    queue,
    index,
    track.bitrate_kbps,
    deviceId
  );
}

/**
 * Play All — starts from the first song in the current filtered list.
 */
function playerPlayAll() {
  if (!playerTabFiltered || playerTabFiltered.length === 0) return;
  playerTabPlaySong(playerTabFiltered[0].filepath || playerTabFiltered[0]._data, 0, playerTabDeviceId);
}

/**
 * Shuffle All — plays the library in shuffled order starting from a random song.
 */
function playerShuffleAll() {
  if (!playerTabFiltered || playerTabFiltered.length === 0) return;
  const idx = Math.floor(Math.random() * playerTabFiltered.length);
  playerTabPlaySong(playerTabFiltered[idx].filepath || playerTabFiltered[idx]._data, idx, playerTabDeviceId);
  // After loading queue, enable shuffle
  if (!isShuffled) toggleShuffle();
}

/**
 * Filter the player-tab song list by the search box.
 */
function filterPlayerSongs() {
  const q = (document.getElementById('player-search')?.value || '').toLowerCase().trim();
  if (!q) {
    playerTabFiltered = [...playerTabSongs];
  } else {
    playerTabFiltered = playerTabSongs.filter(s =>
      (s.title || '').toLowerCase().includes(q) ||
      (s.artist || '').toLowerCase().includes(q) ||
      (s.album || '').toLowerCase().includes(q) ||
      (s.filename || '').toLowerCase().includes(q)
    );
  }
  const countEl = document.getElementById('player-song-count');
  if (countEl) {
    countEl.textContent = q
      ? `${playerTabFiltered.length} / ${playerTabSongs.length} songs`
      : `${playerTabSongs.length.toLocaleString()} songs`;
  }
  renderPlayerSongTable(playerTabFiltered, playerTabDeviceId);
}

/**
 * Update which row in the player-tab table is highlighted as "now playing".
 */
function updatePlayerTabRowHighlight() {
  const tbody = document.getElementById('player-songs-tbody');
  if (!tbody) return;
  tbody.querySelectorAll('tr[data-filepath]').forEach(row => {
    const fp = row.getAttribute('data-filepath');
    if (fp === currentTrackPath) {
      row.classList.add('player-row-active');
    } else {
      row.classList.remove('player-row-active');
    }
  });
}

/**
 * Render the queue panel with current activeQueue.
 */
function renderQueuePanel() {
  const list = document.getElementById('player-queue-list');
  const countEl = document.getElementById('player-queue-count');
  if (!list) return;

  if (!activeQueue || activeQueue.length === 0) {
    list.innerHTML = '<div class="text-muted" style="padding:1.5rem 1rem;text-align:center;font-size:0.85rem;">No tracks in queue yet.</div>';
    if (countEl) countEl.textContent = '';
    return;
  }

  if (countEl) countEl.textContent = `${activeQueue.length} tracks`;

  list.innerHTML = activeQueue.map((t, i) => {
    const isActive = i === queueIndex;
    const title = escHtml(t.title || t.filename || (t.filepath || '').split('/').pop() || 'Unknown');
    const artist = escHtml(t.artist || 'Unknown');
    const cls = isActive ? ' queue-active' : '';
    const prefix = isActive
      ? '<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor" style="width:10px;height:10px;flex-shrink:0;"><polygon points="5 3 19 12 5 21 5 3"/></svg>'
      : '';
    return `<div class="player-queue-item${cls}" onclick="playerQueueJumpTo(${i})" title="${title}">
      <span class="q-num">${prefix || (i + 1)}</span>
      <div class="q-info">
        <div class="q-title">${title}</div>
        <div class="q-artist">${artist}</div>
      </div>
    </div>`;
  }).join('');

  // Scroll active item into view
  const activeEl = list.querySelector('.queue-active');
  if (activeEl) activeEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

/**
 * Jump to a specific track in the active queue.
 */
function playerQueueJumpTo(index) {
  if (!activeQueue || index < 0 || index >= activeQueue.length) return;
  const t = activeQueue[index];
  playAudio(
    t.filepath || t._data,
    t.title,
    t.artist,
    activeQueue,
    index,
    t.bitrate_kbps,
    t.device_id
  );
}

/**
 * Clear the current play queue and stop playback.
 */
function clearPlayerQueue() {
  activeQueue = [];
  originalQueue = [];
  queueIndex = 0;
  isShuffled = false;
  const shuffleBtn = document.getElementById('btn-player-shuffle');
  if (shuffleBtn) shuffleBtn.classList.remove('shuffle-on');
  renderQueuePanel();
  closeAudioPlayer();
}

/** Simple HTML escaping helper (may already exist, this is safe to duplicate). */
function escHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ==========================================
// =============================================================================
// LIBRARY MODULE: Music Library Browsing, Filter, Sort, Pagination, Upload, Transcode
// =============================================================================

function refreshCurrentDeviceLibrary() {
  streamDeviceSongs(currentDeviceId);
}

let libEventSource = null;

function applyDeviceLibraryData(data) {
  currentDeviceName = data.device_name || currentDeviceId;
  currentDeviceType = data.device_type || 'Storage';
  allSongs = data.songs || [];

  const titleEl = document.getElementById('library-title-text');
  if (titleEl) titleEl.textContent = currentDeviceName;

  const badgeEl = document.getElementById('library-device-badge');
  if (badgeEl) badgeEl.textContent = `${currentDeviceType} (${allSongs.length} songs)`;

  const selectEl = document.getElementById('library-device-select');
  if (selectEl) selectEl.value = currentDeviceId;

  applyLibraryFilterAndSort();
}

function streamDeviceSongs(deviceId = 'local', showTerminal = true, forceRefresh = showTerminal) {
  currentDeviceId = deviceId;
  if (libEventSource) {
    libEventSource.close();
    libEventSource = null;
  }

  const btn = document.getElementById('btn-refresh-library');
  const terminal = document.getElementById('lib-terminal');
  const termLog = document.getElementById('lib-terminal-log');
  const tbody = document.getElementById('songs-tbody');

  if (showTerminal && terminal) terminal.style.display = 'block';
  if (showTerminal && termLog) termLog.innerHTML = '';
  if (btn && showTerminal) {
    btn.disabled = true;
    btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Scanning…`;
  }
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-muted">Loading music library…</td></tr>';
  }

  const url = `/api/devices/${encodeURIComponent(deviceId)}/songs/stream?refresh=${forceRefresh ? 'true' : 'false'}`;
  const evtSource = new EventSource(url);
  libEventSource = evtSource;

  function appendLibLog(msg) {
    pushTermLine(termLog, msg);
  }

  evtSource.onmessage = (e) => {
    let payload;
    try { payload = JSON.parse(e.data); } catch { return; }

    if (payload.type === 'log') {
      appendLibLog(payload.msg);
    } else if (payload.type === 'done') {
      appendLibLog('[DONE] Library scan complete!');
      evtSource.close();
      libEventSource = null;

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Scan / Refresh`;
      }

      const data = payload.result || {};
      applyDeviceLibraryData(data);

      if (showTerminal) {
        loadDashboardStats();

        // Collapse terminal after 2.5 seconds
        setTimeout(() => {
          if (terminal) terminal.style.display = 'none';
        }, 2500);
      }
    } else if (payload.type === 'error') {
      appendLibLog('[ERROR] ' + (payload.msg || 'Scan failed.'));
      evtSource.close();
      libEventSource = null;
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Scan / Refresh`;
      }
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-muted" style="color: var(--status-offline) !important;">Scan failed.</td></tr>';
      }
    }
  };

  evtSource.onerror = () => {
    if (evtSource.readyState === EventSource.CLOSED) return;
    evtSource.close();
    libEventSource = null;
    appendLibLog('[ERROR] Connection to server lost.');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Scan / Refresh`;
    }
    if (!showTerminal) {
      // Quiet loads should never block on a cold cache: fall back to the cached
      // library fetch once if the stream could not be established.
      fetch(`/api/devices/${encodeURIComponent(deviceId)}/songs`)
        .then(r => r.json())
        .then(data => { applyDeviceLibraryData(data); })
        .catch(() => {});
    }
  };
}

// --- MUSIC LIBRARY SEARCH, SORTING & PAGINATION ---

async function loadDeviceSongs(deviceId = 'local', forceRefresh = false) {
  currentDeviceId = deviceId;
  if (forceRefresh) {
    streamDeviceSongs(deviceId, true, true);
    return;
  }

  // Fast direct load from SQLite / in-memory cache (< 5ms)
  try {
    const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/songs`);
    if (res.ok) {
      const data = await res.json();
      applyDeviceLibraryData(data);
      // If local DB is empty on first startup, trigger initial scan
      if (deviceId === 'local' && (!data.songs || data.songs.length === 0)) {
        streamDeviceSongs('local', true, true);
      }
      return;
    }
  } catch (err) {
    console.warn('[Dashboard] Direct songs fetch failed, falling back to stream:', err);
  }

  streamDeviceSongs(deviceId, false, false);
}

async function loadSongs() {
  await loadDeviceSongs(currentDeviceId);
}

function onLibrarySearchInput() {
  applyLibraryFilterAndSort();
}

function onLibrarySortChange(criteria) {
  currentSortCriteria = criteria;
  updateSortIcons(criteria);
  applyLibraryFilterAndSort();
}

function toggleLibrarySort(field) {
  let nextSort;
  if (currentSortCriteria.startsWith(field)) {
    nextSort = currentSortCriteria.endsWith('_desc') ? `${field}_asc` : `${field}_desc`;
  } else {
    nextSort = (field === 'title') ? 'title_asc' : `${field}_desc`;
  }

  const sel = document.getElementById('library-sort');
  if (sel) sel.value = nextSort;
  onLibrarySortChange(nextSort);
}

function updateSortIcons(criteria) {
  const fields = ['title', 'duration', 'size', 'bitrate', 'ctime', 'mtime'];
  fields.forEach(f => {
    const iconEl = document.getElementById(`sort-icon-${f}`);
    if (iconEl) {
      if (criteria.startsWith(f)) {
        iconEl.innerHTML = criteria.endsWith('_asc') ? SVG_CHEVRON_UP : SVG_CHEVRON_DOWN;
      } else {
        iconEl.innerHTML = '';
      }
    }
  });
}

function setLibraryFormatFilter(filter, btnEl) {
  currentFormatFilter = filter;
  document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.classList.toggle('active', chip === btnEl || chip.dataset.filter === filter);
  });
  applyLibraryFilterAndSort();
}

function clearLibrarySearch() {
  const input = document.getElementById('library-search');
  if (input) {
    input.value = '';
    applyLibraryFilterAndSort();
    input.focus();
  }
}

function applyLibraryFilterAndSort() {
  const searchInput = document.getElementById('library-search');
  const query = (searchInput?.value || '').trim().toLowerCase();
  const clearBtn = document.getElementById('library-search-clear');
  if (clearBtn) {
    clearBtn.style.display = query ? 'block' : 'none';
  }

  let list = allSongs;
  if (query) {
    list = allSongs.filter(s => {
      const text = `${s.title || ''} ${s.artist || ''} ${s.album || ''} ${s.filename || ''} ${s.filepath || ''}`.toLowerCase();
      return text.includes(query);
    });
  }

  // Format Filter
  if (currentFormatFilter && currentFormatFilter !== 'all') {
    list = list.filter(s => {
      const ext = (s.filepath || s.filename || '').split('.').pop().toLowerCase();
      const bitVal = s.bitrate_val || 0;
      if (currentFormatFilter === 'flac') return ext === 'flac' || ext === 'wav';
      if (currentFormatFilter === 'highres') return bitVal >= 320 || ext === 'flac' || ext === 'wav';
      if (currentFormatFilter === 'mp3') return ext === 'mp3';
      if (currentFormatFilter === 'm4a') return ext === 'm4a' || ext === 'aac';
      if (currentFormatFilter === 'other') return !['flac', 'wav', 'mp3', 'm4a', 'aac'].includes(ext);
      if (currentFormatFilter === 'liked') return likedSongPaths.has(s.filepath);
      return true;
    });
  }

  const sorted = [...list];
  sorted.sort((a, b) => {
    switch (currentSortCriteria) {
      case 'mtime_desc':
        return (b.mtime || 0) - (a.mtime || 0);
      case 'mtime_asc':
        return (a.mtime || 0) - (b.mtime || 0);
      case 'ctime_desc':
        return (b.ctime || 0) - (a.ctime || 0);
      case 'ctime_asc':
        return (a.ctime || 0) - (b.ctime || 0);
      case 'bitrate_desc':
        return (b.bitrate_val || 0) - (a.bitrate_val || 0);
      case 'bitrate_asc':
        return (a.bitrate_val || 0) - (b.bitrate_val || 0);
      case 'size_desc':
        return (b.size || 0) - (a.size || 0);
      case 'size_asc':
        return (a.size || 0) - (b.size || 0);
      case 'duration_desc':
        return (b.duration || b.duration_sec || 0) - (a.duration || a.duration_sec || 0);
      case 'duration_asc':
        return (a.duration || a.duration_sec || 0) - (b.duration || b.duration_sec || 0);
      case 'title_asc':
        return (a.title || '').localeCompare(b.title || '');
      case 'title_desc':
        return (b.title || '').localeCompare(a.title || '');
      default:
        return (b.ctime || 0) - (a.ctime || 0);
    }
  });

  filteredSongs = sorted;
  libPage = 1;
  renderLibraryPage();
}

function changeLibraryPage(delta) {
  const totalPages = Math.ceil(filteredSongs.length / libPageSize) || 1;
  libPage = Math.max(1, Math.min(totalPages, libPage + delta));
  renderLibraryPage();
}

function toggleLibrarySongSelection(filepath, isChecked) {
  if (isChecked) {
    selectedSongPaths.add(filepath);
  } else {
    selectedSongPaths.delete(filepath);
  }
  updateLibrarySelectionUI();
  const startIdx = (libPage - 1) * libPageSize;
  const pageSongs = filteredSongs.slice(startIdx, startIdx + libPageSize);
  const masterCb = document.getElementById('lib-select-all');
  if (masterCb) {
    masterCb.checked = (pageSongs.length > 0 && pageSongs.every(s => selectedSongPaths.has(s.filepath)));
  }
}

function toggleSelectAllLibrarySongs(isChecked) {
  const startIdx = (libPage - 1) * libPageSize;
  const pageSongs = filteredSongs.slice(startIdx, startIdx + libPageSize);
  pageSongs.forEach(s => {
    if (isChecked) {
      selectedSongPaths.add(s.filepath);
    } else {
      selectedSongPaths.delete(s.filepath);
    }
  });
  renderLibraryPage();
  updateLibrarySelectionUI();
}

function clearLibrarySelection() {
  selectedSongPaths.clear();
  const masterCb = document.getElementById('lib-select-all');
  if (masterCb) masterCb.checked = false;
  renderLibraryPage();
  updateLibrarySelectionUI();
}

function updateLibrarySelectionUI() {
  const bar = document.getElementById('lib-bulk-action-bar');
  const countEl = document.getElementById('lib-bulk-selected-count');
  const count = selectedSongPaths.size;

  if (countEl) countEl.textContent = count;
  if (bar) bar.style.display = (count > 0) ? 'flex' : 'none';
}

function openBulkDeleteLibraryModal() {
  const count = selectedSongPaths.size;
  if (count === 0) return;
  const paths = Array.from(selectedSongPaths);

  showConfirmModal({
    title: 'Delete Selected Songs',
    message: `Move ${count} selected song(s) to Trash (tmp/deleted/)?`,
    details: paths.slice(0, 8).map(p => p.split('/').pop() || p),
    confirmText: `Delete ${count} Songs`,
    confirmClass: 'btn btn-secondary btn-danger',
    onConfirm: async () => {
      try {
        const res = await fetch('/api/songs/batch-delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filepaths: paths })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast(`Moved ${data.deleted_count} songs to Trash`, 'success', 3500);
          clearLibrarySelection();
          await loadDeviceSongs(currentDeviceId, true);
          loadDashboardStats();
        } else {
          showToast(`Error deleting songs: ${data.error || data.message || 'Failed'}`, 'error', 4000);
        }
      } catch (err) {
        showToast('Network error while deleting songs.', 'error', 4000);
      }
    }
  });
}

function executeBulkHideSongs() {
  const count = selectedSongPaths.size;
  if (count === 0) return;
  const paths = Array.from(selectedSongPaths);

  showConfirmModal({
    title: 'Hide Selected Songs',
    message: `Hide ${count} selected song(s) from sync lists?`,
    details: paths.slice(0, 8).map(p => p.split('/').pop() || p),
    confirmText: `Hide ${count} Songs`,
    confirmClass: 'btn',
    onConfirm: async () => {
      let hiddenCount = 0;
      for (const fp of paths) {
        try {
          await fetch('/api/hide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filepath: fp })
          });
          hiddenCount++;
        } catch (e) {
          console.error(e);
        }
      }
      showToast(`Hid ${hiddenCount} song(s) from sync lists`, 'success', 3500);
      clearLibrarySelection();
      loadHiddenFiles();
      loadDashboardStats();
    }
  });
}

function openBulkPlaylistModal() {
  const count = selectedSongPaths.size;
  if (count === 0) return;
  const paths = Array.from(selectedSongPaths);

  const modal = document.getElementById('modal-add-to-playlist');
  const titleEl = document.getElementById('modal-track-title');
  if (titleEl) titleEl.textContent = `Batch adding ${count} selected song(s)`;
  targetTrackForPlaylist = { filepath: paths[0], filepaths: paths };
  if (modal) modal.style.display = 'flex';
}

function openBulkSyncModal() {
  const count = selectedSongPaths.size;
  if (count === 0) return;
  const paths = Array.from(selectedSongPaths);
  const firstSong = allSongs.find(s => s.filepath === paths[0]) || { filepath: paths[0], title: paths[0].split('/').pop() };

  openSyncSongModal(
    firstSong.filepath,
    `${count} Selected Tracks (Batch Sync)`,
    firstSong.artist || 'Multiple Artists',
    firstSong.duration_formatted || '',
    '',
    '',
    ''
  );
  const syncModal = document.getElementById('modal-sync-song');
  if (syncModal) {
    syncModal.dataset.batchPaths = JSON.stringify(paths);
  }
}

function renderLibraryPage() {
  const tbody = document.getElementById('songs-tbody');
  if (!tbody) return;

  if (!filteredSongs || filteredSongs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="text-muted">No songs matching search query.</td></tr>';
    updateLibraryPaginationInfo(0, 0, 0, 1);
    return;
  }

  const totalPages = Math.ceil(filteredSongs.length / libPageSize);
  const startIdx = (libPage - 1) * libPageSize;
  const pageSongs = filteredSongs.slice(startIdx, startIdx + libPageSize);

  const isLocalStorage = (currentDeviceId === 'local');
  const isOverIp = (currentDeviceId && (currentDeviceId.startsWith('ip_') || currentDeviceId.startsWith('ip:') || currentDeviceId.startsWith('http://') || currentDeviceId.startsWith('https://')));

  // Toggle Upload to Device button visibility
  const uploadBtn = document.getElementById('btn-upload-to-device');
  if (uploadBtn) {
    uploadBtn.style.display = (!isLocalStorage) ? 'inline-flex' : 'none';
  }

  let html = '';
  pageSongs.forEach((s, idx) => {
    const globalIdx = startIdx + idx + 1;
    const isThisTrackPlaying = (currentTrackPath === s.filepath && isPlaying);
    const playBtnIcon = isThisTrackPlaying ? SVG_PAUSE : SVG_PLAY;
    const playBtnText = isThisTrackPlaying ? 'Pause' : 'Play';
    const rowClass = isThisTrackPlaying ? 'class="playing-row"' : '';
    const eqHtml = isThisTrackPlaying ? '<span class="playing-equalizer"><span></span><span></span><span></span></span>' : '';

    const isSelected = selectedSongPaths.has(s.filepath);

    const isLiked = likedSongPaths.has(s.filepath);
    const likeBtn = `
      <button class="btn btn-secondary btn-sm btn-song-like ${isLiked ? 'btn-liked' : ''}" data-filepath="${escapeHtml(s.filepath)}" onclick="toggleLikeTrack('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}')" title="${isLiked ? 'Unlike' : 'Like'}">${isLiked ? SVG_HEART_FILLED : SVG_HEART}</button>
    `;

    let actionButtons = '';
    const moreBtn = `
      <button class="btn btn-secondary btn-sm action-btn-more" onclick="showAddToPlaylistModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}')" title="More actions">•••</button>
    `;

    if (isLocalStorage) {
      const bitrateNum = parseInt(s.bitrate_kbps, 10) || 0;
      const convertBtn = (bitrateNum >= 256 || bitrateNum === 320) ? `
        <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="showTranscodeModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.bitrate_kbps || '')}')" title="Downconvert Audio">${SVG_CONVERT} <span class="btn-text">Convert</span></button>
      ` : '';

      actionButtons = `
        <div class="action-btn-group">
          ${likeBtn}
          <button class="btn btn-secondary btn-sm" onclick="playOrToggleAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}', ${startIdx + idx}, '${escapeJs(s.bitrate_kbps || '')}', 'local')" title="${playBtnText}">${playBtnIcon} <span class="btn-text">${playBtnText}</span></button>
          <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="openSyncSongModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}', '${escapeJs(s.duration_formatted || '')}', '${escapeJs(s.size_formatted || '')}', '${escapeJs(s.bitrate_kbps || '')}', '${escapeJs(s.album || '')}')" title="Sync to target device">${SVG_SYNC} <span class="btn-text">Sync</span></button>
          ${convertBtn}
          <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="showAddToPlaylistModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}')" title="Add to Playlist">${SVG_PLUS} <span class="btn-text">Playlist</span></button>
          <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="hideSong('${escapeJs(s.filepath)}')" title="Hide song">${SVG_HIDE}</button>
          <button class="btn btn-secondary btn-danger btn-sm action-btn-secondary" onclick="deleteSong('${escapeJs(s.filepath)}', event, '${escapeJs(currentDeviceId)}', '${escapeJs(s._id || '')}', '${escapeJs(s.filename || '')}')" title="Delete song">${SVG_TRASH}</button>
          ${moreBtn}
        </div>
      `;
    } else if (isOverIp) {
      actionButtons = `
        <div class="action-btn-group">
          ${likeBtn}
          <button class="btn btn-secondary btn-sm" style="color: var(--accent-yellow); border-color: rgba(250, 204, 21, 0.4);" onclick="playOrToggleAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}', ${startIdx + idx}, '${escapeJs(s.bitrate_kbps || '')}', '${escapeJs(currentDeviceId)}')" title="${playBtnText}">${playBtnIcon} <span class="btn-text">${playBtnText}</span></button>
          <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="showAddToPlaylistModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}')" title="Add to Playlist">${SVG_PLUS} <span class="btn-text">Playlist</span></button>
          <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="showToast('File: ${escapeJs(s.filepath || s.filename)}', 'info', 4000)" title="View Details">Details</button>
          <button class="btn btn-secondary btn-danger btn-sm action-btn-secondary" onclick="deleteSong('${escapeJs(s.filepath)}', event, '${escapeJs(currentDeviceId)}', '${escapeJs(s._id || '')}', '${escapeJs(s.filename || '')}')" title="Delete song">${SVG_TRASH}</button>
          ${moreBtn}
        </div>
      `;
    } else {
      actionButtons = `
        <div class="action-btn-group">
          ${likeBtn}
          <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="showAddToPlaylistModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}')" title="Add to Playlist">${SVG_PLUS} <span class="btn-text">Playlist</span></button>
          <button class="btn btn-secondary btn-sm action-btn-secondary" onclick="showToast('File: ${escapeJs(s.filepath || s.filename)}', 'info', 4000)" title="View Details">Details</button>
          <button class="btn btn-secondary btn-danger btn-sm action-btn-secondary" onclick="deleteSong('${escapeJs(s.filepath)}', event, '${escapeJs(currentDeviceId)}', '${escapeJs(s._id || '')}', '${escapeJs(s.filename || '')}')" title="Delete song">${SVG_TRASH}</button>
          ${moreBtn}
        </div>
      `;
    }

    const clickToSyncAttr = isLocalStorage
      ? `style="cursor: pointer;" onclick="openSyncSongModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}', '${escapeJs(s.duration_formatted || '')}', '${escapeJs(s.size_formatted || '')}', '${escapeJs(s.bitrate_kbps || '')}', '${escapeJs(s.album || '')}')" title="Click to sync to device"`
      : (isOverIp
          ? `style="cursor: pointer;" onclick="playOrToggleAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}', ${startIdx + idx}, '${escapeJs(s.bitrate_kbps || '')}', '${escapeJs(currentDeviceId)}')" title="Click to play from device"`
          : '');

    html += `
      <tr ${rowClass}>
        <td class="col-center">
          <input type="checkbox" class="lib-song-checkbox" data-path="${escapeHtml(s.filepath)}" ${isSelected ? 'checked' : ''} onchange="toggleLibrarySongSelection('${escapeJs(s.filepath)}', this.checked)">
        </td>
        <td class="col-center text-tabular col-hide-sm">${globalIdx}</td>
        <td ${clickToSyncAttr}>
          <div class="track-meta-cell">
            <span class="track-title" title="${escapeHtml(s.title || 'Unknown')}">${eqHtml}${escapeHtml(s.title || 'Unknown')}</span>
            <span class="track-subtitle" title="${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}">${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}</span>
            <div class="track-meta-mobile">
              ${s.duration_formatted ? `<span class="meta-tag">${escapeHtml(s.duration_formatted)}</span>` : ''}
              ${s.bitrate_kbps && s.bitrate_kbps !== 'Unknown' ? `<span class="meta-tag" style="color:var(--accent-yellow);font-weight:600;">${escapeHtml(s.bitrate_kbps)}</span>` : ''}
              ${s.size_formatted ? `<span class="meta-tag">${escapeHtml(s.size_formatted)}</span>` : ''}
            </div>
          </div>
        </td>
        <td class="col-center text-tabular col-hide-xs">${escapeHtml(s.duration_formatted || '00:00')}</td>
        <td class="col-center text-tabular col-hide-sm">${escapeHtml(s.size_formatted || '—')}</td>
        <td class="col-center col-hide-md"><span class="badge badge-purple text-tabular">${escapeHtml(s.bitrate_kbps || 'Unknown')}</span></td>
        <td class="col-center text-tabular col-hide-lg"><small class="text-muted">${escapeHtml(s.ctime_str || '—')}</small></td>
        <td class="col-center text-tabular col-hide-lg"><small class="text-muted">${escapeHtml(s.mtime_str || '—')}</small></td>
        <td class="col-right col-actions">${actionButtons}</td>
      </tr>
    `;
  });
  tbody.innerHTML = html;

  const masterCb = document.getElementById('lib-select-all');
  if (masterCb) {
    masterCb.checked = (pageSongs.length > 0 && pageSongs.every(s => selectedSongPaths.has(s.filepath)));
  }

  updateLibraryPaginationInfo(startIdx + 1, Math.min(startIdx + pageSongs.length, filteredSongs.length), filteredSongs.length, totalPages);
}

function updateLibraryPaginationInfo(start, end, total, totalPages) {
  document.getElementById('library-showing-start').textContent = start;
  document.getElementById('library-showing-end').textContent = end;
  document.getElementById('library-total-count').textContent = total;
  document.getElementById('lib-page-info').textContent = `Page ${libPage} of ${totalPages}`;

  document.getElementById('lib-prev-btn').disabled = (libPage <= 1);
  document.getElementById('lib-next-btn').disabled = (libPage >= totalPages);
}


// --- DIRECT DEVICE UPLOAD MODAL LOGIC ---

function openDeviceUploadModal() {
  if (currentDeviceId === 'local') {
    showToast('Select an Over-IP companion device or ADB device to upload files.', 'info');
    return;
  }
  const modal = document.getElementById('modal-device-upload');
  const badge = document.getElementById('upload-device-name-badge');
  const input = document.getElementById('upload-device-files-input');
  const summary = document.getElementById('upload-files-summary');
  const progress = document.getElementById('upload-device-progress');
  const bar = document.getElementById('upload-progress-bar');
  const btn = document.getElementById('btn-submit-device-upload');

  if (badge) badge.textContent = currentDeviceName || currentDeviceId;
  if (input) input.value = '';
  if (summary) summary.textContent = 'No files selected';
  if (progress) progress.style.display = 'none';
  if (bar) bar.style.width = '0%';
  if (btn) btn.disabled = false;

  if (modal) modal.style.display = 'flex';
}

function hideDeviceUploadModal() {
  const modal = document.getElementById('modal-device-upload');
  if (modal) modal.style.display = 'none';
}

function onUploadDeviceFilesSelected(input) {
  const summary = document.getElementById('upload-files-summary');
  if (!summary) return;
  if (input.files && input.files.length > 0) {
    let totalBytes = 0;
    for (let i = 0; i < input.files.length; i++) {
      totalBytes += input.files[i].size;
    }
    summary.textContent = `${input.files.length} file(s) selected (${formatBytes(totalBytes)})`;
  } else {
    summary.textContent = 'No files selected';
  }
}

function submitDeviceUpload() {
  const input = document.getElementById('upload-device-files-input');
  if (!input || !input.files || input.files.length === 0) {
    showToast('Please select at least one audio file to upload.', 'warning');
    return;
  }

  const qualitySelect = document.getElementById('upload-device-quality');
  const qualityVal = qualitySelect ? qualitySelect.value : 'original';
  const targetBitrate = qualityVal === 'original' ? '' : qualityVal;

  const formData = new FormData();
  for (let i = 0; i < input.files.length; i++) {
    formData.append('files', input.files[i]);
  }
  if (targetBitrate) {
    formData.append('target_bitrate', targetBitrate);
  }

  const progressWrap = document.getElementById('upload-device-progress');
  const progressBar = document.getElementById('upload-progress-bar');
  const progressStatus = document.getElementById('upload-progress-status');
  const progressPercent = document.getElementById('upload-progress-percent');
  const submitBtn = document.getElementById('btn-submit-device-upload');

  if (progressWrap) progressWrap.style.display = 'block';
  if (progressBar) progressBar.style.width = '0%';
  if (progressPercent) progressPercent.textContent = '0%';
  if (progressStatus) progressStatus.textContent = 'Starting upload...';
  if (submitBtn) submitBtn.disabled = true;

  const xhr = new XMLHttpRequest();
  xhr.open('POST', `/api/devices/${encodeURIComponent(currentDeviceId)}/upload`);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      if (progressBar) progressBar.style.width = pct + '%';
      if (progressPercent) progressPercent.textContent = pct + '%';
      if (progressStatus) {
        progressStatus.textContent = (pct < 100) ? `Uploading files... (${pct}%)` : 'Processing & Transcoding on server...';
      }
    }
  };

  xhr.onload = () => {
    if (submitBtn) submitBtn.disabled = false;
    try {
      const res = JSON.parse(xhr.responseText);
      if (xhr.status >= 200 && xhr.status < 300 && res.status === 'success') {
        showToast(res.message || `Uploaded ${input.files.length} song(s) successfully!`, 'success', 5000);
        hideDeviceUploadModal();
        refreshCurrentDeviceLibrary();
      } else {
        showToast(res.error || res.message || 'Upload to device failed.', 'error', 6000);
      }
    } catch (e) {
      showToast('Unexpected server response during upload.', 'error');
    }
  };

  xhr.onerror = () => {
    if (submitBtn) submitBtn.disabled = false;
    showToast('Network error while uploading to device.', 'error');
  };

  xhr.send(formData);
}


// --- LOCAL DOWNCONVERT / TRANSCODE MODAL LOGIC ---

let currentTranscodeTrack = null;

function showTranscodeModal(filepath, title, bitrate) {
  currentTranscodeTrack = { filepath, title, bitrate };
  const modal = document.getElementById('modal-transcode-song');
  const titleEl = document.getElementById('transcode-song-title');
  const bitrateEl = document.getElementById('transcode-song-bitrate');
  const btn = document.getElementById('btn-execute-transcode');

  if (titleEl) titleEl.textContent = title || filepath;
  if (bitrateEl) bitrateEl.textContent = `Current: ${bitrate ? bitrate + ' kbps' : 'Unknown'}`;
  if (btn) {
    btn.disabled = false;
    btn.textContent = 'Downconvert';
  }

  if (modal) modal.style.display = 'flex';
}

function hideTranscodeModal() {
  const modal = document.getElementById('modal-transcode-song');
  if (modal) modal.style.display = 'none';
  currentTranscodeTrack = null;
}

async function submitTranscode() {
  if (!currentTranscodeTrack || !currentTranscodeTrack.filepath) return;
  const targetSelect = document.getElementById('transcode-target-bitrate');
  const replaceCb = document.getElementById('transcode-replace-original');
  const btn = document.getElementById('btn-execute-transcode');

  const targetBitrate = targetSelect ? parseInt(targetSelect.value, 10) : 192;
  const replaceOriginal = replaceCb ? replaceCb.checked : false;

  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Downconverting...';
  }

  try {
    const res = await fetch('/api/song/transcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filepath: currentTranscodeTrack.filepath,
        target_bitrate: targetBitrate,
        replace_original: replaceOriginal
      })
    });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      showToast(data.message || 'Track successfully downconverted!', 'success', 4000);
      hideTranscodeModal();
      refreshCurrentDeviceLibrary();
    } else {
      showToast(data.error || 'Downconversion failed.', 'error', 5000);
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Downconvert';
      }
    }
  } catch (err) {
    console.error('Transcode request failed:', err);
    showToast('Network error during downconversion.', 'error');
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Downconvert';
    }
  }
}



// =============================================================================
// =============================================================================
// DUPLICATES MODULE: Tag & Audio Fingerprint Clusters, Deduplication Strategies
// =============================================================================

// --- DUPLICATES SEARCH, SELECTION & PAGINATION ---

let selectedDuplicatePaths = new Set();
let currentDupKeepStrategy = 'best_quality';

function findKeeperInCluster(cluster, strategy = 'best_quality') {
  if (!cluster || !cluster.songs || cluster.songs.length === 0) return null;
  const songsCopy = [...cluster.songs];

  if (strategy === 'newest') {
    songsCopy.sort((a, b) => (b.mtime || 0) - (a.mtime || 0) || (b.size || 0) - (a.size || 0));
  } else if (strategy === 'oldest') {
    songsCopy.sort((a, b) => (a.mtime || 0) - (b.mtime || 0) || (b.size || 0) - (a.size || 0));
  } else {
    // Default: best quality / size
    songsCopy.sort((a, b) => {
      const bitA = a.bitrate_val || 0;
      const bitB = b.bitrate_val || 0;
      if (bitB !== bitA) return bitB - bitA;
      const sizeA = a.size || 0;
      const sizeB = b.size || 0;
      if (sizeB !== sizeA) return sizeB - sizeA;
      return (b.mtime || 0) - (a.mtime || 0);
    });
  }
  return songsCopy[0];
}

function onToggleFingerprintMatching(checked) {
  useAudioFingerprinting = Boolean(checked);
  localStorage.setItem('antigravity_use_audio_fingerprint', useAudioFingerprinting);
  const container = document.getElementById('duplicates-container');
  if (container) {
    container.innerHTML = `<p class="text-muted" style="display: flex; align-items: center; gap: 0.5rem; padding: 1rem 0;">${SVG_SPARKLES} Loading duplicates...</p>`;
  }
  loadDuplicates(true);
}

// --- Live SSE Duplicate Analysis Terminal ---

function _dupTerminalLineClass(msg) {
  const tag = msg.slice(0, 7).toUpperCase();
  if (tag.startsWith('[CACHE]')) return 'log-cache';
  if (tag.startsWith('[FP]'))    return 'log-fp';
  if (tag.startsWith('[SCAN]'))  return 'log-scan';
  if (tag.startsWith('[TAG]'))   return 'log-tag';
  if (tag.startsWith('[MATCH]')) return 'log-match';
  if (tag.startsWith('[SKIP]'))  return 'log-skip';
  if (tag.startsWith('[FAIL]'))  return 'log-fail';
  if (tag.startsWith('[WARN]'))  return 'log-warn';
  if (tag.startsWith('[START]')) return 'log-start';
  if (tag.startsWith('[INFO]'))  return 'log-info';
  if (tag.startsWith('[DONE]'))  return 'log-done';
  if (tag.startsWith('[ERROR]')) return 'log-error';
  return '';
}

// Terminal render helper — caps the number of DOM nodes and coalesces the
// auto-scroll into a single per-frame update so progress bursts cannot freeze
// the tab's main thread.
function pushTermLine(logEl, msg) {
  if (!logEl) return;
  const line = document.createElement('span');
  line.className = 'dup-terminal-line ' + _dupTerminalLineClass(msg);
  line.textContent = msg;
  logEl.appendChild(line);
  logEl.appendChild(document.createTextNode('\n'));
  while (logEl.childElementCount > 250) {
    logEl.removeChild(logEl.firstElementChild);
  }
  if (logEl._scrollFrame == null) {
    logEl._scrollFrame = requestAnimationFrame(() => {
      logEl._scrollFrame = null;
      logEl.scrollTop = logEl.scrollHeight;
    });
  }
}

function _dupTerminalAppend(msg) {
  const log = document.getElementById('dup-terminal-log');
  pushTermLine(log, msg);
}

function streamDuplicates() {
  // Close any existing SSE connection
  if (dupEventSource) {
    dupEventSource.close();
    dupEventSource = null;
  }

  const btn = document.getElementById('btn-rescan-duplicates');
  const terminal = document.getElementById('dup-terminal');
  const termLog = document.getElementById('dup-terminal-log');
  const container = document.getElementById('duplicates-container');

  // Show terminal, clear previous log
  if (terminal) terminal.style.display = 'block';
  if (termLog) termLog.innerHTML = '';
  if (btn) { btn.disabled = true; btn.textContent = 'Analyzing…'; }
  if (container) container.innerHTML = '';

  const params = new URLSearchParams();
  params.set('fingerprint', useAudioFingerprinting ? 'true' : 'false');

  const evtSource = new EventSource(`/api/duplicates/stream?${params.toString()}`);
  dupEventSource = evtSource;

  let logCount = 0;
  const counter = document.getElementById('dup-terminal-counter');

  evtSource.onmessage = (e) => {
    let payload;
    try { payload = JSON.parse(e.data); } catch { return; }

    if (payload.type === 'log') {
      _dupTerminalAppend(payload.msg);
      logCount++;
      if (counter) counter.textContent = `${logCount} lines`;

    } else if (payload.type === 'done') {
      evtSource.close();
      dupEventSource = null;
      _dupTerminalAppend(payload.msg || '');

      // Brief pause then collapse terminal and render results
      setTimeout(() => {
        if (terminal) terminal.style.display = 'none';
      }, 1800);

      // Populate clusters and render
      const data = payload.result || {};
      allClusters = data.clusters || [];
      filteredClusters = [...allClusters];
      dupPage = 1;

      const warnEl = document.getElementById('dup-fingerprint-warning');
      const warnText = document.getElementById('dup-fingerprint-warning-text');
      if (warnEl && warnText) {
        if (data.warning) {
          warnText.textContent = data.warning;
          warnEl.style.display = 'flex';
        } else {
          warnEl.style.display = 'none';
        }
      }

      const validPaths = new Set();
      allClusters.forEach(c => (c.songs || []).forEach(s => validPaths.add(s.filepath)));
      for (const p of selectedDuplicatePaths) {
        if (!validPaths.has(p)) selectedDuplicatePaths.delete(p);
      }

      updateDuplicatesSelectionUI();
      renderDuplicatesPage();

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Analyze`;
      }

    } else if (payload.type === 'error') {
      _dupTerminalAppend(`[ERROR] ${payload.msg}`);
      evtSource.close();
      dupEventSource = null;
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Analyze`;
      }
    }
  };

  evtSource.onerror = () => {
    if (evtSource.readyState === EventSource.CLOSED) return;
    _dupTerminalAppend('[ERROR] Connection to server lost.');
    evtSource.close();
    dupEventSource = null;
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Analyze`;
    }
  };
}


async function loadDuplicates(forceRefresh = false) {
  const container = document.getElementById('duplicates-container');
  if (!container) return;

  const fpToggle = document.getElementById('toggle-use-fingerprints');
  if (fpToggle) {
    fpToggle.checked = useAudioFingerprinting;
  }

  try {
    const params = new URLSearchParams();
    params.set('fingerprint', useAudioFingerprinting ? 'true' : 'false');
    if (forceRefresh) {
      params.set('refresh', 'true');
    }
    const res = await fetch(`/api/duplicates?${params.toString()}`);
    const data = await res.json();
    allClusters = data.clusters || [];
    filteredClusters = [...allClusters];
    dupPage = 1;

    // Handle dependency warning banner
    const warnEl = document.getElementById('dup-fingerprint-warning');
    const warnText = document.getElementById('dup-fingerprint-warning-text');
    if (warnEl && warnText) {
      if (data.warning) {
        warnText.textContent = data.warning;
        warnEl.style.display = 'flex';
      } else {
        warnEl.style.display = 'none';
      }
    }

    // Clean up any selected paths that no longer exist in clusters
    const validPaths = new Set();
    allClusters.forEach(c => (c.songs || []).forEach(s => validPaths.add(s.filepath)));
    for (const p of selectedDuplicatePaths) {
      if (!validPaths.has(p)) selectedDuplicatePaths.delete(p);
    }

    updateDuplicatesSelectionUI();
    renderDuplicatesPage();
  } catch (err) {
    console.error('Error loading duplicates:', err);
  }
}

function onDuplicatesSearchInput() {
  const query = (document.getElementById('duplicates-search')?.value || '').trim().toLowerCase();
  if (!query) {
    filteredClusters = [...allClusters];
  } else {
    filteredClusters = allClusters.filter(c => {
      if ((c.cluster_name || '').toLowerCase().includes(query)) return true;
      return c.songs.some(s => (s.filepath || '').toLowerCase().includes(query));
    });
  }
  dupPage = 1;
  renderDuplicatesPage();
}

function onDuplicateStrategyChange() {
  const sel = document.getElementById('dup-keep-strategy');
  if (sel) {
    currentDupKeepStrategy = sel.value || 'best_quality';
  }
  // Re-evaluate current selections if user has already selected
  if (selectedDuplicatePaths.size > 0) {
    selectAllDuplicates();
  } else {
    renderDuplicatesPage();
  }
}

function selectAllDuplicates() {
  if (!allClusters || allClusters.length === 0) return;
  selectedDuplicatePaths.clear();

  allClusters.forEach(c => {
    const keeper = findKeeperInCluster(c, currentDupKeepStrategy);
    if (!keeper) return;
    (c.songs || []).forEach(s => {
      if (s.filepath !== keeper.filepath) {
        selectedDuplicatePaths.add(s.filepath);
      }
    });
  });

  updateDuplicatesSelectionUI();
  renderDuplicatesPage();
}

function deselectAllDuplicates() {
  selectedDuplicatePaths.clear();
  updateDuplicatesSelectionUI();
  renderDuplicatesPage();
}

function autoSelectClusterDuplicates(clusterIndex) {
  const cluster = filteredClusters[clusterIndex];
  if (!cluster || !cluster.songs) return;

  const keeper = findKeeperInCluster(cluster, currentDupKeepStrategy);
  if (!keeper) return;

  cluster.songs.forEach(s => {
    if (s.filepath === keeper.filepath) {
      selectedDuplicatePaths.delete(s.filepath);
    } else {
      selectedDuplicatePaths.add(s.filepath);
    }
  });

  updateDuplicatesSelectionUI();
  renderDuplicatesPage();
}

function onDuplicateCheckboxChange(filepath, isChecked, clusterIndex) {
  const cluster = filteredClusters[clusterIndex];
  if (isChecked) {
    // Safety safeguard: Ensure at least one copy is kept in this cluster!
    if (cluster && cluster.songs) {
      const otherSongs = cluster.songs.filter(s => s.filepath !== filepath);
      const allOthersSelected = otherSongs.every(s => selectedDuplicatePaths.has(s.filepath));
      if (allOthersSelected && otherSongs.length > 0) {
        showToast("Safety Limit: At least one copy in this cluster must be kept so the song is not lost.", 'error');
        const cb = document.querySelector(`input.dup-checkbox[data-path="${CSS.escape(filepath)}"]`);
        if (cb) cb.checked = false;
        return;
      }
    }
    selectedDuplicatePaths.add(filepath);
  } else {
    selectedDuplicatePaths.delete(filepath);
  }
  updateDuplicatesSelectionUI();
  renderDuplicatesPage();
}

function updateDuplicatesSelectionUI() {
  const count = selectedDuplicatePaths.size;
  const counterEl = document.getElementById('dup-selected-counter');
  const deleteBtn = document.getElementById('btn-batch-delete-duplicates');

  if (counterEl) {
    counterEl.textContent = `${count} files selected`;
  }
  if (deleteBtn) {
    deleteBtn.disabled = (count === 0);
    deleteBtn.innerHTML = `
      <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      Delete Selected (${count})
    `;
  }
}

function changeDuplicatesPage(delta) {
  const totalPages = Math.ceil(filteredClusters.length / dupPageSize) || 1;
  dupPage = Math.max(1, Math.min(totalPages, dupPage + delta));
  renderDuplicatesPage();
}

function updateDuplicatesReclaimableSummary() {
  const banner = document.getElementById('dup-reclaimable-banner');
  const sizeEl = document.getElementById('dup-reclaimable-size');
  const countEl = document.getElementById('dup-reclaimable-count');
  if (!banner || !sizeEl || !countEl) return;

  if (!allClusters || allClusters.length === 0) {
    banner.style.display = 'none';
    return;
  }

  let redundantCount = 0;
  let redundantBytes = 0;

  allClusters.forEach(c => {
    const keeper = findKeeperInCluster(c, currentDupKeepStrategy);
    if (c.songs && c.songs.length > 1) {
      c.songs.forEach(s => {
        if (keeper && s.filepath === keeper.filepath) return;
        redundantCount++;
        if (typeof s.size === 'number') {
          redundantBytes += s.size;
        }
      });
    }
  });

  if (redundantCount > 0) {
    sizeEl.textContent = formatBytes(redundantBytes);
    countEl.textContent = redundantCount;
    banner.style.display = 'flex';
  } else {
    banner.style.display = 'none';
  }
}

function selectAllRedundantDuplicates() {
  if (!allClusters || allClusters.length === 0) {
    showToast('No duplicate clusters found.', 'info');
    return;
  }

  selectedDuplicatePaths.clear();
  let count = 0;
  allClusters.forEach(c => {
    const keeper = findKeeperInCluster(c, currentDupKeepStrategy);
    if (c.songs && c.songs.length > 1) {
      c.songs.forEach(s => {
        if (keeper && s.filepath === keeper.filepath) return;
        selectedDuplicatePaths.add(s.filepath);
        count++;
      });
    }
  });

  updateDuplicatesSelectionUI();
  renderDuplicatesPage();
  showToast(`Selected ${count} redundant copies across all clusters (best copies preserved).`, 'success');
}

function renderDuplicatesPage() {
  updateDuplicatesReclaimableSummary();
  const container = document.getElementById('duplicates-container');
  if (!container) return;

  const badgeEl = document.getElementById('duplicates-summary-badge');
  if (badgeEl) {
    badgeEl.textContent = `${allClusters.length} duplicate clusters`;
  }

  if (!filteredClusters || filteredClusters.length === 0) {
    container.innerHTML = `<p style="color: var(--status-online); font-weight: 600; display: flex; align-items: center; gap: 0.5rem; padding: 1rem 0;">${SVG_SPARKLES} No duplicate clusters found matching query!</p>`;
    updateDuplicatesPaginationInfo(0, 0, 0, 1);
    return;
  }

  const totalPages = Math.ceil(filteredClusters.length / dupPageSize);
  const startIdx = (dupPage - 1) * dupPageSize;
  const pageClusters = filteredClusters.slice(startIdx, startIdx + dupPageSize);

  let html = '';
  pageClusters.forEach((c, idx) => {
    const globalIdx = startIdx + idx + 1;
    const currentClusterIdx = startIdx + idx;
    const keeper = findKeeperInCluster(c, currentDupKeepStrategy);

    const matchBadge = c.match_type === 'audio_fingerprint'
      ? `<span class="badge badge-yellow" style="font-size: 0.72rem; display: inline-flex; align-items: center; gap: 0.25rem;" title="Acoustic waveform match via Chromaprint fpcalc">${SVG_WAVEFORM} Waveform Fingerprint</span>`
      : (c.match_type === 'filename'
          ? '<span class="badge badge-yellow" style="font-size: 0.72rem;">Filename</span>'
          : '<span class="badge badge-yellow" style="font-size: 0.72rem;">Tag Match</span>');

    html += `
      <div class="duplicate-cluster-card">
        <div class="cluster-card-header">
          <div class="cluster-title-group" style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <h4 class="cluster-title">
              Cluster #${globalIdx}: ${escapeHtml(c.cluster_name)}
            </h4>
            ${matchBadge}
            <span class="badge badge-yellow text-tabular">${c.count} copies</span>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="autoSelectClusterDuplicates(${currentClusterIdx})" title="Select duplicate copies and keep the best copy">
            Auto-select (Keep Best)
          </button>
        </div>
        <ul class="cluster-items-list">
    `;

    c.songs.forEach(s => {
      const isSelected = selectedDuplicatePaths.has(s.filepath);
      const isKeeper = keeper && (s.filepath === keeper.filepath);

      let rowBorder = '1px solid var(--border-color)';
      let rowBg = 'var(--bg-card)';
      let statusBadge = '';

      if (isSelected) {
        rowBorder = '1px solid rgba(239, 68, 68, 0.4)';
        rowBg = 'rgba(239, 68, 68, 0.08)';
        statusBadge = '<span class="badge badge-offline" style="font-size: 0.72rem; font-weight: 700;">DELETE</span>';
      } else if (isKeeper) {
        rowBorder = '1px solid rgba(34, 197, 94, 0.35)';
        rowBg = 'rgba(34, 197, 94, 0.06)';
        statusBadge = '<span class="badge badge-online" style="font-size: 0.72rem; font-weight: 700;" title="Preserved original copy">KEEP (Best)</span>';
      } else {
        statusBadge = '<span class="badge badge-yellow" style="font-size: 0.72rem;">COPY</span>';
      }

      const checkedAttr = isSelected ? 'checked' : '';

      html += `
        <li class="duplicate-item-row" style="background: ${rowBg}; border: ${rowBorder};">
          <div class="dup-left-content">
            <input type="checkbox" class="dup-checkbox" data-path="${escapeHtml(s.filepath)}" ${checkedAttr} onchange="onDuplicateCheckboxChange('${escapeJs(s.filepath)}', this.checked, ${currentClusterIdx})" style="width: 1.15rem; height: 1.15rem; cursor: pointer; accent-color: var(--accent-yellow); flex-shrink: 0;">
            ${statusBadge}
            <div class="dup-file-info">
              <code class="dup-filepath" title="${escapeHtml(s.filepath)}">${escapeHtml(s.filepath)}</code>
              <div class="dup-file-meta">
                <span class="meta-tag text-tabular">${escapeHtml(s.size_formatted || '—')}</span>
                ${s.bitrate_kbps ? `<span class="meta-tag text-tabular">${escapeHtml(s.bitrate_kbps)}</span>` : ''}
                ${s.mtime_str ? `<span class="meta-tag text-tabular">${escapeHtml(s.mtime_str)}</span>` : ''}
              </div>
            </div>
          </div>
          <div class="action-btn-group">
            <button class="btn btn-secondary btn-sm" onclick="playAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}')" title="Play track">${SVG_PLAY} Play</button>
            <button class="btn btn-secondary btn-danger btn-sm" onclick="deleteSong('${escapeJs(s.filepath)}', event)" title="Delete track">${SVG_TRASH} Delete</button>
          </div>
        </li>
      `;
    });
    html += '</ul></div>';
  });
  container.innerHTML = html;

  updateDuplicatesPaginationInfo(startIdx + 1, Math.min(startIdx + pageClusters.length, filteredClusters.length), filteredClusters.length, totalPages);
}

function updateDuplicatesPaginationInfo(start, end, total, totalPages) {
  document.getElementById('dup-showing-start').textContent = start;
  document.getElementById('dup-showing-end').textContent = end;
  document.getElementById('dup-total-count').textContent = total;
  document.getElementById('dup-page-info').textContent = `Page ${dupPage} of ${totalPages}`;

  document.getElementById('dup-prev-btn').disabled = (dupPage <= 1);
  document.getElementById('dup-next-btn').disabled = (dupPage >= totalPages);
}

// Modal Handlers for Batch Duplicate Deletion
function openBatchDeleteDuplicatesModal() {
  if (selectedDuplicatePaths.size === 0) return;
  const modal = document.getElementById('modal-delete-duplicates-confirm');
  const summaryEl = document.getElementById('batch-delete-summary-text');
  const previewEl = document.getElementById('batch-delete-files-preview');
  if (!modal) return;

  if (summaryEl) {
    summaryEl.innerHTML = `You have selected <strong>${selectedDuplicatePaths.size}</strong> duplicate files for deletion across your duplicate song clusters.`;
  }

  if (previewEl) {
    let filesHtml = '';
    selectedDuplicatePaths.forEach(p => {
      filesHtml += `<div style="margin-bottom: 0.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--status-offline); display: flex; align-items: center; gap: 0.35rem;"><span style="display: inline-flex; align-items: center; color: var(--status-offline); flex-shrink: 0;">${SVG_TRASH}</span><span>${escapeHtml(p)}</span></div>`;
    });
    previewEl.innerHTML = filesHtml;
  }

  modal.style.display = 'flex';
}

function hideBatchDeleteDuplicatesModal() {
  const modal = document.getElementById('modal-delete-duplicates-confirm');
  if (modal) modal.style.display = 'none';
}

async function executeBatchDeleteDuplicates() {
  if (selectedDuplicatePaths.size === 0) return;
  const btn = document.getElementById('btn-execute-batch-delete');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Deleting duplicate files...';
  }

  const pathsToDelete = Array.from(selectedDuplicatePaths);
  try {
    const res = await fetch('/api/songs/delete-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filepaths: pathsToDelete,
        device_id: 'local'
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      hideBatchDeleteDuplicatesModal();
      showToast(`Deleted ${data.deleted_count} duplicate files. Exactly 1 copy in each cluster preserved!`, 'success');
      selectedDuplicatePaths.clear();
      updateDuplicatesSelectionUI();
      loadDuplicates();
      loadSongs();
      loadDashboardStats();
    } else {
      showToast(`Error deleting duplicate files: ${data.error || data.message || 'Batch delete failed'}`, 'error');
    }
  } catch (err) {
    console.error('Error executing batch duplicate deletion:', err);
    showToast('Connection error while batch deleting duplicate files.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Confirm & Delete Selected Files';
    }
  }
}

// =============================================================================
// SYNC MODULE: Folder Sync Planner, Device Diff Table, Push Engine & Track Modal
// =============================================================================

// --- MUSIC FOLDER SYNC (LOCAL -> ADB) JS LOGIC ---

let syncPreviewData = null;

async function loadSyncDevices(selectFirst = true) {
  const select = document.getElementById('sync-device-select');
  const statusEl = document.getElementById('sync-status');
  if (!select) return;

  try {
    const res = await fetch('/api/sync/devices');
    const data = await res.json();
    const devices = data.devices || [];

    if (devices.length === 0) {
      select.innerHTML = '<option value="">No ADB devices connected</option>';
      if (statusEl) statusEl.textContent = 'No connected ADB devices found. Plug in a device and click Refresh Devices.';
      return;
    }

    const prevValue = select.value;
    let options = '<option value="">-- Select target ADB device --</option>';
    devices.forEach(d => {
      options += `<option value="${escapeHtml(d.serial)}">${escapeHtml(d.name)} (${d.count} songs)</option>`;
    });
    select.innerHTML = options;

    if (prevValue) {
      select.value = prevValue;
    } else if (selectFirst) {
      select.selectedIndex = 1;
    }

    if (statusEl) statusEl.textContent = `${devices.length} ADB device(s) available. Select a target and click "Scan & Compare".`;
  } catch (err) {
    console.error('Error loading sync devices:', err);
    if (statusEl) statusEl.textContent = 'Error loading ADB devices.';
  }
}

async function runSyncPreview() {
  const select = document.getElementById('sync-device-select');
  const statusEl = document.getElementById('sync-status');
  const forceCheckbox = document.getElementById('sync-force-checkbox');
  const remoteDirInput = document.getElementById('sync-remote-dir');

  const serial = select ? select.value : '';
  if (!serial) {
    if (statusEl) statusEl.textContent = 'Please select a target ADB device first.';
    return;
  }

  const force = forceCheckbox ? forceCheckbox.checked : false;
  if (statusEl) statusEl.textContent = 'Scanning local folders and comparing with device...';

  try {
    const res = await fetch(`/api/sync/preview?serial=${encodeURIComponent(serial)}&force=${force}`);
    const data = await res.json();
    if (data.error) {
      if (statusEl) statusEl.textContent = `Error: ${data.error}`;
      return;
    }
    if (remoteDirInput) remoteDirInput.value = data.remote_dir || '';
    syncPreviewData = data;
    renderSyncPreview(data);
    if (statusEl) statusEl.textContent = `Compare complete for ${data.serial}: ${data.local_count} local files, ${data.device_songs_count} songs on device, ${data.to_sync.length} to sync.`;
  } catch (err) {
    console.error('Error running sync preview:', err);
    if (statusEl) statusEl.textContent = 'Error running sync preview.';
  }
}

function renderSyncPreview(data) {
  const container = document.getElementById('sync-preview-panel');
  if (!container) return;

  const toSync = data.to_sync || [];
  const already = data.already_present || [];

  let html = '';

  // Summary cards
  html += `
    <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); margin-bottom: 1.25rem;">
      <div class="metric-card">
        <div class="metric-header"><span>Local Files</span></div>
        <div class="metric-value" style="font-size: 1.8rem;">${data.local_count}</div>
      </div>
      <div class="metric-card">
        <div class="metric-header"><span>Device Songs</span></div>
        <div class="metric-value" style="font-size: 1.8rem;">${data.device_songs_count}</div>
      </div>
      <div class="metric-card">
        <div class="metric-header"><span>Already Present</span></div>
        <div class="metric-value" style="font-size: 1.8rem; -webkit-text-fill-color: #34d399;">${already.length}</div>
      </div>
      <div class="metric-card">
        <div class="metric-header"><span>To Sync</span></div>
        <div class="metric-value" style="font-size: 1.8rem; -webkit-text-fill-color: #fbbf24;">${toSync.length}</div>
      </div>
    </div>
  `;

  // To Sync section
  html += `<div class="panel" style="margin-bottom: 1.25rem;">`;
  html += `
    <div class="panel-title">
      <span>Files To Sync (${toSync.length})</span>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-secondary" onclick="toggleSelectAllSyncFiles()">Select All</button>
        <button class="btn" id="btn-push-sync" onclick="pushSelectedSyncFiles()" ${toSync.length === 0 ? 'disabled' : ''}>Push Selected</button>
      </div>
    </div>`;

  if (toSync.length === 0) {
    html += '<p class="text-muted">Nothing to sync. All local files are already present on the device!</p>';
  } else {
    html += `
      <table>
        <thead>
          <tr>
            <th style="width: 32px;"><input type="checkbox" id="sync-select-all" onchange="toggleSelectAllSyncFiles()"></th>
            <th>Track</th>
            <th>Local Path</th>
            <th>Size</th>
          </tr>
        </thead>
        <tbody>
    `;
    toSync.forEach(f => {
      const rel = f.rel_path || f.filename || f.path;
      html += `
        <tr>
          <td><input type="checkbox" class="sync-file-checkbox" data-path="${escapeHtml(f.path)}" onchange="updateSyncPushButton()"></td>
          <td><strong>${escapeHtml(f.filename)}</strong></td>
          <td><small class="text-muted"><code>${escapeHtml(rel)}</code></small></td>
          <td>${escapeHtml(f.size_formatted || '')}</td>
        </tr>
      `;
    });
    html += '</tbody></table>';
  }
  html += '</div>';

  // Already Present section
  if (already.length > 0) {
    html += '<div class="panel" style="margin-bottom: 0;">';
    html += `
      <div class="panel-title">
        <span>Already Present On Device (${already.length})</span>
        <button class="btn btn-secondary" id="btn-toggle-already" onclick="toggleAlreadySection()">Show</button>
      </div>
      <div id="already-section" style="display: none;">
        <table>
          <thead>
            <tr>
              <th>Track</th>
              <th>Local Path</th>
              <th>Size</th>
              <th>Matched As</th>
            </tr>
          </thead>
          <tbody>
    `;
    already.slice(0, 25).forEach(a => {
      html += `
        <tr>
          <td><strong>${escapeHtml(a.filename)}</strong></td>
          <td><small class="text-muted"><code>${escapeHtml(a.rel_path)}</code></small></td>
          <td>${escapeHtml(a.size_formatted || '')}</td>
          <td><small class="text-muted">${escapeHtml(a.match_reason || '')}</small></td>
        </tr>
      `;
    });
    if (already.length > 25) {
      html += `<tr><td colspan="4" class="text-muted">... and ${already.length - 25} more files already present on device.</td></tr>`;
    }
    html += '</tbody></table></div></div>';
  }

  container.style.display = 'block';
  container.innerHTML = html;
  updateSyncPushButton();
}

function toggleSelectAllSyncFiles() {
  const master = document.getElementById('sync-select-all');
  const checked = master ? master.checked : false;
  document.querySelectorAll('.sync-file-checkbox').forEach(cb => { cb.checked = checked; });
  updateSyncPushButton();
}

function updateSyncPushButton() {
  const checked = document.querySelectorAll('.sync-file-checkbox:checked').length;
  const btn = document.getElementById('btn-push-sync');
  if (btn) btn.textContent = checked > 0 ? `Push Selected (${checked})` : 'Push Selected';
}

function toggleAlreadySection() {
  const section = document.getElementById('already-section');
  const btn = document.getElementById('btn-toggle-already');
  if (!section || !btn) return;
  const isHidden = section.style.display === 'none';
  section.style.display = isHidden ? 'block' : 'none';
  btn.textContent = isHidden ? 'Hide' : 'Show';
}

async function pushSelectedSyncFiles() {
  const checkedBoxes = [...document.querySelectorAll('.sync-file-checkbox:checked')];
  if (checkedBoxes.length === 0) {
    showToast('No files selected to sync.', 'info');
    return;
  }

  const serial = document.getElementById('sync-device-select')?.value || '';
  const remoteDir = document.getElementById('sync-remote-dir')?.value || '';
  const statusEl = document.getElementById('sync-status');
  const progressContainer = document.getElementById('sync-progress-container');
  const progressBar = document.getElementById('sync-progress-bar');
  const progressLabel = document.getElementById('sync-progress-label');
  const progressPercent = document.getElementById('sync-progress-percent');
  const progressCurrentFile = document.getElementById('sync-progress-current-file');
  const pushBtn = document.getElementById('btn-push-sync');

  if (!serial) {
    showToast('Please select a destination ADB device.', 'error');
    return;
  }

  const files = checkedBoxes.map(cb => cb.dataset.path);

  showConfirmModal({
    title: 'Push Files to ADB Device',
    message: `Push ${files.length} file(s) to device [${serial}]?`,
    details: `Destination: ${remoteDir}`,
    confirmText: 'Push Files',
    confirmClass: 'btn',
    onConfirm: async () => {
      if (pushBtn) pushBtn.disabled = true;
      if (statusEl) statusEl.textContent = `Starting sync of ${files.length} file(s)...`;

      if (progressContainer) {
        progressContainer.style.display = 'block';
        if (progressBar) progressBar.style.width = '0%';
        if (progressPercent) progressPercent.textContent = '0%';
        if (progressLabel) progressLabel.textContent = `Syncing to ${serial}...`;
      }

      let successCount = 0;
      let failCount = 0;

      const batchQualityEl = document.getElementById('sync-batch-quality');
      const batchQuality = batchQualityEl ? batchQualityEl.value : 'original';
      const targetBitrate = (batchQuality === 'original') ? null : parseInt(batchQuality, 10);

      for (let i = 0; i < files.length; i++) {
        const fp = files[i];
        const fn = fp.split('/').pop();
        const currentIdx = i + 1;
        const pct = Math.round((currentIdx / files.length) * 100);

        if (progressLabel) progressLabel.textContent = `Pushing ${currentIdx} of ${files.length} (${pct}%)`;
        if (progressPercent) progressPercent.textContent = `${pct}%`;
        if (progressBar) progressBar.style.width = `${pct}%`;
        if (progressCurrentFile) progressCurrentFile.textContent = fn;

        try {
          const res = await fetch('/api/sync/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              serial: serial,
              remote_dir: remoteDir,
              files: [fp],
              target_bitrate: targetBitrate
            })
          });
          const data = await res.json();
          if (data.status === 'success' && data.pushed > 0) {
            successCount++;
          } else {
            failCount++;
          }
        } catch (err) {
          console.error(`Failed to push ${fp}:`, err);
          failCount++;
        }
      }

      if (pushBtn) pushBtn.disabled = false;
      if (progressLabel) progressLabel.textContent = `Completed (${successCount} succeeded, ${failCount} failed)`;
      if (statusEl) statusEl.textContent = `Sync completed: ${successCount} pushed, ${failCount} failed.`;

      if (successCount > 0) {
        showToast(`Synced ${successCount} file(s) to ${serial}!`, 'success');
      }
      if (failCount > 0) {
        showToast(`${failCount} file(s) failed to sync. Check server logs.`, 'error');
      }

      setTimeout(() => {
        if (progressContainer) progressContainer.style.display = 'none';
      }, 3500);

      loadSyncedHistory();
      loadDashboardStats();
      loadSyncDevices(false);
      runSyncPreview();
    }
  });
}


// --- SYNC TRACK TO DEVICE MODAL & EXISTENCE CHECKING ---
let syncCurrentSong = null;
let syncTargetDevicesList = [];

async function openSyncSongModal(filepath, title, artist, duration, size, bitrate, album) {
  syncCurrentSong = { filepath, title, artist, duration, size, bitrate, album };

  // Set local track summary UI
  document.getElementById('sync-local-title').textContent = title || filepath.split('/').pop();
  document.getElementById('sync-local-artist-album').textContent = `${artist || 'Unknown'} | ${album || 'Unknown'}`;
  document.getElementById('sync-local-bitrate').textContent = bitrate ? (String(bitrate).includes('kbps') ? bitrate : `${bitrate} kbps`) : 'Bitrate Unknown';
  document.getElementById('sync-local-duration').textContent = duration || '00:00';
  document.getElementById('sync-local-size').textContent = size || '0 MB';
  document.getElementById('sync-local-path').textContent = filepath;

  const statusEl = document.getElementById('sync-action-status');
  if (statusEl) statusEl.innerHTML = '';

  const syncBtn = document.getElementById('btn-execute-sync-song');
  if (syncBtn) syncBtn.disabled = false;
  const syncBtnText = document.getElementById('btn-execute-sync-text');
  if (syncBtnText) syncBtnText.textContent = 'Sync to Device';

  const modal = document.getElementById('modal-sync-song');
  if (modal) modal.style.display = 'flex';

  const qualitySelect = document.getElementById('sync-quality-bitrate');
  if (qualitySelect) qualitySelect.value = 'original';

  // Load target devices
  await populateSyncTargetDevices();
}

function hideSyncSongModal() {
  const modal = document.getElementById('modal-sync-song');
  if (modal) modal.style.display = 'none';
  syncCurrentSong = null;
}

async function populateSyncTargetDevices() {
  const selectEl = document.getElementById('sync-destination-device');
  if (!selectEl) return;
  selectEl.innerHTML = '<option value="">Loading available devices...</option>';

  try {
    const res = await fetch('/api/devices');
    const devices = await res.json();
    // Exclude 'local' storage as destination
    syncTargetDevicesList = (devices || []).filter(d => d.id !== 'local');

    if (syncTargetDevicesList.length === 0) {
      selectEl.innerHTML = '<option value="">No connected ADB or Over-IP target devices found</option>';
      const syncBtn = document.getElementById('btn-execute-sync-song');
      if (syncBtn) syncBtn.disabled = true;
      document.getElementById('sync-check-results').style.display = 'none';
      document.getElementById('sync-check-loading').style.display = 'none';
      return;
    }

    let html = '';
    let defaultDevId = '';
    syncTargetDevicesList.forEach((d, idx) => {
      const isOnline = (d.status === 'online');
      const label = `${d.name} (${d.type}) - ${isOnline ? 'ONLINE' : 'OFFLINE'}`;
      html += `<option value="${escapeHtml(d.id)}">${escapeHtml(label)}</option>`;
      if (!defaultDevId && isOnline) {
        defaultDevId = d.id;
      }
    });

    selectEl.innerHTML = html;
    if (defaultDevId) {
      selectEl.value = defaultDevId;
    }

    // Trigger check for selected device
    await onSyncDestinationDeviceChange();
  } catch (err) {
    console.error('Error loading devices for sync modal:', err);
    selectEl.innerHTML = '<option value="">Error loading devices</option>';
  }
}

async function onSyncDestinationDeviceChange() {
  const selectEl = document.getElementById('sync-destination-device');
  const resultsWrap = document.getElementById('sync-check-results');
  const loadingWrap = document.getElementById('sync-check-loading');
  const syncBtnText = document.getElementById('btn-execute-sync-text');
  const bannerEl = document.getElementById('sync-status-banner');
  const similarListEl = document.getElementById('sync-similar-list');
  const similarCountEl = document.getElementById('sync-similar-count');

  if (!selectEl || !selectEl.value || !syncCurrentSong) {
    if (resultsWrap) resultsWrap.style.display = 'none';
    return;
  }

  const deviceId = selectEl.value;
  if (loadingWrap) loadingWrap.style.display = 'block';
  if (resultsWrap) resultsWrap.style.display = 'none';

  try {
    const res = await fetch(`/api/sync/check-song?filepath=${encodeURIComponent(syncCurrentSong.filepath)}&device_id=${encodeURIComponent(deviceId)}`);
    const data = await res.json();
    if (loadingWrap) loadingWrap.style.display = 'none';
    if (resultsWrap) resultsWrap.style.display = 'block';

    if (data.status === 'error') {
      if (bannerEl) {
        bannerEl.className = '';
        bannerEl.style.background = 'rgba(243, 139, 168, 0.15)';
        bannerEl.style.border = '1px solid rgba(243, 139, 168, 0.4)';
        bannerEl.style.color = '#f38ba8';
        bannerEl.innerHTML = `<strong>Error checking device:</strong> ${escapeHtml(data.message || 'Device offline or unreachable')}`;
      }
      return;
    }

    // 1. Render Exact Match Banner
    if (data.exact_match && data.exact_match.found) {
      const em = data.exact_match.device_song || {};
      if (bannerEl) {
        bannerEl.style.background = 'rgba(249, 226, 175, 0.15)';
        bannerEl.style.border = '1px solid rgba(249, 226, 175, 0.4)';
        bannerEl.style.color = '#f9e2af';
        bannerEl.innerHTML = `
          <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.4rem;">
            ${SVG_ALERT}
            <span>Song Already Exists on ${escapeHtml(data.device_name)}</span>
          </div>
          <div style="color: #f9e2af; font-size: 0.8rem;">${escapeHtml(data.exact_match.match_reason || 'Match found')}</div>
          <div style="display: flex; gap: 0.6rem; margin-top: 0.4rem; font-size: 0.75rem; flex-wrap: wrap;">
            <span class="badge" style="background: rgba(255,255,255,0.08);">${escapeHtml(em.duration_formatted || '00:00')}</span>
            <span class="badge badge-yellow">${escapeHtml(em.bitrate_kbps ? `${em.bitrate_kbps} kbps` : 'Bitrate Unknown')}</span>
            <span class="badge" style="background: rgba(255,255,255,0.08);">${escapeHtml(em.size_formatted || '')}</span>
          </div>
          <div style="font-family: monospace; font-size: 0.72rem; color: var(--text-muted); margin-top: 0.35rem; word-break: break-all;">
            Path: ${escapeHtml(em.filepath || em.filename || '')}
          </div>
        `;
      }
      if (syncBtnText) syncBtnText.textContent = 'Overwrite & Force Sync';
    } else {
      if (bannerEl) {
        bannerEl.style.background = 'rgba(166, 227, 161, 0.15)';
        bannerEl.style.border = '1px solid rgba(166, 227, 161, 0.4)';
        bannerEl.style.color = '#a6e3a1';
        bannerEl.innerHTML = `
          <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.4rem;">
            ${SVG_CHECK}
            <span>Not Present on Destination Device</span>
          </div>
          <div style="color: #a6e3a1; font-size: 0.8rem;">This track does not currently exist on ${escapeHtml(data.device_name)}. Ready to sync!</div>
        `;
      }
      if (syncBtnText) syncBtnText.textContent = 'Sync to Device';
    }

    // 2. Render Similar Songs
    const similar = data.similar_songs || [];
    if (similarCountEl) similarCountEl.textContent = `${similar.length} found`;

    if (similarListEl) {
      if (similar.length === 0) {
        similarListEl.innerHTML = '<p class="text-muted" style="font-size: 0.82rem; margin: 0.25rem 0;">No similar songs found on this device.</p>';
      } else {
        let simHtml = '';
        similar.forEach(s => {
          simHtml += `
            <div style="background: var(--bg-mantle); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.6rem 0.85rem; display: flex; justify-content: space-between; align-items: center; gap: 0.75rem;">
              <div style="min-width: 0; flex: 1;">
                <div style="font-weight: 600; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(s.title || 'Unknown')}</div>
                <div class="text-muted" style="font-size: 0.75rem;">${escapeHtml(s.artist || 'Unknown')} &bull; ${escapeHtml(s.duration_formatted || '')} &bull; <span class="badge badge-yellow" style="font-size: 0.7rem;">${escapeHtml(s.bitrate_kbps ? `${s.bitrate_kbps} kbps` : '')}</span></div>
                ${s.comparison_note ? `<div style="font-size: 0.72rem; color: var(--accent-orange); margin-top: 0.2rem;">${escapeHtml(s.comparison_note)}</div>` : ''}
              </div>
              <div style="text-align: right; flex-shrink: 0;">
                <span class="badge badge-yellow" style="font-size: 0.75rem; font-weight: 700;">
                  ${s.similarity_score}% Match
                </span>
              </div>
            </div>
          `;
        });
        similarListEl.innerHTML = simHtml;
      }
    }
  } catch (err) {
    console.error('Error during destination check:', err);
    if (loadingWrap) loadingWrap.style.display = 'none';
  }
}

async function submitSyncSongToDevice() {
  const selectEl = document.getElementById('sync-destination-device');
  const syncBtn = document.getElementById('btn-execute-sync-song');
  const syncBtnText = document.getElementById('btn-execute-sync-text');
  const statusEl = document.getElementById('sync-action-status');

  if (!selectEl || !selectEl.value || !syncCurrentSong) {
    showToast('Please select a valid destination device.', 'error');
    return;
  }

  const deviceId = selectEl.value;
  const qualityEl = document.getElementById('sync-quality-bitrate');
  const qualityVal = qualityEl ? qualityEl.value : 'original';
  const targetBitrate = (qualityVal === 'original') ? null : parseInt(qualityVal, 10);

  syncBtn.disabled = true;
  syncBtnText.textContent = 'Syncing...';
  if (statusEl) statusEl.innerHTML = '<span class="text-muted">Uploading and indexing track on destination device...</span>';

  try {
    const res = await fetch('/api/sync/song', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filepath: syncCurrentSong.filepath,
        device_id: deviceId,
        target_bitrate: targetBitrate,
        force: true
      })
    });
    const data = await res.json();

    if (data.status === 'success') {
      syncBtnText.innerHTML = `Synced ${SVG_CHECK}`;
      if (statusEl) {
        statusEl.innerHTML = `<span style="color: var(--status-online); font-weight: 600; display: inline-flex; align-items: center; gap: 0.35rem;">${SVG_CHECK} ${escapeHtml(data.message || 'Track synced successfully!')}</span>`;
      }
      loadDashboardStats();
      setTimeout(() => {
        hideSyncSongModal();
      }, 1500);
    } else {
      syncBtn.disabled = false;
      syncBtnText.textContent = 'Retry Sync';
      if (statusEl) {
        statusEl.innerHTML = `<span style="color: var(--status-offline); font-weight: 600;">Error: ${escapeHtml(data.error || data.message || 'Sync failed')}</span>`;
      }
    }
  } catch (err) {
    console.error('Error executing single song sync:', err);
    syncBtn.disabled = false;
    syncBtnText.textContent = 'Retry Sync';
    if (statusEl) {
      statusEl.innerHTML = '<span style="color: var(--status-offline); font-weight: 600;">Connection error while syncing song.</span>';
    }
  }
}

// =============================================================================
// SYNCED HISTORY MODULE: Synced Tracks Table & Status Tracking
// =============================================================================

async function loadSyncedHistory() {
  const tbody = document.getElementById('synced-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/synced');
    const records = await res.json();

    if (!records || records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No synced track history recorded in database/db.db.</td></tr>';
      return;
    }

    let html = '';
    records.forEach((r, idx) => {
      html += `
        <tr>
          <td class="col-center text-tabular">${idx + 1}</td>
          <td><strong style="color: var(--text-main);">${escapeHtml(r.filename)}</strong></td>
          <td class="col-center"><span class="badge badge-purple">${escapeHtml(r.device_serial)}</span></td>
          <td><small class="text-muted"><code style="word-break: break-all;">${escapeHtml(r.remote_dir || 'N/A')}</code></small></td>
          <td class="col-center text-tabular"><small class="text-muted">${escapeHtml(r.synced_at || '—')}</small></td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    console.error('Error loading synced history:', err);
  }
}

// =============================================================================
// PLAYLISTS MODULE: Playlist CRUD, Tracks Management & Absent Song Resolution
// =============================================================================

// --- PLAYLIST MANAGEMENT JS LOGIC ---

async function loadPlaylists() {
  const grid = document.getElementById('playlists-grid');
  if (!grid) return;

  try {
    const res = await fetch('/api/playlists');
    allPlaylists = await res.json() || [];
    renderPlaylistsGrid();
  } catch (err) {
    console.error('Error loading playlists:', err);
    grid.innerHTML = '<p class="text-muted">Error loading playlists.</p>';
  }
}

function renderPlaylistsGrid() {
  const grid = document.getElementById('playlists-grid');
  if (!grid) return;

  if (!allPlaylists || allPlaylists.length === 0) {
    grid.innerHTML = '<p class="text-muted">No playlists created yet. Click "+ Create Playlist" to get started!</p>';
    return;
  }

  // Pin "Liked Music" at top
  const sorted = [...allPlaylists].sort((a, b) => {
    if (a.name === 'Liked Music') return -1;
    if (b.name === 'Liked Music') return 1;
    return 0;
  });

  let html = '';
  sorted.forEach(p => {
    const isActive = selectedPlaylist && selectedPlaylist.id === p.id ? 'active' : '';
    const isLikedMusic = (p.name === 'Liked Music');
    const plIcon = isLikedMusic
      ? `<span style="color:#ff0055;display:inline-flex;">${SVG_HEART_FILLED}</span>`
      : `<span style="font-size: 1.25rem;">${SVG_LIST}</span>`;

    html += `
      <div class="playlist-card ${isActive}" onclick="selectPlaylist(${p.id}, '${escapeJs(p.name)}')">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <h4 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: ${isLikedMusic ? 'var(--accent-yellow)' : 'var(--text-main)'};">${escapeHtml(p.name)}</h4>
          ${plIcon}
        </div>
        <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;" class="text-muted">
          <div style="display: flex; align-items: center; gap: 0.35rem;">
            <small>${p.track_count || 0} tracks</small>
            ${p.absent_count > 0 ? `<span class="badge badge-red" style="font-size: 0.65rem; padding: 0.1rem 0.35rem;">${p.absent_count} absent</span>` : ''}
          </div>
          <small>${p.created_at ? p.created_at.substring(0, 10) : ''}</small>
        </div>
      </div>
    `;
  });
  grid.innerHTML = html;

  // Also update sidebar if currently on the detail view
  renderPlaylistSidebar();
}

function renderPlaylistSidebar() {
  const sidebarList = document.getElementById('playlist-sidebar-list');
  if (!sidebarList) return;

  if (!allPlaylists || allPlaylists.length === 0) {
    sidebarList.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">No playlists.</span>';
    return;
  }

  const sorted = [...allPlaylists].sort((a, b) => {
    if (a.name === 'Liked Music') return -1;
    if (b.name === 'Liked Music') return 1;
    return 0;
  });

  let html = '';
  sorted.forEach(p => {
    const isSelected = selectedPlaylist && selectedPlaylist.id === p.id;
    const isLikedMusic = (p.name === 'Liked Music');
    const icon = isLikedMusic ? '❤️' : '🎵';

    html += `
      <div onclick="selectPlaylist(${p.id}, '${escapeJs(p.name)}')"
           style="display: flex; align-items: center; justify-content: space-between; padding: 0.45rem 0.65rem;
                  border-radius: 8px; cursor: pointer; transition: all 0.15s;
                  background: ${isSelected ? 'var(--accent-primary, #6366f1)' : 'transparent'};
                  color: ${isSelected ? '#ffffff' : 'var(--text-main)'};">
        <div style="display: flex; align-items: center; gap: 0.5rem; overflow: hidden;">
          <span style="font-size: 0.85rem; flex-shrink: 0;">${icon}</span>
          <span style="font-size: 0.82rem; font-weight: ${isSelected ? '700' : '500'}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${escapeHtml(p.name)}
          </span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.35rem; flex-shrink: 0; margin-left: 0.4rem;">
          ${p.absent_count > 0 ? `<span class="badge badge-red" style="font-size: 0.6rem; padding: 0.05rem 0.25rem;">${p.absent_count}</span>` : ''}
          <span style="font-size: 0.7rem; opacity: 0.75;">
            ${p.track_count || 0}
          </span>
        </div>
      </div>
    `;
  });
  sidebarList.innerHTML = html;
}

function backToPlaylistGrid() {
  const gridView = document.getElementById('playlist-grid-view');
  const detailView = document.getElementById('playlist-detail-view');
  if (gridView) gridView.style.display = 'block';
  if (detailView) detailView.style.display = 'none';
  selectedPlaylist = null;
  renderPlaylistsGrid();
}

async function selectPlaylist(playlistId, playlistName) {
  selectedPlaylist = { id: playlistId, name: playlistName };

  // 1. Switch to 3-Column Detail View
  const gridView = document.getElementById('playlist-grid-view');
  const detailView = document.getElementById('playlist-detail-view');
  if (gridView) gridView.style.display = 'none';
  if (detailView) detailView.style.display = 'flex';

  // 2. Update Top Header in Detail View
  const nameTitle = document.getElementById('selected-playlist-name');
  if (nameTitle) {
    const isLiked = playlistName === 'Liked Music';
    nameTitle.innerHTML = isLiked
      ? `<span style="color:#ff0055; display:inline-flex;">${SVG_HEART_FILLED}</span> ${escapeHtml(playlistName)}`
      : `<span style="color:var(--accent-yellow); font-size: 1.1rem;">🎵</span> ${escapeHtml(playlistName)}`;
  }

  // 3. Render Left Sidebar
  renderPlaylistSidebar();

  // 4. Update Absent Songs Right Panel
  renderPlaylistAbsentRightPanel(playlistId, playlistName);

  // 5. Load and Render Center Tracks
  const tbody = document.getElementById('playlist-tracks-tbody');
  const badge = document.getElementById('selected-playlist-badge');
  const countText = document.getElementById('playlist-track-count-text');

  if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-muted col-center" style="padding: 2rem;">Loading tracks...</td></tr>';
  if (badge) badge.textContent = 'loading...';
  if (countText) countText.textContent = 'Loading...';

  try {
    const res = await fetch(`/api/playlists/${playlistId}/tracks`);
    currentPlaylistTracks = await res.json() || [];
    renderPlaylistTracks();

    const trackCount = currentPlaylistTracks.length;
    if (badge) badge.textContent = `${trackCount} track${trackCount !== 1 ? 's' : ''}`;
    if (countText) countText.textContent = `${trackCount} song${trackCount !== 1 ? 's' : ''}`;
  } catch (err) {
    console.error('Error fetching playlist tracks:', err);
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-muted col-center">Error loading tracks.</td></tr>';
  }
}

async function ensurePowerampReportLoaded() {
  if (currentAbsentSongs && currentAbsentSongs.length > 0) return;
  try {
    const res = await fetch('/api/poweramp/status');
    if (res.ok) {
      const data = await res.json();
      if (data.has_report && data.report) {
        currentPowerampReport = data.report;
        currentAbsentSongs = data.report.absent_songs || [];
      }
    }
  } catch (e) {
    console.warn('Could not fetch poweramp status:', e);
  }
}

async function renderPlaylistAbsentRightPanel(playlistId, playlistName) {
  const container = document.getElementById('playlist-absent-list');
  const badge = document.getElementById('playlist-absent-count-badge');
  const searchInput = document.getElementById('playlist-absent-search');
  if (searchInput) searchInput.value = '';
  if (badge) badge.textContent = '...';

  // Fetch persistent absent tracks from SQLite for this playlist
  try {
    const res = await fetch(`/api/playlists/${playlistId}/absent`);
    if (res.ok) {
      const dbAbsent = await res.json();
      if (Array.isArray(dbAbsent)) {
        currentAbsentSongs = currentAbsentSongs.filter(s => s.playlist_id !== playlistId && s.playlist_name !== playlistName);
        currentAbsentSongs = [...currentAbsentSongs, ...dbAbsent];
      }
    }
  } catch (err) {
    console.warn('Could not fetch playlist absent tracks:', err);
  }

  await ensurePowerampReportLoaded();
  filterPlaylistPageAbsentSongs();
}

function filterPlaylistPageAbsentSongs() {
  const container = document.getElementById('playlist-absent-list');
  const badge = document.getElementById('playlist-absent-count-badge');
  const searchInput = document.getElementById('playlist-absent-search');
  if (!container) return;

  const currentPlName = selectedPlaylist ? selectedPlaylist.name : '';
  const currentPlId = selectedPlaylist ? selectedPlaylist.id : null;
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  // Filter absent songs for this playlist
  let matchingAbsent = currentAbsentSongs.filter(s => {
    if (currentPlId && s.playlist_id) {
      return s.playlist_id === currentPlId;
    }
    return s.playlist_name && s.playlist_name.toLowerCase() === (currentPlName || '').toLowerCase();
  });

  if (badge) badge.textContent = matchingAbsent.length;

  if (query) {
    matchingAbsent = matchingAbsent.filter(item => {
      const name = (item.readable_name || '').toLowerCase();
      const fn = (item.filename || '').toLowerCase();
      const path = (item.original_path || '').toLowerCase();
      return name.includes(query) || fn.includes(query) || path.includes(query);
    });
  }

  if (matchingAbsent.length === 0) {
    container.innerHTML = `
      <div style="font-size: 0.8rem; color: var(--accent-green, #4ade80); padding: 0.5rem 0; display: flex; align-items: center; gap: 0.4rem;">
        <span>✓</span> All songs matched in this playlist!
      </div>`;
    return;
  }

  let html = '';
  matchingAbsent.forEach((item) => {
    const globalIdx = currentAbsentSongs.indexOf(item);
    const resolveKey = `right-resolve-panel-${globalIdx}`;
    const title = item.readable_name || item.filename;
    const isResolved = Boolean(item._resolved_filepath);

    html += `
      <div id="right-absent-card-${globalIdx}"
           style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.6rem; transition: border 0.15s;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
          <div style="flex: 1; min-width: 0;">
            <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-main); word-break: break-word; line-height: 1.3; ${isResolved ? 'text-decoration: line-through; color: var(--text-muted);' : ''}">
              ${escapeHtml(title)}
            </div>
            <div style="font-size: 0.68rem; color: var(--text-muted); font-family: monospace; word-break: break-all; margin-top: 0.2rem;">
              ${escapeHtml(item.filename)}
            </div>
          </div>
          ${isResolved
            ? `<span style="font-size: 0.68rem; color: var(--accent-green, #4ade80); font-weight: 700; white-space: nowrap;">✓ Resolved</span>`
            : `<button class="btn btn-secondary btn-sm" style="font-size: 0.68rem; padding: 0.2rem 0.45rem; white-space: nowrap; flex-shrink: 0;"
                 onclick="resolveRightAbsentSong(${globalIdx}, this)" title="Fuzzy search local library">
                 🔍 Resolve
               </button>`
          }
        </div>
        <!-- Expandable resolve container -->
        <div id="${resolveKey}" style="display: none; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-color);">
          <div id="${resolveKey}-results" style="display: flex; flex-direction: column; gap: 0.35rem;">
            <span class="text-muted" style="font-size: 0.72rem;">Searching...</span>
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

async function resolveRightAbsentSong(globalIdx, btn) {
  const item = currentAbsentSongs[globalIdx];
  if (!item) return;

  const resolveKey = `right-resolve-panel-${globalIdx}`;
  const panel = document.getElementById(resolveKey);
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  if (!panel) return;

  if (panel.style.display !== 'none') {
    panel.style.display = 'none';
    if (btn) btn.textContent = '🔍 Resolve';
    return;
  }

  panel.style.display = 'block';
  if (btn) btn.textContent = '▲ Close';
  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.72rem;">Searching library...</span>';

  const query = item.readable_name || item.filename;
  const playlistName = item.playlist_name;

  try {
    let matches = fuzzySearchLocalSongs(query, allSongs, 6);
    if (matches.length === 0 && allSongs.length === 0) {
      const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(query)}&n=6`);
      if (res.ok) matches = await res.json();
    }
    renderRightResolveResults(resolveKey, matches, item, playlistName, globalIdx);
  } catch (err) {
    if (resultsDiv) resultsDiv.innerHTML = `<span style="color: var(--accent-red); font-size: 0.72rem;">Search failed: ${escapeHtml(err.message)}</span>`;
  }
}

function renderRightResolveResults(resolveKey, matches, absentItem, playlistName, globalIdx) {
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  if (!resultsDiv) return;

  if (!matches || matches.length === 0) {
    resultsDiv.innerHTML = `
      <div style="font-size: 0.72rem; color: var(--text-muted);">
        No local matches found.
        <div style="margin-top: 0.4rem; display: flex; gap: 0.3rem;">
          <input type="text" id="${resolveKey}-q" class="search-bar" style="height: 24px; font-size: 0.7rem; flex: 1;" placeholder="Custom query...">
          <button class="btn btn-secondary btn-sm" style="font-size: 0.65rem; padding: 0.15rem 0.4rem;" onclick="searchRightCustom(${globalIdx})">Go</button>
        </div>
      </div>`;
    return;
  }

  let html = `<div style="font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.2rem;">${matches.length} candidate match${matches.length !== 1 ? 'es' : ''}:</div>`;
  matches.forEach(s => {
    const fp = s.filepath || s._data || '';
    const title = s.title || s.filename || fp;
    const artist = s.artist || 'Unknown';

    html += `
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.4rem; padding: 0.3rem 0.4rem; background: var(--bg-crust); border-radius: 6px;">
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(title)}">
            ${escapeHtml(title)}
          </div>
          <div style="font-size: 0.65rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${escapeHtml(artist)}
          </div>
        </div>
        <button class="btn btn-sm" style="font-size: 0.65rem; padding: 0.15rem 0.45rem; white-space: nowrap; flex-shrink: 0;"
          onclick="confirmResolveMatch(${globalIdx}, '${escapeJs(fp)}', '${escapeJs(title)}', '${escapeJs(playlistName)}'); filterPlaylistPageAbsentSongs();">
          + Use
        </button>
      </div>
    `;
  });

  html += `
    <div style="margin-top: 0.35rem; display: flex; gap: 0.3rem;">
      <input type="text" id="${resolveKey}-q" class="search-bar" style="height: 24px; font-size: 0.7rem; flex: 1;" placeholder="Search different title...">
      <button class="btn btn-secondary btn-sm" style="font-size: 0.65rem; padding: 0.15rem 0.4rem;" onclick="searchRightCustom(${globalIdx})">Search</button>
    </div>
  `;

  resultsDiv.innerHTML = html;
}

async function searchRightCustom(globalIdx) {
  const resolveKey = `right-resolve-panel-${globalIdx}`;
  const inputEl = document.getElementById(`${resolveKey}-q`);
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  const item = currentAbsentSongs[globalIdx];
  if (!inputEl || !item) return;

  const q = inputEl.value.trim();
  if (!q) return;

  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.72rem;">Searching...</span>';

  let matches = fuzzySearchLocalSongs(q, allSongs, 6);
  if (matches.length === 0) {
    try {
      const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(q)}&n=6`);
      if (res.ok) matches = await res.json();
    } catch (_) {}
  }
  renderRightResolveResults(resolveKey, matches, item, item.playlist_name, globalIdx);
}

function renderPlaylistTracks() {
  const tbody = document.getElementById('playlist-tracks-tbody');
  if (!tbody) return;

  if (!currentPlaylistTracks || currentPlaylistTracks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-muted col-center" style="padding: 2rem;">No tracks in this playlist yet. Add songs from the Music Library tab!</td></tr>';
    return;
  }

  let html = '';
  currentPlaylistTracks.forEach((s, idx) => {
    const isAbsent = (s.status === 'absent');
    const isThisTrackPlaying = (currentTrackPath === s.filepath && isPlaying);
    const playBtnIcon = isThisTrackPlaying ? SVG_PAUSE : SVG_PLAY;
    const playBtnText = isThisTrackPlaying ? 'Pause' : 'Play';
    const rowClass = isThisTrackPlaying ? 'class="playing-row"' : (isAbsent ? 'class="absent-track-row" style="opacity: 0.88;"' : '');

    const absentBadge = isAbsent
      ? `<span class="badge badge-red" style="font-size: 0.65rem; margin-left: 0.4rem; vertical-align: middle;">ABSENT</span>`
      : '';

    const actionsHtml = isAbsent
      ? `<div class="action-btn-group">
           <button class="btn btn-secondary btn-sm" onclick="openResolveForTrack(${idx})" title="Resolve absent track in right panel">🔍 Resolve</button>
           <button class="btn btn-secondary btn-danger btn-sm" onclick="removeTrackFromPlaylist(${selectedPlaylist.id}, '${escapeJs(s.filepath)}')" title="Remove from playlist">${SVG_TRASH} Remove</button>
         </div>`
      : `<div class="action-btn-group">
           <button class="btn btn-secondary btn-sm btn-song-like ${likedSongPaths.has(s.filepath) ? 'btn-liked' : ''}" data-filepath="${escapeHtml(s.filepath)}" onclick="toggleLikeTrack('${escapeJs(s.filepath)}', '${escapeJs(s.title || s.filename)}', '${escapeJs(s.artist || '')}')" title="${likedSongPaths.has(s.filepath) ? 'Unlike' : 'Like'}">${likedSongPaths.has(s.filepath) ? SVG_HEART_FILLED : SVG_HEART}</button>
           <button class="btn btn-secondary btn-sm" onclick="playPlaylistFromTrack(${idx})" title="${playBtnText}">${playBtnIcon} ${playBtnText}</button>
           <button class="btn btn-secondary btn-danger btn-sm" onclick="removeTrackFromPlaylist(${selectedPlaylist.id}, '${escapeJs(s.filepath)}')" title="Remove from playlist">${SVG_TRASH} Remove</button>
         </div>`;

    html += `
      <tr ${rowClass}>
        <td class="col-center text-tabular">${idx + 1}</td>
        <td>
          <div class="track-meta-cell">
            <span class="track-title" title="${escapeHtml(s.title || s.filename)}">
              ${escapeHtml(s.title || s.filename)}
              ${absentBadge}
            </span>
            <span class="track-subtitle" title="${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}">${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}</span>
          </div>
        </td>
        <td class="col-center text-tabular">${escapeHtml(s.duration_formatted || (isAbsent ? 'N/A' : '00:00'))}</td>
        <td class="col-center text-tabular">${escapeHtml(s.size_formatted || (isAbsent ? 'N/A' : '—'))}</td>
        <td class="col-right">
          ${actionsHtml}
        </td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

function openResolveForTrack(idx) {
  const track = currentPlaylistTracks[idx];
  if (!track) return;

  // Find or insert absent item into currentAbsentSongs
  let absentItem = currentAbsentSongs.find(a =>
    (track.id && a.id === track.id) ||
    (track.original_path && a.original_path === track.original_path) ||
    (a.original_path === track.filepath) ||
    (a.filepath === track.filepath)
  );

  if (!absentItem) {
    absentItem = {
      playlist_id: selectedPlaylist ? selectedPlaylist.id : track.playlist_id,
      playlist_name: selectedPlaylist ? selectedPlaylist.name : '',
      filename: track.filename || track.title,
      readable_name: track.title,
      original_path: track.original_path || track.filepath,
      filepath: track.filepath,
      id: track.id
    };
    currentAbsentSongs.push(absentItem);
    filterPlaylistPageAbsentSongs();
  }

  const globalIdx = currentAbsentSongs.indexOf(absentItem);
  filterPlaylistPageAbsentSongs();
  setTimeout(() => {
    const card = document.getElementById(`right-absent-card-${globalIdx}`);
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const btn = card.querySelector('button');
      resolveRightAbsentSong(globalIdx, btn);
    }
  }, 50);
}

async function deleteCurrentPlaylist() {
  if (!selectedPlaylist) return;
  const pName = selectedPlaylist.name;
  const pId = selectedPlaylist.id;

  if (pName === 'Liked Music') {
    showToast('Cannot delete the Liked Music playlist', 'info');
    return;
  }

  showConfirmModal({
    title: 'Delete Playlist',
    message: `Are you sure you want to delete playlist "${pName}"?`,
    details: 'This will delete the playlist only; your audio files remain intact.',
    confirmText: 'Delete Playlist',
    confirmClass: 'btn btn-danger',
    onConfirm: async () => {
      try {
        const res = await fetch('/api/playlists/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ playlist_id: pId })
        });
        const data = await res.json();
        if (data.status === 'success') {
          backToPlaylistGrid();
          loadPlaylists();
          showToast(`Playlist "${pName}" deleted.`, 'success');
        } else {
          showToast(`Error deleting playlist: ${data.error || 'Failed to delete'}`, 'error');
        }
      } catch (err) {
        console.error('Error deleting playlist:', err);
        showToast('Error connecting to server.', 'error');
      }
    }
  });
}

function showAddToPlaylistModal(filepath, title) {
  targetTrackForPlaylist = { filepath, title };
  const modal = document.getElementById('modal-add-to-playlist');
  const trackTitleEl = document.getElementById('modal-track-title');
  const select = document.getElementById('select-playlist-choice');

  if (trackTitleEl) trackTitleEl.textContent = `Song: ${title}`;

  if (select) {
    let options = '<option value="">Select a playlist...</option>';
    allPlaylists.forEach(p => {
      options += `<option value="${p.id}">${escapeHtml(p.name)} (${p.track_count} tracks)</option>`;
    });
    select.innerHTML = options;
  }

  if (modal) modal.style.display = 'flex';
}

function hideAddToPlaylistModal() {
  const modal = document.getElementById('modal-add-to-playlist');
  if (modal) modal.style.display = 'none';
  targetTrackForPlaylist = null;
}

async function submitAddToPlaylist() {
  const select = document.getElementById('select-playlist-choice');
  const playlistId = select ? select.value : null;

  if (!playlistId || !targetTrackForPlaylist) {
    showToast('Please select a playlist!', 'error');
    return;
  }

  const trackTitle = targetTrackForPlaylist.title;

  try {
    const res = await fetch(`/api/playlists/${playlistId}/add-track`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath: targetTrackForPlaylist.filepath })
    });
    const data = await res.json();
    if (data.status === 'success') {
      hideAddToPlaylistModal();
      await loadPlaylists();
      if (selectedPlaylist && selectedPlaylist.id == playlistId) {
        selectPlaylist(selectedPlaylist.id, selectedPlaylist.name);
      }
      showToast(`Added "${trackTitle}" to playlist.`, 'success');
    } else {
      showToast(`Error adding track: ${data.error || 'Failed to add track'}`, 'error');
    }
  } catch (err) {
    console.error('Error adding track to playlist:', err);
    showToast('Error connecting to server.', 'error');
  }
}

async function removeTrackFromPlaylist(playlistId, filepath) {
  try {
    const res = await fetch(`/api/playlists/${playlistId}/remove-track`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath: filepath })
    });
    const data = await res.json();
    if (data.status === 'success') {
      await loadPlaylists();
      if (selectedPlaylist && selectedPlaylist.id == playlistId) {
        selectPlaylist(selectedPlaylist.id, selectedPlaylist.name);
      }
      showToast('Track removed from playlist.', 'info');
    } else {
      showToast(`Error removing track: ${data.error || 'Failed to remove'}`, 'error');
    }
  } catch (err) {
    console.error('Error removing track from playlist:', err);
    showToast('Error connecting to server.', 'error');
  }
}

function playCurrentPlaylist() {
  if (!currentPlaylistTracks || currentPlaylistTracks.length === 0) return;
  playPlaylistFromTrack(0);
}

function playPlaylistFromTrack(index) {
  if (!currentPlaylistTracks || index < 0 || index >= currentPlaylistTracks.length) return;
  const queue = currentPlaylistTracks.map(t => ({
    filepath: t.filepath,
    title: t.title || t.filename,
    artist: t.artist || 'Unknown Artist'
  }));

  const startTrack = queue[index];
  playAudio(startTrack.filepath, startTrack.title, startTrack.artist, queue, index);
}

// =============================================================================
// TRASH & HIDDEN MODULE: Deleted Songs Log, File Restore & SQLite Hide List
// =============================================================================

// --- FILE DELETION, HIDING & OTHER UTILITIES ---

async function deleteSong(filepath, evt, deviceId, songId, filename) {
  const targetDevice = deviceId || currentDeviceId || 'local';
  let devLabel = 'Local Storage';
  if (targetDevice.startsWith('adb')) {
    const serial = targetDevice.replace('adb_', '').replace('adb:', '');
    devLabel = `ADB Device [${serial}]`;
  } else if (targetDevice.startsWith('ip')) {
    const ip = targetDevice.replace('ip_', '').replace('ip:', '');
    devLabel = `Over-IP Peer [${ip}]`;
  }

  const songName = filename || filepath.split('/').pop() || 'this audio file';

  showConfirmModal({
    title: 'Delete Audio File',
    message: `Permanently delete '${songName}' from ${devLabel}?`,
    details: filepath,
    confirmText: 'Delete Song',
    confirmClass: 'btn btn-danger',
    onConfirm: async () => {
      let targetEl = null;
      if (evt && evt.target) {
        targetEl = evt.target.closest('li, tr');
        if (targetEl) {
          targetEl.style.transition = 'all 0.3s ease';
          targetEl.style.opacity = '0.2';
          targetEl.style.filter = 'blur(4px)';
        }
      }

      try {
        const res = await fetch('/api/song/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filepath: filepath,
            device_id: targetDevice,
            song_id: songId,
            filename: filename
          })
        });
        const data = await res.json();
        if (data.status === 'success') {
          if (targetEl) targetEl.remove();

          if (allSongs && allSongs.length > 0) {
            allSongs = allSongs.filter(s => s.filepath !== filepath);
            filteredSongs = filteredSongs.filter(s => s.filepath !== filepath);
            updateLibraryPaginationInfo(
              1,
              Math.min(libPageSize, filteredSongs.length),
              filteredSongs.length,
              Math.ceil(filteredSongs.length / libPageSize) || 1
            );
          }

          if (targetDevice === 'local') {
            loadDuplicates();
            loadSongs();
          } else {
            loadDeviceSongs(targetDevice, true);
          }
          loadDashboardStats();
          showToast(`Deleted '${songName}' successfully.`, 'success');
        } else {
          if (targetEl) {
            targetEl.style.opacity = '1';
            targetEl.style.filter = 'none';
          }
          showToast(`Error deleting file: ${data.error || data.message || 'Failed to delete file'}`, 'error');
        }
      } catch (err) {
        console.error('Error deleting song:', err);
        if (targetEl) {
          targetEl.style.opacity = '1';
          targetEl.style.filter = 'none';
        }
        showToast('Error connecting to server to delete file.', 'error');
      }
    }
  });
}

async function loadHiddenFiles() {
  const tbody = document.getElementById('hidden-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/hidden');
    const records = await res.json();

    if (!records || records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-muted">No hidden files in SQLite database (database/db.db).</td></tr>';
      return;
    }

    let html = '';
    records.forEach((r, idx) => {
      html += `
        <tr>
          <td class="col-center text-tabular">${idx + 1}</td>
          <td><strong style="color: var(--text-main);">${escapeHtml(r.filename)}</strong></td>
          <td><small class="text-muted"><code style="word-break: break-all;">${escapeHtml(r.filepath)}</code></small></td>
          <td class="col-right">
            <button class="btn btn-secondary btn-sm" onclick="unhideSong('${escapeJs(r.filepath)}')">${SVG_UNHIDE} Unhide</button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    console.error('Error loading hidden files:', err);
  }
}


async function unhideSong(filepath) {
  try {
    const res = await fetch('/api/unhide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath: filepath })
    });
    const data = await res.json();
    if (data.status === 'success') {
      loadHiddenFiles();
      loadDashboardStats();
      loadSongs();
    }
  } catch (err) {
    console.error('Error unhiding song:', err);
  }
}

async function hideSong(filepath) {
  try {
    const res = await fetch('/api/hide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath: filepath })
    });
    const data = await res.json();
    if (data.status === 'success') {
      loadHiddenFiles();
      loadDashboardStats();
      loadSongs();
    }
  } catch (err) {
    console.error('Error hiding song:', err);
  }
}


// --- DELETED SONGS (TRASH) JS LOGIC ---

async function loadDeletedSongs() {
  const tbody = document.getElementById('deleted-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/deleted');
    const records = await res.json();

    if (!records || records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-muted">No deleted songs. Deleted files are kept in tmp/deleted/ until restored or trash is emptied.</td></tr>';
      return;
    }

    let html = '';
    records.forEach((r, idx) => {
      const bitrate = r.bitrate_kbps ? String(r.bitrate_kbps).replace(/\s*kbps\s*$/i, '') + ' kbps' : '—';
      const size = r.size_bytes ? formatBytes(r.size_bytes) : '—';
      html += `
        <tr>
          <td class="col-center text-tabular">${idx + 1}</td>
          <td>
            <div class="track-meta-cell">
              <span class="track-title" title="${escapeHtml(r.title || r.filename || 'Unknown')}">${escapeHtml(r.title || r.filename || 'Unknown')}</span>
              <span class="track-subtitle" title="${escapeHtml(r.filepath || '')}">${escapeHtml(r.filepath || '')}</span>
            </div>
          </td>
          <td><small class="text-muted"><code style="word-break: break-all;">${escapeHtml(r.filepath || '')}</code></small></td>
          <td class="col-center"><span class="badge badge-purple text-tabular">${escapeHtml(bitrate)}</span></td>
          <td class="col-center text-tabular">${escapeHtml(size)}</td>
          <td class="col-center text-tabular"><small class="text-muted">${escapeHtml(r.file_created_at || '—')}</small></td>
          <td class="col-center text-tabular"><small class="text-muted">${escapeHtml(r.file_modified_at || '—')}</small></td>
          <td class="col-center text-tabular"><small class="text-muted">${escapeHtml(r.deleted_at || '—')}</small></td>
          <td class="col-right">
            <button class="btn btn-secondary btn-sm" onclick="restoreDeletedSong(${r.id})" title="Restore song">Restore</button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    console.error('Error loading deleted songs:', err);
    tbody.innerHTML = '<tr><td colspan="9" class="text-muted">Error loading deleted songs.</td></tr>';
  }
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  let val = bytes;
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024;
    i++;
  }
  return `${val.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

async function restoreDeletedSong(recordId) {
  showConfirmModal({
    title: 'Restore Deleted Track',
    message: 'Restore this audio file back to its original location?',
    confirmText: 'Restore Track',
    confirmClass: 'btn',
    onConfirm: async () => {
      try {
        const res = await fetch('/api/deleted/restore', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: recordId })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast(`Restored ${data.message || 'song successfully.'}`, 'success');
          loadDeletedSongs();
          loadSongs();
          loadDuplicates();
          loadDashboardStats();
        } else {
          showToast(`Error restoring song: ${data.error || data.message || 'Failed to restore'}`, 'error');
          loadDeletedSongs();
        }
      } catch (err) {
        console.error('Error restoring deleted song:', err);
        showToast('Error connecting to server.', 'error');
      }
    }
  });
}

async function clearDeletedHistory() {
  showConfirmModal({
    title: 'Empty Trash',
    message: 'Empty the trash and permanently purge all deleted files?',
    details: 'This will permanently remove all cached files in tmp/deleted/ and clear the deletion history. This action cannot be undone.',
    confirmText: 'Empty Trash',
    confirmClass: 'btn btn-danger',
    onConfirm: async () => {
      try {
        const res = await fetch('/api/deleted/clear', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
          showToast(data.message || 'Trash emptied successfully.', 'success');
          loadDeletedSongs();
        } else {
          showToast(`Error emptying trash: ${data.error || data.message || 'Failed to clear history'}`, 'error');
        }
      } catch (err) {
        console.error('Error clearing deleted songs history:', err);
        showToast('Error connecting to server.', 'error');
      }
    }
  });
}

// =============================================================================
// POWERAMP MODULE: Poweramp Backup Importer, Report Modal & Candidate Resolver
// =============================================================================

// POWERAMP PLAYLIST IMPORT & REPORT SYSTEM
// ==========================================

let currentPowerampReport = null;
let currentAbsentSongs = [];
let powerampSelectedFile = null;

function showPowerampImportModal() {
  const modal = document.getElementById('modal-poweramp-import');
  const pathInput = document.getElementById('poweramp-path-input');
  const statusDiv = document.getElementById('poweramp-import-status');
  const filenameLabel = document.getElementById('poweramp-selected-filename');
  const fileInput = document.getElementById('poweramp-file-input');

  powerampSelectedFile = null;
  if (fileInput) fileInput.value = '';
  if (pathInput) pathInput.value = '';
  if (filenameLabel) filenameLabel.textContent = 'No file chosen';
  if (statusDiv) {
    statusDiv.style.display = 'none';
    statusDiv.textContent = '';
  }

  if (modal) modal.style.display = 'flex';
}

function hidePowerampImportModal() {
  const modal = document.getElementById('modal-poweramp-import');
  if (modal) modal.style.display = 'none';
}

function handlePowerampFileChosen(event) {
  const file = event.target.files && event.target.files[0];
  const label = document.getElementById('poweramp-selected-filename');
  if (file) {
    powerampSelectedFile = file;
    if (label) label.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  } else {
    powerampSelectedFile = null;
    if (label) label.textContent = 'No file chosen';
  }
}

async function submitPowerampImport() {
  const pathInput = document.getElementById('poweramp-path-input');
  const statusDiv = document.getElementById('poweramp-import-status');
  const submitBtn = document.getElementById('btn-submit-poweramp-import');

  const enteredPath = pathInput ? pathInput.value.trim() : '';

  if (!powerampSelectedFile && !enteredPath) {
    showToast('Please select a file or enter a local path!', 'error');
    return;
  }

  if (statusDiv) {
    statusDiv.style.display = 'block';
    statusDiv.style.color = 'var(--text-main)';
    statusDiv.innerHTML = 'Analyzing database and matching library tracks...';
  }
  if (submitBtn) submitBtn.disabled = true;

  try {
    let res;
    if (powerampSelectedFile) {
      const formData = new FormData();
      formData.append('file', powerampSelectedFile);
      res = await fetch('/api/poweramp/import', {
        method: 'POST',
        body: formData
      });
    } else {
      res = await fetch('/api/poweramp/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: enteredPath })
      });
    }

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      hidePowerampImportModal();
      showToast(`Imported ${data.total_playlists} playlists! ${data.matched_tracks_count} songs matched.`, 'success');
      await loadPlaylists();
      renderAbsentSongsModal(data);
    } else {
      if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.style.color = 'var(--accent-red, #f87171)';
        statusDiv.textContent = `Import error: ${data.error || 'Unknown error'}`;
      }
      showToast(`Import failed: ${data.error || 'Server error'}`, 'error');
    }
  } catch (err) {
    console.error('Poweramp import error:', err);
    if (statusDiv) {
      statusDiv.style.display = 'block';
      statusDiv.style.color = 'var(--accent-red, #f87171)';
      statusDiv.textContent = `Connection error: ${err.message}`;
    }
    showToast('Error connecting to server during import.', 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function renderAbsentSongsModal(report) {
  currentPowerampReport = report;
  currentAbsentSongs = report.absent_songs || [];

  const modal = document.getElementById('modal-absent-songs');
  if (!modal) return;

  // Stats
  const elPlaylists = document.getElementById('report-stat-playlists');
  const elMatched = document.getElementById('report-stat-matched');
  const elAbsent = document.getElementById('report-stat-absent');
  const elLiked = document.getElementById('report-stat-liked');

  if (elPlaylists) elPlaylists.textContent = report.total_playlists || 0;
  if (elMatched) elMatched.textContent = report.matched_tracks_count || 0;
  if (elAbsent) elAbsent.textContent = report.absent_tracks_count || 0;
  if (elLiked) elLiked.textContent = report.liked_tracks_synced || 0;

  // Populate playlist filter
  const filterSelect = document.getElementById('absent-filter-playlist');
  if (filterSelect) {
    let options = '<option value="">All Playlists</option>';
    if (report.playlists) {
      report.playlists.forEach(pl => {
        options += `<option value="${escapeHtml(pl.name)}">${escapeHtml(pl.name)} (${pl.absent_count} absent)</option>`;
      });
    }
    filterSelect.innerHTML = options;
    filterSelect.value = '';
  }

  const searchInput = document.getElementById('absent-search-input');
  if (searchInput) searchInput.value = '';

  filterAbsentSongs();
  modal.style.display = 'flex';
}

function hideAbsentSongsModal() {
  const modal = document.getElementById('modal-absent-songs');
  if (modal) modal.style.display = 'none';
}

// Track which resolve panels are open: key = "idx-playlistname-filename"
const _resolveOpenPanels = new Set();

function filterAbsentSongs() {
  const filterSelect = document.getElementById('absent-filter-playlist');
  const searchInput = document.getElementById('absent-search-input');
  const tbody = document.getElementById('absent-songs-tbody');
  const countLabel = document.getElementById('absent-count-label');

  const selectedPl = filterSelect ? filterSelect.value : '';
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  let filtered = currentAbsentSongs;
  if (selectedPl) {
    filtered = filtered.filter(item => item.playlist_name === selectedPl);
  }
  if (query) {
    filtered = filtered.filter(item => {
      const name = (item.readable_name || '').toLowerCase();
      const fn = (item.filename || '').toLowerCase();
      const path = (item.original_path || '').toLowerCase();
      return name.includes(query) || fn.includes(query) || path.includes(query);
    });
  }

  if (countLabel) {
    countLabel.textContent = `Showing ${filtered.length} of ${currentAbsentSongs.length} absent songs`;
  }

  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-muted col-center" style="padding: 1.5rem;">No absent songs match criteria.</td></tr>';
    return;
  }

  let html = '';
  filtered.forEach((item, idx) => {
    const globalIdx = currentAbsentSongs.indexOf(item);
    const resolveKey = `resolve-panel-${globalIdx}`;
    html += `
      <tr id="absent-row-${globalIdx}">
        <td class="col-center text-tabular">${idx + 1}</td>
        <td>
          <div style="font-weight: 600; color: var(--text-main); word-break: break-all;">
            ${escapeHtml(item.readable_name || item.filename)}
          </div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">${escapeHtml(item.filename)}</div>
        </td>
        <td style="font-size: 0.78rem; font-family: monospace; color: var(--text-muted); word-break: break-all;">
          ${escapeHtml(item.original_path || '—')}
        </td>
        <td style="font-size: 0.85rem;">
          <span class="badge badge-purple">${escapeHtml(item.playlist_name || 'Unknown')}</span>
        </td>
        <td class="col-center">
          <button class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 0.25rem 0.5rem; white-space: nowrap;"
            onclick="resolveAbsentSong(${globalIdx}, this)" title="Search local library for a match">
            🔍 Resolve
          </button>
        </td>
      </tr>
      <tr id="${resolveKey}" style="display: none;">
        <td colspan="5" style="padding: 0; background: var(--bg-crust); border-bottom: 1px solid var(--border-color);">
          <div style="padding: 0.75rem 1rem;">
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
              Searching library for: <strong style="color: var(--text-main);">${escapeHtml(item.readable_name || item.filename)}</strong>
            </div>
            <div id="${resolveKey}-results" style="display: flex; flex-direction: column; gap: 0.4rem;">
              <span class="text-muted" style="font-size: 0.8rem;">Searching...</span>
            </div>
          </div>
        </td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

async function resolveAbsentSong(globalIdx, btn) {
  const item = currentAbsentSongs[globalIdx];
  if (!item) return;

  const resolveKey = `resolve-panel-${globalIdx}`;
  const panelRow = document.getElementById(resolveKey);
  const resultsDiv = document.getElementById(`${resolveKey}-results`);

  if (!panelRow) return;

  // Toggle: close if already open
  if (panelRow.style.display !== 'none') {
    panelRow.style.display = 'none';
    if (btn) btn.textContent = '🔍 Resolve';
    return;
  }

  // Open panel and start searching
  panelRow.style.display = '';
  if (btn) btn.textContent = '▲ Close';
  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">Searching library...</span>';

  const query = item.readable_name || item.filename;
  const playlistName = item.playlist_name;

  try {
    // Strategy 1: client-side fuzzy search against allSongs (instant, no round-trip)
    let matches = fuzzySearchLocalSongs(query, allSongs, 8);

    // Strategy 2: fallback to server-side search if allSongs is empty
    if (matches.length === 0 && allSongs.length === 0) {
      const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(query)}&n=8`);
      if (res.ok) {
        matches = await res.json();
      }
    }

    renderResolveResults(resolveKey, matches, item, playlistName, globalIdx);
  } catch (err) {
    console.error('Resolve search error:', err);
    if (resultsDiv) resultsDiv.innerHTML = `<span style="color: var(--accent-red, #f87171); font-size: 0.8rem;">Search failed: ${escapeHtml(err.message)}</span>`;
  }
}

function fuzzySearchLocalSongs(query, songs, maxResults = 8) {
  if (!query || !songs || songs.length === 0) return [];

  const qLower = query.toLowerCase();
  const cleanQ = cleanStringForResolve(query);
  const qWords = cleanQ.split(/\s+/).filter(Boolean);

  const scored = [];
  for (const s of songs) {
    const title = (s.title || '').toLowerCase();
    const fn = (s.filename || '').toLowerCase();
    const artist = (s.artist || '').toLowerCase();
    const cleanTitle = cleanStringForResolve(s.title || s.filename || '');
    const cleanFn = cleanStringForResolve(s.filename || '');

    let score = 0;

    // Exact / substring matches
    if (title === qLower || fn === qLower) score += 100;
    else if (title.startsWith(qLower) || fn.startsWith(qLower)) score += 60;
    else if (title.includes(qLower) || fn.includes(qLower)) score += 30;

    // Clean-string matches
    if (cleanTitle === cleanQ) score += 70;
    else if (cleanTitle.startsWith(cleanQ)) score += 35;
    else if (cleanQ && cleanTitle.includes(cleanQ)) score += 20;

    if (cleanFn === cleanQ) score += 55;
    else if (cleanFn.startsWith(cleanQ)) score += 28;
    else if (cleanQ && cleanFn.includes(cleanQ)) score += 15;

    // Word overlap scoring
    if (qWords.length > 0) {
      const titleWords = new Set(cleanTitle.split(/\s+/).filter(Boolean));
      const fnWords = new Set(cleanFn.split(/\s+/).filter(Boolean));
      const allWords = new Set([...titleWords, ...fnWords]);
      const common = qWords.filter(w => allWords.has(w)).length;
      score += Math.round(80 * common / qWords.length);
    }

    if (score > 0) scored.push({ ...s, _score: score });
  }

  scored.sort((a, b) => b._score - a._score);
  return scored.slice(0, maxResults);
}

function cleanStringForResolve(text) {
  if (!text) return '';
  let s = text.toLowerCase();
  s = s.replace(/\s*[\(\[][^\)\]]*(?:128|192|256|320|flac|kbps|audio|video|lyrics|official|remaster|hd|hq)[^\)\]]*[\)\]]/gi, '');
  s = s.replace(/\.(?:mp3|flac|m4a|wav|ogg|opus|aac)$/i, '');
  s = s.replace(/[\-_.\(\)\[\]'"~]+/g, ' ');
  return s.split(/\s+/).filter(Boolean).join(' ').trim();
}

function renderResolveResults(resolveKey, matches, absentItem, playlistName, globalIdx) {
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  if (!resultsDiv) return;

  if (!matches || matches.length === 0) {
    resultsDiv.innerHTML = `
      <div style="font-size: 0.8rem; color: var(--text-muted); padding: 0.35rem 0;">
        No matches found in local library.
        <a href="#" style="color: var(--accent-yellow); margin-left: 0.4rem; font-size: 0.75rem;"
           onclick="resolveSearchDesktop(${globalIdx}); return false;">
          Search connected device →
        </a>
      </div>`;
    return;
  }

  let html = `<div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.35rem;">${matches.length} match${matches.length !== 1 ? 'es' : ''} found:</div>`;
  html += `<div style="display: flex; flex-direction: column; gap: 0.3rem; max-height: 200px; overflow-y: auto;">`;

  matches.forEach((song, i) => {
    const fp = song.filepath || song._data || '';
    const title = song.title || song.filename || fp;
    const artist = song.artist || 'Unknown';
    const dur = song.duration_formatted || '';
    const isResolved = absentItem._resolved_filepath === fp;

    html += `
      <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.5rem;
                  background: ${isResolved ? 'rgba(74,222,128,0.12)' : 'var(--bg-card)'}; border-radius: 6px;
                  border: 1px solid ${isResolved ? 'rgba(74,222,128,0.3)' : 'var(--border-color)'};">
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 0.8rem; font-weight: 600; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
               title="${escapeHtml(fp)}">
            ${escapeHtml(title)}
          </div>
          <div style="font-size: 0.7rem; color: var(--text-muted);">
            ${escapeHtml(artist)}${dur ? ' • ' + escapeHtml(dur) : ''}
          </div>
        </div>
        ${isResolved
          ? `<span style="font-size: 0.7rem; color: var(--accent-green, #4ade80); font-weight: 700; white-space: nowrap;">✓ Resolved</span>`
          : `<button class="btn btn-sm" style="font-size: 0.7rem; padding: 0.2rem 0.55rem; white-space: nowrap; flex-shrink: 0;"
               onclick="confirmResolveMatch(${globalIdx}, '${escapeJs(fp)}', '${escapeJs(title)}', '${escapeJs(playlistName)}')"
               title="Add this song to the playlist as a replacement">
               + Use This
             </button>`}
      </div>
    `;
  });

  html += `</div>`;

  // Also add manual search box
  html += `
    <div style="margin-top: 0.5rem; display: flex; gap: 0.4rem; align-items: center;">
      <input type="text" id="${resolveKey}-manual-q" class="search-bar" style="flex: 1; height: 28px; font-size: 0.75rem; box-sizing: border-box;"
             placeholder="Search differently..." value="${escapeHtml(absentItem.readable_name || absentItem.filename)}"
             onkeydown="if(event.key==='Enter') resolveManualSearch(${globalIdx})">
      <button class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 0.25rem 0.6rem; white-space: nowrap;"
              onclick="resolveManualSearch(${globalIdx})">Search</button>
    </div>`;

  resultsDiv.innerHTML = html;
}

async function resolveManualSearch(globalIdx) {
  const resolveKey = `resolve-panel-${globalIdx}`;
  const inputEl = document.getElementById(`${resolveKey}-manual-q`);
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  const item = currentAbsentSongs[globalIdx];
  if (!item || !inputEl) return;

  const q = inputEl.value.trim();
  if (!q) return;

  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">Searching...</span>';

  let matches = fuzzySearchLocalSongs(q, allSongs, 8);
  if (matches.length === 0) {
    try {
      const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(q)}&n=8`);
      if (res.ok) matches = await res.json();
    } catch (_) {}
  }

  renderResolveResults(resolveKey, matches, item, item.playlist_name, globalIdx);
}

async function resolveSearchDesktop(globalIdx) {
  const item = currentAbsentSongs[globalIdx];
  if (!item) return;

  const resolveKey = `resolve-panel-${globalIdx}`;
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">Searching connected device...</span>';

  const q = item.readable_name || item.filename;
  try {
    const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(q)}&n=8`);
    const matches = res.ok ? await res.json() : [];
    renderResolveResults(resolveKey, matches, item, item.playlist_name, globalIdx);
  } catch (err) {
    if (resultsDiv) resultsDiv.innerHTML = `<span style="color: var(--accent-red, #f87171); font-size: 0.8rem;">Search failed: ${escapeHtml(err.message)}</span>`;
  }
}

async function confirmResolveMatch(globalIdx, filepath, songTitle, playlistName) {
  const item = currentAbsentSongs[globalIdx];
  if (!item) return;

  // Find playlist ID from allPlaylists or selectedPlaylist
  const playlist = allPlaylists.find(p => p.name && p.name.toLowerCase() === (playlistName || '').toLowerCase())
                   || (selectedPlaylist && selectedPlaylist.name === playlistName ? selectedPlaylist : null)
                   || (selectedPlaylist ? selectedPlaylist : null);

  if (!playlist) {
    showToast(`Playlist "${playlistName}" not found locally. Import first to create the playlist.`, 'info');
    // Still mark as resolved in UI
    item._resolved_filepath = filepath;
    item._resolved_title = songTitle;
    const resolveKey = `resolve-panel-${globalIdx}`;
    renderResolveResults(resolveKey, null, item, playlistName, globalIdx);
    updateAbsentRowResolved(globalIdx, songTitle);
    return;
  }

  try {
    const res = await fetch(`/api/playlists/${playlist.id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resolved_filepath: filepath,
        original_path: item.original_path || item.filepath,
        track_id: item.id || null,
        title: songTitle
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      item._resolved_filepath = filepath;
      item._resolved_title = songTitle;
      item.status = 'present';

      const resolveKey = `resolve-panel-${globalIdx}`;
      // Re-render the results panel showing ✓ Resolved state
      const currentQ = currentAbsentSongs[globalIdx].readable_name || currentAbsentSongs[globalIdx].filename;
      const matches = fuzzySearchLocalSongs(currentQ, allSongs, 8);
      renderResolveResults(resolveKey, matches, item, playlistName, globalIdx);

      updateAbsentRowResolved(globalIdx, songTitle);
      showToast(`Resolved "${songTitle}" in playlist "${playlist.name}"!`, 'success');
      loadPlaylists();
      // If currently viewing this playlist in 3-column detail view, reload tracks & right panel
      if (selectedPlaylist && selectedPlaylist.id === playlist.id) {
        fetch(`/api/playlists/${playlist.id}/tracks`)
          .then(r => r.json())
          .then(tracks => {
            currentPlaylistTracks = tracks || [];
            renderPlaylistTracks();
            const badge = document.getElementById('selected-playlist-badge');
            const countText = document.getElementById('playlist-track-count-text');
            if (badge) badge.textContent = `${tracks.length} track${tracks.length !== 1 ? 's' : ''}`;
            if (countText) countText.textContent = `${tracks.length} song${tracks.length !== 1 ? 's' : ''}`;
          })
          .catch(e => console.error('Error reloading tracks:', e));
        filterPlaylistPageAbsentSongs();
      }
    } else {
      showToast(`Failed to resolve track: ${data.error || 'Unknown error'}`, 'error');
    }
  } catch (err) {
    console.error('Error resolving track:', err);
    showToast('Failed to connect to server.', 'error');
  }
}

function updateAbsentRowResolved(globalIdx, songTitle) {
  const row = document.getElementById(`absent-row-${globalIdx}`);
  if (!row) return;

  // Find and update the Resolve button cell to show ✓
  const resolveCell = row.querySelector('td:last-child');
  if (resolveCell) {
    resolveCell.innerHTML = `<span style="font-size: 0.72rem; color: var(--accent-green, #4ade80); font-weight: 700;">✓ Resolved</span>`;
  }

  // Strike-through the title cell
  const titleCell = row.querySelector('td:nth-child(2) div:first-child');
  if (titleCell) {
    titleCell.style.textDecoration = 'line-through';
    titleCell.style.color = 'var(--text-muted)';
  }
}

function downloadAbsentSongsReport() {
  if (!currentPowerampReport || !currentPowerampReport.absent_songs) {
    showToast('No absent songs report available to download.', 'info');
    return;
  }

  fetch('/api/poweramp/export-absent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ absent_songs: currentAbsentSongs })
  })
    .then(response => {
      if (!response.ok) throw new Error('Download request failed');
      return response.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'poweramp_absent_songs.txt';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      showToast('Absent songs report downloaded.', 'success');
    })
    .catch(err => {
      console.error('Error downloading report:', err);
      showToast('Error downloading report.', 'error');
    });
}
// =============================================================================
// APP BOOTSTRAP: DOMContentLoaded Initialization & Feature Coordination
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
  if (typeof initTheme === 'function') initTheme();
  
  const fpToggle = document.getElementById('toggle-use-fingerprints');
  if (fpToggle) {
    fpToggle.checked = useAudioFingerprinting;
  }
  
  if (typeof initTabs === 'function') initTabs();
  if (typeof initAudioPlayer === 'function') initAudioPlayer();
  if (typeof initPlayerTab === 'function') initPlayerTab();
  if (typeof loadDashboardStats === 'function') loadDashboardStats();
  if (typeof loadSongs === 'function') loadSongs();
  if (typeof loadDuplicates === 'function') loadDuplicates();
  if (typeof loadHiddenFiles === 'function') loadHiddenFiles();
  if (typeof loadSyncedHistory === 'function') loadSyncedHistory();
  if (typeof loadPlaylists === 'function') loadPlaylists();
  if (typeof loadLikedMusicSet === 'function') loadLikedMusicSet();
  if (typeof loadSyncDevices === 'function') loadSyncDevices();
  if (typeof loadDeletedSongs === 'function') loadDeletedSongs();
});
