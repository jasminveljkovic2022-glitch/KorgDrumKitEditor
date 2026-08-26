from korg.midi import midi_to_note, note_to_midi


def test_midi_to_note():
    assert midi_to_note(24) == "C1"
    assert midi_to_note(25) == "C#1"
    assert midi_to_note(26) == "D1"
    assert midi_to_note(36) == "C2"


def test_note_to_midi():
    assert note_to_midi("C1") == 24
    assert note_to_midi("C#1") == 25
    assert note_to_midi("D1") == 26
    assert note_to_midi("C2") == 36


if __name__ == "__main__":
    test_midi_to_note()
    test_note_to_midi()
    print("MIDI tests OK")
