import numpy as np
import pytest

from probability_sonification.stochastic_music import (
    DrumSoundSamplingConfig,
    EventCountSamplingConfig,
    EventMatrix,
    EventPitchSamplingConfig,
    EventTimeSamplingConfig,
    InstrumentDefinition,
    SamplingBackend,
    StochasticMusicConfig,
)


def make_config(**overrides) -> StochasticMusicConfig:
    instruments = (
        InstrumentDefinition("Acoustic Grand Piano", "Piano", 0),
        InstrumentDefinition("Violin", "Solo strings", 40),
    )
    values = {
        "selected_instruments": instruments,
        "composition_duration": 60.0,
        "n_time_blocks": 12,
        "note_duration": 2.0,
        "note_velocity": 90,
        "sampling_backend": SamplingBackend.SCIPY,
        "random_seed": 42,
        "event_count_sampling": EventCountSamplingConfig(rate=2.5),
        "event_time_sampling": EventTimeSamplingConfig(),
        "event_pitch_sampling": EventPitchSamplingConfig(
            mean=60,
            standard_deviation=10,
            minimum_pitch=0,
            maximum_pitch=127,
        ),
        "drum_sound_sampling": DrumSoundSamplingConfig(
            sounds=(36, 38),
            probabilities=(0.5, 0.5),
        ),
    }
    values.update(overrides)
    return StochasticMusicConfig(**values)


def test_stochastic_music_config_accepts_reviewed_settings():
    config = make_config()

    assert [instrument.name for instrument in config.selected_instruments] == [
        "Acoustic Grand Piano",
        "Violin",
    ]
    assert config.random_seed == 42


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"selected_instruments": ()}, "At least one instrument"),
        ({"composition_duration": 0}, "Composition duration"),
        ({"n_time_blocks": 0}, "time blocks"),
        ({"note_duration": 0}, "Note duration"),
        ({"note_velocity": 128}, "Note velocity"),
        ({"random_seed": -1}, "Random seed"),
    ],
)
def test_stochastic_music_config_rejects_invalid_settings(override, message):
    with pytest.raises(ValueError, match=message):
        make_config(**override)


def test_event_matrix_exposes_shape_and_total_without_mutable_counts():
    source = np.array([[1, 2, 0], [3, 1, 2]])
    matrix = EventMatrix(source, ("Piano", "Violin"))
    source[0, 0] = 99

    assert matrix.n_instruments == 2
    assert matrix.n_time_blocks == 3
    assert matrix.total_event_count == 9
    assert matrix.counts[0, 0] == 1
    assert not matrix.counts.flags.writeable


def test_event_matrix_rejects_non_integer_counts():
    with pytest.raises(ValueError, match="must be integers"):
        EventMatrix(np.array([[1.5]]), ("Piano",))


def test_sampling_configs_validate_distribution_parameters():
    with pytest.raises(ValueError, match="Event rate"):
        EventCountSamplingConfig(rate=-0.1)
    with pytest.raises(ValueError, match="standard deviation"):
        EventPitchSamplingConfig(60, 0, 0, 127)
    with pytest.raises(ValueError, match="valid MIDI range"):
        EventPitchSamplingConfig(60, 10, -1, 127)
    with pytest.raises(ValueError, match="sum to one"):
        DrumSoundSamplingConfig((36, 38), (0.2, 0.2))
