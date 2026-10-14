"""Configuration and binary tool resolution manager for standalone ADMasterUI."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Dict, Optional, Tuple


@dataclass
class BinaryStatus:
    """Represents the resolution and operational status of a dependency binary."""
    key: str
    display_name: str
    path: str
    is_valid: bool
    version_str: str
    status_badge: str  # "[OK]" or "[MISSING]"


def strip_json_comments(text: str) -> str:
    """Strip single-line (//) and multi-line (/* */) comments from JSON text."""
    pattern = r'(//[^\n]*)|(/\*.*?\*/)'
    return re.sub(pattern, '', text, flags=re.DOTALL)


class ConfigManager:
    """Manages application configuration, persistence, and external binary probing."""

    DEFAULT_CONFIG_NAME = "config.default.json"
    CONFIG_NAMES = ["config.local.json", "config.json", "config.default.json"]

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            # Root directory is two levels above gui/models/
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = Path(root_dir).resolve()

        self.core_dir: Path = self.root_dir / "core"
        self.bin_dir: Path = self.root_dir / "bin"
        self.config_path: Path = self._locate_config_file()
        self.data: Dict = self.load_config()

    def _locate_config_file(self) -> Path:
        """Find the highest-priority configuration file present on disk."""
        for name in self.CONFIG_NAMES:
            candidate = self.root_dir / name
            if candidate.is_file():
                return candidate
        return self.root_dir / self.DEFAULT_CONFIG_NAME

    def load_config(self) -> Dict:
        """Load configuration dictionary, falling back to defaults if needed."""
        if not self.config_path.is_file():
            default_path = self.root_dir / self.DEFAULT_CONFIG_NAME
            if default_path.is_file():
                self.config_path = default_path
            else:
                return {}

        try:
            raw_text = self.config_path.read_text(encoding="utf-8")
            clean_text = strip_json_comments(raw_text)
            return json.loads(clean_text)
        except Exception as exc:
            print(f"[WARNING] Failed to parse {self.config_path.name}: {exc}")
            return {}

    def get(self, key: str, default=None):
        """Retrieve a configuration value."""
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value in memory."""
        self.data[key] = value

    def save(self, target_name: str = "config.json") -> Path:
        """Save active configuration to disk."""
        target_path = self.root_dir / target_name
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        self.config_path = target_path
        return target_path

    # =========================================================================
    # Binary & Dependency Discovery
    # =========================================================================

    def resolve_core_engine(self) -> Tuple[Optional[Path], bool]:
        """Verify the internal core engine exists inside ADMasterUI/core/."""
        sync_script = self.core_dir / "sync_ad_track.py"
        if sync_script.is_file():
            return sync_script.resolve(), True
        return None, False

    def resolve_executable(self, key: str, binary_name: str, extra_search_dirs=None) -> Optional[str]:
        """Resolve an executable binary across config, local bin/, and system PATH."""
        configured = self.get(key, "").strip()
        if configured:
            expanded = os.path.expanduser(os.path.expandvars(configured))
            if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
                return str(Path(expanded).resolve())

        search_dirs = []
        if extra_search_dirs:
            search_dirs.extend(extra_search_dirs)

        # Local application bin/ directory
        search_dirs.append(self.bin_dir)

        # Standard OS directories
        if sys.platform == "win32":
            program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
            search_dirs.append(Path(program_files) / "MKVToolNix")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
            search_dirs.append(Path(program_files_x86) / "MKVToolNix")
            exts = [".exe", ".cmd", ".bat", ""]
        else:
            search_dirs.extend([
                Path("/usr/local/bin"),
                Path("/usr/bin"),
                Path("/opt/homebrew/bin"),
                Path("/usr/local/opt/mkvtoolnix/bin"),
            ])
            exts = [""]

        # Check search dirs first
        for sdir in search_dirs:
            if not sdir.is_dir():
                continue
            for ext in exts:
                candidate = sdir / f"{binary_name}{ext}"
                if candidate.is_file():
                    return str(candidate.resolve())

        # Fall back to system PATH
        which_path = shutil.which(binary_name)
        if which_path:
            return str(Path(which_path).resolve())

        return None

    def probe_binary(self, key: str, display_name: str, binary_name: str, version_arg: str = "-version") -> BinaryStatus:
        """Probe an executable binary to determine if it exists and executes cleanly."""
        resolved = self.resolve_executable(key, binary_name)
        if not resolved:
            return BinaryStatus(
                key=key,
                display_name=display_name,
                path="",
                is_valid=False,
                version_str="Not found in PATH or search directories",
                status_badge="[MISSING]"
            )

        try:
            cmd = [resolved, version_arg]
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            proc = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
                encoding="ascii",
                errors="replace"
            )

            output = (proc.stdout or proc.stderr).strip().splitlines()
            first_line = output[0] if output else "Executable responded"

            if len(first_line) > 60:
                first_line = first_line[:57] + "..."

            return BinaryStatus(
                key=key,
                display_name=display_name,
                path=resolved,
                is_valid=True,
                version_str=first_line,
                status_badge="[OK]"
            )
        except Exception as exc:
            return BinaryStatus(
                key=key,
                display_name=display_name,
                path=resolved,
                is_valid=False,
                version_str=f"Execution error: {exc}",
                status_badge="[FAILED]"
            )

    def probe_all_dependencies(self) -> Dict[str, BinaryStatus]:
        """Probe all required internal engines and external binaries."""
        results = {}

        # 1. Internal Standalone Core Engine
        sync_script, sync_ok = self.resolve_core_engine()
        if sync_ok and sync_script:
            results["core_engine"] = BinaryStatus(
                key="core_engine",
                display_name="ADMaster Core Engine",
                path=str(sync_script),
                is_valid=True,
                version_str=f"Found: core/{sync_script.name}",
                status_badge="[OK]"
            )
        else:
            results["core_engine"] = BinaryStatus(
                key="core_engine",
                display_name="ADMaster Core Engine",
                path="",
                is_valid=False,
                version_str="Missing core/sync_ad_track.py",
                status_badge="[MISSING]"
            )

        # 2. FFmpeg & FFprobe
        results["ffmpeg"] = self.probe_binary("ffmpeg_path", "FFmpeg", "ffmpeg", "-version")
        results["ffprobe"] = self.probe_binary("ffprobe_path", "FFprobe", "ffprobe", "-version")

        # 3. MKVToolNix Suite
        results["mkvmerge"] = self.probe_binary("mkvmerge_path", "MKVMerge", "mkvmerge", "--version")
        results["mkvpropedit"] = self.probe_binary("mkvpropedit_path", "MKVPropEdit", "mkvpropedit", "--version")
        results["mkvextract"] = self.probe_binary("mkvextract_path", "MKVExtract", "mkvextract", "--version")

        return results
