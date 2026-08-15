import altair as alt
import numpy as np
import streamlit as st

from probability_sonification.distributions import (
    DISTRIBUTIONS,
    sample_distribution,
)
from probability_sonification.sonification import MappingConfig, render_audio, sonify


INSTRUMENTS = [
    "Acoustic Grand Piano",
    "Acoustic Guitar (steel)",
    "Electric Guitar (clean)",
    "Violin",
    "Cello",
    "Flute",
    "Synth Drum",
]

st.set_page_config(
    page_title="Probability Sonification",
    page_icon="♫",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root { --rust-accent: #cf704c; --sage-accent: #82a58f; }
    .stApp {
        background: var(--background-color);
        color: var(--text-color);
    }
    .block-container { max-width: 1180px; padding-top: 3rem; }
    h1, h2, h3 { letter-spacing: -0.025em; }
    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
        padding: .75rem;
    }
    div[data-testid="stExpander"] {
        border-color: color-mix(in srgb, var(--text-color) 18%, transparent);
        background: var(--secondary-background-color);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def parameter_controls(side: str, distribution_name: str) -> dict[str, float | int]:
    values = {}
    for name, parameter in DISTRIBUTIONS[distribution_name].parameters.items():
        key = f"{side}-{distribution_name}-{name}"
        if parameter.integer:
            values[name] = st.number_input(
                parameter.label,
                min_value=int(parameter.minimum) if parameter.minimum is not None else None,
                max_value=int(parameter.maximum) if parameter.maximum is not None else None,
                value=int(parameter.default),
                step=int(parameter.step),
                key=key,
            )
        else:
            values[name] = st.number_input(
                parameter.label,
                min_value=float(parameter.minimum) if parameter.minimum is not None else None,
                max_value=float(parameter.maximum) if parameter.maximum is not None else None,
                value=float(parameter.default),
                step=float(parameter.step),
                key=key,
            )
    return values


def distribution_chart(samples: np.ndarray, name: str, discrete: bool, color: str):
    if discrete:
        sample_values, counts = np.unique(samples, return_counts=True)
        probabilities = counts / counts.sum()
        chart_data = [
            {
                "Sample value": int(value),
                "Probability": float(probability),
                "Count": int(count),
            }
            for value, probability, count in zip(
                sample_values, probabilities, counts, strict=True
            )
        ]
        chart = (
            alt.Chart(alt.Data(values=chart_data))
            .mark_bar(color=color, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X(
                    "Sample value:O",
                    title="Sample value",
                    sort="ascending",
                    axis=alt.Axis(labelAngle=0),
                ),
                y=alt.Y("Probability:Q", title="Probability"),
                tooltip=[
                    alt.Tooltip("Sample value:O"),
                    alt.Tooltip("Count:Q"),
                    alt.Tooltip("Probability:Q", format=".3f"),
                ],
            )
        )
    else:
        chart = (
            alt.Chart(alt.Data(values=[{"Sample value": float(v)} for v in samples]))
            .transform_density("Sample value", as_=["Sample value", "Density"])
            .mark_area(color=color, opacity=0.75, line=True)
            .encode(
                x=alt.X("Sample value:Q", title="Sample value"),
                y=alt.Y("Density:Q", title="Density"),
                tooltip=[alt.Tooltip("Sample value:Q", format=".3f"), alt.Tooltip("Density:Q", format=".3f")],
            )
        )
    return chart.properties(title=f"{name} sample", height=260).configure_view(strokeOpacity=0)


def controls(side: str, default_distribution: str, default_instrument: str):
    distribution_names = sorted(DISTRIBUTIONS)
    distribution_name = st.selectbox(
        "Distribution",
        distribution_names,
        index=distribution_names.index(default_distribution),
        key=f"{side}-distribution",
    )
    parameters = parameter_controls(side, distribution_name)
    instrument = st.selectbox(
        "Instrument", INSTRUMENTS, index=INSTRUMENTS.index(default_instrument), key=f"{side}-instrument"
    )
    return distribution_name, parameters, instrument


def present_result(
    side: str,
    settings,
    color: str,
    config: MappingConfig,
    sample_size: int,
    seed: int,
):
    name, parameters, instrument = settings
    samples = sample_distribution(name, parameters, sample_size, seed)
    result = sonify(samples, instrument, config)
    wav, used_fluidsynth = render_audio(result.midi)

    st.altair_chart(
        distribution_chart(samples, name, DISTRIBUTIONS[name].discrete, color),
        width="stretch",
    )
    metric_columns = st.columns(3)
    metric_columns[0].metric("Minimum", f"{np.min(samples):.2f}")
    metric_columns[1].metric("Mean", f"{np.mean(samples):.2f}")
    metric_columns[2].metric("Maximum", f"{np.max(samples):.2f}")
    st.audio(wav, format="audio/wav")
    st.download_button(
        "Download MIDI",
        result.midi_bytes,
        file_name=f"{side.lower()}-{name.lower()}-{instrument.lower().replace(' ', '-')}.mid",
        mime="audio/midi",
        key=f"{side}-download",
        width="stretch",
    )
    if not used_fluidsynth:
        st.warning("FluidSynth is unavailable, so this is a simple sine-wave preview. The MIDI file still contains the selected instrument.")
    return result


st.title("Basic sonification of probability distributions.")
st.write(
    "Choose two distributions, draw samples, and compare the patterns after mapping every value to pitch. Both sides use the same scale, so equal values produce equal notes."
)

with st.expander("How the sonification works"):
    st.markdown(
        """
        Each sampled value becomes one MIDI note. Larger values become higher pitches,
        while sample order determines note order. Timing, duration, velocity, and pitch
        limits are held constant so the comparison focuses on the distributions. The
        instrument changes timbre, not the mapping.
        """
    )

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Distribution A")
    left_settings = controls("A", "Uniform", "Acoustic Grand Piano")
with right:
    st.subheader("Distribution B")
    right_settings = controls("B", "Poisson", "Violin")

with st.expander("Shared sampling", expanded=True):
    st.caption("Both distributions use the same sample size and random seed.")
    sample_size = st.number_input(
        "Sample size", min_value=8, max_value=500, value=50, step=1
    )
    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=2_147_483_647,
        value=42,
        step=1,
    )

with st.expander("Note articulation", expanded=True):
    st.caption(
        "Changes how long each note is held without changing the spacing between notes."
    )
    articulation = st.slider(
        "Note length",
        min_value=20,
        max_value=120,
        value=80,
        step=5,
        format="%d%%",
    )
    if articulation < 60:
        articulation_description = "Short and detached"
    elif articulation <= 100:
        articulation_description = "Smooth and connected"
    else:
        articulation_description = "Overlapping"
    st.caption(
        f"{articulation_description} · approximately {sample_size / 4:.1f} seconds total"
    )

with st.expander("Pitch mapping", expanded=False):
    st.write("These shared settings preserve the same value-to-pitch relationship on both sides.")
    map_columns = st.columns(3)
    reference_value = map_columns[0].number_input(
        "Reference value", value=2.0, step=0.5, format="%.2f"
    )
    reference_pitch = map_columns[1].slider("Reference MIDI pitch", 36, 84, 60)
    semitones_per_unit = map_columns[2].slider("Semitones per unit", 0.25, 12.0, 4.0, 0.25)
    st.caption("The default maps value 2 to middle C (MIDI 60), then moves four semitones for each unit of sample value. Notes are limited to MIDI 36–96.")

generate = st.button("Generate comparison", type="primary", width="stretch")
if generate:
    notes_per_second = 4.0
    seconds_per_note = 1.0 / notes_per_second
    config = MappingConfig(
        reference_value=reference_value,
        reference_pitch=reference_pitch,
        semitones_per_unit=semitones_per_unit,
        seconds_per_note=seconds_per_note,
        note_duration=seconds_per_note * articulation / 100.0,
        tempo=notes_per_second * 60.0,
    )
    result_left, result_right = st.columns(2, gap="large")
    with result_left:
        left_result = present_result(
            "A", left_settings, "#cf704c", config, int(sample_size), int(seed)
        )
    with result_right:
        right_result = present_result(
            "B", right_settings, "#82a58f", config, int(sample_size), int(seed)
        )

    with st.expander("Pitch clipping report", expanded=True):
        st.caption(
            "Notes outside the shared MIDI range of 36–96 are moved to the nearest limit."
        )
        report_columns = st.columns(2, gap="large")
        for column, label, result in (
            (report_columns[0], "Distribution A", left_result),
            (report_columns[1], "Distribution B", right_result),
        ):
            with column:
                clipped_total = result.clipped_low + result.clipped_high
                st.markdown(f"**{label}**")
                metrics = st.columns(3)
                metrics[0].metric("Total", f"{clipped_total}/{sample_size}")
                metrics[1].metric("Low", result.clipped_low)
                metrics[2].metric("High", result.clipped_high)
                if clipped_total == 0:
                    st.success("No pitch clipping.")
                else:
                    st.warning(
                        f"{clipped_total / sample_size:.1%} of notes were clipped."
                    )
