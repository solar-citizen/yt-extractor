# CLAUDE.md - yt-extractor

## Project Overview
`yt-extractor` is a Python-based tool for batch downloading YouTube videos/audio and optionally splitting them into precise timestamped segments using `yt-dlp` and `ffmpeg`.

## Architecture & Service Boundaries
The codebase follows a strict class-oriented, service-isolated architecture:
- **`Config` (`config.py`):** Loads environment variables (`EXTRACTION_FOLDER_PATH`), manages file paths (`config_data/`), and ensures directory existence.
- **`YouTubeService` (`services/youtube_service.py`):** Handles video downloading via `yt-dlp`, title extraction, and video ID resolution.
- **`FFmpegService` (`services/ffmpeg_service.py`):** Handles segment cutting, duration probing, and full audio extraction.
- **`MetadataService` (`services/metadata_service.py`):** Tracks and persists metadata for downloaded videos (`video_metadatas.json`).
- **`TimestampService` (`services/timestamp_service.py`):** Parses `timestamps.txt` for segment slicing.
- **`Video` (`models/video.py`):** Data model representing extracted media entities.
- **`GUI Package` (`gui/`):** Contains `app.py` (CustomTkinter interface with Download, Timestamps, and History tabs) and `workers.py` (`ExtractionWorker` background thread for streaming async extractions).
- **`Entrypoints`:** `main.py` (CLI batch runner) and `gui_main.py` (CustomTkinter graphical desktop interface).

## Cross-Platform Setup & Execution
Refer to **`README.MD`** for detailed step-by-step installation instructions across platforms:
- **Windows:** PowerShell/cmd commands, winget ffmpeg installation, `.env` configuration.
- **Ubuntu / Linux:** Apt package manager (`ffmpeg`, `python3-tk`), python tools setup, and path configuration.
- **CLI Execution:** `python main.py`
- **GUI Execution:** `python gui_main.py` (Windows) / `python3 gui_main.py` (Linux)

## Coding Conventions
- **Python 3:** Use explicit type hints, modular service classes, and follow the existing OOP patterns.
- **Formatting:** Code formatted with `black`.
- **Error Handling:** Graceful exception handling with traceback logging in batch URL loops (`main.py`), with auto-creation of missing template config files (`urls.txt`, `timestamps.txt`).
- **Console Output:** Ensure UTF-8 console output is respected via `SystemUtils.configure_utf8_console()`.
