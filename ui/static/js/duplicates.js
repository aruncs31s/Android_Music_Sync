// =============================================================================
// DUPLICATES MODULE: Tag & Audio Fingerprint Clusters, Deduplication Strategies
// =============================================================================

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
    container.innerHTML = `<p class="text-muted" style="display: flex; align-items: center; gap: 0.5rem; padding: 1rem 0;">${SVG_SPARKLES} Loading duplicates...</p>`;
  }
  loadDuplicates(true);
}

// --- Live SSE Duplicate Analysis Terminal ---

function _dupTerminalLineClass(msg) {
  const tag = msg.slice(0, 7).toUpperCase();
  if (tag.startsWith('[CACHE]')) return 'log-cache';
  if (tag.startsWith('[FP]'))    return 'log-fp';
  if (tag.startsWith('[SCAN]'))  return 'log-scan';
  if (tag.startsWith('[TAG]'))   return 'log-tag';
  if (tag.startsWith('[MATCH]')) return 'log-match';
  if (tag.startsWith('[SKIP]'))  return 'log-skip';
  if (tag.startsWith('[FAIL]'))  return 'log-fail';
  if (tag.startsWith('[WARN]'))  return 'log-warn';
  if (tag.startsWith('[START]')) return 'log-start';
  if (tag.startsWith('[INFO]'))  return 'log-info';
  if (tag.startsWith('[DONE]'))  return 'log-done';
  if (tag.startsWith('[ERROR]')) return 'log-error';
  return '';
}

// Terminal render helper — caps the number of DOM nodes and coalesces the
// auto-scroll into a single per-frame update so progress bursts cannot freeze
// the tab's main thread.
function pushTermLine(logEl, msg) {
  if (!logEl) return;
  const line = document.createElement('span');
  line.className = 'dup-terminal-line ' + _dupTerminalLineClass(msg);
  line.textContent = msg;
  logEl.appendChild(line);
  logEl.appendChild(document.createTextNode('\n'));
  while (logEl.childElementCount > 250) {
    logEl.removeChild(logEl.firstElementChild);
  }
  if (logEl._scrollFrame == null) {
    logEl._scrollFrame = requestAnimationFrame(() => {
      logEl._scrollFrame = null;
      logEl.scrollTop = logEl.scrollHeight;
    });
  }
}

function _dupTerminalAppend(msg) {
  const log = document.getElementById('dup-terminal-log');
  pushTermLine(log, msg);
}

function streamDuplicates() {
  // Close any existing SSE connection
  if (dupEventSource) {
    dupEventSource.close();
    dupEventSource = null;
  }

  const btn = document.getElementById('btn-rescan-duplicates');
  const terminal = document.getElementById('dup-terminal');
  const termLog = document.getElementById('dup-terminal-log');
  const container = document.getElementById('duplicates-container');

  // Show terminal, clear previous log
  if (terminal) terminal.style.display = 'block';
  if (termLog) termLog.innerHTML = '';
  if (btn) { btn.disabled = true; btn.textContent = 'Analyzing…'; }
  if (container) container.innerHTML = '';

  const params = new URLSearchParams();
  params.set('fingerprint', useAudioFingerprinting ? 'true' : 'false');

  const evtSource = new EventSource(`/api/duplicates/stream?${params.toString()}`);
  dupEventSource = evtSource;

  let logCount = 0;
  const counter = document.getElementById('dup-terminal-counter');

  evtSource.onmessage = (e) => {
    let payload;
    try { payload = JSON.parse(e.data); } catch { return; }

    if (payload.type === 'log') {
      _dupTerminalAppend(payload.msg);
      logCount++;
      if (counter) counter.textContent = `${logCount} lines`;

    } else if (payload.type === 'done') {
      evtSource.close();
      dupEventSource = null;
      _dupTerminalAppend(payload.msg || '');

      // Brief pause then collapse terminal and render results
      setTimeout(() => {
        if (terminal) terminal.style.display = 'none';
      }, 1800);

      // Populate clusters and render
      const data = payload.result || {};
      allClusters = data.clusters || [];
      filteredClusters = [...allClusters];
      dupPage = 1;

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

      const validPaths = new Set();
      allClusters.forEach(c => (c.songs || []).forEach(s => validPaths.add(s.filepath)));
      for (const p of selectedDuplicatePaths) {
        if (!validPaths.has(p)) selectedDuplicatePaths.delete(p);
      }

      updateDuplicatesSelectionUI();
      renderDuplicatesPage();

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Analyze`;
      }

    } else if (payload.type === 'error') {
      _dupTerminalAppend(`[ERROR] ${payload.msg}`);
      evtSource.close();
      dupEventSource = null;
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Analyze`;
      }
    }
  };

  evtSource.onerror = () => {
    if (evtSource.readyState === EventSource.CLOSED) return;
    _dupTerminalAppend('[ERROR] Connection to server lost.');
    evtSource.close();
    dupEventSource = null;
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Analyze`;
    }
  };
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
        showToast("Safety Limit: At least one copy in this cluster must be kept so the song is not lost.", 'error');
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

function updateDuplicatesReclaimableSummary() {
  const banner = document.getElementById('dup-reclaimable-banner');
  const sizeEl = document.getElementById('dup-reclaimable-size');
  const countEl = document.getElementById('dup-reclaimable-count');
  if (!banner || !sizeEl || !countEl) return;

  if (!allClusters || allClusters.length === 0) {
    banner.style.display = 'none';
    return;
  }

  let redundantCount = 0;
  let redundantBytes = 0;

  allClusters.forEach(c => {
    const keeper = findKeeperInCluster(c, currentDupKeepStrategy);
    if (c.songs && c.songs.length > 1) {
      c.songs.forEach(s => {
        if (keeper && s.filepath === keeper.filepath) return;
        redundantCount++;
        if (typeof s.size === 'number') {
          redundantBytes += s.size;
        }
      });
    }
  });

  if (redundantCount > 0) {
    sizeEl.textContent = formatBytes(redundantBytes);
    countEl.textContent = redundantCount;
    banner.style.display = 'flex';
  } else {
    banner.style.display = 'none';
  }
}

function selectAllRedundantDuplicates() {
  if (!allClusters || allClusters.length === 0) {
    showToast('No duplicate clusters found.', 'info');
    return;
  }

  selectedDuplicatePaths.clear();
  let count = 0;
  allClusters.forEach(c => {
    const keeper = findKeeperInCluster(c, currentDupKeepStrategy);
    if (c.songs && c.songs.length > 1) {
      c.songs.forEach(s => {
        if (keeper && s.filepath === keeper.filepath) return;
        selectedDuplicatePaths.add(s.filepath);
        count++;
      });
    }
  });

  updateDuplicatesSelectionUI();
  renderDuplicatesPage();
  showToast(`Selected ${count} redundant copies across all clusters (best copies preserved).`, 'success');
}

function renderDuplicatesPage() {
  updateDuplicatesReclaimableSummary();
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
      showToast(`Deleted ${data.deleted_count} duplicate files. Exactly 1 copy in each cluster preserved!`, 'success');
      selectedDuplicatePaths.clear();
      updateDuplicatesSelectionUI();
      loadDuplicates();
      loadSongs();
      loadDashboardStats();
    } else {
      showToast(`Error deleting duplicate files: ${data.error || data.message || 'Batch delete failed'}`, 'error');
    }
  } catch (err) {
    console.error('Error executing batch duplicate deletion:', err);
    showToast('Connection error while batch deleting duplicate files.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Confirm & Delete Selected Files';
    }
  }
}

