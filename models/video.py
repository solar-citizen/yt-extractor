from datetime import datetime
import pytz


class VideoSegment:
    def __init__(self, start, full_name, index=None):
        self.start = start
        self.full_name = full_name
        self.index = index
        self.numbered_label = (
            f"{index}. {full_name}" if index is not None else full_name
        )


class Video:
    def __init__(self, url, title=None, id=None, file_path=None, duration=None):
        self.url = url
        self.title = title
        self.id = id
        self.file_path = file_path
        self.duration = duration
        self.segments = []

    def add_segment(self, segment):
        self.segments.append(segment)

    def to_metadata_dict(self, time_zone):
        """Convert video object to metadata dictionary format"""
        return {
            "yt_id": self.id,
            "yt_name": self.title,
            "local_name": self.sanitized_title,
            "yt_link": self.url,
            "yt_duration": self.duration,
            "segments": len(self.segments),
            "insert_date": datetime.now(pytz.timezone(time_zone)).isoformat(),
        }

    @property
    def sanitized_title(self):
        from utils.file_utils import FileUtils

        return FileUtils.sanitize_filename(self.title) if self.title else None
