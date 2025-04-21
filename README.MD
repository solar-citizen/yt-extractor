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

## Windows:
winget install ffmpeg

## Ubuntu:
sudo apt update
sudo apt install ffmpeg

## MacOS (with Homebrew)
brew install ffmpeg
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
```

## 5. Set environment variables:

Check .example.env

```bash
EXTRACTION_FOLDER_PATH="path where you want to export everything"
```

## 6. Add urls.txt in config_data folder or copy example.urls.txt
(The file will be created if non-existent.)

Add url(-s) of video(-s) you want to download.

## 7. Add timestamps.txt in config_data folder or copy example.timestamps.txt
(The file will be created if non-existent.)

Fill it with timestamps, if required.
Leave empty if you want to extract video in one piece.

## 8. Optional - add code formatter

```bash
pip install black
```

Install VSCode extension "Black Formatter"

# Run program
