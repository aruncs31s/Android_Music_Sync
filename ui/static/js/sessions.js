// =============================================================================
// SESSIONS MODULE: Multi-device session panel for web UI
// =============================================================================

function formatDurMs(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, '0')}`;
}

async function fetchPeerSessionState(ip, port) {
  try {
    const res = await fetch(`http://${ip}:${port}/api/session/state`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

async function sendPeerSessionCommand(ip, port, cmd, body = null) {
  try {
    await fetch(`http://${ip}:${port}/api/session/${cmd}`, {
      method: 'POST',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(5000),
    });
  } catch (e) {
    console.warn(`[Sessions] Command '${cmd}' to ${ip}:${port} failed:`, e);
  }
}

function renderSessionCard(state, peerIp, peerPort, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const progress = state.duration_ms > 0
    ? Math.round((state.position_ms / state.duration_ms) * 100)
    : 0;

  const isPlaying = state.is_playing;
  const deviceName = state.device_name || `${peerIp}:${peerPort}`;
  const deviceRole = state.device_role || 'android';
  const title = state.current_title || 'Nothing playing';
  const artist = state.current_artist || '';
  const posStr = formatDurMs(state.position_ms || 0);
  const durStr = formatDurMs(state.duration_ms || 0);

  const cardId = `session-card-${peerIp.replace(/\./g, '-')}-${peerPort}`;
  const existing = document.getElementById(cardId);
  if (existing) existing.remove();

  const deviceIcon = deviceRole === 'desktop'
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>`;

  const playIcon = isPlaying
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;

  const card = document.createElement('div');
  card.id = cardId;
  card.className = 'session-card';
  card.style.cssText = 'background:var(--bg-card,#1e1e1e);border:1px solid #333;border-radius:10px;padding:14px;margin-bottom:12px;';

  card.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
      <span style="color:var(--yellow,#f0c040);">${deviceIcon}</span>
      <div style="flex:1;">
        <div style="font-weight:bold;color:#fff;font-size:14px;">${escHtml(deviceName)}</div>
        <div style="color:#888;font-size:11px;font-family:monospace;">${peerIp}:${peerPort}</div>
      </div>
      <span style="font-size:10px;font-weight:bold;padding:3px 8px;border-radius:4px;${
        isPlaying
          ? 'background:#1a3a1a;color:#4caf50;'
          : 'background:#2a2a1a;color:#f0c040;'
      }">${isPlaying ? 'PLAYING' : 'PAUSED'}</span>
    </div>
    <div style="color:var(--yellow,#f0c040);font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escHtml(title)}</div>
    <div style="color:#888;font-size:11px;margin-bottom:8px;">${escHtml(artist)}</div>
    <div style="position:relative;height:4px;background:#333;border-radius:2px;margin-bottom:4px;">
      <div style="height:100%;width:${progress}%;background:var(--yellow,#f0c040);border-radius:2px;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:10px;color:#666;font-family:monospace;margin-bottom:12px;">
      <span>${posStr}</span><span>${durStr}</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
      <button class="sess-btn" data-cmd="prev" style="background:transparent;border:none;cursor:pointer;color:#ccc;padding:4px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
      </button>
      <button class="sess-btn sess-playpause" data-cmd="${isPlaying ? 'pause' : 'play'}" style="background:var(--yellow,#f0c040);border:none;cursor:pointer;border-radius:50%;padding:8px;color:#000;">
        ${playIcon}
      </button>
      <button class="sess-btn" data-cmd="next" style="background:transparent;border:none;cursor:pointer;color:#ccc;padding:4px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
      </button>
      <div style="flex:1;"></div>
      <button class="sess-transfer-btn" style="background:#1e1e2e;border:1px solid #444;border-radius:6px;color:var(--yellow,#f0c040);font-size:11px;font-weight:bold;cursor:pointer;padding:6px 12px;">Play Here</button>
    </div>
  `;

  // Bind control buttons
  card.querySelectorAll('.sess-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const cmd = btn.dataset.cmd;
      await sendPeerSessionCommand(peerIp, peerPort, cmd);
      setTimeout(() => refreshSessionsPanel(), 800);
    });
  });

  card.querySelector('.sess-transfer-btn')?.addEventListener('click', async () => {
    if (!state.current_filepath) return;
    // Pause remote
    await sendPeerSessionCommand(peerIp, peerPort, 'pause');
    // Build stream URL
    const streamUrl = `http://${peerIp}:${peerPort}/api/song/stream?filepath=${encodeURIComponent(state.current_filepath)}`;
    // Play locally via our own player
    const player = document.getElementById('audio-player');
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
      // Update title/artist in player UI
      const titleEl = document.getElementById('player-title') || document.getElementById('bottom-bar-title');
      if (titleEl) titleEl.textContent = state.current_title;
      const artistEl = document.getElementById('player-artist') || document.getElementById('bottom-bar-artist');
      if (artistEl) artistEl.textContent = state.current_artist;
      if (typeof showToast === 'function') showToast(`Playing here: ${state.current_title}`);
    }
  });

  container.appendChild(card);
}

let _sessionRefreshTimer = null;

async function refreshSessionsPanel() {
  const container = document.getElementById('sessions-panel-cards');
  const emptyEl = document.getElementById('sessions-panel-empty');
  if (!container) return;

  container.innerHTML = '';

  // Get discovered peers from overview.js peerDiscovery or the sync tab
  const peers = window.lastDiscoveredPeers || [];

  if (peers.length === 0) {
    if (emptyEl) {
      emptyEl.textContent = 'No peers discovered. Use the Overview tab to scan for devices first.';
      emptyEl.style.display = 'block';
    }
    return;
  }

  if (emptyEl) emptyEl.style.display = 'none';

  for (const peer of peers) {
    const state = await fetchPeerSessionState(peer.ip, peer.port);
    if (state) {
      renderSessionCard(state, peer.ip, peer.port, 'sessions-panel-cards');
    }
  }

  // Also show our own desktop session state
  try {
    const ownState = await fetch('/api/session/state').then(r => r.json());
    ownState.device_name = (ownState.device_name || window.location.hostname) + ' (This Desktop)';
    // Render own state at top if there is content
    const ownCard = document.createElement('div');
    ownCard.id = 'session-card-local';
    ownCard.style.cssText = 'background:#101020;border:2px solid var(--yellow,#f0c040);border-radius:10px;padding:14px;margin-bottom:12px;';
    ownCard.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f0c040" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        <span style="font-weight:bold;color:#fff;">${escHtml(ownState.device_name)}</span>
        <span style="margin-left:auto;font-size:10px;font-weight:bold;padding:2px 8px;border-radius:4px;background:#1a1a2a;color:#f0c040;">THIS DEVICE</span>
      </div>
      <div style="color:#f0c040;font-size:13px;font-weight:600;">${escHtml(ownState.current_title || 'Nothing playing')}</div>
      <div style="color:#888;font-size:11px;">${escHtml(ownState.current_artist || '')}</div>
    `;
    container.prepend(ownCard);
  } catch { /* ignore */ }
}

function initSessionsPanel() {
  // Start SSE + heartbeat
  if (typeof startSessionSSE === 'function') startSessionSSE();
  if (typeof startSessionHeartbeat === 'function') startSessionHeartbeat();

  // Initial load
  refreshSessionsPanel();

  // Refresh button
  const refreshBtn = document.getElementById('btn-sessions-refresh');
  if (refreshBtn) refreshBtn.addEventListener('click', refreshSessionsPanel);

  // Auto-refresh every 10 seconds while panel visible
  _sessionRefreshTimer = setInterval(() => {
    const panel = document.getElementById('sessions-panel');
    if (panel && panel.style.display !== 'none' && panel.offsetParent !== null) {
      refreshSessionsPanel();
    }
  }, 10000);
}

// Helper: ensure escHtml is available
if (typeof escHtml === 'undefined') {
  window.escHtml = function(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  };
}

window.refreshSessionsPanel = refreshSessionsPanel;
window.initSessionsPanel = initSessionsPanel;
