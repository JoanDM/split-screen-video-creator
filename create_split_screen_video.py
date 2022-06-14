import argparse
from pathlib import Path
import subprocess
from config import (
    FFPROBE_PATH,
    FFMPEG_PATH,
    DEFAULT_FONT_PATH,
    TIMER_VIDEO_PATH,
)
from models.constants import (
    DEFAULT_SUBTITLE_HEIGHT_PERCENTAGE,
    PADDING_WIDTH_IN_PIXELS,
    VIDEO_EXTENSIONS,
)
from PIL import ImageFont
import webbrowser


def create_split_screen_video(
    dir_with_videos: Path,
    target_dir=None,
    insert_subtitles=True,
    slow_mo_factor=None,
    last_frame_freeze_duration=2,
    insert_timers=False,
    remove_audio=True,
) -> Path:
    """Create a split screen video composition by stitching the videos in a directory side by side.
    To do so, the script will construct and execute the FFMPEG command line program
    :param dir_with_videos: Directory containing videos to stitch together, sorted by name from left to right
    :param target_dir: Target directory to store video composition
    :param insert_subtitles: Insert a subtitle below every video (text maps to video file names)
    :param slow_mo_factor: Factor for video slow-down
    :param last_frame_freeze_duration: How long should the last composition's frame stay frozen
    :param insert_timers: Insert a timer at the top-left side of every video
    :param remove_audio: Remove audio from final composition
    """
    if not target_dir:
        target_dir = dir_with_videos.parents[0] / f"{dir_with_videos.stem}_split_screen"
    tmp_dir = target_dir / "tmp_input_stripped_exif"

    target_dir.mkdir(exist_ok=True)
    tmp_dir.mkdir(exist_ok=True)

    paths_to_videos = []
    comp_duration = 0
    vid_duration_list = []
    ffmpeg_input_videos = ""
    # Rotation metadata can cause trouble - this will strip metadata from input videos
    for raw_vid in sorted(
        filter(lambda path: path.suffix in VIDEO_EXTENSIONS, dir_with_videos.glob("*"))
    ):
        vid = tmp_dir / raw_vid.name
        if not vid.exists():
            subprocess.check_output(
                [f"{FFMPEG_PATH}  -i '{raw_vid}' '{vid}'"], shell=True
            )
        paths_to_videos.append(vid)

        # Construct FFMPEG command for input videos
        ffmpeg_input_videos += f"-i '{vid}' "

        # Collect the video length to properly trim and cut composition
        vid_duration = float(
            subprocess.check_output(
                [
                    f"{FFPROBE_PATH} -v error -select_streams v:0 -show_entries stream=duration -of default=nw=1:nk=1"
                    f" '{vid}'"
                ],
                shell=True,
            )
        )

        vid_duration_list.append(vid_duration)
        comp_duration = (
            max(comp_duration, vid_duration)
            + last_frame_freeze_duration / slow_mo_factor
        )

    # Final composition height is based on first video size
    final_video_h = int(
        subprocess.check_output(
            [
                f"{FFPROBE_PATH} -v error -show_entries stream=height -select_streams v:0 -of default=nw=1:nk=1"
                f" '{paths_to_videos[0]}'"
            ],
            shell=True,
        )
    )
    # The following actions are done by constructing FFMPEG complex filters
    ffmpeg_complex_filter = ""

    video_widths = []
    # Video scaling
    for i in range(len(paths_to_videos)):
        # All videos must be scaled to match first input video height
        ffmpeg_complex_filter += f"[{i}:v]scale=-1:{final_video_h}[v{i}];"
        input_video_w = int(
            subprocess.check_output(
                [
                    f"{FFPROBE_PATH} -v error -show_entries stream=width -select_streams v:0 -of default=nw=1:nk=1"
                    f" '{paths_to_videos[i]}'"
                ],
                shell=True,
            )
        )
        input_video_h = int(
            subprocess.check_output(
                [
                    f"{FFPROBE_PATH} -v error -show_entries stream=height -select_streams v:0 -of default=nw=1:nk=1"
                    f" '{paths_to_videos[i]}'"
                ],
                shell=True,
            )
        )
        video_widths.append(input_video_w / input_video_h * final_video_h)

        if insert_timers:
            # Scale and set durations for timers
            timer_height = int(final_video_h * DEFAULT_SUBTITLE_HEIGHT_PERCENTAGE)
            ffmpeg_input_videos += f" -i '{TIMER_VIDEO_PATH}'"
            ffmpeg_complex_filter += (
                f"[{len(paths_to_videos) + i}:v]scale=-1:{timer_height}[timer{i}];"
                f"[timer{i}]trim=duration={vid_duration_list[i]}[timer{i}];"
            )

    # Construct the horizontal video stack layout with padding inbetween videos
    padding_width = PADDING_WIDTH_IN_PIXELS
    ffmpeg_stack_filter = ""
    for i in range(len(paths_to_videos) - 1):
        ffmpeg_complex_filter += f"color=black:{padding_width}x{final_video_h}:d={comp_duration}[blackpad{i}];"
        ffmpeg_stack_filter += f"[v{i}][blackpad{i}]"

    ffmpeg_stack_filter += (
        f"[v{len(paths_to_videos) - 1}]hstack=inputs={len(paths_to_videos) * 2 - 1}"
    )
    ffmpeg_complex_filter += ffmpeg_stack_filter

    # Insert a black banner at the bottom of the composition and insert video subtitles
    # to identify every single input video
    if insert_subtitles:
        text_box_opacity = 1.0
        ffmpeg_complex_filter += (
            f"[composition];[composition]drawbox=x=0:y=ih-h:w=iw:h=ih*{DEFAULT_SUBTITLE_HEIGHT_PERCENTAGE}"
            f":color=black@{text_box_opacity}:t=fill"
        )
        normalized_font_size = 1000

        ref_font_size = 100
        # Find best-fitting font size
        for i, vid_path in enumerate(paths_to_videos):
            # If input video had to be rescaled, find resulting w after scaling
            subtitle_text = vid_path.stem.replace(" ", "\ ")
            font = ImageFont.truetype(str(DEFAULT_FONT_PATH), ref_font_size)
            ref_w, ref_h = font.getsize(subtitle_text)
            limit_text_width = video_widths[i]
            limit_text_height = DEFAULT_SUBTITLE_HEIGHT_PERCENTAGE * final_video_h
            fitting_font_size = int(
                min(
                    ref_font_size * (limit_text_width / ref_w),
                    ref_font_size * (limit_text_height / ref_h),
                )
            )

            normalized_font_size = min(normalized_font_size, fitting_font_size)

        # Insert subtitle
        subtitle_x_position = 0
        for i, vid_path in enumerate(paths_to_videos):
            subtitle_x_position += video_widths[i] / 2
            subtitle_text = vid_path.stem.replace(" ", "\ ")
            ffmpeg_complex_filter += (
                f",drawtext=fontfile={DEFAULT_FONT_PATH}:text='{subtitle_text}':"
                f"fontcolor=white:fontsize={normalized_font_size}:x={subtitle_x_position}"
                f"-text_w/2:y=h-text_h-10"
            )
            subtitle_x_position += video_widths[i] / 2 + padding_width

    if insert_timers:
        video_width_tracker = 0
        ffmpeg_complex_filter += f"[composition]"
        for i in range(len(paths_to_videos) - 1):
            ffmpeg_complex_filter += f";[composition][timer{i}]overlay={video_width_tracker}:{0}[composition]"
            video_width_tracker += video_widths[i] + padding_width
        ffmpeg_complex_filter += f";[composition][timer{len(paths_to_videos)}]overlay={video_width_tracker}:{0}"

    # Slow down the final composition by x factor
    ffmpeg_complex_filter += (
        f"[composition];[composition]setpts={float(slow_mo_factor)}*PTS"
    )
    audio_option = "-an"
    if not remove_audio:
        if slow_mo_factor <= 2:
            ffmpeg_complex_filter += f";amix=inputs={len(paths_to_videos)},atempo={float(1 / slow_mo_factor)}"
            audio_option = "-ac 2"
        else:
            print(
                "\033[91m{}\033[00m".format(
                    "Warning, audio will be removed since it's not possible to preserve with slow down factors >2"
                )
            )
    target_file_path = target_dir / f"{dir_with_videos.stem}_split_screen.mp4"
    # -ac 2 to downmix audio to stereo
    subprocess.check_output(
        [
            f"{FFMPEG_PATH} {ffmpeg_input_videos} -filter_complex '{ffmpeg_complex_filter}' {audio_option} -vsync 0"
            f" '{target_file_path}'"
        ],
        shell=True,
    )

    return target_file_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a split screen video composition by stitching videos in a directory"
    )
    parser.add_argument(
        "-dir", type=Path, required=True, help="Directory containing videos"
    )
    parser.add_argument(
        "-out",
        type=Path,
        required=False,
        default=None,
        help="Output directory to store video composition. Defaults to same folder containing input video",
    )
    parser.add_argument(
        "-nosubs",
        required=False,
        action="store_false",
        help="Flag to deactivate default video subtitle insertion",
    )

    parser.add_argument(
        "-smf",
        help="Slow-motion factor. E.g. x2 will slowdown frame rate by two. N.B. Audio cannot be preserved if smf>2",
        default=1,
        type=int,
    )
    parser.add_argument(
        "-fd",
        help="Last frame freezing duration in seconds",
        default=2,
        type=int,
    )
    parser.add_argument("-timers", help="insert timers", action="store_true")
    parser.add_argument(
        "-noaudio", help="remove audio from final composition", action="store_true"
    )

    args = parser.parse_args()

    video_composition_path = create_split_screen_video(
        args.dir, args.out, args.nosubs, args.smf, args.fd, args.timers, args.noaudio
    )

    print(
        ("\033[92m{}\033[00m".format(f"Composition saved at {video_composition_path}"))
    )
    new = 2  # open in a new tab, if possible
    webbrowser.open(f"file://{video_composition_path}", new=new)
