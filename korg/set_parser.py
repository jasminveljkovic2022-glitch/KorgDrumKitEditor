from pathlib import Path
from typing import Optional

from .models import DrumInstrument, DrumKit
from .midi import midi_to_note


class KorgSetParser:
    """
    Osnovni parser za Korg PA300 SET podatke.

    Raspored drum instrumenata nije fiksan.
    Svaki SET može imati drugačiji MIDI raspored.
    """

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    def parse(self) -> list[DrumKit]:
        """
        Učitava Korg .SET datoteku.

        Stvarni binarni parser bit će dodan nakon što
        definiramo strukturu Korg SET podataka.
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
        Kreira instrument i automatski određuje naziv MIDI note.

        Primjer:
        MIDI 24 -> C1
        MIDI 36 -> C2
        """

        return DrumInstrument(
            midi_note=midi_note,
            note_name=midi_to_note(midi_note),
            name=name,
            program=program,
            bank_msb=bank_msb,
            bank_lsb=bank_lsb,
        )
