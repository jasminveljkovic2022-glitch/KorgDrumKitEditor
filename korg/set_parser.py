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

    #23

    Obraduje:
    - sirove binarne podatke
    - veličinu fajla
    - SHA-256 checksum
    - hex pregled
    - ASCII stringove
    - byte pattern search
    - hexdump
    - KORF blok
    - Drum Kit name records
    - 24-byte Drum Kit records
    - binarnu analizu Drum Kit recorda
    - poređenje Drum Kit recorda
    - automatsku analizu promjena po byte offsetima
    - analizu vjerovatnih MIDI mapping byteova

    VAŽNO:

    Parser NE mijenja originalni PCG/SET fajl.

    Parser NE zapisuje izmjene nazad u Korg fajl.

    MIDI mapping analiza je heuristička.
    Pronađeni byte nije automatski potvrđen kao stvarni
    Korg MIDI mapping.
    """

    # ------------------------------------------------------------------
    # Confirmed structure
    # ------------------------------------------------------------------

    KORF_MAGIC = b"KORF"
    KORF_HEADER_SIZE = 13
    DRUM_KIT_RECORD_SIZE = 24

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    # ------------------------------------------------------------------
    # Validation / raw data
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """
        Provjerava da li ulazni fajl postoji i da li je podržan.
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
        Učitava originalni fajl kao bytes.
        """

        self._validate()

        return self.set_path.read_bytes()

    def raw_bytes(self) -> bytes:
        """
        Alias za read_bytes().
        """

        return self.read_bytes()

    def sha256(self) -> str:
        """
        Vraća SHA-256 checksum fajla.
        """

        return sha256(
            self.read_bytes()
        ).hexdigest()

    def copy_original(
        self,
        destination: str | Path,
    ) -> Path:
        """
        Pravi kopiju originalnog fajla.
        """

        destination_path = Path(destination)

        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        copyfile(
            self.set_path,
            destination_path,
        )

        return destination_path

    # ------------------------------------------------------------------
    # Basic inspection
    # ------------------------------------------------------------------

    def inspect(
        self,
        preview_size: int = 256,
    ) -> dict:
        """
        Osnovna analiza fajla.
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
        Pronalazi ASCII stringove.
        """

        records = (
            self.find_ascii_strings_with_offsets(
                minimum_length=minimum_length
            )
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
        Pronalazi ASCII stringove sa offsetima.
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
                        "text": current.decode(
                            "ascii"
                        ),
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
                    "text": current.decode(
                        "ascii"
                    ),
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
        Pronalazi sva pojavljivanja byte patterna.
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
        Vraća hex dump.
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
                offset
                + relative_offset
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
    # KORF
    # ------------------------------------------------------------------

    def find_korf_offset(
        self,
    ) -> Optional[int]:
        """
        Pronalazi KORF marker.
        """

        data = self.read_bytes()

        offset = data.find(
            self.KORF_MAGIC
        )

        if offset == -1:
            return None

        return offset

    # ------------------------------------------------------------------
    # Drum Kit name records
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_pcg_name(
        record: bytes,
    ) -> str:
        """
        Dekodira naziv Drum Kita.
        """

        raw_name = record.split(
            b"\x00",
            1,
        )[0]

        return raw_name.decode(
            "ascii",
            errors="replace",
        ).strip()

    @staticmethod
    def _is_printable_ascii_name(
        record: bytes,
    ) -> bool:
        """
        Provjerava da li record počinje ASCII nazivom.
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
        Pronalazi Drum Kit name recorde.
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
            offset
            + self.DRUM_KIT_RECORD_SIZE
            <= len(data)
        ):

            record = data[
                offset:
                offset
                + self.DRUM_KIT_RECORD_SIZE
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
                    "size": (
                        self.DRUM_KIT_RECORD_SIZE
                    ),
                    "name": name,
                    "raw": record,
                    "hex": record.hex(" "),
                }
            )

            index += 1

            offset += (
                self.DRUM_KIT_RECORD_SIZE
            )

        return records

    def find_drum_kit_names(
        self,
    ) -> list[str]:
        """
        Vraća samo nazive Drum Kitova.
        """

        return [
            record["name"]
            for record
            in self.find_drum_kit_name_records()
        ]

    def get_drum_kit_name_record(
        self,
        index: int,
    ) -> dict:
        """
        Vraća jedan Drum Kit record.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if index < 0 or index >= len(records):
            raise IndexError(
                f"Drum Kit index out of range: {index}"
            )

        return records[index]

    # ------------------------------------------------------------------
    # #19 - Drum Kit binary record analysis
    # ------------------------------------------------------------------

    def inspect_drum_kit_record(
        self,
        index: int,
    ) -> dict:
        """
        Detaljna analiza jednog Drum Kit recorda.
        """

        record = (
            self.get_drum_kit_name_record(
                index
            )
        )

        raw = record["raw"]

        byte_values = []

        for relative_offset, byte in enumerate(
            raw
        ):

            byte_values.append(
                {
                    "offset": (
                        record["offset"]
                        + relative_offset
                    ),
                    "relative_offset": (
                        relative_offset
                    ),
                    "value": byte,
                    "hex": f"{byte:02X}",
                }
            )

        midi_candidates = []

        for relative_offset, byte in enumerate(
            raw
        ):

            if 0 <= byte <= 127:

                midi_candidates.append(
                    {
                        "relative_offset": (
                            relative_offset
                        ),
                        "value": byte,
                        "hex": f"{byte:02X}",
                        "midi_note": byte,
                        "note_name": midi_to_note(
                            byte
                        ),
                    }
                )

        return {
            "index": record["index"],
            "offset": record["offset"],
            "end_offset": record["end_offset"],
            "size": record["size"],
            "name": record["name"],
            "raw_hex": record["hex"],
            "bytes": byte_values,
            "midi_candidates": midi_candidates,
        }

    def inspect_all_drum_kit_records(
        self,
    ) -> list[dict]:
        """
        Analizira sve Drum Kit recorde.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        return [
            self.inspect_drum_kit_record(
                record["index"]
            )
            for record in records
        ]

    def compare_drum_kit_records(
        self,
        first_index: int,
        second_index: int,
    ) -> dict:
        """
        Uspoređuje dva Drum Kit recorda.
        """

        first = (
            self.get_drum_kit_name_record(
                first_index
            )
        )

        second = (
            self.get_drum_kit_name_record(
                second_index
            )
        )

        first_raw = first["raw"]
        second_raw = second["raw"]

        if len(first_raw) != len(second_raw):
            raise ValueError(
                "Drum Kit records have different sizes"
            )

        differences = []

        for relative_offset, (
            first_byte,
            second_byte,
        ) in enumerate(
            zip(
                first_raw,
                second_raw,
            )
        ):

            if first_byte != second_byte:

                differences.append(
                    {
                        "relative_offset": (
                            relative_offset
                        ),
                        "absolute_offset_first": (
                            first["offset"]
                            + relative_offset
                        ),
                        "absolute_offset_second": (
                            second["offset"]
                            + relative_offset
                        ),
                        "first_value": first_byte,
                        "first_hex": (
                            f"{first_byte:02X}"
                        ),
                        "second_value": second_byte,
                        "second_hex": (
                            f"{second_byte:02X}"
                        ),
                    }
                )

        return {
            "first": {
                "index": first["index"],
                "offset": first["offset"],
                "name": first["name"],
            },
            "second": {
                "index": second["index"],
                "offset": second["offset"],
                "name": second["name"],
            },
            "record_size": len(first_raw),
            "different_bytes": len(differences),
            "identical_bytes": (
                len(first_raw)
                - len(differences)
            ),
            "differences": differences,
        }

    def find_record_byte_variations(
        self,
    ) -> list[dict]:
        """
        Pronalazi byte pozicije koje se razlikuju
        između Drum Kitova.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        variations = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE
        ):

            values = []

            for record in records:

                value = record["raw"][
                    relative_offset
                ]

                if value not in values:
                    values.append(value)

            if len(values) > 1:

                variations.append(
                    {
                        "relative_offset": (
                            relative_offset
                        ),
                        "values": values,
                        "hex_values": [
                            f"{value:02X}"
                            for value in values
                        ],
                        "record_count": len(
                            records
                        ),
                    }
                )

        return variations

    # ------------------------------------------------------------------
    # #20 - Automatic byte analysis
    # ------------------------------------------------------------------

    def analyze_drum_kit_byte_positions(
        self,
    ) -> list[dict]:
        """
        Automatski analizira svaki byte offset
        unutar Drum Kit recorda.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        analysis = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE
        ):

            values: dict[int, list[dict]] = {}

            for record in records:

                value = record["raw"][
                    relative_offset
                ]

                values.setdefault(
                    value,
                    [],
                ).append(
                    {
                        "index": record["index"],
                        "name": record["name"],
                    }
                )

            value_details = []

            for value in sorted(values):

                item = {
                    "value": value,
                    "hex": f"{value:02X}",
                    "count": len(values[value]),
                    "drum_kits": values[value],
                }

                if 0 <= value <= 127:

                    item["midi_note"] = value
                    item["note_name"] = (
                        midi_to_note(value)
                    )

                else:

                    item["midi_note"] = None
                    item["note_name"] = None

                value_details.append(item)

            analysis.append(
                {
                    "relative_offset": (
                        relative_offset
                    ),
                    "unique_value_count": (
                        len(values)
                    ),
                    "changes_between_kits": (
                        len(values) > 1
                    ),
                    "values": value_details,
                }
            )

        return analysis

    def find_likely_variable_byte_positions(
        self,
    ) -> list[dict]:
        """
        Izdvaja byte pozicije koje imaju
        više različitih vrijednosti.
        """

        analysis = (
            self.analyze_drum_kit_byte_positions()
        )

        return [
            item
            for item in analysis
            if item["changes_between_kits"]
        ]

    def summarize_drum_kit_differences(
        self,
    ) -> dict:
        """
        Sažeti pregled promjenjivih byte pozicija.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        variable_positions = (
            self.find_likely_variable_byte_positions()
        )

        return {
            "drum_kit_count": len(records),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "variable_byte_positions": (
                len(variable_positions)
            ),
            "fixed_byte_positions": (
                self.DRUM_KIT_RECORD_SIZE
                - len(variable_positions)
            ),
            "positions": variable_positions,
        }

    # ------------------------------------------------------------------
    # #23 - Likely MIDI mapping analysis
    # ------------------------------------------------------------------

    def find_likely_midi_mapping_bytes(
        self,
    ) -> list[dict]:
        """
        #23

        Pronalazi byte pozicije koje mogu predstavljati
        MIDI note vrijednosti.

        Kandidat mora:

        - biti u MIDI rasponu 0-127
        - mijenjati se između Drum Kitova
        - nalaziti se na istoj relativnoj poziciji
          unutar 24-byte recorda

        VAŽNO:

        Ovo je heuristička analiza.

        Rezultat NE znači da je byte sigurno MIDI mapping.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        candidates: list[dict] = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE
        ):

            values = []

            for record in records:

                value = record["raw"][
                    relative_offset
                ]

                if value not in values:
                    values.append(value)

            # Byte mora biti promjenjiv.
            if len(values) <= 1:
                continue

            # Sve vrijednosti moraju biti
            # validne MIDI vrijednosti.
            if not all(
                0 <= value <= 127
                for value in values
            ):
                continue

            midi_notes = []

            for value in values:

                midi_notes.append(
                    {
                        "value": value,
                        "hex": f"{value:02X}",
                        "note_name": midi_to_note(
                            value
                        ),
                    }
                )

            kit_values = []

            for record in records:

                value = record["raw"][
                    relative_offset
                ]

                kit_values.append(
                    {
                        "index": record["index"],
                        "name": record["name"],
                        "value": value,
                        "hex": f"{value:02X}",
                        "note_name": midi_to_note(
                            value
                        ),
                    }
                )

            candidates.append(
                {
                    "relative_offset": (
                        relative_offset
                    ),
                    "unique_values": len(values),
                    "values": values,
                    "hex_values": [
                        f"{value:02X}"
                        for value in values
                    ],
                    "midi_notes": midi_notes,
                    "drum_kits": kit_values,
                }
            )

        return candidates

    def summarize_likely_midi_mapping(
        self,
    ) -> dict:
        """
        #23

        Sažetak mogućih MIDI mapping byte pozicija.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        candidates = (
            self.find_likely_midi_mapping_bytes()
        )

        return {
            "drum_kit_count": len(records),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "candidate_count": len(candidates),
            "candidate_offsets": [
                candidate["relative_offset"]
                for candidate in candidates
            ],
            "candidates": candidates,
        }

    # ------------------------------------------------------------------
    # Combined Drum Kit analysis
    # ------------------------------------------------------------------

    def inspect_drum_kit_binary_structure(
        self,
    ) -> dict:
        """
        Kombinovana analiza Drum Kit strukture.
        """

        records = (
            self.inspect_all_drum_kit_records()
        )

        return {
            "format": "PA300 USERDK.PCG",
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "record_count": len(records),
            "records": records,
            "byte_variations": (
                self.find_record_byte_variations()
            ),
            "automatic_byte_analysis": (
                self.analyze_drum_kit_byte_positions()
            ),
            "likely_variable_positions": (
                self.find_likely_variable_byte_positions()
            ),
            "likely_midi_mapping_bytes": (
                self.find_likely_midi_mapping_bytes()
            ),
            "midi_mapping_summary": (
                self.summarize_likely_midi_mapping()
            ),
            "difference_summary": (
                self.summarize_drum_kit_differences()
            ),
        }

    # ------------------------------------------------------------------
    # Structural inspection
    # ------------------------------------------------------------------

    def inspect_userdk_pcg(
        self,
    ) -> dict:
        """
        Detaljna analiza USERDK.PCG.
        """

        data = self.read_bytes()

        korf_offset = self.find_korf_offset()

        records = (
            self.find_drum_kit_name_records()
        )

        return {
            "path": str(self.set_path),
            "size": len(data),
            "sha256": self.sha256(),
            "format": "PA300 USERDK.PCG",
            "korf": {
                "magic": (
                    self.KORF_MAGIC.decode(
                        "ascii"
                    )
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
                "record_size": (
                    self.DRUM_KIT_RECORD_SIZE
                ),
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
            "drum_kit_binary_analysis": (
                self.inspect_drum_kit_binary_structure()
            ),
        }

    def inspect_structure(
        self,
        preview_size: int = 256,
        minimum_string_length: int = 4,
    ) -> dict:
        """
        Objedinjeni structural inspection.

        Uključuje #20 i #23 analizu.
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

        return {
            "path": str(self.set_path),
            "size": len(data),
            "sha256": self.sha256(),
            "preview": {
                "size": len(preview),
                "hex": preview.hex(" "),
            },
            "ascii_strings": (
                self.find_ascii_strings_with_offsets(
                    minimum_length=(
                        minimum_string_length
                    )
                )
            ),
            "korf_offset": (
                self.find_korf_offset()
            ),
            "drum_kit_names": (
                self.find_drum_kit_names()
            ),
            "drum_kit_binary_analysis": (
                self.inspect_drum_kit_binary_structure()
            ),
        }

    # ------------------------------------------------------------------
    # DrumKit model conversion
    # ------------------------------------------------------------------

    def parse(self) -> list[DrumKit]:
        """
        Parsira Drum Kit nazive.

        Instruments ostaje prazan dok stvarni mapping
        ne bude potvrđen.
        """

        data = self.read_bytes()

        if not data:
            return []

        records = (
            self.find_drum_kit_name_records()
        )

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
        Kreira DrumInstrument.
        """

        if not 0 <= midi_note <= 127:
            raise ValueError(
                "midi_note must be between 0 and 127"
            )

        return DrumInstrument(
            midi_note=midi_note,
            note_name=midi_to_note(
                midi_note
            ),
            name=name,
            program=program,
            bank_msb=bank_msb,
            bank_lsb=bank_lsb,
        )
