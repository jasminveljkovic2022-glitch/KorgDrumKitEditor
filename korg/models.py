from dataclasses import dataclass
from typing import Optional


@dataclass
class DrumInstrument:
    midi_note: int
    note_name: str
    name: str
    program: Optional[int] = None
    bank_msb: Optional[int] = None
    bank_lsb: Optional[int] = None


@dataclass
class DrumKit:
    name: str
    instruments: list[DrumInstrument]

    def get_instrument(self, midi_note: int) -> Optional[DrumInstrument]:
        for instrument in self.instruments:
            if instrument.midi_note == midi_note:
                return instrument
        return None
