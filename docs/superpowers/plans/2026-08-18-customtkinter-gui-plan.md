# CustomTkinter GUI Implementation Plan & Execution Record

> **Status:** Completed & Tested

**Goal:** Add a modern, cross-platform CustomTkinter desktop GUI with folder persistence, quality selector, browser cookie authentication (to bypass YouTube 403 blocks), smart timestamp parsing, real-time streaming console, and standalone packaging support.

**Architecture:** A `gui/` package containing `app.py` (main window and tabview), `workers.py` (background thread with real-time `Popen` log streaming and progress parsing), integrated with core services (`YouTubeService`, `FFmpegService`, `MetadataService`, `TimestampService`, `Config`).

---

### Task 1: Setup Dependencies & Package Structure
- [x] **Step 1: Install GUI and Decryption Dependencies**
  ```bash
  # Windows:
  pip install customtkinter cryptography yt-dlp python-dotenv

  # Linux:
  sudo apt install python3-tk
  pip install customtkinter cryptography secretstorage yt-dlp python-dotenv
  ```
- [x] **Step 2: Create `gui/__init__.py`**
  ```python
  """GUI package for yt-extractor."""
  ```

---

### Task 2: Implement Config & Settings Persistence (`config.py`)
- [x] **Step 1: Update `config.py`**
  - Add `_load_extraction_folder()` to read from `config_data/settings.json`, falling back to `EXTRACTION_FOLDER_PATH` from `.env` or `~/yt-extractor-extractions`.
  - Add `set_extraction_folder(folder_path)` to dynamically update paths and persist to `config_data/settings.json`.

---

### Task 3: Implement Smart Timestamp Parser (`services/timestamp_service.py`)
- [x] **Step 1: Update `TimestampService`**
  - Add `normalize_timestamp(ts)` supporting `M:SS`, `MM:SS`, `H:MM:SS`, `HH:MM:SS`.
  - Add `parse_line(line)` supporting dashes, brackets, numbered lists, ranges, and pipe separators while ignoring blank lines.
  - Implement `parse_config_file()` using `parse_line()`.

---

### Task 4: Implement Streaming Background Worker (`gui/workers.py`)
- [x] **Step 1: Implement `ExtractionWorker` & `_run_streaming`**
  - Stream `yt-dlp` output line-by-line via `Popen`.
  - Parse `[download] XX%` lines for real-time progress bar animation.
  - Support `cookie_browser` parameter (`--cookies-from-browser <browser>`) to bypass YouTube 403 errors on HD streams.
  - Default to official Android client (`--extractor-args youtube:player_client=android`) when no cookies are provided to prevent `android_vr` 403 blocks.
  - Build proper `Video` objects and call `ffmpeg_service.cut_segments()`, `ffmpeg_service.extract_full_audio()`, and `metadata_service.update_metadata()`.

---

### Task 5: Implement Main CustomTkinter Application (`gui/app.py`)
- [x] **Step 1: Create `gui/app.py`**
  - **Download Tab:**
    - Extraction Folder picker with `Browse…` button and persistence.
    - URL textbox with auto-loading from `config_data/urls.txt`.
    - **Fetch Qualities** button + dropdown (sorted 1080p, 720p, etc. with size and codec info).
    - **Cookies** dropdown (`Cookies: None`, `chrome`, `firefox`, `edge`, `brave`, etc.).
    - Audio Only and Timestamps slicing switches.
    - Granular progress bar with text status label.
    - Thread-safe scrollable console (`self.after(0, ...)`).
  - **Timestamps Tab:**
    - Multi-line editor with `Auto-Format & Preview` button to normalize timestamps into `HH:MM:SS Title`.
    - `Save Timestamps` button.
  - **History Tab:**
    - Formatted JSON metadata viewer with `Refresh History` button.

---

### Task 6: Add Entrypoints & Documentation
- [x] **Step 1: Create `gui_main.py`**
  ```python
  from gui.app import App
  from utils.system_utils import SystemUtils

  def main():
      SystemUtils.configure_utf8_console()
      app = App()
      app.mainloop()

  if __name__ == "__main__":
      main()
  ```
- [x] **Step 2: Update `README.MD` and `CLAUDE.md`**
  - Add cross-platform execution instructions, supported timestamp format documentation, and cookie decryption notes.

---

### Task 7: Standalone Packaging with PyInstaller
- [x] **Step 1: Package into Standalone Binary / Executable**
  ```bash
  # Single File (.exe or binary):
  pyinstaller --noconsole --onefile --collect-all customtkinter --collect-all yt_dlp --name "yt-extractor" gui_main.py

  # Standalone Directory (Recommended):
  pyinstaller --noconsole --onedir --collect-all customtkinter --collect-all yt_dlp --name "yt-extractor" gui_main.py
  ```
