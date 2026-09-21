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
    const icon = isLikedMusic
      ? `<span style="color:#ff0055;display:inline-flex;">${SVG_HEART_FILLED}</span>`
      : `<span style="display:inline-flex;">${SVG_LIST}</span>`;

    html += `
      <div onclick="selectPlaylist(${p.id}, '${escapeJs(p.name)}')"
           style="display: flex; align-items: center; justify-content: space-between; padding: 0.45rem 0.65rem;
                  border-radius: 8px; cursor: pointer; transition: all 0.15s;
                  background: ${isSelected ? 'var(--accent-primary, #6366f1)' : 'transparent'};
                  color: ${isSelected ? '#ffffff' : 'var(--text-main)'};">
        <div style="display: flex; align-items: center; gap: 0.5rem; overflow: hidden;">
          <span style="font-size: 0.85rem; flex-shrink: 0; display: inline-flex; align-items: center;">${icon}</span>
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
      : `<span style="color:var(--accent-yellow); display:inline-flex; align-items: center;">${SVG_LIST}</span> ${escapeHtml(playlistName)}`;
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
        <span style="display:inline-flex;">${SVG_CHECK}</span> All songs matched in this playlist!
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
            ? `<span style="font-size: 0.68rem; color: var(--accent-green, #4ade80); font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 0.2rem;">${SVG_CHECK} Resolved</span>`
            : `<button class="btn btn-secondary btn-sm" style="font-size: 0.68rem; padding: 0.2rem 0.45rem; white-space: nowrap; flex-shrink: 0;"
                 onclick="resolveRightAbsentSong(${globalIdx}, this)" title="Fuzzy search local library">
                 Resolve
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
    if (btn) btn.textContent = 'Resolve';
    return;
  }

  panel.style.display = 'block';
  if (btn) btn.textContent = 'Close';
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
           <button class="btn btn-secondary btn-sm" onclick="openResolveForTrack(${idx})" title="Resolve absent track in right panel">Resolve</button>
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

