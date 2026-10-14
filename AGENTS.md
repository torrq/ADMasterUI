# ADMasterUI -- Agent Guidelines & Architecture Rules

This repository (`ADMasterUI`) contains the cross-platform PyQt6 desktop graphical user interface for the **ADMaster** audio description and secondary audio synchronization toolkit.

---

## 1. Core Relationship with ADMaster

* **ADMaster Core (`../ADMaster`)**: Houses the production Python backend algorithms, mathematical models (100-anchor cross-correlation, ADSync Viterbi lattice DP, DescribeAlign DTW, Multilayer stitcher), and CLI batch scripts.
* **ADMasterUI (`ADMasterUI`)**: The standalone presentation and orchestration layer. It exposes rich graphical controls, batch queue tables, real-time log streaming, progress tracking, and interactive preview workflows.
* **Loose Coupling**: ADMasterUI interacts with ADMaster via robust configuration discovery (`config.json`), resolving local scripts and binary tools dynamically.

---

## 2. Strict Pure ASCII Protocol (No Unicode Characters)

* **All Python scripts, JSON configuration files, markdown documentation, comments, and console print outputs MUST be 100% pure ASCII.**
* Never use Unicode checkmarks (use `[OK]`), Unicode cross marks (use `[X]`), em-dashes (use `--`), en-dashes (use `-`), Unicode bullets (use `*`), Unicode arrows (use `->` or `<-`), curly quotes (use standard `'` or `"`), mathematical symbols (use `+/-`, `*`, `pi`, `^2`), or box-drawing characters.

---

## 3. Documentation Integrity (The "Doc-Sync" Rule)

* Whenever you add, refactor, or adjust GUI components or backend bindings, evaluate whether documentation in `README.md` or `AGENTS.md` is affected.
* If user workflows, CLI flags, configuration parameters, or dependency requirements change, update documentation immediately in the same commit.

---

## 4. PyQt6 Architecture Standards

* **Thread Safety**: Never run heavy audio processing, FFmpeg transcoding, or file system sweeps on the Qt main GUI thread. Always use worker threads (`QThread` or `QThreadPool`) with Qt signals and slots.
* **Process Management**: Wrap external CLI tools with proper subprocessing (`subprocess.Popen` or `QProcess`) supporting graceful termination (`SIGTERM` / `terminate()`) upon user cancellation.
* **Cross-Platform Path Handling**: Use Python's `os.path` or `pathlib.Path` exclusively. Never hardcode Windows backslashes (`\`) or POSIX slashes (`/`).
* **Visual Status Conventions**:
  * Success / Ready: `[OK]` (Green)
  * Active / Running: `[RUNNING]` (Cyan / Blue)
  * Warning / Attention: `[WARNING]` (Yellow)
  * Error / Missing: `[MISSING]` or `[FAILED]` (Red)

---

## 5. Directory Layout

* `gui/`: Main PyQt6 package.
  * `gui/models/`: Configuration management, queue models, audio stream probing.
  * `gui/workers/`: Subprocess streamers, background workers, cancellation tokens.
  * `gui/views/`: QMainWindow, tabs, and reusable components (drop zones, log viewers).
  * `gui/theme.py`: Pure ASCII dark/light theme stylesheets.
* `docs/`: Project documentation and legacy references (`docs/legacy/`).
* `run_gui.py`: Root launch script.
