"""streamlit_video_background — a reusable fullscreen video background for Streamlit.

Public API
----------
* :func:`render_video_background` — render a fullscreen, blurred, translucent
  video as the page background (theme-aware; supports base64 embedding).
* :func:`build_background_html` — pure HTML builder, handy for testing.
* :func:`compress_video` — FFmpeg helper to prepare a lightweight background file.
* :func:`ensure_static` / :func:`static_url` / :func:`static_serving_enabled` /
  :func:`configure_static_serving` — helpers for Streamlit's ``static/`` serving.
* :func:`video_data_url` — convert a local video into a base64 ``data:`` URI.
"""

from __future__ import annotations

from .background import build_background_html, render_video_background
from .compress import compress_video, probe
from .serving import (
    configure_static_serving,
    ensure_static,
    resolve_video_source,
    static_serving_enabled,
    static_url,
    video_data_url,
)

__version__ = "0.2.0"

__all__ = [
    "build_background_html",
    "compress_video",
    "configure_static_serving",
    "ensure_static",
    "probe",
    "render_video_background",
    "resolve_video_source",
    "static_serving_enabled",
    "static_url",
    "video_data_url",
    "__version__",
]
