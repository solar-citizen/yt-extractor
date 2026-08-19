import os
import re
import subprocess
import threading
import traceback
from config import Config
from models.video import Video
from services.ffmpeg_service import FFmpegService
from services.timestamp_service import TimestampService
from services.metadata_service import MetadataService
from services.youtube_service import YouTubeService
from utils.file_utils import FileUtils


def _run_streaming(cmd: list, log_callback, progress_callback=None, progress_range=(0.0, 1.0)):
    """
    Run a subprocess, stream its stdout+stderr line by line to log_callback.
    If progress_callback is provided, parse yt-dlp '[download] X%' lines and
    map them into progress_range (start, end).
    Returns True on success, False on failure.
    """
    start, end = progress_range
    span = end - start

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue

            # Parse yt-dlp download progress lines
            if progress_callback:
                m = re.search(r"\[download\]\s+([\d.]+)%", line)
                if m:
                    pct = float(m.group(1)) / 100.0
                    val = start + pct * span
                    progress_callback(val, f"Downloading… {m.group(1)}%")
                    continue  # don't spam the console with raw progress lines

            log_callback(line + "\n")

        proc.wait()
        return proc.returncode == 0
    except Exception as e:
        log_callback(f"[subprocess error] {e}\n")
        return False


class ExtractionWorker(threading.Thread):
    def __init__(
        self,
        urls: list,
        audio_only: bool,
        use_timestamps: bool,
        format_selector,        # str like "137+bestaudio/best" or None
        cookie_browser: str | None,
        log_callback,
        progress_callback,      # fn(val: float, label: str)
        finish_callback,
        config: Config,
    ):
        super().__init__()
        self.urls = urls
        self.audio_only = audio_only
        self.use_timestamps = use_timestamps
        self.format_selector = format_selector
        self.cookie_browser = cookie_browser
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.config = config
        self.daemon = True

    def run(self):
        try:
            self._run()
            self.finish_callback(True)
        except Exception as e:
            self.log_callback(f"\n[FATAL ERROR] {e}\n{traceback.format_exc()}\n")
            self.finish_callback(False)

    def _run(self):
        self.config.is_audio_only_extraction = self.audio_only

        ffmpeg_service = FFmpegService(self.config)
        metadata_service = MetadataService(self.config)
        youtube_service = YouTubeService(self.config)
        timestamp_service = TimestampService(self.config)

        # Parse timestamps once
        segments = []
        if self.use_timestamps:
            if os.path.exists(self.config.timestamps_path):
                segments = timestamp_service.parse_config_file()
                self.log_callback(f"Loaded {len(segments)} timestamp segments.\n")
            else:
                self.log_callback("Warning: Timestamps file not found.\n")

        base_segments_folder = os.path.join(
            self.config.extraction_folder_path, "segments"
        )
        os.makedirs(base_segments_folder, exist_ok=True)

        total = len(self.urls)

        for i, url in enumerate(self.urls):
            url = url.strip()
            if not url:
                continue

            # Per-URL progress window: e.g. URL 0 of 3 → [0.00, 0.33]
            url_start = i / total
            url_end = (i + 1) / total
            # Download takes ~80% of per-URL budget; cutting takes ~20%
            dl_end = url_start + (url_end - url_start) * 0.80
            cut_end = url_end

            self.log_callback(f"\n{'='*60}\n")
            self.log_callback(f"[{i+1}/{total}] {url}\n")
            self.progress_callback(url_start, f"[{i+1}/{total}] Preparing download…")

            # --- Build yt-dlp download command ---
            title = youtube_service.get_video_title(url)
            if title:
                safe_title = FileUtils.sanitize_filename(title)
                safe_template = self.config.video_path_template.replace(
                    "%(title)s", safe_title
                )
            else:
                safe_template = self.config.video_path_template

            fmt = self._resolve_format()
            cmd = [
                "yt-dlp",
                "-o", safe_template,
            ]
            if self.cookie_browser and self.cookie_browser != "Cookies: None":
                browser_name = self.cookie_browser.replace("Cookies: ", "").strip()
                cmd.extend(["--cookies-from-browser", browser_name])
            else:
                # Use android client when not using cookies to avoid android_vr 403 Forbidden
                cmd.extend(["--extractor-args", "youtube:player_client=android"])

            cmd.extend(["-f", fmt, url])

            self.log_callback(f"Format: {fmt}\n")
            self.log_callback(f"Output template: {safe_template}\n\n")

            ok = _run_streaming(
                cmd,
                log_callback=self.log_callback,
                progress_callback=self.progress_callback,
                progress_range=(url_start, dl_end),
            )
            if not ok:
                self.log_callback(f"Download failed for: {url}\n")
                self.progress_callback(dl_end, f"[{i+1}/{total}] Download failed.")
                continue

            # Find the downloaded file
            video_file = youtube_service.get_existing_video(url)
            if not video_file:
                self.log_callback("Could not locate downloaded file.\n")
                continue

            self.log_callback(f"\nDownloaded: {video_file}\n")
            self.progress_callback(dl_end, f"[{i+1}/{total}] Download complete.")

            # Build Video object
            video = Video(
                url=url,
                title=title,
                id=youtube_service.get_video_id(url),
                file_path=video_file,
                duration=ffmpeg_service.get_video_duration(video_file),
            )

            # --- Cut or extract ---
            if segments:
                for seg in segments:
                    video.add_segment(seg)

                safe_title_folder = video.sanitized_title or "Unknown"
                video_segments_folder = os.path.join(base_segments_folder, safe_title_folder)
                self.log_callback(
                    f"\nCutting {len(segments)} segments into {video_segments_folder}…\n"
                )
                self.progress_callback(dl_end, f"[{i+1}/{total}] Cutting segments…")
                ffmpeg_service.cut_segments(video_file, segments, video_segments_folder)
            else:
                self.log_callback(f"\nExtracting full audio…\n")
                self.progress_callback(dl_end, f"[{i+1}/{total}] Extracting audio…")
                ffmpeg_service.extract_full_audio(
                    video_file,
                    output_dir=base_segments_folder,
                    title=title or "Unknown",
                )

            metadata_service.update_metadata(video)
            self.progress_callback(cut_end, f"[{i+1}/{total}] Done.")
            self.log_callback(f"\n[{i+1}/{total}] Finished: {title}\n")

        self.log_callback(f"\n{'='*60}\nAll URLs processed.\n")

    def _resolve_format(self) -> str:
        """Return the yt-dlp -f string to use."""
        if self.format_selector:
            return self.format_selector
        if self.audio_only:
            return "bestaudio/best"
        has_cookies = bool(self.cookie_browser and self.cookie_browser != "Cookies: None")
        if has_cookies:
            return "bestvideo+bestaudio/best"
        return "best/18/b"

