// =============================================================================
// APP BOOTSTRAP: DOMContentLoaded Initialization & Feature Coordination
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
  if (typeof initTheme === 'function') initTheme();
  
  const fpToggle = document.getElementById('toggle-use-fingerprints');
  if (fpToggle) {
    fpToggle.checked = useAudioFingerprinting;
  }
  
  if (typeof initTabs === 'function') initTabs();
  if (typeof initAudioPlayer === 'function') initAudioPlayer();
  if (typeof initPlayerTab === 'function') initPlayerTab();
  if (typeof loadDashboardStats === 'function') loadDashboardStats();
  if (typeof loadSongs === 'function') loadSongs();
  if (typeof loadDuplicates === 'function') loadDuplicates();
  if (typeof loadHiddenFiles === 'function') loadHiddenFiles();
  if (typeof loadSyncedHistory === 'function') loadSyncedHistory();
  if (typeof loadPlaylists === 'function') loadPlaylists();
  if (typeof loadLikedMusicSet === 'function') loadLikedMusicSet();
  if (typeof loadSyncDevices === 'function') loadSyncDevices();
  if (typeof loadDeletedSongs === 'function') loadDeletedSongs();
  if (typeof initSessionsPanel === 'function') initSessionsPanel();
});
