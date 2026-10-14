# ADMasterUI -- Cross-Platform Desktop GUI for ADMaster

**ADMasterUI** is a modern, cross-platform desktop application built with **PyQt6** for the **ADMaster** Universal Audio Description & Secondary Audio Sync Toolkit.

It provides a graphical interface for synchronizing Audio Description (AD) tracks, downmixing surround masters (5.1/7.1 to ITU-R BS.775 2.0 Stereo and EBU R128 Night Mode), managing batch queues, orchestrating TV seasons, and tagging Matroska containers.

---

## Key Features

1. **Movie Sync & Fast Preview**:
   * Drag-and-drop inputs for Reference Media and AD Tracks.
   * Auto-discovery mode for movie directories (`source/` and `tosync/`).
   * Stream selection: Interrogates MKV/MP4 files to pick specific surround streams.
   * Warp Engine Selector: High-speed ADSync Viterbi DP (15-30s) or DescribeAlign DTW.
   * 3-Minute Test Preview with synchronized video playback.
   * Fast iteration mode: Uncompressed PCM WAV deliverables (`--wav`) without Night Mode (`--no-night`).

2. **Batch Queue Manager**:
   * Scan queue folders and display items in an interactive table.
   * Real-time progress tracking per item and overall queue.
   * Pause, resume, skip, and scratch-cleanup controls.

3. **TV Season Orchestrator**:
   * Inspect season directories and evaluate alignment strategy per episode (`Direct Mux`, `Frame-Perfect Cut`, `DTW Warp`).
   * Dry-run analysis and batch execution.

4. **Specialized Audio/Video Utilities**:
   * **In-Place MKV Commentary Tagger**: Batch flag commentary audio tracks via `mkvpropedit` in ~10ms.
   * **Commercial Break Cutter**: Detect black frames and silence intervals; slice cleanly without re-encoding.
   * **Surround Master Downmixer**: Batch extract 5.1/7.1 audio into True 2.0 Stereo and Night Mode.
   * **2-Pass Loudness Normalizer**: EBU R128 standalone audio processor.
   * **Gemini Video Chunker**: Slice movies into 1 FPS MP4 chunks with JSON manifests for multimodal AI.

5. **Tool Diagnostics & Configuration**:
   * Visual status validation (`[OK]` / `[MISSING]`) for external tools (`ffmpeg`, `ffprobe`, `mkvmerge`, `mkvpropedit`, `mkvextract`, `adsync`, `describealign`).
   * Thread throttling and loudness target configuration.

---

## Supported Operating Systems

* **Windows**: Windows 10 / 11 (64-bit)
* **Linux**: Ubuntu, Debian, Fedora, Arch, and major distributions (X11 / Wayland)
* **macOS**: macOS 11+ (Intel & Apple Silicon)

---

## Getting Started

### 1. Requirements
* Python 3.9 or newer (tested with Python 3.12).
* Dependencies:
  ```bash
  pip install PyQt6 numpy scipy
  ```
* Media Binaries:
  * `ffmpeg` and `ffprobe` (in system PATH, local `bin/`, or configured in Settings).
  * `MKVToolNix` (`mkvmerge`, `mkvpropedit`, `mkvextract`).

### 2. Launching the Application
```bash
python run_gui.py
```

### 3. Configuration
Copy `config.default.json` to `config.local.json` or `config.json` to customize binary locations, default thread counts, and ADMaster repository paths. Settings can also be adjusted directly inside the application under the **Settings & Diagnostics** tab.

---

## Architecture Overview

```
ADMasterUI/
|-- run_gui.py                   # Root application launcher
|-- config.default.json          # Default configuration template
|-- gui/
|   |-- main.py                  # PyQt6 application entry point
|   |-- theme.py                 # Pure ASCII dark theme stylesheet
|   |-- models/
|   |   +-- config_manager.py    # Reads/writes configuration and validates binaries
|   |   +-- queue_model.py       # Table data model for batch queues
|   |-- workers/
|   |   +-- base_worker.py       # QThread background worker with cancel token
|   |   +-- sync_worker.py       # Worker executing sync pipelines with live log streaming
|   +-- views/
|       |-- main_window.py       # Main window with tab navigation
|       |-- components/          # Reusable widgets (drop zones, status badges, log viewer)
|       +-- tabs/                # Sync, Queue, Season, Utilities, Settings tabs
+-- docs/
    +-- legacy/                  # Legacy ADMaster reference documentation
```

---

## License

Open-source and licensed under the [MIT License](LICENSE).
