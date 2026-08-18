import streamlit as st

from probability_sonification.theme import apply_surface_theme


st.set_page_config(
    page_title="Probability Sonification Lab",
    page_icon="♫",
    layout="wide",
)
apply_surface_theme()

navigation = st.navigation(
    [
        st.Page(
            "pages/landing.py",
            title="Probability Sonification Lab",
            icon=":material/home:",
            default=True,
        ),
        st.Page(
            "pages/experiment_1.py",
            title="Distribution Sonification",
            icon=":material/graphic_eq:",
        ),
        st.Page(
            "pages/experiment_2.py",
            title="Stochastic Music Generator",
            icon=":material/music_note:",
        ),
    ]
)
navigation.run()
