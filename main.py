#!/usr/bin/env python3
"""Video Labeling Tool - Entry Point"""

import sys
from PyQt6.QtWidgets import QApplication
from src.app import VideoLabelingApp


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Video Labeling Tool")
    app.setApplicationVersion("1.0.0")

    window = VideoLabelingApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
