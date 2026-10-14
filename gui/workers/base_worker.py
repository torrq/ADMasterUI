"""Base worker thread for executing pipeline subprocesses with live streaming and cancellation."""

import os
from pathlib import Path
import re
import signal
import subprocess
import sys
from typing import List, Optional

from PyQt6.QtCore import QThread, pyqtSignal


class BaseSubprocessWorker(QThread):
    """QThread for executing CLI processes with real-time log parsing and process tree termination."""

    log_line = pyqtSignal(str)
    stage_changed = pyqtSignal(int, str)
    progress_changed = pyqtSignal(int, str)
    process_finished = pyqtSignal(int, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, cmd: List[str], cwd: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.cmd = [str(c) for c in cmd]
        self.cwd = str(cwd) if cwd else None
        self.process: Optional[subprocess.Popen] = None
        self._is_cancelled: bool = False

    def run(self) -> None:
        """Execute process and stream stdout/stderr lines."""
        self._is_cancelled = False
        creationflags = 0
        preexec_fn = None

        if sys.platform == "win32":
            # Create a separate process group on Windows so tree killing works
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            # Create a new session on POSIX
            preexec_fn = os.setsid

        self.log_line.emit(f"[EXEC] {' '.join(self.cmd)}")

        try:
            self.process = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout for chronological logging
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                preexec_fn=preexec_fn,
                bufsize=1,
            )

            # Read lines continuously
            for line in self.process.stdout:
                if self._is_cancelled:
                    break
                self.log_line.emit(line)
                self.parse_progress_line(line)

            self.process.stdout.close()
            return_code = self.process.wait()

            if self._is_cancelled:
                self.process_finished.emit(-1, "[CANCELLED] Operation was cancelled by user.")
            elif return_code == 0:
                self.process_finished.emit(0, "[SUCCESS] Operation completed successfully.")
            else:
                self.process_finished.emit(
                    return_code, f"[FAILED] Process exited with error code {return_code}."
                )

        except Exception as exc:
            self.error_occurred.emit(f"Process execution error: {exc}")
            self.process_finished.emit(-1, f"[ERROR] {exc}")

    def cancel(self) -> None:
        """Cancel and terminate the running subprocess tree."""
        self._is_cancelled = True
        if self.process and self.process.poll() is None:
            self.log_line.emit("[ABORT] Terminating subprocess...")
            try:
                if sys.platform == "win32":
                    # Send CTRL_BREAK_EVENT to process group
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                    self.process.kill()
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception as exc:
                self.log_line.emit(f"[WARNING] Termination error: {exc}")
                try:
                    self.process.kill()
                except Exception:
                    pass

    def parse_progress_line(self, line: str) -> None:
        """Default progress line parser; can be overridden by subclasses."""
        clean = line.strip()

        # Check for stage triggers: [Stage 1/4: Predecoding], [1/3], etc.
        stage_match = re.search(r'\[(?:Stage\s+)?(\d+)/(\d+)[:\s]+([^\]]+)\]', clean, re.IGNORECASE)
        if stage_match:
            curr = int(stage_match.group(1)) - 1
            name = stage_match.group(3).strip()
            self.stage_changed.emit(curr, f"Stage {curr + 1}: {name}")

        # Check for percentage indicators: 45%, [ 45% ], etc.
        pct_match = re.search(r'(\d{1,3})%', clean)
        if pct_match:
            pct = int(pct_match.group(1))
            if 0 <= pct <= 100:
                self.progress_changed.emit(pct, clean)
