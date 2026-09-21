"""
Forwarding shim for utils.syncer -> services.syncer.
Maintains 100% backward compatibility for all callers and tests.
"""
from services.syncer import *
import services.syncer as _syncer

# Re-export module-level attributes
scan_local_music_folder = _syncer.scan_local_music_folder
compare_local_files_with_device = _syncer.compare_local_files_with_device
run_sync_workflow = _syncer.run_sync_workflow
DEFAULT_AUDIO_EXTENSIONS = _syncer.DEFAULT_AUDIO_EXTENSIONS
