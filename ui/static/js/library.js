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

  const tbody = document.getElementById('songs-tbody');
  if (tbody) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-muted" style="text-align:center;padding:2rem;">Loading library from ${escapeHtml(currentDeviceName || deviceId)}…</td></tr>`;
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
