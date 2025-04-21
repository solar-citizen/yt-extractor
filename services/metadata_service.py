import os
import json


class MetadataService:
    def __init__(self, config):
        self.config = config

    def load_metadata(self):
        """Load video metadata from JSON file."""
        if os.path.exists(self.config.metadata_path):
            try:
                with open(self.config.metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error loading metadata file: {e}")
                return {}
        return {}

    def save_metadata(self, metadata):
        """Save video metadata to JSON file."""
        os.makedirs(os.path.dirname(self.config.metadata_path), exist_ok=True)
        try:
            with open(self.config.metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving metadata file: {e}")

    def update_metadata(self, video):
        """Update metadata with video information."""
        metadata = self.load_metadata()

        # Check if video already exists in metadata by YouTube ID
        for key, value in metadata.items():
            if value.get("yt_id") == video.id:
                print(
                    f"Video ID {video.id} already exists in metadata. Skipping update."
                )
                return

        # Find the highest existing numeric ID and increment by 1
        next_id = 1
        for key in metadata:
            if key.isdigit() and int(key) >= next_id:
                next_id = int(key) + 1

        # Add new video entry with sequential ID
        metadata[str(next_id)] = video.to_metadata_dict()

        self.save_metadata(metadata)
        print(f"Updated metadata for video {video.id}: {video.title} (ID: {next_id})")
