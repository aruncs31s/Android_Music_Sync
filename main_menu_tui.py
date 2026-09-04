"""
Interactive Main Menu TUI for app.py when launched without CLI arguments.
Provides visual menu options for Search, Sync, Download, Cache Refresh, and Reverse Sync.
"""
import sys
import os
import curses
from typing import Optional

import fzf_tui

MENU_OPTIONS = [
    ("1", "Search", "Device File Search (FZF Real-time Fuzzy Search)"),
    ("2", "Sync", "Synchronize Local Music Folder -> ADB Device"),
    ("3", "Download", "Download Song from Spotify Link or Query"),
    ("4", "Cache Refresh", "Clear & Re-populate Redis Song Cache"),
    ("5", "Reverse Sync", "Reverse Sync: Pull missing songs from ADB Device -> Local Folder"),
    ("Q", "Exit", "Quit Application")
]


def show_main_menu_tui() -> Optional[str]:
    """
    Interactive full-screen Curses main menu.
    Returns the action key string ('search', 'sync', 'download', 'cache_refresh', 'reverse_sync') or None.
    """
    def _menu(stdscr):
        curses.curs_set(0) # Hide cursor
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Highlight
        curses.init_pair(2, curses.COLOR_YELLOW, -1)                 # Title
        curses.init_pair(3, curses.COLOR_GREEN, -1)                  # Numbers
        curses.init_pair(4, curses.COLOR_CYAN, -1)                   # Descriptions

        current_row = 0

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            if height < 12 or width < 40:
                stdscr.addstr(0, 0, "Terminal window too small!")
                stdscr.refresh()
                key = stdscr.getch()
                if key in (27, ord('q'), ord('Q')):
                    return None
                continue

            # App Title & Header
            title = " ADB MUSIC MANAGER & SYNCHRONIZER "
            subtitle = " Select an action using Up/Down arrows & press ENTER: "
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(1, 2, title)
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(2, 2, subtitle, curses.A_DIM)
            stdscr.addstr(3, 2, "─" * (width - 4))

            for idx, (key_num, name, desc) in enumerate(MENU_OPTIONS):
                row_y = 5 + (idx * 2)
                if row_y >= height - 2:
                    break

                text = f" [{key_num}] {name:<18} - {desc} "
                text = text.ljust(width - 6)

                if idx == current_row:
                    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    stdscr.addstr(row_y, 3, text[:width-6])
                    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                    stdscr.addstr(row_y, 3, f" [{key_num}] ")
                    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

                    stdscr.attron(curses.A_BOLD)
                    stdscr.addstr(row_y, 8, f"{name:<18}")
                    stdscr.attroff(curses.A_BOLD)

                    stdscr.attron(curses.color_pair(4))
                    stdscr.addstr(row_y, 27, f"- {desc}"[:width-28])
                    stdscr.attroff(curses.color_pair(4))

            # Bottom Status Bar
            footer = " [UP/DN] Move | [1-5] Quick Jump | [ENTER] Select | [ESC/Q] Exit "
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(height - 1, 0, footer[:width-1].ljust(width-1))
            stdscr.attroff(curses.A_REVERSE)

            stdscr.refresh()

            key = stdscr.getch()

            if key in (curses.KEY_UP, ord('k')):
                current_row = (current_row - 1) % len(MENU_OPTIONS)
            elif key in (curses.KEY_DOWN, ord('j')):
                current_row = (current_row + 1) % len(MENU_OPTIONS)
            elif key in (10, 13): # Enter
                selected_num = MENU_OPTIONS[current_row][0]
                if selected_num == "1":
                    return "search"
                elif selected_num == "2":
                    return "sync"
                elif selected_num == "3":
                    return "download"
                elif selected_num == "4":
                    return "cache_refresh"
                elif selected_num == "5":
                    return "reverse_sync"
                else:
                    return None
            elif key == ord('1'):
                return "search"
            elif key == ord('2'):
                return "sync"
            elif key == ord('3'):
                return "download"
            elif key == ord('4'):
                return "cache_refresh"
            elif key == ord('5'):
                return "reverse_sync"
            elif key in (27, ord('q'), ord('Q'), ord('0')):
                return None

    return fzf_tui.run_with_tty(_menu)
