"""Video file scanner for recursive directory traversal"""

import os
from pathlib import Path
from typing import List, Set, Callable, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from .constants import VIDEO_EXTENSIONS


def is_video_file(path: Path) -> bool:
    """Check if a file has a video extension."""
    return path.suffix.lower() in VIDEO_EXTENSIONS


def scan_directory(root_path: str) -> List[str]:
    """
    Recursively scan a directory for video files.

    Args:
        root_path: The root directory to scan.

    Returns:
        A sorted list of absolute paths to video files.
    """
    video_files = []
    root = Path(root_path)

    if not root.exists() or not root.is_dir():
        return video_files

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip _failures directory
        if "_failures" in dirnames:
            dirnames.remove("_failures")

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if is_video_file(file_path):
                video_files.append(str(file_path.resolve()))

    return sorted(video_files)


def filter_unlabeled(
    all_videos: List[str],
    labeled_videos: Set[str]
) -> List[str]:
    """
    Filter out videos that have already been labeled.

    Args:
        all_videos: List of all video paths found.
        labeled_videos: Set of video paths that are already labeled.

    Returns:
        List of video paths that haven't been labeled yet.
    """
    return [v for v in all_videos if v not in labeled_videos]


class VideoScannerThread(QThread):
    """Background thread for scanning directories without freezing UI."""

    progress = pyqtSignal(int, int)  # current, total (estimated)
    finished_scanning = pyqtSignal(list)  # list of video paths
    error = pyqtSignal(str)

    def __init__(self, root_path: str, parent=None):
        super().__init__(parent)
        self.root_path = root_path

    def run(self):
        try:
            videos = scan_directory(self.root_path)
            self.finished_scanning.emit(videos)
        except Exception as e:
            self.error.emit(str(e))
