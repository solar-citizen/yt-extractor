import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()

        # Required environment variables
        self.youtube_url = self._get_required_env("YOUTUBE_URL")
        self.timezone = self._get_required_env("PY_TZ")
        self.extraction_folder_path = self._get_required_env("EXTRACTION_FOLDER_PATH")

        # Create extraction folder if it doesn't exist
        if not os.path.exists(self.extraction_folder_path):
            os.makedirs(self.extraction_folder_path, exist_ok=True)

        # Paths
        self.video_path_template = os.path.join(
            self.extraction_folder_path, "%(title)s.%(ext)s"
        )
        self.config_path = os.path.join("config", "timestamps.txt")
        self.metadata_path = os.path.join("config", "video_metadatas.json")

        # Settings
        self.is_audio_only_extraction = True

        # External commands
        self.ffmpeg_cmd = "ffmpeg"
        self.ffprobe_cmd = "ffprobe"

    def _get_required_env(self, key):
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"{key} environment variable is not set")
        return value
