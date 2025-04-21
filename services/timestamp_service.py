import re
from models.video import VideoSegment


class TimestampService:
    def __init__(self, config):
        self.config = config

    def parse_config_file(self):
        """Parse timestamp config file into VideoSegment objects."""
        segments = []
        pattern = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+(.*)$")

        try:
            with open(self.config.config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    match = pattern.match(line)
                    if match:
                        timestamp = match.group(1)
                        full_name = match.group(2)
                        segments.append({"start": timestamp, "full_name": full_name})
                    else:
                        print("Line didn't match expected format:", line)
        except Exception as e:
            print(f"Error reading config file: {e}")
            return []

        # Convert to VideoSegment objects with index
        return [
            VideoSegment(seg["start"], seg["full_name"], idx + 1)
            for idx, seg in enumerate(segments)
        ]
