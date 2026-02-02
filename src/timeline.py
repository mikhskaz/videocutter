"""Custom timeline/scrubber widget with segment selection support"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent


class TimelineWidget(QWidget):
    """
    Custom timeline widget for video scrubbing and segment selection.

    Features:
    - Click to seek
    - Visual progress indicator
    - Segment markers for failure clip selection
    """

    # Emitted when user clicks to seek (position in milliseconds)
    seek_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Video state
        self._duration = 0  # Total duration in ms
        self._position = 0  # Current position in ms

        # Segment selection state
        self._segment_mode = False
        self._segment_start = None  # Start time in ms
        self._segment_end = None    # End time in ms

        # Colors
        self._bg_color = QColor("#2d2d2d")
        self._progress_color = QColor("#4a90d9")
        self._segment_color = QColor(255, 107, 107, 100)  # Semi-transparent red
        self._marker_color = QColor("#ffd93d")
        self._border_color = QColor("#555555")

    def set_duration(self, duration_ms: int):
        """Set the total duration of the video."""
        self._duration = max(0, duration_ms)
        self.update()

    def set_position(self, position_ms: int):
        """Set the current playback position."""
        self._position = max(0, min(position_ms, self._duration))
        self.update()

    def set_segment_mode(self, enabled: bool):
        """Enable or disable segment selection mode."""
        self._segment_mode = enabled
        if not enabled:
            self._segment_start = None
            self._segment_end = None
        self.update()

    def set_segment_start(self, time_ms: int):
        """Set the segment start time."""
        self._segment_start = time_ms
        self.update()

    def set_segment_end(self, time_ms: int):
        """Set the segment end time."""
        self._segment_end = time_ms
        self.update()

    def get_segment(self):
        """Get the current segment (start, end) in milliseconds."""
        return self._segment_start, self._segment_end

    def clear_segment(self):
        """Clear the segment markers."""
        self._segment_start = None
        self._segment_end = None
        self.update()

    def _ms_to_x(self, ms: int) -> int:
        """Convert milliseconds to x coordinate."""
        if self._duration <= 0:
            return 0
        return int((ms / self._duration) * self.width())

    def _x_to_ms(self, x: int) -> int:
        """Convert x coordinate to milliseconds."""
        if self.width() <= 0:
            return 0
        return int((x / self.width()) * self._duration)

    def paintEvent(self, event):
        """Draw the timeline."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw background
        painter.fillRect(0, 0, width, height, self._bg_color)

        # Draw segment highlight (if in segment mode and segment is defined)
        if self._segment_mode and self._segment_start is not None:
            start_x = self._ms_to_x(self._segment_start)
            end_x = self._ms_to_x(self._segment_end) if self._segment_end else self._ms_to_x(self._position)

            if end_x < start_x:
                start_x, end_x = end_x, start_x

            segment_rect = QRect(start_x, 0, end_x - start_x, height)
            painter.fillRect(segment_rect, self._segment_color)

        # Draw progress bar
        if self._duration > 0:
            progress_width = self._ms_to_x(self._position)
            progress_rect = QRect(0, height - 6, progress_width, 6)
            painter.fillRect(progress_rect, self._progress_color)

        # Draw segment markers
        if self._segment_mode:
            marker_pen = QPen(self._marker_color, 2)
            painter.setPen(marker_pen)

            # Start marker
            if self._segment_start is not None:
                start_x = self._ms_to_x(self._segment_start)
                painter.drawLine(start_x, 0, start_x, height)
                # Draw "S" label
                painter.drawText(start_x + 3, 12, "S")

            # End marker
            if self._segment_end is not None:
                end_x = self._ms_to_x(self._segment_end)
                painter.drawLine(end_x, 0, end_x, height)
                # Draw "E" label
                painter.drawText(end_x + 3, 12, "E")

        # Draw border
        border_pen = QPen(self._border_color, 1)
        painter.setPen(border_pen)
        painter.drawRect(0, 0, width - 1, height - 1)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click for seeking."""
        if event.button() == Qt.MouseButton.LeftButton and self._duration > 0:
            click_ms = self._x_to_ms(int(event.position().x()))
            self.seek_requested.emit(click_ms)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse drag for seeking."""
        if event.buttons() & Qt.MouseButton.LeftButton and self._duration > 0:
            click_ms = self._x_to_ms(int(event.position().x()))
            click_ms = max(0, min(click_ms, self._duration))
            self.seek_requested.emit(click_ms)
