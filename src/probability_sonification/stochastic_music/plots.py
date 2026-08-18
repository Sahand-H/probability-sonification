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
        .properties(title="Event matrix", height=max(120, 50 * event_matrix.n_instruments))
        .configure_view(strokeOpacity=0)
    )


def event_timeline_plot(
    events: tuple[MusicalEvent, ...],
    config: StochasticMusicConfig,
):
    """Plot event start times and the boundaries between time blocks."""

    event_values = [
        {
            "Instrument": event.instrument_name,
            "Start time": event.start_time,
            "Time block": event.time_block_index + 1,
            "Pitch": event.pitch,
        }
        for event in events
    ]
    color_scale = _instrument_color_scale(config.selected_instruments)

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
                sort=list(config.selected_instruments),
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
                "Pitch:Q",
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
            height=max(140, 50 * len(config.selected_instruments)),
        )
        .configure_view(strokeOpacity=0)
    )


def event_pitch_distribution_plot(
    events: tuple[MusicalEvent, ...],
    instruments: tuple[str, ...],
):
    """Plot the sampled pitch probability for each instrument."""

    pitch_values = [
        {"Instrument": event.instrument_name, "Pitch": event.pitch}
        for event in events
    ]

    # Normalize each instrument separately so different event counts remain comparable.
    return (
        alt.Chart(alt.Data(values=pitch_values))
        .transform_aggregate(
            Count="count()",
            groupby=["Instrument", "Pitch"],
        )
        .transform_joinaggregate(
            Total="sum(Count)",
            groupby=["Instrument"],
        )
        .transform_calculate(Probability="datum.Count / datum.Total")
        .mark_bar()
        .encode(
            x=alt.X("Pitch:O", title="MIDI pitch", sort="ascending"),
            y=alt.Y("Probability:Q", title="Probability"),
            color=alt.Color(
                "Instrument:N",
                scale=_instrument_color_scale(instruments),
                legend=None,
            ),
            column=alt.Column(
                "Instrument:N",
                title=None,
                sort=list(instruments),
            ),
            tooltip=[
                "Instrument:N",
                "Pitch:O",
                "Count:Q",
                alt.Tooltip("Probability:Q", format=".3f"),
            ],
        )
        .properties(title="Event pitch distribution", width=220, height=180)
        .configure_view(strokeOpacity=0)
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
            "Note": pretty_midi.note_number_to_name(event.pitch),
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
            y=alt.Y("Pitch:Q", title="MIDI pitch"),
            color=alt.Color(
                "Instrument:N",
                scale=_instrument_color_scale(instruments),
                title="Instrument",
            ),
            tooltip=[
                "Instrument:N",
                "Note:N",
                "Pitch:Q",
                alt.Tooltip("Start time:Q", format=".2f"),
                alt.Tooltip("End time:Q", format=".2f"),
                "Velocity:Q",
            ],
        )
        .properties(title="Note map", height=260)
        .configure_view(strokeOpacity=0)
    )
