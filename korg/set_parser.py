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

    #29

    Nastavak na #28.

    Dodano:
    - analiza susjednih byteova
    - analiza byte parova
    - analiza byte tripleta
    - detekcija sekvencijalnih MIDI vrijednosti
    - detekcija MIDI raspona
    - analiza pozicijske stabilnosti
    - analiza korelacije između Drum Kitova
    - rangiranje mogućih mapping blokova
    - analiza mogućih MIDI mapping područja
    - prošireni MIDI mapping report

    VAŽNO:
    Parser NE mijenja originalni PCG/SET fajl.

    MIDI mapping kandidati nisu automatski potvrđeni kao
    stvarni Korg Drum Kit mapping.

    Analiza predstavlja strukturalnu analizu binarnog fajla.
    """

    KORF_MAGIC = b"KORF"
    KORF_HEADER_SIZE = 13
    DRUM_KIT_RECORD_SIZE = 24

    # ---------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------

    def __init__(
        self,
        set_path: str | Path,
    ):
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

        if self.set_path.suffix.lower() not in {
            ".set",
            ".pcg",
        }:
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
    # MIDI helper
    # ---------------------------------------------------------------

    @staticmethod
    def is_midi_value(
        value: int,
    ) -> bool:

        return 0 <= value <= 127

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

        for relative_offset, byte in enumerate(
            raw
        ):

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

        for relative_offset, byte in enumerate(
            raw
        ):

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

                if self.is_midi_value(
                    value
                ):

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

    # ---------------------------------------------------------------
    # MIDI candidates
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
                candidates.append(candidate)

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

                if self.is_midi_value(
                    value
                ):

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
                        "note_name": midi_to_note(
                            value
                        ),
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

    def find_most_variable_midi_positions(
        self,
    ) -> list[dict]:

        analysis = (
            self.analyze_midi_candidates()
        )

        return sorted(
            analysis,
            key=lambda item: item[
                "candidate_count"
            ],
            reverse=True,
        )

    # ---------------------------------------------------------------
    # MIDI scoring
    # ---------------------------------------------------------------

    @staticmethod
    def _midi_range_score(
        midi_note: int,
    ) -> float:

        if not 0 <= midi_note <= 127:
            return 0.0

        if 24 <= midi_note <= 96:
            return 1.0

        if 12 <= midi_note <= 108:
            return 0.75

        return 0.5

    @staticmethod
    def _frequency_score(
        count: int,
        total: int,
    ) -> float:

        if total <= 0:
            return 0.0

        ratio = count / total

        if ratio >= 0.75:
            return 1.0

        if ratio >= 0.50:
            return 0.8

        if ratio >= 0.25:
            return 0.6

        if ratio > 0:
            return 0.4

        return 0.0

    @staticmethod
    def _variation_score(
        candidate_count: int,
    ) -> float:

        if candidate_count <= 1:
            return 0.35

        if candidate_count == 2:
            return 0.60

        if candidate_count <= 4:
            return 0.80

        if candidate_count <= 8:
            return 0.95

        return 1.0

    def score_midi_candidate(
        self,
        relative_offset: int,
        value: int,
        candidate_count: int,
        occurrence_count: int,
        total_drum_kits: int,
    ) -> dict:

        range_score = (
            self._midi_range_score(
                value
            )
        )

        frequency_score = (
            self._frequency_score(
                occurrence_count,
                total_drum_kits,
            )
        )

        variation_score = (
            self._variation_score(
                candidate_count
            )
        )

        position_variability = (
            1.0
            if candidate_count > 1
            else 0.25
        )

        weighted_score = (
            range_score * 25.0
            + frequency_score * 35.0
            + variation_score * 20.0
            + position_variability * 20.0
        )

        return {
            "relative_offset": relative_offset,
            "value": value,
            "hex": f"{value:02X}",
            "midi_note": value,
            "note_name": midi_to_note(value),
            "occurrence_count": occurrence_count,
            "total_drum_kits": total_drum_kits,
            "candidate_count_at_position": (
                candidate_count
            ),
            "range_score": round(
                range_score,
                4,
            ),
            "frequency_score": round(
                frequency_score,
                4,
            ),
            "variation_score": round(
                variation_score,
                4,
            ),
            "position_variability": round(
                position_variability,
                4,
            ),
            "score": round(
                weighted_score,
                2,
            ),
        }

    def rank_midi_candidates(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        total_drum_kits = len(records)

        if total_drum_kits == 0:
            return []

        analysis = (
            self.analyze_midi_candidates()
        )

        ranked = []

        for position in analysis:

            relative_offset = (
                position[
                    "relative_offset"
                ]
            )

            candidate_count = (
                position[
                    "candidate_count"
                ]
            )

            for candidate in position[
                "candidates"
            ]:

                scored = (
                    self.score_midi_candidate(
                        relative_offset=(
                            relative_offset
                        ),
                        value=candidate[
                            "value"
                        ],
                        candidate_count=(
                            candidate_count
                        ),
                        occurrence_count=(
                            candidate[
                                "count"
                            ]
                        ),
                        total_drum_kits=(
                            total_drum_kits
                        ),
                    )
                )

                scored["drum_kits"] = (
                    candidate[
                        "drum_kits"
                    ]
                )

                ranked.append(
                    scored
                )

        ranked.sort(
            key=lambda item: (
                item["score"],
                item["occurrence_count"],
            ),
            reverse=True,
        )

        for rank, item in enumerate(
            ranked,
            start=1,
        ):

            item["rank"] = rank

        return ranked

    # ---------------------------------------------------------------
    # MIDI candidates grouped by note
    # ---------------------------------------------------------------

    def group_midi_candidates_by_note(
        self,
    ) -> dict[int, list[dict]]:

        ranked = (
            self.rank_midi_candidates()
        )

        grouped: dict[int, list[dict]] = {}

        for candidate in ranked:

            midi_note = candidate[
                "midi_note"
            ]

            grouped.setdefault(
                midi_note,
                [],
            ).append(
                candidate
            )

        return grouped

    def find_best_candidate_for_midi_note(
        self,
        midi_note: int,
    ) -> Optional[dict]:

        if not self.is_midi_value(
            midi_note
        ):
            raise ValueError(
                "midi_note must be between 0 and 127"
            )

        candidates = (
            self.group_midi_candidates_by_note()
            .get(
                midi_note,
                [],
            )
        )

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda item: item[
                "score"
            ],
        )

    # ---------------------------------------------------------------
    # MIDI mapping by Drum Kit
    # ---------------------------------------------------------------

    def analyze_drum_kit_midi_mapping(
        self,
        index: int,
    ) -> dict:

        record = (
            self.get_drum_kit_name_record(
                index
            )
        )

        ranked = (
            self.rank_midi_candidates()
        )

        mapping = []

        for candidate in ranked:

            for drum_kit in candidate[
                "drum_kits"
            ]:

                if drum_kit[
                    "index"
                ] == index:

                    mapping.append(
                        {
                            "rank": candidate[
                                "rank"
                            ],
                            "relative_offset": (
                                candidate[
                                    "relative_offset"
                                ]
                            ),
                            "absolute_offset": (
                                record["offset"]
                                + candidate[
                                    "relative_offset"
                                ]
                            ),
                            "value": candidate[
                                "value"
                            ],
                            "hex": candidate[
                                "hex"
                            ],
                            "midi_note": candidate[
                                "midi_note"
                            ],
                            "note_name": candidate[
                                "note_name"
                            ],
                            "score": candidate[
                                "score"
                            ],
                            "occurrence_count": (
                                candidate[
                                    "occurrence_count"
                                ]
                            ),
                        }
                    )

        mapping.sort(
            key=lambda item: (
                item["score"],
                item["midi_note"],
            ),
            reverse=True,
        )

        return {
            "index": record["index"],
            "name": record["name"],
            "offset": record["offset"],
            "mapping_candidates": mapping,
        }

    def analyze_all_drum_kit_midi_mappings(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        return [
            self.analyze_drum_kit_midi_mapping(
                record["index"]
            )
            for record in records
        ]

    # ---------------------------------------------------------------
    # #29 Adjacent byte analysis
    # ---------------------------------------------------------------

    @staticmethod
    def _pair_key(
        first: int,
        second: int,
    ) -> str:

        return (
            f"{first:02X} {second:02X}"
        )

    @staticmethod
    def _triplet_key(
        first: int,
        second: int,
        third: int,
    ) -> str:

        return (
            f"{first:02X} "
            f"{second:02X} "
            f"{third:02X}"
        )

    def analyze_adjacent_byte_pairs(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        result = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE - 1
        ):

            pairs: dict[
                tuple[int, int],
                list[dict]
            ] = {}

            for record in records:

                first = record["raw"][
                    relative_offset
                ]

                second = record["raw"][
                    relative_offset + 1
                ]

                key = (
                    first,
                    second,
                )

                pairs.setdefault(
                    key,
                    [],
                ).append(
                    {
                        "index": record["index"],
                        "name": record["name"],
                    }
                )

            pair_details = []

            for (
                first,
                second,
            ) in sorted(pairs):

                pair_details.append(
                    {
                        "first": first,
                        "second": second,
                        "first_hex": (
                            f"{first:02X}"
                        ),
                        "second_hex": (
                            f"{second:02X}"
                        ),
                        "key": self._pair_key(
                            first,
                            second,
                        ),
                        "count": len(
                            pairs[
                                (
                                    first,
                                    second,
                                )
                            ]
                        ),
                        "drum_kits": pairs[
                            (
                                first,
                                second,
                            )
                        ],
                    }
                )

            result.append(
                {
                    "relative_offset": (
                        relative_offset
                    ),
                    "next_offset": (
                        relative_offset + 1
                    ),
                    "unique_pair_count": (
                        len(pairs)
                    ),
                    "pairs": pair_details,
                }
            )

        return result

    def analyze_adjacent_byte_triplets(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        result = []

        for relative_offset in range(
            self.DRUM_KIT_RECORD_SIZE - 2
        ):

            triplets: dict[
                tuple[int, int, int],
                list[dict]
            ] = {}

            for record in records:

                first = record["raw"][
                    relative_offset
                ]

                second = record["raw"][
                    relative_offset + 1
                ]

                third = record["raw"][
                    relative_offset + 2
                ]

                key = (
                    first,
                    second,
                    third,
                )

                triplets.setdefault(
                    key,
                    [],
                ).append(
                    {
                        "index": record["index"],
                        "name": record["name"],
                    }
                )

            details = []

            for (
                first,
                second,
                third,
            ) in sorted(triplets):

                details.append(
                    {
                        "first": first,
                        "second": second,
                        "third": third,
                        "first_hex": (
                            f"{first:02X}"
                        ),
                        "second_hex": (
                            f"{second:02X}"
                        ),
                        "third_hex": (
                            f"{third:02X}"
                        ),
                        "key": self._triplet_key(
                            first,
                            second,
                            third,
                        ),
                        "count": len(
                            triplets[
                                (
                                    first,
                                    second,
                                    third,
                                )
                            ]
                        ),
                        "drum_kits": triplets[
                            (
                                first,
                                second,
                                third,
                            )
                        ],
                    }
                )

            result.append(
                {
                    "relative_offset": (
                        relative_offset
                    ),
                    "unique_triplet_count": (
                        len(triplets)
                    ),
                    "triplets": details,
                }
            )

        return result

    # ---------------------------------------------------------------
    # Sequential MIDI detection
    # ---------------------------------------------------------------

    @staticmethod
    def _is_sequential(
        values: list[int],
    ) -> bool:

        if len(values) < 2:
            return False

        return all(
            values[index] + 1
            == values[index + 1]
            for index in range(
                len(values) - 1
            )
        )

    def find_sequential_midi_patterns(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        patterns = []

        for record in records:

            raw = record["raw"]

            for start in range(
                len(raw)
            ):

                values = []

                for end in range(
                    start,
                    len(raw),
                ):

                    value = raw[end]

                    if not self.is_midi_value(
                        value
                    ):
                        break

                    values.append(value)

                    if len(values) >= 2:

                        if self._is_sequential(
                            values
                        ):

                            patterns.append(
                                {
                                    "index": (
                                        record[
                                            "index"
                                        ]
                                    ),
                                    "name": (
                                        record[
                                            "name"
                                        ]
                                    ),
                                    "start_relative_offset": (
                                        start
                                    ),
                                    "end_relative_offset": (
                                        end
                                    ),
                                    "length": (
                                        len(values)
                                    ),
                                    "values": (
                                        values.copy()
                                    ),
                                    "hex_values": [
                                        f"{value:02X}"
                                        for value
                                        in values
                                    ],
                                    "note_names": [
                                        midi_to_note(
                                            value
                                        )
                                        for value
                                        in values
                                    ],
                                }
                            )

        return patterns

    # ---------------------------------------------------------------
    # MIDI range analysis
    # ---------------------------------------------------------------

    def analyze_midi_ranges(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        ranges = []

        for record in records:

            midi_values = [
                value
                for value in record["raw"]
                if self.is_midi_value(value)
            ]

            if not midi_values:

                ranges.append(
                    {
                        "index": record["index"],
                        "name": record["name"],
                        "count": 0,
                        "minimum": None,
                        "maximum": None,
                        "span": None,
                        "average": None,
                        "values": [],
                    }
                )

                continue

            minimum = min(midi_values)
            maximum = max(midi_values)

            ranges.append(
                {
                    "index": record["index"],
                    "name": record["name"],
                    "count": len(midi_values),
                    "minimum": minimum,
                    "maximum": maximum,
                    "span": maximum - minimum,
                    "average": round(
                        sum(midi_values)
                        / len(midi_values),
                        2,
                    ),
                    "values": midi_values,
                    "note_names": [
                        midi_to_note(
                            value
                        )
                        for value
                        in midi_values
                    ],
                }
            )

        return ranges

    # ---------------------------------------------------------------
    # Position stability
    # ---------------------------------------------------------------

    def analyze_position_stability(
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
                record["raw"][
                    relative_offset
                ]
                for record in records
            ]

            unique_values = set(values)

            fixed = len(unique_values) == 1

            if fixed:

                stability_score = 1.0

            else:

                most_common = max(
                    values.count(value)
                    for value
                    in unique_values
                )

                stability_score = (
                    most_common
                    / len(values)
                )

            result.append(
                {
                    "relative_offset": (
                        relative_offset
                    ),
                    "fixed": fixed,
                    "unique_value_count": (
                        len(unique_values)
                    ),
                    "stability_score": round(
                        stability_score,
                        4,
                    ),
                    "values": sorted(
                        unique_values
                    ),
                    "hex_values": [
                        f"{value:02X}"
                        for value
                        in sorted(unique_values)
                    ],
                }
            )

        return result

    # ---------------------------------------------------------------
    # Cross-kit position correlation
    # ---------------------------------------------------------------

    def analyze_position_correlation(
        self,
    ) -> list[dict]:

        records = (
            self.find_drum_kit_name_records()
        )

        if len(records) < 2:
            return []

        result = []

        for first_offset in range(
            self.DRUM_KIT_RECORD_SIZE
        ):

            first_values = [
                record["raw"][
                    first_offset
                ]
                for record in records
            ]

            for second_offset in range(
                first_offset + 1,
                self.DRUM_KIT_RECORD_SIZE,
            ):

                second_values = [
                    record["raw"][
                        second_offset
                    ]
                    for record in records
                ]

                same_count = sum(
                    first == second
                    for first, second
                    in zip(
                        first_values,
                        second_values,
                    )
                )

                total = len(records)

                correlation = (
                    same_count / total
                    if total
                    else 0.0
                )

                if correlation >= 0.75:

                    result.append(
                        {
                            "first_relative_offset": (
                                first_offset
                            ),
                            "second_relative_offset": (
                                second_offset
                            ),
                            "same_value_count": (
                                same_count
                            ),
                            "total_records": total,
                            "correlation": round(
                                correlation,
                                4,
                            ),
                        }
                    )

        result.sort(
            key=lambda item: item[
                "correlation"
            ],
            reverse=True,
        )

        return result

    # ---------------------------------------------------------------
    # Possible MIDI mapping blocks
    # ---------------------------------------------------------------

    def find_possible_midi_mapping_blocks(
        self,
        minimum_length: int = 2,
    ) -> list[dict]:

        if minimum_length < 2:
            raise ValueError(
                "minimum_length must be at least 2"
            )

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        position_analysis = (
            self.analyze_midi_candidates()
        )

        blocks = []

        start = None

        for position in position_analysis:

            candidate_count = (
                position[
                    "candidate_count"
                ]
            )

            if candidate_count > 0:

                if start is None:
                    start = position[
                        "relative_offset"
                    ]

            else:

                if start is not None:

                    end = (
                        position[
                            "relative_offset"
                        ]
                        - 1
                    )

                    length = (
                        end - start + 1
                    )

                    if length >= minimum_length:

                        block_positions = (
                            position_analysis[
                                start:
                                end + 1
                            ]
                        )

                        blocks.append(
                            {
                                "start_relative_offset": (
                                    start
                                ),
                                "end_relative_offset": (
                                    end
                                ),
                                "length": length,
                                "positions": (
                                    block_positions
                                ),
                            }
                        )

                    start = None

        if start is not None:

            end = (
                self.DRUM_KIT_RECORD_SIZE
                - 1
            )

            length = (
                end - start + 1
            )

            if length >= minimum_length:

                block_positions = (
                    position_analysis[
                        start:
                        end + 1
                    ]
                )

                blocks.append(
                    {
                        "start_relative_offset": start,
                        "end_relative_offset": end,
                        "length": length,
                        "positions": (
                            block_positions
                        ),
                    }
                )

        return blocks

    # ---------------------------------------------------------------
    # Mapping block score
    # ---------------------------------------------------------------

    def score_mapping_block(
        self,
        block: dict,
    ) -> dict:

        positions = block[
            "positions"
        ]

        if not positions:

            return {
                **block,
                "score": 0.0,
                "average_candidate_count": 0.0,
                "variable_position_ratio": 0.0,
                "midi_density": 0.0,
            }

        candidate_counts = [
            position[
                "candidate_count"
            ]
            for position in positions
        ]

        variable_positions = sum(
            count > 1
            for count
            in candidate_counts
        )

        total_positions = len(
            positions
        )

        average_candidate_count = (
            sum(candidate_counts)
            / total_positions
        )

        variable_ratio = (
            variable_positions
            / total_positions
        )

        midi_density = (
            sum(
                count > 0
                for count
                in candidate_counts
            )
            / total_positions
        )

        density_score = (
            midi_density * 40.0
        )

        variability_score = (
            variable_ratio * 35.0
        )

        length_score = min(
            total_positions * 5.0,
            25.0,
        )

        score = (
            density_score
            + variability_score
            + length_score
        )

        return {
            **block,
            "score": round(
                score,
                2,
            ),
            "average_candidate_count": round(
                average_candidate_count,
                2,
            ),
            "variable_position_ratio": round(
                variable_ratio,
                4,
            ),
            "midi_density": round(
                midi_density,
                4,
            ),
        }

    def rank_possible_midi_mapping_blocks(
        self,
        minimum_length: int = 2,
    ) -> list[dict]:

        blocks = (
            self.find_possible_midi_mapping_blocks(
                minimum_length=minimum_length
            )
        )

        ranked = [
            self.score_mapping_block(
                block
            )
            for block in blocks
        ]

        ranked.sort(
            key=lambda item: (
                item["score"],
                item["length"],
            ),
            reverse=True,
        )

        for rank, block in enumerate(
            ranked,
            start=1,
        ):

            block["rank"] = rank

        return ranked

    # ---------------------------------------------------------------
    # #29 structural report
    # ---------------------------------------------------------------

    def build_structural_mapping_report(
        self,
    ) -> dict:

        return {
            "adjacent_pairs": (
                self.analyze_adjacent_byte_pairs()
            ),
            "adjacent_triplets": (
                self.analyze_adjacent_byte_triplets()
            ),
            "sequential_midi_patterns": (
                self.find_sequential_midi_patterns()
            ),
            "midi_ranges": (
                self.analyze_midi_ranges()
            ),
            "position_stability": (
                self.analyze_position_stability()
            ),
            "position_correlation": (
                self.analyze_position_correlation()
            ),
            "possible_mapping_blocks": (
                self.rank_possible_midi_mapping_blocks()
            ),
        }

    # ---------------------------------------------------------------
    # MIDI summary
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

            for candidate in item[
                "candidates"
            ]:

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
    # MIDI scoring summary
    # ---------------------------------------------------------------

    def summarize_midi_scoring(
        self,
        top_n: int = 50,
    ) -> dict:

        if top_n < 1:
            raise ValueError(
                "top_n must be greater than 0"
            )

        ranked = (
            self.rank_midi_candidates()
        )

        return {
            "total_candidates": len(
                ranked
            ),
            "top_n": min(
                top_n,
                len(ranked),
            ),
            "top_candidates": ranked[
                :top_n
            ],
        }

    def find_high_confidence_midi_candidates(
        self,
        minimum_score: float = 70.0,
    ) -> list[dict]:

        if not 0 <= minimum_score <= 100:
            raise ValueError(
                "minimum_score must be between 0 and 100"
            )

        ranked = (
            self.rank_midi_candidates()
        )

        return [
            candidate
            for candidate in ranked
            if candidate["score"]
            >= minimum_score
        ]

    # ---------------------------------------------------------------
    # MIDI position report
    # ---------------------------------------------------------------

    def build_midi_position_report(
        self,
    ) -> list[dict]:

        analysis = (
            self.analyze_midi_candidates()
        )

        report = []

        for position in analysis:

            candidates = position[
                "candidates"
            ]

            best_candidate = None

            if candidates:

                best_candidate = max(
                    candidates,
                    key=lambda item: item[
                        "count"
                    ],
                )

            report.append(
                {
                    "relative_offset": (
                        position[
                            "relative_offset"
                        ]
                    ),
                    "candidate_count": (
                        position[
                            "candidate_count"
                        ]
                    ),
                    "best_value": (
                        best_candidate[
                            "value"
                        ]
                        if best_candidate
                        else None
                    ),
                    "best_hex": (
                        best_candidate[
                            "hex"
                        ]
                        if best_candidate
                        else None
                    ),
                    "best_midi_note": (
                        best_candidate[
                            "midi_note"
                        ]
                        if best_candidate
                        else None
                    ),
                    "best_note_name": (
                        best_candidate[
                            "note_name"
                        ]
                        if best_candidate
                        else None
                    ),
                    "best_count": (
                        best_candidate[
                            "count"
                        ]
                        if best_candidate
                        else 0
                    ),
                }
            )

        return report

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
            "midi_scoring": (
                self.summarize_midi_scoring()
            ),
            "structural_mapping": (
                self.build_structural_mapping_report()
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
            "midi_scoring": (
                self.summarize_midi_scoring()
            ),
            "midi_mapping_report": (
                self.build_midi_position_report()
            ),
            "structural_mapping_report": (
                self.build_structural_mapping_report()
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
            "midi_scoring": (
                self.summarize_midi_scoring()
            ),
            "midi_mapping_report": (
                self.build_midi_position_report()
            ),
            "structural_mapping_report": (
                self.build_structural_mapping_report()
            ),
        }

    # ---------------------------------------------------------------
    # DrumKit model conversion
    # ---------------------------------------------------------------

    def parse(
        self,
    ) -> list[DrumKit]:

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
    # MIDI instrument helper
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
