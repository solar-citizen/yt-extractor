# Installation & Setup Guide

yt-extractor supports multiple platforms with dedicated installation paths for **Windows** and **Ubuntu / Linux**.

---

## Platform-Specific Installation

### Windows Setup
1. **Install Python:** Ensure Python 3.x is installed from [python.org](https://www.python.org/) and `Add Python to PATH` is checked during installation. (Tkinter is included by default).
2. **Install FFmpeg via Winget:**
   Open PowerShell or Command Prompt and run:
   ```cmd
   winget install ffmpeg
   ```
   *Restart your terminal after installation.*
3. **Verify FFmpeg:**
   ```cmd
   ffmpeg
   ```

### Ubuntu / Linux Setup
1. **Install Python & Tkinter (for GUI):**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-dotenv python3-tk
   ```
2. **Install FFmpeg via Apt:**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```
3. **Verify FFmpeg:**
   ```bash
   ffmpeg
   ```

---

## Core Dependencies & Python Tools

1. **Install / Upgrade yt-dlp:**
   ```bash
   pip install -U yt-dlp
   ```
   *Verify installation:* `yt-dlp --version`

2. **Install Required Python Libraries:**
   - **Cross-platform / Windows:**
     ```bash
     pip install python-dotenv customtkinter cryptography
     ```
   - **Linux / Ubuntu (adds keyring cookie decryption support):**
     ```bash
     pip install python-dotenv customtkinter cryptography secretstorage
     ```

3. **Optional (Code Formatter):**
   ```bash
   pip install black
   ```

---

## Configuration

1. **Environment Variables:**
   Copy `.example.env` to `.env` and set your extraction folder path:
   ```env
   EXTRACTION_FOLDER_PATH="path/to/your/extraction/folder"
   ```

2. **URLs Configuration (CLI):**
   Add YouTube URLs to `config_data/urls.txt` (one per line).

3. **Timestamps Configuration (Optional):**
   Fill `config_data/timestamps.txt` with timestamps if you want to split the video into segments. Leave empty for full audio/video extraction.
   
   The parser is smart and forgiving — you can copy/paste timestamps directly from YouTube descriptions, comments, or tracklists in any of these formats (empty lines between timestamps are automatically skipped):
   - `0:00 - Path of Glory Intro` *(M:SS with dash)*
   - `2:06 - Hellfire 2`
   - `00:02:06 Hellfire 2` *(HH:MM:SS with space)*
   - `[02:06] Hellfire 2` or `(02:06) Hellfire 2` *(bracketed)*
   - `1. 02:06 - Hellfire 2` *(numbered lists)*
   - `00:00 - 02:06 Intro` *(range format)*
   - `01:05:22 | Track Name` *(pipe separated)*

---

## Running the Program

### Command Line Interface (CLI)
```bash
python main.py
```

### Graphical User Interface (GUI)
The project includes a desktop interface built with `customtkinter`. It features:
- **Download Tab:**
  - **Extraction Folder Picker:** Browse and select any output directory (automatically remembered across app launches).
  - **URL Input:** Paste YouTube URLs (one per line).
  - **Fetch Qualities:** Query and select specific video resolutions (1080p, 720p, 480p, 360p, etc.).
  - **Cookies Dropdown:** Select your browser (`chrome`, `firefox`, `edge`, `brave`, etc.) to use your active session and bypass YouTube 403 errors on HD downloads.
  - **Audio Only & Timestamp Slicing Switches.**
  - **Live Progress & Streaming Console:** Real-time percentage tracking and output logs.
- **Timestamps Tab:**
  - Built-in editor supporting any YouTube timestamp format.
  - **Auto-Format & Preview:** One-click cleanup to normalize all pasted timestamps into standard `HH:MM:SS Title`.
  - Empty lines and extra spacing are automatically ignored.
- **History Tab:** View metadata history of all previously extracted videos.

To launch the GUI:
```bash
# Windows:
python gui_main.py

# Linux / Ubuntu:
python3 gui_main.py
```
