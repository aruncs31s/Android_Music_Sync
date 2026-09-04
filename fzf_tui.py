"""
Interactive curses-based terminal user interface (TUI) for:
1. Device selection menu navigation.
2. FZF-style live fuzzy song searching and interactive selection.
"""
import sys
import os
import curses
from typing import List, Dict, Any, Optional
import fuzzy_matcher

def run_with_tty(func, *args, **kwargs):
    """
    Ensure curses has access to /dev/tty even if sys.stdin was redirected via pipe.
    """
    stdin_fd_backup = None
    tty_fd = None

    if not sys.stdin.isatty():
        try:
            tty_fd = open("/dev/tty", "rb", buffering=0)
            stdin_fd_backup = os.dup(0)
            os.dup2(tty_fd.fileno(), 0)
        except Exception:
            pass

    try:
        return curses.wrapper(func, *args, **kwargs)
    finally:
        if stdin_fd_backup is not None:
            os.dup2(stdin_fd_backup, 0)
            os.close(stdin_fd_backup)
        if tty_fd is not None:
            tty_fd.close()

def select_device_tui(devices: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Interactive TUI menu for choosing an ADB device using arrow keys / Enter.
    """
    if not devices:
        return None
    if len(devices) == 1:
        return devices[0]

    def _menu(stdscr):
        curses.curs_set(0) # Hide cursor
        stdscr.keypad(True)
        current_row = 0

        # Color pairs
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN) # Highlight
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) # Header

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            title = " Select ADB Device (Use Up/Down arrows & Enter to select): "
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(0, 0, title[:width-1])
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            for idx, dev in enumerate(devices):
                row_y = idx + 2
                if row_y >= height - 1:
                    break

                text = f"  [{idx + 1}] {dev['serial']} - {dev['model']} ({dev['state']})  "
                text = text.ljust(width - 2)

                if idx == current_row:
                    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    stdscr.addstr(row_y, 1, text[:width-2])
                    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addstr(row_y, 1, text[:width-2])

            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP or key == ord('k'):
                current_row = (current_row - 1) % len(devices)
            elif key == curses.KEY_DOWN or key == ord('j'):
                current_row = (current_row + 1) % len(devices)
            elif key in (10, 13): # Enter
                return devices[current_row]
            elif key in (27, ord('q')): # ESC / q
                return None

    return run_with_tty(_menu)


def search_songs_tui(songs: List[Dict[str, Any]], device_info: str = "Connected Device") -> Optional[Dict[str, Any]]:
    """
    Interactive fzf-style song search UI with live fuzzy filtering, counter, and preview.
    """
    def _search(stdscr):
        curses.curs_set(1) # Show cursor for prompt
        stdscr.keypad(True)

        # Enable color support
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Selected row
        curses.init_pair(2, curses.COLOR_YELLOW, -1)                # Header & prompt symbol
        curses.init_pair(3, curses.COLOR_GREEN, -1)                 # Song title
        curses.init_pair(4, curses.COLOR_CYAN, -1)                  # Artist
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)               # Duration / Details

        query = ""
        filtered_songs = songs
        selected_idx = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            if height < 4 or width < 20:
                stdscr.addstr(0, 0, "Terminal window too small!")
                stdscr.refresh()
                key = stdscr.getch()
                if key in (27, ord('q')):
                    return None
                continue

            # Header info line
            header_str = f" ADB Song Search [{device_info}] | {len(filtered_songs)}/{len(songs)} matches "
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(0, 0, header_str[:width-1])
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            # Search prompt line (Row 1)
            prompt = "> "
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(1, 0, prompt)
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            
            query_display = query[:width - len(prompt) - 1]
            stdscr.addstr(1, len(prompt), query_display)

            # Calculate printable list area (Row 3 to height-2)
            list_start_y = 3
            list_height = height - list_start_y - 1

            if list_height < 1:
                list_height = 1

            # Adjust scroll offset if needed
            if selected_idx < scroll_offset:
                scroll_offset = selected_idx
            elif selected_idx >= scroll_offset + list_height:
                scroll_offset = selected_idx - list_height + 1

            # Draw songs list
            for i in range(list_height):
                item_idx = scroll_offset + i
                if item_idx >= len(filtered_songs):
                    break

                row_y = list_start_y + i
                song = filtered_songs[item_idx]

                title = song.get("title") or "Unknown Title"
                artist = song.get("artist") or "Unknown Artist"
                album = song.get("album") or ""
                duration = song.get("duration_formatted") or "00:00"

                # Format line display
                line_str = f"{item_idx + 1:4d}. {title} - {artist} [{album}] ({duration})"
                line_str = line_str[:width - 2]

                if item_idx == selected_idx:
                    # Highlight selected row
                    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    stdscr.addstr(row_y, 0, line_str.ljust(width - 1))
                    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addstr(row_y, 0, line_str)

            # Footer / Status bar (Bottom row)
            footer = " [UP/DN] Navigate | [ENTER] Select | [ESC/Ctrl+C] Quit "
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(height - 1, 0, footer[:width-1].ljust(width-1))
            stdscr.attroff(curses.A_REVERSE)

            # Place cursor at end of search prompt
            cursor_x = min(len(prompt) + len(query), width - 1)
            try:
                stdscr.move(1, cursor_x)
            except curses.error:
                pass

            stdscr.refresh()

            # Read user key input
            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                return None

            if key in (27, 3, 17): # ESC, Ctrl+C, Ctrl+Q
                return None
            elif key in (10, 13): # Enter key
                if filtered_songs and 0 <= selected_idx < len(filtered_songs):
                    return filtered_songs[selected_idx]
                return None
            elif key in (curses.KEY_UP, 16): # Up arrow or Ctrl+P
                if selected_idx > 0:
                    selected_idx -= 1
            elif key in (curses.KEY_DOWN, 14): # Down arrow or Ctrl+N
                if selected_idx < len(filtered_songs) - 1:
                    selected_idx += 1
            elif key == curses.KEY_PPAGE: # Page Up
                selected_idx = max(0, selected_idx - list_height)
            elif key == curses.KEY_NPAGE: # Page Down
                selected_idx = min(len(filtered_songs) - 1, selected_idx + list_height)
            elif key == curses.KEY_HOME: # Home
                selected_idx = 0
            elif key == curses.KEY_END: # End
                selected_idx = max(0, len(filtered_songs) - 1)
            elif key in (curses.KEY_BACKSPACE, 127, 8): # Backspace
                if len(query) > 0:
                    query = query[:-1]
                    filtered_songs = fuzzy_matcher.filter_and_rank_songs(query, songs)
                    selected_idx = 0
                    scroll_offset = 0
            elif 32 <= key <= 126: # Printable ASCII characters
                query += chr(key)
                filtered_songs = fuzzy_matcher.filter_and_rank_songs(query, songs)
                selected_idx = 0
                scroll_offset = 0

    return run_with_tty(_search)
