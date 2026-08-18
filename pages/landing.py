import streamlit as st


st.title("Probability Sonification Lab")
st.write("Choose an experiment to begin.")

distribution, stochastic_music = st.columns(2, gap="large")

with distribution:
    st.subheader("Distribution Sonification")
    st.caption("Experiment 1")
    st.write("Compare probability distributions through sound and visualization.")
    st.page_link(
        "pages/experiment_1.py",
        label="Open Distribution Sonification",
        icon=":material/graphic_eq:",
        width="stretch",
    )

with stochastic_music:
    st.subheader("Stochastic Music Generator")
    st.caption("Experiment 2")
    st.write("Build a composition from stochastic musical events.")
    st.page_link(
        "pages/experiment_2.py",
        label="Open Stochastic Music Generator",
        icon=":material/music_note:",
        width="stretch",
    )
