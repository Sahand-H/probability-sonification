"""Streamlit presentation for the stochastic music experiment."""

import pretty_midi
import streamlit as st

from probability_sonification.sonification import render_audio
from probability_sonification.stochastic_music.models import (
    DrumSoundSamplingConfig,
    EventCountSamplingConfig,
    EventPitchSamplingConfig,
    EventTimeSamplingConfig,
    InstrumentDefinition,
    SamplingBackend,
    StochasticMusicConfig,
)
from probability_sonification.stochastic_music.pipeline import (
    generate_stochastic_music,
)
from probability_sonification.stochastic_music.plots import (
    drum_sound_distribution_plot,
    event_matrix_plot,
    event_pitch_distribution_plot,
    event_timeline_plot,
    note_map_plot,
)
from probability_sonification.stochastic_music.scipy_backend import (
    create_scipy_sampler_suite,
)


def _pitched_instrument(name: str, family: str) -> InstrumentDefinition:
    """Create metadata for a standard General MIDI program instrument."""

    return InstrumentDefinition(
        name=name,
        family=family,
        program=pretty_midi.instrument_name_to_program(name),
    )


INSTRUMENT_GROUPS = (
    (
        "Piano",
        (
            _pitched_instrument("Acoustic Grand Piano", "Piano"),
            _pitched_instrument("Electric Piano 1", "Piano"),
        ),
    ),
    (
        "Chromatic percussion",
        (_pitched_instrument("Xylophone", "Chromatic percussion"),),
    ),
    ("Organ", (_pitched_instrument("Harmonica", "Organ"),)),
    (
        "Guitar",
        (
            _pitched_instrument("Acoustic Guitar (steel)", "Guitar"),
            _pitched_instrument("Electric Guitar (clean)", "Guitar"),
        ),
    ),
    ("Bass", (_pitched_instrument("Electric Bass (pick)", "Bass"),)),
    (
        "Solo strings",
        (
            _pitched_instrument("Violin", "Solo strings"),
            _pitched_instrument("Cello", "Solo strings"),
        ),
    ),
    (
        "Brass",
        (
            _pitched_instrument("Trumpet", "Brass"),
            _pitched_instrument("Trombone", "Brass"),
            _pitched_instrument("French Horn", "Brass"),
        ),
    ),
    (
        "Reed",
        (
            _pitched_instrument("Alto Sax", "Reed"),
            _pitched_instrument("Clarinet", "Reed"),
        ),
    ),
    (
        "Pipe",
        (
            _pitched_instrument("Flute", "Pipe"),
            _pitched_instrument("Recorder", "Pipe"),
        ),
    ),
    ("Percussive", (_pitched_instrument("Synth Drum", "Percussive"),)),
    (
        "Percussion and drums",
        (InstrumentDefinition("Drum Kit", "Percussion and drums", 0, is_drum=True),),
    ),
)
AVAILABLE_INSTRUMENTS = tuple(
    instrument
    for _, instruments in INSTRUMENT_GROUPS
    for instrument in instruments
)
DEFAULT_INSTRUMENTS = {
    "Acoustic Grand Piano",
    "Violin",
    "Cello",
    "Flute",
}
DEFAULT_DRUM_SOUNDS = (36, 38, 42, 46, 49)
DEFAULT_DRUM_PROBABILITIES = (0.2, 0.2, 0.2, 0.2, 0.2)


def _backend_label(backend: SamplingBackend) -> str:
    return {SamplingBackend.SCIPY: "SciPy"}[backend]


def _sampler_suite(backend: SamplingBackend):
    """Resolve the one suite selected for all sampling tasks."""

    if backend is SamplingBackend.SCIPY:
        return create_scipy_sampler_suite()
    raise ValueError(f"Unsupported sampling backend: {backend.value}")


def render_stochastic_music_experiment() -> None:
    """Render controls and results for stochastic music generation."""

    st.title("Stochastic Music Generator")
    st.write(
        "Populate a matrix of musical events, sample when each event begins and "
        "which pitch it plays, then hear the resulting multi-instrument composition."
    )

    with st.expander("Instruments", expanded=True):
        st.caption("Select at least one instrument. Their order is preserved in the plots and MIDI tracks.")
        st.info(
            "Percussion and drum support is a work in progress. "
            "Drum sounds and controls may change."
        )
        instrument_columns = st.columns(2)
        selected_instruments = []
        for group_index, (group_name, instruments) in enumerate(INSTRUMENT_GROUPS):
            # Keep related General MIDI instruments together under a visible heading.
            with instrument_columns[group_index % 2]:
                st.markdown(f"**{group_name}**")
                for instrument in instruments:
                    if st.checkbox(
                        instrument.name,
                        value=instrument.name in DEFAULT_INSTRUMENTS,
                        key=f"stochastic-instrument-{instrument.name}",
                    ):
                        selected_instruments.append(instrument)
        selected_instruments = tuple(selected_instruments)

    with st.expander("Composition", expanded=True):
        composition_columns = st.columns(2)
        composition_duration = composition_columns[0].number_input(
            "Composition duration (seconds)",
            min_value=1.0,
            max_value=300.0,
            value=60.0,
            step=1.0,
        )
        n_time_blocks = composition_columns[1].number_input(
            "Number of time blocks",
            min_value=1,
            max_value=60,
            value=12,
            step=1,
        )
        note_duration = composition_columns[0].number_input(
            "Note duration (seconds)",
            min_value=0.05,
            max_value=20.0,
            value=2.0,
            step=0.05,
        )
        note_velocity = composition_columns[1].slider(
            "Note velocity",
            min_value=1,
            max_value=127,
            value=90,
        )
        st.caption(
            "Composition duration limits when notes may start; notes may finish after it."
        )

    with st.expander("Sampling", expanded=True):
        sampling_backend = st.selectbox(
            "Sampling backend",
            options=list(SamplingBackend),
            format_func=_backend_label,
        )
        st.caption("The selected backend is used for event counts, times, and pitches.")

        st.markdown("**Event counts**")
        event_rate = st.number_input(
            "Event rate",
            min_value=0.0,
            max_value=25.0,
            value=2.5,
            step=0.1,
            help="Expected musical events per instrument in each time block.",
        )

        st.markdown("**Event times**")
        st.caption("Event start times are sampled uniformly within their assigned time block.")

        st.markdown("**Event pitches**")
        pitch_columns = st.columns(2)
        pitch_mean = pitch_columns[0].number_input(
            "Mean MIDI pitch",
            min_value=0.0,
            max_value=127.0,
            value=60.0,
            step=1.0,
        )
        pitch_standard_deviation = pitch_columns[1].number_input(
            "Pitch standard deviation",
            min_value=0.1,
            max_value=64.0,
            value=10.0,
            step=0.5,
        )
        minimum_pitch, maximum_pitch = st.slider(
            "Allowed MIDI pitch range",
            min_value=0,
            max_value=127,
            value=(0, 127),
        )

        st.markdown("**Drum sounds**")
        st.caption(
            "Drum Kit events select Bass Drum, Snare, Closed Hi-Hat, "
            "Open Hi-Hat, or Crash Cymbal with equal categorical probabilities."
        )

    with st.expander("Reproducibility", expanded=False):
        use_reproducible_seed = st.toggle(
            "Use reproducible seed",
            value=False,
        )
        random_seed = None
        if use_reproducible_seed:
            random_seed = int(
                st.number_input(
                    "Random seed",
                    min_value=0,
                    max_value=4_294_967_295,
                    value=42,
                    step=1,
                )
            )

    generate_preview = st.button(
        "Generate preview",
        type="primary",
        width="stretch",
    )
    if generate_preview:
        if not selected_instruments:
            st.error("Select at least one instrument before generating a preview.")
        else:
            config = StochasticMusicConfig(
                selected_instruments=selected_instruments,
                composition_duration=float(composition_duration),
                n_time_blocks=int(n_time_blocks),
                note_duration=float(note_duration),
                note_velocity=int(note_velocity),
                sampling_backend=sampling_backend,
                random_seed=random_seed,
                event_count_sampling=EventCountSamplingConfig(rate=float(event_rate)),
                event_time_sampling=EventTimeSamplingConfig(),
                event_pitch_sampling=EventPitchSamplingConfig(
                    mean=float(pitch_mean),
                    standard_deviation=float(pitch_standard_deviation),
                    minimum_pitch=int(minimum_pitch),
                    maximum_pitch=int(maximum_pitch),
                ),
                drum_sound_sampling=DrumSoundSamplingConfig(
                    sounds=DEFAULT_DRUM_SOUNDS,
                    probabilities=DEFAULT_DRUM_PROBABILITIES,
                ),
            )
            with st.spinner("Generating stochastic music..."):
                result = generate_stochastic_music(config, _sampler_suite(sampling_backend))
                audio, used_fluidsynth = render_audio(result.midi)

            # Preserve the preview while other controls cause Streamlit reruns.
            st.session_state["stochastic_music_result"] = result
            st.session_state["stochastic_music_audio"] = audio
            st.session_state["stochastic_music_used_fluidsynth"] = used_fluidsynth

    result = st.session_state.get("stochastic_music_result")
    if result is None:
        return

    st.header("Preview")
    metrics = st.columns(3)
    metrics[0].metric("Musical events", result.event_matrix.total_event_count)
    metrics[1].metric("Instruments", len(result.config.selected_instruments))
    metrics[2].metric("Duration", f"{result.config.composition_duration:g} s")

    st.altair_chart(event_matrix_plot(result.event_matrix), width="stretch")
    st.altair_chart(
        event_timeline_plot(result.events, result.config),
        width="stretch",
    )
    if any(not event.is_drum for event in result.events):
        st.altair_chart(
            event_pitch_distribution_plot(
                result.events,
                tuple(
                    instrument.name
                    for instrument in result.config.selected_instruments
                    if not instrument.is_drum
                ),
            ),
            width="stretch",
        )
    if any(event.is_drum for event in result.events):
        st.altair_chart(
            drum_sound_distribution_plot(
                result.events,
                tuple(
                    instrument.name
                    for instrument in result.config.selected_instruments
                    if instrument.is_drum
                ),
            ),
            width="stretch",
        )
    st.altair_chart(
        note_map_plot(
            result.events,
            tuple(instrument.name for instrument in result.config.selected_instruments),
        ),
        width="stretch",
    )

    st.subheader("Audio preview")
    st.audio(st.session_state["stochastic_music_audio"], format="audio/wav")
    st.download_button(
        "Download MIDI",
        data=result.midi_bytes,
        file_name="stochastic-music.mid",
        mime="audio/midi",
        width="stretch",
    )
    if not st.session_state["stochastic_music_used_fluidsynth"]:
        st.warning(
            "FluidSynth is unavailable, so this is a sine-wave preview. "
            "The MIDI download still contains the selected instruments."
        )

    with st.expander("Sampling summary"):
        st.write(f"Backend: {_backend_label(result.sampler_metadata.backend)}")
        st.write(
            "Event counts: Poisson · Event times: Uniform · Event pitches: Normal · "
            "Drum sounds: Categorical"
        )
