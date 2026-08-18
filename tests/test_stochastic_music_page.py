import pretty_midi
from streamlit.testing.v1 import AppTest

from probability_sonification.stochastic_music.page import (
    AVAILABLE_INSTRUMENTS,
    DEFAULT_DRUM_SOUNDS,
    INSTRUMENT_GROUPS,
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

    checkbox_labels = [checkbox.label for checkbox in app.checkbox]
    assert "Alto Sax" in checkbox_labels
    assert "French Horn" in checkbox_labels
    assert "Recorder" in checkbox_labels
    assert "Clarinet" in checkbox_labels
    assert "Electric Bass (pick)" in checkbox_labels
    assert "Electric Bass (finger)" not in checkbox_labels
    assert "Electric Piano 1" in checkbox_labels
    assert "Xylophone" in checkbox_labels
    assert "Harmonica" in checkbox_labels
    assert "Trumpet" in checkbox_labels
    assert "Trombone" in checkbox_labels
    assert "Drum Kit" in checkbox_labels
    assert [group_name for group_name, _ in INSTRUMENT_GROUPS] == [
        "Piano",
        "Chromatic percussion",
        "Organ",
        "Guitar",
        "Bass",
        "Solo strings",
        "Brass",
        "Reed",
        "Pipe",
        "Percussive",
        "Percussion and drums",
    ]
    assert "work in progress" in app.info[0].value

    app.toggle[0].set_value(True).run()

    assert "Random seed" in [widget.label for widget in app.number_input]


def test_all_instrument_options_are_valid_general_midi_names():
    for instrument in AVAILABLE_INSTRUMENTS:
        if instrument.is_drum:
            assert instrument.program == 0
        else:
            assert pretty_midi.instrument_name_to_program(instrument.name) == instrument.program


def test_default_drum_palette_contains_common_kit_sounds():
    drum_names = {
        pretty_midi.note_number_to_drum_name(note_number)
        for note_number in DEFAULT_DRUM_SOUNDS
    }

    assert {
        "Bass Drum 1",
        "Acoustic Snare",
        "Closed Hi Hat",
        "Pedal Hi Hat",
        "Open Hi Hat",
        "Low Tom",
        "Hi-Mid Tom",
        "Crash Cymbal 1",
        "Ride Cymbal 1",
    } == drum_names
