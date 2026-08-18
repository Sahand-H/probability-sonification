from probability_sonification.stochastic_music import (
    DrumSoundSamplingConfig,
    EventCountSamplingConfig,
    EventMatrix,
    EventPitchSamplingConfig,
    EventTimeSamplingConfig,
    InstrumentDefinition,
    MusicalEvent,
    SamplingBackend,
    StochasticMusicConfig,
    drum_sound_distribution_plot,
    event_matrix_plot,
    event_pitch_distribution_plot,
    event_timeline_plot,
    note_map_plot,
)
import numpy as np


INSTRUMENTS = ("Acoustic Grand Piano", "Violin")
EVENTS = (
    MusicalEvent(0, INSTRUMENTS[0], 0, 0, 1.0, 2.0, 60, 90),
    MusicalEvent(1, INSTRUMENTS[1], 1, 0, 6.0, 2.0, 64, 90),
)


def make_config() -> StochasticMusicConfig:
    return StochasticMusicConfig(
        selected_instruments=(
            InstrumentDefinition(INSTRUMENTS[0], "Piano", 0),
            InstrumentDefinition(INSTRUMENTS[1], "Solo strings", 40),
        ),
        composition_duration=10,
        n_time_blocks=2,
        note_duration=2,
        note_velocity=90,
        sampling_backend=SamplingBackend.SCIPY,
        random_seed=42,
        event_count_sampling=EventCountSamplingConfig(2.5),
        event_time_sampling=EventTimeSamplingConfig(),
        event_pitch_sampling=EventPitchSamplingConfig(60, 10, 0, 127),
        drum_sound_sampling=DrumSoundSamplingConfig((36, 38), (0.5, 0.5)),
    )


def test_event_matrix_plot_contains_every_matrix_cell():
    matrix = EventMatrix(np.array([[1, 2], [3, 4]]), INSTRUMENTS)

    spec = event_matrix_plot(matrix).to_dict()

    assert spec["title"] == "Event matrix"
    assert len(spec["data"]["values"]) == 4


def test_event_timeline_plot_contains_boundaries_and_events():
    spec = event_timeline_plot(EVENTS, make_config()).to_dict()

    assert spec["title"] == "Event timeline"
    assert len(spec["layer"]) == 2
    assert spec["layer"][0]["data"]["values"] == [{"Boundary": 5.0}]
    assert len(spec["layer"][1]["data"]["values"]) == 2


def test_event_pitch_distribution_plot_uses_approved_title():
    spec = event_pitch_distribution_plot(EVENTS, INSTRUMENTS).to_dict()

    assert spec["title"] == "Event pitch distribution"
    assert len(spec["data"]["values"]) == 2


def test_note_map_plot_contains_note_spans():
    spec = note_map_plot(EVENTS, INSTRUMENTS).to_dict()

    assert spec["title"] == "Note map"
    assert spec["data"]["values"][0]["Start time"] == 1.0
    assert spec["data"]["values"][0]["End time"] == 3.0


def test_drum_sound_distribution_uses_general_midi_drum_names():
    drum_event = MusicalEvent(
        0, "Drum Kit", 0, 0, 1.0, 1.0, 38, 90, is_drum=True
    )

    spec = drum_sound_distribution_plot((drum_event,), ("Drum Kit",)).to_dict()

    assert spec["title"] == "Drum sound distribution"
    assert spec["data"]["values"][0]["Drum sound"] == "Acoustic Snare"


def test_event_plots_accept_empty_event_results():
    timeline_spec = event_timeline_plot((), make_config()).to_dict()
    pitch_spec = event_pitch_distribution_plot((), INSTRUMENTS).to_dict()
    note_spec = note_map_plot((), INSTRUMENTS).to_dict()

    assert timeline_spec["layer"][1]["data"]["values"] == []
    assert pitch_spec["data"]["values"] == []
    assert note_spec["data"]["values"] == []
