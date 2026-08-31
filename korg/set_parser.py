```python id="r7m3kd"
    # ===============================================================
    # #38 HUMAN-READABLE DRUM KIT REPORT
    # ===============================================================

    def build_human_readable_drum_kit_report(
        self,
    ) -> dict:
        """
        #38

        Pretvara rezultate #37 u strukturirani,
        čitljiv izvještaj.

        Cilj:
        - prikazati svaki Drum Kit pregledno
        - prikazati najbolje MIDI mapping kandidate
        - prikazati mapping fieldove
        - prikazati confidence i score
        - prikazati unknown byte pozicije
        - omogućiti lakše ručno provjeravanje rezultata
        - NE mijenjati originalni PCG/SET fajl
        """

        structure_report = (
            self.build_drum_kit_structure_report()
        )

        reconstructed_kits = structure_report.get(
            "reconstructed_kits",
            [],
        )

        if not reconstructed_kits:
            return {
                "title": (
                    "Korg Drum Kit Analysis Report"
                ),
                "drum_kit_count": 0,
                "kits": [],
                "summary": {
                    "high_confidence_kits": 0,
                    "kits_with_midi_mapping": 0,
                    "total_mapping_positions": 0,
                    "total_mapping_fields": 0,
                },
            }

        # -----------------------------------------------------------
        # Helper functions
        # -----------------------------------------------------------

        def format_hex(
            value,
        ):
            try:
                return f"{int(value):02X}"
            except (
                TypeError,
                ValueError,
            ):
                return "??"

        def safe_note_name(
            value,
        ):
            try:
                if (
                    isinstance(
                        value,
                        int,
                    )
                    and 0 <= value <= 127
                ):
                    return midi_to_note(
                        value
                    )
            except Exception:
                pass

            return None

        # -----------------------------------------------------------
        # Build human-readable kit reports
        # -----------------------------------------------------------

        kit_reports = []

        for kit in reconstructed_kits:

            record_index = kit.get(
                "record_index"
            )

            raw_bytes = kit.get(
                "raw_bytes",
                [],
            )

            midi_positions = kit.get(
                "midi_mapping_positions",
                [],
            )

            mapping_fields = kit.get(
                "mapping_fields",
                [],
            )

            interpreted_fields = kit.get(
                "interpreted_fields",
                [],
            )

            unknown_positions = kit.get(
                "unknown_positions",
                [],
            )

            reconstruction_score = kit.get(
                "reconstruction_score",
                0.0,
            )

            reconstruction_confidence = (
                kit.get(
                    "reconstruction_confidence",
                    "low",
                )
            )

            # -------------------------------------------------------
            # MIDI mapping summary
            # -------------------------------------------------------

            midi_mapping_summary = []

            for mapping in midi_positions:

                offset = mapping.get(
                    "relative_offset"
                )

                value = mapping.get(
                    "value"
                )

                note_name = mapping.get(
                    "midi_note_name"
                )

                if note_name is None:
                    note_name = safe_note_name(
                        value
                    )

                midi_mapping_summary.append(
                    {
                        "offset": offset,
                        "offset_hex": (
                            format_hex(
                                offset
                            )
                        ),
                        "value": value,
                        "hex": (
                            format_hex(
                                value
                            )
                        ),
                        "midi_note": (
                            note_name
                        ),
                        "validation": (
                            mapping.get(
                                "validation"
                            )
                        ),
                        "confidence": (
                            mapping.get(
                                "confidence"
                            )
                        ),
                        "score": (
                            mapping.get(
                                "validation_score",
                                0.0,
                            )
                        ),
                    }
                )

            # -------------------------------------------------------
            # Mapping field summary
            # -------------------------------------------------------

            field_summary = []

            for field in mapping_fields:

                offsets = field.get(
                    "offsets",
                    [],
                )

                offset_text = ", ".join(
                    f"0x{format_hex(offset)}"
                    for offset in offsets
                )

                field_summary.append(
                    {
                        "field_id": (
                            field.get(
                                "field_id"
                            )
                        ),
                        "offsets": offsets,
                        "offset_range": (
                            f"0x{format_hex(field.get('start_offset'))}"
                            f"-0x{format_hex(field.get('end_offset'))}"
                        ),
                        "offset_text": (
                            offset_text
                        ),
                        "field_size": (
                            field.get(
                                "field_size"
                            )
                        ),
                        "score": (
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
                    }
                )

            # -------------------------------------------------------
            # Interpretation summary
            # -------------------------------------------------------

            interpretation_summary = []

            for field in interpreted_fields:

                interpretation_summary.append(
                    {
                        "field_id": (
                            field.get(
                                "field_id"
                            )
                        ),
                        "offsets": (
                            field.get(
                                "offsets",
                                [],
                            )
                        ),
                        "interpretation": (
                            field.get(
                                "interpretation"
                            )
                        ),
                        "confidence": (
                            field.get(
                                "confidence"
                            )
                        ),
                        "score": (
                            field.get(
                                "interpretation_score",
                                0.0,
                            )
                        ),
                        "midi_mapping": (
                            field.get(
                                "midi_mapping"
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
            # Unknown byte summary
            # -------------------------------------------------------

            unknown_summary = []

            for unknown in unknown_positions:

                offset = unknown.get(
                    "relative_offset"
                )

                value = unknown.get(
                    "value"
                )

                unknown_summary.append(
                    {
                        "offset": offset,
                        "offset_hex": (
                            format_hex(
                                offset
                            )
                        ),
                        "value": value,
                        "hex": (
                            format_hex(
                                value
                            )
                        ),
                    }
                )

            # -------------------------------------------------------
            # Raw hex grouped in rows
            # -------------------------------------------------------

            raw_hex_rows = []

            for start in range(
                0,
                len(raw_bytes),
                16,
            ):

                chunk = raw_bytes[
                    start:start + 16
                ]

                raw_hex_rows.append(
                    {
                        "start_offset": start,
                        "end_offset": (
                            start
                            + len(chunk)
                            - 1
                        ),
                        "hex": " ".join(
                            format_hex(
                                value
                            )
                            for value
                            in chunk
                        ),
                    }
                )

            # -------------------------------------------------------
            # Human-readable status
            # -------------------------------------------------------

            if reconstruction_confidence == "high":

                status = (
                    "HIGH CONFIDENCE"
                )

            elif (
                reconstruction_confidence
                == "medium"
            ):

                status = (
                    "MEDIUM CONFIDENCE"
                )

            else:

                status = (
                    "LOW CONFIDENCE"
                )

            # -------------------------------------------------------
            # Build kit report
            # -------------------------------------------------------

            kit_reports.append(
                {
                    "kit_number": (
                        record_index
                    ),
                    "status": status,
                    "confidence": (
                        reconstruction_confidence
                    ),
                    "reconstruction_score": (
                        reconstruction_score
                    ),
                    "record_size": (
                        len(raw_bytes)
                    ),
                    "midi_mapping_count": (
                        len(
                            midi_mapping_summary
                        )
                    ),
                    "mapping_field_count": (
                        len(
                            field_summary
                        )
                    ),
                    "midi_mappings": (
                        midi_mapping_summary
                    ),
                    "mapping_fields": (
                        field_summary
                    ),
                    "interpretations": (
                        interpretation_summary
                    ),
                    "unknown_positions": (
                        unknown_summary
                    ),
                    "raw_hex_rows": (
                        raw_hex_rows
                    ),
                }
            )

        # -----------------------------------------------------------
        # Summary
        # -----------------------------------------------------------

        high_confidence_count = sum(
            1
            for kit
            in kit_reports
            if kit[
                "confidence"
            ]
            == "high"
        )

        medium_confidence_count = sum(
            1
            for kit
            in kit_reports
            if kit[
                "confidence"
            ]
            == "medium"
        )

        low_confidence_count = sum(
            1
            for kit
            in kit_reports
            if kit[
                "confidence"
            ]
            == "low"
        )

        kits_with_midi_mapping = sum(
            1
            for kit
            in kit_reports
            if kit[
                "midi_mapping_count"
            ] > 0
        )

        total_mapping_positions = sum(
            kit[
                "midi_mapping_count"
            ]
            for kit
            in kit_reports
        )

        total_mapping_fields = sum(
            kit[
                "mapping_field_count"
            ]
            for kit
            in kit_reports
        )

        # -----------------------------------------------------------
        # Best candidates
        # -----------------------------------------------------------

        best_midi_candidates = []

        for kit in kit_reports:

            for mapping in kit[
                "midi_mappings"
            ]:

                best_midi_candidates.append(
                    {
                        "kit_number": (
                            kit[
                                "kit_number"
                            ]
                        ),
                        "offset": (
                            mapping[
                                "offset"
                            ]
                        ),
                        "value": (
                            mapping[
                                "value"
                            ]
                        ),
                        "hex": (
                            mapping[
                                "hex"
                            ]
                        ),
                        "midi_note": (
                            mapping[
                                "midi_note"
                            ]
                        ),
                        "validation": (
                            mapping[
                                "validation"
                            ]
                        ),
                        "confidence": (
                            mapping[
                                "confidence"
                            ]
                        ),
                        "score": (
                            mapping[
                                "score"
                            ]
                        ),
                    }
                )

        best_midi_candidates.sort(
            key=lambda item: (
                item[
                    "score"
                ]
            ),
            reverse=True,
        )

        # -----------------------------------------------------------
        # Final report
        # -----------------------------------------------------------

        return {
            "title": (
                "Korg Drum Kit Human-Readable Analysis"
            ),
            "version": (
                "#38"
            ),
            "description": (
                "Human-readable reconstruction of "
                "Drum Kit binary structure."
            ),
            "drum_kit_count": len(
                kit_reports
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "summary": {
                "high_confidence_kits": (
                    high_confidence_count
                ),
                "medium_confidence_kits": (
                    medium_confidence_count
                ),
                "low_confidence_kits": (
                    low_confidence_count
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
            },
            "best_midi_candidates": (
                best_midi_candidates
            ),
            "kits": (
                kit_reports
            ),
            "analysis_chain": [
                "#32 Mapping Consistency",
                "#33 Mapping Relationships",
                "#34 Mapping Field Detection",
                "#35 Mapping Field Interpretation",
                "#36 MIDI Mapping Validation",
                "#37 Drum Kit Structure Reconstruction",
                "#38 Human-Readable Drum Kit Report",
            ],
            "warning": (
                "Results are analytical candidates only. "
                "No values are written back to the original "
                "PCG/SET file."
            ),
        }

    def get_best_midi_mapping_candidates(
        self,
    ) -> list[dict]:
        """
        Returns the best MIDI mapping candidates
        from the #38 human-readable report.
        """

        report = (
            self.build_human_readable_drum_kit_report()
        )

        return report.get(
            "best_midi_candidates",
            [],
        )

    def get_drum_kit_report_summary(
        self,
    ) -> dict:
        """
        Returns only the summary section of #38.
        """

        report = (
            self.build_human_readable_drum_kit_report()
        )

        return report.get(
            "summary",
            {},
        )
```
