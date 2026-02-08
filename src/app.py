"""Main application window for Video Labeling Tool"""

import os
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QFrame, QProgressDialog, QSizePolicy, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent, QFont

from .video_player import VideoPlayer
from .timeline import TimelineWidget
from .csv_manager import CSVManager
from .video_scanner import scan_directory, filter_unlabeled
from .clip_extractor import extract_failure_clip, check_ffmpeg_available


class VideoLabelingApp(QMainWindow):
    """Main application window for video labeling."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Labeling Tool")
        self.setMinimumSize(1000, 700)

        # State
        self._video_queue: List[str] = []
        self._current_index = 0
        self._current_video: Optional[str] = None
        self._root_dir: Optional[str] = None
        self._csv_manager: Optional[CSVManager] = None
        self._segment_mode = False
        self._segment_start: Optional[int] = None
        self._segment_end: Optional[int] = None

        self._setup_ui()
        self._setup_shortcuts()

        # Show startup dialog after window is shown
        QTimer.singleShot(100, self._show_startup_dialog)

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left side: Video player and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # File info label
        self._file_label = QLabel("No video loaded")
        self._file_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: #1a1a1a;
                padding: 8px;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        left_layout.addWidget(self._file_label)

        # Video player
        self._player = VideoPlayer()
        self._player.position_changed.connect(self._on_position_changed)
        self._player.duration_changed.connect(self._on_duration_changed)
        self._player.playback_error.connect(self._on_playback_error)
        left_layout.addWidget(self._player, 1)

        # Timeline
        self._timeline = TimelineWidget()
        self._timeline.seek_requested.connect(self._on_seek_requested)
        self._timeline.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        left_layout.addWidget(self._timeline)

        # Time display
        time_layout = QHBoxLayout()
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        time_layout.addWidget(self._time_label)
        time_layout.addStretch()

        # Segment controls (hidden by default)
        self._segment_frame = QFrame()
        segment_layout = QHBoxLayout(self._segment_frame)
        segment_layout.setContentsMargins(0, 0, 0, 0)
        segment_layout.setSpacing(5)

        self._segment_info = QLabel("Segment: --:-- to --:--")
        self._segment_info.setStyleSheet("color: #ffd93d; font-size: 12px;")
        segment_layout.addWidget(self._segment_info)

        self._set_start_btn = QPushButton("Set Start (S)")
        self._set_start_btn.clicked.connect(self._set_segment_start)
        self._set_start_btn.setStyleSheet(self._get_segment_button_style())
        self._set_start_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        segment_layout.addWidget(self._set_start_btn)

        self._set_end_btn = QPushButton("Set End (E)")
        self._set_end_btn.clicked.connect(self._set_segment_end)
        self._set_end_btn.setStyleSheet(self._get_segment_button_style())
        self._set_end_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        segment_layout.addWidget(self._set_end_btn)

        self._confirm_btn = QPushButton("Confirm (Enter)")
        self._confirm_btn.clicked.connect(self._confirm_segment)
        self._confirm_btn.setStyleSheet(self._get_segment_button_style("#4caf50"))
        self._confirm_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        segment_layout.addWidget(self._confirm_btn)

        self._cancel_btn = QPushButton("Cancel (Esc)")
        self._cancel_btn.clicked.connect(self._cancel_segment)
        self._cancel_btn.setStyleSheet(self._get_segment_button_style("#f44336"))
        self._cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        segment_layout.addWidget(self._cancel_btn)

        self._segment_frame.hide()
        time_layout.addWidget(self._segment_frame)

        left_layout.addLayout(time_layout)

        main_layout.addWidget(left_panel, 1)

        # Right side: Action panel
        right_panel = QFrame()
        right_panel.setFixedWidth(200)
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)

        # Stats
        self._stats_label = QLabel("Videos: 0 / 0")
        self._stats_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        self._stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self._stats_label)

        right_layout.addStretch()

        # Pass button
        self._pass_btn = self._create_action_button(
            "PASS", "#4caf50", "P"
        )
        self._pass_btn.clicked.connect(self._mark_pass)
        right_layout.addWidget(self._pass_btn)

        # Fail button
        self._fail_btn = self._create_action_button(
            "FAIL", "#f44336", "F"
        )
        self._fail_btn.clicked.connect(self._mark_fail)
        right_layout.addWidget(self._fail_btn)

        # Replay button
        self._replay_btn = self._create_action_button(
            "REPLAY", "#2196f3", "R"
        )
        self._replay_btn.clicked.connect(self._replay)
        right_layout.addWidget(self._replay_btn)

        # Uncertain button
        self._uncertain_btn = self._create_action_button(
            "UNCERTAIN", "#ff9800", "U"
        )
        self._uncertain_btn.clicked.connect(self._mark_uncertain)
        right_layout.addWidget(self._uncertain_btn)

        # Play/Pause button
        self._play_pause_btn = self._create_action_button(
            "PLAY/PAUSE", "#9c27b0", "Space"
        )
        self._play_pause_btn.clicked.connect(self._toggle_play_pause)
        right_layout.addWidget(self._play_pause_btn)

        # Slow motion button
        self._slow_btn = self._create_action_button(
            "SLOW MO", "#607d8b", "M"
        )
        self._slow_btn.clicked.connect(self._toggle_slow_motion)
        right_layout.addWidget(self._slow_btn)

        # Previous button
        self._prev_btn = self._create_action_button(
            "PREVIOUS", "#795548", "B"
        )
        self._prev_btn.clicked.connect(self._go_previous)
        right_layout.addWidget(self._prev_btn)

        right_layout.addStretch()

        # Speed indicator
        self._speed_label = QLabel("Speed: 1.0x")
        self._speed_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        self._speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self._speed_label)

        # Mode indicator
        self._mode_label = QLabel("NORMAL MODE")
        self._mode_label.setStyleSheet("""
            color: #4caf50;
            font-size: 11px;
            font-weight: bold;
        """)
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self._mode_label)

        main_layout.addWidget(right_panel)

        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
            }
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
        """)

    def _create_action_button(self, text: str, color: str, shortcut: str) -> QPushButton:
        """Create a styled action button."""
        btn = QPushButton(f"{text}\n({shortcut})")
        btn.setMinimumHeight(70)
        btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """)
        return btn

    def _get_segment_button_style(self, color: str = "#666666") -> str:
        """Get style for segment control buttons."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color)};
            }}
        """

    def _lighten_color(self, hex_color: str) -> str:
        """Lighten a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = int(r * 0.8)
        g = int(g * 0.8)
        b = int(b * 0.8)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        pass  # Handled in keyPressEvent

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key = event.key()

        if self._segment_mode:
            # Segment mode shortcuts
            if key == Qt.Key.Key_S:
                self._set_segment_start()
            elif key == Qt.Key.Key_E:
                self._set_segment_end()
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self._confirm_segment()
            elif key == Qt.Key.Key_Escape:
                self._cancel_segment()
            elif key == Qt.Key.Key_Space:
                self._toggle_play_pause()
            elif key == Qt.Key.Key_M:
                self._toggle_slow_motion()
            elif key == Qt.Key.Key_R:
                self._replay()
        else:
            # Normal mode shortcuts
            if key == Qt.Key.Key_P:
                self._mark_pass()
            elif key == Qt.Key.Key_F:
                self._mark_fail()
            elif key == Qt.Key.Key_U:
                self._mark_uncertain()
            elif key == Qt.Key.Key_R:
                self._replay()
            elif key == Qt.Key.Key_Space:
                self._toggle_play_pause()
            elif key == Qt.Key.Key_M:
                self._toggle_slow_motion()
            elif key == Qt.Key.Key_B:
                self._go_previous()

        super().keyPressEvent(event)

    def _show_startup_dialog(self):
        """Show the startup dialog to select directory or load CSV."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Video Labeling Tool")
        msg.setText("Welcome! How would you like to start?")
        msg.setInformativeText("You can start fresh with a new directory or resume from an existing CSV file.")

        new_btn = msg.addButton("Select Video Directory", QMessageBox.ButtonRole.ActionRole)
        load_btn = msg.addButton("Load Existing CSV", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton(QMessageBox.StandardButton.Cancel)

        msg.exec()

        clicked = msg.clickedButton()
        if clicked == new_btn:
            self._start_new_session()
        elif clicked == load_btn:
            self._load_existing_session()
        else:
            self.close()

    def _start_new_session(self):
        """Start a new labeling session."""
        # Select video directory
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Video Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not dir_path:
            self._show_startup_dialog()
            return

        self._root_dir = dir_path

        # Select CSV save location
        csv_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Labels CSV",
            os.path.join(dir_path, "labels.csv"),
            "CSV Files (*.csv)"
        )

        if not csv_path:
            self._show_startup_dialog()
            return

        self._csv_manager = CSVManager(csv_path)
        self._scan_and_load_videos()

    def _load_existing_session(self):
        """Load an existing labeling session from CSV."""
        csv_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Labels CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not csv_path:
            self._show_startup_dialog()
            return

        self._csv_manager = CSVManager(csv_path)

        # Try to auto-detect video directory from CSV entries
        entries = self._csv_manager.get_all_entries()
        if entries:
            first_video = entries[0][0]
            guessed_dir = os.path.dirname(first_video)

            reply = QMessageBox.question(
                self,
                "Video Directory",
                f"Use detected directory?\n{guessed_dir}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._root_dir = guessed_dir
            else:
                dir_path = QFileDialog.getExistingDirectory(
                    self,
                    "Select Video Directory",
                    "",
                    QFileDialog.Option.ShowDirsOnly
                )
                if dir_path:
                    self._root_dir = dir_path
                else:
                    self._show_startup_dialog()
                    return
        else:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "Select Video Directory",
                "",
                QFileDialog.Option.ShowDirsOnly
            )
            if dir_path:
                self._root_dir = dir_path
            else:
                self._show_startup_dialog()
                return

        self._scan_and_load_videos()

    def _scan_and_load_videos(self):
        """Scan directory and load unlabeled videos."""
        progress = QProgressDialog("Scanning for videos...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Scan directory
        all_videos = scan_directory(self._root_dir)

        # Filter out already labeled videos
        labeled = self._csv_manager.get_labeled_videos()
        self._video_queue = filter_unlabeled(all_videos, labeled)

        progress.close()

        if not self._video_queue:
            if all_videos:
                QMessageBox.information(
                    self,
                    "Complete",
                    f"All {len(all_videos)} videos have been labeled!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Videos",
                    "No video files found in the selected directory."
                )
            self._show_startup_dialog()
            return

        self._current_index = 0
        self._update_stats()
        self._load_current_video()

    def _load_current_video(self):
        """Load the current video from the queue."""
        if self._current_index >= len(self._video_queue):
            QMessageBox.information(
                self,
                "Complete",
                "All videos have been labeled!"
            )
            self._show_startup_dialog()
            return

        self._current_video = self._video_queue[self._current_index]
        self._player.load(self._current_video)
        self._player.set_playback_rate(1.0)  # Reset speed for new video
        self._speed_label.setText("Speed: 1.0x")
        self._player.play()

        # Update file label
        filename = os.path.basename(self._current_video)
        self._file_label.setText(f"{filename}")

        self._update_stats()

    def _update_stats(self):
        """Update the stats display."""
        current = self._current_index + 1
        total = len(self._video_queue)
        stats = self._csv_manager.get_stats() if self._csv_manager else {'passed': 0, 'failed': 0, 'uncertain': 0}

        self._stats_label.setText(
            f"Video {current} / {total}\n"
            f"Pass: {stats['passed']} | Fail: {stats['failed']} | ?: {stats.get('uncertain', 0)}"
        )

    def _on_position_changed(self, position: int):
        """Handle playback position change."""
        self._timeline.set_position(position)
        self._update_time_display(position)

    def _on_duration_changed(self, duration: int):
        """Handle duration change."""
        self._timeline.set_duration(duration)

    def _update_time_display(self, position: int):
        """Update the time display label."""
        duration = self._player.get_duration()

        pos_str = self._format_time(position)
        dur_str = self._format_time(duration)

        self._time_label.setText(f"{pos_str} / {dur_str}")

    def _format_time(self, ms: int) -> str:
        """Format milliseconds as MM:SS."""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _on_seek_requested(self, position: int):
        """Handle seek request from timeline."""
        self._player.seek(position)

    def _on_playback_error(self, error: str):
        """Handle playback error by skipping to next video."""
        QMessageBox.warning(
            self,
            "Playback Error",
            f"Error playing video:\n{error}\n\nSkipping to next video."
        )
        self._next_video()

    def _toggle_play_pause(self):
        """Toggle play/pause."""
        self._player.toggle_play_pause()

    def _replay(self):
        """Replay current video from start."""
        self._player.replay()

    def _toggle_slow_motion(self):
        """Toggle slow motion playback."""
        rate = self._player.toggle_slow_motion()
        self._speed_label.setText(f"Speed: {rate}x")

    def _mark_pass(self):
        """Mark current video as PASS."""
        if self._segment_mode or not self._current_video:
            return

        self._csv_manager.write_pass(self._current_video)
        self._next_video()

    def _mark_uncertain(self):
        """Mark current video as UNCERTAIN with optional note."""
        if self._segment_mode or not self._current_video:
            return

        self._player.pause()

        note, ok = QInputDialog.getText(
            self,
            "Uncertain - Add Note",
            "Enter a note (optional):",
        )

        if ok:  # User clicked OK (note can be empty)
            self._csv_manager.write_uncertain(self._current_video, note)
            self._next_video()
        else:  # User cancelled
            self._player.play()

    def _mark_fail(self):
        """Enter segment mode to mark failure."""
        if self._segment_mode or not self._current_video:
            return

        # Check FFmpeg availability
        if not check_ffmpeg_available():
            QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                "FFmpeg is required to extract failure clips.\n\n"
                "Please install FFmpeg and add it to your system PATH."
            )
            return

        self._enter_segment_mode()

    def _enter_segment_mode(self):
        """Enter segment selection mode."""
        self._segment_mode = True
        self._segment_start = None
        self._segment_end = None

        self._player.pause()
        self._timeline.set_segment_mode(True)
        self._segment_frame.show()

        self._mode_label.setText("SEGMENT MODE")
        self._mode_label.setStyleSheet("color: #ff6b6b; font-size: 11px; font-weight: bold;")

        self._pass_btn.setEnabled(False)
        self._fail_btn.setEnabled(False)
        self._uncertain_btn.setEnabled(False)
        self._prev_btn.setEnabled(False)

        self._update_segment_info()

    def _exit_segment_mode(self):
        """Exit segment selection mode."""
        self._segment_mode = False
        self._segment_start = None
        self._segment_end = None

        self._timeline.set_segment_mode(False)
        self._segment_frame.hide()

        self._mode_label.setText("NORMAL MODE")
        self._mode_label.setStyleSheet("color: #4caf50; font-size: 11px; font-weight: bold;")

        self._pass_btn.setEnabled(True)
        self._fail_btn.setEnabled(True)
        self._uncertain_btn.setEnabled(True)
        self._prev_btn.setEnabled(True)

    def _set_segment_start(self):
        """Set segment start at current position."""
        if not self._segment_mode:
            return

        self._segment_start = self._player.get_position()
        self._timeline.set_segment_start(self._segment_start)
        self._update_segment_info()

    def _set_segment_end(self):
        """Set segment end at current position."""
        if not self._segment_mode:
            return

        self._segment_end = self._player.get_position()
        self._timeline.set_segment_end(self._segment_end)
        self._update_segment_info()

    def _update_segment_info(self):
        """Update segment info display."""
        start_str = self._format_time(self._segment_start) if self._segment_start is not None else "--:--"
        end_str = self._format_time(self._segment_end) if self._segment_end is not None else "--:--"
        self._segment_info.setText(f"Segment: {start_str} to {end_str}")

    def _confirm_segment(self):
        """Confirm segment and extract clip."""
        if not self._segment_mode:
            return

        if self._segment_start is None or self._segment_end is None:
            QMessageBox.warning(
                self,
                "Incomplete Segment",
                "Please set both start and end points."
            )
            return

        # Ensure start < end
        start = min(self._segment_start, self._segment_end)
        end = max(self._segment_start, self._segment_end)

        if end - start < 100:  # Less than 100ms
            QMessageBox.warning(
                self,
                "Segment Too Short",
                "The selected segment is too short."
            )
            return

        # Extract clip
        progress = QProgressDialog("Extracting clip...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        success, message, clip_path = extract_failure_clip(
            self._current_video,
            self._root_dir,
            start,
            end
        )

        progress.close()

        if success and clip_path:
            self._csv_manager.write_fail(self._current_video, clip_path)
            self._exit_segment_mode()
            self._next_video()
        else:
            QMessageBox.critical(
                self,
                "Extraction Failed",
                f"Failed to extract clip:\n{message}"
            )

    def _cancel_segment(self):
        """Cancel segment selection and return to normal mode."""
        self._exit_segment_mode()
        self._player.play()

    def _next_video(self):
        """Load the next video in the queue."""
        self._current_index += 1
        self._load_current_video()

    def _go_previous(self):
        """Go back to the previous video and allow re-labeling."""
        if self._segment_mode:
            return

        if self._current_index <= 0:
            QMessageBox.information(
                self,
                "No Previous Video",
                "You are at the first video."
            )
            return

        # Remove the last entry from CSV (the previous video's label)
        removed = self._csv_manager.remove_last_entry()
        if removed:
            self._current_index -= 1
            self._load_current_video()
        else:
            QMessageBox.warning(
                self,
                "Cannot Go Back",
                "No previous labels to undo."
            )
