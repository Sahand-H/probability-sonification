import numpy as np
import pytest

from probability_sonification.stochastic_music import (
    DrumSoundSamplingConfig,
    EventCountSamplingConfig,
    EventCountDistribution,
    EventPitchSamplingConfig,
    EventPitchDistribution,
    EventTimeSamplingConfig,
    SamplingBackend,
    ScipyDrumSoundSampler,
    ScipyEventCountSampler,
    ScipyEventPitchSampler,
    ScipyEventTimeSampler,
    create_scipy_sampler_suite,
)


def test_event_count_sampler_is_seeded_and_returns_matrix_shape():
    sampler = ScipyEventCountSampler()
    config = EventCountSamplingConfig(rate=2.5)

    first = sampler.sample_event_counts(4, 12, config, random_seed=42)
    second = sampler.sample_event_counts(4, 12, config, random_seed=42)

    assert np.array_equal(first, second)
    assert first.shape == (4, 12)
    assert np.issubdtype(first.dtype, np.integer)
    assert np.all(first >= 0)


def test_event_time_sampler_returns_raw_bounded_draws():
    sampler = ScipyEventTimeSampler()

    times = sampler.sample_event_times(
        20,
        block_start=5.0,
        block_end=10.0,
        config=EventTimeSamplingConfig(),
        random_seed=42,
    )

    assert times.shape == (20,)
    assert np.all(times >= 5.0)
    assert np.all(times < 10.0)
    # The sampler deliberately leaves chronological sorting to the pipeline.
    assert np.any(times[1:] < times[:-1])


def test_event_pitch_sampler_rounds_and_clips_to_midi_limits():
    sampler = ScipyEventPitchSampler()
    config = EventPitchSamplingConfig(
        mean=60,
        standard_deviation=100,
        minimum_pitch=48,
        maximum_pitch=72,
    )

    pitches = sampler.sample_event_pitches(100, config, random_seed=42)

    assert pitches.shape == (100,)
    assert np.issubdtype(pitches.dtype, np.integer)
    assert np.all((pitches >= 48) & (pitches <= 72))
    assert 48 in pitches
    assert 72 in pitches


def test_drum_sound_sampler_uses_configured_categorical_choices():
    sampler = ScipyDrumSoundSampler()
    config = DrumSoundSamplingConfig(
        sounds=(36, 38, 42),
        probabilities=(0.2, 0.5, 0.3),
    )

    first = sampler.sample_drum_sounds(100, config, random_seed=42)
    second = sampler.sample_drum_sounds(100, config, random_seed=42)

    assert np.array_equal(first, second)
    assert set(first).issubset(config.sounds)
    assert np.issubdtype(first.dtype, np.integer)


def test_samplers_support_empty_output_requests():
    assert ScipyEventCountSampler().sample_event_counts(
        0, 3, EventCountSamplingConfig(2.5), random_seed=42
    ).shape == (0, 3)
    assert ScipyEventTimeSampler().sample_event_times(
        0, 0.0, 5.0, EventTimeSamplingConfig(), random_seed=42
    ).shape == (0,)
    assert ScipyEventPitchSampler().sample_event_pitches(
        0, EventPitchSamplingConfig(60, 10, 0, 127), random_seed=42
    ).shape == (0,)
    assert ScipyDrumSoundSampler().sample_drum_sounds(
        0, DrumSoundSamplingConfig((36,), (1.0,)), random_seed=42
    ).shape == (0,)


@pytest.mark.parametrize("invalid_count", [-1, -10])
def test_samplers_reject_negative_output_requests(invalid_count):
    with pytest.raises(ValueError, match="must be non-negative"):
        ScipyEventTimeSampler().sample_event_times(
            invalid_count, 0, 5, EventTimeSamplingConfig(), random_seed=42
        )


def test_sampler_suite_identifies_distributions_and_backend():
    suite = create_scipy_sampler_suite()

    assert suite.backend is SamplingBackend.SCIPY
    assert suite.metadata.backend is SamplingBackend.SCIPY
    assert suite.metadata.event_count["distribution"] == "poisson"
    assert suite.metadata.event_time["distribution"] == "uniform"
    assert suite.metadata.event_pitch["distribution"] == "normal"
    assert suite.metadata.drum_sound["distribution"] == "categorical"


def test_placeholder_distributions_fail_explicitly_if_called():
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        ScipyEventCountSampler().sample_event_counts(
            1,
            2,
            EventCountSamplingConfig(2.5, EventCountDistribution.BINOMIAL),
            random_seed=42,
        )
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        ScipyEventPitchSampler().sample_event_pitches(
            2,
            EventPitchSamplingConfig(
                60, 10, 48, 72, EventPitchDistribution.UNIFORM
            ),
            random_seed=42,
        )
