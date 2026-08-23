"""Unit tests for the HTML builder and URL helpers (no Streamlit runtime needed)."""

from streamlit_video_background import build_background_html
from streamlit_video_background.serving import resolve_video_source, static_url


def test_static_url():
    assert static_url("bg.mp4") == "/app/static/bg.mp4"


def test_resolve_passthrough_urls():
    assert resolve_video_source("https://example.com/bg.mp4") == "https://example.com/bg.mp4"
    assert resolve_video_source("/app/static/bg.mp4") == "/app/static/bg.mp4"


def test_resolve_filename_to_static():
    assert resolve_video_source("bg.mp4") == "/app/static/bg.mp4"


def test_resolve_none():
    assert resolve_video_source(None) is None


def test_build_html_includes_video_styles():
    html = build_background_html(
        "/app/static/bg.mp4", blur="8px", opacity=0.5, backdrop="#FFFFFF"
    )
    assert 'src="/app/static/bg.mp4"' in html
    assert "filter:blur(8px)" in html
    assert "opacity:0.5" in html
    assert "background-color:#FFFFFF" in html
    assert "unsafe" not in html  # the HTML itself is neutral; st.html adds the flag


def test_build_html_autoplay_muted_present():
    html = build_background_html("bg.mp4")
    assert "autoplay" in html
    assert "muted" in html
    assert "loop" in html
    assert "playsinline" in html
