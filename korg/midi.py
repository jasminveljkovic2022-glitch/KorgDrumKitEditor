NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]


def midi_to_note(midi_note: int) -> str:
    """
    Convert MIDI note number to note name.

    MIDI 60 = C4
    MIDI 36 = C2
    MIDI 24 = C1
    """
    if not 0 <= midi_note <= 127:
        raise ValueError("MIDI note must be between 0 and 127")

    octave = (midi_note // 12) - 1
    note = NOTE_NAMES[midi_note % 12]

    return f"{note}{octave}"


def note_to_midi(note_name: str) -> int:
    """
    Convert note name such as C1, D#2 or F#3 to MIDI number.
    """

    note_name = note_name.strip().upper()

    if len(note_name) < 2:
        raise ValueError("Invalid note name")

    if note_name[1] == "#":
        note = note_name[:2]
        octave_text = note_name[2:]
    else:
        note = note_name[:1]
        octave_text = note_name[1:]

    if note not in NOTE_NAMES:
        raise ValueError(f"Invalid note: {note}")

    try:
        octave = int(octave_text)
    except ValueError:
        raise ValueError(f"Invalid octave: {octave_text}")

    midi_note = (octave + 1) * 12 + NOTE_NAMES.index(note)

    if not 0 <= midi_note <= 127:
        raise ValueError("Resulting MIDI note is outside 0-127")

    return midi_note
