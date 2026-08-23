"""Helpers for serving a local video through Streamlit's static-file mount.

Streamlit serves everything inside the ``static/`` directory (next to the main
script) at ``/app/static/<name>`` when ``server.enableStaticServing`` is enabled.
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path
from typing import Optional, Union

import streamlit as st

APP_STATIC_DIRNAME = "static"

_EXT_MIME = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}


def static_url(name) -> str:
    """Build the public URL for a file inside the app's ``static/`` directory."""
    return f"/app/static/{Path(name).name}"


def video_data_url(path: Union[str, Path], mime: Optional[str] = None) -> str:
    """Return a ``data:`` URI embedding a local video file as base64.

    Use this to render the background without relying on Streamlit's ``static/``
    serving, which is not reliably available on Streamlit Community Cloud. Works
    on any host (local, Community Cloud, self-hosted).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"video file not found: {path}")
    if mime is None:
        mime = _EXT_MIME.get(path.suffix.lower(), "video/mp4")
    data = path.read_bytes()
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def resolve_video_source(video_source: Union[str, Path]) -> Optional[str]:
    """Turn a user-provided video source into a playable URL.

    * A string that is already a URL (``http(s)://`` or ``/...``) is returned
      unchanged.
    * Anything else (a filename or path) is treated as living in the app's
      ``static/`` dir and returned as ``/app/static/<name>``.

    Returns ``None`` for an empty source.
    """
    if video_source is None:
        return None
    if isinstance(video_source, str):
        s = video_source.strip()
        if not s:
            return None
        if s.startswith(("http://", "https://", "/")):
            return s
        return static_url(s)
    return static_url(Path(video_source).name)


def static_serving_enabled() -> bool:
    """Return whether ``server.enableStaticServing`` is on for the running app."""
    try:
        return bool(st.get_option("server.enableStaticServing"))
    except Exception:  # noqa: BLE001 - option may be unavailable in old versions
        return False


def get_app_static_dir(project_root: Optional[Union[str, Path]] = None) -> Path:
    """Return the ``static/`` directory that Streamlit serves.

    ``project_root`` is the folder that contains the main script (and
    ``.streamlit/config.toml``). When omitted we walk up from the current working
    directory looking for a ``static`` folder or a ``.streamlit`` folder.
    """
    if project_root is not None:
        return (Path(project_root).resolve() / APP_STATIC_DIRNAME)
    # Heuristic fallback: search from cwd upwards for the app static dir.
    for parent in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        candidate = parent / APP_STATIC_DIRNAME
        if candidate.is_dir():
            return candidate
        if (parent / ".streamlit").is_dir():
            return candidate
    return Path.cwd().resolve() / APP_STATIC_DIRNAME


def find_config_toml(project_root: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Locate the project ``.streamlit/config.toml`` (or ``None`` if absent)."""
    if project_root is not None:
        candidate = Path(project_root).resolve() / ".streamlit" / "config.toml"
        return candidate if candidate.exists() else None
    for parent in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        candidate = parent / ".streamlit" / "config.toml"
        if candidate.exists():
            return candidate
    return None


def configure_static_serving(
    enable: bool = True,
    project_root: Optional[Union[str, Path]] = None,
    print_warning: bool = True,
) -> bool:
    """Idempotently set ``server.enableStaticServing`` in the app config.

    Returns ``True`` if the option is enabled afterwards. Existing unrelated
    ``[server]`` settings (e.g. ``runOnSave``) are preserved. A server restart is
    required for the change to take effect.
    """
    config = find_config_toml(project_root)
    if config is None:
        if project_root is None:
            config = Path.cwd() / ".streamlit" / "config.toml"
        else:
            config = Path(project_root).resolve() / ".streamlit" / "config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)

    lines = config.read_text(encoding="utf-8").splitlines() if config.exists() else []
    value = "true" if enable else "false"

    # Minimal, dependency-free TOML edit: ensure the `[server]` section exists and
    # set/update `enableStaticServing` inside it.
    server_header_index = None
    for i, line in enumerate(lines):
        if line.strip() == "[server]":
            server_header_index = i
            break

    if server_header_index is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("[server]")
        server_header_index = len(lines) - 1
        lines.append(f"enableStaticServing = {value}")
        written = True
    else:
        written = False
        for i in range(server_header_index + 1, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("[") and not stripped.startswith("[server]"):
                break  # reached the next TOML section
            if stripped.startswith("enableStaticServing"):
                lines[i] = f"enableStaticServing = {value}"
                written = True
                break
        if not written:
            # insert right after the [server] header
            lines.insert(server_header_index + 1, f"enableStaticServing = {value}")

    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if print_warning and enable and not static_serving_enabled():
        st.warning(
            "video-background: `server.enableStaticServing` was set to true in "
            f"{config}. **Restart the Streamlit server** for it to take effect.",
            icon=":material/restart_alt:",
        )
    return True


def ensure_static(
    video_file: Union[str, Path],
    project_root: Optional[Union[str, Path]] = None,
    *,
    overwrite: bool = False,
) -> str:
    """Copy a video into the app's ``static/`` dir and return its served URL.

    If the file is already inside a ``static/`` directory the copy is skipped.
    Use :func:`configure_static_serving` (or your own config) so Streamlit serves
    the folder, then pass the returned URL to :func:`render_video_background`.
    """
    src = Path(video_file).resolve()
    if not src.exists():
        raise FileNotFoundError(f"video file not found: {src}")

    static_dir = get_app_static_dir(project_root)
    if src.parent.resolve() != static_dir.resolve():
        static_dir.mkdir(parents=True, exist_ok=True)
        dst = static_dir / src.name
        if overwrite or not dst.exists():
            shutil.copy2(src, dst)
    return static_url(src.name)
