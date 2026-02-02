"""Constants for the Video Labeling Tool"""

from PyQt6.QtCore import Qt

# Supported video file extensions
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.webm',
    '.flv', '.m4v', '.mpeg', '.mpg', '.3gp'
}

# CSV column indices
CSV_VIDEO_PATH = 0
CSV_LABEL = 1
CSV_OUTPUT_PATH = 2

# Label values
LABEL_PASS = 1
LABEL_FAIL = 0

# Keyboard shortcuts
SHORTCUTS = {
    'pass': Qt.Key.Key_P,
    'fail': Qt.Key.Key_F,
    'replay': Qt.Key.Key_R,
    'play_pause': Qt.Key.Key_Space,
    'set_start': Qt.Key.Key_S,
    'set_end': Qt.Key.Key_E,
    'confirm': Qt.Key.Key_Return,
    'cancel': Qt.Key.Key_Escape,
}

# UI Colors
TIMELINE_BG_COLOR = "#2d2d2d"
TIMELINE_PROGRESS_COLOR = "#4a90d9"
TIMELINE_SEGMENT_COLOR = "#ff6b6b"
TIMELINE_MARKER_COLOR = "#ffd93d"

# Failures subdirectory name
FAILURES_DIR = "_failures"
