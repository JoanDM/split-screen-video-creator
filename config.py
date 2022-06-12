import os
from pathlib import Path

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
TIMER_VIDEO_PATH = BASE_DIR / "resources" / "1min_b&w_timer.mp4"

FFMPEG_PATH = Path("/opt/homebrew/bin/ffmpeg")
FFPROBE_PATH = Path("/opt/homebrew/bin/ffprobe")
DEFAULT_FONT_PATH = Path("/System/Library/Fonts/SFNS.ttf")
