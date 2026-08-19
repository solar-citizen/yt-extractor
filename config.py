import json
import os
from datetime import datetime
from dotenv import load_dotenv


class Config:
    def __init__(self):
        self.config_data_dir = "config_data"
        self.settings_file = os.path.join(self.config_data_dir, "settings.json")

        load_dotenv()

        # Load extraction folder with priority: settings.json -> .env -> default ~/yt-extractor-extractions
        self.extraction_folder_path = self._load_extraction_folder()

        # Create extraction folder if it doesn't exist
        os.makedirs(self.extraction_folder_path, exist_ok=True)

        # Paths
        self.video_path_template = os.path.join(
            self.extraction_folder_path, "%(title)s.%(ext)s"
        )
        self.urls_file_path = os.path.join(self.config_data_dir, "urls.txt")
        self.timestamps_path = os.path.join(self.config_data_dir, "timestamps.txt")
        self.metadata_path = os.path.join(self.config_data_dir, "video_metadatas.json")

        # Settings
        self.is_audio_only_extraction = True

        # External commands
        self.ffmpeg_cmd = "ffmpeg"
        self.ffprobe_cmd = "ffprobe"

    def _load_extraction_folder(self):
        # 1. Check settings.json
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    folder = data.get("extraction_folder_path")
                    if folder and os.path.isdir(folder):
                        return folder
            except Exception:
                pass

        # 2. Check .env
        env_folder = os.getenv("EXTRACTION_FOLDER_PATH")
        if env_folder:
            return env_folder

        # 3. Fallback default
        default_folder = os.path.join(
            os.path.expanduser("~"), "yt-extractor-extractions"
        )
        return default_folder

    def set_extraction_folder(self, folder_path: str):
        """Update extraction folder and save to settings.json."""
        if not folder_path:
            return
        self.extraction_folder_path = folder_path
        os.makedirs(self.extraction_folder_path, exist_ok=True)
        self.video_path_template = os.path.join(
            self.extraction_folder_path, "%(title)s.%(ext)s"
        )

        os.makedirs(self.config_data_dir, exist_ok=True)
        settings = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception:
                pass
        settings["extraction_folder_path"] = folder_path
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def _get_required_env(self, key):
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"{key} environment variable is not set")
        return value

