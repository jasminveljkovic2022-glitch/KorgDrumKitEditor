from pathlib import Path
from typing import Optional

from .models import DrumInstrument, DrumKit
from .midi import midi_to_note


class KorgSetParser:
    """
    Binarni inspector/parser za Korg PA SET datoteke.

    Ova verzija ne pokušava nagađati nepoznatu internu Korg strukturu.
    Umjesto toga omogućava detaljnu analizu stvarnog SET fajla:

    - osnovne informacije o fajlu
    - hex pregled
    - ASCII stringove
    - ASCII stringove sa offsetima
    - pretragu proizvoljnih byte patterna
    - hexdump određenog dijela fajla
    - objedinjeni structural inspection rezultat

    Kasnije se ove funkcije mogu koristiti za izgradnju pravog
    Korg SET/PCG/Drum Kit parsera.
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

        Args:
            preview_size: Broj prvih byteova koji će biti prikazan
                u hex formatu.

        Returns:
            Dictionary sa osnovnim informacijama.
        """

        data = self.read_bytes()

        if preview_size < 1:
            raise ValueError(
                "preview_size must be greater than 0"
            )

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

        Returns:
            Lista pronađenih ASCII stringova.
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

    def find_ascii_strings_with_offsets(
        self,
        minimum_length: int = 4,
    ) -> list[dict]:
        """
        Pronalazi ASCII stringove i vraća njihov početni offset.

        Primjer rezultata:

            {
                "offset": 1234,
                "length": 8,
                "text": "DrumKit1"
            }

        Offset je decimalni byte offset od početka SET datoteke.
        """

        data = self.read_bytes()

        if minimum_length < 1:
            raise ValueError(
                "minimum_length must be greater than 0"
            )

        strings: list[dict] = []
        current = bytearray()
        start_offset: Optional[int] = None

        for offset, byte in enumerate(data):
            if 32 <= byte <= 126:
                if start_offset is None:
                    start_offset = offset

                current.append(byte)

            else:
                if (
                    start_offset is not None
                    and len(current) >= minimum_length
                ):
                    strings.append(
                        {
                            "offset": start_offset,
                            "length": len(current),
                            "text": current.decode("ascii"),
                        }
                    )

                current.clear()
                start_offset = None

        if (
            start_offset is not None
            and len(current) >= minimum_length
        ):
            strings.append(
                {
                    "offset": start_offset,
                    "length": len(current),
                    "text": current.decode("ascii"),
                }
            )

        return strings

    def find_byte_pattern(
        self,
        pattern: bytes,
    ) -> list[int]:
        """
        Pronalazi sva pojavljivanja byte patterna u SET fajlu.

        Args:
            pattern: Byte sekvenca koju treba pronaći.

        Returns:
            Lista početnih offseta na kojima je pattern pronađen.

        Primjer:

            parser.find_byte_pattern(b"PCG")

        može vratiti:

            [1024, 8192]
        """

        data = self.read_bytes()

        if not pattern:
            raise ValueError(
                "pattern must not be empty"
            )

        offsets: list[int] = []
        start = 0

        while True:
            offset = data.find(pattern, start)

            if offset == -1:
                break

            offsets.append(offset)

            # +1 omogućava pronalaženje preklapajućih patterna.
            start = offset + 1

        return offsets

    def hexdump(
        self,
        offset: int = 0,
        length: int = 256,
        bytes_per_line: int = 16,
    ) -> str:
        """
        Vraća klasični hex dump određenog dijela SET fajla.

        Format primjera:

            00000000  50 43 47 00 01 02 03 04  PCG.....

        Args:
            offset: Početni byte offset.
            length: Broj byteova za prikaz.
            bytes_per_line: Broj byteova po liniji.
        """

        data = self.read_bytes()

        if offset < 0:
            raise ValueError(
                "offset must not be negative"
            )

        if length < 1:
            raise ValueError(
                "length must be greater than 0"
            )

        if bytes_per_line < 1:
            raise ValueError(
                "bytes_per_line must be greater than 0"
            )

        if offset > len(data):
            raise ValueError(
                "offset is outside the SET file"
            )

        chunk = data[offset:offset + length]

        lines: list[str] = []

        for relative_offset in range(
            0,
            len(chunk),
            bytes_per_line,
        ):
            line = chunk[
                relative_offset:
                relative_offset + bytes_per_line
            ]

            absolute_offset = offset + relative_offset

            hex_part = " ".join(
                f"{byte:02X}"
                for byte in line
            )

            padding = " ".join(
                "  "
                for _ in range(
                    bytes_per_line - len(line)
                )
            )

            ascii_part = "".join(
                chr(byte)
                if 32 <= byte <= 126
                else "."
                for byte in line
            )

            if padding:
                hex_part = f"{hex_part} {padding}"

            lines.append(
                f"{absolute_offset:08X}  "
                f"{hex_part:<{bytes_per_line * 3 - 1}}  "
                f"{ascii_part}"
            )

        return "\n".join(lines)

    def inspect_structure(
        self,
        preview_size: int = 256,
        minimum_string_length: int = 4,
    ) -> dict:
        """
        Objedinjuje osnovne rezultate binarne analize.

        Ova metoda je namijenjena za CLI i kasniju GUI aplikaciju.

        Ne interpretira Korg strukturu. Samo prikuplja sirove
        informacije koje će nam pomoći da utvrdimo strukturu.
        """

        data = self.read_bytes()

        if preview_size < 1:
            raise ValueError(
                "preview_size must be greater than 0"
            )

        if minimum_string_length < 1:
            raise ValueError(
                "minimum_string_length must be greater than 0"
            )

        preview = data[:preview_size]

        strings = self.find_ascii_strings_with_offsets(
            minimum_length=minimum_string_length
        )

        return {
            "path": str(self.set_path),
            "size": len(data),
            "preview": {
                "size": len(preview),
                "hex": preview.hex(" "),
            },
            "ascii_strings": strings,
        }

    def parse(self) -> list[DrumKit]:
        """
        Trenutno osnovno parsiranje SET datoteke.

        Fajl se učita i provjeri, ali se DrumKit struktura još
        ne generira dok ne utvrdimo stvarni binarni format.

        Važno:
            Ne treba nagađati strukturu Korg SET fajla bez stvarnog
            uzorka i validacije pronađenih offseta/podataka.
        """

        data = self.read_bytes()

        if not data:
            return []

        # TODO:
        # 1. Identifikovati Korg SET strukture.
        # 2. Identifikovati PCG/Drum Kit blokove.
        # 3. Pronaći strukturu Drum Kit programa.
        # 4. Pročitati MIDI mapiranje.
        # 5. Kreirati DrumKit objekte.
        #
        # Ove korake treba implementirati tek nakon analize
        # stvarnog PA300 SET fajla.

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
