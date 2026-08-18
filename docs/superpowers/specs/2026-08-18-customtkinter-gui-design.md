# Design Specification: CustomTkinter GUI for yt-extractor

## 1. Overview
Add a modern, cross-platform desktop graphical user interface (GUI) to `yt-extractor` using **CustomTkinter**, ensuring seamless operation on both Windows and Ubuntu (Linux) without disrupting the existing CLI functionality.

---

## 2. Architecture & Service Integration
- **GUI Package (`gui/`):**
  - `app.py`: Main window, tab navigation, UI state management, thread-safe message dispatch (`self.after()`), folder picker, quality fetching, and cookies selector.
  - `workers.py`: `ExtractionWorker` background thread (`threading.Thread`) executing extraction loops with real-time `Popen` stdout streaming, percentage parsing, and granular progress reporting.
- **Service Integration:**
  - `Config`: Loads extraction directory with fallback hierarchy (`config_data/settings.json` -> `.env` -> `~/yt-extractor-extractions`). Manages path templates and persists directory choices.
  - `YouTubeService`: Resolves video titles, IDs, duration checks, and downloaded file matching.
  - `FFmpegService`: Executes video slicing into timestamped segments (`cut_segments`) and audio extraction (`extract_full_audio`).
  - `TimestampService`: Smart, forgiving parser normalizing any timestamp string (M:SS, MM:SS, HH:MM:SS, brackets, numbered lists, ranges, pipes) into `HH:MM:SS Title`.
  - `MetadataService`: Persists video information into `config_data/video_metadatas.json`.

---

## 3. Tabs & Features

### 1. Download & Extract Tab
- **Extraction Folder Picker:**
  - Displays current output directory with `Browse…` button (`filedialog.askdirectory`).
  - Automatically saves the chosen folder to `config_data/settings.json` for persistence across app restarts.
- **URL Input Box:** Multi-line text entry for YouTube URLs (one per line). Auto-loads from and saves to `config_data/urls.txt`.
- **Quality Selector:**
  - **Fetch Qualities Button:** Queries available video formats using `yt-dlp -F` in a background thread.
  - **Quality Combobox:** Displays parsed streams sorted from highest resolution (1080p, 720p, etc.) down to lowest, with container, codec, and approximate file size.
  - Formats automatically multiplex with `+bestaudio` for complete video+audio downloads.
- **Browser Cookies Dropdown:**
  - Select active browser (`Cookies: None`, `chrome`, `firefox`, `edge`, `brave`, `chromium`, `opera`).
  - Passes `--cookies-from-browser` to decrypt and use browser sessions, avoiding YouTube 403 Forbidden blocks on HD/4K streams.
  - When no cookies are selected, automatically routes via the official Android player client to avoid `android_vr` 403 errors.
- **Toggles & Action:**
  - `Audio Only` switch.
  - `Use Timestamps Slicing` switch.
  - `Start Extraction` button (disables during active jobs, changes text to "Extracting…").
- **Live Progress & Streaming Console:**
  - Granular progress bar with text status (`[1/3] Downloading… 45%`, `[1/3] Cutting segments…`, `Done!`).
  - Scrollable console with real-time `yt-dlp` output streaming.

### 2. Timestamps Tab
- **Multi-line Text Editor:** Load/save from `config_data/timestamps.txt`.
- **Forgiving Parsing Support:**
  - `0:00 - Path of Glory Intro` *(M:SS with dash)*
  - `2:06 - Hellfire 2`
  - `00:02:06 Hellfire 2` *(HH:MM:SS with space)*
  - `[02:06] Hellfire 2` or `(02:06) Hellfire 2` *(bracketed)*
  - `1. 02:06 - Hellfire 2` *(numbered lists)*
  - `00:00 - 02:06 Intro` *(range format)*
  - `01:05:22 | Track Name` *(pipe separated)*
  - Blank and empty lines are automatically skipped.
- **Auto-Format & Preview Button:** Parses and reformats all pasted text into clean `HH:MM:SS Title` with validation counter.
- **Save Timestamps Button:** Persists timestamps to file.

### 3. History Tab
- **Metadata Viewer:** Formatted JSON viewer displaying all previously extracted media from `video_metadatas.json`.
- **Refresh Button:** Reloads history dynamically after extraction runs.

---

## 4. Cross-Platform & Security Specifications
- **Ubuntu / Linux:**
  - Requires `python3-tk` for Tkinter bindings.
  - Uses `secretstorage` + `cryptography` for GNOME Keyring Chrome cookie decryption.
- **Windows:**
  - Uses native Python Tkinter installation.
  - Uses `cryptography` + native DPAPI (`crypt32.dll`) for Windows browser cookie decryption.
  - Suppresses subprocess console flashes with `STARTUPINFO`.
  - Configures UTF-8 console output via `SystemUtils.configure_utf8_console()`.

---

## 5. Packaging & Standalone Executable
- Built with **PyInstaller**:
  - `--collect-all customtkinter`: Bundles JSON themes, fonts, and styling assets.
  - `--collect-all yt_dlp`: Bundles extractors and network components.
  - `--noconsole`: Hides command prompt window on launch.
