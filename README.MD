# Installation & Setup Guide

yt-extractor supports multiple platforms with dedicated installation paths for Windows and Ubuntu/Linux.

---

## Platform-Specific Installation

### Windows Setup
1. **Install Python:** Ensure Python 3.x is installed and added to your system `PATH`.
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
1. **Install Python & Pip:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-dotenv
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

1. **Install yt-dlp:**
   ```bash
   pip install -U yt-dlp
   ```
   *Verify installation:* `yt-dlp --version`

2. **Install Required Python Libraries:**
   ```bash
   pip install python-dotenv
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

2. **URLs Configuration:**
   Add YouTube URLs to `config_data/urls.txt` (one per line).

3. **Timestamps Configuration (Optional):**
   Fill `config_data/timestamps.txt` with timestamps if you want to split the video into segments. Leave empty for full audio/video extraction.

---

## Running the Program

```bash
python main.py
```
