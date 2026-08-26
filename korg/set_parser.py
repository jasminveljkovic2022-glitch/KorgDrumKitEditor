from pathlib import Path
from typing import Optional

from .models import DrumInstrument, DrumKit
from .midi import midi_to_note


class KorgSetParser:
    """
    Parser za Korg PA300 .SET podatke.

    VAŽNO:
    MIDI raspored drum instrumenata nije fiksan.
    Svaki SET može imati drugačiji raspored.
    """

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    def read_bytes(self) -> bytes:
        """
        Učitaj cijeli SET kao binarne podatke.
        """

        if not self.set_path.exists():
            raise FileNotFoundError(
                f"SET file does not exist: {self.set_path}"
            )

        if not self.set_path.is_file():
            raise ValueError(
                f"SET path is not a file: {self.set_path}"
            )

        if self.set_path.suffix.lower() != ".set":
            raise ValueError(
                "Expected a Korg .SET file"
            )

        return self.set_path.read_bytes()

    def parse(self) -> list[DrumKit]:
        """
        Analizira Korg PA300 SET.

        Trenutna faza:
        - provjera SET datoteke
        - učitavanje binarnih podataka
        - priprema za pronalaženje drum kit struktura

        Ne pretpostavlja fiksni MIDI raspored.
        """

        data = self.read_bytes()

        if not data:
            raise ValueError("SET file is empty")

        # Za sada vraćamo praznu listu dok ne definiramo
        # stvarnu binarnu strukturu PA300 SET datoteke.
        #
        # OVDJE će kasnije biti:
        #
        # SET
        #  └── SOUND
        #       └── Drum Kit
        #            ├── MIDI note
        #            ├── instrument
        #            ├── program
        #            ├── bank MSB
        #            └── bank LSB

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
        MIDI 38 -> D2
        """

        return DrumInstrument(
            midi_note=midi_note,
            note_name=midi_to_note(midi_note),
            name=name,
            program=program,
            bank_msb=bank_msb,
            bank_lsb=bank_lsb,
        )
