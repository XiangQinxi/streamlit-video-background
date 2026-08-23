"""Minimal working example for streamlit-video-background.

Run from the package directory (or after ``pip install -e .``):

    streamlit run examples/demo.py
"""

import streamlit as st

from streamlit_video_background import configure_static_serving, render_video_background

st.set_page_config("Video BG Demo", page_icon=":material/movie:", layout="wide")

# If the file already lives in your app's `static/` folder, just use its URL.
# Otherwise call `ensure_static("path/to/bg.mp4", project_root=".")` to copy it in.
VIDEO_SOURCE = "/app/static/background_720p.mp4"

# Make sure Streamlit serves the `static/` folder (warns you to restart if needed).
configure_static_serving(print_warning=True)

render_video_background(
    VIDEO_SOURCE,
    blur="8px",       # CSS blur on the video
    opacity=0.5,      # translucent video
    backdrop_light="#FFFFFF",  # light-theme backdrop under the video
    backdrop_dark="#0E0E0E",   # dark-theme backdrop under the video
)

st.title("Fullscreen video background")
st.caption(
    "Open the settings menu and switch the theme, or narrow the window to a phone "
    "width: the backdrop follows the theme and the sidebar stays readable."
)
