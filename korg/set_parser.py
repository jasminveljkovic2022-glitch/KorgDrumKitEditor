```python
    # ===============================================================
    # #35 MAPPING FIELD INTERPRETATION
    # ===============================================================

    def analyze_mapping_field_interpretation(
        self,
    ) -> list[dict]:
        """
        #35

        Pokušava interpretirati mapping fieldove pronađene
        u #34.

        Cilj:
        - identificirati moguće MIDI note pozicije
        - identificirati pomoćne / povezane pozicije
        - razlikovati MIDI-like vrijednosti od ostalih vrijednosti
        - koristiti rezultate #32, #33 i #34
        - izračunati interpretation score
        - NE mijenjati originalni PCG/SET fajl
        """

        fields = (
            self.analyze_mapping_fields()
        )

        if not fields:
            return []

        consistency_report = (
            self.analyze_mapping_consistency()
        )

        relationship_report = (
            self.analyze_mapping_relationships()
        )

        if not consistency_report:
            return []

        consistency_by_offset = {
            item[
                "relative_offset"
            ]: item
            for item in consistency_report
        }

        relationship_by_pair = {}

        for relationship in relationship_report:

            offset_a = relationship[
                "offset_a"
            ]

            offset_b = relationship[
                "offset_b"
            ]

            relationship_by_pair[
                (
                    offset_a,
                    offset_b,
                )
            ] = relationship

            relationship_by_pair[
                (
                    offset_b,
                    offset_a,
                )
            ] = relationship

        interpretation_report = []

        # -----------------------------------------------------------
        # Analyze every mapping field
        # -----------------------------------------------------------

        for field in fields:

            offsets = field.get(
                "offsets",
                [],
            )

            if not offsets:
                continue

            positions = []

            for offset in offsets:

                consistency = (
                    consistency_by_offset.get(
                        offset
                    )
                )

                if not consistency:
                    continue

                unique_values = consistency.get(
                    "unique_values",
                    [],
                )

                midi_values = consistency.get(
                    "midi_values",
                    [],
                )

                midi_ratio = consistency.get(
                    "midi_ratio",
                    0.0,
                )

                consistency_score = consistency.get(
                    "consistency_score",
                    0.0,
                )

                minimum_value = consistency.get(
                    "minimum_value"
                )

                maximum_value = consistency.get(
                    "maximum_value"
                )

                value_range = consistency.get(
                    "value_range"
                )

                # ---------------------------------------------------
                # MIDI note plausibility
                # ---------------------------------------------------

                midi_note_score = 0.0

                if midi_ratio >= 1.0:
                    midi_note_score += 40.0

                elif midi_ratio >= 0.75:
                    midi_note_score += 30.0

                elif midi_ratio >= 0.50:
                    midi_note_score += 15.0

                # Typical MIDI note range
                if (
                    minimum_value is not None
                    and maximum_value is not None
                ):

                    if (
                        0
                        <= minimum_value
                        <= 127
                        and
                        0
                        <= maximum_value
                        <= 127
                    ):
                        midi_note_score += 25.0

                    if (
                        24
                        <= minimum_value
                        <= 108
                        and
                        24
                        <= maximum_value
                        <= 108
                    ):
                        midi_note_score += 15.0

                # Compact note range is useful evidence
                if value_range is not None:

                    if value_range <= 12:
                        midi_note_score += 15.0

                    elif value_range <= 24:
                        midi_note_score += 10.0

                    elif value_range <= 36:
                        midi_note_score += 5.0

                midi_note_score = min(
                    midi_note_score,
                    100.0,
                )

                # ---------------------------------------------------
                # Constant-field detection
                # ---------------------------------------------------

                if len(unique_values) == 1:

                    field_type = (
                        "constant_parameter"
                    )

                    interpretation_score = (
                        consistency_score
                    )

                    confidence = (
                        "low"
                    )

                # ---------------------------------------------------
                # MIDI note candidate
                # ---------------------------------------------------

                elif midi_note_score >= 75.0:

                    field_type = (
                        "midi_note_candidate"
                    )

                    interpretation_score = (
                        midi_note_score
                    )

                    confidence = (
                        "high"
                        if midi_note_score >= 90.0
                        else "medium"
                    )

                elif midi_note_score >= 55.0:

                    field_type = (
                        "possible_midi_note"
                    )

                    interpretation_score = (
                        midi_note_score
                    )

                    confidence = (
                        "medium"
                    )

                else:

                    field_type = (
                        "unknown_mapping_parameter"
                    )

                    interpretation_score = (
                        consistency_score
                    )

                    confidence = (
                        "low"
                    )

                # ---------------------------------------------------
                # MIDI note names
                # ---------------------------------------------------

                note_names = []

                for value in midi_values:

                    try:
                        note_names.append(
                            midi_to_note(
                                value
                            )
                        )
                    except Exception:
                        note_names.append(
                            None
                        )

                # ---------------------------------------------------
                # Related positions
                # ---------------------------------------------------

                related_positions = []

                for other_offset in offsets:

                    if (
                        other_offset
                        == offset
                    ):
                        continue

                    relationship = (
                        relationship_by_pair.get(
                            (
                                offset,
                                other_offset,
                            )
                        )
                    )

                    if not relationship:
                        continue

                    related_positions.append(
                        {
                            "offset": (
                                other_offset
                            ),
                            "relationship_score": (
                                relationship[
                                    "relationship_score"
                                ]
                            ),
                            "co_change_ratio": (
                                relationship[
                                    "co_change_ratio"
                                ]
                            ),
                            "correlation": (
                                relationship[
                                    "correlation"
                                ]
                            ),
                            "constant_delta": (
                                relationship[
                                    "constant_delta"
                                ]
                            ),
                            "classification": (
                                relationship[
                                    "classification"
                                ]
                            ),
                        }
                    )

                related_positions.sort(
                    key=lambda item: (
                        item[
                            "relationship_score"
                        ]
                    ),
                    reverse=True,
                )

                positions.append(
                    {
                        "offset": offset,
                        "unique_values": (
                            unique_values
                        ),
                        "hex_values": (
                            consistency.get(
                                "hex_values",
                                [],
                            )
                        ),
                        "midi_values": (
                            midi_values
                        ),
                        "midi_note_names": (
                            note_names
                        ),
                        "midi_ratio": (
                            midi_ratio
                        ),
                        "minimum_value": (
                            minimum_value
                        ),
                        "maximum_value": (
                            maximum_value
                        ),
                        "value_range": (
                            value_range
                        ),
                        "consistency_score": (
                            consistency_score
                        ),
                        "midi_note_score": round(
                            midi_note_score,
                            2,
                        ),
                        "field_type": (
                            field_type
                        ),
                        "confidence": (
                            confidence
                        ),
                        "related_positions": (
                            related_positions
                        ),
                    }
                )

            if not positions:
                continue

            # -------------------------------------------------------
            # Find best MIDI note position
            # -------------------------------------------------------

            midi_candidates = [
                item
                for item in positions
                if item[
                    "field_type"
                ]
                in (
                    "midi_note_candidate",
                    "possible_midi_note",
                )
            ]

            midi_candidates.sort(
                key=lambda item: (
                    item[
                        "midi_note_score"
                    ],
                    item[
                        "midi_ratio"
                    ],
                    item[
                        "consistency_score"
                    ],
                ),
                reverse=True,
            )

            primary_midi_position = (
                midi_candidates[0]
                if midi_candidates
                else None
            )

            # -------------------------------------------------------
            # Field-level MIDI score
            # -------------------------------------------------------

            if primary_midi_position:

                field_midi_score = (
                    primary_midi_position[
                        "midi_note_score"
                    ]
                )

            else:

                field_midi_score = (
                    field.get(
                        "group_midi_ratio",
                        0.0,
                    )
                    * 100.0
                )

            # -------------------------------------------------------
            # Field relationship evidence
            # -------------------------------------------------------

            group_relationship_score = field.get(
                "group_relationship_score",
                0.0,
            )

            group_consistency_score = field.get(
                "group_consistency_score",
                0.0,
            )

            contiguous_ratio = field.get(
                "contiguous_ratio",
                0.0,
            )

            # -------------------------------------------------------
            # Determine likely field role
            # -------------------------------------------------------

            role_evidence = []

            if primary_midi_position:

                role_evidence.append(
                    "field_contains_midi_note_candidate"
                )

            if group_relationship_score >= 80.0:

                role_evidence.append(
                    "field_has_strong_internal_relationships"
                )

            if group_consistency_score >= 80.0:

                role_evidence.append(
                    "field_positions_are_highly_consistent"
                )

            if contiguous_ratio >= 0.75:

                role_evidence.append(
                    "field_offsets_are_mostly_contiguous"
                )

            if len(
                positions
            ) >= 2:

                role_evidence.append(
                    "field_contains_multiple_positions"
                )

            # -------------------------------------------------------
            # Determine interpretation
            # -------------------------------------------------------

            if (
                primary_midi_position
                and field_midi_score >= 85.0
                and group_relationship_score >= 70.0
            ):

                interpretation = (
                    "likely_midi_mapping_field"
                )

            elif (
                primary_midi_position
                and field_midi_score >= 70.0
            ):

                interpretation = (
                    "possible_midi_mapping_field"
                )

            elif (
                group_relationship_score >= 80.0
                and len(positions) >= 2
            ):

                interpretation = (
                    "related_parameter_group"
                )

            elif (
                len(positions) == 1
                and positions[0][
                    "field_type"
                ]
                == "constant_parameter"
            ):

                interpretation = (
                    "constant_parameter_field"
                )

            else:

                interpretation = (
                    "unknown_mapping_field"
                )

            # -------------------------------------------------------
            # Final interpretation score
            # -------------------------------------------------------

            interpretation_score = (
                field_midi_score * 0.40
                + group_relationship_score * 0.30
                + group_consistency_score * 0.20
                + contiguous_ratio * 100.0 * 0.10
            )

            interpretation_score = min(
                interpretation_score,
                100.0,
            )

            # -------------------------------------------------------
            # Confidence
            # -------------------------------------------------------

            if (
                interpretation_score >= 85.0
                and interpretation
                == "likely_midi_mapping_field"
            ):

                field_confidence = (
                    "high"
                )

            elif interpretation_score >= 70.0:

                field_confidence = (
                    "medium"
                )

            else:

                field_confidence = (
                    "low"
                )

            # -------------------------------------------------------
            # MIDI mapping summary
            # -------------------------------------------------------

            midi_mapping = None

            if primary_midi_position:

                midi_mapping = {
                    "relative_offset": (
                        primary_midi_position[
                            "offset"
                        ]
                    ),
                    "field_type": (
                        primary_midi_position[
                            "field_type"
                        ]
                    ),
                    "midi_values": (
                        primary_midi_position[
                            "midi_values"
                        ]
                    ),
                    "midi_note_names": (
                        primary_midi_position[
                            "midi_note_names"
                        ]
                    ),
                    "minimum_value": (
                        primary_midi_position[
                            "minimum_value"
                        ]
                    ),
                    "maximum_value": (
                        primary_midi_position[
                            "maximum_value"
                        ]
                    ),
                    "value_range": (
                        primary_midi_position[
                            "value_range"
                        ]
                    ),
                    "midi_note_score": (
                        primary_midi_position[
                            "midi_note_score"
                        ]
                    ),
                    "confidence": (
                        primary_midi_position[
                            "confidence"
                        ]
                    ),
                }

            # -------------------------------------------------------
            # Final result
            # -------------------------------------------------------

            interpretation_report.append(
                {
                    "field_id": field.get(
                        "field_id"
                    ),
                    "rank": field.get(
                        "rank"
                    ),
                    "offsets": offsets,
                    "start_offset": field.get(
                        "start_offset"
                    ),
                    "end_offset": field.get(
                        "end_offset"
                    ),
                    "field_size": len(
                        offsets
                    ),
                    "field_score": field.get(
                        "group_score",
                        0.0,
                    ),
                    "group_consistency_score": (
                        group_consistency_score
                    ),
                    "group_relationship_score": (
                        group_relationship_score
                    ),
                    "contiguous_ratio": (
                        contiguous_ratio
                    ),
                    "field_midi_score": round(
                        field_midi_score,
                        2,
                    ),
                    "interpretation_score": round(
                        interpretation_score,
                        2,
                    ),
                    "interpretation": (
                        interpretation
                    ),
                    "confidence": (
                        field_confidence
                    ),
                    "midi_mapping": (
                        midi_mapping
                    ),
                    "positions": positions,
                    "evidence": role_evidence,
                }
            )

        # -----------------------------------------------------------
        # Sort strongest interpretations first
        # -----------------------------------------------------------

        interpretation_report.sort(
            key=lambda item: (
                item[
                    "interpretation_score"
                ],
                item[
                    "field_midi_score"
                ],
                item[
                    "group_relationship_score"
                ],
            ),
            reverse=True,
        )

        # -----------------------------------------------------------
        # Re-number ranks
        # -----------------------------------------------------------

        for rank, item in enumerate(
            interpretation_report,
            start=1,
        ):
            item["rank"] = rank

        return interpretation_report

    def find_likely_midi_mapping_fields(
        self,
    ) -> list[dict]:
        """
        Returns fields interpreted as likely
        MIDI mapping fields.
        """

        report = (
            self.analyze_mapping_field_interpretation()
        )

        return [
            item
            for item in report
            if item[
                "interpretation"
            ]
            == "likely_midi_mapping_field"
        ]

    def find_possible_midi_mapping_fields(
        self,
    ) -> list[dict]:
        """
        Returns likely and possible MIDI
        mapping fields.
        """

        report = (
            self.analyze_mapping_field_interpretation()
        )

        return [
            item
            for item in report
            if item[
                "interpretation"
            ]
            in (
                "likely_midi_mapping_field",
                "possible_midi_mapping_field",
            )
        ]

    def build_mapping_interpretation_report(
        self,
    ) -> dict:
        """
        Complete #35 report.
        """

        report = (
            self.analyze_mapping_field_interpretation()
        )

        likely_midi_fields = [
            item
            for item in report
            if item[
                "interpretation"
            ]
            == "likely_midi_mapping_field"
        ]

        possible_midi_fields = [
            item
            for item in report
            if item[
                "interpretation"
            ]
            == "possible_midi_mapping_field"
        ]

        related_parameter_groups = [
            item
            for item in report
            if item[
                "interpretation"
            ]
            == "related_parameter_group"
        ]

        return {
            "drum_kit_count": len(
                self.find_drum_kit_name_records()
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "fields_analyzed": len(
                report
            ),
            "likely_midi_mapping_fields": (
                likely_midi_fields
            ),
            "possible_midi_mapping_fields": (
                possible_midi_fields
            ),
            "related_parameter_groups": (
                related_parameter_groups
            ),
            "all_interpretations": report,
        }
```
