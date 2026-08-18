from dataclasses import replace

import numpy as np
import pytest

from probability_sonification.stochastic_music import (
    DrumSoundSamplingConfig,
    EventCountSamplingConfig,
    EventMatrix,
    EventPitchSamplingConfig,
    EventTimeSamplingConfig,
    InstrumentDefinition,
    InstrumentSamplingOverride,
    SamplingProfile,
    SamplingBackend,
    StochasticMusicConfig,
    assign_event_notes,
    assign_event_times,
    expand_event_matrix,
    populate_event_matrix,
)


def make_config(random_seed=42) -> StochasticMusicConfig:
    return StochasticMusicConfig(
        selected_instruments=(
            InstrumentDefinition("Piano", "Piano", 0),
            InstrumentDefinition("Violin", "Solo strings", 40),
        ),
        composition_duration=20,
        n_time_blocks=2,
        note_duration=2,
        note_velocity=90,
        sampling_backend=SamplingBackend.SCIPY,
        random_seed=random_seed,
        event_count_sampling=EventCountSamplingConfig(rate=2.5),
        event_time_sampling=EventTimeSamplingConfig(),
        event_pitch_sampling=EventPitchSamplingConfig(60, 10, 48, 72),
        drum_sound_sampling=DrumSoundSamplingConfig((36, 38), (0.5, 0.5)),
    )


class RecordingCountSampler:
    def __init__(self):
        self.seed = None

    def sample_event_counts(self, n_instruments, n_time_blocks, config, random_seed):
        self.seed = random_seed
        return np.array([[2, 0], [1, 1]])


class ReverseTimeSampler:
    def __init__(self):
        self.seeds = []

    def sample_event_times(
        self, n_events, block_start, block_end, config, random_seed
    ):
        self.seeds.append(random_seed)
        # Deliberately return reverse order so the pipeline must sort the values.
        if n_events == 1:
            return np.array([(block_start + block_end) / 2])
        return np.linspace(block_end - 1, block_start + 1, n_events)


class FixedPitchSampler:
    def __init__(self):
        self.seed = None

    def sample_event_pitches(self, n_events, config, random_seed):
        self.seed = random_seed
        return np.arange(60, 60 + n_events, dtype=int)


class FixedDrumSoundSampler:
    def __init__(self):
        self.seed = None

    def sample_drum_sounds(self, n_events, config, random_seed):
        self.seed = random_seed
        return np.full(n_events, 38, dtype=int)


def test_populate_and_expand_event_matrix():
    config = make_config()
    sampler = RecordingCountSampler()

    matrix = populate_event_matrix(config, sampler)
    slots = expand_event_matrix(matrix)

    assert matrix.total_event_count == 4
    assert len(slots) == 4
    assert [slot.instrument_name for slot in slots] == [
        "Piano",
        "Piano",
        "Violin",
        "Violin",
    ]
    assert [slot.event_index_within_block for slot in slots[:2]] == [0, 1]
    assert sampler.seed is not None


def test_populate_event_matrix_resolves_per_instrument_profiles():
    shared = make_config()
    violin_profile = SamplingProfile(
        event_count=EventCountSamplingConfig(rate=7.0),
        event_time=shared.event_time_sampling,
        event_pitch=shared.event_pitch_sampling,
    )
    config = replace(
        shared,
        instrument_sampling_overrides=(
            InstrumentSamplingOverride("Violin", violin_profile),
        ),
    )

    class RateRecordingSampler:
        def __init__(self):
            self.rates = []

        def sample_event_counts(
            self, n_instruments, n_time_blocks, config, random_seed
        ):
            self.rates.append(config.rate)
            return np.full((n_instruments, n_time_blocks), int(config.rate))

    sampler = RateRecordingSampler()
    matrix = populate_event_matrix(config, sampler)

    assert sampler.rates == [2.5, 7.0]
    assert matrix.counts.tolist() == [[2, 2], [7, 7]]


def test_assign_event_times_sorts_each_instrument_and_block_group():
    config = make_config()
    slots = expand_event_matrix(
        EventMatrix(
            np.array([[2, 0], [1, 1]]),
            tuple(instrument.name for instrument in config.selected_instruments),
        )
    )
    sampler = ReverseTimeSampler()

    timed_events = assign_event_times(slots, config, sampler)

    assert [event.start_time for event in timed_events[:2]] == [1.0, 9.0]
    assert timed_events[2].start_time == 5.0
    assert timed_events[3].start_time == 15.0
    assert len(set(sampler.seeds)) == 3


def test_assign_event_notes_creates_complete_pitched_events():
    config = make_config()
    slots = expand_event_matrix(EventMatrix(np.array([[2, 0]]), ("Piano",)))
    timed_events = assign_event_times(slots, config, ReverseTimeSampler())
    sampler = FixedPitchSampler()

    events = assign_event_notes(
        timed_events,
        config,
        sampler,
        FixedDrumSoundSampler(),
    )

    assert [event.pitch for event in events] == [60, 61]
    assert all(event.duration == 2 for event in events)
    assert all(event.velocity == 90 for event in events)
    assert events[1].end_time == 11.0
    assert sampler.seed is not None


def test_task_seeds_are_repeatable_and_independent():
    config = make_config()
    count_sampler = RecordingCountSampler()
    populate_event_matrix(config, count_sampler)

    slots = expand_event_matrix(EventMatrix(np.array([[1, 0]]), ("Piano",)))
    time_sampler = ReverseTimeSampler()
    timed_events = assign_event_times(slots, config, time_sampler)
    pitch_sampler = FixedPitchSampler()
    drum_sampler = FixedDrumSoundSampler()
    assign_event_notes(timed_events, config, pitch_sampler, drum_sampler)

    first_seeds = (
        count_sampler.seed,
        time_sampler.seeds[0],
        pitch_sampler.seed,
        drum_sampler.seed,
    )

    second_count = RecordingCountSampler()
    populate_event_matrix(config, second_count)
    second_time = ReverseTimeSampler()
    second_timed = assign_event_times(slots, config, second_time)
    second_pitch = FixedPitchSampler()
    second_drum = FixedDrumSoundSampler()
    assign_event_notes(second_timed, config, second_pitch, second_drum)

    assert first_seeds == (
        second_count.seed,
        second_time.seeds[0],
        second_pitch.seed,
        second_drum.seed,
    )
    assert len(set(first_seeds)) == 4


def test_pipeline_passes_none_seed_when_reproducibility_is_disabled():
    config = make_config(random_seed=None)
    sampler = RecordingCountSampler()

    populate_event_matrix(config, sampler)

    assert sampler.seed is None


def test_assign_event_times_rejects_values_outside_the_block():
    class InvalidTimeSampler:
        def sample_event_times(self, n_events, block_start, block_end, config, random_seed):
            return np.full(n_events, block_end)

    config = make_config()
    slots = expand_event_matrix(EventMatrix(np.array([[1, 0]]), ("Piano",)))

    with pytest.raises(ValueError, match="outside the time block"):
        assign_event_times(slots, config, InvalidTimeSampler())


def test_assign_event_notes_rejects_non_integer_pitches():
    class InvalidPitchSampler:
        def sample_event_pitches(self, n_events, config, random_seed):
            return np.full(n_events, 60.5)

    config = make_config()
    slots = expand_event_matrix(EventMatrix(np.array([[1, 0]]), ("Piano",)))
    timed_events = assign_event_times(slots, config, ReverseTimeSampler())

    with pytest.raises(ValueError, match="integer MIDI pitches"):
        assign_event_notes(
            timed_events,
            config,
            InvalidPitchSampler(),
            FixedDrumSoundSampler(),
        )


def test_assign_event_notes_uses_categorical_sampler_for_drum_events():
    config = replace(
        make_config(),
        selected_instruments=(
            InstrumentDefinition("Piano", "Piano", 0),
            InstrumentDefinition("Drum Kit", "Percussion and drums", 0, is_drum=True),
        ),
    )
    slots = expand_event_matrix(
        EventMatrix(np.array([[1, 0], [1, 0]]), ("Piano", "Drum Kit"))
    )
    timed_events = assign_event_times(slots, config, ReverseTimeSampler())

    events = assign_event_notes(
        timed_events,
        config,
        FixedPitchSampler(),
        FixedDrumSoundSampler(),
    )

    assert events[0].pitch == 60
    assert not events[0].is_drum
    assert events[1].pitch == 38
    assert events[1].is_drum
