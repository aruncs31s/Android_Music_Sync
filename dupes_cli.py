"""
Duplicate Cleaner CLI module.

Usage:
    python app.py --dupes                     Report duplicate clusters (no changes).
    python app.py --dupes -i                  Interactive cleanup — inspect clusters and
                                               choose which copies to delete.
    python app.py --dupes -d                  Immediately delete all but one copy per cluster.
    python app.py --dupes -af                 Use acoustic audio fingerprinting for detection.
    python app.py --dupes -d -af              Fingerprint detection + immediate cleanup.

Notes:
    -d (immediate delete) and -i/--interactive are mutually exclusive.
    By default one copy per cluster is kept — prioritising copies already present on the
    ADB device, then highest bitrate, largest file, and newest modification time.
    Deletions are always recoverable: files are moved to tmp/deleted and logged.
"""

import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import config_manager
import song_parser
import ui.stats_manager as ui_stats
from repositories import song_repo
from utils import get_logger
from utils.android.adb import adb_manager

logger = get_logger()


def _norm(s: str) -> str:
    """Normalize text for comparison (lowercase, alphanumeric only)."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _parse_bitrate(song: Dict[str, Any]) -> int:
    """Extract a numeric bitrate (kbps) from a song dict; -1 when unknown."""
    try:
        val = song.get("bitrate_val")
        if val:
            return int(val)
        m = re.search(r"(\d+(?:\.\d+)?)", str(song.get("bitrate_kbps") or ""))
        return int(float(m.group(1))) if m else -1
    except Exception:
        return -1


def _parse_size_bytes(song: Dict[str, Any]) -> int:
    """Extract a numeric file size (bytes) from a song dict; 0 when unknown."""
    try:
        size = song.get("size")
        if size is not None:
            return int(size)
    except Exception:
        pass
    m = re.search(
        r"([\d.]+)\s*(B|KB|MB|GB)", str(song.get("size_formatted") or "").upper()
    )
    if not m:
        return 0
    value, unit = float(m.group(1)), m.group(2)
    mult = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}[unit]
    return int(value * mult)


def get_device_filename_set(
    device_serial: Optional[str], redis_cfg: Optional[Dict[str, Any]]
) -> Set[str]:
    """
    Best-effort set of normalized audio filenames present on the target ADB device.
    Used to prefer keeping copies that already exist on the device.
    Returns an empty set if no serial is given or the device query fails.
    """
    if not device_serial:
        return set()
    try:
        raw = adb_manager.query_songs_from_device(
            device_serial, redis_cfg=redis_cfg, refresh_cache=False
        )
        songs = song_parser.parse_songs(raw)
        names = set()
        for s in songs:
            name = os.path.basename(s.get("_data") or s.get("_display_name") or "")
            if name:
                names.add(_norm(name))
        logger.info(
            f"[Dupes] Loaded {len(names)} device filenames from [{device_serial}] — used to prefer copies on device."
        )
        return names
    except Exception as e:
        logger.warning(
            f"[Dupes] Could not query device [{device_serial}] for keeper preference: {e}"
        )
        return set()


def pick_keeper(
    cluster_songs: List[Dict[str, Any]], device_filename_set: Set[str]
) -> Dict[str, Any]:
    """
    Select the single copy to keep from a duplicate cluster.
    Preference order: exists on ADB device -> highest bitrate -> largest file ->
    newest mtime. Ties break towards the first-listed song.
    """

    def key(s: Dict[str, Any]) -> Tuple:
        on_dev = int(
            _norm(os.path.basename(s.get("filepath") or "")) in device_filename_set
        )
        return (
            on_dev,
            _parse_bitrate(s),
            _parse_size_bytes(s),
            float(s.get("mtime") or 0),
        )

    best = sorted(cluster_songs, key=key, reverse=True)[0]
    keep_path = os.path.abspath(best.get("filepath") or "")
    same_path = [
        s
        for s in cluster_songs
        if os.path.abspath(s.get("filepath") or "") == keep_path
    ]
    return same_path[0] if same_path else best


def plan_deletions(dups: Dict[str, Any], device_filename_set: Set[str]):
    """
    Convert duplicate detection output into a concrete cleanup plan.
    Returns (plan, total_duplicate_files, freed_bytes) where plan is a list of
    dicts: {cluster, keep, delete: [song, ...]}.
    """
    plan: List[Dict[str, Any]] = []
    total_dup = 0
    freed = 0
    for cluster in dups.get("clusters") or []:
        songs = cluster.get("songs") or []
        if len(songs) < 2:
            continue
        keeper = pick_keeper(songs, device_filename_set)
        keeper_path = os.path.abspath(keeper.get("filepath") or "")
        deletes = [
            s for s in songs if os.path.abspath(s.get("filepath") or "") != keeper_path
        ]
        plan.append({"cluster": cluster, "keep": keeper, "delete": deletes})
        total_dup += len(deletes)
        freed += sum(_parse_size_bytes(s) for s in deletes)
    return plan, total_dup, freed


def _format_bytes(n: int) -> str:
    if n >= 1024**3:
        return f"{n / 1024**3:.2f} GB"
    if n >= 1024**2:
        return f"{n / 1024**2:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def _cluster_blocks(
    plan: List[Dict[str, Any]], device_filename_set: Set[str]
) -> List[str]:
    """Render readable text blocks describing each cluster in the cleanup plan."""
    blocks = []
    for idx, item in enumerate(plan, 1):
        cluster = item["cluster"]
        songs = cluster.get("songs") or []
        keeper_path = os.path.abspath(item["keep"].get("filepath") or "")
        header = (
            f"[{idx}/{len(plan)}] CLUSTER '{cluster.get('cluster_name', 'Untitled')}' "
            f"({cluster.get('match_type', 'match')}) — {len(songs)} copies, "
            f"{len(item['delete'])} to delete"
        )
        lines = [header, "=" * len(header)]
        for j, s in enumerate(songs, 1):
            path = s.get("filepath") or ""
            is_keep = os.path.abspath(path) == keeper_path
            on_dev = (
                "*ON-DEVICE*"
                if (_norm(os.path.basename(path)) in device_filename_set)
                else ""
            )
            mark = "*" if is_keep else " "
            meta = (
                f"{s.get('size_formatted') or _format_bytes(_parse_size_bytes(s))} | {s.get('bitrate_kbps') or 'Unknown'}"
                f" | {s.get('codec') or 'audio'} | {s.get('mtime_str') or 'Unknown'}"
            )
            lines.append(
                f"  {mark}[{j}] {os.path.basename(path) or path}  {on_dev}\n"
                f"      {meta}\n"
                f"      {path or 'Unknown path'}"
            )
        lines.append(
            f"      -> keep: {os.path.basename(keeper_path)} ({item['keep'].get('size_formatted') or ''})"
        )
        blocks.append("\n".join(lines))
    return blocks


def print_report(
    plan: List[Dict[str, Any]],
    device_filename_set: Set[str],
    total_dup: int = 0,
    freed: int = 0,
):
    """Print the duplicate cleanup plan report without deleting anything."""
    print("\n" + "=" * 70)
    print(
        f"            DUPLICATE FILES REPORT — {len(plan)} cluster(s), {total_dup} duplicate file(s)"
    )
    print("=" * 70)
    for block in _cluster_blocks(plan, device_filename_set):
        print()
        print(block)
    print()
    print(
        f"Summary: {len(plan)} cluster(s) — {total_dup} duplicate file(s), "
        f"~{_format_bytes(freed)} of duplicates would be moved to trash."
    )
    print(
        "No files deleted. Use --dupes -d to delete automatically, or --dupes -i interactively.\n"
    )


def run_interactive(
    plan: List[Dict[str, Any]], device_filename_set: Set[str]
) -> List[str]:
    """
    Interactively walk each cluster, show the data and let the user choose which
    copy to keep. Returns the list of filepaths scheduled for deletion.
    """
    deletes: List[str] = []
    print("\n" + "=" * 70)
    print("            INTERACTIVE DUPLICATE CLEANUP — choose which copy to keep")
    print("=" * 70)

    for idx, item in enumerate(plan, 1):
        cluster = item["cluster"]
        songs = cluster.get("songs") or []
        keeper_path = os.path.abspath(item["keep"].get("filepath") or "")

        print(
            f"\n[{idx}/{len(plan)}] CLUSTER '{cluster.get('cluster_name', 'Untitled')}' "
            f"({cluster.get('match_type', 'match')}) — {len(songs)} copies"
        )
        print("-" * 70)
        keep_index = 1
        for j, s in enumerate(songs, 1):
            path = s.get("filepath") or ""
            is_keep = os.path.abspath(path) == keeper_path
            on_dev = (
                "*ON-DEVICE*"
                if (_norm(os.path.basename(path)) in device_filename_set)
                else ""
            )
            if is_keep:
                keep_index = j
            mark = ">" if is_keep else " "
            print(
                f"  {mark}[{j}] {os.path.basename(path) or path} {on_dev}\n"
                f"        size={s.get('size_formatted') or '?'}  bitrate={s.get('bitrate_kbps') or '?'}  "
                f"codec={s.get('codec') or '?'}  modified={s.get('mtime_str') or '?'}\n"
                f"        {path}"
            )
        print("-" * 70)
        default_msg = f"({keep_index} = recommended)"

        while True:
            try:
                choice = (
                    input(
                        f"  Keep copy [1-{len(songs)}] {default_msg} | [s]kip cluster | [q]uit: "
                    )
                    .strip()
                    .lower()
                )
            except (KeyboardInterrupt, EOFError):
                print("\nAborted by user.")
                return deletes

            if choice in ("s", "skip"):
                print(
                    f"  Skipping cluster — nothing will be deleted from '{cluster.get('cluster_name', '')}'."
                )
                break
            if choice in ("q", "quit"):
                print("  Quitting interactive cleanup.")
                return deletes
            if choice in ("", "d", "default"):
                choice = str(keep_index)
            if choice.isdigit():
                chosen = int(choice)
                if 1 <= chosen <= len(songs):
                    chosen_path = os.path.abspath(
                        songs[chosen - 1].get("filepath") or ""
                    )
                    for s in songs:
                        p = os.path.abspath(s.get("filepath") or "")
                        if p != chosen_path and p not in deletes:
                            deletes.append(p)
                    n = len(songs) - 1
                    print(
                        f"  Marked {n} cop{'y' if n == 1 else 'ies'} for deletion (keeping "
                        f"'{os.path.basename(chosen_path)}')."
                    )
                    break
            print("  Invalid choice. Try again.")

    return deletes


def _confirm(prompt: str) -> bool:
    while True:
        try:
            ans = input(prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            return False
        if ans in ("", "y", "yes"):
            return True
        if ans in ("n", "no"):
            return False


def _delete_paths(paths: List[str], auto_confirm: bool = False) -> Dict[str, Any]:
    """Confirm (unless auto_confirm) and move the listed files to trash via song_repo."""
    if not paths:
        return {
            "status": "success",
            "deleted_count": 0,
            "failed": [],
            "message": "No files to delete",
        }

    total_size = 0
    for p in paths:
        try:
            total_size += os.path.getsize(p)
        except OSError:
            pass
    print(
        f"\nWill move {len(paths)} duplicate file(s) (~{_format_bytes(total_size)}) to the recoverable trash folder (tmp/deleted)."
    )

    if not auto_confirm and not _confirm("Proceed to delete these duplicates? [Y/n]: "):
        print("Cancelled — nothing was deleted.")
        return {
            "status": "cancelled",
            "deleted_count": 0,
            "failed": [],
            "message": "Cancelled by user",
        }

    result = song_repo.delete_songs_batch(paths)
    if result.get("deleted_count") is not None:
        print(f"Deleted {result['deleted_count']} duplicate file(s).")
    if result.get("failed"):
        print(f"Failed to delete {len(result['failed'])} file(s):")
        for f in result["failed"]:
            print(f"  - {f.get('filepath')}: {f.get('error')}")
    return result


def run_dupes_workflow(
    interactive: bool = False,
    immediate_delete: bool = False,
    use_fingerprint: bool = False,
    device_serial: Optional[str] = None,
    auto_confirm: bool = False,
    config_path: Optional[str] = None,
):
    """
    Main duplicate detection & cleanup workflow.

    - interactive=True: show each cluster and let the user pick which copies to delete.
    - immediate_delete=True: automatically delete all but one copy per cluster.
    - otherwise: print a report only (no changes).
    """
    if interactive and immediate_delete:
        print(
            "[Dupes] Error: -i (interactive) and -d (immediate delete) cannot be used together."
        )
        sys.exit(1)

    cfg = config_manager.load_config(config_path)
    redis_cfg = cfg.get("redis")

    print("=" * 70)
    print("              DUPLICATE DETECTOR", flush=True)
    print("=" * 70)
    print(
        f"[Dupes] Detection mode: {'acoustic audio fingerprinting' if use_fingerprint else 'tag & filename matching'}",
        flush=True,
    )
    print("[Dupes] Scanning local music library...", flush=True)
    songs = song_repo.get_all_songs(force_refresh=True)

    if not songs:
        print("[Dupes] No audio files found in configured music folders.")
        return

    print(f"[Dupes] Loaded {len(songs)} song(s) — detecting duplicates...", flush=True)
    dups = ui_stats.detect_duplicate_songs(songs, use_fingerprint=use_fingerprint)

    if dups.get("warning"):
        print(f"[Dupes] Warning: {dups['warning']}")

    clusters = dups.get("clusters") or []
    if not clusters:
        print("[Dupes] No duplicate clusters found — your library is clean.")
        return

    device_filename_set = get_device_filename_set(device_serial, redis_cfg)
    plan, total_dup, freed = plan_deletions(dups, device_filename_set)
    if not plan:
        print("[Dupes] No clusters with more than one copy remain.")
        return

    if interactive:
        paths = run_interactive(plan, device_filename_set)
        _delete_paths(paths, auto_confirm=auto_confirm)
        return

    if immediate_delete:
        print_report(plan, device_filename_set, total_dup, freed)
        all_paths: List[str] = []
        for item in plan:
            for s in item["delete"]:
                p = os.path.abspath(s.get("filepath") or "")
                if p not in all_paths:
                    all_paths.append(p)
        _delete_paths(all_paths, auto_confirm=auto_confirm)
        return

    print_report(plan, device_filename_set, total_dup, freed)

