```python
from pathlib import Path
from typing import Optional

from .models import DrumInstrument, DrumKit
from .midi import midi_to_note


class KorgSetParser:
    """
    Osnovni binarni inspector/parser za Korg PA SET datoteke.

    Korg .SET format je binaran i njegova unutrašnja struktura
    može zavisiti od modela i verzije sistema. Zato prvo učitavamo
    sirove podatke i pripremamo ih za dalju analizu.
    """

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    def _validate(self) -> None:
        """Provjerava da li SET datoteka postoji i ima .SET ekstenziju."""

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

    def read_bytes(self) -> bytes:
        """
        Učitava cijelu SET datoteku kao binarne podatke.
        """

        self._validate()

        return self.set_path.read_bytes()

    def inspect(self, preview_size: int = 256) -> dict:
        """
        Vraća osnovne informacije o binarnoj SET datoteci.

        Ne pokušava još interpretirati nepoznate Korg strukture.
        """

        data = self.read_bytes()

        preview_size = max(1, preview_size)

        preview = data[:preview_size]

        return {
            "path": str(self.set_path),
            "size": len(data),
            "preview_size": len(preview),
            "hex": preview.hex(" "),
        }

    def find_ascii_strings(
        self,
        minimum_length: int = 4,
    ) -> list[str]:
        """
        Pronalazi jednostavne ASCII tekstove unutar binarne datoteke.

        Ovo je pomoćna funkcija za istraživanje SET strukture.
        """

        data = self.read_bytes()

        if minimum_length < 1:
            raise ValueError(
                "minimum_length must be greater than 0"
            )

        strings: list[str] = []
        current = bytearray()

        for byte in data:
            if 32 <= byte <= 126:
                current.append(byte)
            else:
                if len(current) >= minimum_length:
                    strings.append(
                        current.decode("ascii")
                    )

                current.clear()

        if len(current) >= minimum_length:
            strings.append(
                current.decode("ascii")
            )

        return strings

    def parse(self) -> list[DrumKit]:
        """
        Trenutno osnovno parsiranje SET datoteke.

        Datoteka se učita i provjeri, ali se Drum Kit struktura
        još ne generira dok ne utvrdimo tačan binarni format.
        """

        self._validate()

        data = self.read_bytes()

        if not data:
            return []

        # TODO:
        # 1. Identifikovati Korg SET strukture.
        # 2. Pronaći PCG/Drum Kit podatke.
        # 3. Pročitati MIDI mapiranje.
        # 4. Kreirati DrumKit objekte.

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
        Kreira DrumInstrument i automatski određuje naziv MIDI note.

        Primjeri:
            MIDI 24 -> C1
            MIDI 36 -> C2
            MIDI 60 -> C4
        """

        return DrumInstrument(
            midi_note=midi_note,
            note_name=midi_to_note(midi_note),
            name=name,
            program=program,
            bank_msb=bank_msb,
            bank_lsb=bank_lsb,
        )
```
