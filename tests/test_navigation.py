from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parents[1]


def test_navigation_defaults_to_landing_page():
    app = AppTest.from_file(ROOT / "app.py").run()

    assert not app.exception
    assert app.title[0].value == "Probability Sonification Lab"
    assert [subheader.value for subheader in app.subheader] == [
        "Distribution Sonification",
        "Stochastic Music Generator",
    ]
    assert [caption.value for caption in app.caption] == [
        "Experiment 1",
        "Experiment 2",
    ]
    assert [link.proto.label for link in app.get("page_link")] == [
        "Open Distribution Sonification",
        "Open Stochastic Music Generator",
    ]
    landing_copy = [markdown.value for markdown in app.markdown]
    assert (
        "Compare probability distributions through sound and visualization."
        in landing_copy
    )
    assert "Build a composition from stochastic musical events." in landing_copy


def test_distribution_sonification_destination():
    app = AppTest.from_file(ROOT / "pages" / "experiment_1.py").run()

    assert not app.exception
    assert app.title[0].value == "Distribution Sonification"
    assert app.caption[0].value == "Experiment 1"
    assert app.button[0].label == "Generate comparison"
    assert app.toggle[0].label == "Use reproducible seed"
    assert app.toggle[0].value is False
    assert "Random seed" not in [widget.label for widget in app.number_input]
    instrument_defaults = [
        selectbox.value
        for selectbox in app.selectbox
        if selectbox.label == "Instrument"
    ]
    assert instrument_defaults == [
        "Acoustic Grand Piano",
        "Acoustic Grand Piano",
    ]


def test_distribution_sonification_reproducible_seed_control():
    app = AppTest.from_file(ROOT / "pages" / "experiment_1.py").run()

    app.toggle[0].set_value(True).run()

    assert not app.exception
    random_seed = next(
        widget for widget in app.number_input if widget.label == "Random seed"
    )
    assert random_seed.value == 42


def test_stochastic_music_generator_destination():
    app = AppTest.from_file(ROOT / "pages" / "experiment_2.py").run()

    assert not app.exception
    assert app.title[0].value == "Stochastic Music Generator"
    assert app.caption[0].value == "Experiment 2"
    assert "Generate preview" in [button.label for button in app.button]
