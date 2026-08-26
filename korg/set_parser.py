from pathlib import Path
from typing import Optional

from .models import DrumInstrument, DrumKit
from .midi import midi_note_to_name


class KorgSetParser:
    """
    Parser za Korg PA SET podatke.

    Važno:
    Ne pretpostavlja unaprijed da je Kick uvijek na C1,
    Snare uvijek na D1 itd.

    Raspored instrumenata mora se dobiti iz konkretnog
    SET/PCG/DrumKit podatka.
    """

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    def parse(self) -> list[DrumKit]:
        """
        Parsira SET i vraća pronađene DrumKit objekte.

        Trenutno je ovo osnovna struktura.
        Stvarni binarni PA300 parser dodajemo nakon što
        utvrdimo strukturu podataka iz stvarnog SET-a.
        """
        if not self.set_path.exists():
            raise FileNotFoundError(
                f"SET file does not exist: {self.set_path}"
            )

        if self.set_path.suffix.lower() != ".set":
            raise ValueError(
                "Expected a Korg .SET file"
            )

        return []

    @staticmethod
    def create_instrument(
        midi_note: int,
        name: str,
        program: Optional[int] = None,
        bank_msb: Optional[int] = None,
        bank_lsb: Optional[int] = None,
    ) -> DrumInstrument:
        """
        Kreira instrument koristeći stvarni MIDI broj note.
        """
        return DrumInstrument(
            midi_note=midi_note,
            note_name=midi_note_to_name(midi_note),
            name=name,
            program=program,
            bank_msb=bank_msb,
            bank_lsb=bank_lsb,
        )
