import json
import os
import subprocess
import threading
from tkinter import filedialog

import customtkinter as ctk

from config import Config
from gui.workers import ExtractionWorker
from services.timestamp_service import TimestampService

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = Config()

        self.title("yt-extractor Pro")
        self.geometry("960x700")
        self.minsize(800, 600)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tab_download = self.tabview.add("Download")
        self.tab_timestamps = self.tabview.add("Timestamps")
        self.tab_history = self.tabview.add("History & Metadata")

        self.setup_download_tab()
        self.setup_timestamps_tab()
        self.setup_history_tab()

    # ------------------------------------------------------------------ #
    #  Download Tab
    # ------------------------------------------------------------------ #

    def setup_download_tab(self):
        self.tab_download.grid_rowconfigure(5, weight=1)
        self.tab_download.grid_columnconfigure(0, weight=1)

        # Folder picker row
        folder_frame = ctk.CTkFrame(self.tab_download, fg_color="transparent")
        folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        folder_frame.grid_columnconfigure(1, weight=1)

        folder_lbl = ctk.CTkLabel(
            folder_frame, text="Extraction Folder:", font=("Helvetica", 12, "bold")
        )
        folder_lbl.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.folder_var = ctk.StringVar(value=self.config.extraction_folder_path)
        self.folder_entry = ctk.CTkEntry(
            folder_frame, textvariable=self.folder_var, state="readonly"
        )
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            folder_frame, text="Browse…", width=90, command=self.browse_extraction_folder
        )
        self.browse_btn.grid(row=0, column=2, sticky="e")

        # URL label + textbox
        lbl = ctk.CTkLabel(
            self.tab_download,
            text="YouTube URLs (one per line):",
            font=("Helvetica", 14, "bold"),
        )
        lbl.grid(row=1, column=0, sticky="w", padx=10, pady=(6, 2))

        self.url_textbox = ctk.CTkTextbox(self.tab_download, height=95)
        self.url_textbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=2)

        if os.path.exists(self.config.urls_file_path):
            with open(self.config.urls_file_path, "r", encoding="utf-8") as f:
                self.url_textbox.insert("0.0", f.read())

        # Quality row
        quality_frame = ctk.CTkFrame(self.tab_download, fg_color="transparent")
        quality_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 4))

        self.fetch_btn = ctk.CTkButton(
            quality_frame,
            text="Fetch Qualities",
            width=130,
            command=self.fetch_qualities,
        )
        self.fetch_btn.pack(side="left", padx=(0, 10))

        self.quality_var = ctk.StringVar(value="best (default)")
        self.quality_combo = ctk.CTkComboBox(
            quality_frame,
            variable=self.quality_var,
            values=["best (default)"],
            width=380,
            state="readonly",
        )
        self.quality_combo.pack(side="left")

        self.quality_status = ctk.CTkLabel(
            quality_frame, text="", text_color="gray", font=("Helvetica", 11)
        )
        self.quality_status.pack(side="left", padx=10)

        # Options row
        opts_frame = ctk.CTkFrame(self.tab_download, fg_color="transparent")
        opts_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=6)

        self.audio_switch = ctk.CTkSwitch(opts_frame, text="Audio Only")
        self.audio_switch.pack(side="left", padx=10)

        self.timestamps_switch = ctk.CTkSwitch(opts_frame, text="Use Timestamps Slicing")
        self.timestamps_switch.pack(side="left", padx=10)

        self.cookie_var = ctk.StringVar(value="Cookies: None")
        self.cookie_combo = ctk.CTkComboBox(
            opts_frame,
            variable=self.cookie_var,
            values=["Cookies: None", "chrome", "firefox", "brave", "edge", "chromium", "opera"],
            width=140,
            state="readonly",
        )
        self.cookie_combo.pack(side="left", padx=10)

        self.start_btn = ctk.CTkButton(
            opts_frame,
            text="Start Extraction",
            command=self.start_extraction,
            fg_color="#10B981",
            hover_color="#059669",
        )
        self.start_btn.pack(side="right", padx=10)

        # Progress + console
        bottom_frame = ctk.CTkFrame(self.tab_download)
        bottom_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=10)
        bottom_frame.grid_rowconfigure(2, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(
            bottom_frame, text="Idle", font=("Helvetica", 11), text_color="gray"
        )
        self.progress_label.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

        self.progress_bar = ctk.CTkProgressBar(bottom_frame)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 6))
        self.progress_bar.set(0)

        self.console = ctk.CTkTextbox(
            bottom_frame, state="disabled", font=("Courier", 11)
        )
        self.console.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def browse_extraction_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.config.extraction_folder_path)
        if chosen:
            self.config.set_extraction_folder(chosen)
            self.folder_var.set(chosen)
            self.log_message(f"Extraction folder updated: {chosen}\n")

    def fetch_qualities(self):
        urls_text = self.url_textbox.get("0.0", "end")
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        if not urls:
            self.quality_status.configure(text="No URL entered.", text_color="red")
            return

        url = urls[0]  # inspect the first URL only
        self.fetch_btn.configure(state="disabled", text="Fetching…")
        self.quality_status.configure(text="Querying yt-dlp…", text_color="gray")
        self.quality_combo.configure(values=["best (default)"])
        self.quality_var.set("best (default)")

        def _run():
            try:
                cmd = ["yt-dlp", "-F"]
                cookie_browser = self.cookie_var.get()
                if cookie_browser and cookie_browser != "Cookies: None":
                    browser_name = cookie_browser.replace("Cookies: ", "").strip()
                    cmd.extend(["--cookies-from-browser", browser_name])
                cmd.append(url)

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                lines = (result.stdout or "").splitlines()
                formats = self._parse_format_list(lines)
            except Exception as e:
                formats = []
                self.after(
                    0,
                    lambda: self.quality_status.configure(
                        text=f"Error: {e}", text_color="red"
                    ),
                )
            self.after(0, lambda: self._apply_qualities(formats))

        threading.Thread(target=_run, daemon=True).start()

    def _parse_format_list(self, lines: list) -> list:
        """
        Parse `yt-dlp -F` output into clean, sorted human-readable options.
        """
        options = ["best (default)", "bestaudio (audio only)"]
        video_formats = []

        for line in lines:
            if line.count("|") < 2:
                continue

            cols = line.split("|")
            left = cols[0].split()
            if not left:
                continue

            fmt_id = left[0]
            if not (fmt_id.isdigit() or fmt_id[:2] in ("sb", "hd")):
                continue

            ext = left[1] if len(left) > 1 else "?"
            res = left[2] if len(left) > 2 else "?"
            fps = left[3] if len(left) > 3 and left[3].isdigit() else ""

            if ext == "mhtml" or res == "audio" or "storyboard" in line:
                continue

            # Middle column: filesize
            mid = cols[1].split()
            filesize = mid[0] if mid else ""
            if filesize in ("https", "m3u8", "mhtml"):
                filesize = ""

            # Right column: codec
            right = cols[2].split()
            vcodec = right[0] if right else ""

            # Extract numeric height for sorting (e.g. 1080 from 1920x1080)
            height = 0
            quality_label = res
            if "x" in res:
                try:
                    height = int(res.split("x")[1])
                    quality_label = f"{height}p"
                except ValueError:
                    pass
            elif res.endswith("p") and res[:-1].isdigit():
                height = int(res[:-1])

            fps_str = f" {fps}fps" if fps and fps != "30" else ""
            size_str = f" | {filesize}" if filesize else ""
            label = f"{fmt_id} | {quality_label}{fps_str} ({res}) | {ext} | {vcodec}{size_str}"
            video_formats.append((height, label))

        # Sort highest resolution first
        video_formats.sort(key=lambda x: x[0], reverse=True)
        for _, label in video_formats:
            options.append(label)

        return options

    def _apply_qualities(self, formats: list):
        if len(formats) <= 2:
            self.quality_status.configure(
                text="No formats found or private video.", text_color="orange"
            )
        else:
            self.quality_status.configure(
                text=f"{len(formats) - 2} quality options found.", text_color="green"
            )
        self.quality_combo.configure(values=formats)
        self.quality_var.set(formats[0])
        self.fetch_btn.configure(state="normal", text="Fetch Qualities")

    def _selected_format(self):
        """Convert combo selection to a yt-dlp -f argument, or None for default."""
        val = self.quality_var.get()
        if val.startswith("best (default)"):
            return None  # worker decides based on audio_only switch
        if val.startswith("bestaudio"):
            return "bestaudio/best"
        fmt_id = val.split("|")[0].strip()
        if fmt_id in ("18", "22"):
            return fmt_id
        return f"{fmt_id}+bestaudio/{fmt_id}/best"

    # ------------------------------------------------------------------ #
    #  Thread-safe GUI helpers
    # ------------------------------------------------------------------ #

    def log_message(self, msg: str):
        """Called from worker thread — schedule on main thread."""
        self.after(0, self._log_message_ui, msg)

    def _log_message_ui(self, msg: str):
        self.console.configure(state="normal")
        self.console.insert("end", msg)
        self.console.see("end")
        self.console.configure(state="disabled")

    def update_progress(self, val: float, label: str = ""):
        """Called from worker thread — schedule on main thread."""
        self.after(0, self._update_progress_ui, val, label)

    def _update_progress_ui(self, val: float, label: str):
        self.progress_bar.set(val)
        if label:
            self.progress_label.configure(text=label, text_color="gray")

    def extraction_finished(self, success: bool):
        """Called from worker thread — schedule on main thread."""
        self.after(0, self._extraction_finished_ui, success)

    def _extraction_finished_ui(self, success: bool):
        status = "Done!" if success else "Finished with errors."
        color = "green" if success else "red"
        self.progress_label.configure(text=status, text_color=color)
        if success:
            self.progress_bar.set(1.0)
        self.start_btn.configure(state="normal", text="Start Extraction")
        self.load_history()

    # ------------------------------------------------------------------ #
    #  Actions
    # ------------------------------------------------------------------ #

    def start_extraction(self):
        urls_text = self.url_textbox.get("0.0", "end")
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        if not urls:
            self.log_message("Error: No URLs provided.\n")
            return

        os.makedirs(os.path.dirname(self.config.urls_file_path), exist_ok=True)
        with open(self.config.urls_file_path, "w", encoding="utf-8") as f:
            f.write(urls_text)

        self.start_btn.configure(state="disabled", text="Extracting…")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting…", text_color="gray")

        # Clear console on each new run
        self.console.configure(state="normal")
        self.console.delete("0.0", "end")
        self.console.configure(state="disabled")

        cookie_browser = self.cookie_var.get()

        worker = ExtractionWorker(
            urls=urls,
            audio_only=self.audio_switch.get() == 1,
            use_timestamps=self.timestamps_switch.get() == 1,
            format_selector=self._selected_format(),
            cookie_browser=cookie_browser,
            log_callback=self.log_message,
            progress_callback=self.update_progress,
            finish_callback=self.extraction_finished,
            config=self.config,
        )
        worker.start()

    # ------------------------------------------------------------------ #
    #  Timestamps Tab
    # ------------------------------------------------------------------ #

    def setup_timestamps_tab(self):
        self.tab_timestamps.grid_rowconfigure(1, weight=1)
        self.tab_timestamps.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            self.tab_timestamps,
            text="Paste Timestamps (Any format: 0:00 - Title, 00:00:00 Title, [02:06] Title, etc.):",
            font=("Helvetica", 14, "bold"),
        )
        lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.ts_textbox = ctk.CTkTextbox(self.tab_timestamps)
        self.ts_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        if os.path.exists(self.config.timestamps_path):
            with open(self.config.timestamps_path, "r", encoding="utf-8") as f:
                self.ts_textbox.insert("0.0", f.read())

        # Action buttons row
        actions_frame = ctk.CTkFrame(self.tab_timestamps, fg_color="transparent")
        actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        self.ts_status_label = ctk.CTkLabel(
            actions_frame, text="", text_color="gray", font=("Helvetica", 12)
        )
        self.ts_status_label.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(
            actions_frame, text="Save Timestamps", command=self.save_timestamps, fg_color="#10B981", hover_color="#059669"
        )
        save_btn.pack(side="right", padx=(5, 0))

        clean_btn = ctk.CTkButton(
            actions_frame,
            text="Auto-Format & Preview",
            command=self.auto_format_timestamps,
            fg_color="#3B82F6",
            hover_color="#2563EB",
        )
        clean_btn.pack(side="right", padx=5)

    def auto_format_timestamps(self):
        """Parse whatever text was pasted and reformat it cleanly into 'HH:MM:SS Title'."""
        content = self.ts_textbox.get("0.0", "end")
        lines = content.splitlines()
        cleaned_lines = []
        for line in lines:
            parsed = TimestampService.parse_line(line)
            if parsed:
                ts, title = parsed
                cleaned_lines.append(f"{ts} {title}")

        if cleaned_lines:
            self.ts_textbox.delete("0.0", "end")
            self.ts_textbox.insert("0.0", "\n".join(cleaned_lines) + "\n")
            self.ts_status_label.configure(
                text=f"Cleaned & formatted {len(cleaned_lines)} segments.",
                text_color="green",
            )
        else:
            self.ts_status_label.configure(
                text="No valid timestamps found to format.", text_color="red"
            )

    def save_timestamps(self):
        content = self.ts_textbox.get("0.0", "end")
        lines = content.splitlines()
        valid_count = sum(1 for line in lines if TimestampService.parse_line(line))

        os.makedirs(os.path.dirname(self.config.urls_file_path), exist_ok=True)
        with open(self.config.timestamps_path, "w", encoding="utf-8") as f:
            f.write(content)

        msg = f"Saved {valid_count} timestamp segments successfully."
        self.ts_status_label.configure(text=msg, text_color="green")
        self.log_message(msg + "\n")

    # ------------------------------------------------------------------ #
    #  History Tab
    # ------------------------------------------------------------------ #

    def setup_history_tab(self):
        self.tab_history.grid_rowconfigure(1, weight=1)
        self.tab_history.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            self.tab_history,
            text="Extracted Video Metadata History:",
            font=("Helvetica", 14, "bold"),
        )
        lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.history_box = ctk.CTkTextbox(self.tab_history, state="disabled")
        self.history_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        refresh_btn = ctk.CTkButton(
            self.tab_history, text="Refresh History", command=self.load_history
        )
        refresh_btn.grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.load_history()

    def load_history(self):
        self.history_box.configure(state="normal")
        self.history_box.delete("0.0", "end")
        if os.path.exists(self.config.metadata_path):
            try:
                with open(self.config.metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history_box.insert("0.0", json.dumps(data, indent=2))
            except Exception as e:
                self.history_box.insert("0.0", f"Error loading metadata: {e}")
        else:
            self.history_box.insert("0.0", "No metadata history found yet.")
        self.history_box.configure(state="disabled")
