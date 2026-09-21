import argparse
import sys


def parse_args():
    argv = sys.argv[1:]
    return _parse(list(argv))


def _parse(argv):
    # Context-scoped '-d': inside --dupes mode, '-d' means "immediate delete",
    # NOT device (--device) selection. The real option is --dupes-delete; the
    # shim rewrites '-d' so the existing --device flag keeps its '-d' alias.
    if "--dupes" in argv:
        argv = ["--dupes-delete" if a == "-d" else a for a in argv]

    parser = argparse.ArgumentParser(
        description="Query, fuzzy search, download, sync, reverse-sync, Over-IP sync, and Web Dashboard.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  1. Launch Web Dashboard Interface:
     python app.py --web

  2. Over-IP Sync across devices over HTTP:
     python app.py --ip

  3. Launch Over-IP Flask REST API server:
     python app.py --serve-ip

  4. Interactive Ranger-style Dual-Pane Reverse Sync (ADB Device -> Local Folder):
     python app.py --reverse-sync -i

  5. Interactive Ranger-style Dual-Pane Sync (Local Folder -> ADB Device):
     python app.py --sync -i

  6. List all files currently hidden in SQLite database:
     python app.py --list-hidden

  7. Unhide a file (or 'all') from SQLite database:
     python app.py --unhide all

8. Include hidden files during sync:
     python app.py --sync --show-hidden

   9. Detect and report duplicate songs:
     python app.py --dupes

  10. Interactive duplicate cleanup (choose which copies to keep/delete):
     python app.py --dupes -i

  11. Auto-delete all but one copy per duplicate cluster:
     python app.py --dupes -d

  12. Duplicate detection using acoustic audio fingerprinting:
     python app.py --dupes -af

  13. Interactive fingerprinted duplicate cleanup:
     python app.py --dupes -i -af

  14. Auto-delete with fingerprinting and auto-confirm:
     python app.py --dupes -d -af -y

   6. Launch Interactive Main Menu:
     python app.py
""",
    )
    parser.add_argument("--config", type=str, help="Path to custom config.json file.")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch Flask Web Dashboard Interface on http://localhost:5000.",
    )
    parser.add_argument(
        "--ip",
        nargs="?",
        const="",
        type=str,
        help="Sync music across devices over HTTP IP address (e.g. --ip 192.168.1.50).",
    )
    parser.add_argument(
        "--serve-ip",
        action="store_true",
        help="Start Flask REST API server to serve local music library over HTTP.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronize local music folder with ADB device.",
    )
    parser.add_argument(
        "--reverse-sync",
        action="store_true",
        help="Reverse sync: Pull missing songs from ADB device into local music folder.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Launch Ranger-style interactive dual-pane TUI during folder sync or reverse sync.",
    )
    parser.add_argument(
        "--show-hidden",
        action="store_true",
        help="Include files hidden in SQLite database during sync operations.",
    )
    parser.add_argument(
        "--list-hidden",
        action="store_true",
        help="List all files stored in the SQLite hide list database (sync_hide_list.db) and exit.",
    )
    parser.add_argument(
        "--list-synced",
        action="store_true",
        help="List all files recorded in the SQLite synced history database (sync_hide_list.db) and exit.",
    )
    parser.add_argument(
        "--unhide",
        type=str,
        help="Remove specified file path (or 'all') from the SQLite hide list database and exit.",
    )
    parser.add_argument(
        "--sync-folder",
        type=str,
        help="Local music folder to sync (overrides config.json local_sync_folder).",
    )
    parser.add_argument(
        "--remote-dir",
        type=str,
        help="Target folder on ADB device (overrides config.json remote_adb_folder).",
    )
    parser.add_argument(
        "--force-sync",
        action="store_true",
        help="Include songs already present on device in sync upload list.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Automatically confirm sync, reverse-sync, and push operations without prompting.",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Bypass Redis cache and re-query live ADB device.",
    )
    parser.add_argument(
        "-dl",
        "--download",
        type=str,
        help="Spotify track/album URL or song query to download into songs/download/ directory.",
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        help="Target folder for downloaded songs (overrides config.json download_folder).",
    )
    parser.add_argument(
        "--use-telegram",
        action="store_true",
        help="Force using Telegram Deezload bot for Spotify link downloading.",
    )
    parser.add_argument(
        "--push-adb",
        action="store_true",
        default=None,
        help="Automatically push downloaded song to ADB device.",
    )
    parser.add_argument(
        "--no-push-adb",
        action="store_false",
        dest="push_adb",
        help="Skip pushing downloaded song to ADB device.",
    )
    parser.add_argument(
        "-d", "--device", type=str, help="ADB device serial number (or index)."
    )
    parser.add_argument(
        "-s",
        "--search",
        type=str,
        help="Non-interactive search query (lazy fuzzy match).",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Path to file containing ADB content query data (e.g., songs.txt).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "path", "csv"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "-l",
        "--list-devices",
        action="store_true",
        help="List connected ADB devices and exit.",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=None,
        help="Limit number of search results printed in non-interactive mode.",
    )
    parser.add_argument(
        "--dupes",
        action="store_true",
        help="Detect duplicate songs across the local music library and print a report.",
    )
    parser.add_argument(
        "--dupes-delete",
        action="store_true",
        help="With --dupes: immediately delete all but one copy per duplicate cluster (short form: -d).",
    )
    parser.add_argument(
        "-af",
        "--dupes-fingerprint",
        action="store_true",
        dest="dupes_fingerprint",
        help="With --dupes: use acoustic audio fingerprinting for duplicate detection.",
    )

    args = parser.parse_args(argv)

    if args.dupes and args.dupes_delete and args.interactive:
        parser.error(
            "--dupes -d (immediate delete) and -i/--interactive cannot be used together. "
            "Pick one mode."
        )

    return args
