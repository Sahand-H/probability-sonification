"""Core types and sampling interfaces for stochastic music generation."""

from probability_sonification.stochastic_music.models import (
    EventCountSamplingConfig,
    EventMatrix,
    EventPitchSamplingConfig,
    EventSlot,
    EventTimeSamplingConfig,
    MusicalEvent,
    SamplerMetadata,
    SamplingBackend,
    StochasticMusicConfig,
    StochasticMusicResult,
    TimedEvent,
)
from probability_sonification.stochastic_music.pipeline import (
    assign_event_pitches,
    assign_event_times,
    expand_event_matrix,
    generate_stochastic_music,
    populate_event_matrix,
)
from probability_sonification.stochastic_music.midi import build_midi, midi_to_bytes
from probability_sonification.stochastic_music.plots import (
    event_matrix_plot,
    event_pitch_distribution_plot,
    event_timeline_plot,
    note_map_plot,
)
from probability_sonification.stochastic_music.samplers import (
    EventCountSampler,
    EventPitchSampler,
    EventTimeSampler,
    SamplerSuite,
)
from probability_sonification.stochastic_music.scipy_backend import (
    ScipyEventCountSampler,
    ScipyEventPitchSampler,
    ScipyEventTimeSampler,
    create_scipy_sampler_suite,
)

__all__ = [
    "EventCountSampler",
    "EventCountSamplingConfig",
    "EventMatrix",
    "EventPitchSampler",
    "EventPitchSamplingConfig",
    "EventSlot",
    "EventTimeSampler",
    "EventTimeSamplingConfig",
    "MusicalEvent",
    "SamplerMetadata",
    "SamplerSuite",
    "SamplingBackend",
    "ScipyEventCountSampler",
    "ScipyEventPitchSampler",
    "ScipyEventTimeSampler",
    "StochasticMusicConfig",
    "StochasticMusicResult",
    "TimedEvent",
    "assign_event_pitches",
    "assign_event_times",
    "build_midi",
    "create_scipy_sampler_suite",
    "event_matrix_plot",
    "event_pitch_distribution_plot",
    "event_timeline_plot",
    "expand_event_matrix",
    "generate_stochastic_music",
    "midi_to_bytes",
    "note_map_plot",
    "populate_event_matrix",
]
