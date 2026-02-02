# Video Labeling Tool

A desktop application for efficiently labeling video datasets with Pass/Fail/Uncertain classifications. Built with PyQt6 for video playback and FFmpeg for clip extraction.

## Features

- **Video Playback** - Play, pause, seek, and replay videos with a custom timeline
- **Keyboard-Driven Workflow** - Label videos quickly using keyboard shortcuts
- **Three Label Types**:
  - **Pass (1)** - Video passes validation
  - **Fail (0)** - Video fails; extract a failure clip segment
  - **Uncertain (2)** - Mark for later review
- **Failure Clip Extraction** - Select start/end points to extract the failure segment
- **Slow Motion** - Toggle between 1x, 0.5x, and 0.25x playback speeds
- **Resume Support** - Load an existing CSV to continue where you left off
- **Go Back** - Return to the previous video and re-label it
- **Progress Tracking** - View pass/fail/uncertain counts in real-time

## Requirements

- Python 3.10+
- PyQt6
- FFmpeg (must be in system PATH for clip extraction)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/videocutter.git
   cd videocutter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install FFmpeg:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## Usage

Run the application:
```bash
python main.py
```

### Startup Options

1. **Select Video Directory** - Start a new labeling session
2. **Load Existing CSV** - Resume from a previous session

### Workflow

1. Videos play automatically when loaded
2. Watch the video and decide on a label
3. Press the appropriate key to label and advance:
   - `P` for Pass
   - `F` for Fail (enters segment mode)
   - `U` for Uncertain
4. For failures, select the segment:
   - `S` to set start point
   - `E` to set end point
   - `Enter` to confirm and extract clip
   - `Esc` to cancel

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `P` | Mark as Pass |
| `F` | Mark as Fail (enter segment mode) |
| `U` | Mark as Uncertain |
| `R` | Replay video from start |
| `Space` | Play/Pause |
| `M` | Toggle slow motion (1x -> 0.5x -> 0.25x) |
| `B` | Go back to previous video |

### Segment Mode (after pressing F)

| Key | Action |
|-----|--------|
| `S` | Set segment start |
| `E` | Set segment end |
| `Enter` | Confirm and extract clip |
| `Esc` | Cancel and return to normal mode |
| `Space` | Play/Pause |
| `M` | Toggle slow motion |

## CSV Output Format

The tool outputs a CSV file with the following columns (no header row):

| Column | Description |
|--------|-------------|
| Video Path | Absolute path to the source video |
| Label | `1` = Pass, `0` = Fail, `2` = Uncertain |
| Output Path | Path to extracted failure clip (empty for Pass/Uncertain) |
| Note | Optional note for uncertain videos |

Example:
```csv
C:/Videos/video1.mp4,1,,
C:/Videos/video2.mp4,0,C:/Videos/_failures/video2_fail_5s-12s.mp4,
C:/Videos/video3.mp4,2,,needs review - lighting issue
```

## Project Structure

```
videocutter/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── README.md
└── src/
    ├── __init__.py
    ├── app.py              # Main application window
    ├── video_player.py     # Video player widget
    ├── timeline.py         # Custom timeline/scrubber
    ├── csv_manager.py      # CSV read/write operations
    ├── video_scanner.py    # Directory scanning
    ├── clip_extractor.py   # FFmpeg wrapper
    └── constants.py        # Configuration constants
```

## Supported Video Formats

`.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.webm`, `.flv`, `.m4v`, `.mpeg`, `.mpg`, `.3gp`

## Notes

- Failure clips are saved in a `_failures` subdirectory within the video root directory
- FFmpeg uses stream copy mode for fast, lossless extraction when possible
- The application automatically skips the `_failures` directory when scanning for videos
- Large directories (1000+ files) are supported without UI freezing

## License

MIT License
