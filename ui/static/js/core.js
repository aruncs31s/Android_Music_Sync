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
