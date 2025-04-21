import os
from config import Config
from models.video import Video
from services.youtube_service import YouTubeService
from services.ffmpeg_service import FFmpegService
from services.metadata_service import MetadataService
from services.timestamp_service import TimestampService
from utils.system_utils import SystemUtils


class YouTubeDownloader:
    UNKNOWN_TITLE = "unknown_title"

    def __init__(self):
        self.config = Config()
        self.youtube_service = YouTubeService(self.config)
        self.ffmpeg_service = FFmpegService(self.config)
        self.metadata_service = MetadataService(self.config)
        self.timestamp_service = TimestampService(self.config)

    def download_and_process(self):
        """Main method to download and process video."""
        try:
            # Configure console for UTF-8
            SystemUtils.configure_utf8_console()

            # Step 1: Download video
            print("\nStep 1: Downloading video...")
            video_file = self.youtube_service.download_video(self.config.youtube_url)
            if not video_file:
                print("Failed to download video.")
                return

            # Create Video object
            video = Video(
                url=self.config.youtube_url,
                title=self.youtube_service.get_video_title(self.config.youtube_url),
                id=self.youtube_service.get_video_id(self.config.youtube_url),
                file_path=video_file,
                duration=self.ffmpeg_service.get_video_duration(video_file),
            )

            # Create base segments folder
            base_segments_folder = os.path.join(
                self.config.extraction_folder_path, "segments"
            )
            os.makedirs(base_segments_folder, exist_ok=True)

            # Check for config file
            if not os.path.exists(self.config.config_path):
                print(
                    f"Config file not found at {self.config.config_path}. No segments will be cut."
                )
                if self.config.is_audio_only_extraction:
                    # Extract full audio instead
                    self.ffmpeg_service.extract_full_audio(
                        video_file,
                        output_dir=base_segments_folder,
                        title=video.title or self.UNKNOWN_TITLE,
                    )
                    # Update metadata
                    self.metadata_service.update_metadata(video)
                return

            # Parse timestamps
            segments = self.timestamp_service.parse_config_file()
            if not segments:
                print("No valid timestamps found in config file.")
                if self.config.is_audio_only_extraction:
                    print("Config is empty. Extracting full audio from video...")
                    self.ffmpeg_service.extract_full_audio(
                        video_file,
                        output_dir=base_segments_folder,
                        title=video.title or self.UNKNOWN_TITLE,
                    )
                    # Update metadata
                    self.metadata_service.update_metadata(video)
                else:
                    print("Skipping segmentation. Video will remain as downloaded.")
                return

            # Add segments to video object
            for segment in segments:
                video.add_segment(segment)

            print(f"Parsed {len(segments)} segments from config file.")

            # Create dedicated folder for segments
            safe_title = video.sanitized_title or self.UNKNOWN_TITLE
            video_segments_folder = os.path.join(base_segments_folder, safe_title)
            os.makedirs(video_segments_folder, exist_ok=True)

            # Cut video into segments
            print("\nStep 2: Cutting video into segments...")
            self.ffmpeg_service.cut_segments(
                video_file, segments, video_segments_folder
            )

            # Update metadata
            self.metadata_service.update_metadata(video)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    downloader = YouTubeDownloader()
    downloader.download_and_process()
