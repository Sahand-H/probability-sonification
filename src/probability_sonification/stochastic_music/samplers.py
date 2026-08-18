"""Backend-neutral interfaces for stochastic music sampling tasks."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from probability_sonification.stochastic_music.models import (
    DrumSoundSamplingConfig,
    EventCountSamplingConfig,
    EventPitchSamplingConfig,
    EventTimeSamplingConfig,
    SamplerMetadata,
    SamplingBackend,
)


class EventCountSampler(Protocol):
    """Populate the instrument-by-time-block event matrix."""

    def sample_event_counts(
        self,
        n_instruments: int,
        n_time_blocks: int,
        config: EventCountSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray: ...


class EventTimeSampler(Protocol):
    """Assign start times to musical events within one time block."""

    def sample_event_times(
        self,
        n_events: int,
        block_start: float,
        block_end: float,
        config: EventTimeSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray: ...


class EventPitchSampler(Protocol):
    """Assign MIDI pitches to musical events."""

    def sample_event_pitches(
        self,
        n_events: int,
        config: EventPitchSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray: ...


class DrumSoundSampler(Protocol):
    """Assign categorical General MIDI sounds to drum events."""

    def sample_drum_sounds(
        self,
        n_events: int,
        config: DrumSoundSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray: ...


@dataclass(frozen=True)
class SamplerSuite:
    """All task-specific samplers supplied by one backend."""

    # The backend is recorded here so the pipeline can check it against its config.
    backend: SamplingBackend
    event_count_sampler: EventCountSampler
    event_time_sampler: EventTimeSampler
    event_pitch_sampler: EventPitchSampler
    drum_sound_sampler: DrumSoundSampler
    metadata: SamplerMetadata
