import pretty_midi
from streamlit.testing.v1 import AppTest

from probability_sonification.stochastic_music.page import (
    AVAILABLE_INSTRUMENTS,
    DEFAULT_DRUM_PROBABILITIES,
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
    detailed_instrument_buttons = [
        button
        for button in app.button
        if str(button.key).startswith("stochastic-instrument-button-")
    ]
    assert len(detailed_instrument_buttons) == len(AVAILABLE_INSTRUMENTS)
    assert sum(
        bool(app.session_state[f"stochastic-instrument-{instrument.name}"])
        for instrument in AVAILABLE_INSTRUMENTS
    ) == 4
    backend = next(
        selectbox for selectbox in app.selectbox if selectbox.label == "Sampling backend"
    )
    assert backend.value == "scipy"
    customize_toggle = next(
        toggle
        for toggle in app.toggle
        if toggle.key == "stochastic-customize-sampling"
    )
    seed_toggle = next(
        toggle for toggle in app.toggle if toggle.key == "stochastic-use-seed"
    )
    assert customize_toggle.value is False
    assert seed_toggle.value is False
    assert "Random seed" not in [widget.label for widget in app.number_input]
    assert "Generate preview" in [button.label for button in app.button]
    assert "How sampling works" in [expander.label for expander in app.expander]
    assert any(latex.value for latex in app.latex)
    assert any(
        "not measurements from a drum corpus" in caption.value
        for caption in app.caption
    )

    instrument_labels = {button.label for button in detailed_instrument_buttons}
    assert instrument_labels == {
        instrument.name for instrument in AVAILABLE_INSTRUMENTS
    }
    assert "Electric Bass (finger)" not in instrument_labels
    assert [group_name for group_name, _ in INSTRUMENT_GROUPS] == [
        "Piano",
        "Chromatic percussion",
        "Organ",
        "Guitar",
        "Bass",
        "Solo strings",
        "Ensemble",
        "Brass",
        "Reed",
        "Pipe",
        "Percussive",
        "Percussion and drums",
    ]
    assert "work in progress" in app.info[0].value

    seed_toggle.set_value(True).run()

    assert "Random seed" in [widget.label for widget in app.number_input]


def test_all_instrument_options_are_valid_general_midi_names():
    for instrument in AVAILABLE_INSTRUMENTS:
        if instrument.is_drum:
            assert instrument.program == 0
        else:
            assert pretty_midi.instrument_name_to_program(instrument.name) == instrument.program


def test_per_instrument_sampling_controls_start_with_shared_profiles():
    app = AppTest.from_string(
        "from probability_sonification.stochastic_music.page import "
        "render_stochastic_music_experiment\n"
        "render_stochastic_music_experiment()"
    )
    app.run()

    customize_toggle = next(
        toggle
        for toggle in app.toggle
        if toggle.key == "stochastic-customize-sampling"
    )
    customize_toggle.set_value(True).run()

    assert not app.exception
    shared_profile_checkboxes = [
        checkbox
        for checkbox in app.checkbox
        if str(checkbox.key).startswith("stochastic-use-shared-sampling-")
    ]
    assert len(shared_profile_checkboxes) == 4
    assert not any(checkbox.value for checkbox in shared_profile_checkboxes)

    distribution_labels = [selectbox.label for selectbox in app.selectbox]
    assert distribution_labels.count("Event-count distribution") == 5
    assert distribution_labels.count("Event-time distribution") == 5
    assert distribution_labels.count("Event-pitch distribution") == 5


def test_selected_instrument_can_be_removed_from_summary():
    app = AppTest.from_string(
        "from probability_sonification.stochastic_music.page import "
        "render_stochastic_music_experiment\n"
        "render_stochastic_music_experiment()"
    )
    app.run()

    remove_piano = next(
        button
        for button in app.button
        if button.key == "stochastic-remove-instrument-Acoustic Grand Piano"
    )
    remove_piano.click().run()

    assert not app.exception
    assert app.session_state["stochastic-instrument-Acoustic Grand Piano"] is False
    assert not any(
        button.key == "stochastic-remove-instrument-Acoustic Grand Piano"
        for button in app.button
    )


def test_guided_setup_advances_from_instruments_to_generation_review():
    app = AppTest.from_string(
        "from probability_sonification.stochastic_music.page import "
        "render_stochastic_music_experiment\n"
        "render_stochastic_music_experiment()"
    )
    app.run()

    confirm_instruments = next(
        button for button in app.button if button.label == "Confirm instruments"
    )
    confirm_instruments.click().run()

    assert not app.exception
    assert any(caption.value == "Step 2 of 3" for caption in app.caption)
    confirm_composition = next(
        button for button in app.button if button.label == "Confirm composition"
    )
    confirm_composition.click().run()

    assert not app.exception
    assert any(button.label == "Generate music" for button in app.button)


def test_guided_instrument_buttons_can_deselect_an_instrument():
    app = AppTest.from_string(
        "from probability_sonification.stochastic_music.page import "
        "render_stochastic_music_experiment\n"
        "render_stochastic_music_experiment()"
    )
    app.run()

    guided_piano = next(
        button
        for button in app.button
        if button.key == "guided-instrument-button-Acoustic Grand Piano"
    )
    guided_piano.click().run()
    next(
        button for button in app.button if button.label == "Confirm instruments"
    ).click().run()

    assert not app.exception
    assert "Acoustic Grand Piano" not in app.session_state["guided-setup-draft"][
        "selected_names"
    ]


def test_guided_setup_includes_sampling_step_when_customization_is_enabled():
    app = AppTest.from_string(
        "from probability_sonification.stochastic_music.page import "
        "render_stochastic_music_experiment\n"
        "render_stochastic_music_experiment()"
    )
    app.run()

    guided_toggle = next(
        toggle for toggle in app.toggle if toggle.key == "guided-customize-sampling"
    )
    guided_toggle.set_value(True)
    next(
        button for button in app.button if button.label == "Confirm instruments"
    ).click().run()

    assert not app.exception
    assert any(caption.value == "Step 2 of 4" for caption in app.caption)
    assert any(button.label == "Confirm sampling" for button in app.button)
    assert any(caption.value == "Instrument 1 of 4" for caption in app.caption)

    next(
        button for button in app.button if button.label == "Confirm sampling"
    ).click().run()

    assert not app.exception
    assert any(caption.value == "Instrument 2 of 4" for caption in app.caption)
    assert not any(
        button.label == "Confirm composition" for button in app.button
    )


def test_guided_setup_can_start_over():
    app = AppTest.from_string(
        "from probability_sonification.stochastic_music.page import "
        "render_stochastic_music_experiment\n"
        "render_stochastic_music_experiment()"
    )
    app.run()

    next(
        button for button in app.button if button.label == "Confirm instruments"
    ).click().run()
    assert any(caption.value == "Step 2 of 3" for caption in app.caption)

    next(button for button in app.button if button.label == "Start over").click().run()

    assert not app.exception
    assert any(caption.value == "Step 1 of 3" for caption in app.caption)
    assert "guided-setup-draft" in app.session_state
    assert not app.session_state["guided-setup-draft"]


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
    probability_by_name = dict(
        zip(
            (
                pretty_midi.note_number_to_drum_name(note_number)
                for note_number in DEFAULT_DRUM_SOUNDS
            ),
            DEFAULT_DRUM_PROBABILITIES,
            strict=True,
        )
    )
    assert abs(sum(DEFAULT_DRUM_PROBABILITIES) - 1.0) < 1e-12
    assert probability_by_name["Closed Hi Hat"] > probability_by_name["Crash Cymbal 1"]
    assert probability_by_name["Bass Drum 1"] > probability_by_name["Low Tom"]
    assert probability_by_name["Acoustic Snare"] > probability_by_name["Ride Cymbal 1"]
