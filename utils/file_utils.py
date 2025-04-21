import glob
import os
import sys
import unicodedata


class FileUtils:
    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize a filename by removing/replacing characters that are not allowed in filenames
        across different operating systems, while preserving Unicode characters.
        """
        # Normalize Unicode characters
        filename = unicodedata.normalize("NFC", filename)

        # Replace characters that are invalid for filenames
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "-")

        # Remove or replace any other problematic characters
        filename = filename.replace("\n", " ").replace("\r", " ")

        # Remove leading/trailing spaces and dots
        filename = filename.strip(". ")

        # Transliterate non-ASCII characters to ASCII equivalents if on Windows
        if sys.platform == "win32":
            try:
                filename.encode("ascii")
            except UnicodeEncodeError:
                transliterated = ""
                for char in filename:
                    try:
                        char.encode("ascii")
                        transliterated += char
                    except UnicodeEncodeError:
                        simplified = unicodedata.normalize("NFKD", char)
                        ascii_char = "".join(c for c in simplified if ord(c) < 128)
                        transliterated += ascii_char if ascii_char else "-"
                filename = transliterated

        # Ensure the filename is not empty after sanitization
        if not filename:
            filename = "unnamed_file"

        return filename

    @staticmethod
    def find_file_by_pattern(base_path, pattern):
        """Find files matching a glob pattern"""
        return glob.glob(os.path.join(base_path, pattern))

    @staticmethod
    def find_newest_file(folder_path, extension="*"):
        """Find the most recently created file in a directory with optional extension filter"""
        files = glob.glob(os.path.join(folder_path, f"*.{extension}"))
        if not files:
            return None
        return max(files, key=os.path.getctime)
