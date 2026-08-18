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
    populate_event_matrix,
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
    "create_scipy_sampler_suite",
    "expand_event_matrix",
    "populate_event_matrix",
]
