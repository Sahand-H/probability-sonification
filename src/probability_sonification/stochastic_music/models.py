"""Domain models for the stochastic music experiment."""

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

import numpy as np
import pretty_midi


class SamplingBackend(str, Enum):
    """A supported implementation backend for every sampling task."""

    SCIPY = "scipy"


@dataclass(frozen=True)
class InstrumentDefinition:
    """General MIDI information needed to create an instrument track."""

    name: str
    family: str
    program: int
    is_drum: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.family.strip():
            raise ValueError("Instrument name and family must not be empty.")
        if not 0 <= self.program <= 127:
            raise ValueError("Instrument program must be between 0 and 127.")


@dataclass(frozen=True)
class EventCountSamplingConfig:
    # Expected musical events per instrument in each time block.
    rate: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.rate) or self.rate < 0:
            raise ValueError("Event rate must be a finite, non-negative number.")


@dataclass(frozen=True)
class EventTimeSamplingConfig:
    """Reserved for future event-time model parameters."""


@dataclass(frozen=True)
class EventPitchSamplingConfig:
    """Parameters for the initial Normal model of MIDI pitches."""

    mean: float
    standard_deviation: float
    minimum_pitch: int
    maximum_pitch: int

    def __post_init__(self) -> None:
        if not np.isfinite(self.mean):
            raise ValueError("Mean pitch must be finite.")
        if not np.isfinite(self.standard_deviation) or self.standard_deviation <= 0:
            raise ValueError("Pitch standard deviation must be positive and finite.")
        if not 0 <= self.minimum_pitch <= self.maximum_pitch <= 127:
            raise ValueError("Pitch limits must define a valid MIDI range from 0 to 127.")


@dataclass(frozen=True)
class DrumSoundSamplingConfig:
    """Categorical choices and probabilities for General MIDI drum sounds."""

    sounds: tuple[int, ...]
    probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.sounds:
            raise ValueError("At least one drum sound must be configured.")
        if len(self.sounds) != len(self.probabilities):
            raise ValueError("Drum sounds and probabilities must have equal lengths.")
        if len(set(self.sounds)) != len(self.sounds):
            raise ValueError("Drum sounds must be unique.")
        if any(not 0 <= sound <= 127 for sound in self.sounds):
            raise ValueError("Drum sounds must be valid MIDI note numbers.")
        if any(not np.isfinite(value) or value < 0 for value in self.probabilities):
            raise ValueError("Drum sound probabilities must be finite and non-negative.")
        if not np.isclose(sum(self.probabilities), 1.0):
            raise ValueError("Drum sound probabilities must sum to one.")


@dataclass(frozen=True)
class StochasticMusicConfig:
    """Musical structure and sampling choices for one generation run."""

    selected_instruments: tuple[InstrumentDefinition, ...]
    composition_duration: float
    n_time_blocks: int
    note_duration: float
    note_velocity: int
    sampling_backend: SamplingBackend
    random_seed: int | None
    event_count_sampling: EventCountSamplingConfig
    event_time_sampling: EventTimeSamplingConfig
    event_pitch_sampling: EventPitchSamplingConfig
    drum_sound_sampling: DrumSoundSamplingConfig

    def __post_init__(self) -> None:
        if not self.selected_instruments:
            raise ValueError("At least one instrument must be selected.")
        instrument_names = [instrument.name for instrument in self.selected_instruments]
        if len(set(instrument_names)) != len(instrument_names):
            raise ValueError("Selected instruments must be unique.")
        if not np.isfinite(self.composition_duration) or self.composition_duration <= 0:
            raise ValueError("Composition duration must be positive and finite.")
        if self.n_time_blocks < 1:
            raise ValueError("The number of time blocks must be at least one.")
        if not np.isfinite(self.note_duration) or self.note_duration <= 0:
            raise ValueError("Note duration must be positive and finite.")
        if not 1 <= self.note_velocity <= 127:
            raise ValueError("Note velocity must be between 1 and 127.")
        if self.random_seed is not None and self.random_seed < 0:
            raise ValueError("Random seed must be non-negative when provided.")


@dataclass(frozen=True)
class EventMatrix:
    """Musical event counts indexed by instrument and time block."""

    counts: np.ndarray
    instruments: tuple[str, ...]

    def __post_init__(self) -> None:
        counts = np.asarray(self.counts)
        if counts.ndim != 2:
            raise ValueError("Event matrix counts must be two-dimensional.")
        if counts.shape[0] != len(self.instruments):
            raise ValueError("Event matrix rows must match its instruments.")
        if counts.shape[1] < 1:
            raise ValueError("Event matrix must contain at least one time block.")
        if not np.issubdtype(counts.dtype, np.integer):
            raise ValueError("Event matrix counts must be integers.")
        if np.any(counts < 0):
            raise ValueError("Event matrix counts must be non-negative.")

        # Own a read-only copy so callers cannot change validated counts later.
        immutable_counts = counts.copy()
        immutable_counts.setflags(write=False)
        object.__setattr__(self, "counts", immutable_counts)

    @property
    def n_instruments(self) -> int:
        return self.counts.shape[0]

    @property
    def n_time_blocks(self) -> int:
        return self.counts.shape[1]

    @property
    def total_event_count(self) -> int:
        return int(self.counts.sum())


@dataclass(frozen=True)
class EventSlot:
    """An event-matrix entry expanded before timing and pitch are assigned."""

    instrument_index: int
    instrument_name: str
    time_block_index: int
    event_index_within_block: int


@dataclass(frozen=True)
class TimedEvent:
    """An event slot after a start time has been assigned."""

    slot: EventSlot
    start_time: float


@dataclass(frozen=True)
class MusicalEvent:
    """A complete event after time and pitch sampling."""

    instrument_index: int
    instrument_name: str
    time_block_index: int
    event_index_within_block: int
    start_time: float
    duration: float
    pitch: int
    velocity: int
    is_drum: bool = False

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration


@dataclass(frozen=True)
class SamplerMetadata:
    """Backend details and optional task-specific diagnostics."""

    backend: SamplingBackend
    event_count: Mapping[str, object]
    event_time: Mapping[str, object]
    event_pitch: Mapping[str, object]
    drum_sound: Mapping[str, object]


@dataclass(frozen=True)
class StochasticMusicResult:
    """Reusable outputs and provenance from one generation run."""

    config: StochasticMusicConfig
    event_matrix: EventMatrix
    events: tuple[MusicalEvent, ...]
    midi: pretty_midi.PrettyMIDI
    midi_bytes: bytes
    sampler_metadata: SamplerMetadata
