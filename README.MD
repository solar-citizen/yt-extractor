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
# run in terminal:
winget install ffmpeg
```

Restart terminal

### Verify installation

```bash
# run in terminal:
ffmpeg
```

## 4. Install python tools

```bash
# run in terminal:
pip install dotenv
pip install pytz
```

## 5. Set environment variables:

Check .example.env

```bash
YOUTUBE_URL="video you want to download"
EXTRACTION_FOLDER_PATH="path where you want to export everything"
```

## 6. Add timestamps.txt in config folder (copy example.timestamps.txt)

Fill it with timestamps, if required

## 7. Optional - add code formatter

```bash
pip install black
```

Install VSCode extension "Black Formatter"

# Run program
