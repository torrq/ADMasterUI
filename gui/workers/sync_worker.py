"""Specialized worker for executing sync_ad_track.py with ADMaster stage tracking."""

import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional

from gui.workers.base_worker import BaseSubprocessWorker


class SyncWorker(BaseSubprocessWorker):
    """Worker executing core/sync_ad_track.py with parsed pipeline stages."""

    STAGES = ["Predecode", "Cross-Correlation", "Warping", "Encoding"]

    def __init__(
        self,
        script_path: Path,
        params: Dict,
        python_exe: Optional[str] = None,
        cwd: Optional[Path] = None,
        parent=None,
    ):
        self.script_path = Path(script_path).resolve()
        self.params = params
        self.python_exe = python_exe or sys.executable
        cmd = self._build_command()
        super().__init__(cmd, cwd=cwd, parent=parent)

    def _build_command(self) -> List[str]:
        cmd = [self.python_exe, str(self.script_path)]

        mode = self.params.get("mode", "folder")

        if mode == "folder":
            folder = self.params.get("folder_path", "").strip()
            if folder:
                cmd.append(folder)
        else:
            ref_path = self.params.get("ref_path", "").strip()
            ad_path = self.params.get("ad_path", "").strip()
            if ref_path:
                cmd.extend(["-r", ref_path])
            if ad_path:
                cmd.extend(["-a", ad_path])

        ref_stream = self.params.get("ref_stream", "").strip()
        if ref_stream and ref_stream != "default":
            cmd.extend(["--ref-stream", ref_stream])

        # Warp engine
        warp_engine = self.params.get("warp_engine", "adsync")
        cmd.extend(["--warp-engine", warp_engine])

        if self.params.get("force_dtw"):
            cmd.append("--force-dtw")

        # Speed / PAL options
        if self.params.get("no_pal"):
            cmd.append("--no-pal")
        elif self.params.get("force_pal"):
            cmd.append("--pal")

        if not self.params.get("speed_detect", True):
            cmd.append("--no-speed-detect")

        if not self.params.get("multiband", True):
            cmd.append("--no-multiband")

        # Deliverables
        if self.params.get("convert_main"):
            cmd.append("--convert-main")

        if self.params.get("wav_deliverables"):
            cmd.append("--wav")

        if self.params.get("no_night"):
            cmd.append("--no-night")

        if self.params.get("clean_scratch"):
            cmd.append("--clean-scratch")

        if self.params.get("overwrite"):
            cmd.append("--overwrite")

        # Numeric tunings
        threads = self.params.get("threads")
        if threads:
            cmd.extend(["--threads", str(threads)])

        anchors = self.params.get("anchors")
        if anchors:
            cmd.extend(["--anchors", str(anchors)])

        # Preview mode
        preview_sec = int(self.params.get("preview_sec", 0))
        if preview_sec > 0:
            cmd.extend(["--preview", str(preview_sec)])
            if self.params.get("preview_mux") and self.params.get("ref_path"):
                cmd.extend(["-m", self.params.get("ref_path")])

        return cmd

    def parse_progress_line(self, line: str) -> None:
        clean = line.strip()

        # Catch Stage indicators
        lower = clean.lower()
        if "predecod" in lower or "stage 1" in lower:
            self.stage_changed.emit(0, "Stage 1: Predecoding audio bitstreams...")
        elif "cross-correlation" in lower or "anchor" in lower or "stage 2" in lower:
            self.stage_changed.emit(1, "Stage 2: Multiband acoustic cross-correlation...")
        elif "warp" in lower or "adsync" in lower or "describealign" in lower or "viterbi" in lower:
            self.stage_changed.emit(2, "Stage 3: Non-linear alignment and time warping...")
        elif "encoding" in lower or "downmixing" in lower or "loudnorm" in lower or "rendering" in lower:
            self.stage_changed.emit(3, "Stage 4: Rendering broadcast deliverables...")

        # Percentage parser
        pct_match = re.search(r'(\d{1,3})%', clean)
        if pct_match:
            pct = int(pct_match.group(1))
            if 0 <= pct <= 100:
                self.progress_changed.emit(pct, clean)

        # Catch Final summary lines
        if "offset:" in lower or "confidence:" in lower or "speed ratio:" in lower:
            self.progress_changed.emit(95, clean)
