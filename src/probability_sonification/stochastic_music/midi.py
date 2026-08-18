"""MIDI construction helpers for stochastic musical events."""

from io import BytesIO

import pretty_midi

from probability_sonification.stochastic_music.models import MusicalEvent


def build_midi(
    events: tuple[MusicalEvent, ...],
    selected_instruments: tuple[str, ...],
) -> pretty_midi.PrettyMIDI:
    """Build an ordered MIDI track for every selected instrument."""

    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    tracks = []

    # Create tracks before adding notes so silent instruments remain represented.
    for instrument_name in selected_instruments:
        program = pretty_midi.instrument_name_to_program(instrument_name)
        track = pretty_midi.Instrument(program=program, name=instrument_name)
        midi.instruments.append(track)
        tracks.append(track)

    for event in events:
        if not 0 <= event.instrument_index < len(tracks):
            raise ValueError("Musical event references an unknown instrument index.")
        if selected_instruments[event.instrument_index] != event.instrument_name:
            raise ValueError("Musical event instrument name does not match its index.")

        # PrettyMIDI uses absolute seconds, so notes may extend past the target duration.
        tracks[event.instrument_index].notes.append(
            pretty_midi.Note(
                velocity=event.velocity,
                pitch=event.pitch,
                start=event.start_time,
                end=event.end_time,
            )
        )

    return midi


def midi_to_bytes(midi: pretty_midi.PrettyMIDI) -> bytes:
    """Serialize a MIDI object for download or storage."""

    output = BytesIO()
    midi.write(output)
    return output.getvalue()
