import numpy as np

from probability_sonification.sonification import MappingConfig, map_values_to_pitches, sonify


def test_shared_mapping_preserves_equal_values():
    config = MappingConfig(reference_value=0.0)
    left, _, _ = map_values_to_pitches(np.array([0.0, 1.0, 2.0]), config)
    right, _, _ = map_values_to_pitches(np.array([2.0, 1.0, 0.0]), config)
    assert left.tolist() == [60, 64, 68]
    assert right.tolist() == [68, 64, 60]


def test_mapping_reports_clipping():
    pitches, low, high = map_values_to_pitches(
        np.array([-100.0, 0.0, 100.0]), MappingConfig(reference_value=0.0)
    )
    assert pitches.tolist() == [36, 60, 96]
    assert (low, high) == (1, 1)


def test_sonification_returns_midi_bytes():
    result = sonify(np.array([0.0, 1.0]), "Violin")
    assert result.midi_bytes.startswith(b"MThd")
    assert len(result.midi.instruments[0].notes) == 2
