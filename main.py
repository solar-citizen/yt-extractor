import os
from config import Config
from models.video import Video
from services.youtube_service import YouTubeService
from services.ffmpeg_service import FFmpegService
from services.metadata_service import MetadataService
from services.timestamp_service import TimestampService
from utils.system_utils import SystemUtils


class YouTubeDownloader:
    def __init__(self):
        self.config = Config()
        self.youtube_service = YouTubeService(self.config)
        self.ffmpeg_service = FFmpegService(self.config)
        self.metadata_service = MetadataService(self.config)
        self.timestamp_service = TimestampService(self.config)

    def _process_url(self, url):
        """Process a single YouTube URL."""

        unknown_title = "Unknown title"
        download_title = "Downloading video..."
        cut_title = "Cutting video into segments..."
        complete_extract_title = f"[No valid timestamps found in a timestamps config file.] \n[Extracting full audio from video...]"

        has_config = os.path.exists(self.config.timestamps_path)
        segments = []

        # Step 1: Download video
        print(f"\n[{download_title}]\n")
        video_file = self.youtube_service.download_video(url)
        if not video_file:
            print("Failed to download video.")
            return

        # Create Video object
        video = Video(
            url=url,
            title=self.youtube_service.get_video_title(url),
            id=self.youtube_service.get_video_id(url),
            file_path=video_file,
            duration=self.ffmpeg_service.get_video_duration(video_file),
        )

        # Create base segments folder
        base_segments_folder = os.path.join(
            self.config.extraction_folder_path, "segments"
        )
        os.makedirs(base_segments_folder, exist_ok=True)

        if not has_config:
            print(
                f"Config file not found at {self.config.timestamps_path}. Creating empty file."
            )
            os.makedirs(os.path.dirname(self.config.timestamps_path), exist_ok=True)
        else:
            # Parse timestamps
            segments = self.timestamp_service.parse_config_file()

            if segments:
                # Add segments to video object
                for segment in segments:
                    video.add_segment(segment)

                print(f"Parsed {len(segments)} segments from config file.")

                # Create dedicated folder for segments
                safe_title = video.sanitized_title or unknown_title
                video_segments_folder = os.path.join(base_segments_folder, safe_title)
                os.makedirs(video_segments_folder, exist_ok=True)

                # Step 2a: Cut video into segments
                print(f"\n[{cut_title}]\n")
                self.ffmpeg_service.cut_segments(
                    video_file, segments, video_segments_folder
                )
            else:
                # Step 2b: Extract full video
                print(f"\n{complete_extract_title}\n")
                if self.config.is_audio_only_extraction:
                    self.ffmpeg_service.extract_full_audio(
                        video_file,
                        output_dir=base_segments_folder,
                        title=video.title or unknown_title,
                    )
                else:
                    print("Skipping segmentation. Video will remain as downloaded.")

        # Update metadata
        self.metadata_service.update_metadata(video)

    def _read_urls_from_file(self):
        """Read and return list of URLs from the URLs file."""
        # Check if the URLs file exists
        if not os.path.exists(self.config.urls_file_path):
            print(
                f"URLs file not found at {self.config.urls_file_path}. Creating empty file."
            )
            os.makedirs(os.path.dirname(self.config.urls_file_path), exist_ok=True)
            with open(self.config.urls_file_path, "w", encoding="utf-8") as f:
                f.write("# Add one YouTube URL per line\n")
            print(f"Please add URLs to {self.config.urls_file_path} and run again.")
            return []

        # Read URLs from file
        urls = []
        with open(self.config.urls_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    urls.append(line)

        if not urls:
            print(f"No valid URLs found in {self.config.urls_file_path}.")
            print("Please add URLs to the file and run again.")
        else:
            print(f"Found {len(urls)} URLs to process.")

        return urls

    def process_urls(self, urls):
        """Process a list of YouTube URLs."""
        # Process each URL
        for index, url in enumerate(urls):
            print(f"\n{'=' * 80}")
            print(f"Processing URL {index+1}/{len(urls)}: {url}")
            print(f"{'=' * 80}")

            try:
                self._process_url(url)
            except Exception as e:
                print(f"Error processing URL {url}: {e}")
                import traceback

                traceback.print_exc()

    def run(self):
        """Main method to run the YouTube downloader."""
        # Configure console for UTF-8
        SystemUtils.configure_utf8_console()

        # Get URLs
        urls = self._read_urls_from_file()

        # Process URLs if any were found
        if urls:
            self.process_urls(urls)


if __name__ == "__main__":
    downloader = YouTubeDownloader()
    downloader.run()
