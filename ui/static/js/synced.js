// =============================================================================
// SYNCED HISTORY MODULE: Synced Tracks Table & Status Tracking
// =============================================================================

async function loadSyncedHistory() {
  const tbody = document.getElementById('synced-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/synced');
    const records = await res.json();

    if (!records || records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No synced track history recorded in database/db.db.</td></tr>';
      return;
    }

    let html = '';
    records.forEach((r, idx) => {
      html += `
        <tr>
          <td class="col-center text-tabular">${idx + 1}</td>
          <td><strong style="color: var(--text-main);">${escapeHtml(r.filename)}</strong></td>
          <td class="col-center"><span class="badge badge-purple">${escapeHtml(r.device_serial)}</span></td>
          <td><small class="text-muted"><code style="word-break: break-all;">${escapeHtml(r.remote_dir || 'N/A')}</code></small></td>
          <td class="col-center text-tabular"><small class="text-muted">${escapeHtml(r.synced_at || '—')}</small></td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    console.error('Error loading synced history:', err);
  }
}

