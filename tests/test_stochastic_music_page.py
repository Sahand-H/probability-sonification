from streamlit.testing.v1 import AppTest

from probability_sonification.stochastic_music.page import (
    AVAILABLE_INSTRUMENTS,
)


def test_stochastic_music_page_initial_controls():
    app = AppTest.from_string(
        "from probability_sonification.stochastic_music.page import "
        "render_stochastic_music_experiment\n"
        "render_stochastic_music_experiment()"
    )

    app.run()

    assert not app.exception
    assert app.title[0].value == "Stochastic Music Generator"
    assert len(app.checkbox) == len(AVAILABLE_INSTRUMENTS)
    assert sum(checkbox.value for checkbox in app.checkbox) == 4
    assert app.selectbox[0].value == "scipy"
    assert app.toggle[0].label == "Use reproducible seed"
    assert app.toggle[0].value is False
    assert "Random seed" not in [widget.label for widget in app.number_input]
    assert app.button[0].label == "Generate preview"

    app.toggle[0].set_value(True).run()

    assert "Random seed" in [widget.label for widget in app.number_input]
