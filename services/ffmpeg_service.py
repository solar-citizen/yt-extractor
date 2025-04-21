import os
from utils.system_utils import SystemUtils
from utils.file_utils import FileUtils


class FFmpegService:
    def __init__(self, config):
        self.config = config

    def get_video_duration(self, video_path):
        """Use ffprobe to retrieve the total duration of the video in seconds."""
        cmd = [
            self.config.ffprobe_cmd,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = SystemUtils.run_subprocess(cmd)
        if result and result.stdout:
            try:
                return float(result.stdout.strip())
            except ValueError:
                print(
                    f"Error converting duration string to float: '{result.stdout.strip()}'"
                )
        return None

    def seconds_to_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS.mmm format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def cut_segments(self, video_file, segments, output_dir):
        """Cut video into segments based on timestamps."""
        os.makedirs(output_dir, exist_ok=True)
        total_duration = self.get_video_duration(video_file)
        if total_duration is None:
            print("Could not retrieve video duration.")
            return

        total_duration_ts = self.seconds_to_timestamp(total_duration)
        num_segments = len(segments)

        # Configure UTF-8 console
        SystemUtils.configure_utf8_console()

        for i, segment in enumerate(segments):
            start = segment.start
            end = segments[i + 1].start if i < num_segments - 1 else total_duration_ts
            safe_label = FileUtils.sanitize_filename(segment.numbered_label)

            if self.config.is_audio_only_extraction:
                output_file = os.path.join(output_dir, f"{safe_label}.m4a")
                cmd = [
                    self.config.ffmpeg_cmd,
                    "-y",
                    "-i",
                    video_file,
                    "-ss",
                    start,
                    "-to",
                    end,
                    "-vn",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "256k",
                    output_file,
                ]
            else:
                output_file = os.path.join(output_dir, f"{safe_label}.mp4")
                cmd = [
                    self.config.ffmpeg_cmd,
                    "-y",
                    "-i",
                    video_file,
                    "-ss",
                    start,
                    "-to",
                    end,
                    "-c",
                    "copy",
                    output_file,
                ]

            print(f"Cutting segment: {segment.numbered_label} from {start} to {end}")
            print(f"Output file: {output_file}")

            SystemUtils.run_subprocess(cmd, show_progress=True)
            print(f"Segment saved as {output_file}")

    def extract_full_audio(self, video_path, output_dir, title):
        """Extract full audio from video file."""
        from utils.file_utils import FileUtils

        os.makedirs(output_dir, exist_ok=True)
        safe_title = FileUtils.sanitize_filename(title)
        output_file = os.path.join(output_dir, f"{safe_title}.m4a")

        cmd = [
            self.config.ffmpeg_cmd,
            "-y",
            "-i",
            video_path,
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            output_file,
        ]

        print(f"Extracting full audio from video to {output_file}")
        SystemUtils.run_subprocess(cmd, show_progress=True)
        print(f"Full audio saved as {output_file}")

        return output_file
