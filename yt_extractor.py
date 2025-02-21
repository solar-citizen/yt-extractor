import subprocess
import re
import os
import json
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

VIDEO_PATH = "video.webm" # toDo: use only name, format might differ
CONFIG_PATH = os.path.join("config", "timestamps.txt")

def download_video(url, output):
    """
    Download the video from YouTube using yt-dlp, but only if a local file
    doesn't exist or its duration doesn't match the online video's duration.
    """
    if os.path.exists(output):
        local_duration = get_video_duration(output)
        print(f"Local file '{output}' exists with duration: {local_duration} seconds.")
        
        # Get online video duration via yt-dlp (using JSON output)
        try:
            cmd = ["yt-dlp", "--skip-download", "--print-json", url]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(result.stdout)
            online_duration = info.get("duration")
            print(f"Online video duration: {online_duration} seconds.")
        except Exception as e:
            print("Error extracting online duration:", e)
            online_duration = None
        
        # If both durations are available, compare them (allow 1 second tolerance)
        if online_duration is not None and local_duration is not None:
            if abs(local_duration - online_duration) < 1:
                print("Local video file exists and duration matches. Skipping download.")
                return
            else:
                print("Local video duration differs from online video. Redownloading...")
        else:
            print("Could not determine durations. Proceeding to download.")
    
    # Proceed to download the video
    cmd = ["yt-dlp", "-o", output, url]
    print("Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Downloaded video as {output}")

def get_video_duration(video_path):
    """
    Use ffprobe to retrieve the total duration of the video in seconds.
    """

    cmd = [FFPROBE_EXE_PATH, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration_str = result.stdout.strip()
    try:
        duration = float(duration_str)
    except ValueError:
        duration = None
    return duration

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
    
    Expected line format (one per chapter):
      HH:MM:SS Chapter Title - Author

    Returns a list of dictionaries with keys:
      "start": starting timestamp (as string),
      "clip_name": chapter title,
      "author": author,
      "label": a combined label for naming the output file.
    """

    segments = []
   
    # toDo: remove regexp
    # Pattern: capture a timestamp, then the chapter title, a dash, and the author.
    pattern = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+(.*?)\s*-\s*(.+)$")
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if m:
                start_time = m.group(1)
                clip_name = m.group(2)
                author = m.group(3)
                segments.append({
                    "start": start_time,
                    "clip_name": clip_name,
                    "author": author,
                    "label": f"{clip_name} - {author}"
                })
            else:
                print("Line didn't match expected format:", line)
    return segments

def cut_segments(video_path, segments, output_dir="segments"):
    """
    Use FFmpeg to cut segments from the video.
    Each segment is defined by its start time and the start time of the next segment,
    with the final segment running to the end of the video.
    
    Output files are stored in the specified output directory.
    """

    os.makedirs(output_dir, exist_ok=True)
    
    # Get total video duration
    total_duration = get_video_duration(video_path)
    
    if total_duration is None:
        print("Could not retrieve video duration.")
        return
    total_duration_ts = seconds_to_timestamp(total_duration)
    
    num_segments = len(segments)
    for i, seg in enumerate(segments):
        start = seg["start"]
        # Determine end time: next segment's start or video duration for the last segment.
        if i < num_segments - 1:
            end = segments[i + 1]["start"]
        else:
            end = total_duration_ts
        
        # Sanitize output file name (remove forbidden characters)
        label = seg["label"]
        safe_label = "".join(c for c in label if c not in r'\/:*?"<>|')
        output_file = os.path.join(output_dir, f"{safe_label}.mp4")
        
        cmd = [FFMPEG_EXE_PATH, "-y", "-i", video_path, "-ss", start, "-to", end, "-c", "copy", output_file]
        print(f"Cutting segment: {label} from {start} to {end}")
        subprocess.run(cmd, check=True)
        print(f"Segment saved as {output_file}")

def main():
    print("\nStep 1: Downloading video...")
    download_video(YOUTUBE_URL, VIDEO_PATH)

    # Path to the configuration file with timestamps (e.g., config/timestamps.txt)
    print("\nStep 2: Reading config file...")
    
    
    if not os.path.exists(CONFIG_PATH):
        print(f"Config file not found at {CONFIG_PATH}.")
        return

    print("\nStep 3: Parsing config file...")
    segments = parse_config_file(CONFIG_PATH)

    if not segments:
        print("No valid timestamps found in config file. Exiting.")
        return
    print(f"Parsed {len(segments)} segments from config file.")

    print("\nStep 4: Cutting video on segments...")
    cut_segments(VIDEO_PATH, segments)

if __name__ == "__main__":
    main()
