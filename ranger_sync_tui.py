"""
Ranger-Style Interactive Dual-Pane TUI for Music Folder Sync (-i).

Left Pane: Local files to sync with spacebar checkboxes [X].
Right Pane: Live fuzzy search results on connected ADB device + technical Audio Metadata (Bit Rate, Sample Rate, Codec).

Keybindings:
  Up / Down, k / j : Navigate file list
  Spacebar          : Toggle selection checkbox [X]
  h                 : Hide current file (Persists in SQLite hide_list_db)
  s                 : Sync/upload selected file(s) (or current item) to device
  m / Enter         : Mark current file as matched with device (skip upload)
  q / ESC           : Exit interactive sync UI
"""
import sys
import os
import curses
from typing import List, Dict, Any, Optional

import fuzzy_matcher
import adb_pusher
import fzf_tui
import audio_metadata
import hide_list_db


def run_ranger_sync_tui(
    to_sync_files: List[Dict[str, str]],
    device_songs: List[Dict[str, Any]],
    device_serial: str,
    remote_dir: str = "/storage/emulated/0/Music/ADB",
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ranger-style interactive dual-pane TUI for song sync.
    Returns summary dict of synced, skipped, and hidden files.
    """
    if not to_sync_files:
        print("[RangerSync] No files to sync.", file=sys.stderr)
        return {"synced": [], "skipped": [], "hidden": []}

    def _tui(stdscr):
        nonlocal to_sync_files
        curses.curs_set(0) # Hide cursor
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Highlight left
        curses.init_pair(2, curses.COLOR_YELLOW, -1)                 # Headers & badges
        curses.init_pair(3, curses.COLOR_GREEN, -1)                  # Selected [X] check
        curses.init_pair(4, curses.COLOR_CYAN, -1)                   # Device search match
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)                # Technical metadata

        current_idx = 0
        scroll_offset = 0

        selected_set = set()
        synced_list = []
        skipped_list = []
        hidden_list = []

        match_cache = {}

        def get_device_matches(local_item: Dict[str, str]):
            fn = local_item["title_no_ext"]
            if fn not in match_cache:
                matches = fuzzy_matcher.filter_and_rank_songs(fn, device_songs)
                match_cache[fn] = matches[:6]
            return match_cache[fn]

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            if height < 6 or width < 40:
                stdscr.addstr(0, 0, "Terminal window too small!")
                stdscr.refresh()
                key = stdscr.getch()
                if key in (27, ord('q')):
                    break
                continue

            left_width = width // 2
            right_x = left_width + 1
            right_width = width - right_x - 1

            # Top Header Bar
            header = f" RANGER INTERACTIVE SYNC [-i] | Device: {device_serial} | Target: {remote_dir} "
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(0, 0, header[:width-1].ljust(width-1))
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            # Pane Headers (Row 1)
            left_header = f" Local Files ({len(to_sync_files)}) [{len(selected_set)} selected] "
            right_header = " Technical Audio Specs & Device Matches "
            stdscr.addstr(1, 0, left_header[:left_width-1].ljust(left_width-1), curses.A_REVERSE)
            stdscr.addstr(1, right_x, right_header[:right_width-1].ljust(right_width-1), curses.A_REVERSE)

            # Vertical separator bar
            for y in range(1, height - 1):
                try:
                    stdscr.addstr(y, left_width, "│")
                except curses.error:
                    pass

            list_height = height - 3

            # Scroll bounds checking
            if current_idx < scroll_offset:
                scroll_offset = current_idx
            elif current_idx >= scroll_offset + list_height:
                scroll_offset = current_idx - list_height + 1

            # --- RENDER LEFT PANE (Local Files) ---
            for i in range(list_height):
                item_idx = scroll_offset + i
                if item_idx >= len(to_sync_files):
                    break

                row_y = i + 2
                item = to_sync_files[item_idx]
                is_selected = item_idx in selected_set
                check_str = "[X]" if is_selected else "[ ]"

                filename = item["filename"]
                line_str = f" {check_str} {item_idx+1:3d}. {filename}"
                line_str = line_str[:left_width - 2].ljust(left_width - 2)

                if item_idx == current_idx:
                    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    stdscr.addstr(row_y, 0, line_str)
                    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
                else:
                    if is_selected:
                        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                        stdscr.addstr(row_y, 0, line_str)
                        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
                    else:
                        stdscr.addstr(row_y, 0, line_str)

            # --- RENDER RIGHT PANE (Audio Metadata & Device Search Results) ---
            if 0 <= current_idx < len(to_sync_files):
                curr_item = to_sync_files[current_idx]
                matches = get_device_matches(curr_item)

                meta = audio_metadata.extract_audio_metadata(curr_item["path"])

                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(2, right_x, f"File Specs: {curr_item['filename']}"[:right_width-1])
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

                spec_line_1 = f"   • Bit Rate   : {meta['bitrate']}   |   Sample Rate: {meta['sample_rate']}"
                spec_line_2 = f"   • Codec      : {meta['codec']}   |   Channels   : {meta['channels']}"
                spec_line_3 = f"   • Duration   : {meta['duration']}   |   File Size  : {meta['size']}"

                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(3, right_x, spec_line_1[:right_width-1])
                stdscr.addstr(4, right_x, spec_line_2[:right_width-1])
                stdscr.addstr(5, right_x, spec_line_3[:right_width-1])
                stdscr.attroff(curses.color_pair(5))

                stdscr.addstr(6, right_x, "─" * (right_width - 1))

                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(7, right_x, f"Top Device Matches ({len(matches)} found):"[:right_width-1])
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

                if not matches:
                    stdscr.addstr(9, right_x, "(No matching songs found on ADB device)", curses.A_DIM)
                    stdscr.addstr(11, right_x, "Press 's' to sync/upload this track.")
                else:
                    for m_idx, song_match in enumerate(matches[:list_height - 9]):
                        row_y = m_idx + 9
                        m_title = song_match.get("title") or song_match.get("_display_name") or "Unknown"
                        m_artist = song_match.get("artist") or "Unknown Artist"
                        m_dur = song_match.get("duration_formatted") or ""

                        m_line = f" {m_idx+1}. {m_title} - {m_artist} ({m_dur})"
                        m_line = m_line[:right_width - 1]

                        stdscr.attron(curses.color_pair(4))
                        stdscr.addstr(row_y, right_x, m_line)
                        stdscr.attroff(curses.color_pair(4))

            # Bottom Keybinding Footer
            footer = " [SPACE] Select | [s] Sync | [h] Hide (SQLite DB) | [m/ENTER] Mark | [q] Quit "
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(height - 1, 0, footer[:width-1].ljust(width-1))
            stdscr.attroff(curses.A_REVERSE)

            stdscr.refresh()

            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                break

            if key in (27, ord('q')): # ESC / q
                break
            elif key in (curses.KEY_UP, ord('k')):
                if current_idx > 0:
                    current_idx -= 1
            elif key in (curses.KEY_DOWN, ord('j')):
                if current_idx < len(to_sync_files) - 1:
                    current_idx += 1
            elif key == ord(' '): # Spacebar toggles selection
                if current_idx in selected_set:
                    selected_set.remove(current_idx)
                else:
                    selected_set.add(current_idx)
                if current_idx < len(to_sync_files) - 1:
                    current_idx += 1
            elif key == ord('h'): # Hide file and persist to SQLite DB
                if 0 <= current_idx < len(to_sync_files):
                    h_item = to_sync_files.pop(current_idx)
                    hide_list_db.add_hidden_file(h_item["path"], h_item["filename"])
                    hidden_list.append(h_item)
                    if selected_set:
                        selected_set = {idx - 1 if idx > current_idx else idx for idx in selected_set if idx != current_idx}
                    if current_idx >= len(to_sync_files):
                        current_idx = max(0, len(to_sync_files) - 1)
            elif key in (ord('m'), 10, 13): # Mark / Enter (Skip as already matched)
                if 0 <= current_idx < len(to_sync_files):
                    skipped_item = to_sync_files.pop(current_idx)
                    skipped_list.append(skipped_item)
                    if selected_set:
                        selected_set = {idx - 1 if idx > current_idx else idx for idx in selected_set if idx != current_idx}
                    if current_idx >= len(to_sync_files):
                        current_idx = max(0, len(to_sync_files) - 1)
            elif key == ord('s'): # Sync highlighted or selected item(s)
                items_to_push = []
                if selected_set:
                    items_to_push = [to_sync_files[i] for i in sorted(selected_set)]
                elif 0 <= current_idx < len(to_sync_files):
                    items_to_push = [to_sync_files[current_idx]]

                if items_to_push:
                    curses.def_prog_mode()
                    curses.endwin()

                    print(f"\n[RangerSync] Syncing {len(items_to_push)} file(s) to device...", file=sys.stderr)
                    synced_this_batch = []
                    for item in items_to_push:
                        try:
                            pushed = adb_pusher.push_song_to_device(device_serial, item["path"], remote_dir, redis_cfg=redis_cfg)
                        except Exception as e:
                            pushed = False
                            print(f"[ERROR] Failed to push '{item.get('filename')}': {e}", file=sys.stderr)
                        if pushed:
                            synced_list.append(item)
                            synced_this_batch.append(item)
                        else:
                            print(f"[ERROR] Failed to push '{item.get('filename')}'", file=sys.stderr)

                    # Only remove files that were actually pushed successfully.
                    pushed_paths = set(item["path"] for item in synced_this_batch)
                    to_sync_files[:] = [item for item in to_sync_files if item["path"] not in pushed_paths]
                    selected_set.clear()
                    current_idx = max(0, min(current_idx, len(to_sync_files) - 1))

                    input("\nPress ENTER to return to Ranger Sync UI...")
                    curses.reset_prog_mode()

        return {"synced": synced_list, "skipped": skipped_list, "hidden": hidden_list}

    return fzf_tui.run_with_tty(_tui)
