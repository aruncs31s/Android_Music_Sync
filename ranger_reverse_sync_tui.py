"""
Ranger-Style Interactive Dual-Pane TUI for Reverse Sync (ADB Device -> Local Folder).

Left Pane: ADB Device songs missing locally with selection checkboxes [X].
Right Pane: Live fuzzy search results in local music folder for highlighted device song.

Keybindings:
  Up / Down, k / j : Navigate device songs list
  Spacebar          : Toggle selection checkbox [X]
  s / p             : Pull/download selected song(s) (or current item) from device -> local folder
  m / Enter         : Mark current device song as matched with local file (skip pull)
  q / ESC           : Exit interactive reverse sync UI
"""
import sys
import os
import curses
import subprocess
from typing import List, Dict, Any, Optional

import fuzzy_matcher
import fzf_tui


def run_ranger_reverse_sync_tui(
    missing_songs: List[Dict[str, Any]],
    local_files: List[Dict[str, str]],
    device_serial: str,
    local_dir: str = "/home/aruncs/Music",
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ranger-style interactive dual-pane TUI for reverse sync (ADB -> Local).
    Returns summary dict of pulled and skipped files.
    """
    if not missing_songs:
        print("[RangerReverseSync] No missing songs to pull from device.", file=sys.stderr)
        return {"pulled": [], "skipped": []}

    def _tui(stdscr):
        nonlocal missing_songs
        curses.curs_set(0) # Hide cursor
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Highlight left
        curses.init_pair(2, curses.COLOR_YELLOW, -1)                 # Headers & badges
        curses.init_pair(3, curses.COLOR_GREEN, -1)                  # Selected [X] check
        curses.init_pair(4, curses.COLOR_CYAN, -1)                   # Local search match

        current_idx = 0
        scroll_offset = 0

        selected_set = set()
        pulled_list = []
        skipped_list = []

        match_cache = {}

        def get_local_matches(device_item: Dict[str, Any]):
            query_str = device_item.get("title") or device_item.get("_display_name") or ""
            if query_str not in match_cache:
                matches = []
                for f in local_files:
                    title_no_ext = f["title_no_ext"]
                    m_matched, m_score, _ = fuzzy_matcher.fuzzy_subsequence_match(query_str, title_no_ext)
                    if m_matched:
                        matches.append((m_score, f))
                matches.sort(key=lambda x: x[0], reverse=True)
                match_cache[query_str] = [m[1] for m in matches[:8]]
            return match_cache[query_str]

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
            header = f" RANGER REVERSE SYNC (ADB -> Local) | Device: {device_serial} | Target: {local_dir} "
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(0, 0, header[:width-1].ljust(width-1))
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            # Pane Headers (Row 1)
            left_header = f" Device Songs Missing Locally ({len(missing_songs)}) [{len(selected_set)} selected] "
            right_header = " Local Folder Search Preview (Matches) "
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

            # --- RENDER LEFT PANE (Device Songs Missing Locally) ---
            for i in range(list_height):
                item_idx = scroll_offset + i
                if item_idx >= len(missing_songs):
                    break

                row_y = i + 2
                item = missing_songs[item_idx]
                is_selected = item_idx in selected_set
                check_str = "[X]" if is_selected else "[ ]"

                title = item.get("title") or item.get("_display_name") or "Unknown"
                artist = item.get("artist") or ""
                dur = item.get("duration_formatted") or ""

                line_str = f" {check_str} {item_idx+1:3d}. {title} - {artist} ({dur})"
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

            # --- RENDER RIGHT PANE (Live Local Search Results) ---
            if 0 <= current_idx < len(missing_songs):
                curr_item = missing_songs[current_idx]
                matches = get_local_matches(curr_item)

                title_query = curr_item.get("title") or curr_item.get("_display_name") or ""
                query_info = f"Query: {title_query}"
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(2, right_x, query_info[:right_width-1])
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

                remote_path = curr_item.get("_data") or ""
                if remote_path:
                    stdscr.addstr(3, right_x, f"Remote Path: {remote_path}"[:right_width-1], curses.A_DIM)

                if not matches:
                    stdscr.addstr(5, right_x, "(No matching files found in local music folder)", curses.A_DIM)
                    stdscr.addstr(7, right_x, "Press 's' or 'p' to pull this track from ADB device.")
                else:
                    stdscr.addstr(5, right_x, f"Top Local Matches ({len(matches)} found):", curses.A_UNDERLINE)
                    for m_idx, loc_match in enumerate(matches[:list_height - 5]):
                        row_y = m_idx + 6
                        m_line = f" {m_idx+1}. {loc_match['filename']} ({loc_match['size_formatted']})"
                        m_line = m_line[:right_width - 1]

                        stdscr.attron(curses.color_pair(4))
                        stdscr.addstr(row_y, right_x, m_line)
                        stdscr.attroff(curses.color_pair(4))

            # Bottom Keybinding Footer
            footer = " [SPACE] Select/Unselect | [s/p] Pull Selected/Current | [m/ENTER] Mark Matched | [q] Quit "
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
                if current_idx < len(missing_songs) - 1:
                    current_idx += 1
            elif key == ord(' '): # Spacebar toggles selection
                if current_idx in selected_set:
                    selected_set.remove(current_idx)
                else:
                    selected_set.add(current_idx)
                if current_idx < len(missing_songs) - 1:
                    current_idx += 1
            elif key in (ord('m'), 10, 13): # Mark / Enter (Skip as already matched)
                if 0 <= current_idx < len(missing_songs):
                    skipped_item = missing_songs.pop(current_idx)
                    skipped_list.append(skipped_item)
                    if selected_set:
                        selected_set = {idx - 1 if idx > current_idx else idx for idx in selected_set if idx != current_idx}
                    if current_idx >= len(missing_songs):
                        current_idx = max(0, len(missing_songs) - 1)
            elif key in (ord('s'), ord('p')): # Pull highlighted or selected item(s)
                items_to_pull = []
                if selected_set:
                    items_to_pull = [missing_songs[i] for i in sorted(selected_set)]
                elif 0 <= current_idx < len(missing_songs):
                    items_to_pull = [missing_songs[current_idx]]

                if items_to_pull:
                    curses.def_prog_mode()
                    curses.endwin()

                    print(f"\n[RangerReverseSync] Pulling {len(items_to_pull)} file(s) from device...", file=sys.stderr)
                    os.makedirs(local_dir, exist_ok=True)
                    for item in items_to_pull:
                        remote_path = item.get("_data")
                        display_name = item.get("_display_name") or f"song_{item.get('_id', 0)}.mp3"

                        if not remote_path:
                            continue

                        print(f"Pulling: {display_name} -> {local_dir}/", file=sys.stderr)
                        cmd = ["adb", "-s", device_serial, "pull", remote_path, os.path.join(local_dir, display_name)]
                        try:
                            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                            print(res.stdout.strip(), file=sys.stderr)
                            pulled_list.append(item)
                        except subprocess.CalledProcessError as e:
                            print(f"[ERROR] Failed to pull '{remote_path}': {e.stderr or e.stdout}", file=sys.stderr)

                    pulled_paths = set(item.get("_data") for item in items_to_pull)
                    missing_songs[:] = [item for item in missing_songs if item.get("_data") not in pulled_paths]
                    selected_set.clear()
                    current_idx = max(0, min(current_idx, len(missing_songs) - 1))

                    input("\nPress ENTER to return to Ranger Reverse Sync UI...")
                    curses.reset_prog_mode()

        return {"pulled": pulled_list, "skipped": skipped_list}

    return fzf_tui.run_with_tty(_tui)
