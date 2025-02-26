# Installation

## 1. Install Python with adding it to PATH

## 2. Install yt-dlp

```bash
# run in terminal:
pip install -U yt-dlp
```

### Verify installation

```bash
# run in terminal:
yt-dlp --version
```

## 3. Install FFMPEG

```bash
# visit and download package
https://ffmpeg.org/download.html
```

### Install FFMPEG package

### Verify installation

```bash
# run in terminal:
ffmpeg
```

## 4. Set environment variables:

Check .example.env

```bash
YOUTUBE_URL="video you want to download"
FFMPEG_EXE_PATH="path to ffmpeg.exe (typically in /FFMPEG/bin/ffmpeg.exe)"
FFPROBE_EXE_PATH="path to ffprobe.exe (typically in /FFMPEG/bin/ffprobe.exe)"
EXTRACTION_FOLDER_PATH="path where you want to export everything"
```

## 5. Add timestamps.txt in config folder (copy example.timestamps.txt)

Fill it with timestamps, if required

# Run program
