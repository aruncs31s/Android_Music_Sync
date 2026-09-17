// Antigravity Web Dashboard JS with Playlists, Search, Pagination & SVG Icons

// SVG Icon Templates
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

// Theme Management System
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

// Global Search & Pagination State
let allSongs = [];
let filteredSongs = [];
let libPage = 1;
const libPageSize = 15;

let allClusters = [];
let filteredClusters = [];
let dupPage = 1;
const dupPageSize = 5;
let useAudioFingerprinting = localStorage.getItem('antigravity_use_audio_fingerprint') === 'true';

// Global Audio Player & Playlist State
let currentTrackPath = null;
let isPlaying = false;
let activeQueue = [];
let queueIndex = 0;

let allPlaylists = [];
let selectedPlaylist = null;
let currentPlaylistTracks = [];
let targetTrackForPlaylist = null;

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  const fpToggle = document.getElementById('toggle-use-fingerprints');
  if (fpToggle) {
    fpToggle.checked = useAudioFingerprinting;
  }
  initTabs();
  initAudioPlayer();
  loadDashboardStats();
  loadSongs();
  loadDuplicates();
  loadHiddenFiles();
  loadSyncedHistory();
  loadPlaylists();
  loadSyncDevices();
  loadDeletedSongs();
});

function initTabs() {
  const btns = document.querySelectorAll('.tab-btn');
  const sections = document.querySelectorAll('.tab-content');

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      sections.forEach(s => s.style.display = 'none');

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetSec = document.getElementById(targetId);
      if (targetSec) targetSec.style.display = 'block';
    });
  });
}

async function loadDashboardStats() {
  try {
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();

    document.getElementById('stat-total-songs').textContent = data.total_local_songs || 0;
    document.getElementById('stat-synced-count').textContent = data.synced_count || 0;
    document.getElementById('stat-hidden-count').textContent = data.hidden_count || 0;
    document.getElementById('stat-duplicates-count').textContent = data.duplicates_count || 0;

    renderDeviceBreakdown(data.device_counts || []);
  } catch (err) {
    console.error('Error fetching dashboard stats:', err);
  }
}

// Active Device State & Sorting State
let currentDeviceId = 'local';
let currentDeviceName = 'Local Music Folders';
let currentDeviceType = 'Local Storage';
let currentSortCriteria = 'ctime_desc';
let availableDevicesList = [];

function switchTab(tabId) {
  const btns = document.querySelectorAll('.tab-btn');
  const sections = document.querySelectorAll('.tab-content');
  btns.forEach(b => {
    if (b.getAttribute('data-tab') === tabId) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });
  sections.forEach(s => {
    s.style.display = (s.id === tabId) ? 'block' : 'none';
  });
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

function refreshCurrentDeviceLibrary() {
  loadDeviceSongs(currentDeviceId, true);
}

// --- MUSIC LIBRARY SEARCH, SORTING & PAGINATION ---

async function loadDeviceSongs(deviceId = 'local', forceRefresh = false) {
  currentDeviceId = deviceId;
  const tbody = document.getElementById('songs-tbody');
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-muted">Loading songs for device...</td></tr>';
  }

  try {
    const url = `/api/devices/${encodeURIComponent(deviceId)}/songs${forceRefresh ? '?refresh=true' : ''}`;
    const res = await fetch(url);
    const data = await res.json();

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
  } catch (err) {
    console.error('Error loading device songs:', err);
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-muted" style="color: var(--status-offline) !important;">Failed to load songs from device.</td></tr>';
    }
  }
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

function applyLibraryFilterAndSort() {
  const query = (document.getElementById('library-search')?.value || '').trim().toLowerCase();
  let list = allSongs;
  if (query) {
    list = allSongs.filter(s => {
      const text = `${s.title || ''} ${s.artist || ''} ${s.album || ''} ${s.filename || ''} ${s.filepath || ''}`.toLowerCase();
      return text.includes(query);
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

function renderLibraryPage() {
  const tbody = document.getElementById('songs-tbody');
  if (!tbody) return;

  if (!filteredSongs || filteredSongs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-muted">No songs matching search query.</td></tr>';
    updateLibraryPaginationInfo(0, 0, 0, 1);
    return;
  }

  const totalPages = Math.ceil(filteredSongs.length / libPageSize);
  const startIdx = (libPage - 1) * libPageSize;
  const pageSongs = filteredSongs.slice(startIdx, startIdx + libPageSize);

  const isLocalStorage = (currentDeviceId === 'local');

  let html = '';
  pageSongs.forEach((s, idx) => {
    const globalIdx = startIdx + idx + 1;
    const isThisTrackPlaying = (currentTrackPath === s.filepath && isPlaying);
    const playBtnIcon = isThisTrackPlaying ? SVG_PAUSE : SVG_PLAY;
    const playBtnText = isThisTrackPlaying ? 'Pause' : 'Play';
    const rowClass = isThisTrackPlaying ? 'class="playing-row"' : '';

    let actionButtons = '';
    if (isLocalStorage) {
      actionButtons = `
        <div class="action-btn-group">
          <button class="btn btn-secondary btn-sm" onclick="playOrToggleAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}')" title="${playBtnText}">${playBtnIcon} ${playBtnText}</button>
          <button class="btn btn-secondary btn-sm" onclick="openSyncSongModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}', '${escapeJs(s.duration_formatted || '')}', '${escapeJs(s.size_formatted || '')}', '${escapeJs(s.bitrate_kbps || '')}', '${escapeJs(s.album || '')}')" title="Sync to target device">${SVG_SYNC} Sync</button>
          <button class="btn btn-secondary btn-sm" onclick="showAddToPlaylistModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}')" title="Add to Playlist">${SVG_PLUS} Playlist</button>
          <button class="btn btn-secondary btn-sm" onclick="hideSong('${escapeJs(s.filepath)}')" title="Hide song">${SVG_HIDE}</button>
          <button class="btn btn-secondary btn-danger btn-sm" onclick="deleteSong('${escapeJs(s.filepath)}', event, '${escapeJs(currentDeviceId)}', '${escapeJs(s._id || '')}', '${escapeJs(s.filename || '')}')" title="Delete song">${SVG_TRASH}</button>
        </div>
      `;
    } else {
      actionButtons = `
        <div class="action-btn-group">
          <button class="btn btn-secondary btn-sm" onclick="showAddToPlaylistModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}')" title="Add to Playlist">${SVG_PLUS} Playlist</button>
          <button class="btn btn-secondary btn-sm" onclick="alert('File: ${escapeJs(s.filepath || s.filename)}')" title="View Details">Details</button>
          <button class="btn btn-secondary btn-danger btn-sm" onclick="deleteSong('${escapeJs(s.filepath)}', event, '${escapeJs(currentDeviceId)}', '${escapeJs(s._id || '')}', '${escapeJs(s.filename || '')}')" title="Delete song">${SVG_TRASH}</button>
        </div>
      `;
    }

    const clickToSyncAttr = isLocalStorage ? `style="cursor: pointer;" onclick="openSyncSongModal('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}', '${escapeJs(s.duration_formatted || '')}', '${escapeJs(s.size_formatted || '')}', '${escapeJs(s.bitrate_kbps || '')}', '${escapeJs(s.album || '')}')" title="Click to sync to device"` : '';

    html += `
      <tr ${rowClass}>
        <td class="col-center text-tabular">${globalIdx}</td>
        <td ${clickToSyncAttr}>
          <div class="track-meta-cell">
            <span class="track-title" title="${escapeHtml(s.title || 'Unknown')}">${escapeHtml(s.title || 'Unknown')}</span>
            <span class="track-subtitle" title="${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}">${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}</span>
          </div>
        </td>
        <td class="col-center text-tabular">${escapeHtml(s.duration_formatted || '00:00')}</td>
        <td class="col-center text-tabular">${escapeHtml(s.size_formatted || '—')}</td>
        <td class="col-center"><span class="badge badge-purple text-tabular">${escapeHtml(s.bitrate_kbps || 'Unknown')}</span></td>
        <td class="col-center text-tabular"><small class="text-muted">${escapeHtml(s.ctime_str || '—')}</small></td>
        <td class="col-center text-tabular"><small class="text-muted">${escapeHtml(s.mtime_str || '—')}</small></td>
        <td class="col-right">${actionButtons}</td>
      </tr>
    `;
  });
  tbody.innerHTML = html;

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
    container.innerHTML = `<p class="text-muted" style="display: flex; align-items: center; gap: 0.5rem; padding: 1rem 0;">${SVG_SPARKLES} Analyzing duplicates with ${useAudioFingerprinting ? 'acoustic audio fingerprinting' : 'tag & filename matching'}...</p>`;
  }
  loadDuplicates(true);
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
        alert("Safety Limit: At least one copy in this cluster must be kept so the song is not lost from your library.");
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

function renderDuplicatesPage() {
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
      alert(`Successfully deleted ${data.deleted_count} duplicate files!\nExactly 1 copy in each cluster has been preserved.`);
      selectedDuplicatePaths.clear();
      updateDuplicatesSelectionUI();
      loadDuplicates();
      loadSongs();
      loadDashboardStats();
    } else {
      alert(`Error deleting duplicate files: ${data.error || data.message || 'Batch delete failed'}`);
    }
  } catch (err) {
    console.error('Error executing batch duplicate deletion:', err);
    alert('Connection error while batch deleting duplicate files.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Confirm & Delete Selected Files';
    }
  }
}

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
  if (checkedBoxes.length === 0) return;

  const serial = document.getElementById('sync-device-select')?.value || '';
  const remoteDir = document.getElementById('sync-remote-dir')?.value || '';
  const statusEl = document.getElementById('sync-status');

  if (!serial) return;

  const files = checkedBoxes.map(cb => cb.dataset.path);
  if (!confirm(`Push ${files.length} file(s) to device ${serial}?\n\nRemote folder:\n${remoteDir}`)) return;

  if (statusEl) statusEl.textContent = `Pushing ${files.length} file(s) to ${serial}...`;

  const pushBtn = document.getElementById('btn-push-sync');
  if (pushBtn) pushBtn.disabled = true;

  try {
    const res = await fetch('/api/sync/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ serial: serial, remote_dir: remoteDir, files: files })
    });
    const data = await res.json();
    if (data.status !== 'success') {
      if (statusEl) statusEl.textContent = `Error: ${data.error || 'Failed to run sync'}`;
      return;
    }

    if (statusEl) statusEl.textContent = `Sync complete: ${data.pushed}/${data.total} files pushed to ${serial}.`;

    const failures = (data.results || []).filter(r => !r.success);
    if (failures.length > 0) {
      const names = failures.slice(0, 5).map(f => f.filepath.split('/').pop()).join(', ');
      console.warn('Sync failures:', failures);
      if (statusEl) statusEl.textContent += ` ${failures.length} failed (${names}${failures.length > 5 ? ', ...' : ''}). Check server logs.`;
    }

    loadSyncedHistory();
    loadDashboardStats();
    loadSyncDevices(false);
    runSyncPreview();
  } catch (err) {
    console.error('Error pushing sync files:', err);
    if (statusEl) statusEl.textContent = 'Error pushing files. See server logs.';
  } finally {
    if (pushBtn) pushBtn.disabled = false;
  }
}

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
  if (!confirm(`Are you sure you want to permanently delete '${songName}' from ${devLabel}?\n\nRemote/Local Path:\n${filepath}`)) {
    return;
  }

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

      // Update in-memory lists if viewing this device
      if (allSongs && allSongs.length > 0) {
        allSongs = allSongs.filter(s => s.filepath !== filepath);
        filteredSongs = filteredSongs.filter(s => s.filepath !== filepath);
        // If we filtered or searched, update pagination counter
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
        // Force-refresh device query so that Android MediaStore count updates
        loadDeviceSongs(targetDevice, true);
      }
      loadDashboardStats();
    } else {
      if (targetEl) {
        targetEl.style.opacity = '1';
        targetEl.style.filter = 'none';
      }
      alert(`Error deleting file: ${data.error || data.message || 'Failed to delete file'}`);
    }
  } catch (err) {
    console.error('Error deleting song:', err);
    if (targetEl) {
      targetEl.style.opacity = '1';
      targetEl.style.filter = 'none';
    }
    alert('Error connecting to server to delete file.');
  }
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

function initAudioPlayer() {
  const player = document.getElementById('audio-player');
  if (!player) return;

  player.onplay = () => setPlayerPlayState(true);
  player.onpause = () => setPlayerPlayState(false);
  player.onended = () => handleTrackEnded();
}

function setPlayerPlayState(playing) {
  isPlaying = playing;
  const playPauseBtn = document.getElementById('btn-player-playpause');
  if (playPauseBtn) {
    playPauseBtn.innerHTML = isPlaying ? SVG_PAUSE : SVG_PLAY;
    playPauseBtn.title = isPlaying ? 'Pause' : 'Play';
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
    player.play();
  } else {
    player.pause();
  }
}

function playOrToggleAudio(filepath, title, artist) {
  const player = document.getElementById('audio-player');
  if (currentTrackPath === filepath && player && player.src) {
    togglePlayPause();
  } else {
    playAudio(filepath, title, artist);
  }
}

function playAudio(filepath, title, artist, queue = null, index = 0) {
  const player = document.getElementById('audio-player');
  const playerBar = document.getElementById('audio-player-bar');
  const titleEl = document.getElementById('player-title');
  const artistEl = document.getElementById('player-artist');

  if (player && playerBar) {
    currentTrackPath = filepath;
    if (queue && queue.length > 0) {
      activeQueue = queue;
      queueIndex = index;
    } else {
      activeQueue = [{ filepath, title, artist }];
      queueIndex = 0;
    }

    player.src = `/api/song/stream?filepath=${encodeURIComponent(filepath)}`;
    if (titleEl) titleEl.textContent = title || 'Unknown Title';
    if (artistEl) artistEl.textContent = artist || 'Unknown Artist';
    playerBar.style.display = 'flex';
    player.play();
  }
}

function handleTrackEnded() {
  if (activeQueue && queueIndex + 1 < activeQueue.length) {
    queueIndex++;
    const nextTrack = activeQueue[queueIndex];
    playAudio(nextTrack.filepath, nextTrack.title, nextTrack.artist, activeQueue, queueIndex);
  } else {
    setPlayerPlayState(false);
  }
}

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

  let html = '';
  allPlaylists.forEach(p => {
    const isActive = selectedPlaylist && selectedPlaylist.id === p.id ? 'active' : '';
    html += `
      <div class="playlist-card ${isActive}" onclick="selectPlaylist(${p.id}, '${escapeJs(p.name)}')">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <h4 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: var(--text-main);">${escapeHtml(p.name)}</h4>
          <span style="font-size: 1.25rem;">${SVG_LIST}</span>
        </div>
        <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;" class="text-muted">
          <small>${p.track_count || 0} tracks</small>
          <small>${p.created_at ? p.created_at.substring(0, 10) : ''}</small>
        </div>
      </div>
    `;
  });
  grid.innerHTML = html;
}

function showCreatePlaylistModal() {
  const modal = document.getElementById('modal-create-playlist');
  const input = document.getElementById('input-playlist-name');
  if (modal) {
    if (input) input.value = '';
    modal.style.display = 'flex';
  }
}

function hideCreatePlaylistModal() {
  const modal = document.getElementById('modal-create-playlist');
  if (modal) modal.style.display = 'none';
}

async function submitCreatePlaylist() {
  const input = document.getElementById('input-playlist-name');
  const name = input ? input.value.trim() : '';

  if (!name) {
    alert('Please enter a playlist name!');
    return;
  }

  try {
    const res = await fetch('/api/playlists/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    const data = await res.json();
    if (data.status === 'success') {
      hideCreatePlaylistModal();
      await loadPlaylists();
      if (data.playlist) {
        selectPlaylist(data.playlist.id, data.playlist.name);
      }
    } else {
      alert(`Error creating playlist: ${data.error || 'Failed to create'}`);
    }
  } catch (err) {
    console.error('Error creating playlist:', err);
    alert('Error connecting to server.');
  }
}

async function selectPlaylist(playlistId, playlistName) {
  selectedPlaylist = { id: playlistId, name: playlistName };
  renderPlaylistsGrid();

  const detailsPanel = document.getElementById('playlist-details-panel');
  const nameTitle = document.getElementById('selected-playlist-name');

  if (nameTitle) nameTitle.textContent = playlistName;
  if (detailsPanel) detailsPanel.style.display = 'block';

  const tbody = document.getElementById('playlist-tracks-tbody');
  if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-muted">Loading playlist tracks...</td></tr>';

  try {
    const res = await fetch(`/api/playlists/${playlistId}/tracks`);
    currentPlaylistTracks = await res.json() || [];
    renderPlaylistTracks();
  } catch (err) {
    console.error('Error fetching playlist tracks:', err);
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-muted">Error loading playlist tracks.</td></tr>';
  }
}

function renderPlaylistTracks() {
  const tbody = document.getElementById('playlist-tracks-tbody');
  if (!tbody) return;

  if (!currentPlaylistTracks || currentPlaylistTracks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No tracks in this playlist yet. Add songs from the Music Library tab!</td></tr>';
    return;
  }

  let html = '';
  currentPlaylistTracks.forEach((s, idx) => {
    const isThisTrackPlaying = (currentTrackPath === s.filepath && isPlaying);
    const playBtnIcon = isThisTrackPlaying ? SVG_PAUSE : SVG_PLAY;
    const playBtnText = isThisTrackPlaying ? 'Pause' : 'Play';
    const rowClass = isThisTrackPlaying ? 'class="playing-row"' : '';

    html += `
      <tr ${rowClass}>
        <td class="col-center text-tabular">${idx + 1}</td>
        <td>
          <div class="track-meta-cell">
            <span class="track-title" title="${escapeHtml(s.title || s.filename)}">${escapeHtml(s.title || s.filename)}</span>
            <span class="track-subtitle" title="${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}">${escapeHtml(s.artist || 'Unknown')} • ${escapeHtml(s.album || 'Unknown')}</span>
          </div>
        </td>
        <td class="col-center text-tabular">${escapeHtml(s.duration_formatted || '00:00')}</td>
        <td class="col-center text-tabular">${escapeHtml(s.size_formatted || '—')}</td>
        <td class="col-right">
          <div class="action-btn-group">
            <button class="btn btn-secondary btn-sm" onclick="playPlaylistFromTrack(${idx})" title="${playBtnText}">${playBtnIcon} ${playBtnText}</button>
            <button class="btn btn-secondary btn-danger btn-sm" onclick="removeTrackFromPlaylist(${selectedPlaylist.id}, '${escapeJs(s.filepath)}')" title="Remove from playlist">${SVG_TRASH} Remove</button>
          </div>
        </td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

async function deleteCurrentPlaylist() {
  if (!selectedPlaylist) return;
  if (!confirm(`Are you sure you want to delete the playlist "${selectedPlaylist.name}"?`)) return;

  try {
    const res = await fetch('/api/playlists/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playlist_id: selectedPlaylist.id })
    });
    const data = await res.json();
    if (data.status === 'success') {
      selectedPlaylist = null;
      currentPlaylistTracks = [];
      const detailsPanel = document.getElementById('playlist-details-panel');
      if (detailsPanel) detailsPanel.style.display = 'none';
      loadPlaylists();
    } else {
      alert(`Error deleting playlist: ${data.error || 'Failed to delete'}`);
    }
  } catch (err) {
    console.error('Error deleting playlist:', err);
    alert('Error connecting to server.');
  }
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
    alert('Please select a playlist!');
    return;
  }

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
    } else {
      alert(`Error adding track: ${data.error || 'Failed to add track'}`);
    }
  } catch (err) {
    console.error('Error adding track to playlist:', err);
    alert('Error connecting to server.');
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
    } else {
      alert(`Error removing track: ${data.error || 'Failed to remove'}`);
    }
  } catch (err) {
    console.error('Error removing track from playlist:', err);
    alert('Error connecting to server.');
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
  if (!confirm(`Restore this deleted song to its original location?`)) return;

  try {
    const res = await fetch('/api/deleted/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: recordId })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert(`Restored ${data.message || 'song'}`);
      loadDeletedSongs();
      loadSongs();
      loadDuplicates();
      loadDashboardStats();
    } else {
      alert(`Error restoring song: ${data.error || data.message || 'Failed to restore'}`);
      loadDeletedSongs();
    }
  } catch (err) {
    console.error('Error restoring deleted song:', err);
    alert('Error connecting to server.');
  }
}

async function clearDeletedHistory() {
  if (!confirm('Empty the trash?\n\nThis PERMANENTLY deletes all files kept in tmp/deleted/ and clears the history. This cannot be undone.')) return;

  try {
    const res = await fetch('/api/deleted/clear', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      alert(data.message || 'Trash emptied.');
      loadDeletedSongs();
    } else {
      alert(`Error emptying trash: ${data.error || data.message || 'Failed to clear history'}`);
    }
  } catch (err) {
    console.error('Error clearing deleted songs history:', err);
    alert('Error connecting to server.');
  }
}

function escapeHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJs(str) {
  return String(str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
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
    alert('Please select a valid destination device.');
    return;
  }

  const deviceId = selectEl.value;
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


