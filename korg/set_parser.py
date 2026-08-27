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

    #21

    Nastavak na #20.

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
    - MIDI candidate analysis
    - MIDI candidate scoring

    VAŽNO:

    Parser NE mijenja originalni PCG/SET fajl.

    Parser NE zapisuje izmjene nazad u Korg fajl.

    #21 NE tvrdi da je pronađeni MIDI kandidat
    stvarni Korg Drum Kit mapping.

    #21 samo rangira moguće MIDI vrijednosti
    na osnovu njihove pozicije i ponašanja između
    Drum Kit recorda.
    """

    KORF_MAGIC = b"KORF"
    KORF_HEADER_SIZE = 13
    DRUM_KIT_RECORD_SIZE = 24

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    # ------------------------------------------------------------------
    # Validation / raw data
    # ------------------------------------------------------------------

    def _validate(self) -> None:
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
        self._validate()
        return self.set_path.read_bytes()

    def raw_bytes(self) -> bytes:
        return self.read_bytes()

    def sha256(self) -> str:
        return sha256(
            self.read_bytes()
        ).hexdigest()

    def copy_original(
        self,
        destination: str | Path,
    ) -> Path:
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

        return [
            record["name"]
            for record
            in self.find_drum_kit_name_records()
        ]

    def get_drum_kit_name_record(
        self,
        index: int,
    ) -> dict:

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

        records = (
            self.find_drum_kit_name_records()
        )

        return [
            self.inspect_drum_kit_record(
                record["index"]
            )
            for record in records
        ]

    # ------------------------------------------------------------------
    # Record comparison
    # ------------------------------------------------------------------

    def compare_drum_kit_records(
        self,
        first_index: int,
        second_index: int,
    ) -> dict:

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

    # ------------------------------------------------------------------
    # #20 - Automatic byte analysis
    # ------------------------------------------------------------------

    def find_record_byte_variations(
        self,
    ) -> list[dict]:

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

    def analyze_drum_kit_byte_positions(
        self,
    ) -> list[dict]:

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
    # #21 - MIDI candidate analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _midi_candidate_score(
        relative_offset: int,
        value: int,
        unique_value_count: int,
        record_count: int,
    ) -> int:
        """
        #21

        Daje heuristički score MIDI kandidatu.

        Ovo NIJE dokaz da je vrijednost stvarni
        MIDI mapping.

        Score povećava:
        - MIDI vrijednost 0-127
        - promjenjivi byte
        - umjeren broj različitih vrijednosti
        - vrijednosti koje nisu dio ASCII imena
        """

        score = 0

        if 0 <= value <= 127:
            score += 10

        if unique_value_count > 1:
            score += 5

        if 0 < relative_offset < 24:
            score += 1

        if unique_value_count <= record_count:
            score += 1

        # ASCII slova/brojevi su češće dio imena,
        # pa ih ne favorizujemo kao MIDI kandidat.
        if 32 <= value <= 126:
            score -= 2

        # Tipične MIDI note vrijednosti.
        if 24 <= value <= 108:
            score += 2

        return score

    def analyze_midi_candidates(
        self,
    ) -> list[dict]:
        """
        #21

        Analizira sve promjenjive byte pozicije
        i pravi listu mogućih MIDI kandidata.

        Rezultat je sortiran po score vrijednosti.

        NE tvrdi da je kandidat stvarni Korg mapping.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        analysis = (
            self.analyze_drum_kit_byte_positions()
        )

        candidates: list[dict] = []

        for position in analysis:

            if not position[
                "changes_between_kits"
            ]:
                continue

            relative_offset = position[
                "relative_offset"
            ]

            unique_value_count = position[
                "unique_value_count"
            ]

            for value_info in position[
                "values"
            ]:

                value = value_info[
                    "value"
                ]

                if not 0 <= value <= 127:
                    continue

                score = (
                    self._midi_candidate_score(
                        relative_offset=(
                            relative_offset
                        ),
                        value=value,
                        unique_value_count=(
                            unique_value_count
                        ),
                        record_count=len(records),
                    )
                )

                candidates.append(
                    {
                        "relative_offset": (
                            relative_offset
                        ),
                        "value": value,
                        "hex": f"{value:02X}",
                        "midi_note": value,
                        "note_name": (
                            midi_to_note(value)
                        ),
                        "unique_value_count": (
                            unique_value_count
                        ),
                        "drum_kit_count": (
                            len(records)
                        ),
                        "used_by_count": (
                            value_info["count"]
                        ),
                        "drum_kits": (
                            value_info["drum_kits"]
                        ),
                        "score": score,
                    }
                )

        candidates.sort(
            key=lambda item: (
                -item["score"],
                item["relative_offset"],
                item["value"],
            )
        )

        return candidates

    def find_top_midi_candidates(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """
        Vraća najbolje MIDI kandidate.
        """

        if limit < 1:
            raise ValueError(
                "limit must be greater than 0"
            )

        candidates = (
            self.analyze_midi_candidates()
        )

        return candidates[:limit]

    def analyze_midi_candidates_by_offset(
        self,
    ) -> dict[int, list[dict]]:
        """
        Grupira MIDI kandidate po byte offsetu.
        """

        candidates = (
            self.analyze_midi_candidates()
        )

        grouped: dict[int, list[dict]] = {}

        for candidate in candidates:

            offset = candidate[
                "relative_offset"
            ]

            grouped.setdefault(
                offset,
                [],
            ).append(candidate)

        return grouped

    def summarize_midi_candidates(
        self,
    ) -> dict:
        """
        Sažetak #21 MIDI analize.
        """

        records = (
            self.find_drum_kit_name_records()
        )

        candidates = (
            self.analyze_midi_candidates()
        )

        offsets = sorted(
            {
                candidate[
                    "relative_offset"
                ]
                for candidate in candidates
            }
        )

        return {
            "drum_kit_count": len(records),
            "candidate_count": len(candidates),
            "candidate_offsets": offsets,
            "top_candidates": candidates[:20],
        }

    # ------------------------------------------------------------------
    # Combined Drum Kit analysis
    # ------------------------------------------------------------------

    def inspect_drum_kit_binary_structure(
        self,
    ) -> dict:

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
            "difference_summary": (
                self.summarize_drum_kit_differences()
            ),
            "midi_candidate_analysis": (
                self.summarize_midi_candidates()
            ),
        }

    # ------------------------------------------------------------------
    # Structural inspection
    # ------------------------------------------------------------------

    def inspect_userdk_pcg(
        self,
    ) -> dict:

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
