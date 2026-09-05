// Antigravity Web Dashboard JS
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

async function loadSongs() {
  const tbody = document.getElementById('songs-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/songs');
    const songs = await res.json();

    if (!songs || songs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted">No songs found in local music library.</td></tr>';
      return;
    }

    let html = '';
    songs.forEach((s, idx) => {
      html += `
        <tr>
          <td>${idx + 1}</td>
          <td>
            <strong>${escapeHtml(s.title || 'Unknown')}</strong>
            <br><small class="text-muted">${escapeHtml(s.artist || 'Unknown')} | ${escapeHtml(s.album || 'Unknown')}</small>
          </td>
          <td>${escapeHtml(s.duration_formatted || '00:00')}</td>
          <td>${escapeHtml(s.size_formatted || '')}</td>
          <td><span class="badge badge-purple">${escapeHtml(s.bitrate_kbps || '')}</span></td>
          <td>
            <button class="btn btn-secondary" onclick="playAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}')">▶ Play</button>
            <button class="btn btn-secondary" onclick="hideSong('${escapeJs(s.filepath)}')">🙈 Hide</button>
            <button class="btn btn-secondary" style="background: rgba(244, 63, 94, 0.2); color: #f87171; border-color: rgba(244, 63, 94, 0.3);" onclick="deleteSong('${escapeJs(s.filepath)}')">🗑️ Delete</button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    console.error('Error loading songs:', err);
  }
}

async function loadDuplicates() {
  const container = document.getElementById('duplicates-container');
  if (!container) return;

  try {
    const res = await fetch('/api/duplicates');
    const data = await res.json();

    if (!data.clusters || data.clusters.length === 0) {
      container.innerHTML = '<p style="color: #34d399; font-weight: 600;">✨ No duplicate songs detected in library!</p>';
      return;
    }

    let html = '';
    data.clusters.forEach((c, idx) => {
      html += `
        <div style="background: rgba(15,23,42,0.5); padding: 1rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid var(--border-color);">
          <h4 style="color: #f43f5e; margin-bottom: 0.75rem;">Cluster #${idx + 1}: ${escapeHtml(c.cluster_name)} (${c.count} copies)</h4>
          <ul style="list-style: none; padding-left: 0.25rem;">
      `;
      c.songs.forEach(s => {
        html += `
          <li style="margin-bottom: 0.6rem; font-size: 0.85rem; display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.4); padding: 0.5rem 0.75rem; border-radius: 8px;">
            <div>
              📁 <code style="color: #cbd5e1;">${escapeHtml(s.filepath)}</code> 
              <span class="text-muted" style="margin-left: 0.5rem;">(${s.size_formatted}, ${s.mtime_str})</span>
            </div>
            <div style="display: flex; gap: 0.35rem;">
              <button class="btn btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="playAudio('${escapeJs(s.filepath)}', '${escapeJs(s.title)}', '${escapeJs(s.artist)}')">▶ Play</button>
              <button class="btn btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.75rem; background: rgba(244, 63, 94, 0.25); color: #f87171; border-color: rgba(244, 63, 94, 0.4);" onclick="deleteSong('${escapeJs(s.filepath)}')">🗑️ Delete</button>
            </div>
          </li>
        `;
      });
      html += '</ul></div>';
    });
    container.innerHTML = html;
  } catch (err) {
    console.error('Error loading duplicates:', err);
  }
}

async function deleteSong(filepath) {
  if (!confirm(`Are you sure you want to permanently delete this audio file?\n\nFilepath:\n${filepath}`)) {
    return;
  }

  try {
    const res = await fetch('/api/song/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath: filepath })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert(`Deleted: ${data.message || filepath}`);
      loadDuplicates();
      loadSongs();
      loadDashboardStats();
    } else {
      alert(`Error deleting file: ${data.error || 'Failed to delete file'}`);
    }
  } catch (err) {
    console.error('Error deleting song:', err);
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
      tbody.innerHTML = '<tr><td colspan="4" class="text-muted">No hidden files in SQLite database (ui/db.db).</td></tr>';
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
            <button class="btn btn-secondary" onclick="unhideSong('${escapeJs(r.filepath)}')">👁️ Unhide</button>
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
      tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No synced track history recorded in ui/db.db.</td></tr>';
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
