NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]


def midi_to_note(midi_note: int) -> str:
    """Convert MIDI note number to note name."""
    if not 0 <= midi_note <= 127:
        raise ValueError("MIDI note must be between 0 and 127")

    octave = (midi_note // 12) - 1
    name = NOTE_NAMES[midi_note % 12]

    return f"{name}{octave}"


def note_to_midi(note: str) -> int:
    """Convert note name to MIDI note number."""
    note = note.strip().upper()

    for midi_note in range(128):
        if midi_to_note(midi_note).upper() == note:
            return midi_note

    raise ValueError(f"Invalid note: {note}")
