"""Altair plots for inspecting stochastic music results."""

import altair as alt
import pretty_midi

from probability_sonification.stochastic_music.models import (
    EventMatrix,
    MusicalEvent,
    StochasticMusicConfig,
)


def _instrument_color_scale(instruments: tuple[str, ...]) -> alt.Scale:
    """Keep instrument colors stable across every plot."""

    return alt.Scale(domain=list(instruments), scheme="tableau10")


def event_matrix_plot(event_matrix: EventMatrix):
    """Plot musical event counts by instrument and time block."""

    cells = [
        {
            "Instrument": instrument_name,
            "Time block": time_block_index + 1,
            "Event count": int(event_matrix.counts[instrument_index, time_block_index]),
        }
        for instrument_index, instrument_name in enumerate(event_matrix.instruments)
        for time_block_index in range(event_matrix.n_time_blocks)
    ]

    return (
        alt.Chart(alt.Data(values=cells))
        .mark_rect()
        .encode(
            x=alt.X("Time block:O", title="Time block"),
            y=alt.Y(
                "Instrument:N",
                title="Instrument",
                sort=list(event_matrix.instruments),
            ),
            color=alt.Color(
                "Event count:Q",
                title="Events",
                scale=alt.Scale(scheme="blues"),
            ),
            tooltip=["Instrument:N", "Time block:O", "Event count:Q"],
        )
        .properties(
            title="Event matrix",
            height=max(190, 65 * event_matrix.n_instruments),
            background="transparent",
        )
        .configure_view(fill="transparent", strokeOpacity=0)
        .configure_axis(
            grid=True,
            gridColor="#9b969d",
            gridOpacity=0.52,
            gridDash=[2, 2],
        )
    )


def event_timeline_plot(
    events: tuple[MusicalEvent, ...],
    config: StochasticMusicConfig,
):
    """Plot event start times and the boundaries between time blocks."""

    instrument_names = tuple(
        instrument.name for instrument in config.selected_instruments
    )
    event_values = [
        {
            "Instrument": event.instrument_name,
            "Start time": event.start_time,
            "Time block": event.time_block_index + 1,
            "MIDI note": event.pitch,
            "Note or sound": (
                pretty_midi.note_number_to_drum_name(event.pitch)
                if event.is_drum
                else pretty_midi.note_number_to_name(event.pitch)
            ),
        }
        for event in events
    ]
    color_scale = _instrument_color_scale(instrument_names)

    # Tick marks emphasize event onset without implying a sampled duration.
    event_marks = (
        alt.Chart(alt.Data(values=event_values))
        .mark_tick(thickness=2, size=24)
        .encode(
            x=alt.X(
                "Start time:Q",
                title="Time (seconds)",
                scale=alt.Scale(domain=[0, config.composition_duration]),
            ),
            y=alt.Y(
                "Instrument:N",
                title="Instrument",
                sort=list(instrument_names),
            ),
            color=alt.Color(
                "Instrument:N",
                scale=color_scale,
                legend=None,
            ),
            tooltip=[
                "Instrument:N",
                alt.Tooltip("Start time:Q", format=".2f"),
                "Time block:O",
                "Note or sound:N",
                "MIDI note:Q",
            ],
        )
    )

    time_block_duration = config.composition_duration / config.n_time_blocks
    boundaries = [
        {"Boundary": block_index * time_block_duration}
        for block_index in range(1, config.n_time_blocks)
    ]
    boundary_rules = (
        alt.Chart(alt.Data(values=boundaries))
        .mark_rule(color="gray", strokeDash=[4, 4], opacity=0.5)
        .encode(x="Boundary:Q")
    )

    return (
        alt.layer(boundary_rules, event_marks)
        .properties(
            title="Event timeline",
            height=max(210, 65 * len(instrument_names)),
            background="transparent",
        )
        .configure_view(fill="transparent", strokeOpacity=0)
        .configure_axis(
            grid=True,
            gridColor="#9b969d",
            gridOpacity=0.52,
            gridDash=[2, 2],
        )
    )


def event_pitch_distribution_plot(
    events: tuple[MusicalEvent, ...],
    instruments: tuple[str, ...],
    pitch_range: tuple[int, int] = (0, 127),
):
    """Plot a pitch histogram with a kernel-density overlay."""

    pitch_values = [
        {"Instrument": event.instrument_name, "Pitch": event.pitch}
        for event in events
        if not event.is_drum and event.instrument_name in instruments
    ]

    pitch_data = alt.Data(values=pitch_values)
    color = alt.Color(
        "Instrument:N",
        scale=_instrument_color_scale(instruments),
        legend=None,
        sort=list(instruments),
    )

    # Express both layers as density so the histogram and KDE share one y-axis.
    histogram = (
        alt.Chart(pitch_data)
        .transform_bin(
            as_=["PitchBin", "PitchBinEnd"],
            field="Pitch",
            bin=alt.Bin(maxbins=16),
        )
        .transform_aggregate(
            Count="count()",
            groupby=["Instrument", "PitchBin", "PitchBinEnd"],
        )
        .transform_joinaggregate(
            Total="sum(Count)",
            groupby=["Instrument"],
        )
        .transform_calculate(
            Density="datum.Count / (datum.Total * (datum.PitchBinEnd - datum.PitchBin))"
        )
        .mark_bar(opacity=0.68, strokeWidth=1)
        .encode(
            x=alt.X(
                "PitchBin:Q",
                title="MIDI pitch",
                scale=alt.Scale(domain=list(pitch_range)),
            ),
            x2="PitchBinEnd:Q",
            y=alt.Y("Density:Q", title="Density"),
            y2=alt.Y2(datum=0),
            color=color,
            tooltip=[
                "Instrument:N",
                alt.Tooltip("PitchBin:Q", title="Pitch from", format=".1f"),
                alt.Tooltip("PitchBinEnd:Q", title="Pitch to", format=".1f"),
                "Count:Q",
                alt.Tooltip("Density:Q", format=".3f"),
            ],
        )
    )
    kde = (
        alt.Chart(pitch_data)
        .transform_density(
            "Pitch",
            as_=["Pitch", "Density"],
            extent=list(pitch_range),
            groupby=["Instrument"],
        )
        .mark_line(strokeWidth=3)
        .encode(
            x=alt.X(
                "Pitch:Q",
                title="MIDI pitch",
                scale=alt.Scale(domain=list(pitch_range)),
            ),
            y=alt.Y("Density:Q", title="Density"),
            color=color,
            tooltip=[
                "Instrument:N",
                alt.Tooltip("Pitch:Q", format=".1f"),
                alt.Tooltip("Density:Q", format=".3f"),
            ],
        )
    )

    return (
        alt.layer(histogram, kde)
        .properties(
            title="Event pitch distribution",
            width="container",
            height=320,
            background="transparent",
        )
        .configure_view(fill="transparent", strokeOpacity=0)
        .configure_axis(
            grid=True,
            gridColor="#9b969d",
            gridOpacity=0.52,
            gridDash=[2, 2],
        )
    )


def drum_sound_distribution_plot(
    events: tuple[MusicalEvent, ...],
    instruments: tuple[str, ...],
):
    """Plot the categorical drum sounds selected for drum events."""

    drum_values = [
        {
            "Instrument": event.instrument_name,
            "Drum sound": pretty_midi.note_number_to_drum_name(event.pitch),
        }
        for event in events
        if event.is_drum
    ]

    return (
        alt.Chart(alt.Data(values=drum_values))
        .mark_bar()
        .encode(
            x=alt.X("Drum sound:N", title="Drum sound"),
            y=alt.Y("count():Q", title="Events"),
            color=alt.Color(
                "Instrument:N",
                scale=_instrument_color_scale(instruments),
                legend=None,
            ),
            tooltip=["Instrument:N", "Drum sound:N", alt.Tooltip("count():Q")],
        )
        .properties(
            title="Drum sound distribution",
            height=280,
            background="transparent",
        )
        .configure_view(fill="transparent", strokeOpacity=0)
        .configure_axis(
            grid=True,
            gridColor="#9b969d",
            gridOpacity=0.52,
            gridDash=[2, 2],
        )
    )


def note_map_plot(
    events: tuple[MusicalEvent, ...],
    instruments: tuple[str, ...],
):
    """Plot each MIDI note by its time span and pitch."""

    note_values = [
        {
            "Instrument": event.instrument_name,
            "Start time": event.start_time,
            "End time": event.end_time,
            "Pitch": event.pitch,
            "Note or sound": (
                pretty_midi.note_number_to_drum_name(event.pitch)
                if event.is_drum
                else pretty_midi.note_number_to_name(event.pitch)
            ),
            "Velocity": event.velocity,
        }
        for event in events
    ]

    return (
        alt.Chart(alt.Data(values=note_values))
        .mark_bar(size=7)
        .encode(
            x=alt.X("Start time:Q", title="Time (seconds)"),
            x2="End time:Q",
            y=alt.Y("Pitch:Q", title="MIDI note number"),
            color=alt.Color(
                "Instrument:N",
                scale=_instrument_color_scale(instruments),
                title="Instrument",
            ),
            tooltip=[
                "Instrument:N",
                "Note or sound:N",
                "Pitch:Q",
                alt.Tooltip("Start time:Q", format=".2f"),
                alt.Tooltip("End time:Q", format=".2f"),
                "Velocity:Q",
            ],
        )
        .properties(title="Note map", height=360, background="transparent")
        .configure_view(fill="transparent", strokeOpacity=0)
        .configure_axis(
            grid=True,
            gridColor="#9b969d",
            gridOpacity=0.52,
            gridDash=[2, 2],
        )
    )
