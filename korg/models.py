from dataclasses import dataclass


@dataclass
class DrumInstrument:
    midi_note: int
    name: str
    sample_name: str = ""
    velocity: int | None = None

    @property
    def note_name(self) -> str:
        from .midi import midi_to_note
        return midi_to_note(self.midi_note)


@dataclass
class DrumKit:
    name: str
    instruments: list[DrumInstrument]

    def get_instrument(self, midi_note: int) -> DrumInstrument | None:
        for instrument in self.instruments:
            if instrument.midi_note == midi_note:
                return instrument

        return None
