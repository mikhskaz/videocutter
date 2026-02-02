"""CSV management for video labels"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class CSVManager:
    """Manages reading and writing video labels to CSV."""

    def __init__(self, csv_path: str):
        """
        Initialize the CSV manager.

        Args:
            csv_path: Path to the CSV file.
        """
        self.csv_path = csv_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create the CSV file if it doesn't exist."""
        path = Path(self.csv_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.touch()

    def get_labeled_videos(self) -> Set[str]:
        """
        Get the set of video paths that have already been labeled.

        Returns:
            Set of absolute paths to labeled videos.
        """
        labeled = set()

        if not os.path.exists(self.csv_path):
            return labeled

        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 1:
                        # Normalize the path for comparison
                        video_path = os.path.normpath(row[0])
                        labeled.add(video_path)
        except Exception:
            pass

        return labeled

    def get_all_entries(self) -> List[Tuple[str, int, Optional[str]]]:
        """
        Read all entries from the CSV.

        Returns:
            List of tuples (video_path, label, output_path).
        """
        entries = []

        if not os.path.exists(self.csv_path):
            return entries

        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 2:
                        video_path = row[0]
                        label = int(row[1])
                        output_path = row[2] if len(row) > 2 and row[2] else None
                        entries.append((video_path, label, output_path))
        except Exception:
            pass

        return entries

    def write_pass(self, video_path: str):
        """
        Write a PASS label for a video.

        Args:
            video_path: Absolute path to the video file.
        """
        self._append_row(video_path, 1, "")

    def write_fail(self, video_path: str, clip_path: str):
        """
        Write a FAIL label for a video with the clip path.

        Args:
            video_path: Absolute path to the source video.
            clip_path: Absolute path to the extracted failure clip.
        """
        self._append_row(video_path, 0, clip_path)

    def write_uncertain(self, video_path: str):
        """
        Write an UNCERTAIN label for a video.

        Args:
            video_path: Absolute path to the video file.
        """
        self._append_row(video_path, 2, "")

    def _append_row(self, video_path: str, label: int, output_path: str):
        """
        Append a row to the CSV file.

        Args:
            video_path: Path to the video file.
            label: 1 for pass, 0 for fail.
            output_path: Path to the failure clip (empty for pass).
        """
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([video_path, label, output_path])

    def remove_last_entry(self) -> Optional[Tuple[str, int, Optional[str]]]:
        """
        Remove the last entry from the CSV file.

        Returns:
            The removed entry (video_path, label, output_path) or None if empty.
        """
        entries = self.get_all_entries()

        if not entries:
            return None

        removed = entries.pop()

        # Rewrite the CSV without the last entry
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for video_path, label, output_path in entries:
                writer.writerow([video_path, label, output_path or ""])

        return removed

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the labeled videos.

        Returns:
            Dictionary with 'total', 'passed', 'failed', and 'uncertain' counts.
        """
        entries = self.get_all_entries()
        passed = sum(1 for _, label, _ in entries if label == 1)
        failed = sum(1 for _, label, _ in entries if label == 0)
        uncertain = sum(1 for _, label, _ in entries if label == 2)

        return {
            'total': len(entries),
            'passed': passed,
            'failed': failed,
            'uncertain': uncertain
        }
