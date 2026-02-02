"""Video player component using Qt Multimedia"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VideoPlayer(QWidget):
    """
    Video player widget with playback controls.

    Signals:
        position_changed: Emitted when playback position changes (ms)
        duration_changed: Emitted when video duration is known (ms)
        playback_error: Emitted when a playback error occurs
        video_ended: Emitted when video playback ends
    """

    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    playback_error = pyqtSignal(str)
    video_ended = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._playback_rate = 1.0
        self._setup_ui()
        self._setup_player()

    def _setup_ui(self):
        """Set up the video display UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Video widget
        self._video_widget = QVideoWidget()
        self._video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._video_widget)

        # Error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                background-color: #2d2d2d;
                padding: 20px;
                font-size: 14px;
            }
        """)
        self._error_label.hide()
        layout.addWidget(self._error_label)

    def _setup_player(self):
        """Set up the media player."""
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()

        self._player.setVideoOutput(self._video_widget)
        self._player.setAudioOutput(self._audio_output)

        # Connect signals
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.errorOccurred.connect(self._on_error)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

        # Set default volume
        self._audio_output.setVolume(0.7)

    def _on_position_changed(self, position: int):
        """Handle position change."""
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration: int):
        """Handle duration change."""
        self.duration_changed.emit(duration)

    def _on_error(self, error):
        """Handle playback error."""
        error_msg = self._player.errorString()
        self._show_error(f"Playback error: {error_msg}")
        self.playback_error.emit(error_msg)

    def _on_media_status_changed(self, status):
        """Handle media status changes."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.video_ended.emit()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._show_error("Invalid or corrupt video file")
            self.playback_error.emit("Invalid media")

    def _show_error(self, message: str):
        """Display an error message."""
        self._video_widget.hide()
        self._error_label.setText(message)
        self._error_label.show()

    def _hide_error(self):
        """Hide the error message."""
        self._error_label.hide()
        self._video_widget.show()

    def load(self, file_path: str):
        """
        Load a video file.

        Args:
            file_path: Absolute path to the video file.
        """
        self._hide_error()
        url = QUrl.fromLocalFile(file_path)
        self._player.setSource(url)

    def play(self):
        """Start or resume playback."""
        self._player.play()

    def pause(self):
        """Pause playback."""
        self._player.pause()

    def toggle_play_pause(self):
        """Toggle between play and pause."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def stop(self):
        """Stop playback."""
        self._player.stop()

    def seek(self, position_ms: int):
        """
        Seek to a specific position.

        Args:
            position_ms: Position in milliseconds.
        """
        self._player.setPosition(position_ms)

    def replay(self):
        """Restart playback from the beginning."""
        self._player.setPosition(0)
        self.play()

    def get_position(self) -> int:
        """Get current position in milliseconds."""
        return self._player.position()

    def get_duration(self) -> int:
        """Get total duration in milliseconds."""
        return self._player.duration()

    def set_volume(self, volume: float):
        """
        Set playback volume.

        Args:
            volume: Volume level (0.0 to 1.0).
        """
        self._audio_output.setVolume(max(0.0, min(1.0, volume)))

    def set_playback_rate(self, rate: float):
        """
        Set playback speed.

        Args:
            rate: Playback rate (e.g., 0.5 for half speed, 1.0 for normal).
        """
        self._playback_rate = rate
        self._player.setPlaybackRate(rate)

    def get_playback_rate(self) -> float:
        """Get current playback rate."""
        return self._playback_rate

    def toggle_slow_motion(self) -> float:
        """
        Toggle between normal speed and slow motion.

        Returns:
            The new playback rate.
        """
        if self._playback_rate == 1.0:
            self.set_playback_rate(0.5)
        elif self._playback_rate == 0.5:
            self.set_playback_rate(0.25)
        else:
            self.set_playback_rate(1.0)
        return self._playback_rate
