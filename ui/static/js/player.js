// =============================================================================
// PLAYER MODULE: Audio Engine, Bottom Bar, Queue Panel, Liked Songs & Player Tab
// =============================================================================

// --- BESPOKE AUDIO PLAYER ENGINE ---

function formatDuration(sec) {
  if (isNaN(sec) || !isFinite(sec) || sec < 0) return '0:00';
  const minutes = Math.floor(sec / 60);
  const seconds = Math.floor(sec % 60);
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

const SVG_VOL_HIGH = `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>`;
const SVG_VOL_MUTED = `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>`;

function initAudioPlayer() {
  const player = document.getElementById('audio-player');
  const scrubber = document.getElementById('player-scrubber');
  const curTimeEl = document.getElementById('player-current-time');
  const totalTimeEl = document.getElementById('player-total-time');
  const volSlider = document.getElementById('player-volume');
  if (!player) return;

  // Restore saved volume
  const savedVol = localStorage.getItem('antigravity_player_volume');
  if (savedVol !== null) {
    const v = parseFloat(savedVol);
    player.volume = isNaN(v) ? 1 : Math.max(0, Math.min(1, v));
    if (volSlider) volSlider.value = player.volume;
  }
  updatePlayerVolumeIcon();

  player.onplay = () => setPlayerPlayState(true);
  player.onpause = () => setPlayerPlayState(false);
  player.onended = () => handleTrackEnded();

  player.ontimeupdate = () => {
    if (!isScrubbing && scrubber && player.duration) {
      scrubber.value = player.currentTime;
      if (curTimeEl) curTimeEl.textContent = formatDuration(player.currentTime);
      updateScrubberProgress(player.currentTime, player.duration);
    }
  };

  player.onloadedmetadata = () => {
    if (scrubber) {
      scrubber.min = 0;
      scrubber.max = player.duration || 100;
      scrubber.value = player.currentTime || 0;
    }
    if (totalTimeEl) {
      totalTimeEl.textContent = formatDuration(player.duration);
    }
    updateScrubberProgress(player.currentTime || 0, player.duration || 100);
  };

  player.onvolumechange = () => {
    if (volSlider) volSlider.value = player.muted ? 0 : player.volume;
    updatePlayerVolumeIcon();
  };

  player.onerror = (e) => {
    const err = player.error;
    let codeStr = 'UNKNOWN';
    let userMsg = 'Audio playback error occurred.';
    if (err) {
      switch (err.code) {
        case 1: // MediaError.MEDIA_ERR_ABORTED
          codeStr = 'MEDIA_ERR_ABORTED';
          userMsg = 'Playback was aborted.';
          break;
        case 2: // MediaError.MEDIA_ERR_NETWORK
          codeStr = 'MEDIA_ERR_NETWORK';
          userMsg = 'Network error while loading audio.';
          break;
        case 3: // MediaError.MEDIA_ERR_DECODE
          codeStr = 'MEDIA_ERR_DECODE';
          userMsg = 'Audio decoding failed (unsupported codec or corrupt audio stream).';
          break;
        case 4: // MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED
          codeStr = 'MEDIA_ERR_SRC_NOT_SUPPORTED';
          userMsg = 'Audio format or source URL not supported by browser.';
          break;
      }
    }
    const trackInfo = currentTrackPath ? `on '${currentTrackPath}'` : '';
    console.error(`[AudioPlayer] Playback Error (${codeStr}):`, err, trackInfo);
    showToast(userMsg, 'error', 4000);
    setPlayerPlayState(false);

    // Send error to server logger so it appears in terminal and server logs
    fetch('/api/player/log_error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error_code: codeStr,
        message: userMsg,
        src: player.src,
        filepath: currentTrackPath
      })
    }).catch(() => {});
  };

  setupPlayerKeyboardHotkeys();
}

function updateScrubberProgress(current, total) {
  const scrubber = document.getElementById('player-scrubber');
  if (!scrubber || !total) return;
  const pct = Math.min(100, Math.max(0, (current / total) * 100));
  scrubber.style.background = `linear-gradient(to right, var(--accent-yellow) ${pct}%, #262626 ${pct}%)`;
}

function onScrubberInput(val) {
  isScrubbing = true;
  const player = document.getElementById('audio-player');
  const curTimeEl = document.getElementById('player-current-time');
  const v = parseFloat(val);
  if (curTimeEl) curTimeEl.textContent = formatDuration(v);
  if (player && player.duration) {
    updateScrubberProgress(v, player.duration);
  }
}

function onScrubberChange(val) {
  const player = document.getElementById('audio-player');
  if (player) {
    player.currentTime = parseFloat(val);
  }
  isScrubbing = false;
}

function onVolumeInput(val) {
  const player = document.getElementById('audio-player');
  if (!player) return;
  const v = parseFloat(val);
  player.volume = isNaN(v) ? 1 : Math.max(0, Math.min(1, v));
  player.muted = false;
  localStorage.setItem('antigravity_player_volume', player.volume);
  updatePlayerVolumeIcon();
}

function togglePlayerMute() {
  const player = document.getElementById('audio-player');
  const volSlider = document.getElementById('player-volume');
  if (!player) return;
  player.muted = !player.muted;
  if (volSlider) {
    volSlider.value = player.muted ? 0 : player.volume;
  }
  updatePlayerVolumeIcon();
}

function updatePlayerVolumeIcon() {
  const player = document.getElementById('audio-player');
  const icon = document.getElementById('player-vol-icon');
  if (!player || !icon) return;
  const isMuted = player.muted || player.volume === 0;
  icon.innerHTML = isMuted ? SVG_VOL_MUTED : SVG_VOL_HIGH;
}

function togglePlayerLoop() {
  isPlayerLooping = !isPlayerLooping;
  const player = document.getElementById('audio-player');
  if (player) player.loop = isPlayerLooping;
  const loopBtn = document.getElementById('btn-player-loop');
  if (loopBtn) {
    if (isPlayerLooping) {
      loopBtn.style.color = 'var(--accent-yellow)';
      loopBtn.title = 'Repeat Mode: Active (Loop)';
    } else {
      loopBtn.style.color = '';
      loopBtn.title = 'Toggle Repeat Mode';
    }
  }
}

function toggleShuffle() {
  const shuffleBtn = document.getElementById('btn-player-shuffle');
  if (isShuffled) {
    // Restore original order and find current track's new position
    const currentPath = currentTrackPath;
    activeQueue = [...originalQueue];
    queueIndex = activeQueue.findIndex(t => t.filepath === currentPath);
    if (queueIndex < 0) queueIndex = 0;
    isShuffled = false;
    if (shuffleBtn) shuffleBtn.classList.remove('shuffle-on');
    if (shuffleBtn) shuffleBtn.title = 'Shuffle Off';
  } else {
    // Save original and shuffle
    originalQueue = [...activeQueue];
    const currentTrack = activeQueue[queueIndex];
    const rest = activeQueue.filter((_, i) => i !== queueIndex);
    for (let i = rest.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [rest[i], rest[j]] = [rest[j], rest[i]];
    }
    activeQueue = [currentTrack, ...rest];
    queueIndex = 0;
    isShuffled = true;
    if (shuffleBtn) shuffleBtn.classList.add('shuffle-on');
    if (shuffleBtn) shuffleBtn.title = 'Shuffle On — click to disable';
  }
  renderQueuePanel();
}

function seekRelative(sec) {
  const player = document.getElementById('audio-player');
  if (!player || !player.duration) return;
  player.currentTime = Math.max(0, Math.min(player.duration, player.currentTime + sec));
}

function playPreviousTrack() {
  const player = document.getElementById('audio-player');
  if (player && player.currentTime > 3) {
    player.currentTime = 0;
    return;
  }
  if (activeQueue && activeQueue.length > 0) {
    if (queueIndex > 0) {
      queueIndex--;
      const prevTrack = activeQueue[queueIndex];
      playAudio(prevTrack.filepath, prevTrack.title, prevTrack.artist, activeQueue, queueIndex, prevTrack.bitrate_kbps, prevTrack.device_id);
    } else if (isPlayerLooping) {
      queueIndex = activeQueue.length - 1;
      const lastTrack = activeQueue[queueIndex];
      playAudio(lastTrack.filepath, lastTrack.title, lastTrack.artist, activeQueue, queueIndex, lastTrack.bitrate_kbps, lastTrack.device_id);
    } else if (player) {
      player.currentTime = 0;
    }
  }
}

function playNextTrack() {
  if (activeQueue && activeQueue.length > 0) {
    if (queueIndex + 1 < activeQueue.length) {
      queueIndex++;
      const nextTrack = activeQueue[queueIndex];
      playAudio(nextTrack.filepath, nextTrack.title, nextTrack.artist, activeQueue, queueIndex, nextTrack.bitrate_kbps, nextTrack.device_id);
    } else if (isPlayerLooping) {
      queueIndex = 0;
      const firstTrack = activeQueue[0];
      playAudio(firstTrack.filepath, firstTrack.title, firstTrack.artist, activeQueue, 0, firstTrack.bitrate_kbps, firstTrack.device_id);
    } else {
      setPlayerPlayState(false);
    }
  } else {
    setPlayerPlayState(false);
  }
}

function closeAudioPlayer() {
  const player = document.getElementById('audio-player');
  const playerBar = document.getElementById('audio-player-bar');
  if (player) {
    player.pause();
    player.src = '';
  }
  if (playerBar) {
    playerBar.style.display = 'none';
  }
  currentTrackPath = null;
  setPlayerPlayState(false);
}

function setupPlayerKeyboardHotkeys() {
  document.addEventListener('keydown', (e) => {
    const active = document.activeElement;
    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT' || active.isContentEditable)) {
      if (e.key === 'Escape') {
        active.blur();
      }
      return;
    }

    if (e.key === ' ' || e.code === 'Space') {
      e.preventDefault();
      togglePlayPause();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      seekRelative(-5);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      seekRelative(5);
    } else if (e.key === 'j' || e.key === 'J') {
      e.preventDefault();
      playPreviousTrack();
    } else if (e.key === 'k' || e.key === 'K') {
      e.preventDefault();
      playNextTrack();
    } else if (e.key === 'm' || e.key === 'M') {
      e.preventDefault();
      togglePlayerMute();
    } else if (e.key === 'l' || e.key === 'L') {
      e.preventDefault();
      toggleCurrentTrackLike();
    } else if (e.key === 'Escape') {
      closeConfirmModal(false);
      hideAddToPlaylistModal();
      hideCreatePlaylistModal();
      hideBatchDeleteDuplicatesModal();
      hideDeviceUploadModal();
      hideTranscodeModal();
      hideSyncSongModal();
      closeAudioPlayer();
    } else if (e.key === '/') {
      const searchInput = document.getElementById('lib-search');
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
    }
  });
}

function setPlayerPlayState(playing) {
  isPlaying = playing;
  const playPauseBtn = document.getElementById('btn-player-playpause');
  if (playPauseBtn) {
    playPauseBtn.innerHTML = isPlaying ? SVG_PAUSE : SVG_PLAY;
    playPauseBtn.title = isPlaying ? 'Pause (Space)' : 'Play (Space)';
  }
  renderLibraryPage();
  if (selectedPlaylist) {
    renderPlaylistTracks();
  }
}

function togglePlayPause() {
  const player = document.getElementById('audio-player');
  if (!player || !player.src) return;

  if (player.paused) {
    player.play().catch(err => console.warn('Play error:', err));
  } else {
    player.pause();
  }
}

function playOrToggleAudio(filepath, title, artist, index = -1, bitrate = '', deviceId = null) {
  const targetDev = deviceId || currentDeviceId || 'local';
  const player = document.getElementById('audio-player');
  if (currentTrackPath === filepath && player && player.src) {
    togglePlayPause();
  } else {
    let queue = null;
    let qIdx = 0;
    if (index >= 0 && filteredSongs && filteredSongs.length > 0) {
      queue = filteredSongs.map(s => ({ ...s, device_id: s.device_id || targetDev }));
      qIdx = index;
    }
    playAudio(filepath, title, artist, queue, qIdx, bitrate, targetDev);
  }
}

function playAudio(filepath, title, artist, queue = null, index = 0, bitrate = null, deviceId = null) {
  const player = document.getElementById('audio-player');
  const playerBar = document.getElementById('audio-player-bar');
  const titleEl = document.getElementById('player-title');
  const artistEl = document.getElementById('player-artist');
  const badgeEl = document.getElementById('player-quality-badge');

  if (player && playerBar) {
    const trackDeviceId = deviceId || (queue && queue[index] && queue[index].device_id) || currentDeviceId || 'local';
    currentTrackPath = filepath;
    if (queue && queue.length > 0) {
      activeQueue = queue.map(item => ({ ...item, device_id: item.device_id || trackDeviceId }));
      queueIndex = index;
    } else {
      activeQueue = [{ filepath, title, artist, bitrate_kbps: bitrate, device_id: trackDeviceId }];
      queueIndex = 0;
    }

    const streamUrl = `/api/song/stream?filepath=${encodeURIComponent(filepath)}` +
      (trackDeviceId && trackDeviceId !== 'local' ? `&device_id=${encodeURIComponent(trackDeviceId)}` : '');
    player.src = streamUrl;
    if (titleEl) titleEl.textContent = title || 'Unknown Title';
    if (artistEl) {
      artistEl.textContent = (trackDeviceId && trackDeviceId !== 'local')
        ? `${artist || 'Unknown Artist'} • (${currentDeviceName || trackDeviceId})`
        : (artist || 'Unknown Artist');
    }

    const bVal = bitrate || (activeQueue[queueIndex] && activeQueue[queueIndex].bitrate_kbps);
    if (badgeEl) {
      if (bVal && bVal !== 'Unknown') {
        badgeEl.textContent = bVal;
        badgeEl.style.display = 'inline-block';
      } else {
        badgeEl.style.display = 'none';
      }
    }

    playerBar.style.display = 'flex';
    player.play().catch(err => {
      console.warn('[AudioPlayer] play() rejected:', err);
      const isNotAllowed = err.name === 'NotAllowedError';
      const msg = isNotAllowed
        ? 'Autoplay blocked by browser. Click Play to start playback.'
        : `Playback error: ${err.message || 'Unknown error'}`;
      showToast(msg, 'warning', 3500);

      fetch('/api/player/log_error', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error_code: err.name || 'PlayRejected',
          message: err.message,
          src: player.src,
          filepath: currentTrackPath
        })
      }).catch(() => {});
    });

    // Update queue panel and player-tab song row highlights
    renderQueuePanel();
    updatePlayerTabRowHighlight();
    updateAllLikeButtonsUI();
  }
}

function handleTrackEnded() {
  if (activeQueue && queueIndex + 1 < activeQueue.length) {
    playNextTrack();
  } else if (isPlayerLooping && activeQueue && activeQueue.length > 0) {
    playNextTrack();
  } else {
    setPlayerPlayState(false);
  }
}

// --- LIKED MUSIC SYSTEM JS LOGIC ---

async function loadLikedMusicSet() {
  try {
    const res = await fetch('/api/playlists');
    if (!res.ok) return;
    const playlists = await res.json() || [];
    let likedPl = playlists.find(p => p.name === 'Liked Music');
    if (likedPl) {
      likedPlaylistId = likedPl.id;
      const trRes = await fetch(`/api/playlists/${likedPl.id}/tracks`);
      if (trRes.ok) {
        const tracks = await trRes.json() || [];
        likedSongPaths = new Set(tracks.map(t => t.filepath));
        updateAllLikeButtonsUI();
      }
    }
  } catch (e) {
    console.warn('Failed to load liked music set:', e);
  }
}

async function toggleLikeTrack(filepath, title, artist) {
  if (!filepath) return;
  try {
    if (!likedPlaylistId) {
      const plRes = await fetch('/api/playlists');
      const playlists = await plRes.json() || [];
      let likedPl = playlists.find(p => p.name === 'Liked Music');
      if (!likedPl) {
        const createRes = await fetch('/api/playlists/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Liked Music' })
        });
        const created = await createRes.json();
        likedPl = created.playlist;
      }
      if (likedPl) likedPlaylistId = likedPl.id;
    }

    const isLiked = likedSongPaths.has(filepath);
    if (isLiked) {
      await fetch(`/api/playlists/${likedPlaylistId}/remove-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath })
      });
      likedSongPaths.delete(filepath);
      showToast(`Removed "${title || 'Track'}" from Liked Music`, 'info', 2000);
    } else {
      await fetch(`/api/playlists/${likedPlaylistId}/add-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath })
      });
      likedSongPaths.add(filepath);
      showToast(`Added "${title || 'Track'}" to Liked Music`, 'success', 2000);
    }

    updateAllLikeButtonsUI();

    if (selectedPlaylist && selectedPlaylist.id === likedPlaylistId) {
      selectPlaylist(likedPlaylistId, 'Liked Music');
    }
    if (currentFormatFilter === 'liked') {
      applyLibraryFilterAndSort();
    }
    loadPlaylists();
  } catch (err) {
    console.error('Error toggling like:', err);
    showToast('Failed to update liked state: ' + err.message, 'error', 3000);
  }
}

function toggleCurrentTrackLike() {
  if (!currentTrackPath) {
    showToast('No track is currently playing', 'info', 2000);
    return;
  }
  const curTrack = activeQueue && activeQueue[queueIndex] ? activeQueue[queueIndex] : null;
  const title = curTrack ? curTrack.title : '';
  const artist = curTrack ? curTrack.artist : '';
  toggleLikeTrack(currentTrackPath, title, artist);
}

function updateAllLikeButtonsUI() {
  // Update player bar like button
  const playerLikeBtn = document.getElementById('btn-player-like');
  const playerLikeIcon = document.getElementById('player-like-icon');
  if (playerLikeBtn) {
    const isLiked = Boolean(currentTrackPath && likedSongPaths.has(currentTrackPath));
    playerLikeBtn.classList.toggle('liked', isLiked);
    if (playerLikeIcon) {
      playerLikeIcon.innerHTML = isLiked
        ? '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" fill="#ff0055" stroke="#ff0055"/>'
        : '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>';
    }
  }

  // Update library table rows & player rows
  document.querySelectorAll('.btn-song-like').forEach(btn => {
    const fp = btn.dataset.filepath;
    if (fp) {
      const isLiked = likedSongPaths.has(fp);
      btn.classList.toggle('btn-liked', isLiked);
      btn.innerHTML = isLiked ? SVG_HEART_FILLED : SVG_HEART;
      btn.title = isLiked ? 'Unlike' : 'Like';
    }
  });
}


// MUSIC PLAYER TAB — Library Picker, Song List, Queue Panel, Shuffle
// =============================================================================

// Player-tab internal state
var _playerLibRefreshTimer = null;

/**
 * Called once on DOMContentLoaded. Populates the library dropdown and
 * loads the initial player library songs.
 */
async function initPlayerTab() {
  await refreshPlayerLibraryList(false);
  const sel = document.getElementById('player-library-select');
  const devId = sel ? sel.value : 'local';
  if (!playerTabSongs || playerTabSongs.length === 0) {
    loadPlayerLibrary(devId, false);
  }
}

/**
 * Fetch /api/devices and rebuild the library picker <select>.
 * If reloadSongs is true or songs are not yet loaded, also loads the songs for the selected library.
 */
async function refreshPlayerLibraryList(reloadSongs = false) {
  const sel = document.getElementById('player-library-select');
  const status = document.getElementById('player-lib-status');
  if (!sel) return;

  try {
    const res = await fetch('/api/devices');
    if (!res.ok) throw new Error('Failed to fetch devices');
    const devices = await res.json();

    // Keep current selection
    const prev = sel.value || playerTabDeviceId || 'local';

    // Rebuild options
    let html = '<option value="local">Local Storage</option>';
    if (Array.isArray(devices)) {
      devices.forEach(d => {
        const val = d.device_id || d.serial || d.ip_port;
        if (!val || val === 'local') return;
        const typeBadge = d.device_type === 'Over-IP' ? '[Over-IP]' : '[USB]';
        const label = d.device_name || d.description || val;
        const online = d.is_online !== false ? '' : ' (offline)';
        html += `<option value="${escHtml(val)}">${escHtml(label)} ${typeBadge}${online}</option>`;
      });
    }
    sel.innerHTML = html;

    // Restore previous selection if still available, else fallback to 'local'
    const opts = Array.from(sel.options).map(o => o.value);
    sel.value = opts.includes(prev) ? prev : 'local';

    if (status) {
      const cnt = sel.options.length - 1;
      status.textContent = cnt > 0 ? `${cnt} device${cnt !== 1 ? 's' : ''} found` : 'No remote devices';
    }

    if (reloadSongs || !playerTabSongs || playerTabSongs.length === 0) {
      await loadPlayerLibrary(sel.value, reloadSongs);
    }
  } catch (err) {
    console.warn('[PlayerTab] Could not refresh device list:', err);
    if (status) status.textContent = 'Could not load devices';
  }
}

/**
 * Load songs for the selected library into the player-tab song table.
 */
async function loadPlayerLibrary(deviceId, forceRefresh = false) {
  if (!deviceId) deviceId = 'local';
  playerTabDeviceId = deviceId;

  const tbody = document.getElementById('player-songs-tbody');
  const countEl = document.getElementById('player-song-count');
  if (!tbody) return;

  // Fast path: if device is 'local' and allSongs already loaded, reuse immediately without network wait
  if (deviceId === 'local' && allSongs && allSongs.length > 0 && !forceRefresh) {
    playerTabSongs = allSongs;
    playerTabFiltered = [...allSongs];
    renderPlayerSongTable(playerTabFiltered, deviceId);
    if (countEl) countEl.textContent = `${allSongs.length.toLocaleString()} songs`;
    return;
  }

  tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">⏳ Loading songs…</td></tr>';
  if (countEl) countEl.textContent = '';

  try {
    const url = `/api/devices/${encodeURIComponent(deviceId)}/songs${forceRefresh ? '?refresh=true' : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const songs = data.songs || [];

    playerTabSongs = songs;
    playerTabFiltered = [...songs];

    // If local library is loaded and allSongs is empty, also share with allSongs
    if (deviceId === 'local' && (!allSongs || allSongs.length === 0)) {
      allSongs = songs;
    }

    if (songs.length === 0) {
      if (deviceId === 'local') {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">No local songs indexed yet. Go to <strong>Music Library → Scan / Refresh</strong> to scan your library first.</td></tr>';
      } else {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">No songs found on this device.</td></tr>';
      }
      if (countEl) countEl.textContent = '0 songs';
      return;
    }

    renderPlayerSongTable(playerTabFiltered, deviceId);
    if (countEl) countEl.textContent = `${songs.length.toLocaleString()} songs`;
  } catch (err) {
    console.error('[PlayerTab] Failed to load songs:', err);
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--status-offline);text-align:center;padding:2rem;">Failed to load songs: ${escHtml(String(err))}</td></tr>`;
  }
}

/**
 * Render the player-tab song table from a song array.
 */
function renderPlayerSongTable(songs, deviceId) {
  const tbody = document.getElementById('player-songs-tbody');
  if (!tbody) return;

  if (!songs || songs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem;">No songs found.</td></tr>';
    return;
  }

  const rows = songs.map((s, i) => {
    const fp = s.filepath || s._data || '';
    const title = escHtml(s.title || s.filename || fp.split('/').pop() || 'Unknown');
    const artist = escHtml(s.artist || 'Unknown');
    const album = escHtml(s.album || '—');
    const bitrate = s.bitrate_kbps && s.bitrate_kbps !== 'Unknown' ? `<span class="badge badge-yellow" style="font-size:0.7rem;">${escHtml(String(s.bitrate_kbps))}</span>` : '—';
    const isActive = fp && fp === currentTrackPath;
    const rowClass = isActive ? ' class="player-row-active"' : '';
    const btnClass = isActive ? ' playing' : '';
    const btnIcon = isActive && isPlaying
      ? '<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px;"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
      : '<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px;"><polygon points="5 3 19 12 5 21 5 3"/></svg>';

    return `<tr data-filepath="${escHtml(fp)}"${rowClass}>
      <td style="color:var(--text-muted);font-size:0.75rem;">${i + 1}</td>
      <td title="${title}">${title}</td>
      <td class="col-hide-sm" title="${artist}">${artist}</td>
      <td class="col-hide-md" title="${album}">${album}</td>
      <td class="col-right col-hide-sm">${bitrate}</td>
      <td class="col-center" style="white-space:nowrap;">
        <button class="btn btn-secondary btn-sm btn-song-like ${likedSongPaths.has(fp) ? 'btn-liked' : ''}" data-filepath="${escHtml(fp)}" onclick="toggleLikeTrack('${escapeJs(fp)}', '${escapeJs(s.title || s.filename || '')}', '${escapeJs(s.artist || '')}')" title="${likedSongPaths.has(fp) ? 'Unlike' : 'Like'}" style="padding:0.25rem 0.4rem;margin-right:0.35rem;border-radius:6px;">${likedSongPaths.has(fp) ? SVG_HEART_FILLED : SVG_HEART}</button>
        <button class="player-row-play-btn${btnClass}" title="Play ${title}"
          onclick="playerTabPlaySong('${escapeJs(fp)}', ${i}, '${escapeJs(deviceId)}')">${btnIcon}</button>
      </td>
    </tr>`;
  });

  tbody.innerHTML = rows.join('');
}

/**
 * Play a song from the player tab, loading all filtered songs as the queue.
 */
function playerTabPlaySong(filepath, index, deviceId) {
  if (!playerTabFiltered || playerTabFiltered.length === 0) return;

  // Build queue with device_id on each entry
  const queue = playerTabFiltered.map(s => ({ ...s, device_id: deviceId || 'local' }));
  const track = queue[index] || queue[0];
  if (!track) return;

  // If shuffle was active, reset it since we're starting a new queue
  if (isShuffled) {
    isShuffled = false;
    originalQueue = [];
    const shuffleBtn = document.getElementById('btn-player-shuffle');
    if (shuffleBtn) shuffleBtn.classList.remove('shuffle-on');
  }

  playAudio(
    track.filepath || track._data,
    track.title,
    track.artist,
    queue,
    index,
    track.bitrate_kbps,
    deviceId
  );
}

/**
 * Play All — starts from the first song in the current filtered list.
 */
function playerPlayAll() {
  if (!playerTabFiltered || playerTabFiltered.length === 0) return;
  playerTabPlaySong(playerTabFiltered[0].filepath || playerTabFiltered[0]._data, 0, playerTabDeviceId);
}

/**
 * Shuffle All — plays the library in shuffled order starting from a random song.
 */
function playerShuffleAll() {
  if (!playerTabFiltered || playerTabFiltered.length === 0) return;
  const idx = Math.floor(Math.random() * playerTabFiltered.length);
  playerTabPlaySong(playerTabFiltered[idx].filepath || playerTabFiltered[idx]._data, idx, playerTabDeviceId);
  // After loading queue, enable shuffle
  if (!isShuffled) toggleShuffle();
}

/**
 * Filter the player-tab song list by the search box.
 */
function filterPlayerSongs() {
  const q = (document.getElementById('player-search')?.value || '').toLowerCase().trim();
  if (!q) {
    playerTabFiltered = [...playerTabSongs];
  } else {
    playerTabFiltered = playerTabSongs.filter(s =>
      (s.title || '').toLowerCase().includes(q) ||
      (s.artist || '').toLowerCase().includes(q) ||
      (s.album || '').toLowerCase().includes(q) ||
      (s.filename || '').toLowerCase().includes(q)
    );
  }
  const countEl = document.getElementById('player-song-count');
  if (countEl) {
    countEl.textContent = q
      ? `${playerTabFiltered.length} / ${playerTabSongs.length} songs`
      : `${playerTabSongs.length.toLocaleString()} songs`;
  }
  renderPlayerSongTable(playerTabFiltered, playerTabDeviceId);
}

/**
 * Update which row in the player-tab table is highlighted as "now playing".
 */
function updatePlayerTabRowHighlight() {
  const tbody = document.getElementById('player-songs-tbody');
  if (!tbody) return;
  tbody.querySelectorAll('tr[data-filepath]').forEach(row => {
    const fp = row.getAttribute('data-filepath');
    if (fp === currentTrackPath) {
      row.classList.add('player-row-active');
    } else {
      row.classList.remove('player-row-active');
    }
  });
}

/**
 * Render the queue panel with current activeQueue.
 */
function renderQueuePanel() {
  const list = document.getElementById('player-queue-list');
  const countEl = document.getElementById('player-queue-count');
  if (!list) return;

  if (!activeQueue || activeQueue.length === 0) {
    list.innerHTML = '<div class="text-muted" style="padding:1.5rem 1rem;text-align:center;font-size:0.85rem;">No tracks in queue yet.</div>';
    if (countEl) countEl.textContent = '';
    return;
  }

  if (countEl) countEl.textContent = `${activeQueue.length} tracks`;

  list.innerHTML = activeQueue.map((t, i) => {
    const isActive = i === queueIndex;
    const title = escHtml(t.title || t.filename || (t.filepath || '').split('/').pop() || 'Unknown');
    const artist = escHtml(t.artist || 'Unknown');
    const cls = isActive ? ' queue-active' : '';
    const prefix = isActive
      ? '<svg class="icon-svg" viewBox="0 0 24 24" fill="currentColor" style="width:10px;height:10px;flex-shrink:0;"><polygon points="5 3 19 12 5 21 5 3"/></svg>'
      : '';
    return `<div class="player-queue-item${cls}" onclick="playerQueueJumpTo(${i})" title="${title}">
      <span class="q-num">${prefix || (i + 1)}</span>
      <div class="q-info">
        <div class="q-title">${title}</div>
        <div class="q-artist">${artist}</div>
      </div>
    </div>`;
  }).join('');

  // Scroll active item into view
  const activeEl = list.querySelector('.queue-active');
  if (activeEl) activeEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

/**
 * Jump to a specific track in the active queue.
 */
function playerQueueJumpTo(index) {
  if (!activeQueue || index < 0 || index >= activeQueue.length) return;
  const t = activeQueue[index];
  playAudio(
    t.filepath || t._data,
    t.title,
    t.artist,
    activeQueue,
    index,
    t.bitrate_kbps,
    t.device_id
  );
}

/**
 * Clear the current play queue and stop playback.
 */
function clearPlayerQueue() {
  activeQueue = [];
  originalQueue = [];
  queueIndex = 0;
  isShuffled = false;
  const shuffleBtn = document.getElementById('btn-player-shuffle');
  if (shuffleBtn) shuffleBtn.classList.remove('shuffle-on');
  renderQueuePanel();
  closeAudioPlayer();
}

/** Simple HTML escaping helper (may already exist, this is safe to duplicate). */
function escHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ==========================================

// =============================================================================
// SESSION MANAGEMENT: SSE listener + heartbeat
// =============================================================================

let _sessionClientId = null;
let _sessionHeartbeatInterval = null;
let _sessionEventSource = null;

function startSessionSSE() {
  if (_sessionEventSource) return; // already connected
  _sessionClientId = 'web-' + Math.random().toString(36).slice(2);
  const url = `/api/session/events?client_id=${_sessionClientId}`;
  _sessionEventSource = new EventSource(url);

  _sessionEventSource.onopen = () => {
    console.log('[Session] SSE connected');
  };

  _sessionEventSource.onerror = () => {
    // Auto-reconnect handled by browser EventSource
    console.warn('[Session] SSE connection lost, will retry...');
  };

  _sessionEventSource.addEventListener('session_command', (e) => {
    try {
      const payload = JSON.parse(e.data);
      handleSessionCommand(payload);
    } catch (err) {
      console.error('[Session] Bad SSE payload', err);
    }
  });
}

function handleSessionCommand(payload) {
  const player = document.getElementById('audio-player');
  if (!player) return;
  const cmd = payload.cmd;
  console.log('[Session] Received command:', cmd, payload);

  switch (cmd) {
    case 'play':
      player.play().catch(() => {});
      break;
    case 'pause':
      player.pause();
      break;
    case 'next':
      if (typeof handleNextTrack === 'function') handleNextTrack();
      break;
    case 'prev':
      if (typeof handlePrevTrack === 'function') handlePrevTrack();
      break;
    case 'seek':
      if (payload.position_ms != null && player.duration) {
        player.currentTime = payload.position_ms / 1000;
      }
      break;
    case 'transfer':
      // Play a specific song (streamed from remote peer or from local path)
      if (payload.stream_url) {
        player.src = payload.stream_url;
        player.load();
        player.play().catch(() => {});
        if (payload.position_ms > 2000) {
          player.addEventListener('loadedmetadata', function seekOnLoad() {
            player.currentTime = payload.position_ms / 1000;
            player.removeEventListener('loadedmetadata', seekOnLoad);
          });
        }
        // Update UI if possible
        const titleEl = document.getElementById('player-title') || document.getElementById('bottom-bar-title');
        if (titleEl) titleEl.textContent = payload.title || 'Remote Track';
        const artistEl = document.getElementById('player-artist') || document.getElementById('bottom-bar-artist');
        if (artistEl) artistEl.textContent = payload.artist || '';
        if (typeof showToast === 'function') showToast(`Playing: ${payload.title}`);
      } else if (payload.filepath) {
        const encoded = encodeURIComponent(payload.filepath);
        player.src = `/api/song/stream?filepath=${encoded}`;
        player.load();
        player.play().catch(() => {});
        if (payload.position_ms > 2000) {
          player.addEventListener('loadedmetadata', function seekOnLoad() {
            player.currentTime = payload.position_ms / 1000;
            player.removeEventListener('loadedmetadata', seekOnLoad);
          });
        }
        const titleEl = document.getElementById('player-title') || document.getElementById('bottom-bar-title');
        if (titleEl) titleEl.textContent = payload.title || 'Remote Track';
        const artistEl = document.getElementById('player-artist') || document.getElementById('bottom-bar-artist');
        if (artistEl) artistEl.textContent = payload.artist || '';
        if (typeof showToast === 'function') showToast(`Playing: ${payload.title}`);
      }
      break;
    case 'queue_inject':
      // Add to queue - use existing queue mechanism if available
      if (typeof addToQueue === 'function' && payload.filepath) {
        addToQueue(payload.filepath, payload.title, payload.artist);
        if (typeof showToast === 'function') showToast(`Queued: ${payload.title}`);
      }
      break;
    default:
      console.warn('[Session] Unknown command:', cmd);
  }
}

function sendSessionHeartbeat() {
  const player = document.getElementById('audio-player');
  if (!player) return;
  
  // Gather current queue info from window.currentQueue if available
  const queueSize = (window.activeQueue || []).length;
  const isShuffled = window.isShuffled || false;
  const repeatMode = window.repeatMode || 'off';

  // Get current song info from DOM or window globals
  const titleEl = document.getElementById('player-title') || document.getElementById('bottom-bar-title');
  const artistEl = document.getElementById('player-artist') || document.getElementById('bottom-bar-artist');
  const currentTitle = (window.currentSong && window.currentSong.title) || (titleEl && titleEl.textContent) || '';
  const currentArtist = (window.currentSong && window.currentSong.artist) || (artistEl && artistEl.textContent) || '';
  const currentFilepath = (window.currentSong && window.currentSong.filepath) || '';

  const data = {
    is_playing: !player.paused && !player.ended,
    current_title: currentTitle,
    current_artist: currentArtist,
    current_filepath: currentFilepath,
    position_ms: Math.round((player.currentTime || 0) * 1000),
    duration_ms: Math.round((player.duration || 0) * 1000),
    queue_size: queueSize,
    repeat_mode: repeatMode,
    is_shuffled: isShuffled,
  };

  fetch('/api/session/heartbeat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    keepalive: true,
  }).catch(() => {}); // silent fail
}

function startSessionHeartbeat() {
  if (_sessionHeartbeatInterval) return;
  _sessionHeartbeatInterval = setInterval(sendSessionHeartbeat, 3000);
  sendSessionHeartbeat(); // immediate first send
}

// Export for use by app.js
window.startSessionSSE = startSessionSSE;
window.startSessionHeartbeat = startSessionHeartbeat;
window.handleSessionCommand = handleSessionCommand;
