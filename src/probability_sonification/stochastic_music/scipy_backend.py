"""SciPy implementations of the stochastic music sampling tasks."""

import numpy as np
from scipy import stats

from probability_sonification.stochastic_music.models import (
    DrumSoundSamplingConfig,
    EventCountSamplingConfig,
    EventPitchSamplingConfig,
    EventTimeSamplingConfig,
    SamplerMetadata,
    SamplingBackend,
)
from probability_sonification.stochastic_music.samplers import SamplerSuite


def _validate_sample_count(value: int, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative.")


class ScipyEventCountSampler:
    """Sample Poisson event counts for the event matrix."""

    def sample_event_counts(
        self,
        n_instruments: int,
        n_time_blocks: int,
        config: EventCountSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray:
        _validate_sample_count(n_instruments, "Number of instruments")
        _validate_sample_count(n_time_blocks, "Number of time blocks")

        # Rows represent instruments and columns represent time blocks.
        return stats.poisson.rvs(
            mu=config.rate,
            size=(n_instruments, n_time_blocks),
            random_state=random_seed,
        ).astype(int)


class ScipyEventTimeSampler:
    """Sample event start times uniformly within one time block."""

    def sample_event_times(
        self,
        n_events: int,
        block_start: float,
        block_end: float,
        config: EventTimeSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray:
        _validate_sample_count(n_events, "Number of events")
        if not np.isfinite(block_start) or not np.isfinite(block_end):
            raise ValueError("Time block bounds must be finite.")
        if block_end <= block_start:
            raise ValueError("Time block end must be greater than its start.")

        # Ordering is a pipeline concern; return the backend's raw draws here.
        # SciPy's Uniform uses a starting location plus the interval width.
        return np.asarray(
            stats.uniform.rvs(
                loc=block_start,
                scale=block_end - block_start,
                size=n_events,
                random_state=random_seed,
            ),
            dtype=float,
        )


class ScipyEventPitchSampler:
    """Sample Normal MIDI pitches and constrain them to configured limits."""

    def sample_event_pitches(
        self,
        n_events: int,
        config: EventPitchSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray:
        _validate_sample_count(n_events, "Number of events")
        sampled_pitches = stats.norm.rvs(
            loc=config.mean,
            scale=config.standard_deviation,
            size=n_events,
            random_state=random_seed,
        )

        # MIDI notes require integer pitches within the configured playable range.
        return np.clip(
            np.rint(sampled_pitches),
            config.minimum_pitch,
            config.maximum_pitch,
        ).astype(int)


class ScipyDrumSoundSampler:
    """Select General MIDI drum sounds from a categorical distribution."""

    def sample_drum_sounds(
        self,
        n_events: int,
        config: DrumSoundSamplingConfig,
        random_seed: int | None,
    ) -> np.ndarray:
        _validate_sample_count(n_events, "Number of drum events")
        if n_events == 0:
            return np.empty(0, dtype=int)

        # rv_discrete maps categorical probabilities to the configured MIDI sounds.
        distribution = stats.rv_discrete(
            values=(np.asarray(config.sounds), np.asarray(config.probabilities)),
        )
        return np.asarray(
            distribution.rvs(size=n_events, random_state=random_seed),
            dtype=int,
        )


def create_scipy_sampler_suite() -> SamplerSuite:
    """Create the task samplers and provenance for the SciPy backend."""

    backend = SamplingBackend.SCIPY

    # Metadata keeps the chosen probability models visible in saved results.
    return SamplerSuite(
        backend=backend,
        event_count_sampler=ScipyEventCountSampler(),
        event_time_sampler=ScipyEventTimeSampler(),
        event_pitch_sampler=ScipyEventPitchSampler(),
        drum_sound_sampler=ScipyDrumSoundSampler(),
        metadata=SamplerMetadata(
            backend=backend,
            event_count={"distribution": "poisson"},
            event_time={"distribution": "uniform"},
            event_pitch={"distribution": "normal"},
            drum_sound={"distribution": "categorical"},
        ),
    )
