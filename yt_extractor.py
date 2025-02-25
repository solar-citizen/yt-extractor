import subprocess
import re
import os
import json
import glob
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_URL = os.getenv("YOUTUBE_URL")
if not YOUTUBE_URL:
    raise RuntimeError("YOUTUBE_URL environment variable is not set")

FFMPEG_EXE_PATH = os.getenv("FFMPEG_EXE_PATH")
if not FFMPEG_EXE_PATH:
    raise RuntimeError("FFMPEG_EXE_PATH environment variable is not set")
if not os.path.exists(FFMPEG_EXE_PATH):
    raise RuntimeError(f"FFmpeg executable not found at {FFMPEG_EXE_PATH}")

FFPROBE_EXE_PATH = os.getenv("FFPROBE_EXE_PATH")
if not FFPROBE_EXE_PATH:
    raise RuntimeError("FFPROBE_EXE_PATH environment variable is not set")
if not os.path.exists(FFPROBE_EXE_PATH):
    raise RuntimeError(f"FFprobe executable not found at {FFPROBE_EXE_PATH}")

EXTRACTION_FOLDER_PATH = os.getenv("EXTRACTION_FOLDER_PATH")
if not EXTRACTION_FOLDER_PATH:
    raise RuntimeError("EXTRACTION_FOLDER_PATH environment variable is not set")
if not os.path.exists(EXTRACTION_FOLDER_PATH):
    os.makedirs(EXTRACTION_FOLDER_PATH, exist_ok=True)

# Use YouTube title in the file name by setting the output template accordingly.
VIDEO_PATH_TEMPLATE = os.path.join(EXTRACTION_FOLDER_PATH, "%(title)s.%(ext)s")
CONFIG_PATH = os.path.join("config", "timestamps.txt")

# Global flag: when True, only extract audio.
IS_AUDIO_ONLY_EXTRACTION = True

def get_video_title(url):
    """
    Return the video's title using yt-dlp.
    """
    cmd = [
        "yt-dlp",           # Calls the yt-dlp tool.
        "--get-title",      # Instructs yt-dlp to fetch only the video's title.
        url                 # The URL of the YouTube video.
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    title = result.stdout.strip()
    return title

def get_existing_video(video_template, url):
    """
    Search for an existing video file matching the template pattern,
    substituting the actual title from the URL. The %(ext)s placeholder
    is replaced with a wildcard.
    """
    title = get_video_title(url)
    # Escape special characters in the title for glob matching
    safe_title = glob.escape(title)
    pattern = video_template.replace("%(title)s", safe_title).replace("%(ext)s", "*")
    files = glob.glob(pattern)
    if files:
        return files[0]
    return None

def get_video_duration(video_path):
    """
    Use ffprobe to retrieve the total duration of the video in seconds.
    """
    cmd = [
        FFPROBE_EXE_PATH,                               # Path to the FFprobe executable.
        "-v", "error",                                  # Set log level to 'error' to suppress unnecessary output.
        "-show_entries", "format=duration",             # Retrieve only the duration information from the format section.
        "-of", "default=noprint_wrappers=1:nokey=1",    # Output format: plain text without keys or wrappers.
        video_path                                      # The input video file to analyze.
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration_str = result.stdout.strip()
    try:
        duration = float(duration_str)
    except ValueError:
        duration = None
    return duration

def download_video(url, video_template):
    """
    Download the video from YouTube using yt-dlp, but only if a local file
    doesn't exist or its duration doesn't match the online video's duration.
    """
    existing_file = get_existing_video(video_template, url)
    if existing_file:
        local_duration = get_video_duration(existing_file)
        print(f"Local file '{existing_file}' exists with duration: {local_duration} seconds.")
        try:
            cmd = [
                "yt-dlp",           # Calls the yt-dlp tool.
                "--skip-download",  # Tells yt-dlp not to download the video data.
                "--print-json",     # Instructs yt-dlp to output the video's metadata in JSON format.
                url                 # The URL of the YouTube video.
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(result.stdout)
            online_duration = info.get("duration")
            print(f"Online video duration: {online_duration} seconds.")
        except Exception as e:
            print("Error extracting online duration:", e)
            online_duration = None
        if online_duration is not None and local_duration is not None:
            if abs(local_duration - online_duration) < 1:
                print("Local video file exists and duration matches. Skipping download.")
                return existing_file
            else:
                print("Local video duration differs from online video. Redownloading...")
        else:
            print("Could not determine durations. Proceeding to download.")
    cmd = [
        "yt-dlp",                   # Calls the yt-dlp tool to download the video.
        "-o", video_template,       # Specifies the output template for the downloaded file (which can include placeholders like %(title)s and %(ext)s).
        url                         # The URL of the YouTube video to download.
    ]
    print("Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    downloaded_file = get_existing_video(video_template, url)
    if downloaded_file:
        print(f"Downloaded video as {downloaded_file}")
    else:
        print("Download completed, but file not found using the template.")
    return downloaded_file

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
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                timestamp = match.group(1)
                full_name = match.group(2)
                segments.append({
                    "start": timestamp,
                    "full_name": full_name
                })
            else:
                print("Line didn't match expected format:", line)
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
    for i, seg in enumerate(segments):
        start = seg["start"]
        end = segments[i + 1]["start"] if i < num_segments - 1 else total_duration_ts
        label = seg["numbered_label"]
        safe_label = "".join(c for c in label if c not in r'\/:*?"<>|')
        if IS_AUDIO_ONLY_EXTRACTION:
            output_file = os.path.join(output_dir, f"{safe_label}.m4a")
            cmd = [
                FFMPEG_EXE_PATH,    # The path to the FFmpeg executable. This tells your system which program to run.
                "-y",               # Overwrite output files without prompting. If a file with the same name already exists, it will be replaced.
                "-i", video_path,   # Specifies the input file. 'video_path' is the path to the video you want to process.
                "-ss", start,       # Sets the start time for processing (seek position). 'start' is a timestamp (e.g., "00:04:02") indicating where to begin the extraction.
                "-to", end,         # Sets the end time for processing. 'end' is a timestamp (e.g., "00:08:20") indicating where to stop the extraction.
                "-vn",              # Disables video recording. This tells FFmpeg to ignore the video stream, so only the audio is processed.
                "-c:a", "aac",      # Specifies the audio codec to use. Here, "aac" means FFmpeg will encode the audio using the Advanced Audio Coding codec.
                "-b:a", "256k",     # Sets the audio bitrate to 256 kilobits per second. This determines the quality (and file size) of the output audio.
                output_file         # The output file path where the processed (extracted) audio will be saved.
            ]
        else:
            output_file = os.path.join(output_dir, f"{safe_label}.mp4")
            cmd = [
                FFMPEG_EXE_PATH,    # Path to the FFmpeg executable.
                "-y",               # Overwrite output files without prompting.
                "-i", video_path,   # Specify the input video file.
                "-ss", start,       # Set the start time for the extraction.
                "-to", end,         # Set the end time for the extraction.
                "-c", "copy",       # Copy the streams (both video and audio) without re-encoding.
                output_file         # The path where the extracted segment will be saved.
            ]
        print(f"Cutting segment: {label} from {start} to {end}")
        subprocess.run(cmd, check=True)
        print(f"Segment saved as {output_file}")

def extract_full_audio(video_path, output_dir):
    """
    Extract full audio from the entire video, re-encoded to AAC, and save as a single file.
    The output is saved in output_dir.
    """
    title = get_video_title(YOUTUBE_URL)
    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
    output_file = os.path.join(output_dir, f"{safe_title}.m4a")
    cmd = [
        FFMPEG_EXE_PATH,    # Path to the FFmpeg executable.
        "-y",               # Overwrite output files without prompting.
        "-i", video_path,   # Specify the input video file.
        "-vn",              # Disables video recording. This tells FFmpeg to ignore the video stream, so only the audio is processed.
        "-c:a", "aac",      # Specifies the audio codec to use. Here, "aac" means FFmpeg will encode the audio using the Advanced Audio Coding codec.
        "-b:a", "256k",     # Sets the audio bitrate to 256 kilobits per second. This determines the quality (and file size) of the output audio.
        output_file         # The output file path where the processed (extracted) audio will be saved.
    ]
    print(f"Extracting full audio from video to {output_file}")
    subprocess.run(cmd, check=True)
    print(f"Full audio saved as {output_file}")
    return output_file

def main():
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
        return

    segments = parse_config_file(CONFIG_PATH)
    if not segments:
        print("No valid timestamps found in config file.")
        if IS_AUDIO_ONLY_EXTRACTION:
            print("Config is empty. Extracting full audio from video...")
            extract_full_audio(video_file, output_dir=base_segments_folder)
        else:
            print("Skipping segmentation. Video will remain as downloaded.")
        return

    print(f"Parsed {len(segments)} segments from config file.")
    # Create a dedicated folder for this video's segments based on its title.
    title = get_video_title(YOUTUBE_URL)
    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')
    video_segments_folder = os.path.join(base_segments_folder, safe_title)
    os.makedirs(video_segments_folder, exist_ok=True)
    
    print("\nStep 2: Cutting video into segments...")
    cut_segments(video_file, segments, video_segments_folder)

if __name__ == "__main__":
    main()