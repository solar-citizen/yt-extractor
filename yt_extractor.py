import subprocess
import re
import os
import json
import glob
import unicodedata
import sys
import pytz
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

YOUTUBE_URL = os.getenv("YOUTUBE_URL")
if not YOUTUBE_URL:
    raise RuntimeError("YOUTUBE_URL environment variable is not set")


PY_TZ = os.getenv("PY_TZ")
if not PY_TZ:
    raise RuntimeError("PY_TZ environment variable is not set")


EXTRACTION_FOLDER_PATH = os.getenv("EXTRACTION_FOLDER_PATH")
if not EXTRACTION_FOLDER_PATH:
    raise RuntimeError("EXTRACTION_FOLDER_PATH environment variable is not set")
if not os.path.exists(EXTRACTION_FOLDER_PATH):
    os.makedirs(EXTRACTION_FOLDER_PATH, exist_ok=True)


# Use YouTube title in the file name by setting the output template accordingly.
VIDEO_PATH_TEMPLATE = os.path.join(EXTRACTION_FOLDER_PATH, "%(title)s.%(ext)s")
# Config
CONFIG_PATH = os.path.join("config", "timestamps.txt")
METADATA_PATH = os.path.join("config", "video_metadatas.json")

IS_AUDIO_ONLY_EXTRACTION = True
TIME_ZONE = PY_TZ if PY_TZ else "GMT+0"

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


def sanitize_filename(filename):
    """
    Sanitize a filename by removing/replacing characters that are not allowed in filenames
    across different operating systems, while preserving Unicode characters.
    Also normalizes Unicode characters to ensure they're compatible with the file system.
    """
    # Normalize Unicode characters (converts combined characters to single characters where possible)
    filename = unicodedata.normalize("NFC", filename)

    # Replace characters that are invalid for filenames
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "-")

    # Remove or replace any other problematic characters
    filename = filename.replace("\n", " ").replace("\r", " ")

    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")

    # Transliterate non-ASCII characters to ASCII equivalents if on Windows
    # This is a fallback for Windows systems with limited non-ASCII support
    if sys.platform == "win32":
        try:
            # Try to encode with ASCII, and fall back to transliteration
            filename.encode("ascii")
        except UnicodeEncodeError:
            # For characters that can't be represented in the current encoding
            transliterated = ""
            for char in filename:
                try:
                    char.encode("ascii")
                    transliterated += char
                except UnicodeEncodeError:
                    # Try to get a simplified version using NFKD normalization
                    simplified = unicodedata.normalize("NFKD", char)
                    # Keep only ASCII characters
                    ascii_char = "".join(c for c in simplified if ord(c) < 128)
                    transliterated += ascii_char if ascii_char else "-"
            filename = transliterated

    # Ensure the filename is not empty after sanitization
    if not filename:
        filename = "unnamed_file"

    return filename


def get_video_id(url):
    """
    Extract the YouTube video ID from a URL.
    """
    # Match patterns like youtube.com/watch?v=XXXXXXXXXXX or youtu.be/XXXXXXXXXXX
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com/.*?v=([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # If no match found, return None
    print(f"Warning: Could not extract video ID from URL: {url}")
    return None


def get_video_title(url):
    """
    Return the video's title using yt-dlp.
    """
    cmd = [
        "yt-dlp",  # Calls the yt-dlp tool.
        "--get-title",  # Instructs yt-dlp to fetch only the video's title.
        url,  # The URL of the YouTube video.
    ]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        title = result.stdout.strip()
        return title
    except subprocess.CalledProcessError as e:
        print(f"Error getting video title: {e}")
        print(f"stderr: {e.stderr}")
        return None


def get_existing_video(video_template, url):
    """
    Search for an existing video file matching the template pattern,
    substituting the actual title from the URL. The %(ext)s placeholder
    is replaced with a wildcard.
    """
    title = get_video_title(url)
    if not title:
        return None

    # Sanitize the title for safe file operations
    safe_title = sanitize_filename(title)

    # Create a pattern for glob matching
    # First replace the title placeholder with the sanitized title
    pattern = video_template.replace("%(title)s", safe_title)
    # Then replace the extension placeholder with a wildcard
    pattern = pattern.replace("%(ext)s", "*")

    # Find matching files
    files = glob.glob(pattern)
    if files:
        return files[0]
    return None


def get_video_duration(video_path):
    """
    Use ffprobe to retrieve the total duration of the video in seconds.
    """
    cmd = [
        FFPROBE,  # Path to the FFprobe executable.
        "-v",
        "error",  # Set log level to 'error' to suppress unnecessary output.
        "-show_entries",
        "format=duration",  # Retrieve only the duration information from the format section.
        "-of",
        "default=noprint_wrappers=1:nokey=1",  # Output format: plain text without keys or wrappers.
        video_path,  # The input video file to analyze.
    ]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        duration_str = result.stdout.strip()
        try:
            duration = float(duration_str)
            return duration
        except ValueError:
            print(f"Error converting duration string to float: '{duration_str}'")
            return None
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return None


def load_metadata():
    """
    Load video metadata from the JSON file.
    If the file doesn't exist, return an empty dictionary.
    """
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading metadata file: {e}")
            return {}
    return {}


def save_metadata(metadata):
    """
    Save video metadata to the JSON file.
    Create the directory if it doesn't exist.
    """
    os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
    try:
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving metadata file: {e}")


def update_metadata(url, title, duration, segments_count):
    """
    Update the metadata JSON file with information about the downloaded video.
    Uses sequential numeric IDs instead of YouTube IDs.
    """
    metadata = load_metadata()
    video_id = get_video_id(url)

    if not video_id:
        print("Cannot update metadata: Failed to extract video ID")
        return

    # Check if video already exists in metadata by YouTube ID
    for key, value in metadata.items():
        if value.get("yt_id") == video_id:
            print(f"Video ID {video_id} already exists in metadata. Skipping update.")
            return

    # Find the highest existing numeric ID and increment by 1
    next_id = 1
    for key in metadata:
        if key.isdigit() and int(key) >= next_id:
            next_id = int(key) + 1

    # Add new video entry with sequential ID
    metadata[str(next_id)] = {
        "yt_id": video_id,
        "yt_name": title,
        "local_name": sanitize_filename(title),
        "yt_link": url,
        "yt_duration": duration,
        "segments": segments_count,
        "insert_date": datetime.now(pytz.timezone(TIME_ZONE)).isoformat(),
    }

    save_metadata(metadata)
    print(f"Updated metadata for video {video_id}: {title} (ID: {next_id})")


def download_video(url, video_template):
    """
    Download the video from YouTube using yt-dlp, but only if a local file
    doesn't exist or its duration doesn't match the online video's duration.
    """
    existing_file = get_existing_video(video_template, url)
    if existing_file:
        local_duration = get_video_duration(existing_file)
        print(
            f"Local file '{existing_file}' exists with duration: {local_duration} seconds."
        )
        try:
            cmd = [
                "yt-dlp",  # Calls the yt-dlp tool.
                "--skip-download",  # Tells yt-dlp not to download the video data.
                "--print-json",  # Instructs yt-dlp to output the video's metadata in JSON format.
                url,  # The URL of the YouTube video.
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            info = json.loads(result.stdout)
            online_duration = info.get("duration")
            print(f"Online video duration: {online_duration} seconds.")
        except Exception as e:
            print("Error extracting online duration:", e)
            online_duration = None
        if online_duration is not None and local_duration is not None:
            if abs(local_duration - online_duration) < 1:
                print(
                    "Local video file exists and duration matches. Skipping download."
                )
                return existing_file
            else:
                print(
                    "Local video duration differs from online video. Redownloading..."
                )
        else:
            print("Could not determine durations. Proceeding to download.")

    # Get the title before downloading to create a sanitized output template
    title = get_video_title(url)
    if title:
        safe_title = sanitize_filename(title)
        # Create a modified template with the sanitized title
        safe_template = video_template.replace("%(title)s", safe_title)
        # But keep the extension placeholder
        safe_template = safe_template.replace(".%(ext)s", ".%(ext)s")
    else:
        safe_template = video_template

    cmd = [
        "yt-dlp",  # Calls the yt-dlp tool to download the video.
        "-o",
        safe_template,  # Specifies the output template with sanitized title.
        url,  # The URL of the YouTube video to download.
    ]
    print("Running command:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        downloaded_file = get_existing_video(video_template, url)
        if downloaded_file:
            print(f"Downloaded video as {downloaded_file}")
            return downloaded_file
        else:
            print("Download completed, but file not found using the template.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e}")
        return None


def seconds_to_timestamp(seconds):
    """
    Convert a float number of seconds to a timestamp string in HH:MM:SS.mmm format.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def parse_config_file(config_path):
    """
    Parse the config file containing chapter timestamps.

    Expected format (one per chapter):
      HH:MM:SS Some track name (with any content)

    The function removes the leading timestamp and uses the remainder of the line as the track's full name,
    adding a numerical order to the label.
    Returns a list of dictionaries with keys:
      "start": starting timestamp (as string),
      "numbered_label": label with track number and full name.
    """
    segments = []
    pattern = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+(.*)$")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                match = pattern.match(line)
                if match:
                    timestamp = match.group(1)
                    full_name = match.group(2)
                    segments.append({"start": timestamp, "full_name": full_name})
                else:
                    print("Line didn't match expected format:", line)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return []

    for idx, seg in enumerate(segments, start=1):
        seg["numbered_label"] = f"{idx}. {seg['full_name']}"
    return segments


def cut_segments(video_path, segments, output_dir):
    """
    Use FFmpeg to cut segments from the video.
    Each segment is defined by its start time and the start time of the next segment,
    with the final segment running to the end of the video.
    If IS_AUDIO_ONLY_EXTRACTION is True, extract only audio (re-encoded to AAC) and save as .m4a;
    otherwise, copy the full video and save as .mp4.
    Segments are stored in the specified output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    total_duration = get_video_duration(video_path)
    if total_duration is None:
        print("Could not retrieve video duration.")
        return
    total_duration_ts = seconds_to_timestamp(total_duration)
    num_segments = len(segments)

    # On Windows, ensure the console is set to use UTF-8
    original_encoding = None
    if sys.platform == "win32":
        original_encoding = sys.stdout.encoding
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    for i, seg in enumerate(segments):
        start = seg["start"]
        end = segments[i + 1]["start"] if i < num_segments - 1 else total_duration_ts
        label = seg["numbered_label"]
        safe_label = sanitize_filename(label)

        if IS_AUDIO_ONLY_EXTRACTION:
            output_file = os.path.join(output_dir, f"{safe_label}.m4a")
            cmd = [
                FFMPEG,  # The path to the FFmpeg executable.
                "-y",  # Overwrite output files without prompting.
                "-i",
                video_path,  # Specifies the input file.
                "-ss",
                start,  # Sets the start time for processing.
                "-to",
                end,  # Sets the end time for processing.
                "-vn",  # Disables video recording.
                "-c:a",
                "aac",  # Specifies the audio codec to use.
                "-b:a",
                "256k",  # Sets the audio bitrate.
                output_file,  # The output file path.
            ]
        else:
            output_file = os.path.join(output_dir, f"{safe_label}.mp4")
            cmd = [
                FFMPEG,  # Path to the FFmpeg executable.
                "-y",  # Overwrite output files without prompting.
                "-i",
                video_path,  # Specify the input video file.
                "-ss",
                start,  # Set the start time for the extraction.
                "-to",
                end,  # Set the end time for the extraction.
                "-c",
                "copy",  # Copy the streams without re-encoding.
                output_file,  # The path where the extracted segment will be saved.
            ]

        print(f"Cutting segment: {label} from {start} to {end}")
        print(f"Output file: {output_file}")

        try:
            # When running on Windows, use bytes mode subprocess to avoid encoding issues
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(cmd, check=True, startupinfo=startupinfo)
            else:
                subprocess.run(cmd, check=True)
            print(f"Segment saved as {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error cutting segment: {e}")

    # Restore original encoding if changed
    if original_encoding and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding=original_encoding)


def extract_full_audio(video_path, output_dir):
    """
    Extract full audio from the entire video, re-encoded to AAC, and save as a single file.
    The output is saved in output_dir.
    """
    title = get_video_title(YOUTUBE_URL)
    if not title:
        print("Could not retrieve video title. Using 'unknown_title' as fallback.")
        title = "unknown_title"

    safe_title = sanitize_filename(title)
    output_file = os.path.join(output_dir, f"{safe_title}.m4a")
    cmd = [
        FFMPEG,  # Path to the FFmpeg executable.
        "-y",  # Overwrite output files without prompting.
        "-i",
        video_path,  # Specify the input video file.
        "-vn",  # Disables video recording.
        "-c:a",
        "aac",  # Specifies the audio codec to use.
        "-b:a",
        "256k",  # Sets the audio bitrate.
        output_file,  # The output file path.
    ]
    print(f"Extracting full audio from video to {output_file}")

    try:
        # When running on Windows, use bytes mode subprocess to avoid encoding issues
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, check=True, startupinfo=startupinfo)
        else:
            subprocess.run(cmd, check=True)
        print(f"Full audio saved as {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        return None


def main():
    try:
        # On Windows, ensure the console is set to use UTF-8
        if sys.platform == "win32":
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")

        print("\nStep 1: Downloading video...")
        video_file = download_video(YOUTUBE_URL, VIDEO_PATH_TEMPLATE)
        if not video_file:
            print("Failed to download video.")
            return

        # Always create the base segments folder
        base_segments_folder = os.path.join(EXTRACTION_FOLDER_PATH, "segments")
        os.makedirs(base_segments_folder, exist_ok=True)

        # Check for config file
        if not os.path.exists(CONFIG_PATH):
            print(f"Config file not found at {CONFIG_PATH}. No segments will be cut.")
            if IS_AUDIO_ONLY_EXTRACTION:
                # Save full audio into the base segments folder (no dedicated subfolder)
                extract_full_audio(video_file, output_dir=base_segments_folder)

                # Update metadata
                title = get_video_title(YOUTUBE_URL)
                duration = get_video_duration(video_file)
                update_metadata(YOUTUBE_URL, title, duration, 0)
            return

        segments = parse_config_file(CONFIG_PATH)
        if not segments:
            print("No valid timestamps found in config file.")
            if IS_AUDIO_ONLY_EXTRACTION:
                print("Config is empty. Extracting full audio from video...")
                extract_full_audio(video_file, output_dir=base_segments_folder)

                # Update metadata
                title = get_video_title(YOUTUBE_URL)
                duration = get_video_duration(video_file)
                update_metadata(YOUTUBE_URL, title, duration, 0)
            else:
                print("Skipping segmentation. Video will remain as downloaded.")
            return

        print(f"Parsed {len(segments)} segments from config file.")
        # Create a dedicated folder for this video's segments based on its title.
        title = get_video_title(YOUTUBE_URL)
        if not title:
            print("Could not retrieve video title. Using 'unknown_title' as fallback.")
            title = "unknown_title"

        safe_title = sanitize_filename(title)
        video_segments_folder = os.path.join(base_segments_folder, safe_title)
        os.makedirs(video_segments_folder, exist_ok=True)

        print("\nStep 2: Cutting video into segments...")
        cut_segments(video_file, segments, video_segments_folder)

        # Update metadata after successful processing
        duration = get_video_duration(video_file)
        update_metadata(YOUTUBE_URL, title, duration, len(segments))

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
