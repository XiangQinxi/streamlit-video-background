"""Core background rendering for :mod:`streamlit_video_background`.

This module exposes:

* :func:`build_background_html` — a pure function that returns the HTML/CSS/JS
  string for a fullscreen video background (no ``streamlit`` calls, easy to test).
* :func:`render_video_background` — the ``st``-aware entry point that resolves a
  video source, picks the theme backdrop color and injects the background via
  ``st.html(..., unsafe_allow_javascript=True)``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import streamlit as st

from .serving import resolve_video_source

DEFAULT_BACKDROP_LIGHT = "#FFFFFF"
DEFAULT_BACKDROP_DARK = "#0E0E0E"


def _theme_backdrop(backdrop_light: str, backdrop_dark: str) -> str:
    """Return the backdrop color for the *current* Streamlit theme.

    ``st.context.theme.type`` reflects the theme at the last script run. Because
    Streamlit does **not** rerun the script when the user switches theme in the
    settings menu, this value is only an initial hint; the injected JS syncs the
    backdrop to the *actual live* theme on every switch (see the JS below).
    """
    try:
        if st.context.theme.type == "dark":
            return backdrop_dark
    except Exception:  # noqa: BLE001 - never crash on theme introspection
        pass
    return backdrop_light


def build_background_html(
    video_url: str,
    *,
    blur: str = "8px",
    opacity: float = 0.5,
    backdrop: str = "#FFFFFF",
    autoplay: bool = True,
    loop: bool = True,
    muted: bool = True,
    playsinline: bool = True,
    object_fit: str = "cover",
    element_id: str = "fl-video-bg",
    backdrop_id: str = "fl-bg-backdrop",
) -> str:
    """Build the HTML/CSS/JS used to render a fullscreen video background.

    Must be injected with ``unsafe_allow_javascript=True`` for the theme-sync
    script to run. This function never touches ``streamlit`` so it can be tested
    in isolation.
    """
    play_attrs = " ".join(
        attr
        for attr, on in (
            ("autoplay", autoplay),
            ("loop", loop),
            ("muted", muted),
            ("playsinline", playsinline),
        )
        if on
    )

    initial = backdrop
    video_tag = (
        f'<div id="{element_id}" style="position:fixed; inset:0; z-index:-1; '
        'overflow:hidden; pointer-events:none;">'
        f'<div id="{backdrop_id}" style="position:absolute; inset:0; '
        f'background-color:{initial};"></div>'
        f'<video {play_attrs} '
        'style="position:absolute; inset:0; width:100%; height:100%; '
        f'object-fit:{object_fit}; filter:blur({blur}); opacity:{opacity};" '
        f'src="{video_url}"></video>'
        "</div>"
    )

    style = """
    <style>
    /* Make the main content area transparent so the video behind it shows.
       Kept out of the transparent list: the top header/nav and the sidebar, so
       they retain their own theme background and stay readable on mobile where
       the top nav becomes a sidebar drawer. */
    .stApp,
    [data-testid="stMain"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"] {
        background-color: transparent !important;
    }
    </style>
    """

    # Streamlit switches the theme client-side without rerunning the script, so
    # st.context.theme.type can be stale. Instead, watch the live theme: read the
    # header's real background (with .stApp's color-scheme as a fallback) and keep
    # the backdrop in sync. This is what makes Light<->Dark switching work.
    js = (
        "<script>\n"
        "(function () {\n"
        f"  var bd = document.getElementById('{backdrop_id}');\n"
        "  if (!bd) return;\n"
        "  function sync() {\n"
        "    if (!document.body.contains(bd)) return;\n"
        "    var bg = null;\n"
        "    var header = document.querySelector('[data-testid=\"stHeader\"]');\n"
        "    if (header) {\n"
        "      var c = getComputedStyle(header).backgroundColor;\n"
        "      if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') bg = c;\n"
        "    }\n"
        "    if (!bg) {\n"
        "      var app = document.querySelector('.stApp');\n"
        "      var cs = app ? getComputedStyle(app).colorScheme : '';\n"
        f"      bg = (cs === 'dark') ? '{DEFAULT_BACKDROP_DARK}' : '{DEFAULT_BACKDROP_LIGHT}';\n"
        "    }\n"
        "    if (bg && bd.style.backgroundColor !== bg) bd.style.backgroundColor = bg;\n"
        "  }\n"
        "  sync();\n"
        "  [document.querySelector('[data-testid=\"stHeader\"]'),"
        " document.querySelector('.stApp')].forEach(function (el) {\n"
        "    if (el) new MutationObserver(sync).observe(el, { attributes: true,"
        " attributeFilter: ['style', 'class'] });\n"
        "  });\n"
        "  new MutationObserver(sync).observe(document.head, { childList: true,"
        " subtree: true });\n"
        "})();\n"
        "</script>"
    )

    return video_tag + style + js


def render_video_background(
    video_source: Union[str, Path],
    *,
    blur: str = "8px",
    opacity: float = 0.5,
    backdrop_light: str = DEFAULT_BACKDROP_LIGHT,
    backdrop_dark: str = DEFAULT_BACKDROP_DARK,
    autoplay: bool = True,
    loop: bool = True,
    muted: bool = True,
    playsinline: bool = True,
    object_fit: str = "cover",
    element_id: str = "fl-video-bg",
    backdrop_id: str = "fl-bg-backdrop",
) -> None:
    """Render a fullscreen video background into the current Streamlit page.

    Parameters
    ----------
    video_source:
        The video to play. Either a URL (``https://...``, ``/app/static/x.mp4``)
        or a local path. For a local path the file is expected to live in the
        app's ``static/`` directory (served at ``/app/static/<name>``) — see
        :func:`streamlit_video_background.serving.ensure_static` and make sure
        ``server.enableStaticServing = true`` in ``.streamlit/config.toml``.
    blur:
        CSS blur applied to the video, e.g. ``"8px"`` (or ``"0px"`` to disable).
    opacity:
        Video opacity in ``[0, 1]`` (the translucent effect).
    backdrop_light / backdrop_dark:
        Background color that shows through the translucent video for the light
        and dark themes. The injected JS keeps this in sync on theme switches.
    autoplay / loop / muted / playsinline:
        Native ``<video>`` attributes.
    object_fit:
        CSS ``object-fit`` for the video (``"cover"`` fills the viewport).
    """
    url = resolve_video_source(video_source)
    if url is None:
        st.warning(
            "video-background: could not resolve a playable source for "
            f"{video_source!r}. Put the file in the app's `static/` directory and "
            "enable `server.enableStaticServing` in `.streamlit/config.toml`.",
            icon=":material/note:",
        )
        return

    backdrop = _theme_backdrop(backdrop_light, backdrop_dark)
    html = build_background_html(
        url,
        blur=blur,
        opacity=opacity,
        backdrop=backdrop,
        autoplay=autoplay,
        loop=loop,
        muted=muted,
        playsinline=playsinline,
        object_fit=object_fit,
        element_id=element_id,
        backdrop_id=backdrop_id,
    )
    st.html(html, unsafe_allow_javascript=True)
