import re
from models.video import VideoSegment


class TimestampService:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def normalize_timestamp(ts: str) -> str:
        """Normalize M:SS, MM:SS, H:MM:SS to HH:MM:SS."""
        parts = [int(p) for p in ts.split(":")]
        if len(parts) == 2:
            return f"00:{parts[0]:02d}:{parts[1]:02d}"
        elif len(parts) == 3:
            return f"{parts[0]:02d}:{parts[1]:02d}:{parts[2]:02d}"
        return ts

    @classmethod
    def parse_line(cls, line: str) -> tuple[str, str] | None:
        """
        Parse a single timestamp line in various formats:
          - 0:00 - Title
          - 00:02:06 Hellfire 2
          - [02:06] Hellfire 2
          - (02:06) - Hellfire 2
          - 1. 02:06 - Hellfire 2
          - 00:00 - 02:06 Intro
          - 01:05:22 | Track Name
        Returns (normalized_timestamp, title) or None.
        """
        line = line.strip()
        if not line:
            return None

        # Strip optional leading list numbering like "1. ", "01) ", "[1] ", "- ", "* "
        cleaned = re.sub(r"^(?:\d+[\.\)]\s*|\[\d+\]\s*|[-\*]\s*)", "", line)

        # Match timestamp (M:SS, MM:SS, H:MM:SS, HH:MM:SS) and title
        match = re.match(
            r"^[\[\(]?(\d{1,2}:\d{2}(?::\d{2})?)[\]\)]?"
            r"(?:\s*[-–—]\s*[\[\(]?\d{1,2}:\d{2}(?::\d{2})?[\]\)]?)?"
            r"(?:\s*[-–—|:]\s*|\s+)"
            r"(.*)$",
            cleaned,
        )
        if match:
            raw_ts = match.group(1)
            title = match.group(2).strip()
            # Clean title from any leading separators like "- ", "| ", ": "
            title = re.sub(r"^[-–—|:]\s*", "", title).strip()
            if not title:
                title = f"Segment {cls.normalize_timestamp(raw_ts)}"
            return cls.normalize_timestamp(raw_ts), title

        return None

    def parse_config_file(self):
        """Parse timestamp config file into VideoSegment objects."""
        segments = []

        with open(self.config.timestamps_path, "r", encoding="utf-8") as f:
            for line in f:
                parsed = self.parse_line(line)
                if parsed:
                    ts, title = parsed
                    segments.append({"start": ts, "full_name": title})
                else:
                    if line.strip():
                        print("Line didn't match expected timestamp format:", line.strip())

        # Convert to VideoSegment objects with index
        return [
            VideoSegment(seg["start"], seg["full_name"], idx + 1)
            for idx, seg in enumerate(segments)
        ]

