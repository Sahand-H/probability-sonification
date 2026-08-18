import streamlit as st


st.set_page_config(
    page_title="Probability Sonification",
    page_icon="♫",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root { --rust-accent: #cf704c; --sage-accent: #82a58f; }
    .stApp {
        background: var(--background-color);
        color: var(--text-color);
    }
    .block-container { max-width: 1180px; padding-top: 3rem; }
    h1, h2, h3 { letter-spacing: -0.025em; }
    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
        padding: .75rem;
    }
    div[data-testid="stExpander"] {
        border-color: color-mix(in srgb, var(--text-color) 18%, transparent);
        background: var(--secondary-background-color);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

navigation = st.navigation(
    [
        st.Page(
            "pages/experiment_1.py",
            title="Experiment 1",
            icon=":material/graphic_eq:",
            default=True,
        ),
        st.Page(
            "pages/experiment_2.py",
            title="Experiment 2",
            icon=":material/music_note:",
        ),
    ]
)
navigation.run()
