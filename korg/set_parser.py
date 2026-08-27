from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from shutil import copyfile
from typing import Optional

from .midi import midi_to_note
from .models import DrumInstrument, DrumKit


class KorgSetParser:
    """
    PA300 SET / PCG binary parser and inspector.

    #27

    Nastavak na #26.

    Dodano:
    - napredna analiza stvarnog MIDI mapping kandidata
    - razlikovanje name byteova od mogućih mapping byteova
    - analiza MIDI vrijednosti kroz sve Drum Kitove
    - analiza promjena po istoj byte poziciji
    - analiza note -> offset -> Drum Kit
    - analiza offset -> note -> Drum Kit
    - confidence scoring 0-100
    - ranking najvjerovatnijih MIDI mapping pozicija
    - detekcija stabilnih MIDI pozicija
    - detekcija pozicija koje se mijenjaju između kitova
    - cross-kit MIDI mapping comparison
    - detaljan MIDI mapping report
    - candidate mapping tabela
    - analiza frekvencije MIDI vrijednosti
    - heurističko razlikovanje tekstualnih i numeričkih byteova
    - zaštita od automatskog zaključivanja da je kandidat stvarni Korg mapping

    VAŽNO:
    Parser NE mijenja originalni PCG/SET fajl.

    Ova verzija radi analizu binarne strukture i traži
    najvjerovatnije MIDI mapping podatke.

    MIDI mapping kandidati su HEURISTIČKI.
    Potrebna je potvrda poređenjem sa poznatim Korg
    Drum Kit fajlovima ili stvarnim MIDI ponašanjem PA300.
    """

    KORF_MAGIC = b"KORF"
    KORF_HEADER_SIZE = 13
    DRUM_KIT_RECORD_SIZE = 24

    MIDI_MIN = 0
    MIDI_MAX = 127

    # Vrijednosti koje su često manje korisne kao MIDI-note kandidati
    # kada se pojavljuju u tekstualnom području.
    ASCII_MIN = 32
    ASCII_MAX = 126

    # ---------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------

    def __init__(self, set_path: str | Path):
        self.set_path = Path(set_path)

    # ---------------------------------------------------------------
    # Validation / raw data
    # ---------------------------------------------------------------

    def _validate(self) -> None:
        if not self.set_path.exists():
            raise FileNotFoundError(
                f"SET/PCG file does not exist: {self.set_path}"
            )

        if not self.set_path.is_file():
            raise ValueError(
                f"SET/PCG path is not a file: {self.set_path}"
            )

        if self.set_path.suffix.lower() not in {".set", ".pcg"}:
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

    # ---------------------------------------------------------------
    # Basic inspection
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # ASCII strings
    # ---------------------------------------------------------------

    def find_ascii_strings(
        self,
        minimum_length: int = 4,
    ) -> list[str]:

        return [
            item["text"]
            for item
            in self.find_ascii_strings_with_offsets(
                minimum_length=minimum_length
            )
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

        strings = []
        current = bytearray()
        start_offset: Optional[int] = None

        for offset, byte in enumerate(data):

            if self.ASCII_MIN <= byte <= self.ASCII_MAX:

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

    # ---------------------------------------------------------------
    # Byte pattern search
    # ---------------------------------------------------------------

    def find_byte_pattern(
        self,
        pattern: bytes,
    ) -> list[int]:

        if not pattern:
            raise ValueError(
                "pattern must not be empty"
            )

        data = self.read_bytes()

        offsets = []
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

    # ---------------------------------------------------------------
    # Hex dump
    # ---------------------------------------------------------------

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

        lines = []

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
                if self.ASCII_MIN <= byte <= self.ASCII_MAX
                else "."
                for byte in line
            )

            lines.append(
                f"{absolute_offset:08X}  "
                f"{hex_part:<{bytes_per_line * 3 - 1}}  "
                f"{ascii_part}"
            )

        return "\n".join(lines)

    # ---------------------------------------------------------------
    # KORF
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Drum Kit records
    # ---------------------------------------------------------------

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

        records = []

        offset = first_record_offset
        index = 0

        while (
            offset
            + self.DRUM_KIT_RECORD_SIZE
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

    # ---------------------------------------------------------------
    # MIDI helpers
    # ---------------------------------------------------------------

    @staticmethod
    def is_midi_value(
        value: int,
    ) -> bool:
        return (
            KorgSetParser.MIDI_MIN
            <= value
            <= KorgSetParser.MIDI_MAX
        )

    @staticmethod
    def midi_candidate(
        value: int,
        relative_offset: int,
        absolute_offset: Optional[int] = None,
    ) -> Optional[dict]:

        if not KorgSetParser.is_midi_value(
            value
        ):
            return None

        result = {
            "relative_offset": relative_offset,
            "value": value,
            "hex": f"{value:02X}",
            "midi_note": value,
            "note_name": midi_to_note(value),
        }

        if absolute_offset is not None:
            result["absolute_offset"] = absolute_offset

        return result

    # ---------------------------------------------------------------
    # Binary record analysis
    # ---------------------------------------------------------------

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

        for relative_offset, byte in enumerate(raw):

            byte_values.append(
                {
                    "offset": (
                        record["offset"]
                        + relative_offset
                    ),
                    "relative_offset": relative_offset,
                    "value": byte,
                    "hex": f"{byte:02X}",
                }
            )

        midi_candidates = []

        for relative_offset, byte in enumerate(raw):

            candidate = self.midi_candidate(
                value=byte,
                relative_offset=relative_offset,
                absolute_offset=(
                    record["offset"]
                    + relative_offset
                ),
            )

            if candidate is not None:
                midi_candidates.append(
                    candidate
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

    # ---------------------------------------------------------------
    # Compare records
    # ---------------------------------------------------------------

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
                        "relative_offset": relative_offset,
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

    # ---------------------------------------------------------------
    # Byte variations
    # ---------------------------------------------------------------

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
                        "relative_offset": relative_offset,
                        "values": values,
                        "hex_values": [
                            f"{value:02X}"
                            for value in values
                        ],
                        "record_count": len(records),
                    }
                )

        return variations

    # ---------------------------------------------------------------
    # Automatic byte analysis
    # ---------------------------------------------------------------

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

                if self.is_midi_value(value):

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
                    "relative_offset": relative_offset,
                    "unique_value_count": len(values),
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
            "record_size": self.DRUM_KIT_RECORD_SIZE,
            "variable_byte_positions": (
                len(variable_positions)
            ),
            "fixed_byte_positions": (
                self.DRUM_KIT_RECORD_SIZE
                - len(variable_positions)
            ),
            "positions": variable_positions,
        }

    # ---------------------------------------------------------------
    # MIDI candidate analysis
    # ---------------------------------------------------------------

    def find_midi_candidates_for_drum_kit(
        self,
        index: int,
    ) -> list[dict]:

        record = (
            self.get_drum_kit_name_record(
                index
            )
        )

        candidates = []

        for relative_offset, value in enumerate(
            record["raw"]
        ):

            candidate = self.midi_candidate(
                value=value,
                relative_offset=relative_offset,
                absolute_offset=(
                    record["offset"]
                    + relative_offset
                ),
            )

            if candidate is not None:
                candidates.append(
                    candidate
                )

        return candidates

    def analyze_midi_candidates(
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

            values = []

            for record in records:

                value = record["raw"][
                    relative_offset
                ]

                if self.is_midi_value(value):

                    if value not in values:
                        values.append(value)

            candidates = []

            for value in sorted(values):

                drum_kits = []

                for record in records:

                    record_value = record["raw"][
                        relative_offset
                    ]

                    if record_value == value:

                        drum_kits.append(
                            {
                                "index": record["index"],
                                "name": record["name"],
                            }
                        )

                candidates.append(
                    {
                        "value": value,
                        "hex": f"{value:02X}",
                        "midi_note": value,
                        "note_name": midi_to_note(value),
                        "drum_kits": drum_kits,
                        "count": len(drum_kits),
                    }
                )

            analysis.append(
                {
                    "relative_offset": relative_offset,
                    "candidate_count": len(candidates),
                    "candidates": candidates,
                }
            )

        return analysis

    # ---------------------------------------------------------------
    # MIDI frequency
    # ---------------------------------------------------------------

    def midi_value_frequency(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        counter: Counter[int] = Counter()

        for record in records:

            for value in record["raw"]:

                if self.is_midi_value(value):
                    counter[value] += 1

        result = []

        for value, count in sorted(
            counter.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        ):

            result.append(
                {
                    "value": value,
                    "hex": f"{value:02X}",
                    "midi_note": value,
                    "note_name": midi_to_note(value),
                    "count": count,
                }
            )

        return result

    # ---------------------------------------------------------------
    # Per-position statistics
    # ---------------------------------------------------------------

    def analyze_midi_position_statistics(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        total_kits = len(records)
        result = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE
        ):

            values = [
                record["raw"][relative_offset]
                for record in records
            ]

            unique_values = sorted(
                set(values)
            )

            midi_values = [
                value
                for value in values
                if self.is_midi_value(value)
            ]

            non_midi_values = [
                value
                for value in values
                if not self.is_midi_value(value)
            ]

            frequency = Counter(values)

            most_common_value = (
                frequency.most_common(1)[0]
                if frequency
                else (None, 0)
            )

            midi_coverage = (
                len(midi_values) / total_kits * 100
                if total_kits
                else 0
            )

            stability = (
                100 / len(unique_values)
                if unique_values
                else 0
            )

            result.append(
                {
                    "relative_offset": relative_offset,
                    "total_kits": total_kits,
                    "unique_value_count": (
                        len(unique_values)
                    ),
                    "unique_values": unique_values,
                    "hex_values": [
                        f"{value:02X}"
                        for value in unique_values
                    ],
                    "midi_value_count": (
                        len(midi_values)
                    ),
                    "non_midi_value_count": (
                        len(non_midi_values)
                    ),
                    "midi_coverage_percent": round(
                        midi_coverage,
                        2,
                    ),
                    "stability_percent": round(
                        stability,
                        2,
                    ),
                    "changes_between_kits": (
                        len(unique_values) > 1
                    ),
                    "most_common_value": (
                        most_common_value[0]
                    ),
                    "most_common_count": (
                        most_common_value[1]
                    ),
                }
            )

        return result

    # ---------------------------------------------------------------
    # Name-byte detection
    # ---------------------------------------------------------------

    def analyze_name_byte_positions(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        result = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE
        ):

            values = [
                record["raw"][relative_offset]
                for record in records
            ]

            printable_count = sum(
                self.ASCII_MIN <= value <= self.ASCII_MAX
                for value in values
            )

            zero_count = values.count(0)

            printable_percent = (
                printable_count
                / len(values)
                * 100
                if values
                else 0
            )

            zero_percent = (
                zero_count
                / len(values)
                * 100
                if values
                else 0
            )

            likely_name_byte = (
                printable_percent >= 70
                or zero_percent >= 70
            )

            result.append(
                {
                    "relative_offset": relative_offset,
                    "printable_count": printable_count,
                    "printable_percent": round(
                        printable_percent,
                        2,
                    ),
                    "zero_count": zero_count,
                    "zero_percent": round(
                        zero_percent,
                        2,
                    ),
                    "likely_name_byte": (
                        likely_name_byte
                    ),
                }
            )

        return result

    # ---------------------------------------------------------------
    # MIDI position confidence
    # ---------------------------------------------------------------

    def score_midi_position(
        self,
        relative_offset: int,
    ) -> dict:

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return {
                "relative_offset": relative_offset,
                "score": 0,
                "confidence": "VERY_LOW",
            }

        if not (
            0 <= relative_offset
            < self.DRUM_KIT_RECORD_SIZE
        ):
            raise ValueError(
                "relative_offset is outside Drum Kit record"
            )

        values = [
            record["raw"][relative_offset]
            for record in records
        ]

        total = len(values)

        midi_count = sum(
            self.is_midi_value(value)
            for value in values
        )

        printable_count = sum(
            self.ASCII_MIN <= value <= self.ASCII_MAX
            for value in values
        )

        unique_values = len(set(values))

        midi_coverage = (
            midi_count / total * 100
            if total
            else 0
        )

        printable_percent = (
            printable_count / total * 100
            if total
            else 0
        )

        # Base score:
        # MIDI coverage
        score = midi_coverage * 0.45

        # Position should ideally change between kits.
        if unique_values > 1:
            score += 20

        # Avoid positions which are overwhelmingly ASCII.
        if printable_percent < 30:
            score += 15
        elif printable_percent < 60:
            score += 5
        else:
            score -= 15

        # Avoid positions which are always zero.
        if len(set(values)) == 1:
            if values[0] == 0:
                score -= 25

        # More than one value is more interesting for mapping.
        if unique_values >= 2:
            score += 5

        if unique_values >= 4:
            score += 5

        score = max(
            0,
            min(
                100,
                round(score, 2),
            ),
        )

        if score >= 80:
            confidence = "HIGH"
        elif score >= 60:
            confidence = "MEDIUM"
        elif score >= 40:
            confidence = "LOW"
        else:
            confidence = "VERY_LOW"

        return {
            "relative_offset": relative_offset,
            "score": score,
            "confidence": confidence,
            "total_kits": total,
            "midi_count": midi_count,
            "midi_coverage_percent": round(
                midi_coverage,
                2,
            ),
            "printable_count": printable_count,
            "printable_percent": round(
                printable_percent,
                2,
            ),
            "unique_value_count": unique_values,
            "values": sorted(
                set(values)
            ),
            "hex_values": [
                f"{value:02X}"
                for value in sorted(set(values))
            ],
        }

    def rank_midi_positions(
        self,
    ) -> list[dict]:

        result = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE
        ):

            result.append(
                self.score_midi_position(
                    relative_offset
                )
            )

        return sorted(
            result,
            key=lambda item: (
                -item["score"],
                item["relative_offset"],
            ),
        )

    def find_top_midi_positions(
        self,
        limit: int = 10,
    ) -> list[dict]:

        if limit < 1:
            raise ValueError(
                "limit must be greater than 0"
            )

        return self.rank_midi_positions()[
            :limit
        ]

    # ---------------------------------------------------------------
    # Detailed mapping candidates
    # ---------------------------------------------------------------

    def find_detailed_mapping_candidates(
        self,
        minimum_score: float = 40,
    ) -> list[dict]:

        if not 0 <= minimum_score <= 100:
            raise ValueError(
                "minimum_score must be between 0 and 100"
            )

        records = (
            self.find_drum_kit_name_records()
        )

        rankings = self.rank_midi_positions()

        candidates = []

        for ranking in rankings:

            if ranking["score"] < minimum_score:
                continue

            relative_offset = ranking[
                "relative_offset"
            ]

            for record in records:

                value = record["raw"][
                    relative_offset
                ]

                if not self.is_midi_value(
                    value
                ):
                    continue

                candidates.append(
                    {
                        "drum_kit_index": (
                            record["index"]
                        ),
                        "drum_kit_name": (
                            record["name"]
                        ),
                        "relative_offset": (
                            relative_offset
                        ),
                        "absolute_offset": (
                            record["offset"]
                            + relative_offset
                        ),
                        "value": value,
                        "hex": f"{value:02X}",
                        "midi_note": value,
                        "note_name": (
                            midi_to_note(value)
                        ),
                        "position_score": (
                            ranking["score"]
                        ),
                        "confidence": (
                            ranking["confidence"]
                        ),
                    }
                )

        return candidates

    # ---------------------------------------------------------------
    # Note -> offset -> Drum Kit
    # ---------------------------------------------------------------

    def build_note_mapping_index(
        self,
        minimum_score: float = 40,
    ) -> dict[str, list[dict]]:

        candidates = (
            self.find_detailed_mapping_candidates(
                minimum_score=minimum_score
            )
        )

        result: dict[str, list[dict]] = {}

        for candidate in candidates:

            note = candidate["note_name"]

            result.setdefault(
                note,
                [],
            ).append(
                candidate
            )

        return result

    # ---------------------------------------------------------------
    # Offset -> note -> Drum Kit
    # ---------------------------------------------------------------

    def build_offset_mapping_index(
        self,
        minimum_score: float = 40,
    ) -> dict[int, list[dict]]:

        candidates = (
            self.find_detailed_mapping_candidates(
                minimum_score=minimum_score
            )
        )

        result: dict[int, list[dict]] = {}

        for candidate in candidates:

            offset = candidate[
                "relative_offset"
            ]

            result.setdefault(
                offset,
                [],
            ).append(
                candidate
            )

        return result

    # ---------------------------------------------------------------
    # Cross-kit MIDI comparison
    # ---------------------------------------------------------------

    def compare_midi_position_across_kits(
        self,
        relative_offset: int,
    ) -> dict:

        records = (
            self.find_drum_kit_name_records()
        )

        if not (
            0 <= relative_offset
            < self.DRUM_KIT_RECORD_SIZE
        ):
            raise ValueError(
                "relative_offset is outside Drum Kit record"
            )

        kits = []

        for record in records:

            value = record["raw"][
                relative_offset
            ]

            kits.append(
                {
                    "index": record["index"],
                    "name": record["name"],
                    "value": value,
                    "hex": f"{value:02X}",
                    "is_midi": (
                        self.is_midi_value(value)
                    ),
                    "midi_note": (
                        value
                        if self.is_midi_value(value)
                        else None
                    ),
                    "note_name": (
                        midi_to_note(value)
                        if self.is_midi_value(value)
                        else None
                    ),
                }
            )

        return {
            "relative_offset": relative_offset,
            "kits": kits,
        }

    def compare_all_midi_positions(
        self,
        minimum_score: float = 40,
    ) -> list[dict]:

        rankings = self.rank_midi_positions()

        result = []

        for ranking in rankings:

            if ranking["score"] < minimum_score:
                continue

            comparison = (
                self.compare_midi_position_across_kits(
                    ranking["relative_offset"]
                )
            )

            comparison["score"] = ranking["score"]
            comparison["confidence"] = (
                ranking["confidence"]
            )

            result.append(
                comparison
            )

        return result

    # ---------------------------------------------------------------
    # Stable MIDI positions
    # ---------------------------------------------------------------

    def find_stable_midi_positions(
        self,
        minimum_coverage: float = 90,
    ) -> list[dict]:

        if not 0 <= minimum_coverage <= 100:
            raise ValueError(
                "minimum_coverage must be between 0 and 100"
            )

        statistics = (
            self.analyze_midi_position_statistics()
        )

        result = []

        for item in statistics:

            if (
                item["midi_coverage_percent"]
                >= minimum_coverage
            ):
                result.append(
                    item
                )

        return result

    # ---------------------------------------------------------------
    # Variable MIDI positions
    # ---------------------------------------------------------------

    def find_variable_midi_positions(
        self,
    ) -> list[dict]:

        statistics = (
            self.analyze_midi_position_statistics()
        )

        return [
            item
            for item in statistics
            if (
                item["midi_value_count"] > 0
                and item["unique_value_count"] > 1
            )
        ]

    # ---------------------------------------------------------------
    # Most variable MIDI positions
    # ---------------------------------------------------------------

    def find_most_variable_midi_positions(
        self,
    ) -> list[dict]:

        analysis = (
            self.analyze_midi_candidates()
        )

        return sorted(
            analysis,
            key=lambda item: (
                -item["candidate_count"],
                item["relative_offset"],
            ),
        )

    # ---------------------------------------------------------------
    # MIDI mapping summary
    # ---------------------------------------------------------------

    def summarize_midi_analysis(
        self,
    ) -> dict:

        records = (
            self.find_drum_kit_name_records()
        )

        analysis = (
            self.analyze_midi_candidates()
        )

        positions_with_candidates = [
            item
            for item in analysis
            if item["candidate_count"] > 0
        ]

        variable_positions = [
            item
            for item in analysis
            if item["candidate_count"] > 1
        ]

        unique_midi_values = set()

        for item in analysis:

            for candidate in item["candidates"]:

                unique_midi_values.add(
                    candidate["value"]
                )

        return {
            "drum_kit_count": len(records),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "positions_analyzed": (
                len(analysis)
            ),
            "positions_with_midi_candidates": (
                len(positions_with_candidates)
            ),
            "variable_midi_positions": (
                len(variable_positions)
            ),
            "unique_midi_values": (
                len(unique_midi_values)
            ),
            "midi_values": sorted(
                unique_midi_values
            ),
            "positions": analysis,
        }

    # ---------------------------------------------------------------
    # #26 compatibility summary
    # ---------------------------------------------------------------

    def summarize_midi_mapping_candidates(
        self,
        minimum_score: float = 40,
    ) -> dict:

        rankings = (
            self.rank_midi_positions()
        )

        candidates = (
            self.find_detailed_mapping_candidates(
                minimum_score=minimum_score
            )
        )

        return {
            "minimum_score": minimum_score,
            "ranked_positions": rankings,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "top_positions": rankings[:10],
        }

    # ---------------------------------------------------------------
    # Full MIDI mapping report
    # ---------------------------------------------------------------

    def analyze_real_midi_mapping(
        self,
        minimum_score: float = 40,
        top_positions: int = 10,
    ) -> dict:

        if top_positions < 1:
            raise ValueError(
                "top_positions must be greater than 0"
            )

        records = (
            self.find_drum_kit_name_records()
        )

        rankings = (
            self.rank_midi_positions()
        )

        top = rankings[
            :top_positions
        ]

        candidates = (
            self.find_detailed_mapping_candidates(
                minimum_score=minimum_score
            )
        )

        note_index = (
            self.build_note_mapping_index(
                minimum_score=minimum_score
            )
        )

        offset_index = (
            self.build_offset_mapping_index(
                minimum_score=minimum_score
            )
        )

        return {
            "format": "PA300 USERDK.PCG",
            "drum_kit_count": len(records),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "minimum_score": minimum_score,
            "top_positions": top,
            "all_ranked_positions": rankings,
            "mapping_candidate_count": len(
                candidates
            ),
            "mapping_candidates": candidates,
            "note_to_mapping": note_index,
            "offset_to_mapping": offset_index,
            "stable_midi_positions": (
                self.find_stable_midi_positions()
            ),
            "variable_midi_positions": (
                self.find_variable_midi_positions()
            ),
            "midi_value_frequency": (
                self.midi_value_frequency()
            ),
            "name_byte_analysis": (
                self.analyze_name_byte_positions()
            ),
            "warning": (
                "MIDI mapping candidates are heuristic "
                "and are not automatically confirmed "
                "as real Korg Drum Kit assignments."
            ),
        }

    # ---------------------------------------------------------------
    # Combined binary structure
    # ---------------------------------------------------------------

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
            "midi_analysis": (
                self.summarize_midi_analysis()
            ),
            "midi_mapping_candidates": (
                self.summarize_midi_mapping_candidates()
            ),
            "real_midi_mapping_analysis": (
                self.analyze_real_midi_mapping()
            ),
        }

    # ---------------------------------------------------------------
    # USERDK inspection
    # ---------------------------------------------------------------

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
            "midi_analysis": (
                self.summarize_midi_analysis()
            ),
            "real_midi_mapping": (
                self.analyze_real_midi_mapping()
            ),
        }

    # ---------------------------------------------------------------
    # General structure
    # ---------------------------------------------------------------

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
            "midi_analysis": (
                self.summarize_midi_analysis()
            ),
            "real_midi_mapping": (
                self.analyze_real_midi_mapping()
            ),
        }

    # ---------------------------------------------------------------
    # DrumKit model conversion
    # ---------------------------------------------------------------

    def parse(self) -> list[DrumKit]:

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

    # ---------------------------------------------------------------
    # MIDI helper
    # ---------------------------------------------------------------

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
