// =============================================================================
// SESSIONS MODULE: Multi-device session panel for web UI
// =============================================================================

function formatDurMs(ms) {
  if (isNaN(ms) || ms < 0) return '0:00';
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, '0')}`;
}

async function sendPeerSessionCommand(ip, port, cmd, body = null) {
  try {
    const res = await fetch('/api/session/peer-command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, port, cmd, body }),
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) {
      console.warn(`[Sessions] Command '${cmd}' to ${ip}:${port} returned HTTP ${res.status}`);
    }
  } catch (e) {
    console.warn(`[Sessions] Command '${cmd}' to ${ip}:${port} failed:`, e);
  }
}

function renderLocalSessionCard(local, container) {
  const state = (local && local.state) || {};
  const isPlaying = Boolean(state.is_playing);
  const title = state.current_title || 'Nothing playing';
  const artist = state.current_artist || 'Desktop Player';
  const posStr = formatDurMs(state.position_ms || 0);
  const durStr = formatDurMs(state.duration_ms || 0);
  const progress = state.duration_ms > 0
    ? Math.min(100, Math.round((state.position_ms / state.duration_ms) * 100))
    : 0;

  const cardId = 'session-card-local';
  const existing = document.getElementById(cardId);
  if (existing) existing.remove();

  const playIcon = isPlaying
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;

  const card = document.createElement('div');
  card.id = cardId;
  card.className = 'session-card';
  card.style.cssText = 'background:rgba(255, 204, 0, 0.05);border:1px solid rgba(255, 204, 0, 0.25);border-radius:10px;padding:14px;margin-bottom:12px;';

  card.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
      <span style="color:var(--yellow,#f0c040);">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
      </span>
      <div style="flex:1;">
        <div style="font-weight:bold;color:#fff;font-size:14px;">${escHtml(local.device_name || 'This Desktop')}</div>
        <div style="color:#888;font-size:11px;font-family:monospace;">Local Browser Player</div>
      </div>
      <span style="font-size:10px;font-weight:bold;padding:2px 8px;border-radius:4px;${
        isPlaying
          ? 'background:#1a3a1a;color:#4caf50;'
          : 'background:#2a2a1a;color:#f0c040;'
      }">${isPlaying ? 'PLAYING' : 'IDLE'}</span>
    </div>
    <div style="color:var(--yellow,#f0c040);font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escHtml(title)}</div>
    <div style="color:#888;font-size:11px;margin-bottom:8px;">${escHtml(artist)}</div>
    <div style="position:relative;height:4px;background:#333;border-radius:2px;margin-bottom:4px;">
      <div style="height:100%;width:${progress}%;background:var(--yellow,#f0c040);border-radius:2px;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:10px;color:#666;font-family:monospace;margin-bottom:10px;">
      <span>${posStr}</span><span>${durStr}</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
      <button class="sess-local-btn" data-action="prev" title="Previous" style="background:#222;border:1px solid #444;border-radius:6px;cursor:pointer;color:#ccc;padding:6px 10px;display:flex;align-items:center;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
      </button>
      <button class="sess-local-btn" data-action="toggle" title="Play/Pause" style="background:var(--yellow,#f0c040);border:none;cursor:pointer;border-radius:6px;padding:6px 12px;color:#000;display:flex;align-items:center;">
        ${playIcon}
      </button>
      <button class="sess-local-btn" data-action="next" title="Next" style="background:#222;border:1px solid #444;border-radius:6px;cursor:pointer;color:#ccc;padding:6px 10px;display:flex;align-items:center;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
      </button>
    </div>
  `;

  card.querySelectorAll('.sess-local-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const act = btn.dataset.action;
      if (act === 'toggle' && typeof togglePlayPause === 'function') togglePlayPause();
      else if (act === 'next' && typeof playNext === 'function') playNext();
      else if (act === 'prev' && typeof playPrevious === 'function') playPrevious();
      setTimeout(refreshSessionsPanel, 400);
    });
  });

  container.appendChild(card);
}

function renderSessionCard(state, peerIp, peerPort, containerId, alias = '', songCount = 0) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const isOnline = Boolean(state);
  const isPlaying = Boolean(state && state.is_playing);
  const deviceName = (state && state.device_name) || alias || `${peerIp}:${peerPort}`;
  const deviceRole = (state && state.device_role) || 'android';
  const title = (state && state.current_title) || (isOnline ? 'Idle' : 'Offline');
  const artist = (state && state.current_artist) || (songCount > 0 ? `${songCount} songs stored` : '');
  const posStr = formatDurMs((state && state.position_ms) || 0);
  const durStr = formatDurMs((state && state.duration_ms) || 0);
  const progress = (state && state.duration_ms > 0)
    ? Math.min(100, Math.round((state.position_ms / state.duration_ms) * 100))
    : 0;

  const cardId = `session-card-${peerIp.replace(/\./g, '-')}-${peerPort}`;
  const existing = document.getElementById(cardId);
  if (existing) existing.remove();

  const deviceIcon = deviceRole === 'desktop'
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>`;

  const playIcon = isPlaying
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;

  let statusBadge = '<span style="font-size:10px;font-weight:bold;padding:2px 8px;border-radius:4px;background:#3a1a1a;color:#ff5555;">OFFLINE</span>';
  if (isOnline) {
    if (isPlaying) {
      statusBadge = '<span style="font-size:10px;font-weight:bold;padding:2px 8px;border-radius:4px;background:#1a3a1a;color:#4caf50;">PLAYING</span>';
    } else {
      statusBadge = '<span style="font-size:10px;font-weight:bold;padding:2px 8px;border-radius:4px;background:#2a2a1a;color:#f0c040;">ONLINE</span>';
    }
  }

  const card = document.createElement('div');
  card.id = cardId;
  card.className = 'session-card';
  card.style.cssText = 'background:var(--bg-card,#1e1e1e);border:1px solid #333;border-radius:10px;padding:14px;margin-bottom:12px;';

  card.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
      <span style="color:var(--yellow,#f0c040);">${deviceIcon}</span>
      <div style="flex:1;">
        <div style="font-weight:bold;color:#fff;font-size:14px;">${escHtml(deviceName)}</div>
        <div style="color:#888;font-size:11px;font-family:monospace;">${peerIp}:${peerPort}${songCount > 0 ? ` • ${songCount} songs` : ''}</div>
      </div>
      ${statusBadge}
    </div>
    <div style="color:var(--yellow,#f0c040);font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escHtml(title)}</div>
    <div style="color:#888;font-size:11px;margin-bottom:8px;">${escHtml(artist)}</div>
    ${isOnline ? `
      <div style="position:relative;height:4px;background:#333;border-radius:2px;margin-bottom:4px;">
        <div style="height:100%;width:${progress}%;background:var(--yellow,#f0c040);border-radius:2px;"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:10px;color:#666;font-family:monospace;margin-bottom:10px;">
        <span>${posStr}</span><span>${durStr}</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <button class="sess-btn" data-cmd="prev" title="Previous on remote" style="background:#222;border:1px solid #444;border-radius:6px;cursor:pointer;color:#ccc;padding:6px 10px;display:flex;align-items:center;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
        </button>
        <button class="sess-btn sess-playpause" data-cmd="${isPlaying ? 'pause' : 'play'}" title="Play/Pause remote" style="background:var(--yellow,#f0c040);border:none;cursor:pointer;border-radius:6px;padding:6px 12px;color:#000;display:flex;align-items:center;">
          ${playIcon}
        </button>
        <button class="sess-btn" data-cmd="next" title="Next on remote" style="background:#222;border:1px solid #444;border-radius:6px;cursor:pointer;color:#ccc;padding:6px 10px;display:flex;align-items:center;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
        </button>
        <div style="flex:1;"></div>
        ${state && state.current_filepath ? `
          <button class="sess-transfer-btn" style="background:#1e1e2e;border:1px solid #444;border-radius:6px;color:var(--yellow,#f0c040);font-size:11px;font-weight:bold;cursor:pointer;padding:6px 12px;">Play Here</button>
        ` : ''}
        <button class="sess-lib-btn" style="background:#222;border:1px solid #555;border-radius:6px;color:#fff;font-size:11px;cursor:pointer;padding:6px 10px;">Library &gt;</button>
      </div>
    ` : ''}
  `;

  // Bind remote control buttons
  card.querySelectorAll('.sess-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const cmd = btn.dataset.cmd;
      await sendPeerSessionCommand(peerIp, peerPort, cmd);
      setTimeout(refreshSessionsPanel, 600);
    });
  });

  // Transfer playback locally
  card.querySelector('.sess-transfer-btn')?.addEventListener('click', async () => {
    if (!state || !state.current_filepath) return;
    await sendPeerSessionCommand(peerIp, peerPort, 'pause');
    const streamUrl = `/api/song/stream?filepath=${encodeURIComponent(state.current_filepath)}&device_id=ip_${peerIp}`;
    const player = document.getElementById('audio-player');
    const playerBar = document.getElementById('audio-player-bar');
    if (player) {
      player.src = streamUrl;
      player.load();
      player.play().catch(() => {});
      if (state.position_ms > 2000 && state.duration_ms > 0) {
        player.addEventListener('loadedmetadata', function seekOnce() {
          player.currentTime = state.position_ms / 1000;
          player.removeEventListener('loadedmetadata', seekOnce);
        });
      }
      if (playerBar) playerBar.style.display = 'flex';
      const titleEl = document.getElementById('player-title');
      const artistEl = document.getElementById('player-artist');
      if (titleEl) titleEl.textContent = state.current_title;
      if (artistEl) artistEl.textContent = `${state.current_artist} • (${deviceName})`;
      if (typeof showToast === 'function') showToast(`Playing on desktop: ${state.current_title}`);
    }
  });

  // Open device library
  card.querySelector('.sess-lib-btn')?.addEventListener('click', () => {
    if (typeof openDeviceLibrary === 'function') {
      openDeviceLibrary(`ip_${peerIp}`, deviceName);
    }
  });

  container.appendChild(card);
}

let _sessionRefreshTimer = null;

async function refreshSessionsPanel() {
  const container = document.getElementById('sessions-panel-cards');
  const emptyEl = document.getElementById('sessions-panel-empty');
  if (!container) return;

  try {
    const res = await fetch('/api/session/peers', { signal: AbortSignal.timeout(3500) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    container.innerHTML = '';

    // 1. Render Local Desktop session
    if (data.local) {
      renderLocalSessionCard(data.local, container);
    }

    // 2. Render Over-IP Peer sessions
    const peers = data.peers || [];
    let peerCount = 0;
    for (const p of peers) {
      renderSessionCard(p.state, p.ip, p.port, 'sessions-panel-cards', p.device_name, p.song_count);
      peerCount++;
    }

    if (emptyEl) {
      if (peerCount === 0 && !data.local) {
        emptyEl.textContent = 'No active sessions or discovered devices. Connect companion app to the same Wi-Fi.';
        emptyEl.style.display = 'block';
      } else {
        emptyEl.style.display = 'none';
      }
    }
  } catch (err) {
    console.debug('[Sessions] Could not refresh sessions:', err);
    if (emptyEl && container.children.length === 0) {
      emptyEl.textContent = 'Unable to fetch sessions. Retrying...';
      emptyEl.style.display = 'block';
    }
  }
}

function initSessionsPanel() {
  // Start SSE + heartbeat for desktop browser player
  if (typeof startSessionSSE === 'function') startSessionSSE();
  if (typeof startSessionHeartbeat === 'function') startSessionHeartbeat();

  // Initial load
  refreshSessionsPanel();

  // Refresh button
  const refreshBtn = document.getElementById('btn-sessions-refresh');
  if (refreshBtn) refreshBtn.addEventListener('click', refreshSessionsPanel);

  // Auto-refresh every 5 seconds while panel or overview tab is visible
  if (_sessionRefreshTimer) clearInterval(_sessionRefreshTimer);
  _sessionRefreshTimer = setInterval(() => {
    const panel = document.getElementById('sessions-panel');
    if (panel && panel.offsetParent !== null) {
      refreshSessionsPanel();
    }
  }, 5000);
}

// Ensure escHtml is available
if (typeof escHtml === 'undefined') {
  window.escHtml = function(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  };
}

window.refreshSessionsPanel = refreshSessionsPanel;
window.initSessionsPanel = initSessionsPanel;
