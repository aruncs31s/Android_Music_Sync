# ADB Song Query & FZF Fuzzy Search Tool

A Python command-line application and interactive Terminal User Interface (TUI) that queries audio tracks from connected Android devices via ADB (`adb shell content query`) or parses song lists from text files / stdin. Features real-time FZF-style fuzzy matching with lazy match scoring.

## Features

1. **ADB Device Navigation & Selection**:
   - Discovers connected Android devices automatically via `adb devices -l`.
   - Supports interactive terminal menu selection (arrow keys & Enter) when multiple devices are connected.
   - Non-interactive device selection via `-d <serial>` / `--device` or via numeric/serial input from stdin.

2. **FZF-Style Interactive Song Search**:
   - Real-time search prompt with instant fuzzy filtering as you type.
   - Dynamic song counter (e.g., `15/5771 matches`).
   - Clean scrollable table displaying Title, Artist, Album, Duration, and File Path.
   - Complete keyboard navigation (Up/Down arrows, PageUp/PageDown, Home/End, Enter to select, ESC/Ctrl+C to quit).

3. **Lazy Fuzzy Matching**:
   - Subsequence fuzzy matching (e.g. `"arj sng"` matches `"Arijit Singh"`).
   - Smart relevance ranking based on word boundaries, consecutive character matches, prefix matches, and exact substrings.
   - Multi-token search queries (e.g. `"arijit kesariya"` matches items containing both tokens).

4. **Pipeline & Stdin Support**:
   - Supports piping song list data via stdin (`cat songs.txt | python app.py`).
   - Supports non-interactive search mode with `-s "song query"`.
   - Flexible output formats: `text`, `json`, `path` (for piping filepaths to media players like `mpv` or `vlc`), and `csv`.

---

## Requirements

- **Python**: 3.8+ (uses standard library `curses`, `argparse`, `re`, `subprocess`, `json`).
- **Android Platform Tools**: `adb` command installed and available in system PATH.
- **Android Device**: USB or Wireless Debugging enabled on connected device.

---

## Usage Examples

### 1. Interactive Device Selection & FZF Song Search
Launch interactive search on your connected Android device:
```bash
python app.py
```
If multiple ADB devices are connected, an interactive menu will pop up allowing you to pick a device using arrow keys.

### 2. Direct Search on Connected Device (Non-Interactive)
Search for a song directly using fuzzy matching:
```bash
python app.py -s "Arijit Singh"
```

### 3. Target Specific ADB Device Serial
Specify device serial explicitly:
```bash
python app.py -d HA1DZEC9 -s "Heeriye"
```

### 4. Parse from Text File instead of ADB
If you saved ADB content query output to a text file:
```bash
python app.py -f songs.txt -s "Kesariya"
```

### 5. Stdin Piping Support
Pipe input from another command:
```bash
cat songs.txt | python app.py -s "Mareez" --format path
```

You can also run interactive FZF search on piped input:
```bash
cat songs.txt | python app.py
```

### 6. Pipe Selected File Path to Media Player
Output raw audio file paths (`--format path`) and pipe directly to `vlc` or `mpv`:
```bash
python app.py -s "Khairiyat" --format path | xargs -d '\n' mpv
```

---

## Command Line Arguments

```
options:
  -h, --help            show this help message and exit
  -d, --device DEVICE   ADB device serial number or index.
  -s, --search SEARCH   Non-interactive search query (lazy fuzzy match).
  -f, --file FILE       Path to file containing ADB content query data.
  --format {text,json,path,csv}
                        Output format (default: text).
  -l, --list-devices    List connected ADB devices and exit.
  -n, --limit LIMIT     Limit number of search results printed in non-interactive mode.
```

---

## Project Structure

- `app.py`: Main CLI entry point and CLI argument handler.
- `adb_manager.py`: Handles ADB device discovery, device selection, and running content provider queries.
- `song_parser.py`: Robust parser for ADB MediaStore `content query` format.
- `fuzzy_matcher.py`: Subsequence lazy matching engine and relevance scoring algorithm.
- `fzf_tui.py`: Curses-based interactive terminal user interface for device picker & fzf song search.
