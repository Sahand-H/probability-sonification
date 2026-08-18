from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parents[1]


def test_navigation_defaults_to_experiment_1():
    app = AppTest.from_file(ROOT / "app.py").run()

    assert not app.exception
    assert app.title[0].value == "Basic sonification of probability distributions."
    assert app.button[0].label == "Generate comparison"


def test_experiment_2_is_a_coming_soon_placeholder():
    app = AppTest.from_file(ROOT / "pages" / "experiment_2.py").run()

    assert not app.exception
    assert app.title[0].value == "Experiment 2"
    assert app.info[0].value == "Coming soon."
