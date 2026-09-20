// =============================================================================
// POWERAMP MODULE: Poweramp Backup Importer, Report Modal & Candidate Resolver
// =============================================================================

// POWERAMP PLAYLIST IMPORT & REPORT SYSTEM
// ==========================================

let currentPowerampReport = null;
let currentAbsentSongs = [];
let powerampSelectedFile = null;

function showPowerampImportModal() {
  const modal = document.getElementById('modal-poweramp-import');
  const pathInput = document.getElementById('poweramp-path-input');
  const statusDiv = document.getElementById('poweramp-import-status');
  const filenameLabel = document.getElementById('poweramp-selected-filename');
  const fileInput = document.getElementById('poweramp-file-input');

  powerampSelectedFile = null;
  if (fileInput) fileInput.value = '';
  if (pathInput) pathInput.value = '';
  if (filenameLabel) filenameLabel.textContent = 'No file chosen';
  if (statusDiv) {
    statusDiv.style.display = 'none';
    statusDiv.textContent = '';
  }

  if (modal) modal.style.display = 'flex';
}

function hidePowerampImportModal() {
  const modal = document.getElementById('modal-poweramp-import');
  if (modal) modal.style.display = 'none';
}

function handlePowerampFileChosen(event) {
  const file = event.target.files && event.target.files[0];
  const label = document.getElementById('poweramp-selected-filename');
  if (file) {
    powerampSelectedFile = file;
    if (label) label.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  } else {
    powerampSelectedFile = null;
    if (label) label.textContent = 'No file chosen';
  }
}

async function submitPowerampImport() {
  const pathInput = document.getElementById('poweramp-path-input');
  const statusDiv = document.getElementById('poweramp-import-status');
  const submitBtn = document.getElementById('btn-submit-poweramp-import');

  const enteredPath = pathInput ? pathInput.value.trim() : '';

  if (!powerampSelectedFile && !enteredPath) {
    showToast('Please select a file or enter a local path!', 'error');
    return;
  }

  if (statusDiv) {
    statusDiv.style.display = 'block';
    statusDiv.style.color = 'var(--text-main)';
    statusDiv.innerHTML = 'Analyzing database and matching library tracks...';
  }
  if (submitBtn) submitBtn.disabled = true;

  try {
    let res;
    if (powerampSelectedFile) {
      const formData = new FormData();
      formData.append('file', powerampSelectedFile);
      res = await fetch('/api/poweramp/import', {
        method: 'POST',
        body: formData
      });
    } else {
      res = await fetch('/api/poweramp/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: enteredPath })
      });
    }

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      hidePowerampImportModal();
      showToast(`Imported ${data.total_playlists} playlists! ${data.matched_tracks_count} songs matched.`, 'success');
      await loadPlaylists();
      renderAbsentSongsModal(data);
    } else {
      if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.style.color = 'var(--accent-red, #f87171)';
        statusDiv.textContent = `Import error: ${data.error || 'Unknown error'}`;
      }
      showToast(`Import failed: ${data.error || 'Server error'}`, 'error');
    }
  } catch (err) {
    console.error('Poweramp import error:', err);
    if (statusDiv) {
      statusDiv.style.display = 'block';
      statusDiv.style.color = 'var(--accent-red, #f87171)';
      statusDiv.textContent = `Connection error: ${err.message}`;
    }
    showToast('Error connecting to server during import.', 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function renderAbsentSongsModal(report) {
  currentPowerampReport = report;
  currentAbsentSongs = report.absent_songs || [];

  const modal = document.getElementById('modal-absent-songs');
  if (!modal) return;

  // Stats
  const elPlaylists = document.getElementById('report-stat-playlists');
  const elMatched = document.getElementById('report-stat-matched');
  const elAbsent = document.getElementById('report-stat-absent');
  const elLiked = document.getElementById('report-stat-liked');

  if (elPlaylists) elPlaylists.textContent = report.total_playlists || 0;
  if (elMatched) elMatched.textContent = report.matched_tracks_count || 0;
  if (elAbsent) elAbsent.textContent = report.absent_tracks_count || 0;
  if (elLiked) elLiked.textContent = report.liked_tracks_synced || 0;

  // Populate playlist filter
  const filterSelect = document.getElementById('absent-filter-playlist');
  if (filterSelect) {
    let options = '<option value="">All Playlists</option>';
    if (report.playlists) {
      report.playlists.forEach(pl => {
        options += `<option value="${escapeHtml(pl.name)}">${escapeHtml(pl.name)} (${pl.absent_count} absent)</option>`;
      });
    }
    filterSelect.innerHTML = options;
    filterSelect.value = '';
  }

  const searchInput = document.getElementById('absent-search-input');
  if (searchInput) searchInput.value = '';

  filterAbsentSongs();
  modal.style.display = 'flex';
}

function hideAbsentSongsModal() {
  const modal = document.getElementById('modal-absent-songs');
  if (modal) modal.style.display = 'none';
}

// Track which resolve panels are open: key = "idx-playlistname-filename"
const _resolveOpenPanels = new Set();

function filterAbsentSongs() {
  const filterSelect = document.getElementById('absent-filter-playlist');
  const searchInput = document.getElementById('absent-search-input');
  const tbody = document.getElementById('absent-songs-tbody');
  const countLabel = document.getElementById('absent-count-label');

  const selectedPl = filterSelect ? filterSelect.value : '';
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  let filtered = currentAbsentSongs;
  if (selectedPl) {
    filtered = filtered.filter(item => item.playlist_name === selectedPl);
  }
  if (query) {
    filtered = filtered.filter(item => {
      const name = (item.readable_name || '').toLowerCase();
      const fn = (item.filename || '').toLowerCase();
      const path = (item.original_path || '').toLowerCase();
      return name.includes(query) || fn.includes(query) || path.includes(query);
    });
  }

  if (countLabel) {
    countLabel.textContent = `Showing ${filtered.length} of ${currentAbsentSongs.length} absent songs`;
  }

  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-muted col-center" style="padding: 1.5rem;">No absent songs match criteria.</td></tr>';
    return;
  }

  let html = '';
  filtered.forEach((item, idx) => {
    const globalIdx = currentAbsentSongs.indexOf(item);
    const resolveKey = `resolve-panel-${globalIdx}`;
    html += `
      <tr id="absent-row-${globalIdx}">
        <td class="col-center text-tabular">${idx + 1}</td>
        <td>
          <div style="font-weight: 600; color: var(--text-main); word-break: break-all;">
            ${escapeHtml(item.readable_name || item.filename)}
          </div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">${escapeHtml(item.filename)}</div>
        </td>
        <td style="font-size: 0.78rem; font-family: monospace; color: var(--text-muted); word-break: break-all;">
          ${escapeHtml(item.original_path || '—')}
        </td>
        <td style="font-size: 0.85rem;">
          <span class="badge badge-purple">${escapeHtml(item.playlist_name || 'Unknown')}</span>
        </td>
        <td class="col-center">
          <button class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 0.25rem 0.5rem; white-space: nowrap;"
            onclick="resolveAbsentSong(${globalIdx}, this)" title="Search local library for a match">
            Resolve
          </button>
        </td>
      </tr>
      <tr id="${resolveKey}" style="display: none;">
        <td colspan="5" style="padding: 0; background: var(--bg-crust); border-bottom: 1px solid var(--border-color);">
          <div style="padding: 0.75rem 1rem;">
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
              Searching library for: <strong style="color: var(--text-main);">${escapeHtml(item.readable_name || item.filename)}</strong>
            </div>
            <div id="${resolveKey}-results" style="display: flex; flex-direction: column; gap: 0.4rem;">
              <span class="text-muted" style="font-size: 0.8rem;">Searching...</span>
            </div>
          </div>
        </td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

async function resolveAbsentSong(globalIdx, btn) {
  const item = currentAbsentSongs[globalIdx];
  if (!item) return;

  const resolveKey = `resolve-panel-${globalIdx}`;
  const panelRow = document.getElementById(resolveKey);
  const resultsDiv = document.getElementById(`${resolveKey}-results`);

  if (!panelRow) return;

  // Toggle: close if already open
  if (panelRow.style.display !== 'none') {
    panelRow.style.display = 'none';
    if (btn) btn.textContent = 'Resolve';
    return;
  }

  // Open panel and start searching
  panelRow.style.display = '';
  if (btn) btn.textContent = 'Close';
  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">Searching library...</span>';

  const query = item.readable_name || item.filename;
  const playlistName = item.playlist_name;

  try {
    // Strategy 1: client-side fuzzy search against allSongs (instant, no round-trip)
    let matches = fuzzySearchLocalSongs(query, allSongs, 8);

    // Strategy 2: fallback to server-side search if allSongs is empty
    if (matches.length === 0 && allSongs.length === 0) {
      const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(query)}&n=8`);
      if (res.ok) {
        matches = await res.json();
      }
    }

    renderResolveResults(resolveKey, matches, item, playlistName, globalIdx);
  } catch (err) {
    console.error('Resolve search error:', err);
    if (resultsDiv) resultsDiv.innerHTML = `<span style="color: var(--accent-red, #f87171); font-size: 0.8rem;">Search failed: ${escapeHtml(err.message)}</span>`;
  }
}

function fuzzySearchLocalSongs(query, songs, maxResults = 8) {
  if (!query || !songs || songs.length === 0) return [];

  const qLower = query.toLowerCase();
  const cleanQ = cleanStringForResolve(query);
  const qWords = cleanQ.split(/\s+/).filter(Boolean);

  const scored = [];
  for (const s of songs) {
    const title = (s.title || '').toLowerCase();
    const fn = (s.filename || '').toLowerCase();
    const artist = (s.artist || '').toLowerCase();
    const cleanTitle = cleanStringForResolve(s.title || s.filename || '');
    const cleanFn = cleanStringForResolve(s.filename || '');

    let score = 0;

    // Exact / substring matches
    if (title === qLower || fn === qLower) score += 100;
    else if (title.startsWith(qLower) || fn.startsWith(qLower)) score += 60;
    else if (title.includes(qLower) || fn.includes(qLower)) score += 30;

    // Clean-string matches
    if (cleanTitle === cleanQ) score += 70;
    else if (cleanTitle.startsWith(cleanQ)) score += 35;
    else if (cleanQ && cleanTitle.includes(cleanQ)) score += 20;

    if (cleanFn === cleanQ) score += 55;
    else if (cleanFn.startsWith(cleanQ)) score += 28;
    else if (cleanQ && cleanFn.includes(cleanQ)) score += 15;

    // Word overlap scoring
    if (qWords.length > 0) {
      const titleWords = new Set(cleanTitle.split(/\s+/).filter(Boolean));
      const fnWords = new Set(cleanFn.split(/\s+/).filter(Boolean));
      const allWords = new Set([...titleWords, ...fnWords]);
      const common = qWords.filter(w => allWords.has(w)).length;
      score += Math.round(80 * common / qWords.length);
    }

    if (score > 0) scored.push({ ...s, _score: score });
  }

  scored.sort((a, b) => b._score - a._score);
  return scored.slice(0, maxResults);
}

function cleanStringForResolve(text) {
  if (!text) return '';
  let s = text.toLowerCase();
  s = s.replace(/\s*[\(\[][^\)\]]*(?:128|192|256|320|flac|kbps|audio|video|lyrics|official|remaster|hd|hq)[^\)\]]*[\)\]]/gi, '');
  s = s.replace(/\.(?:mp3|flac|m4a|wav|ogg|opus|aac)$/i, '');
  s = s.replace(/[\-_.\(\)\[\]'"~]+/g, ' ');
  return s.split(/\s+/).filter(Boolean).join(' ').trim();
}

function renderResolveResults(resolveKey, matches, absentItem, playlistName, globalIdx) {
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  if (!resultsDiv) return;

  if (!matches || matches.length === 0) {
    resultsDiv.innerHTML = `
      <div style="font-size: 0.8rem; color: var(--text-muted); padding: 0.35rem 0;">
        No matches found in local library.
        <a href="#" style="color: var(--accent-yellow); margin-left: 0.4rem; font-size: 0.75rem;"
           onclick="resolveSearchDesktop(${globalIdx}); return false;">
          Search connected device →
        </a>
      </div>`;
    return;
  }

  let html = `<div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.35rem;">${matches.length} match${matches.length !== 1 ? 'es' : ''} found:</div>`;
  html += `<div style="display: flex; flex-direction: column; gap: 0.3rem; max-height: 200px; overflow-y: auto;">`;

  matches.forEach((song, i) => {
    const fp = song.filepath || song._data || '';
    const title = song.title || song.filename || fp;
    const artist = song.artist || 'Unknown';
    const dur = song.duration_formatted || '';
    const isResolved = absentItem._resolved_filepath === fp;

    html += `
      <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.5rem;
                  background: ${isResolved ? 'rgba(74,222,128,0.12)' : 'var(--bg-card)'}; border-radius: 6px;
                  border: 1px solid ${isResolved ? 'rgba(74,222,128,0.3)' : 'var(--border-color)'};">
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 0.8rem; font-weight: 600; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
               title="${escapeHtml(fp)}">
            ${escapeHtml(title)}
          </div>
          <div style="font-size: 0.7rem; color: var(--text-muted);">
            ${escapeHtml(artist)}${dur ? ' • ' + escapeHtml(dur) : ''}
          </div>
        </div>
        ${isResolved
          ? `<span style="font-size: 0.7rem; color: var(--accent-green, #4ade80); font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 0.2rem;">${SVG_CHECK} Resolved</span>`
          : `<button class="btn btn-sm" style="font-size: 0.7rem; padding: 0.2rem 0.55rem; white-space: nowrap; flex-shrink: 0;"
               onclick="confirmResolveMatch(${globalIdx}, '${escapeJs(fp)}', '${escapeJs(title)}', '${escapeJs(playlistName)}')"
               title="Add this song to the playlist as a replacement">
               + Use This
             </button>`}
      </div>
    `;
  });

  html += `</div>`;

  // Also add manual search box
  html += `
    <div style="margin-top: 0.5rem; display: flex; gap: 0.4rem; align-items: center;">
      <input type="text" id="${resolveKey}-manual-q" class="search-bar" style="flex: 1; height: 28px; font-size: 0.75rem; box-sizing: border-box;"
             placeholder="Search differently..." value="${escapeHtml(absentItem.readable_name || absentItem.filename)}"
             onkeydown="if(event.key==='Enter') resolveManualSearch(${globalIdx})">
      <button class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 0.25rem 0.6rem; white-space: nowrap;"
              onclick="resolveManualSearch(${globalIdx})">Search</button>
    </div>`;

  resultsDiv.innerHTML = html;
}

async function resolveManualSearch(globalIdx) {
  const resolveKey = `resolve-panel-${globalIdx}`;
  const inputEl = document.getElementById(`${resolveKey}-manual-q`);
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  const item = currentAbsentSongs[globalIdx];
  if (!item || !inputEl) return;

  const q = inputEl.value.trim();
  if (!q) return;

  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">Searching...</span>';

  let matches = fuzzySearchLocalSongs(q, allSongs, 8);
  if (matches.length === 0) {
    try {
      const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(q)}&n=8`);
      if (res.ok) matches = await res.json();
    } catch (_) {}
  }

  renderResolveResults(resolveKey, matches, item, item.playlist_name, globalIdx);
}

async function resolveSearchDesktop(globalIdx) {
  const item = currentAbsentSongs[globalIdx];
  if (!item) return;

  const resolveKey = `resolve-panel-${globalIdx}`;
  const resultsDiv = document.getElementById(`${resolveKey}-results`);
  if (resultsDiv) resultsDiv.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">Searching connected device...</span>';

  const q = item.readable_name || item.filename;
  try {
    const res = await fetch(`/api/poweramp/search-library?q=${encodeURIComponent(q)}&n=8`);
    const matches = res.ok ? await res.json() : [];
    renderResolveResults(resolveKey, matches, item, item.playlist_name, globalIdx);
  } catch (err) {
    if (resultsDiv) resultsDiv.innerHTML = `<span style="color: var(--accent-red, #f87171); font-size: 0.8rem;">Search failed: ${escapeHtml(err.message)}</span>`;
  }
}

async function confirmResolveMatch(globalIdx, filepath, songTitle, playlistName) {
  const item = currentAbsentSongs[globalIdx];
  if (!item) return;

  // Find playlist ID from allPlaylists or selectedPlaylist
  const playlist = allPlaylists.find(p => p.name && p.name.toLowerCase() === (playlistName || '').toLowerCase())
                   || (selectedPlaylist && selectedPlaylist.name === playlistName ? selectedPlaylist : null)
                   || (selectedPlaylist ? selectedPlaylist : null);

  if (!playlist) {
    showToast(`Playlist "${playlistName}" not found locally. Import first to create the playlist.`, 'info');
    // Still mark as resolved in UI
    item._resolved_filepath = filepath;
    item._resolved_title = songTitle;
    const resolveKey = `resolve-panel-${globalIdx}`;
    renderResolveResults(resolveKey, null, item, playlistName, globalIdx);
    updateAbsentRowResolved(globalIdx, songTitle);
    return;
  }

  try {
    const res = await fetch(`/api/playlists/${playlist.id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resolved_filepath: filepath,
        original_path: item.original_path || item.filepath,
        track_id: item.id || null,
        title: songTitle
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      item._resolved_filepath = filepath;
      item._resolved_title = songTitle;
      item.status = 'present';

      const resolveKey = `resolve-panel-${globalIdx}`;
      // Re-render the results panel showing Resolved state
      const currentQ = currentAbsentSongs[globalIdx].readable_name || currentAbsentSongs[globalIdx].filename;
      const matches = fuzzySearchLocalSongs(currentQ, allSongs, 8);
      renderResolveResults(resolveKey, matches, item, playlistName, globalIdx);

      updateAbsentRowResolved(globalIdx, songTitle);
      showToast(`Resolved "${songTitle}" in playlist "${playlist.name}"!`, 'success');
      loadPlaylists();
      // If currently viewing this playlist in 3-column detail view, reload tracks & right panel
      if (selectedPlaylist && selectedPlaylist.id === playlist.id) {
        fetch(`/api/playlists/${playlist.id}/tracks`)
          .then(r => r.json())
          .then(tracks => {
            currentPlaylistTracks = tracks || [];
            renderPlaylistTracks();
            const badge = document.getElementById('selected-playlist-badge');
            const countText = document.getElementById('playlist-track-count-text');
            if (badge) badge.textContent = `${tracks.length} track${tracks.length !== 1 ? 's' : ''}`;
            if (countText) countText.textContent = `${tracks.length} song${tracks.length !== 1 ? 's' : ''}`;
          })
          .catch(e => console.error('Error reloading tracks:', e));
        filterPlaylistPageAbsentSongs();
      }
    } else {
      showToast(`Failed to resolve track: ${data.error || 'Unknown error'}`, 'error');
    }
  } catch (err) {
    console.error('Error resolving track:', err);
    showToast('Failed to connect to server.', 'error');
  }
}

function updateAbsentRowResolved(globalIdx, songTitle) {
  const row = document.getElementById(`absent-row-${globalIdx}`);
  if (!row) return;

  // Find and update the Resolve button cell to show Resolved
  const resolveCell = row.querySelector('td:last-child');
  if (resolveCell) {
    resolveCell.innerHTML = `<span style="font-size: 0.72rem; color: var(--accent-green, #4ade80); font-weight: 700; display: inline-flex; align-items: center; gap: 0.2rem;">${SVG_CHECK} Resolved</span>`;
  }

  // Strike-through the title cell
  const titleCell = row.querySelector('td:nth-child(2) div:first-child');
  if (titleCell) {
    titleCell.style.textDecoration = 'line-through';
    titleCell.style.color = 'var(--text-muted)';
  }
}

function downloadAbsentSongsReport() {
  if (!currentPowerampReport || !currentPowerampReport.absent_songs) {
    showToast('No absent songs report available to download.', 'info');
    return;
  }

  fetch('/api/poweramp/export-absent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ absent_songs: currentAbsentSongs })
  })
    .then(response => {
      if (!response.ok) throw new Error('Download request failed');
      return response.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'poweramp_absent_songs.txt';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      showToast('Absent songs report downloaded.', 'success');
    })
    .catch(err => {
      console.error('Error downloading report:', err);
      showToast('Error downloading report.', 'error');
    });
}
