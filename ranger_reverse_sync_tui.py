"""
Ranger-Style Interactive Dual-Pane TUI for Reverse Sync (ADB Device -> Local Folder).

Left Pane: ADB Device songs missing locally with selection checkboxes [X].
Right Pane: Detailed Device Song Metadata + Live local search matches with Bit Rate, Sample Rate, and Codec.

Keybindings:
  Up / Down, k / j : Navigate device songs list
  Spacebar          : Toggle selection checkbox [X]
  h                 : Hide current track (Persists in SQLite hide_list_db)
  s / p             : Pull/download selected song(s) (or current item) from device -> local folder
  m / Enter         : Mark current device song as matched with local file (skip pull)
  q / ESC           : Exit interactive reverse sync UI
"""
import sys
import os
import curses
import subprocess
from typing import List, Dict, Any, Optional, Callable

import fuzzy_matcher
import fzf_tui
import audio_metadata
import hide_list_db
from utils import get_logger
logger = get_logger()


def run_ranger_reverse_sync_tui(
    missing_songs: List[Dict[str, Any]],
    local_files: List[Dict[str, str]],
    device_serial: str,
    local_dir: str = "/home/aruncs/Music",
    redis_cfg: Optional[Dict[str, Any]] = None,
    pull_callback: Optional[Callable[[Dict[str, Any]], bool]] = None
) -> Dict[str, Any]:
    """
    Ranger-style interactive dual-pane TUI for reverse sync (ADB -> Local).
    Returns summary dict of pulled, skipped, and hidden files.

    If `pull_callback` is provided it is invoked for each selected item instead of
    `adb pull`; it must return True on success. This lets callers (e.g. the Over-IP
    HTTP workflow) reuse the selection UI with their own transfer method.
    """
    if not missing_songs:
        logger.info("[RangerReverseSync] No missing songs to pull from device.")
        return {"pulled": [], "skipped": [], "hidden": []}

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
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)                # Technical metadata

        current_idx = 0
        scroll_offset = 0

        selected_set = set()
        pulled_list = []
        skipped_list = []
        hidden_list = []

        match_cache = {}

        def get_local_matches(device_item: Dict[str, Any]):
            query_str = device_item.get("title") or device_item.get("_display_name") or ""
            if query_str not in match_cache:
                matches = []
                for f in local_files:
                    title_no_ext = f["title_no_ext"]
                    m_matched, m_score, _ = fuzzy_matcher.fuzzy_subsequence_match(query_str, title_no_ext)
                    if m_matched:
                        meta = audio_metadata.extract_audio_metadata(f["path"])
                        f_copy = dict(f)
                        f_copy.update(meta)
                        matches.append((m_score, f_copy))
                matches.sort(key=lambda x: x[0], reverse=True)
                match_cache[query_str] = [m[1] for m in matches[:6]]
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
            right_header = " Track Metadata & Local Matches "
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

            # --- RENDER RIGHT PANE (Track Metadata & Local Matches) ---
            if 0 <= current_idx < len(missing_songs):
                curr_item = missing_songs[current_idx]
                matches = get_local_matches(curr_item)

                title_query = curr_item.get("title") or curr_item.get("_display_name") or ""
                artist_val = curr_item.get("artist") or "Unknown Artist"
                album_val = curr_item.get("album") or "Unknown Album"
                dur_val = curr_item.get("duration_formatted") or "00:00"
                size_val = curr_item.get("size_formatted") or "0 MB"
                mime_val = curr_item.get("mime_type") or "audio/mpeg"

                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(2, right_x, f"Device Track: {title_query}"[:right_width-1])
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

                spec_line_1 = f"   • Artist: {artist_val}   |   Album: {album_val}"
                spec_line_2 = f"   • Duration: {dur_val}   |   Size: {size_val}   |   Format: {mime_val}"
                remote_path = curr_item.get("_data") or ""

                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(3, right_x, spec_line_1[:right_width-1])
                stdscr.addstr(4, right_x, spec_line_2[:right_width-1])
                if remote_path:
                    stdscr.addstr(5, right_x, f"   • Path: {remote_path}"[:right_width-1])
                stdscr.attroff(curses.color_pair(5))

                stdscr.addstr(6, right_x, "─" * (right_width - 1))

                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(7, right_x, f"Top Local Matches ({len(matches)} found):"[:right_width-1])
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

                if not matches:
                    stdscr.addstr(9, right_x, "(No matching files found in local music folder)", curses.A_DIM)
                    stdscr.addstr(11, right_x, "Press 's' or 'p' to pull this track from ADB device.")
                else:
                    for m_idx, loc_match in enumerate(matches[:list_height - 9]):
                        row_y = m_idx + 9
                        m_fn = loc_match["filename"]
                        m_br = loc_match.get("bitrate", "Unknown")
                        m_sr = loc_match.get("sample_rate", "Unknown")
                        m_codec = loc_match.get("codec", "AUDIO")

                        m_line = f" {m_idx+1}. {m_fn} [{m_codec} | {m_br} | {m_sr}]"
                        m_line = m_line[:right_width - 1]

                        stdscr.attron(curses.color_pair(4))
                        stdscr.addstr(row_y, right_x, m_line)
                        stdscr.attroff(curses.color_pair(4))

            # Bottom Keybinding Footer
            footer = " [SPACE] Select | [s/p] Pull | [h] Hide (SQLite DB) | [m/ENTER] Mark | [q] Quit "
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
                if current_idx < len(missing_songs) - 1:
                    current_idx += 1
            elif key == ord(' '): # Spacebar toggles selection
                if current_idx in selected_set:
                    selected_set.remove(current_idx)
                else:
                    selected_set.add(current_idx)
                if current_idx < len(missing_songs) - 1:
                    current_idx += 1
            elif key == ord('h'): # Hide track and persist to SQLite DB
                if 0 <= current_idx < len(missing_songs):
                    h_item = missing_songs.pop(current_idx)
                    remote_path = h_item.get("_data") or h_item.get("title") or ""
                    hide_list_db.add_hidden_file(remote_path, h_item.get("title") or h_item.get("_display_name") or "")
                    hidden_list.append(h_item)
                    if selected_set:
                        selected_set = {idx - 1 if idx > current_idx else idx for idx in selected_set if idx != current_idx}
                    if current_idx >= len(missing_songs):
                        current_idx = max(0, len(missing_songs) - 1)
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

                    logger.info(f"[RangerReverseSync] Pulling {len(items_to_pull)} file(s)...")
                    if pull_callback is None:
                        os.makedirs(local_dir, exist_ok=True)

                    for item in items_to_pull:
                        display_name = item.get("_display_name") or item.get("filename") or f"song_{item.get('_id', 0)}.mp3"

                        if pull_callback is not None:
                            logger.info(f"[RangerReverseSync] Pulling: {display_name} -> {local_dir}/")
                            try:
                                ok = pull_callback(item)
                            except Exception as e:
                                ok = False
                                logger.error(f"[RangerReverseSync] Failed to pull '{display_name}': {e}")
                            if ok:
                                pulled_list.append(item)
                            else:
                                logger.error(f"[RangerReverseSync] Failed to pull '{display_name}'")
                            continue

                        remote_path = item.get("_data")
                        if not remote_path:
                            continue

                        logger.info(f"[RangerReverseSync] Pulling: {display_name} -> {local_dir}/")
                        cmd = ["adb", "-s", device_serial, "pull", remote_path, os.path.join(local_dir, display_name)]
                        try:
                            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                            logger.debug(f"[RangerReverseSync] {res.stdout.strip()}")
                            pulled_list.append(item)
                        except subprocess.CalledProcessError as e:
                            logger.error(f"[RangerReverseSync] Failed to pull '{remote_path}': {e.stderr or e.stdout}")

                    # Only remove items that were actually pulled successfully.
                    pulled_paths = set(item.get("_data") for item in pulled_list)
                    missing_songs[:] = [item for item in missing_songs if item.get("_data") not in pulled_paths]
                    selected_set.clear()
                    current_idx = max(0, min(current_idx, len(missing_songs) - 1))

                    input("\nPress ENTER to return to Ranger Reverse Sync UI...")
                    curses.reset_prog_mode()

        return {"pulled": pulled_list, "skipped": skipped_list, "hidden": hidden_list}

    return fzf_tui.run_with_tty(_tui)
