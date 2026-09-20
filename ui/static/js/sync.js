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

