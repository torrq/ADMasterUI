"""Audio stream probing service using ffprobe."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Optional


@dataclass
class AudioStream:
    """Represents an audio track within a media container."""
    index: int                  # Overall stream index in file (e.g. 1)
    audio_index: int            # Audio-specific index (e.g. 0 for 0:a:0)
    stream_specifier: str       # "0:a:0", "0:a:1"
    codec_name: str             # "truehd", "dts", "ac3", "aac", "flac"
    channels: int               # 2, 6, 8
    channel_layout: str         # "stereo", "5.1(side)", "7.1"
    sample_rate: int            # 48000, 44100
    language: str               # "eng", "und", "spa"
    title: str                  # Track title if present
    is_default: bool            # Default flag

    @property
    def display_label(self) -> str:
        """Formatted display string for dropdown selectors."""
        lang_str = f"[{self.language.upper()}]" if self.language else "[UND]"
        layout_str = self.channel_layout if self.channel_layout else f"{self.channels}ch"
        codec_str = self.codec_name.upper()

        label = f"{self.stream_specifier} | {lang_str} {codec_str} {layout_str} ({self.sample_rate}Hz)"
        if self.title:
            label += f" - {self.title}"
        if self.is_default:
            label += " (Default)"
        return label


class StreamProber:
    """Interrogates container files using FFprobe to discover audio streams."""

    def __init__(self, ffprobe_path: str):
        self.ffprobe_path = ffprobe_path

    def probe_audio_streams(self, file_path: str) -> List[AudioStream]:
        """Probe the specified media file and return list of AudioStream objects."""
        if not file_path or not os.path.isfile(file_path):
            return []

        if not self.ffprobe_path or not os.path.isfile(self.ffprobe_path):
            return []

        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-select_streams", "a",
            file_path
        ]

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            res = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                startupinfo=startupinfo,
                encoding="utf-8",
                errors="replace"
            )

            if res.returncode != 0 or not res.stdout.strip():
                return []

            data = json.loads(res.stdout)
            streams_raw = data.get("streams", [])
            audio_streams: List[AudioStream] = []

            for a_idx, s in enumerate(streams_raw):
                tags = s.get("tags", {})
                disposition = s.get("disposition", {})

                # Normalize tags keys to lowercase
                tags_lower = {k.lower(): str(v) for k, v in tags.items()}

                language = tags_lower.get("language", "und")
                title = tags_lower.get("title", "")
                is_default = bool(disposition.get("default", 0))

                stream_obj = AudioStream(
                    index=int(s.get("index", a_idx)),
                    audio_index=a_idx,
                    stream_specifier=f"0:a:{a_idx}",
                    codec_name=s.get("codec_name", "unknown"),
                    channels=int(s.get("channels", 2)),
                    channel_layout=s.get("channel_layout", ""),
                    sample_rate=int(s.get("sample_rate", 48000)),
                    language=language,
                    title=title,
                    is_default=is_default
                )
                audio_streams.append(stream_obj)

            return audio_streams
        except Exception as exc:
            print(f"[WARNING] Stream probing error on {file_path}: {exc}")
            return []
