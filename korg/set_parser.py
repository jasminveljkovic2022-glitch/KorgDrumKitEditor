```python
    # ===============================================================
    # #37 DRUM KIT STRUCTURE RECONSTRUCTION
    # ===============================================================

    def reconstruct_drum_kit_structure(
        self,
    ) -> list[dict]:
        """
        #37

        Rekonstruira najvjerojatniju strukturu svakog
        pronađenog Drum Kit recorda koristeći rezultate:

        #32 - Mapping Consistency
        #33 - Mapping Relationships
        #34 - Mapping Fields
        #35 - Mapping Interpretation
        #36 - MIDI Mapping Validation

        Cilj:
        - povezati poznate i nepoznate byte pozicije
        - izgraditi strukturirani prikaz svakog Drum Kit recorda
        - označiti moguće MIDI mapping pozicije
        - označiti povezane/konstantne fieldove
        - zadržati originalne byte vrijednosti
        - NE mijenjati originalni PCG/SET fajl
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        consistency_report = (
            self.analyze_mapping_consistency()
        )

        field_report = (
            self.analyze_mapping_fields()
        )

        interpretation_report = (
            self.analyze_mapping_field_interpretation()
        )

        validation_report = (
            self.validate_midi_mapping_candidates()
        )

        if not consistency_report:
            return []

        consistency_by_offset = {
            item[
                "relative_offset"
            ]: item
            for item in consistency_report
        }

        field_by_offset = {}

        for field in field_report:

            for offset in field.get(
                "offsets",
                [],
            ):

                field_by_offset[
                    offset
                ] = field

        interpretation_by_offset = {}

        for interpretation in interpretation_report:

            for offset in interpretation.get(
                "offsets",
                [],
            ):

                interpretation_by_offset[
                    offset
                ] = interpretation

        validation_by_offset = {
            item[
                "relative_offset"
            ]: item
            for item in validation_report
        }

        reconstructed_kits = []

        # -----------------------------------------------------------
        # Determine record size
        # -----------------------------------------------------------

        record_size = (
            self.DRUM_KIT_RECORD_SIZE
        )

        # -----------------------------------------------------------
        # Process every Drum Kit record
        # -----------------------------------------------------------

        for record_index, record in enumerate(
            records,
            start=1,
        ):

            # -------------------------------------------------------
            # Raw record bytes
            # -------------------------------------------------------

            try:
                raw_bytes = bytes(
                    record
                )
            except (
                TypeError,
                ValueError,
            ):
                raw_bytes = bytes(
                    record[:record_size]
                )

            raw_bytes = raw_bytes[
                :record_size
            ]

            # -------------------------------------------------------
            # Build byte-level structure
            # -------------------------------------------------------

            byte_fields = []

            for offset in range(
                len(raw_bytes)
            ):

                value = raw_bytes[
                    offset
                ]

                consistency = (
                    consistency_by_offset.get(
                        offset
                    )
                )

                field = (
                    field_by_offset.get(
                        offset
                    )
                )

                interpretation = (
                    interpretation_by_offset.get(
                        offset
                    )
                )

                validation = (
                    validation_by_offset.get(
                        offset
                    )
                )

                midi_note_name = None

                if (
                    value >= 0
                    and value <= 127
                ):

                    try:
                        midi_note_name = (
                            midi_to_note(
                                value
                            )
                        )
                    except Exception:
                        midi_note_name = None

                byte_fields.append(
                    {
                        "relative_offset": (
                            offset
                        ),
                        "value": (
                            value
                        ),
                        "hex": (
                            f"{value:02X}"
                        ),
                        "binary": (
                            f"{value:08b}"
                        ),
                        "midi_note_name": (
                            midi_note_name
                        ),
                        "consistency_score": (
                            consistency.get(
                                "consistency_score",
                                0.0,
                            )
                            if consistency
                            else 0.0
                        ),
                        "consistency_classification": (
                            consistency.get(
                                "classification"
                            )
                            if consistency
                            else None
                        ),
                        "field_id": (
                            field.get(
                                "field_id"
                            )
                            if field
                            else None
                        ),
                        "field_classification": (
                            field.get(
                                "classification"
                            )
                            if field
                            else None
                        ),
                        "interpretation": (
                            interpretation.get(
                                "interpretation"
                            )
                            if interpretation
                            else None
                        ),
                        "interpretation_confidence": (
                            interpretation.get(
                                "confidence"
                            )
                            if interpretation
                            else None
                        ),
                        "validation": (
                            validation.get(
                                "validation"
                            )
                            if validation
                            else None
                        ),
                        "validation_confidence": (
                            validation.get(
                                "confidence"
                            )
                            if validation
                            else None
                        ),
                        "validation_score": (
                            validation.get(
                                "validation_score",
                                0.0,
                            )
                            if validation
                            else 0.0
                        ),
                    }
                )

            # -------------------------------------------------------
            # Identify mapping positions
            # -------------------------------------------------------

            midi_mapping_positions = []

            for offset, validation in (
                validation_by_offset.items()
            ):

                if (
                    offset < 0
                    or offset >= len(raw_bytes)
                ):
                    continue

                if validation.get(
                    "validation"
                ) in (
                    "validated_midi_mapping",
                    "probable_midi_mapping",
                ):

                    value = raw_bytes[
                        offset
                    ]

                    midi_note_name = None

                    try:
                        midi_note_name = (
                            midi_to_note(
                                value
                            )
                        )
                    except Exception:
                        midi_note_name = None

                    midi_mapping_positions.append(
                        {
                            "relative_offset": (
                                offset
                            ),
                            "value": (
                                value
                            ),
                            "hex": (
                                f"{value:02X}"
                            ),
                            "midi_note_name": (
                                midi_note_name
                            ),
                            "validation": (
                                validation[
                                    "validation"
                                ]
                            ),
                            "confidence": (
                                validation[
                                    "confidence"
                                ]
                            ),
                            "validation_score": (
                                validation[
                                    "validation_score"
                                ]
                            ),
                        }
                    )

            midi_mapping_positions.sort(
                key=lambda item: (
                    item[
                        "validation_score"
                    ]
                ),
                reverse=True,
            )

            # -------------------------------------------------------
            # Identify possible mapping fields
            # -------------------------------------------------------

            mapping_fields = []

            for field in field_report:

                field_offsets = field.get(
                    "offsets",
                    [],
                )

                if not field_offsets:
                    continue

                if any(
                    offset < len(raw_bytes)
                    for offset in field_offsets
                ):

                    mapping_fields.append(
                        {
                            "field_id": (
                                field.get(
                                    "field_id"
                                )
                            ),
                            "offsets": (
                                field_offsets
                            ),
                            "start_offset": (
                                field.get(
                                    "start_offset"
                                )
                            ),
                            "end_offset": (
                                field.get(
                                    "end_offset"
                                )
                            ),
                            "field_size": (
                                field.get(
                                    "field_size"
                                )
                            ),
                            "group_score": (
                                field.get(
                                    "group_score",
                                    0.0,
                                )
                            ),
                            "classification": (
                                field.get(
                                    "classification"
                                )
                            ),
                            "evidence": (
                                field.get(
                                    "evidence",
                                    [],
                                )
                            ),
                        }
                    )

            # -------------------------------------------------------
            # Identify interpreted fields
            # -------------------------------------------------------

            interpreted_fields = []

            for interpretation in (
                interpretation_report
            ):

                offsets = interpretation.get(
                    "offsets",
                    [],
                )

                if not offsets:
                    continue

                field_values = {}

                for offset in offsets:

                    if (
                        offset < 0
                        or offset >= len(raw_bytes)
                    ):
                        continue

                    value = raw_bytes[
                        offset
                    ]

                    field_values[
                        offset
                    ] = {
                        "value": value,
                        "hex": f"{value:02X}",
                    }

                interpreted_fields.append(
                    {
                        "field_id": (
                            interpretation.get(
                                "field_id"
                            )
                        ),
                        "offsets": offsets,
                        "values": field_values,
                        "interpretation": (
                            interpretation.get(
                                "interpretation"
                            )
                        ),
                        "confidence": (
                            interpretation.get(
                                "confidence"
                            )
                        ),
                        "interpretation_score": (
                            interpretation.get(
                                "interpretation_score",
                                0.0,
                            )
                        ),
                        "midi_mapping": (
                            interpretation.get(
                                "midi_mapping"
                            )
                        ),
                        "evidence": (
                            interpretation.get(
                                "evidence",
                                [],
                            )
                        ),
                    }
                )

            # -------------------------------------------------------
            # Unknown positions
            # -------------------------------------------------------

            known_offsets = set()

            for field in field_report:

                for offset in field.get(
                    "offsets",
                    [],
                ):

                    known_offsets.add(
                        offset
                    )

            unknown_positions = []

            for offset in range(
                len(raw_bytes)
            ):

                if offset in known_offsets:
                    continue

                value = raw_bytes[
                    offset
                ]

                unknown_positions.append(
                    {
                        "relative_offset": (
                            offset
                        ),
                        "value": (
                            value
                        ),
                        "hex": (
                            f"{value:02X}"
                        ),
                    }
                )

            # -------------------------------------------------------
            # Group positions by field
            # -------------------------------------------------------

            field_groups = []

            for field in mapping_fields:

                offsets = field.get(
                    "offsets",
                    [],
                )

                values = []

                for offset in offsets:

                    if (
                        0 <= offset
                        < len(raw_bytes)
                    ):

                        value = raw_bytes[
                            offset
                        ]

                        values.append(
                            {
                                "relative_offset": (
                                    offset
                                ),
                                "value": (
                                    value
                                ),
                                "hex": (
                                    f"{value:02X}"
                                ),
                            }
                        )

                field_groups.append(
                    {
                        "field_id": field.get(
                            "field_id"
                        ),
                        "offsets": offsets,
                        "values": values,
                        "classification": (
                            field.get(
                                "classification"
                            )
                        ),
                        "group_score": (
                            field.get(
                                "group_score",
                                0.0,
                            )
                        ),
                    }
                )

            # -------------------------------------------------------
            # Calculate reconstruction confidence
            # -------------------------------------------------------

            strong_mapping_count = len(
                [
                    item
                    for item
                    in midi_mapping_positions
                    if item[
                        "validation"
                    ]
                    == "validated_midi_mapping"
                ]
            )

            probable_mapping_count = len(
                [
                    item
                    for item
                    in midi_mapping_positions
                    if item[
                        "validation"
                    ]
                    == "probable_midi_mapping"
                ]
            )

            strong_field_count = len(
                [
                    field
                    for field
                    in mapping_fields
                    if field[
                        "classification"
                    ]
                    == "strong_mapping_field"
                ]
            )

            average_validation_score = (
                sum(
                    item[
                        "validation_score"
                    ]
                    for item
                    in validation_report
                )
                / len(
                    validation_report
                )
                if validation_report
                else 0.0
            )

            reconstruction_score = (
                min(
                    strong_mapping_count * 20.0,
                    40.0,
                )
                + min(
                    probable_mapping_count * 10.0,
                    20.0,
                )
                + min(
                    strong_field_count * 15.0,
                    20.0,
                )
                + (
                    average_validation_score
                    * 0.20
                )
            )

            reconstruction_score = min(
                reconstruction_score,
                100.0,
            )

            if (
                reconstruction_score >= 85.0
            ):

                reconstruction_confidence = (
                    "high"
                )

            elif (
                reconstruction_score >= 65.0
            ):

                reconstruction_confidence = (
                    "medium"
                )

            else:

                reconstruction_confidence = (
                    "low"
                )

            # -------------------------------------------------------
            # Final reconstructed Drum Kit
            # -------------------------------------------------------

            reconstructed_kits.append(
                {
                    "record_index": (
                        record_index
                    ),
                    "record_size": (
                        len(raw_bytes)
                    ),
                    "raw_hex": (
                        " ".join(
                            f"{value:02X}"
                            for value
                            in raw_bytes
                        )
                    ),
                    "raw_bytes": list(
                        raw_bytes
                    ),
                    "reconstruction_score": round(
                        reconstruction_score,
                        2,
                    ),
                    "reconstruction_confidence": (
                        reconstruction_confidence
                    ),
                    "midi_mapping_positions": (
                        midi_mapping_positions
                    ),
                    "mapping_fields": (
                        mapping_fields
                    ),
                    "interpreted_fields": (
                        interpreted_fields
                    ),
                    "field_groups": (
                        field_groups
                    ),
                    "unknown_positions": (
                        unknown_positions
                    ),
                    "byte_fields": (
                        byte_fields
                    ),
                }
            )

        return reconstructed_kits

    def find_high_confidence_drum_kits(
        self,
    ) -> list[dict]:
        """
        Returns reconstructed Drum Kits with
        high reconstruction confidence.
        """

        report = (
            self.reconstruct_drum_kit_structure()
        )

        return [
            item
            for item in report
            if item[
                "reconstruction_confidence"
            ]
            == "high"
        ]

    def find_reconstructed_midi_mappings(
        self,
    ) -> list[dict]:
        """
        Returns all reconstructed Drum Kits
        that contain validated or probable
        MIDI mapping positions.
        """

        report = (
            self.reconstruct_drum_kit_structure()
        )

        return [
            item
            for item in report
            if item[
                "midi_mapping_positions"
            ]
        ]

    def build_drum_kit_structure_report(
        self,
    ) -> dict:
        """
        Complete #37 Drum Kit structure report.
        """

        report = (
            self.reconstruct_drum_kit_structure()
        )

        high_confidence = [
            item
            for item in report
            if item[
                "reconstruction_confidence"
            ]
            == "high"
        ]

        kits_with_midi_mapping = [
            item
            for item in report
            if item[
                "midi_mapping_positions"
            ]
        ]

        total_mapping_positions = sum(
            len(
                item[
                    "midi_mapping_positions"
                ]
            )
            for item in report
        )

        total_mapping_fields = sum(
            len(
                item[
                    "mapping_fields"
                ]
            )
            for item in report
        )

        return {
            "drum_kit_count": len(
                report
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "reconstructed_kits": (
                report
            ),
            "high_confidence_kits": (
                high_confidence
            ),
            "kits_with_midi_mapping": (
                kits_with_midi_mapping
            ),
            "total_mapping_positions": (
                total_mapping_positions
            ),
            "total_mapping_fields": (
                total_mapping_fields
            ),
        }
```
