# ADB Song Query, FZF Fuzzy Search, & Spotify Downloader Tool

A cli + web tool that queries audio tracks from connected Android devices via ADB (`adb shell content query`) or local files Features real-time FZF-style fuzzy matching with lazy match scoring, Spotify/query song downloading, duplicate detection, and post-download pushing to Android devices.

## For MAC OS Users(12)


You will need a C++ compiler and CMake to build the library. FFmpeg is required to build the fpcalc tool. ([Source](https://acoustid.org/chromaprint))

```bash
git clone https://github.com/acoustid/chromaprint.git
cd chromaprint
cmake .
make
```
or
```bash
brew install chromaprint
```


## Features (AI DOCS)

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

4. **Spotify & Song Downloader (`downloader/`)**:
   - Downloads Spotify track/album links or search queries directly into `songs/download/`.
   - Supports direct engine (`yt-dlp`) and Telegram Deezload bot automation (`@DeezloadBot`).

5. **ADB Post-Download Push & Duplicate Detection (`adb_pusher.py`)**:
   - Checks if a downloaded song already exists on the connected device before pushing, issuing a `[NOTICE]` warning if a duplicate is found.
   - Interactively asks: `"Push it to ADB device? [y/N]"`.
   - Verifies and automatically creates `/storage/emulated/0/Music/ADB` on the device if missing (notifies user if manual creation is required).
   - Triggers Android MediaStore scan broadcast so music player apps detect the new file immediately.

---

## Requirements

- **Python**: 3.8+ (uses standard library `curses`, `argparse`, `re`, `subprocess`, `json`).
- **Android Platform Tools**: `adb` command installed and available in system PATH.
- **Audio Downloader**: `yt-dlp` installed (`/usr/bin/yt-dlp`).

---

## Usage Examples

### 1. Download Song from Spotify Link / Query & Push to ADB Device
```bash
python app.py -dl "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT" --push-adb
```
Or search and download by song name (prompts `Push it to ADB device? [y/N]` interactively):
```bash
python app.py -dl "Kesariya Arijit Singh"
```

### 2. Download using Telegram Deezload Bot
```bash
python app.py -dl "https://open.spotify.com/track/..." --use-telegram
```

### 3. Interactive Device Selection & FZF Song Search
Launch interactive search on your connected Android device:
```bash
python app.py
```

### 4. Direct Non-Interactive Search on Connected Device
```bash
python app.py -s "Arijit Singh"
```

### 5. Target Specific ADB Device Serial
```bash
python app.py -d HA1DZEC9 -s "Heeriye"
```

### 6. Parse from Text File or Pipe Stdin
```bash
python app.py -f songs.txt -s "Kesariya"
cat songs.txt | python app.py -s "Mareez" --format path
```

### 7. Removing Duplicates using `dupes cli`
This uses `fpcalc` and check for duplicates that is harder to find using string matching alone
```
python app.py --dupes -af
```
---

## Project Structure

- `app.py`: Main CLI & TUI entry point.
- `cmd/`: Command line argument definitions (`args.py`).
- `database/`: Centralized SQLite database (`db_manager.py`), Redis caching (`redis_cache.py`), and hide list DB.
- `device_providers/`: Strategy pattern device providers (ADB, Local Storage, Over-IP).
- `downloader/`: Package for downloading songs via direct engine or Telegram Deezload bot.
- `model/`: Data models and dataclasses (`song.py`, `playlist.py`, `device.py`, etc.).
- `over_ip/`: Wireless Over-IP HTTP synchronization client, server, and discovery.
- `repositories/`: Cache-aware repository abstractions for songs, playlists, devices, and trash.
- `services/`: Business services for audio transcoding, audio streaming, forward/reverse sync, and sync verification.
- `tui/`: Curses-based interactive Terminal User Interfaces (`fzf_tui.py`, `ranger_sync_tui.py`, `main_menu_tui.py`).
- `ui/`: Flask Web Dashboard with modular JavaScript frontend, CSS themes, and HTML templates.
- `utils/`: Common utilities including logging, string normalization, time formatting, audio metadata/fingerprinting, and ADB helpers.
