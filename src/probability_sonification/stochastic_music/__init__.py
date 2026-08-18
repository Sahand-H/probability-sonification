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
    "create_scipy_sampler_suite",
]
