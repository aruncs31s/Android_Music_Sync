/**
 * @deprecated Legacy monolithic script.
 * The dashboard frontend has been modularized into separate, single-responsibility files in /static/js/:
 *  - core.js        (icons, escaping, toast notifications, confirmation dialog, theme, tabs)
 *  - overview.js    (metrics stats, device breakdown, over-IP peer scanner)
 *  - player.js      (audio player engine, bottom playback bar, queue, shuffle, liked songs)
 *  - library.js     (library table, filters, sorting, pagination, multi-select, transcode, upload)
 *  - duplicates.js  (duplicate detection, audio fingerprints, strategies, batch deletion)
 *  - sync.js        (sync planner, device diff table, selective push, single track modal)
 *  - synced.js      (synced history table, status tracking)
 *  - playlists.js   (playlist CRUD, tracks view, absent song badges & resolution)
 *  - trash.js       (deleted songs log, restore, purge trash, hide list)
 *  - poweramp.js    (backup importer, report modal, candidate resolver)
 *  - app.js         (DOMContentLoaded bootstrap)
 *
 * If this file is requested directly by legacy clients or cached browsers,
 * it dynamically loads the modular scripts in dependency sequence.
 */
(function() {
  const scripts = [
    'core.js',
    'overview.js',
    'player.js',
    'library.js',
    'duplicates.js',
    'sync.js',
    'synced.js',
    'playlists.js',
    'trash.js',
    'poweramp.js',
    'app.js'
  ];

  // Only inject if not already loaded by base.html
  if (typeof initTabs === 'undefined') {
    scripts.forEach(file => {
      const s = document.createElement('script');
      s.src = '/static/js/' + file;
      s.defer = true;
      document.head.appendChild(s);
    });
  }
})();
