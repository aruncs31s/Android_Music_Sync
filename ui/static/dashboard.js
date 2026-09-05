// Antigravity Web Dashboard JS with Search, Pagination & SVG Icons

// SVG Icon Templates
const SVG_PLAY = `<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
const SVG_HIDE = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
const SVG_UNHIDE = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
const SVG_TRASH = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`;
const SVG_FOLDER = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`;
const SVG_SPARKLES = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`;

// Global Search & Pagination State
let allSongs = [];
let filteredSongs = [];
let libPage = 1;
const libPageSize = 15;

let allClusters = [];
let filteredClusters = [];
let dupPage = 1;
const dupPageSize = 5;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadDashboardStats();
  loadSongs();
  loadDuplicates();
  loadHiddenFiles();
  loadSyncedHistory();
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

function renderDeviceBreakdown(devices) {
  const container = document.getElementById('device-list');
  const fullContainer = document.getElementById('devices-full-list');

  if (!devices || devices.length === 0) {
    if (container) container.innerHTML = '<p class="text-muted">No devices connected.</p>';
    if (fullContainer) fullContainer.innerHTML = '<p class="text-muted">No available devices.</p>';
    return;
  }

  let html = '<table><thead><tr><th>Device / Source</th><th>Type</th><th>Song Count</th><th>Status</th></tr></thead><tbody>';
  devices.forEach(d => {
    const statusBadge = d.status === 'online' || d.status === 'active' 
      ? '<span class="badge badge-online">ONLINE</span>' 
      : '<span class="badge badge-offline">OFFLINE</span>';
    html += `
      <tr>
        <td><strong>${escapeHtml(d.name)}</strong><br><small class="text-muted">${escapeHtml(d.details || d.serial || '')}</small></td>
        <td>${escapeHtml(d.type)}</td>
        <td><strong>${d.count}</strong> songs</td>
        <td>${statusBadge}</td>
      </tr>
    `;
  });
  html += '</tbody></table>';

  if (container) container.innerHTML = html;
  if (fullContainer) fullContainer.innerHTML = html;
}

// --- MUSIC LIBRARY SEARCH & PAGINATION ---

async function loadSongs() {
  const tbody = document.getElementById('songs-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/songs');
    allSongs = await res.json() || [];
    filteredSongs = [...allSongs];
    libPage = 1;
    renderLibraryPage();
  } catch (err) {
    console.error('Error loading songs:', err);
  }
}

function onLibrarySearchInput() {
  const query = (document.getElementById('library-search')?.value || '').trim().toLowerCase();
  if (!query) {
    filteredSongs = [...allSongs];
  } else {
    filteredSongs = allSongs.filter(s => {
      const text = `${s.title || ''} ${s.artist || ''} ${s.album || ''} ${s.filename || ''} ${s.filepath || ''}`.toLowerCase();
      return text.includes(query);
    });
  }
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
    tbody.innerHTML = '<tr><td colspan="6" class="text-muted">No songs matching search query.</td></tr>';
    updateLibraryPaginationInfo(0, 0, 0, 1);
    return;
  }

  const totalPages = Math.ceil(filteredSongs.length / libPageSize);
  const startIdx = (libPage - 1) * libPageSize;
  const pageSongs = filteredSongs.slice(startIdx, startIdx + libPageSize);

  let html = '';
  pageSongs.forEach((s, idx) => {
    const globalIdx = startIdx + idx + 1;
    html += `
      <tr>
        <td>${globalIdx}</td>
        <td>
          <strong>${escapeHtml(s.title || 'Unknown')}</strong>
          <br><small class="text-muted">${escapeHtml(s.artist || 'Unknown')} | ${escapeHtml(s.album || 'Unknown')}</small>
        </td>
        <td>${escapeHtml(s.duration_formatted || '00:00')}</td>
        <td>${escapeHtml(s.size_formatted || '')}</td>
        <td><span class="badge badge-purple">${escapeHtml(s.bitrate_kbps || '')}</span></td>
        <td>
          <button class="btn btn-secondary" onclick="playAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}')">${SVG_PLAY} Play</button>
          <button class="btn btn-secondary" onclick="hideSong('${escapeJs(s.filepath)}')">${SVG_HIDE} Hide</button>
          <button class="btn btn-secondary" style="background: rgba(244, 63, 94, 0.2); color: #f87171; border-color: rgba(244, 63, 94, 0.3);" onclick="deleteSong('${escapeJs(s.filepath)}', event)">${SVG_TRASH} Delete</button>
        </td>
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

// --- DUPLICATES SEARCH & PAGINATION ---

async function loadDuplicates() {
  const container = document.getElementById('duplicates-container');
  if (!container) return;

  try {
    const res = await fetch('/api/duplicates');
    const data = await res.json();
    allClusters = data.clusters || [];
    filteredClusters = [...allClusters];
    dupPage = 1;
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

function changeDuplicatesPage(delta) {
  const totalPages = Math.ceil(filteredClusters.length / dupPageSize) || 1;
  dupPage = Math.max(1, Math.min(totalPages, dupPage + delta));
  renderDuplicatesPage();
}

function renderDuplicatesPage() {
  const container = document.getElementById('duplicates-container');
  if (!container) return;

  if (!filteredClusters || filteredClusters.length === 0) {
    container.innerHTML = `<p style="color: #34d399; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;">${SVG_SPARKLES} No duplicate clusters found matching query!</p>`;
    updateDuplicatesPaginationInfo(0, 0, 0, 1);
    return;
  }

  const totalPages = Math.ceil(filteredClusters.length / dupPageSize);
  const startIdx = (dupPage - 1) * dupPageSize;
  const pageClusters = filteredClusters.slice(startIdx, startIdx + dupPageSize);

  let html = '';
  pageClusters.forEach((c, idx) => {
    const globalIdx = startIdx + idx + 1;
    html += `
      <div style="background: rgba(15,23,42,0.5); padding: 1.25rem; border-radius: 14px; margin-bottom: 1rem; border: 1px solid var(--border-color);">
        <h4 style="color: #f43f5e; margin-bottom: 0.75rem; font-size: 1rem;">Cluster #${globalIdx}: ${escapeHtml(c.cluster_name)} (${c.count} copies)</h4>
        <ul style="list-style: none; padding-left: 0.25rem;">
    `;
    c.songs.forEach(s => {
      html += `
        <li style="margin-bottom: 0.6rem; font-size: 0.85rem; display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.4); padding: 0.6rem 0.85rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
          <div>
            ${SVG_FOLDER} <code style="color: #cbd5e1;">${escapeHtml(s.filepath)}</code> 
            <span class="text-muted" style="margin-left: 0.5rem;">(${s.size_formatted}, ${s.mtime_str})</span>
          </div>
          <div style="display: flex; gap: 0.4rem;">
            <button class="btn btn-secondary" style="padding: 0.3rem 0.75rem; font-size: 0.75rem;" onclick="playAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}')">${SVG_PLAY} Play</button>
            <button class="btn btn-secondary" style="padding: 0.3rem 0.75rem; font-size: 0.75rem; background: rgba(244, 63, 94, 0.25); color: #f87171; border-color: rgba(244, 63, 94, 0.4);" onclick="deleteSong('${escapeJs(s.filepath)}', event)">${SVG_TRASH} Delete</button>
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

// --- FILE DELETION, HIDING & OTHER UTILITIES ---

async function deleteSong(filepath, evt) {
  if (!confirm(`Are you sure you want to permanently delete this audio file?\n\nFilepath:\n${filepath}`)) {
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
      body: JSON.stringify({ filepath: filepath })
    });
    const data = await res.json();
    if (data.status === 'success') {
      if (targetEl) targetEl.remove();
      loadDuplicates();
      loadSongs();
      loadDashboardStats();
    } else {
      if (targetEl) {
        targetEl.style.opacity = '1';
        targetEl.style.filter = 'none';
      }
      alert(`Error deleting file: ${data.error || 'Failed to delete file'}`);
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
          <td>${idx + 1}</td>
          <td><strong>${escapeHtml(r.filename)}</strong></td>
          <td><small class="text-muted"><code>${escapeHtml(r.filepath)}</code></small></td>
          <td>
            <button class="btn btn-secondary" onclick="unhideSong('${escapeJs(r.filepath)}')">${SVG_UNHIDE} Unhide</button>
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
          <td>${idx + 1}</td>
          <td><strong>${escapeHtml(r.filename)}</strong></td>
          <td><span class="badge badge-purple">${escapeHtml(r.device_serial)}</span></td>
          <td><small class="text-muted">${escapeHtml(r.remote_dir || 'N/A')}</small></td>
          <td>${escapeHtml(r.synced_at || '')}</td>
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

function playAudio(filepath, title, artist) {
  const player = document.getElementById('audio-player');
  const playerBar = document.getElementById('audio-player-bar');
  const titleEl = document.getElementById('player-title');
  const artistEl = document.getElementById('player-artist');

  if (player && playerBar) {
    player.src = `/api/song/stream?filepath=${encodeURIComponent(filepath)}`;
    if (titleEl) titleEl.textContent = title || 'Unknown Title';
    if (artistEl) artistEl.textContent = artist || 'Unknown Artist';
    playerBar.style.display = 'flex';
    player.play();
  }
}

function escapeHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJs(str) {
  return String(str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}
