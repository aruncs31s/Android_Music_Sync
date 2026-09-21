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

// Filter state for Connected Devices table
var currentDeviceCategoryFilter = 'all'; // 'all' | 'adb' | 'overip' | 'local'
var deviceOnlineOnlyFilter = false;
var deviceSearchQuery = '';

function getDeviceCategory(d) {
  if (!d) return 'other';
  const id = (d.id || '').toLowerCase();
  const type = (d.type || '').toLowerCase();
  if (id === 'local' || type.includes('local') || type.includes('storage')) {
    return 'local';
  }
  if (id.startsWith('adb') || type.includes('adb')) {
    return 'adb';
  }
  if (id.startsWith('ip') || id.startsWith('http') || type.includes('over-ip') || type.includes('http') || type.includes('peer')) {
    return 'overip';
  }
  return 'other';
}

function updateDeviceFilterCounts(devices) {
  const list = devices || [];
  const total = list.length;
  const adbCount = list.filter(d => getDeviceCategory(d) === 'adb').length;
  const overipCount = list.filter(d => getDeviceCategory(d) === 'overip').length;
  const localCount = list.filter(d => getDeviceCategory(d) === 'local').length;

  const elAll = document.getElementById('count-dev-all');
  const elAdb = document.getElementById('count-dev-adb');
  const elOverip = document.getElementById('count-dev-overip');
  const elLocal = document.getElementById('count-dev-local');

  if (elAll) elAll.textContent = total;
  if (elAdb) elAdb.textContent = adbCount;
  if (elOverip) elOverip.textContent = overipCount;
  if (elLocal) elLocal.textContent = localCount;
}

function filterDevices(devices) {
  if (!devices || !Array.isArray(devices)) return [];
  return devices.filter(d => {
    // 1. Category Filter
    if (currentDeviceCategoryFilter !== 'all') {
      if (getDeviceCategory(d) !== currentDeviceCategoryFilter) return false;
    }
    // 2. Online Only Filter
    if (deviceOnlineOnlyFilter) {
      const isOnline = d.status === 'online' || d.status === 'active';
      if (!isOnline) return false;
    }
    // 3. Search Query Filter
    if (deviceSearchQuery) {
      const q = deviceSearchQuery.toLowerCase();
      const name = (d.name || '').toLowerCase();
      const details = (d.details || '').toLowerCase();
      const serial = (d.serial || '').toLowerCase();
      const ip = (d.ip || '').toLowerCase();
      const type = (d.type || '').toLowerCase();
      const matches = name.includes(q) || details.includes(q) || serial.includes(q) || ip.includes(q) || type.includes(q);
      if (!matches) return false;
    }
    return true;
  });
}

function setDeviceCategoryFilter(category, btnEl) {
  currentDeviceCategoryFilter = category;

  document.querySelectorAll('.device-filter-chips .filter-chip[id^="chip-filter-dev-"]').forEach(chip => {
    if (chip.id !== 'chip-filter-dev-online') {
      chip.classList.remove('active');
    }
  });

  if (btnEl) {
    btnEl.classList.add('active');
  } else {
    const targetChip = document.getElementById(`chip-filter-dev-${category}`);
    if (targetChip) targetChip.classList.add('active');
  }

  renderDeviceListTable();
}

function toggleDeviceOnlineFilter(btnEl) {
  deviceOnlineOnlyFilter = !deviceOnlineOnlyFilter;
  if (btnEl) {
    btnEl.classList.toggle('active', deviceOnlineOnlyFilter);
  }
  renderDeviceListTable();
}

function onDeviceSearchInput(val) {
  deviceSearchQuery = (val || '').trim();
  const clearBtn = document.getElementById('device-search-clear');
  if (clearBtn) {
    clearBtn.style.display = deviceSearchQuery ? 'block' : 'none';
  }
  renderDeviceListTable();
}

function clearDeviceSearch() {
  const input = document.getElementById('device-search-query');
  if (input) input.value = '';
  deviceSearchQuery = '';
  const clearBtn = document.getElementById('device-search-clear');
  if (clearBtn) clearBtn.style.display = 'none';
  renderDeviceListTable();
}

function resetDeviceFilters() {
  currentDeviceCategoryFilter = 'all';
  deviceOnlineOnlyFilter = false;
  deviceSearchQuery = '';

  const input = document.getElementById('device-search-query');
  if (input) input.value = '';
  const clearBtn = document.getElementById('device-search-clear');
  if (clearBtn) clearBtn.style.display = 'none';

  const onlineChip = document.getElementById('chip-filter-dev-online');
  if (onlineChip) onlineChip.classList.remove('active');

  document.querySelectorAll('.device-filter-chips .filter-chip[id^="chip-filter-dev-"]').forEach(chip => {
    if (chip.id === 'chip-filter-dev-all') {
      chip.classList.add('active');
    } else if (chip.id !== 'chip-filter-dev-online') {
      chip.classList.remove('active');
    }
  });

  renderDeviceListTable();
}

function renderDeviceBreakdown(devices) {
  availableDevicesList = devices || [];
  updateLibraryDeviceSelectOptions();
  updateDeviceFilterCounts(availableDevicesList);
  renderDeviceListTable();
}

function renderDeviceListTable() {
  const container = document.getElementById('device-list');
  const fullContainer = document.getElementById('devices-full-list');

  if (!availableDevicesList || availableDevicesList.length === 0) {
    const emptyHtml = '<p class="text-muted">No devices connected.</p>';
    if (container) container.innerHTML = emptyHtml;
    if (fullContainer) fullContainer.innerHTML = emptyHtml;
    return;
  }

  const filteredDevices = filterDevices(availableDevicesList);

  if (filteredDevices.length === 0) {
    const catLabels = { adb: 'ADB Devices', overip: 'Over-IP Peers', local: 'Local Storage' };
    const activeFilters = [];
    if (currentDeviceCategoryFilter !== 'all') {
      activeFilters.push(catLabels[currentDeviceCategoryFilter] || currentDeviceCategoryFilter);
    }
    if (deviceOnlineOnlyFilter) activeFilters.push('Online Only');
    if (deviceSearchQuery) activeFilters.push(`"${deviceSearchQuery}"`);

    const noMatchHtml = `
      <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
        <p style="font-size: 0.95rem; margin-bottom: 0.85rem; color: var(--text-main);">
          No devices found matching: <strong style="color: var(--accent-yellow);">${escapeHtml(activeFilters.join(' + ') || 'criteria')}</strong>
        </p>
        <button class="btn btn-secondary btn-sm" onclick="resetDeviceFilters()">Reset Filters</button>
      </div>
    `;
    if (container) container.innerHTML = noMatchHtml;
    if (fullContainer) fullContainer.innerHTML = noMatchHtml;
    return;
  }

  let html = `
    <table>
      <thead>
        <tr>
          <th style="min-width: 220px;">Device / Source</th>
          <th style="width: 140px;">Type</th>
          <th style="width: 140px;" class="col-center">Song Count</th>
          <th style="width: 120px;" class="col-center">Status</th>
          <th style="width: 150px;" class="col-right">Action</th>
        </tr>
      </thead>
      <tbody>
  `;

  filteredDevices.forEach(d => {
    const isOnline = d.status === 'online' || d.status === 'active';
    const statusBadge = isOnline 
      ? '<span class="badge badge-online">ONLINE</span>' 
      : '<span class="badge badge-offline">OFFLINE</span>';
    
    // Distinguish badge color by device category
    const cat = getDeviceCategory(d);
    let typeBadgeClass = 'badge-purple';
    if (cat === 'local') typeBadgeClass = 'badge-yellow';
    else if (cat === 'adb') typeBadgeClass = 'badge-blue';
    else if (cat === 'overip') typeBadgeClass = 'badge-purple';
    
    html += `
      <tr onclick="openDeviceLibrary('${escapeJs(d.id)}', '${escapeJs(d.name)}')" style="cursor: pointer;" title="Click to open ${escapeHtml(d.name)} Song Library">
        <td>
          <strong style="color: var(--accent-orange); font-size: 0.92rem;">${escapeHtml(d.name)}</strong>
          <br><small class="text-muted">${escapeHtml(d.details || d.serial || '')}</small>
        </td>
        <td><span class="badge ${typeBadgeClass}">${escapeHtml(d.type)}</span></td>
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

  const localDevs = availableDevicesList.filter(d => getDeviceCategory(d) === 'local');
  const adbDevs = availableDevicesList.filter(d => getDeviceCategory(d) === 'adb');
  const ipDevs = availableDevicesList.filter(d => getDeviceCategory(d) === 'overip');
  const otherDevs = availableDevicesList.filter(d => getDeviceCategory(d) === 'other');

  let optionsHtml = '';

  if (localDevs.length > 0) {
    optionsHtml += `<optgroup label="Local Storage">`;
    localDevs.forEach(d => {
      optionsHtml += `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${d.count} songs)</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  if (adbDevs.length > 0) {
    optionsHtml += `<optgroup label="ADB Devices">`;
    adbDevs.forEach(d => {
      optionsHtml += `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${d.count} songs)</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  if (ipDevs.length > 0) {
    optionsHtml += `<optgroup label="Over-IP Peers">`;
    ipDevs.forEach(d => {
      optionsHtml += `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${d.count} songs)</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  if (otherDevs.length > 0) {
    optionsHtml += `<optgroup label="Other Devices">`;
    otherDevs.forEach(d => {
      optionsHtml += `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${d.count} songs)</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  sel.innerHTML = optionsHtml;
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

