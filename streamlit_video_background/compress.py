"""FFmpeg helpers to prepare a lightweight background video.

Backgrounds don't need full resolution or high bitrate. :func:`compress_video`
downscales and re-encodes a video so it streams quickly, and can optionally bake
a blur into the file itself (useful if you prefer the blur in the video over CSS).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Union


def ffmpeg_bin() -> str:
    """Return the path of ``ffmpeg`` (raises if it is not installed)."""
    found = shutil.which("ffmpeg")
    if not found:
        raise RuntimeError(
            "ffmpeg was not found on PATH. Install it (e.g. `choco install ffmpeg` "
            "on Windows, `brew install ffmpeg` on macOS, `apt install ffmpeg` on "
            "Debian/Ubuntu) or pass the `ffmpeg=` argument."
        )
    return found


def probe(path: Union[str, Path]) -> dict:
    """Return a dict with stream/format metadata (dimensions, bitrate, etc.)."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe was not found on PATH.")
    cmd = [
        ffprobe,
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(Path(path).resolve()),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def compress_video(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    *,
    scale: Optional[int] = 1280,
    crf: int = 27,
    preset: str = "slow",
    fps: Optional[int] = None,
    blur: Optional[float] = None,
    keep_audio: bool = False,
    overwrite: bool = True,
    ffmpeg: Optional[str] = None,
) -> Path:
    """Compress a video for use as a background and return the output path.

    Parameters
    ----------
    input_path:
        Source video file.
    output_path:
        Destination. Defaults to ``<input>_720p<ext>`` next to the input.
    scale:
        Downscale the longer axis to this width (e.g. ``1280``), preserving aspect
        ratio. ``None`` keeps the original size.
    crf:
        H.264 quality/compression trade-off (``0`` = lossless, ``~23`` = good,
        ``~27-30`` = very small). Higher is smaller but grainier — fine for a
        blurred background.
    preset:
        x264 speed preset (``slower`` compresses best, ``veryfast`` encodes fast).
    fps:
        Optionally re-encode at a fixed frame rate.
    blur:
        If set, bake a box blur of this pixel radius into the file. When used you
        should set the CSS ``blur="0px"`` in :func:`render_video_background` to
        avoid double-blurring.
    keep_audio:
        By default audio is dropped (a background needs none).
    overwrite:
        Overwrite ``output_path`` if it already exists.
    ffmpeg:
        Path to the ``ffmpeg`` binary (defaults to one found on PATH).
    """
    src = Path(input_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"input video not found: {src}")

    if output_path is None:
        suffix = src.suffix or ".mp4"
        output_path = src.with_name(f"{src.stem}_720p{suffix}")
    dst = Path(output_path)
    if dst.exists() and not overwrite:
        return dst

    filters: list[str] = []
    if scale:
        filters.append(f"scale={scale}:-2")
    if fps:
        filters.append(f"fps={int(fps)}")
    if blur:
        # Cheap box blur; radius in pixels. 8 gives a soft background.
        filters.append(
            f"boxblur=luma_radius={float(blur)}:chroma_radius={float(blur)}"
        )

    cmd = [
        ffmpeg or ffmpeg_bin(),
        "-y",
        "-i", str(src),
    ]
    if filters:
        cmd += ["-vf", ",".join(filters)]
    cmd += [
        "-c:v", "libx264",
        "-crf", str(int(crf)),
        "-preset", str(preset),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]
    if not keep_audio:
        cmd += ["-an"]
    cmd += [str(dst)]

    subprocess.run(cmd, check=True)
    return dst
