import re
import time
import os
from utils.file_utils import FileUtils
from utils.system_utils import SystemUtils
from services.ffmpeg_service import FFmpegService


class YouTubeService:
    def __init__(self, config):
        self.config = config

    def get_video_id(self, url):
        """Extract the YouTube video ID from a URL."""
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/.*?v=([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        print(f"Warning: Could not extract video ID from URL: {url}")
        return None

    def get_video_title(self, url):
        """Return the video's title using yt-dlp."""
        cmd = [
            "yt-dlp",
            "--get-title",
            url,
        ]
        result = SystemUtils.run_subprocess(cmd)
        if result and result.stdout:
            return result.stdout.strip()
        return None

    def get_existing_video(self, url):
        """Search for an existing video file matching the downloaded video."""
        title = self.get_video_title(url)
        if not title:
            return None

        # Sanitize the title for safe file operations
        safe_title = FileUtils.sanitize_filename(title)

        # Create a pattern for glob matching
        pattern = self.config.video_path_template.replace("%(title)s", safe_title)
        pattern = pattern.replace("%(ext)s", "*")

        # Find matching files
        files = FileUtils.find_file_by_pattern("", pattern)

        # If no files found with the sanitized title, try a more flexible search
        if not files:
            print(f"No files found with pattern: {pattern}")
            print("Trying more flexible search...")
            # Extract the main part of the title (before special characters)
            base_title = (
                safe_title.split("[")[0].strip()
                if "[" in safe_title
                else safe_title.split("{")[0].strip()
            )
            base_pattern = self.config.video_path_template.replace(
                "%(title)s", base_title + "*"
            )
            base_pattern = base_pattern.replace("%(ext)s", "*")
            files = FileUtils.find_file_by_pattern("", base_pattern)

            if files:
                print(f"Found file with flexible search: {files[0]}")

        if files:
            return files[0]
        return None

    def download_video(self, url):
        """Download the video from YouTube using yt-dlp."""
        # Check for existing file
        existing_file = self.get_existing_video(url)
        if existing_file:
            # Check if the file is complete/valid by comparing durations
            local_duration = FFmpegService(self.config).get_video_duration(
                existing_file
            )
            print(
                f"Local file '{existing_file}' exists with duration: {local_duration} seconds."
            )

            # Get online duration for comparison
            online_duration = self._get_online_duration(url)

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

        # Prepare download with sanitized title
        title = self.get_video_title(url)
        if title:
            safe_title = FileUtils.sanitize_filename(title)
            safe_template = self.config.video_path_template.replace(
                "%(title)s", safe_title
            )
            safe_template = safe_template.replace(".%(ext)s", ".%(ext)s")
        else:
            safe_template = self.config.video_path_template

        # Download the video
        cmd = [
            "yt-dlp",
            "-o",
            safe_template,
            url,
        ]
        result = SystemUtils.run_subprocess(cmd, show_progress=True)

        # Allow some time for file system to update
        time.sleep(1)

        # Try to find the downloaded file
        downloaded_file = self.get_existing_video(url)
        if downloaded_file:
            print(f"Downloaded video as {downloaded_file}")
            return downloaded_file
        else:
            # Direct search in the extraction folder for recently created files
            print(
                "Download completed, but file not found using the template. Searching directory..."
            )
            all_files = FileUtils.find_file_by_pattern(
                self.config.extraction_folder_path, "*.*"
            )

            # Sort by creation time, newest first
            all_files.sort(key=os.path.getctime, reverse=True)

            if all_files:
                print(f"Using most recently created file: {all_files[0]}")
                return all_files[0]
            else:
                print("No files found in extraction directory.")
                return None

    def _get_online_duration(self, url):
        """Get the duration of the online video without downloading."""
        try:
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--print-json",
                url,
            ]
            result = SystemUtils.run_subprocess(cmd)
            if result and result.stdout:
                import json

                info = json.loads(result.stdout)
                online_duration = info.get("duration")
                print(f"Online video duration: {online_duration} seconds.")
                return online_duration
        except Exception as e:
            print("Error extracting online duration:", e)
        return None
