import sys
import subprocess


class SystemUtils:
    @staticmethod
    def configure_utf8_console():
        """Configure console to use UTF-8 encoding, especially for Windows"""
        if sys.platform == "win32":
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")

    @staticmethod
    def create_windows_startupinfo():
        """Create STARTUPINFO object for Windows to hide console window"""
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return startupinfo
        return None

    @staticmethod
    def run_subprocess(cmd, check=True, show_progress=False):
        """Run a subprocess with appropriate platform-specific settings"""
        print("Running command:", " ".join(cmd))

        try:
            if show_progress:
                # Don't capture output - let it display in console for progress bars
                if sys.platform == "win32":
                    startupinfo = SystemUtils.create_windows_startupinfo()
                    result = subprocess.run(cmd, check=check, startupinfo=startupinfo)
                else:
                    result = subprocess.run(cmd, check=check)
                return result
            else:
                # Capture output (original behavior)
                if sys.platform == "win32":
                    startupinfo = SystemUtils.create_windows_startupinfo()
                    result = subprocess.run(
                        cmd,
                        check=check,
                        startupinfo=startupinfo,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        check=check,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                return result
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            if hasattr(e, "stderr"):
                print(f"stderr: {e.stderr}")
            return None
