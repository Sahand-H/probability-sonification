"""Shared page-level visual styling for direct and navigated routes."""

import streamlit as st


SURFACE_THEME_CSS = """
<style>
:root {
    --app-bg: light-dark(#f6f2ea, #1b1a1d);
    --app-surface: light-dark(#fbf8f2, #222125);
    --app-text: light-dark(#242128, #f2eee8);
    --purple-accent: light-dark(#7367a9, #a99bd4);
    --sage-accent: light-dark(#748668, #afbea3);
    --cyan-accent: light-dark(#57939d, #8fc3cb);
    --amber-accent: light-dark(#b88635, #dcba7b);
    --purple-surface: light-dark(#e6e0f1, #383346);
    --sage-surface: light-dark(#e3e8dc, #30382e);
    --cyan-surface: light-dark(#dcebee, #293b3e);
    --amber-surface: light-dark(#f2e4c9, #413727);
    --app-line: light-dark(rgba(47, 41, 51, .18), rgba(255, 255, 255, .16));
    --app-shadow: 0 24px 70px light-dark(
        rgba(55, 45, 55, .12), rgba(0, 0, 0, .32)
    );
}

.stApp {
    background-color: var(--app-bg);
    background-image:
        radial-gradient(
            circle at 82% 8%,
            color-mix(in srgb, var(--purple-accent) 14%, transparent),
            transparent 24rem
        ),
        radial-gradient(
            circle at 12% 88%,
            color-mix(in srgb, var(--sage-accent) 10%, transparent),
            transparent 28rem
        );
}

.stApp,
.stApp button,
.stApp input,
.stApp select,
.stApp textarea {
    font-family: Manrope, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
}

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    font-family: Manrope, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
    font-weight: 600;
    line-height: 1.08;
    letter-spacing: -.045em;
}

.stApp h1 { letter-spacing: -.06em; }

.block-container {
    max-width: 1200px;
    padding-top: 4.5rem;
    padding-bottom: 5rem;
}

.stApp p { line-height: 1.7; }

[data-testid="stSidebar"] { border-right: 1px solid var(--app-line); }

[data-testid="stSidebarNav"] a {
    border-radius: .5rem;
    font-size: .82rem;
    font-weight: 600;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: var(--app-surface);
    box-shadow: 0 2px 8px color-mix(
        in srgb, var(--app-text) 5%, transparent
    );
}

[data-testid="stCaptionContainer"] {
    color: var(--purple-accent);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: .68rem;
    font-weight: 500;
    letter-spacing: .08em;
    text-transform: uppercase;
}

.stButton > button,
.stDownloadButton > button {
    min-height: 2.75rem;
    font-size: .8rem;
    font-weight: 700;
    transition: transform 180ms ease, box-shadow 180ms ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px color-mix(
        in srgb, var(--app-text) 12%, transparent
    );
}

div[data-testid="stExpander"] {
    border: 2px solid color-mix(
        in srgb, var(--purple-accent) 55%, var(--app-line)
    );
    border-radius: .75rem;
    background: var(--purple-surface);
    overflow: hidden;
}

[data-testid="stMetric"] {
    padding: 1rem;
    border: 2px solid color-mix(
        in srgb, var(--cyan-accent) 60%, var(--app-line)
    );
    border-radius: .75rem;
    background: var(--cyan-surface);
}

[data-testid="stAudio"] {
    display: block;
    box-sizing: border-box;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    padding: 0;
    border: 2px solid var(--app-line);
    border-radius: .75rem;
    background: var(--app-surface);
    overflow: hidden;
}

[data-testid="stAlertContainer"] { border-radius: .75rem; }

[data-testid="stVegaLiteChart"],
[data-testid="stPlotlyChart"] {
    box-sizing: border-box;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
    overflow: visible;
}

[data-testid="stVegaLiteChart"] > svg,
[data-testid="stPlotlyChart"] > div {
    display: block;
    max-width: 100%;
}

[data-testid="stColumn"] { min-width: 0; }

div[class*="st-key-experiment-control-card-"],
div[class*="st-key-generated-section-"] {
    min-width: 0;
    padding: 1.25rem;
    border: 2px solid var(--app-line);
    border-radius: 1rem;
    box-shadow: 0 8px 28px color-mix(
        in srgb, var(--app-text) 8%, transparent
    );
}

div[class*="st-key-generated-section-"] { margin-top: 1rem; }

div.st-key-experiment-control-card-a,
div.st-key-generated-section-summary,
div.st-key-generated-section-distribution-a {
    border-color: var(--cyan-accent);
    background: var(--cyan-surface);
}

div.st-key-experiment-control-card-b,
div.st-key-generated-section-distribution-b {
    border-color: var(--sage-accent);
    background: var(--sage-surface);
}

div.st-key-generated-section-audio {
    border-color: var(--sage-accent);
    background: var(--sage-surface);
}

div.st-key-generated-section-audio .stDownloadButton > button {
    border-color: var(--sage-accent);
    background: var(--sage-accent);
    color: light-dark(#ffffff, #1b1a1d);
}

div.st-key-generated-section-audio .stDownloadButton > button:hover {
    border-color: var(--sage-accent);
    background: color-mix(in srgb, var(--sage-accent) 84%, var(--app-text));
    color: light-dark(#ffffff, #1b1a1d);
}

div.st-key-generated-section-visualizations {
    border-color: var(--purple-accent);
    background: var(--purple-surface);
}

div.st-key-generated-section-clipping {
    border-color: var(--cyan-accent);
    background: var(--cyan-surface);
}

div.st-key-generated-section-distribution-a [data-testid="stMetric"],
div.st-key-generated-section-distribution-b [data-testid="stMetric"] {
    border-color: var(--amber-accent);
    background: var(--amber-surface);
}

/* The page link remains semantic and keyboard-accessible while filling the card. */
div[class*="st-key-experiment-card-"] {
    position: relative;
    min-height: 14rem;
    padding: .45rem;
    border: 2px solid color-mix(
        in srgb, var(--purple-accent) 55%, var(--app-line)
    );
    border-radius: 1.25rem;
    background: linear-gradient(
        145deg,
        var(--app-surface),
        color-mix(in srgb, var(--app-surface) 76%, var(--purple-accent))
    );
    box-shadow: 0 8px 28px color-mix(
        in srgb, var(--app-text) 8%, transparent
    );
    transition: border-color 180ms ease, box-shadow 180ms ease,
        transform 180ms ease;
}

div[class*="st-key-experiment-card-"]:hover {
    border-color: var(--purple-accent);
    box-shadow: var(--app-shadow);
    transform: translateY(-5px);
}

div[class*="st-key-experiment-card-"]:focus-within {
    outline: 3px solid color-mix(
        in srgb, var(--purple-accent) 55%, transparent
    );
    outline-offset: 3px;
    border-color: var(--purple-accent);
}

div[class*="st-key-experiment-card-"]
    [data-testid="stElementContainer"]:has([data-testid="stPageLink"]) {
    position: static;
}

div[class*="st-key-experiment-card-"] [data-testid="stPageLink"] {
    position: absolute;
    inset: 0;
    z-index: 2;
}

div[class*="st-key-experiment-card-"] [data-testid="stPageLink"] > div {
    height: 100%;
}

div[class*="st-key-experiment-card-"] [data-testid="stPageLink"] a {
    width: 100%;
    height: 100%;
    border: 0;
    border-radius: 1.25rem;
    background: transparent;
    color: transparent;
    cursor: pointer;
}

div[class*="st-key-experiment-card-"] [data-testid="stPageLink"] a:hover {
    border: 0;
    background: transparent;
    color: transparent;
}

div[class*="st-key-experiment-card-"] [data-testid="stPageLink"] a > * {
    opacity: 0;
}
</style>
"""


def apply_surface_theme() -> None:
    """Inject section colors on the current page, including direct routes."""

    st.markdown(SURFACE_THEME_CSS, unsafe_allow_html=True)
