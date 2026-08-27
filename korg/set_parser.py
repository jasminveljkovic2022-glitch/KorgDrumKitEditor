from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from shutil import copyfile
from typing import Optional

from .midi import midi_to_note
from .models import DrumInstrument, DrumKit


class KorgSetParser:
    """
    PA300 SET / PCG binary parser and inspector.

    #18

    Ova verzija je prilagođena stvarnom PA300 USERDK.PCG fajlu.

    Trenutno pouzdano obrađuje:

    - sirove binarne podatke
    - veličinu fajla
    - SHA-256 checksum
    - hex pregled
    - ASCII stringove sa offsetima
    - pretragu byte patterna
    - hexdump
    - KORF blok
    - 24-byte Drum Kit name records
    - stvarne nazive Drum Kitova iz USERDK.PCG
    - sirove bajtove pojedinačnih name recorda

    VAŽNO:

    Parser trenutno NE mijenja USERDK.PCG.

    Parser trenutno NE pokušava nagađati MIDI/key mapping.

    Parser trenutno NE zapisuje izmjene nazad u PCG.

    To je namjerno. Prvo moramo potvrditi strukturu MIDI/
    instrument podataka pomoću stvarnog PA300 PCG fajla.
    """

    # ------------------------------------------------------------------
    # Potvrđena struktura iz stvarnog PA300 USERDK.PCG
    # ------------------------------------------------------------------
    #
    # KORF počinje na offsetu 23 (0x17)
    #
    # Nakon KORF zaglavlja:
    #
    #   KORF + 13 byte header
    #   24 byte Drum Kit name record
    #   24 byte Drum Kit name record
    #   24 byte Drum Kit name record
    #   ...
    #
    KORF_MAGIC = b"KORF"
    KORF_HEADER_SIZE = 13
    DRUM_KIT_RECORD_SIZE = 24

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    # ------------------------------------------------------------------
    # Validation / raw data
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """
        Provjerava da li ulazni fajl postoji i da je podržan.

        Podržavamo:

        - .SET
        - .PCG

        USERDK.PCG sa PA300 se može direktno predati parseru.
        """

        if not self.set_path.exists():
            raise FileNotFoundError(
                f"SET/PCG file does not exist: {self.set_path}"
            )

        if not self.set_path.is_file():
            raise ValueError(
                f"SET/PCG path is not a file: {self.set_path}"
            )

        suffix = self.set_path.suffix.lower()

        if suffix not in {".set", ".pcg"}:
            raise ValueError(
                "Expected a Korg .SET or .PCG file"
            )

    def read_bytes(self) -> bytes:
        """
        Učitava originalni fajl kao immutable bytes.

        Ova metoda nikada ne zapisuje ništa na disk.
        """

        self._validate()
        return self.set_path.read_bytes()

    def raw_bytes(self) -> bytes:
        """
        Alias za read_bytes().

        Koristi se kada želimo jasno naglasiti da radimo
        sa originalnim sirovim podacima.
        """

        return self.read_bytes()

    def sha256(self) -> str:
        """
        Vraća SHA-256 checksum originalnog fajla.

        Ovo omogućava da uvijek provjerimo da li je original
        ostao identičan.
        """

        return sha256(self.read_bytes()).hexdigest()

    def copy_original(self, destination: str | Path) -> Path:
        """
        Napravi identičnu kopiju originalnog fajla.

        Originalni fajl se ne mijenja.
        """

        destination_path = Path(destination)

        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        copyfile(self.set_path, destination_path)

        return destination_path

    # ------------------------------------------------------------------
    # Basic inspection
    # ------------------------------------------------------------------

    def inspect(self, preview_size: int = 256) -> dict:
        """
        Vraća osnovne informacije o fajlu.
        """

        if preview_size < 1:
            raise ValueError(
                "preview_size must be greater than 0"
            )

        data = self.read_bytes()
        preview = data[:preview_size]

        return {
            "path": str(self.set_path),
            "suffix": self.set_path.suffix.lower(),
            "size": len(data),
            "sha256": self.sha256(),
            "preview_size": len(preview),
            "hex": preview.hex(" "),
        }

    # ------------------------------------------------------------------
    # ASCII strings
    # ------------------------------------------------------------------

    def find_ascii_strings(
        self,
        minimum_length: int = 4,
    ) -> list[str]:
        """
        Pronalazi ASCII tekstove unutar binarnog fajla.
        """

        records = self.find_ascii_strings_with_offsets(
            minimum_length=minimum_length
        )

        return [
            record["text"]
            for record in records
        ]

    def find_ascii_strings_with_offsets(
        self,
        minimum_length: int = 4,
    ) -> list[dict]:
        """
        Pronalazi ASCII stringove i njihove offsete.

        Primjer:

        {
            "offset": 36,
            "length": 16,
            "text": "Studio-Shain Mix"
        }
        """

        if minimum_length < 1:
            raise ValueError(
                "minimum_length must be greater than 0"
            )

        data = self.read_bytes()

        strings: list[dict] = []

        current = bytearray()
        start_offset: Optional[int] = None

        for offset, byte in enumerate(data):
            if 32 <= byte <= 126:

                if start_offset is None:
                    start_offset = offset

                current.append(byte)
                continue

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

        # Ako fajl završava ASCII stringom
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

    # ------------------------------------------------------------------
    # Byte pattern search
    # ------------------------------------------------------------------

    def find_byte_pattern(
        self,
        pattern: bytes,
    ) -> list[int]:
        """
        Pronalazi sva pojavljivanja proizvoljnog byte patterna.
        """

        if not pattern:
            raise ValueError(
                "pattern must not be empty"
            )

        data = self.read_bytes()

        offsets: list[int] = []
        start = 0

        while True:
            offset = data.find(
                pattern,
                start,
            )

            if offset == -1:
                break

            offsets.append(offset)

            # +1 omogućava i preklapajuće rezultate.
            start = offset + 1

        return offsets

    # ------------------------------------------------------------------
    # Hex dump
    # ------------------------------------------------------------------

    def hexdump(
        self,
        offset: int = 0,
        length: int = 256,
        bytes_per_line: int = 16,
    ) -> str:
        """
        Vraća klasični hex dump određenog dijela fajla.
        """

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

        data = self.read_bytes()

        if offset > len(data):
            raise ValueError(
                "offset is outside the file"
            )

        chunk = data[
            offset:
            offset + length
        ]

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

            absolute_offset = (
                offset + relative_offset
            )

            hex_part = " ".join(
                f"{byte:02X}"
                for byte in line
            )

            ascii_part = "".join(
                chr(byte)
                if 32 <= byte <= 126
                else "."
                for byte in line
            )

            lines.append(
                f"{absolute_offset:08X}  "
                f"{hex_part:<{bytes_per_line * 3 - 1}}  "
                f"{ascii_part}"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # PA300 USERDK.PCG / KORF
    # ------------------------------------------------------------------

    def find_korf_offset(self) -> Optional[int]:
        """
        Pronalazi KORF marker u PCG fajlu.

        Na dostavljenom PA300 USERDK.PCG nalazi se na:

            decimal: 23
            hex:     0x17
        """

        data = self.read_bytes()

        offset = data.find(
            self.KORF_MAGIC
        )

        if offset == -1:
            return None

        return offset

    @staticmethod
    def _decode_pcg_name(record: bytes) -> str:
        """
        Čita naziv iz 24-byte Drum Kit recorda.

        Naziv se završava na prvi NUL byte.

        Ne pokušava mijenjati ili normalizovati originalne bajtove.
        """

        raw_name = record.split(
            b"\x00",
            1,
        )[0]

        try:
            return raw_name.decode(
                "ascii",
                errors="replace",
            ).strip()

        except UnicodeDecodeError:
            return ""

    @staticmethod
    def _is_printable_ascii_name(
        record: bytes,
    ) -> bool:
        """
        Provjerava da li početak 24-byte recorda izgleda
        kao ASCII naziv Drum Kita.

        Ovo je konzervativna provjera.
        """

        if not record:
            return False

        name = record.split(
            b"\x00",
            1,
        )[0]

        if not name:
            return False

        if len(name) > 23:
            return False

        return all(
            32 <= byte <= 126
            for byte in name
        )

    def find_drum_kit_name_records(
        self,
    ) -> list[dict]:
        """
        Pronalazi stvarne Drum Kit name records iz KORF bloka.

        Na dostavljenom PA300 fajlu obrazac je:

            KORF
            13-byte header
            24-byte record
            24-byte record
            24-byte record
            ...

        Parser se zaustavlja kada sljedeći 24-byte blok više
        ne izgleda kao ASCII naziv.

        Rezultat sadrži:

            index
            offset
            end_offset
            size
            name
            raw
            hex

        RAW sadržaj je originalni sadržaj recorda.
        """

        data = self.read_bytes()

        korf_offset = self.find_korf_offset()

        if korf_offset is None:
            return []

        first_record_offset = (
            korf_offset
            + self.KORF_HEADER_SIZE
        )

        records: list[dict] = []

        offset = first_record_offset
        index = 0

        while (
            offset + self.DRUM_KIT_RECORD_SIZE
            <= len(data)
        ):

            record = data[
                offset:
                offset + self.DRUM_KIT_RECORD_SIZE
            ]

            if not self._is_printable_ascii_name(
                record
            ):
                break

            name = self._decode_pcg_name(
                record
            )

            if not name:
                break

            records.append(
                {
                    "index": index,
                    "offset": offset,
                    "end_offset": (
                        offset
                        + self.DRUM_KIT_RECORD_SIZE
                    ),
                    "size": self.DRUM_KIT_RECORD_SIZE,
                    "name": name,
                    "raw": record,
                    "hex": record.hex(" "),
                }
            )

            index += 1
            offset += self.DRUM_KIT_RECORD_SIZE

        return records

    def find_drum_kit_names(self) -> list[str]:
        """
        Vraća samo stvarne nazive Drum Kitova pronađene
        u KORF name-record bloku.
        """

        return [
            record["name"]
            for record in self.find_drum_kit_name_records()
        ]

    def get_drum_kit_name_record(
        self,
        index: int,
    ) -> dict:
        """
        Vraća jedan sirovi Drum Kit name record.

        Originalni byte sadržaj se ne mijenja.
        """

        records = self.find_drum_kit_name_records()

        if index < 0 or index >= len(records):
            raise IndexError(
                f"Drum Kit index out of range: {index}"
            )

        return records[index]

    # ------------------------------------------------------------------
    # Structural inspection
    # ------------------------------------------------------------------

    def inspect_userdk_pcg(self) -> dict:
        """
        Detaljna analiza stvarnog USERDK.PCG fajla.

        Ova metoda je namijenjena za CLI, testove i kasniji GUI.

        Ne mijenja originalni fajl.
        """

        data = self.read_bytes()

        korf_offset = self.find_korf_offset()
        records = self.find_drum_kit_name_records()

        return {
            "path": str(self.set_path),
            "size": len(data),
            "sha256": self.sha256(),
            "format": "PA300 USERDK.PCG",
            "korf": {
                "magic": (
                    self.KORF_MAGIC.decode("ascii")
                    if korf_offset is not None
                    else None
                ),
                "offset": korf_offset,
                "offset_hex": (
                    f"0x{korf_offset:X}"
                    if korf_offset is not None
                    else None
                ),
                "header_size": (
                    self.KORF_HEADER_SIZE
                    if korf_offset is not None
                    else None
                ),
            },
            "drum_kit_name_records": {
                "record_size": self.DRUM_KIT_RECORD_SIZE,
                "count": len(records),
                "first_offset": (
                    records[0]["offset"]
                    if records
                    else None
                ),
                "names": [
                    record["name"]
                    for record in records
                ],
                "records": records,
            },
        }

    def inspect_structure(
        self,
        preview_size: int = 256,
        minimum_string_length: int = 4,
    ) -> dict:
        """
        Objedinjeni structural inspection.

        Za USERDK.PCG uključuje i KORF/Drum Kit analizu.
        """

        if preview_size < 1:
            raise ValueError(
                "preview_size must be greater than 0"
            )

        if minimum_string_length < 1:
            raise ValueError(
                "minimum_string_length must be greater than 0"
            )

        data = self.read_bytes()
        preview = data[:preview_size]

        result = {
            "path": str(self.set_path),
            "size": len(data),
            "sha256": self.sha256(),
            "preview": {
                "size": len(preview),
                "hex": preview.hex(" "),
            },
            "ascii_strings": (
                self.find_ascii_strings_with_offsets(
                    minimum_length=minimum_string_length
                )
            ),
            "korf_offset": self.find_korf_offset(),
            "drum_kit_names": (
                self.find_drum_kit_names()
            ),
        }

        return result

    # ------------------------------------------------------------------
    # DrumKit model conversion
    # ------------------------------------------------------------------

    def parse(self) -> list[DrumKit]:
        """
        Parsira stvarne Drum Kit nazive iz PA300 USERDK.PCG.

        Svaki pronađeni naziv se pretvara u DrumKit objekt.

        Instruments je trenutno prazan jer MIDI/key mapping
        još nije dovoljno potvrđen da bismo sigurno tvrdili
        da određeni bajt predstavlja određeni instrument.

        Ovo je namjerno konzervativno ponašanje.
        """

        data = self.read_bytes()

        if not data:
            return []

        records = self.find_drum_kit_name_records()

        kits: list[DrumKit] = []

        for record in records:
            kits.append(
                DrumKit(
                    name=record["name"],
                    instruments=[],
                )
            )

        return kits

    # ------------------------------------------------------------------
    # MIDI helper
    # ------------------------------------------------------------------

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
        """

        if not 0 <= midi_note <= 127:
            raise ValueError(
                "midi_note must be between 0 and 127"
            )

        return DrumInstrument(
            midi_note=midi_note,
            note_name=midi_to_note(midi_note),
            name=name,
            program=program,
            bank_msb=bank_msb,
            bank_lsb=bank_lsb,
        )
