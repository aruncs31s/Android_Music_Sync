"""
Ranger-Style Interactive Dual-Pane TUI for Music Folder Sync (-i).

Left Pane: Local files to sync with spacebar checkboxes [X].
Right Pane: Live fuzzy search results on connected ADB device for highlighted file.

Keybindings:
  Up / Down, k / j : Navigate file list
  Spacebar          : Toggle selection checkbox [X]
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


def run_ranger_sync_tui(
    to_sync_files: List[Dict[str, str]],
    device_songs: List[Dict[str, Any]],
    device_serial: str,
    remote_dir: str = "/storage/emulated/0/Music/ADB",
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ranger-style interactive dual-pane TUI for song sync.
    Returns summary dict of synced and skipped files.
    """
    if not to_sync_files:
        print("[RangerSync] No files to sync.", file=sys.stderr)
        return {"synced": [], "skipped": []}

    def _tui(stdscr):
        nonlocal to_sync_files
        curses.curs_set(0) # Hide cursor
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()

        # Color pairs
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Highlight left
        curses.init_pair(2, curses.COLOR_YELLOW, -1)                 # Headers & badges
        curses.init_pair(3, curses.COLOR_GREEN, -1)                  # Selected [X] check
        curses.init_pair(4, curses.COLOR_CYAN, -1)                   # Device search match
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)                # File sizes

        current_idx = 0
        scroll_offset = 0

        # State tracking: selected indices for sync, and marked/skipped items
        selected_set = set()
        synced_list = []
        skipped_list = []

        # Pre-cache search matches for each file to keep UI snappy
        match_cache = {}

        def get_device_matches(local_item: Dict[str, str]):
            fn = local_item["title_no_ext"]
            if fn not in match_cache:
                matches = fuzzy_matcher.filter_and_rank_songs(fn, device_songs)
                match_cache[fn] = matches[:8] # Top 8 matches
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
            right_header = " Device Search Preview (Matches) "
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

            # --- RENDER RIGHT PANE (Live Device Search Results) ---
            if 0 <= current_idx < len(to_sync_files):
                curr_item = to_sync_files[current_idx]
                matches = get_device_matches(curr_item)

                query_info = f"Query: {curr_item['title_no_ext']}"
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(2, right_x, query_info[:right_width-1])
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

                if not matches:
                    stdscr.addstr(4, right_x, "(No matching songs found on ADB device)", curses.A_DIM)
                    stdscr.addstr(6, right_x, "Press 's' to sync/upload this track.")
                else:
                    stdscr.addstr(3, right_x, f"Top Device Matches ({len(matches)} found):", curses.A_UNDERLINE)
                    for m_idx, song_match in enumerate(matches[:list_height - 3]):
                        row_y = m_idx + 4
                        m_title = song_match.get("title") or song_match.get("_display_name") or "Unknown"
                        m_artist = song_match.get("artist") or "Unknown Artist"
                        m_dur = song_match.get("duration_formatted") or ""
                        m_path = song_match.get("_data") or ""

                        m_line = f" {m_idx+1}. {m_title} - {m_artist} ({m_dur})"
                        m_line = m_line[:right_width - 1]

                        stdscr.attron(curses.color_pair(4))
                        stdscr.addstr(row_y, right_x, m_line)
                        stdscr.attroff(curses.color_pair(4))

            # Bottom Keybinding Footer
            footer = " [SPACE] Select/Unselect | [s] Sync Selected/Current | [m/ENTER] Mark Matched | [q] Quit "
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(height - 1, 0, footer[:width-1].ljust(width-1))
            stdscr.attroff(curses.A_REVERSE)

            stdscr.refresh()

            # Input Handling
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
                    for item in items_to_push:
                        pushed = adb_pusher.push_song_to_device(device_serial, item["path"], remote_dir, redis_cfg=redis_cfg)
                        if pushed:
                            synced_list.append(item)

                    pushed_paths = set(item["path"] for item in items_to_push)
                    to_sync_files[:] = [item for item in to_sync_files if item["path"] not in pushed_paths]
                    selected_set.clear()
                    current_idx = max(0, min(current_idx, len(to_sync_files) - 1))

                    input("\nPress ENTER to return to Ranger Sync UI...")
                    curses.reset_prog_mode()

        return {"synced": synced_list, "skipped": skipped_list}

    return fzf_tui.run_with_tty(_tui)
