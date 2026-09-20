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

