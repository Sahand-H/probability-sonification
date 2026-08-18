"""Streamlit presentation for the stochastic music experiment."""

import pretty_midi
import streamlit as st

from probability_sonification.sonification import render_audio
from probability_sonification.stochastic_music.distribution_catalog import (
    distribution_info,
)
from probability_sonification.stochastic_music.models import (
    DrumSoundSamplingConfig,
    EventCountDistribution,
    EventCountSamplingConfig,
    EventPitchDistribution,
    EventPitchSamplingConfig,
    EventTimeDistribution,
    EventTimeSamplingConfig,
    InstrumentDefinition,
    InstrumentSamplingOverride,
    SamplingBackend,
    SamplingProfile,
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
        "Ensemble",
        (
            _pitched_instrument("String Ensemble 1", "Ensemble"),
            _pitched_instrument("String Ensemble 2", "Ensemble"),
            _pitched_instrument("Synth Strings 1", "Ensemble"),
            _pitched_instrument("Synth Strings 2", "Ensemble"),
            _pitched_instrument("Choir Aahs", "Ensemble"),
            _pitched_instrument("Voice Oohs", "Ensemble"),
            _pitched_instrument("Synth Choir", "Ensemble"),
            _pitched_instrument("Orchestra Hit", "Ensemble"),
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
    (
        "Percussive",
        (
            _pitched_instrument("Woodblock", "Percussive"),
            _pitched_instrument("Taiko Drum", "Percussive"),
            _pitched_instrument("Melodic Tom", "Percussive"),
            _pitched_instrument("Synth Drum", "Percussive"),
        ),
    ),
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
DEFAULT_DRUM_SOUNDS = (36, 38, 42, 44, 46, 45, 48, 49, 51)
# Heuristic pop/rock-style defaults, not corpus-derived measurements. Hi-hat,
# kick, and snare form the repeating groove; toms and cymbals are rarer accents.
DEFAULT_DRUM_PROBABILITIES = (
    0.22,  # Bass Drum 1
    0.20,  # Acoustic Snare
    0.28,  # Closed Hi-Hat
    0.06,  # Pedal Hi-Hat
    0.08,  # Open Hi-Hat
    0.04,  # Low Tom
    0.04,  # Hi-Mid Tom
    0.04,  # Crash Cymbal 1
    0.04,  # Ride Cymbal 1
)


def _backend_label(backend: SamplingBackend) -> str:
    return {SamplingBackend.SCIPY: "SciPy"}[backend]


def _distribution_label(distribution: object) -> str:
    info = distribution_info(distribution)
    label = info.name.removesuffix(" distribution")
    return label if info.implemented else f"{label} (coming later)"


def _sampler_suite(backend: SamplingBackend):
    """Resolve the one suite selected for all sampling tasks."""

    if backend is SamplingBackend.SCIPY:
        return create_scipy_sampler_suite()
    raise ValueError(f"Unsupported sampling backend: {backend.value}")


def _deselect_instrument(instrument_name: str) -> None:
    """Clear one instrument's detailed-panel selection before rerendering."""

    st.session_state[f"stochastic-instrument-{instrument_name}"] = False


def _toggle_instrument(instrument_name: str) -> None:
    """Toggle an instrument button in the detailed family list."""

    state_key = f"stochastic-instrument-{instrument_name}"
    st.session_state[state_key] = not st.session_state.get(state_key, False)


def _toggle_guided_instrument(instrument_name: str) -> None:
    """Toggle an instrument button in the guided family browser."""

    state_key = f"guided-instrument-selected-{instrument_name}"
    st.session_state[state_key] = not st.session_state.get(state_key, False)


def _reset_guided_setup() -> None:
    """Clear guided-only state and return the flow to instrument selection."""

    for state_key in tuple(st.session_state):
        if state_key.startswith("guided-"):
            del st.session_state[state_key]


def _render_instrument_selection_styles() -> None:
    """Give selected instrument pills stronger contrast than Streamlit's default."""

    st.markdown(
        """
        <style>
        button[data-variant="pills"][aria-pressed="true"],
        [data-baseweb="tag"],
        .st-key-stochastic-selected-instrument-removals button,
        .st-key-guided-selected-instrument-removals button {
            background: light-dark(#fef3c7, #78350f) !important;
            border-color: light-dark(#d97706, #f59e0b) !important;
            color: light-dark(#78350f, #fffbeb) !important;
        }
        .st-key-stochastic-guided-setup
        [class*="st-key-guided-instrument-button-"] button[kind="primary"],
        [class*="st-key-stochastic-instrument-button-"] button[kind="primary"] {
            background: light-dark(#cffafe, #155e75) !important;
            border-color: light-dark(#0891b2, #22d3ee) !important;
            color: light-dark(#164e63, #ecfeff) !important;
        }
        .st-key-guided-start-over button {
            background: light-dark(#fee2e2, #7f1d1d) !important;
            border-color: light-dark(#ef4444, #f87171) !important;
            color: light-dark(#7f1d1d, #fef2f2) !important;
        }
        .st-key-guided-confirm-instruments button,
        .st-key-guided-sampling-next button,
        .st-key-guided-composition-confirm button,
        .st-key-guided-generate button {
            background: light-dark(#dcfce7, #14532d) !important;
            border-color: light-dark(#22c55e, #4ade80) !important;
            color: light-dark(#14532d, #f0fdf4) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _profile_from_widget_state(key_prefix: str) -> SamplingProfile:
    """Build a profile from widget state, using the implemented defaults if absent."""

    minimum_pitch, maximum_pitch = st.session_state.get(
        f"{key_prefix}-pitch-range", (0, 127)
    )
    return SamplingProfile(
        event_count=EventCountSamplingConfig(
            rate=float(st.session_state.get(f"{key_prefix}-event-rate", 2.5)),
            distribution=st.session_state.get(
                f"{key_prefix}-event-count-distribution",
                EventCountDistribution.POISSON,
            ),
        ),
        event_time=EventTimeSamplingConfig(
            distribution=st.session_state.get(
                f"{key_prefix}-event-time-distribution",
                EventTimeDistribution.UNIFORM,
            )
        ),
        event_pitch=EventPitchSamplingConfig(
            mean=float(st.session_state.get(f"{key_prefix}-pitch-mean", 60.0)),
            standard_deviation=float(
                st.session_state.get(f"{key_prefix}-pitch-standard-deviation", 10.0)
            ),
            minimum_pitch=int(minimum_pitch),
            maximum_pitch=int(maximum_pitch),
            distribution=st.session_state.get(
                f"{key_prefix}-event-pitch-distribution",
                EventPitchDistribution.NORMAL,
            ),
        ),
    )


def _write_profile_to_widget_state(key_prefix: str, profile: SamplingProfile) -> None:
    """Synchronize a completed guided profile with the detailed controls."""

    values = {
        "event-count-distribution": profile.event_count.distribution,
        "event-rate": profile.event_count.rate,
        "event-time-distribution": profile.event_time.distribution,
        "event-pitch-distribution": profile.event_pitch.distribution,
        "pitch-mean": profile.event_pitch.mean,
        "pitch-standard-deviation": profile.event_pitch.standard_deviation,
        "pitch-range": (
            profile.event_pitch.minimum_pitch,
            profile.event_pitch.maximum_pitch,
        ),
    }
    for suffix, value in values.items():
        st.session_state[f"{key_prefix}-{suffix}"] = value


def _render_guided_setup() -> None:
    """Render the sequential setup flow and generate from its final review step."""

    step = int(st.session_state.get("guided-setup-step", 1))
    draft = st.session_state.setdefault("guided-setup-draft", {})
    customize_sampling = bool(draft.get("customize_sampling"))
    visible_step = step if customize_sampling else {1: 1, 3: 2, 4: 3}.get(step, step)
    total_steps = 4 if customize_sampling else 3
    with st.container(border=True, key="stochastic-guided-setup"):
        heading_column, reset_column = st.columns([4, 1])
        heading_column.subheader("Guided setup")
        reset_column.button(
            "Start over",
            icon=":material/restart_alt:",
            key="guided-start-over",
            on_click=_reset_guided_setup,
            width="stretch",
        )
        st.caption(f"Step {visible_step} of {total_steps}")

        if step == 1:
            st.markdown("#### Choose instruments")
            st.caption(
                "Browse families from left to right. Click an instrument to select "
                "it; click it again to deselect it."
            )
            guided_defaults = set(draft.get("selected_names", DEFAULT_INSTRUMENTS))
            selected_names = []
            family_tabs = st.tabs([group_name for group_name, _ in INSTRUMENT_GROUPS])
            for family_tab, (_, instruments) in zip(
                family_tabs, INSTRUMENT_GROUPS, strict=True
            ):
                with family_tab:
                    with st.container(horizontal=True):
                        for instrument in instruments:
                            state_key = f"guided-instrument-selected-{instrument.name}"
                            if state_key not in st.session_state:
                                st.session_state[state_key] = (
                                    instrument.name in guided_defaults
                                )
                            is_selected = bool(st.session_state[state_key])
                            if is_selected:
                                selected_names.append(instrument.name)
                            st.button(
                                instrument.name,
                                type="primary" if is_selected else "secondary",
                                icon=":material/check:" if is_selected else None,
                                key=f"guided-instrument-button-{instrument.name}",
                                on_click=_toggle_guided_instrument,
                                args=(instrument.name,),
                            )
            if selected_names:
                st.caption(
                    f"{len(selected_names)} selected · " + " · ".join(selected_names)
                )
                st.caption("Deselect instruments")
                with st.container(
                    horizontal=True,
                    key="guided-selected-instrument-removals",
                ):
                    for instrument_name in selected_names:
                        st.button(
                            instrument_name,
                            icon=":material/close:",
                            key=f"guided-remove-instrument-{instrument_name}",
                            help=f"Deselect {instrument_name}",
                            on_click=_toggle_guided_instrument,
                            args=(instrument_name,),
                        )
            else:
                st.caption("No instruments selected.")
            customize = st.toggle(
                "Customize sampling per instrument",
                value=bool(draft.get("customize_sampling", False)),
                key="guided-customize-sampling",
            )
            confirmed = st.button(
                "Confirm instruments",
                type="primary",
                key="guided-confirm-instruments",
            )
            if confirmed:
                if not selected_names:
                    st.error("Select at least one instrument to continue.")
                else:
                    draft["selected_names"] = tuple(selected_names)
                    draft["customize_sampling"] = bool(customize)
                    draft["shared_profile"] = _profile_from_widget_state(
                        "stochastic-shared-sampling"
                    )
                    draft["sampling_profiles"] = {}
                    st.session_state["guided-sampling-index"] = 0
                    st.session_state["guided-setup-step"] = 2 if customize else 3
                    st.rerun()

        elif step == 2:
            st.markdown("#### Per-instrument sampling")
            selected_names = draft["selected_names"]
            sampling_index = min(
                int(st.session_state.get("guided-sampling-index", 0)),
                len(selected_names) - 1,
            )
            instrument_name = selected_names[sampling_index]
            st.caption(
                f"Instrument {sampling_index + 1} of {len(selected_names)}"
            )
            st.markdown(f"##### {instrument_name}")
            profile, profile_ready = _render_sampling_profile(
                f"guided-instrument-{instrument_name}",
                show_headings=False,
            )
            back_column, next_column = st.columns(2)
            if back_column.button("Back", key="guided-sampling-back"):
                if sampling_index > 0:
                    st.session_state["guided-sampling-index"] = sampling_index - 1
                else:
                    st.session_state["guided-setup-step"] = 1
                st.rerun()
            if next_column.button(
                "Confirm sampling",
                type="primary",
                disabled=not profile_ready,
                key="guided-sampling-next",
            ):
                sampling_profiles = draft.setdefault("sampling_profiles", {})
                sampling_profiles[instrument_name] = profile
                if sampling_index + 1 < len(selected_names):
                    st.session_state["guided-sampling-index"] = sampling_index + 1
                else:
                    draft["overrides"] = tuple(
                        InstrumentSamplingOverride(name, sampling_profiles[name])
                        for name in selected_names
                    )
                    st.session_state["guided-setup-step"] = 3
                st.rerun()

        elif step == 3:
            with st.form("guided-composition-form"):
                st.markdown("#### Composition")
                columns = st.columns(2)
                duration = columns[0].number_input(
                    "Composition duration (seconds)",
                    min_value=1.0,
                    max_value=300.0,
                    value=float(draft.get("duration", 60.0)),
                    step=1.0,
                    key="guided-composition-duration",
                )
                time_blocks = columns[1].number_input(
                    "Number of time blocks",
                    min_value=1,
                    max_value=60,
                    value=int(draft.get("time_blocks", 12)),
                    step=1,
                    key="guided-time-blocks",
                )
                note_duration = columns[0].number_input(
                    "Note duration (seconds)",
                    min_value=0.05,
                    max_value=20.0,
                    value=float(draft.get("note_duration", 2.0)),
                    step=0.05,
                    key="guided-note-duration",
                )
                velocity = columns[1].slider(
                    "Note velocity",
                    min_value=1,
                    max_value=127,
                    value=int(draft.get("velocity", 90)),
                    key="guided-note-velocity",
                )
                use_seed = st.toggle(
                    "Use reproducible seed",
                    value=bool(draft.get("use_seed", False)),
                    key="guided-use-seed",
                )
                seed = None
                if use_seed:
                    seed = int(
                        st.number_input(
                            "Random seed",
                            min_value=0,
                            max_value=4_294_967_295,
                            value=int(draft.get("random_seed", 42)),
                            step=1,
                            key="guided-random-seed",
                        )
                    )
                composition_confirmed = st.form_submit_button(
                    "Confirm composition",
                    type="primary",
                    key="guided-composition-confirm",
                )
            if st.button("Back", key="guided-composition-back"):
                st.session_state["guided-setup-step"] = (
                    2 if draft.get("customize_sampling") else 1
                )
                st.rerun()
            if composition_confirmed:
                draft.update(
                    duration=float(duration),
                    time_blocks=int(time_blocks),
                    note_duration=float(note_duration),
                    velocity=int(velocity),
                    use_seed=bool(use_seed),
                    random_seed=seed,
                )
                st.session_state["guided-setup-step"] = 4
                st.rerun()

        else:
            st.markdown("#### Review and generate")
            st.write("Instruments: " + ", ".join(draft["selected_names"]))
            st.write(
                f"Composition: {draft['duration']:g} seconds · "
                f"{draft['time_blocks']} blocks · notes {draft['note_duration']:g} seconds"
            )
            if st.button("Back", key="guided-review-back"):
                st.session_state["guided-setup-step"] = 3
                st.rerun()
            if st.button(
                "Generate music",
                type="primary",
                width="stretch",
                key="guided-generate",
            ):
                selected_instruments = tuple(
                    instrument
                    for instrument in AVAILABLE_INSTRUMENTS
                    if instrument.name in draft["selected_names"]
                )
                overrides = tuple(draft.get("overrides", ()))
                profile = draft["shared_profile"]
                guided_selected_names = set(draft["selected_names"])
                for instrument in AVAILABLE_INSTRUMENTS:
                    st.session_state[f"stochastic-instrument-{instrument.name}"] = (
                        instrument.name in guided_selected_names
                    )
                st.session_state["stochastic-customize-sampling"] = bool(
                    draft.get("customize_sampling")
                )
                st.session_state["stochastic-composition-duration"] = draft["duration"]
                st.session_state["stochastic-time-blocks"] = draft["time_blocks"]
                st.session_state["stochastic-note-duration"] = draft["note_duration"]
                st.session_state["stochastic-note-velocity"] = draft["velocity"]
                st.session_state["stochastic-use-seed"] = draft["use_seed"]
                if draft["random_seed"] is not None:
                    st.session_state["stochastic-random-seed"] = draft["random_seed"]
                _write_profile_to_widget_state("stochastic-shared-sampling", profile)
                for override in overrides:
                    st.session_state[
                        f"stochastic-use-shared-sampling-{override.instrument_name}"
                    ] = False
                    _write_profile_to_widget_state(
                        f"stochastic-instrument-sampling-{override.instrument_name}",
                        override.profile,
                    )
                config = StochasticMusicConfig(
                    selected_instruments=selected_instruments,
                    composition_duration=draft["duration"],
                    n_time_blocks=draft["time_blocks"],
                    note_duration=draft["note_duration"],
                    note_velocity=draft["velocity"],
                    sampling_backend=SamplingBackend.SCIPY,
                    random_seed=draft["random_seed"],
                    event_count_sampling=profile.event_count,
                    event_time_sampling=profile.event_time,
                    event_pitch_sampling=profile.event_pitch,
                    drum_sound_sampling=DrumSoundSamplingConfig(
                        sounds=DEFAULT_DRUM_SOUNDS,
                        probabilities=DEFAULT_DRUM_PROBABILITIES,
                    ),
                    instrument_sampling_overrides=overrides,
                )
                with st.spinner("Generating stochastic music..."):
                    result = generate_stochastic_music(
                        config, create_scipy_sampler_suite()
                    )
                    audio, used_fluidsynth = render_audio(result.midi)
                st.session_state["stochastic_music_result"] = result
                st.session_state["stochastic_music_audio"] = audio
                st.session_state["stochastic_music_used_fluidsynth"] = used_fluidsynth


def _render_sampling_profile(
    key_prefix: str,
    *,
    show_headings: bool = True,
) -> tuple[SamplingProfile, bool]:
    """Render one distribution profile and report whether it is executable."""

    if show_headings:
        st.markdown("**Event counts**")
    event_count_distribution = st.selectbox(
        "Event-count distribution",
        options=list(EventCountDistribution),
        format_func=_distribution_label,
        key=f"{key_prefix}-event-count-distribution",
    )
    event_rate = st.number_input(
        "Event rate",
        min_value=0.0,
        max_value=25.0,
        value=2.5,
        step=0.1,
        help="Expected musical events per instrument in each time block.",
        disabled=event_count_distribution is not EventCountDistribution.POISSON,
        key=f"{key_prefix}-event-rate",
    )

    if show_headings:
        st.markdown("**Event times**")
    event_time_distribution = st.selectbox(
        "Event-time distribution",
        options=list(EventTimeDistribution),
        format_func=_distribution_label,
        key=f"{key_prefix}-event-time-distribution",
    )
    if event_time_distribution is EventTimeDistribution.UNIFORM:
        st.caption("Uniform event times require no additional parameters.")

    if show_headings:
        st.markdown("**Event pitches**")
    event_pitch_distribution = st.selectbox(
        "Event-pitch distribution",
        options=list(EventPitchDistribution),
        format_func=_distribution_label,
        key=f"{key_prefix}-event-pitch-distribution",
    )
    pitch_placeholder_selected = (
        event_pitch_distribution is not EventPitchDistribution.NORMAL
    )
    pitch_columns = st.columns(2)
    pitch_mean = pitch_columns[0].number_input(
        "Mean MIDI pitch",
        min_value=0.0,
        max_value=127.0,
        value=60.0,
        step=1.0,
        disabled=pitch_placeholder_selected,
        key=f"{key_prefix}-pitch-mean",
    )
    pitch_standard_deviation = pitch_columns[1].number_input(
        "Pitch standard deviation",
        min_value=0.1,
        max_value=64.0,
        value=10.0,
        step=0.5,
        disabled=pitch_placeholder_selected,
        key=f"{key_prefix}-pitch-standard-deviation",
    )
    minimum_pitch, maximum_pitch = st.slider(
        "Allowed MIDI pitch range",
        min_value=0,
        max_value=127,
        value=(0, 127),
        disabled=pitch_placeholder_selected,
        key=f"{key_prefix}-pitch-range",
    )

    ready = (
        event_count_distribution is EventCountDistribution.POISSON
        and event_time_distribution is EventTimeDistribution.UNIFORM
        and event_pitch_distribution is EventPitchDistribution.NORMAL
    )
    if not ready:
        st.info(
            "This distribution is available as a structural placeholder. "
            "Its parameters and sampling behavior will be implemented next."
        )

    return (
        SamplingProfile(
            event_count=EventCountSamplingConfig(
                rate=float(event_rate),
                distribution=event_count_distribution,
            ),
            event_time=EventTimeSamplingConfig(
                distribution=event_time_distribution,
            ),
            event_pitch=EventPitchSamplingConfig(
                mean=float(pitch_mean),
                standard_deviation=float(pitch_standard_deviation),
                minimum_pitch=int(minimum_pitch),
                maximum_pitch=int(maximum_pitch),
                distribution=event_pitch_distribution,
            ),
        ),
        ready,
    )


def _render_distribution_entry(distribution: object) -> None:
    """Render one concise textbook-style distribution reference entry."""

    info = distribution_info(distribution)
    st.markdown(f"#### {info.name}")
    st.caption("Implemented" if info.implemented else "Coming later")
    st.latex(info.formula)
    st.write(info.purpose)
    st.write(info.description)
    st.markdown("**Parameters**")
    for symbol, meaning in info.parameters:
        st.markdown(f"- **{symbol}** — {meaning}")


def _render_sampling_guide(profile: SamplingProfile) -> None:
    """Explain the effective sampling stages for one profile."""

    count_tab, time_tab, pitch_tab, drum_tab = st.tabs(
        ["Event count", "Event time", "Event pitch", "Drum sound"]
    )
    with count_tab:
        _render_distribution_entry(profile.event_count.distribution)
    with time_tab:
        _render_distribution_entry(profile.event_time.distribution)
    with pitch_tab:
        _render_distribution_entry(profile.event_pitch.distribution)
    with drum_tab:
        st.markdown("#### Categorical distribution")
        st.caption("Implemented")
        st.latex(r"D \sim \operatorname{Categorical}(p_1, \ldots, p_k)")
        st.write("Selects the General MIDI drum note assigned to each drum event.")
        st.write(
            "Each configured sound has a non-negative probability, and all sound "
            "probabilities sum to one."
        )
        st.markdown("**Parameters**")
        st.markdown("- **soundₖ** — General MIDI note number for drum choice k.")
        st.markdown("- **pₖ** — Probability of selecting drum choice k.")


def render_stochastic_music_experiment() -> None:
    """Render controls and results for stochastic music generation."""

    st.title("Stochastic Music Generator")
    st.caption("Experiment 2")
    st.write(
        "Populate a matrix of musical events, sample when each event begins and "
        "which pitch it plays, then hear the resulting multi-instrument composition."
    )

    _render_guided_setup()

    with st.expander("Instruments", expanded=True):
        _render_instrument_selection_styles()
        st.caption(
            "Select at least one instrument. Their catalog order is preserved in "
            "plots and MIDI tracks."
        )
        st.info(
            "Percussion and drum support is a work in progress. "
            "Drum sounds and controls may change."
        )
        instrument_columns = st.columns(2)
        selected_instrument_list = []
        for group_index, (group_name, instruments) in enumerate(INSTRUMENT_GROUPS):
            # Keep the complete catalog visible while preserving family groupings.
            with instrument_columns[group_index % 2]:
                st.markdown(f"**{group_name}**")
                with st.container(horizontal=True):
                    for instrument in instruments:
                        instrument_key = f"stochastic-instrument-{instrument.name}"
                        if instrument_key not in st.session_state:
                            st.session_state[instrument_key] = (
                                instrument.name in DEFAULT_INSTRUMENTS
                            )
                        is_selected = bool(st.session_state[instrument_key])
                        if is_selected:
                            selected_instrument_list.append(instrument)
                        st.button(
                            instrument.name,
                            type="primary" if is_selected else "secondary",
                            icon=":material/check:" if is_selected else None,
                            key=f"stochastic-instrument-button-{instrument.name}",
                            on_click=_toggle_instrument,
                            args=(instrument.name,),
                        )
        selected_instruments = tuple(selected_instrument_list)
        if selected_instruments:
            st.caption(
                f"{len(selected_instruments)} selected · "
                + " · ".join(
                    instrument.name for instrument in selected_instruments
                )
            )
            st.caption("Deselect instruments")
            with st.container(
                horizontal=True,
                key="stochastic-selected-instrument-removals",
            ):
                for instrument in selected_instruments:
                    st.button(
                        instrument.name,
                        icon=":material/close:",
                        key=f"stochastic-remove-instrument-{instrument.name}",
                        help=f"Deselect {instrument.name}",
                        on_click=_deselect_instrument,
                        args=(instrument.name,),
                    )
        else:
            st.caption("No instruments selected.")
        customize_instrument_sampling = st.toggle(
            "Customize sampling per instrument",
            value=False,
            key="stochastic-customize-sampling",
            help="Override the shared count, time, and pitch profile for each instrument.",
        )

    with st.expander("Composition", expanded=True):
        composition_columns = st.columns(2)
        composition_duration = composition_columns[0].number_input(
            "Composition duration (seconds)",
            min_value=1.0,
            max_value=300.0,
            value=60.0,
            step=1.0,
            key="stochastic-composition-duration",
        )
        n_time_blocks = composition_columns[1].number_input(
            "Number of time blocks",
            min_value=1,
            max_value=60,
            value=12,
            step=1,
            key="stochastic-time-blocks",
        )
        note_duration = composition_columns[0].number_input(
            "Note duration (seconds)",
            min_value=0.05,
            max_value=20.0,
            value=2.0,
            step=0.05,
            key="stochastic-note-duration",
        )
        note_velocity = composition_columns[1].slider(
            "Note velocity",
            min_value=1,
            max_value=127,
            value=90,
            key="stochastic-note-velocity",
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

        st.markdown("### Shared profile")
        shared_sampling_profile, shared_profile_ready = _render_sampling_profile(
            "stochastic-shared-sampling"
        )

        instrument_sampling_overrides = []
        override_profiles_ready = True
        if customize_instrument_sampling and selected_instruments:
            st.markdown("### Per-instrument profiles")
            st.caption(
                "Each selected instrument starts with the current defaults and "
                "stores its own distribution assignments and parameters."
            )
            # All tabs are rendered so Streamlit retains each instrument's widget state.
            instrument_tabs = st.tabs(
                [instrument.name for instrument in selected_instruments]
            )
            for instrument_tab, instrument in zip(
                instrument_tabs, selected_instruments, strict=True
            ):
                with instrument_tab:
                    use_shared_profile = st.checkbox(
                        "Use shared sampling profile",
                        value=False,
                        key=f"stochastic-use-shared-sampling-{instrument.name}",
                    )
                    if use_shared_profile:
                        st.caption(
                            "This instrument inherits the shared count, time, and "
                            "pitch settings above."
                        )
                        continue
                    if instrument.is_drum:
                        st.caption(
                            "Pitch sampling is retained in the profile but drum notes "
                            "continue to use categorical drum-sound sampling."
                        )
                    profile, profile_ready = _render_sampling_profile(
                        f"stochastic-instrument-sampling-{instrument.name}",
                        show_headings=False,
                    )
                    instrument_sampling_overrides.append(
                        InstrumentSamplingOverride(instrument.name, profile)
                    )
                    override_profiles_ready = (
                        override_profiles_ready and profile_ready
                    )

        distributions_ready = shared_profile_ready and override_profiles_ready

        st.markdown("**Drum sounds**")
        st.caption(
            "Drum Kit events select from nine common kick, snare, hi-hat, tom, "
            "crash, and ride sounds. Weighted categorical probabilities favor "
            "kick, snare, and closed hi-hat."
        )
        st.caption(
            "Defaults — Closed Hi-Hat 28%, Bass Drum 22%, Acoustic Snare 20%, "
            "Open Hi-Hat 8%, Pedal Hi-Hat 6%, and 4% each for Low Tom, "
            "Hi-Mid Tom, Crash Cymbal, and Ride Cymbal. These are heuristic "
            "pop/rock-style weights, not measurements from a drum corpus."
        )

        with st.expander("How sampling works", expanded=False):
            guide_profiles = {"Shared profile": shared_sampling_profile}
            if customize_instrument_sampling:
                override_by_name = {
                    override.instrument_name: override.profile
                    for override in instrument_sampling_overrides
                }
                for instrument in selected_instruments:
                    guide_profiles[instrument.name] = override_by_name.get(
                        instrument.name, shared_sampling_profile
                    )
            guide_profile_name = st.selectbox(
                "Profile to explain",
                options=list(guide_profiles),
                key="stochastic-sampling-guide-profile",
            )
            _render_sampling_guide(guide_profiles[guide_profile_name])

    with st.expander("Reproducibility", expanded=False):
        use_reproducible_seed = st.toggle(
            "Use reproducible seed",
            value=False,
            key="stochastic-use-seed",
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
                    key="stochastic-random-seed",
                )
            )

    generate_preview = st.button(
        "Generate preview",
        type="primary",
        width="stretch",
        disabled=not distributions_ready,
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
                event_count_sampling=shared_sampling_profile.event_count,
                event_time_sampling=shared_sampling_profile.event_time,
                event_pitch_sampling=shared_sampling_profile.event_pitch,
                drum_sound_sampling=DrumSoundSamplingConfig(
                    sounds=DEFAULT_DRUM_SOUNDS,
                    probabilities=DEFAULT_DRUM_PROBABILITIES,
                ),
                instrument_sampling_overrides=tuple(instrument_sampling_overrides),
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

    with st.container(border=True, key="generated-section-summary"):
        st.header("Preview")
        metrics = st.columns(3)
        metrics[0].metric("Musical events", result.event_matrix.total_event_count)
        metrics[1].metric("Instruments", len(result.config.selected_instruments))
        metrics[2].metric("Duration", f"{result.config.composition_duration:g} s")

    with st.container(border=True, key="generated-section-visualizations"):
        st.subheader("Visualizations")
        st.altair_chart(event_matrix_plot(result.event_matrix), width="stretch")
        st.altair_chart(
            event_timeline_plot(result.events, result.config),
            width="stretch",
        )
        if any(not event.is_drum for event in result.events):
            pitched_instruments = tuple(
                instrument.name
                for instrument in result.config.selected_instruments
                if not instrument.is_drum
            )
            selected_pitch_instrument = st.selectbox(
                "Pitch distribution instrument",
                options=pitched_instruments,
                key="stochastic-pitch-distribution-instrument",
            )
            selected_pitch_config = result.config.sampling_profile_for(
                selected_pitch_instrument
            ).event_pitch
            st.altair_chart(
                event_pitch_distribution_plot(
                    result.events,
                    (selected_pitch_instrument,),
                    (
                        selected_pitch_config.minimum_pitch,
                        selected_pitch_config.maximum_pitch,
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

    with st.container(border=True, key="generated-section-audio"):
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
            for instrument in result.config.selected_instruments:
                profile = result.config.sampling_profile_for(instrument.name)
                pitch_label = (
                    "Categorical drums"
                    if instrument.is_drum
                    else profile.event_pitch.distribution.value.replace("_", " ").title()
                )
                st.write(
                    f"{instrument.name}: "
                    f"{profile.event_count.distribution.value.replace('_', ' ').title()} counts · "
                    f"{profile.event_time.distribution.value.replace('_', ' ').title()} timing · "
                    f"{pitch_label}"
                )
