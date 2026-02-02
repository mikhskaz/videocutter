"""FFmpeg-based video clip extraction"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple

from .constants import FAILURES_DIR


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in the system PATH."""
    return shutil.which("ffmpeg") is not None


def format_timestamp(milliseconds: int) -> str:
    """
    Convert milliseconds to FFmpeg timestamp format (HH:MM:SS.mmm).

    Args:
        milliseconds: Time in milliseconds.

    Returns:
        Formatted timestamp string.
    """
    total_seconds = milliseconds / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def get_failures_dir(root_video_dir: str) -> Path:
    """
    Get the path to the failures directory.

    Args:
        root_video_dir: The root directory where videos are stored.

    Returns:
        Path to the _failures subdirectory.
    """
    failures_path = Path(root_video_dir) / FAILURES_DIR
    failures_path.mkdir(parents=True, exist_ok=True)
    return failures_path


def generate_clip_filename(
    source_path: str,
    start_ms: int,
    end_ms: int
) -> str:
    """
    Generate a unique filename for the failure clip.

    Args:
        source_path: Path to the source video.
        start_ms: Start time in milliseconds.
        end_ms: End time in milliseconds.

    Returns:
        The filename for the clip (without directory).
    """
    source = Path(source_path)
    name = source.stem
    ext = source.suffix

    # Create a descriptive filename with timestamps
    start_sec = start_ms // 1000
    end_sec = end_ms // 1000

    return f"{name}_fail_{start_sec}s-{end_sec}s{ext}"


def extract_clip(
    source_path: str,
    output_path: str,
    start_ms: int,
    end_ms: int
) -> Tuple[bool, str]:
    """
    Extract a clip from a video using FFmpeg.

    Uses stream copy mode (-c copy) for lossless, fast extraction.

    Args:
        source_path: Path to the source video file.
        output_path: Path where the clip should be saved.
        start_ms: Start time in milliseconds.
        end_ms: End time in milliseconds.

    Returns:
        Tuple of (success: bool, message: str).
    """
    if not check_ffmpeg_available():
        return False, "FFmpeg not found. Please install FFmpeg and add it to your PATH."

    start_time = format_timestamp(start_ms)
    duration_ms = end_ms - start_ms
    duration = format_timestamp(duration_ms)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Build FFmpeg command
    # Using -ss before -i for fast seeking, then -t for duration
    # -c copy for stream copy (no re-encoding)
    # -avoid_negative_ts make_zero to handle timestamp issues
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file if exists
        "-ss", start_time,
        "-i", source_path,
        "-t", duration,
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result.returncode == 0:
            return True, f"Clip saved to: {output_path}"
        else:
            # Try with re-encoding if stream copy fails
            cmd_reencode = [
                "ffmpeg",
                "-y",
                "-ss", start_time,
                "-i", source_path,
                "-t", duration,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                output_path
            ]

            result = subprocess.run(
                cmd_reencode,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes for re-encoding
            )

            if result.returncode == 0:
                return True, f"Clip saved (re-encoded) to: {output_path}"
            else:
                return False, f"FFmpeg error: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "FFmpeg timed out while extracting clip."
    except Exception as e:
        return False, f"Error extracting clip: {str(e)}"


def extract_failure_clip(
    source_path: str,
    root_video_dir: str,
    start_ms: int,
    end_ms: int
) -> Tuple[bool, str, Optional[str]]:
    """
    Extract a failure clip and save it to the _failures directory.

    Args:
        source_path: Path to the source video file.
        root_video_dir: Root directory where videos are stored.
        start_ms: Start time in milliseconds.
        end_ms: End time in milliseconds.

    Returns:
        Tuple of (success: bool, message: str, clip_path: Optional[str]).
    """
    failures_dir = get_failures_dir(root_video_dir)
    clip_filename = generate_clip_filename(source_path, start_ms, end_ms)
    output_path = str(failures_dir / clip_filename)

    # Handle duplicate filenames
    if os.path.exists(output_path):
        base = Path(output_path).stem
        ext = Path(output_path).suffix
        counter = 1
        while os.path.exists(output_path):
            output_path = str(failures_dir / f"{base}_{counter}{ext}")
            counter += 1

    success, message = extract_clip(source_path, output_path, start_ms, end_ms)

    if success:
        return True, message, output_path
    else:
        return False, message, None
