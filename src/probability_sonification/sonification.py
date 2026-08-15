from dataclasses import dataclass
from io import BytesIO
import wave

import numpy as np
import pretty_midi


@dataclass(frozen=True)
class MappingConfig:
    reference_value: float = 2.0
    reference_pitch: int = 60
    semitones_per_unit: float = 4.0
    pitch_low: int = 36
    pitch_high: int = 96
    seconds_per_note: float = 0.15
    note_duration: float = 0.12
    velocity: int = 90
    tempo: float = 120.0


@dataclass(frozen=True)
class SonificationResult:
    midi: pretty_midi.PrettyMIDI
    midi_bytes: bytes
    pitches: np.ndarray
    clipped_low: int
    clipped_high: int


def map_values_to_pitches(
    samples: np.ndarray, config: MappingConfig
) -> tuple[np.ndarray, int, int]:
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Samples must be a non-empty, finite one-dimensional sequence.")

    raw = config.reference_pitch + (
        values - config.reference_value
    ) * config.semitones_per_unit
    clipped_low = int(np.sum(raw < config.pitch_low))
    clipped_high = int(np.sum(raw > config.pitch_high))
    pitches = np.clip(
        np.rint(raw), config.pitch_low, config.pitch_high
    ).astype(int)
    return pitches, clipped_low, clipped_high


def sonify(
    samples: np.ndarray, instrument_name: str, config: MappingConfig | None = None
) -> SonificationResult:
    config = config or MappingConfig()
    pitches, clipped_low, clipped_high = map_values_to_pitches(samples, config)
    midi = pretty_midi.PrettyMIDI(initial_tempo=config.tempo)
    instrument = pretty_midi.Instrument(
        program=pretty_midi.instrument_name_to_program(instrument_name),
        name=instrument_name,
    )
    for index, pitch in enumerate(pitches):
        start = index * config.seconds_per_note
        instrument.notes.append(
            pretty_midi.Note(
                velocity=config.velocity,
                pitch=int(pitch),
                start=start,
                end=start + config.note_duration,
            )
        )
    midi.instruments.append(instrument)
    buffer = BytesIO()
    midi.write(buffer)
    return SonificationResult(
        midi=midi,
        midi_bytes=buffer.getvalue(),
        pitches=pitches,
        clipped_low=clipped_low,
        clipped_high=clipped_high,
    )


def audio_to_wav(audio: np.ndarray, sample_rate: int = 44_100) -> bytes:
    audio = np.asarray(audio, dtype=float)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0:
        audio = audio / peak * 0.92
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return output.getvalue()


def render_audio(midi: pretty_midi.PrettyMIDI, sample_rate: int = 44_100) -> tuple[bytes, bool]:
    """Render with FluidSynth, falling back to pretty_midi's sine preview."""
    used_fluidsynth = True
    try:
        audio = midi.fluidsynth(fs=sample_rate)
    except (ImportError, OSError, RuntimeError):
        used_fluidsynth = False
        audio = midi.synthesize(fs=sample_rate)
    return audio_to_wav(audio, sample_rate), used_fluidsynth
