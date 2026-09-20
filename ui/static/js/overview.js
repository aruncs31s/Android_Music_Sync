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

