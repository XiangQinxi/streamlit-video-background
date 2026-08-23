# streamlit-video-background

A small, reusable **Streamlit extension** that renders a fullscreen, blurred,
translucent **video as the page background**, with a backdrop color that follows
the Light/Dark theme — including live theme switching and an opaque, readable
sidebar on mobile.

> Build & distribute with **Poetry**. ``poetry build`` produces both ``sdist`` and
> ``wheel``; install via ``pip`` or publish to PyPI.

## What it does

```python
import streamlit as st
from streamlit_video_background import render_video_background, configure_static_serving

st.set_page_config("Demo", layout="wide")

# Ensure Streamlit serves the app's `static/` folder (and warn you to restart).
configure_static_serving()          # sets `server.enableStaticServing = true`

render_video_background(
    "/app/static/background_720p.mp4",  # a URL (recommended) ...
    blur="8px",                         # CSS blur on the video
    opacity=0.5,                        # translucent video (0..1)
)
st.title("Welcome")
```

- The video sits fixed behind the page content (``z-index:-1``), so it never
  intercepts clicks.
- Blur + opacity give a soft, readable background.
- A JS watcher keeps the backdrop in sync with the **actual live theme**, so
  switching Light ↔ Dark updates the backdrop instantly (Streamlit does **not**
  rerun the script on a theme switch, so ``st.context.theme.type`` alone isn't
  enough).
- The top nav and the sidebar keep their own opaque theme background, so the
  mobile nav drawer stays readable.

## Installation

```bash
pip install streamlit-video-background
```

Alternatively, build locally:

```bash
git clone <your-repo> && cd streamlit-video-background
poetry install          # dev environment
poetry build            # produces dist/*.whl and dist/*.tar.gz
pip install dist/*.whl
```

## Setup for a local video file

Streamlit serves everything in the ``static/`` folder of your app directory at
``/app/static/<name>`` when ``server.enableStaticServing`` is enabled.

```python
from streamlit_video_background import ensure_static, render_video_background

url = ensure_static("path/to/background.mp4", project_root=".")  # copies into ./static/
render_video_background(url)
```

Enable static serving in `.streamlit/config.toml` (or let
``configure_static_serving()`` do it):

```toml
[server]
runOnSave = true
enableStaticServing = true
```

> ``enableStaticServing`` is a **server-level** option: restart Streamlit after
> changing it.

### Embed the video (works anywhere — recommended for Community Cloud)

`static/` file serving is not reliably available on **Streamlit Community Cloud**
(and a `.mp4` may even be served with a `text/plain` content-type there). To make
sure the background works on any host, embed a small video as base64 with
``embed=True`` and pass a **local file path**:

```python
from streamlit_video_background import render_video_background
from pathlib import Path

render_video_background(
    Path(__file__).parent / "static" / "bg.mp4",  # committed to the repo
    embed=True,          # base64 data: URI — no static serving needed
    blur="8px",
    opacity=0.5,
)
```

Keep the embedded file tiny (compressed + blurred, a few hundred KB) so the page
payload stays small — use ``compress_video(..., scale=480, blur=3, crf=30)`` to
prepare one. The file must be committed to the repo so the app can read it at
runtime.

## Compress a heavy video (optional)

Backgrounds don't need 1080p or a high bitrate. ``compress_video`` downsizes and
re-encodes with FFmpeg (called from ``round()`` / CLI / notebook):

```python
from streamlit_video_background import compress_video, probe

info = probe("background.mp4")           # duration, bitrate, dimensions
compress_video("background.mp4",
               output_path="static/background_720p.mp4",
               scale=1280, crf=27, fps=20)
```

### Bake the blur into the file instead of CSS

Pass ``blur=8`` to ``compress_video`` to burn a box blur into the output. If you
do, set ``blur="0px"`` in ``render_video_background`` to avoid a double blur.

## API

| Function | Purpose |
|---|---|
| ``render_video_background(video_source, *, blur, opacity, backdrop_light, backdrop_dark, autoplay, loop, muted, playsinline, object_fit)`` | Render the background into the current page. |
| ``build_background_html(video_url, **options)`` | Pure HTML/CSS/JS builder (testable, no Streamlit). |
| ``ensure_static(video_file, project_root=None, *, overwrite=False)`` | Copy a video into ``static/`` and return the URL. |
| ``static_url(name)`` | Build `/app/static/<name>`. |
| ``static_serving_enabled()`` | Whether ``enableStaticServing`` is on. |
| ``configure_static_serving(enable=True, project_root=None)`` | Idempotently set `enableStaticServing` in `config.toml`. |
| ``compress_video(input, output=None, *, scale, crf, preset, fps, blur, keep_audio)`` | FFmpeg compression helper. |
| ``probe(path)`` | FFprobe metadata helper. |

## Notes

- The background is injected via ``st.html(..., unsafe_allow_javascript=True)``.
  The JavaScript only reads the live theme and adjusts a ``background-color``; it
  does not call out to the network or touch user data.
- Tune ``blur`` and ``opacity`` freely; the backdrop colors default to the
  standard Streamlit light/dark background but can be overridden.

## License

MIT
