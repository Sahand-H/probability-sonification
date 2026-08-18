import numpy as np
import pytest

from probability_sonification.stochastic_music import (
    EventCountSamplingConfig,
    EventPitchSamplingConfig,
    EventTimeSamplingConfig,
    MusicalEvent,
    SamplerMetadata,
    SamplerSuite,
    SamplingBackend,
    StochasticMusicConfig,
    build_midi,
    create_scipy_sampler_suite,
    generate_stochastic_music,
    midi_to_bytes,
)


def make_config() -> StochasticMusicConfig:
    return StochasticMusicConfig(
        selected_instruments=("Acoustic Grand Piano", "Violin"),
        composition_duration=10,
        n_time_blocks=2,
        note_duration=2,
        note_velocity=90,
        sampling_backend=SamplingBackend.SCIPY,
        random_seed=42,
        event_count_sampling=EventCountSamplingConfig(rate=1.5),
        event_time_sampling=EventTimeSamplingConfig(),
        event_pitch_sampling=EventPitchSamplingConfig(60, 5, 48, 72),
    )


def test_build_midi_preserves_track_order_and_event_timing():
    instruments = ("Acoustic Grand Piano", "Violin")
    events = (
        MusicalEvent(1, "Violin", 0, 0, 1.5, 2.0, 64, 90),
        MusicalEvent(0, "Acoustic Grand Piano", 0, 0, 0.5, 2.0, 60, 80),
    )

    midi = build_midi(events, instruments)

    assert [track.name for track in midi.instruments] == list(instruments)
    assert midi.instruments[0].notes[0].start == 0.5
    assert midi.instruments[0].notes[0].end == 2.5
    assert midi.instruments[1].notes[0].pitch == 64


def test_build_midi_keeps_silent_selected_instruments():
    midi = build_midi((), ("Acoustic Grand Piano", "Violin"))

    assert len(midi.instruments) == 2
    assert all(not track.notes for track in midi.instruments)


def test_midi_to_bytes_returns_standard_midi_data():
    midi = build_midi((), ("Acoustic Grand Piano",))

    assert midi_to_bytes(midi).startswith(b"MThd")


def test_generate_stochastic_music_returns_reproducible_complete_result():
    config = make_config()
    suite = create_scipy_sampler_suite()

    first = generate_stochastic_music(config, suite)
    second = generate_stochastic_music(config, suite)

    assert np.array_equal(first.event_matrix.counts, second.event_matrix.counts)
    assert first.events == second.events
    assert first.midi_bytes == second.midi_bytes
    assert first.config is config
    assert first.sampler_metadata.backend is SamplingBackend.SCIPY


def test_generate_stochastic_music_rejects_mismatched_metadata_backend():
    scipy_suite = create_scipy_sampler_suite()

    class DifferentBackend(str):
        pass

    # A malformed suite is rejected before any sampler runs.
    suite = SamplerSuite(
        backend=SamplingBackend.SCIPY,
        event_count_sampler=scipy_suite.event_count_sampler,
        event_time_sampler=scipy_suite.event_time_sampler,
        event_pitch_sampler=scipy_suite.event_pitch_sampler,
        metadata=SamplerMetadata(
            backend=DifferentBackend("other"),
            event_count={},
            event_time={},
            event_pitch={},
        ),
    )

    with pytest.raises(ValueError, match="metadata backend"):
        generate_stochastic_music(make_config(), suite)
