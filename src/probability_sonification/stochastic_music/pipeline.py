"""Backend-neutral transformations for creating musical events."""

from collections import defaultdict

import numpy as np

from probability_sonification.stochastic_music.models import (
    EventMatrix,
    EventSlot,
    MusicalEvent,
    StochasticMusicResult,
    StochasticMusicConfig,
    TimedEvent,
)
from probability_sonification.stochastic_music.midi import build_midi, midi_to_bytes
from probability_sonification.stochastic_music.samplers import (
    DrumSoundSampler,
    EventCountSampler,
    EventPitchSampler,
    EventTimeSampler,
    SamplerSuite,
)


_EVENT_COUNT_TASK = 0
_EVENT_TIME_TASK = 1
_EVENT_PITCH_TASK = 2
_DRUM_SOUND_TASK = 3


def _derive_seed(
    random_seed: int | None,
    task: int,
    *coordinates: int,
) -> int | None:
    """Derive a stable seed without sharing random state between tasks."""

    if random_seed is None:
        return None

    seed_sequence = np.random.SeedSequence(
        random_seed,
        spawn_key=(task, *coordinates),
    )
    return int(seed_sequence.generate_state(1)[0])


def populate_event_matrix(
    config: StochasticMusicConfig,
    sampler: EventCountSampler,
) -> EventMatrix:
    """Populate event counts for every selected instrument and time block."""

    # Preserve the original bulk draw when every instrument shares one profile.
    # Overrides require separate rows so each sampler receives its effective config.
    if not config.instrument_sampling_overrides:
        counts = sampler.sample_event_counts(
            n_instruments=len(config.selected_instruments),
            n_time_blocks=config.n_time_blocks,
            config=config.event_count_sampling,
            random_seed=_derive_seed(config.random_seed, _EVENT_COUNT_TASK),
        )
    else:
        rows = []
        for instrument_index, instrument in enumerate(config.selected_instruments):
            profile = config.sampling_profile_for(instrument.name)
            row = np.asarray(
                sampler.sample_event_counts(
                    n_instruments=1,
                    n_time_blocks=config.n_time_blocks,
                    config=profile.event_count,
                    random_seed=_derive_seed(
                        config.random_seed, _EVENT_COUNT_TASK, instrument_index
                    ),
                )
            )
            if row.shape != (1, config.n_time_blocks):
                raise ValueError("Event count sampler returned an unexpected shape.")
            rows.append(row[0])
        counts = np.stack(rows)

    # EventMatrix provides the common validation boundary for every backend.
    return EventMatrix(
        counts=counts,
        instruments=tuple(instrument.name for instrument in config.selected_instruments),
    )


def expand_event_matrix(event_matrix: EventMatrix) -> tuple[EventSlot, ...]:
    """Expand each matrix count into individually addressable event slots."""

    slots = []
    for instrument_index, instrument_name in enumerate(event_matrix.instruments):
        for time_block_index in range(event_matrix.n_time_blocks):
            event_count = int(event_matrix.counts[instrument_index, time_block_index])
            for event_index in range(event_count):
                slots.append(
                    EventSlot(
                        instrument_index=instrument_index,
                        instrument_name=instrument_name,
                        time_block_index=time_block_index,
                        event_index_within_block=event_index,
                    )
                )
    return tuple(slots)


def assign_event_times(
    slots: tuple[EventSlot, ...],
    config: StochasticMusicConfig,
    sampler: EventTimeSampler,
) -> tuple[TimedEvent, ...]:
    """Sample, sort, and assign event start times within each time block."""

    grouped_slots: dict[tuple[int, int], list[EventSlot]] = defaultdict(list)
    for slot in slots:
        group_key = (slot.instrument_index, slot.time_block_index)
        grouped_slots[group_key].append(slot)

    time_block_duration = config.composition_duration / config.n_time_blocks
    timed_events = []

    for (instrument_index, time_block_index), group in grouped_slots.items():
        instrument = config.selected_instruments[instrument_index]
        profile = config.sampling_profile_for(instrument.name)
        block_start = time_block_index * time_block_duration
        block_end = block_start + time_block_duration
        sampled_times = np.asarray(
            sampler.sample_event_times(
                n_events=len(group),
                block_start=block_start,
                block_end=block_end,
                config=profile.event_time,
                random_seed=_derive_seed(
                    config.random_seed,
                    _EVENT_TIME_TASK,
                    instrument_index,
                    time_block_index,
                ),
            ),
            dtype=float,
        )

        if sampled_times.shape != (len(group),):
            raise ValueError("Event time sampler returned an unexpected shape.")
        if not np.all(np.isfinite(sampled_times)):
            raise ValueError("Event time sampler returned non-finite values.")
        if np.any(sampled_times < block_start) or np.any(sampled_times >= block_end):
            raise ValueError("Event time sampler returned values outside the time block.")

        # Sorting makes event indexes chronological regardless of backend behavior.
        for slot, start_time in zip(group, np.sort(sampled_times), strict=True):
            timed_events.append(TimedEvent(slot=slot, start_time=float(start_time)))

    return tuple(timed_events)


def assign_event_notes(
    timed_events: tuple[TimedEvent, ...],
    config: StochasticMusicConfig,
    pitch_sampler: EventPitchSampler,
    drum_sound_sampler: DrumSoundSampler,
) -> tuple[MusicalEvent, ...]:
    """Assign Normal pitches or categorical drum sounds to musical events."""

    pitched_indexes_by_instrument: dict[int, list[int]] = defaultdict(list)
    drum_indexes = []
    for index, timed_event in enumerate(timed_events):
        instrument = config.selected_instruments[timed_event.slot.instrument_index]
        if instrument.is_drum:
            drum_indexes.append(index)
        else:
            pitched_indexes_by_instrument[timed_event.slot.instrument_index].append(index)

    note_numbers = np.empty(len(timed_events), dtype=int)
    # Pitch groups must be sampled separately because their limits and models may differ.
    for instrument_index, pitched_indexes in pitched_indexes_by_instrument.items():
        instrument = config.selected_instruments[instrument_index]
        pitch_config = config.sampling_profile_for(instrument.name).event_pitch
        sampled_pitches = np.asarray(
            pitch_sampler.sample_event_pitches(
                n_events=len(pitched_indexes),
                config=pitch_config,
                random_seed=_derive_seed(
                    config.random_seed, _EVENT_PITCH_TASK, instrument_index
                ),
            )
        )
        if sampled_pitches.shape != (len(pitched_indexes),):
            raise ValueError("Event pitch sampler returned an unexpected shape.")
        if not np.issubdtype(sampled_pitches.dtype, np.integer):
            raise ValueError("Event pitch sampler must return integer MIDI pitches.")
        if np.any(sampled_pitches < pitch_config.minimum_pitch) or np.any(
            sampled_pitches > pitch_config.maximum_pitch
        ):
            raise ValueError("Event pitch sampler returned values outside the pitch limits.")
        note_numbers[pitched_indexes] = sampled_pitches

    sampled_drum_sounds = np.asarray(
        drum_sound_sampler.sample_drum_sounds(
            n_events=len(drum_indexes),
            config=config.drum_sound_sampling,
            random_seed=_derive_seed(config.random_seed, _DRUM_SOUND_TASK),
        )
    )
    if sampled_drum_sounds.shape != (len(drum_indexes),):
        raise ValueError("Drum sound sampler returned an unexpected shape.")
    if not np.issubdtype(sampled_drum_sounds.dtype, np.integer):
        raise ValueError("Drum sound sampler must return integer MIDI note numbers.")
    if not np.all(np.isin(sampled_drum_sounds, config.drum_sound_sampling.sounds)):
        raise ValueError("Drum sound sampler returned an unconfigured drum sound.")
    note_numbers[drum_indexes] = sampled_drum_sounds

    events = []
    for timed_event, note_number in zip(timed_events, note_numbers, strict=True):
        slot = timed_event.slot
        instrument = config.selected_instruments[slot.instrument_index]
        events.append(
            MusicalEvent(
                instrument_index=slot.instrument_index,
                instrument_name=slot.instrument_name,
                time_block_index=slot.time_block_index,
                event_index_within_block=slot.event_index_within_block,
                start_time=timed_event.start_time,
                duration=config.note_duration,
                # PrettyMIDI calls this value pitch even for categorical drum sounds.
                pitch=int(note_number),
                velocity=config.note_velocity,
                is_drum=instrument.is_drum,
            )
        )
    return tuple(events)


def generate_stochastic_music(
    config: StochasticMusicConfig,
    sampler_suite: SamplerSuite,
) -> StochasticMusicResult:
    """Run the complete backend-neutral stochastic music pipeline."""

    if sampler_suite.backend is not config.sampling_backend:
        raise ValueError("Sampler suite backend does not match the configuration.")
    if sampler_suite.metadata.backend is not sampler_suite.backend:
        raise ValueError("Sampler metadata backend does not match its suite.")

    event_matrix = populate_event_matrix(config, sampler_suite.event_count_sampler)
    event_slots = expand_event_matrix(event_matrix)
    timed_events = assign_event_times(
        event_slots,
        config,
        sampler_suite.event_time_sampler,
    )
    events = assign_event_notes(
        timed_events,
        config,
        sampler_suite.event_pitch_sampler,
        sampler_suite.drum_sound_sampler,
    )

    # Keep the MIDI object for visualization and bytes for direct download.
    midi = build_midi(events, config.selected_instruments)
    return StochasticMusicResult(
        config=config,
        event_matrix=event_matrix,
        events=events,
        midi=midi,
        midi_bytes=midi_to_bytes(midi),
        sampler_metadata=sampler_suite.metadata,
    )
