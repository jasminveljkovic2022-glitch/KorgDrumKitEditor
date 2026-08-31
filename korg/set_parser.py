```python id="73m2kx"
    # ===============================================================
    # #36 MIDI MAPPING VALIDATION
    # ===============================================================

    def validate_midi_mapping_candidates(
        self,
    ) -> list[dict]:
        """
        #36

        Validira MIDI mapping kandidate pronađene
        kroz #32, #33, #34 i #35.

        Cilj:
        - provjeriti da li kandidati zaista izgledaju
          kao MIDI note vrijednosti
        - provjeriti kontinuitet i raspon vrijednosti
        - provjeriti ponašanje kroz sve Drum Kit records
        - koristiti dodatne cross-record dokaze
        - izračunati validation score
        - NE mijenjati originalni PCG/SET fajl
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        interpretation_report = (
            self.analyze_mapping_field_interpretation()
        )

        if not interpretation_report:
            return []

        validation_report = []

        # -----------------------------------------------------------
        # Helper: MIDI range
        # -----------------------------------------------------------

        def is_valid_midi_note(
            value,
        ):
            return (
                isinstance(
                    value,
                    int,
                )
                and 0 <= value <= 127
            )

        # -----------------------------------------------------------
        # Helper: note range
        # -----------------------------------------------------------

        def note_range_score(
            values,
        ):

            if not values:
                return 0.0

            valid_values = [
                value
                for value in values
                if is_valid_midi_note(
                    value
                )
            ]

            if not valid_values:
                return 0.0

            minimum = min(
                valid_values
            )

            maximum = max(
                valid_values
            )

            value_range = (
                maximum - minimum
            )

            if value_range <= 12:
                return 1.0

            if value_range <= 24:
                return 0.90

            if value_range <= 36:
                return 0.80

            if value_range <= 48:
                return 0.65

            if value_range <= 72:
                return 0.45

            return 0.25

        # -----------------------------------------------------------
        # Analyze every interpreted field
        # -----------------------------------------------------------

        for field in interpretation_report:

            interpretation = field.get(
                "interpretation"
            )

            if interpretation not in (
                "likely_midi_mapping_field",
                "possible_midi_mapping_field",
            ):
                continue

            midi_mapping = field.get(
                "midi_mapping"
            )

            if not midi_mapping:
                continue

            offset = midi_mapping.get(
                "relative_offset"
            )

            if offset is None:
                continue

            # -------------------------------------------------------
            # Extract values directly from records
            # -------------------------------------------------------

            values = []

            for record in records:

                try:
                    value = record[
                        offset
                    ]
                except (
                    IndexError,
                    TypeError,
                ):
                    continue

                values.append(
                    value
                )

            if not values:
                continue

            # -------------------------------------------------------
            # Basic value analysis
            # -------------------------------------------------------

            record_count = len(
                values
            )

            unique_values = sorted(
                set(values)
            )

            unique_count = len(
                unique_values
            )

            valid_midi_values = [
                value
                for value in unique_values
                if is_valid_midi_note(
                    value
                )
            ]

            invalid_values = [
                value
                for value in unique_values
                if not is_valid_midi_note(
                    value
                )
            ]

            midi_ratio = (
                len(
                    valid_midi_values
                )
                / unique_count
                if unique_count
                else 0.0
            )

            # -------------------------------------------------------
            # Sequential change behavior
            # -------------------------------------------------------

            transitions = max(
                record_count - 1,
                0,
            )

            changed_count = 0
            valid_transition_count = 0

            for i in range(
                1,
                record_count,
            ):

                previous = values[
                    i - 1
                ]

                current = values[
                    i
                ]

                if previous != current:
                    changed_count += 1

                if (
                    is_valid_midi_note(
                        previous
                    )
                    and
                    is_valid_midi_note(
                        current
                    )
                ):
                    valid_transition_count += 1

            change_ratio = (
                changed_count
                / transitions
                if transitions
                else 0.0
            )

            valid_transition_ratio = (
                valid_transition_count
                / transitions
                if transitions
                else 1.0
            )

            # -------------------------------------------------------
            # Range
            # -------------------------------------------------------

            if valid_midi_values:

                minimum_value = min(
                    valid_midi_values
                )

                maximum_value = max(
                    valid_midi_values
                )

                value_range = (
                    maximum_value
                    - minimum_value
                )

            else:

                minimum_value = None
                maximum_value = None
                value_range = None

            compact_range_score = (
                note_range_score(
                    valid_midi_values
                )
            )

            # -------------------------------------------------------
            # Duplicate / frequency analysis
            # -------------------------------------------------------

            frequency = {}

            for value in values:

                frequency[value] = (
                    frequency.get(
                        value,
                        0,
                    )
                    + 1
                )

            max_frequency = (
                max(
                    frequency.values()
                )
                if frequency
                else 0
            )

            dominant_ratio = (
                max_frequency
                / record_count
                if record_count
                else 0.0
            )

            # -------------------------------------------------------
            # Detect ascending / descending note movement
            # -------------------------------------------------------

            ascending_count = 0
            descending_count = 0
            nonzero_transitions = 0

            for i in range(
                1,
                record_count,
            ):

                delta = (
                    values[i]
                    - values[i - 1]
                )

                if delta > 0:

                    ascending_count += 1
                    nonzero_transitions += 1

                elif delta < 0:

                    descending_count += 1
                    nonzero_transitions += 1

            ascending_ratio = (
                ascending_count
                / nonzero_transitions
                if nonzero_transitions
                else 0.0
            )

            descending_ratio = (
                descending_count
                / nonzero_transitions
                if nonzero_transitions
                else 0.0
            )

            # -------------------------------------------------------
            # MIDI note name conversion
            # -------------------------------------------------------

            midi_note_names = []

            for value in valid_midi_values:

                try:
                    midi_note_names.append(
                        midi_to_note(
                            value
                        )
                    )
                except Exception:
                    midi_note_names.append(
                        None
                    )

            # -------------------------------------------------------
            # Field-level scores
            # -------------------------------------------------------

            midi_validity_score = (
                midi_ratio
                * 100.0
            )

            transition_score = (
                valid_transition_ratio
                * 100.0
            )

            # A MIDI mapping normally changes between kits,
            # but does not need to change constantly.
            behavior_score = 0.0

            if (
                0.05
                <= change_ratio
                <= 0.95
            ):
                behavior_score = 100.0

            elif change_ratio == 0.0:
                behavior_score = 55.0

            else:
                behavior_score = 70.0

            # -------------------------------------------------------
            # Combined validation score
            # -------------------------------------------------------

            validation_score = (
                midi_validity_score
                * 0.35
                + compact_range_score
                * 100.0
                * 0.20
                + transition_score
                * 0.15
                + behavior_score
                * 0.15
                + field.get(
                    "field_midi_score",
                    0.0,
                )
                * 0.10
                + field.get(
                    "group_relationship_score",
                    0.0,
                )
                * 0.05
            )

            validation_score = min(
                validation_score,
                100.0,
            )

            # -------------------------------------------------------
            # Validation evidence
            # -------------------------------------------------------

            evidence = []

            if midi_ratio >= 1.0:

                evidence.append(
                    "all_unique_values_are_valid_midi_notes"
                )

            elif midi_ratio >= 0.90:

                evidence.append(
                    "almost_all_unique_values_are_valid_midi_notes"
                )

            elif midi_ratio >= 0.75:

                evidence.append(
                    "most_unique_values_are_valid_midi_notes"
                )

            if compact_range_score >= 0.90:

                evidence.append(
                    "midi_values_have_compact_note_range"
                )

            elif compact_range_score >= 0.70:

                evidence.append(
                    "midi_values_have_reasonable_note_range"
                )

            if valid_transition_ratio >= 0.90:

                evidence.append(
                    "transitions_are_midi_valid"
                )

            if (
                change_ratio > 0.0
                and change_ratio < 1.0
            ):

                evidence.append(
                    "mapping_value_changes_between_some_kits"
                )

            if (
                ascending_ratio >= 0.75
                or descending_ratio >= 0.75
            ):

                evidence.append(
                    "mapping_values_show_directional_change_pattern"
                )

            if (
                field.get(
                    "group_relationship_score",
                    0.0,
                )
                >= 80.0
            ):

                evidence.append(
                    "field_has_strong_relationship_evidence"
                )

            # -------------------------------------------------------
            # Detect suspicious conditions
            # -------------------------------------------------------

            warnings = []

            if invalid_values:

                warnings.append(
                    "contains_values_outside_midi_range"
                )

            if unique_count == 1:

                warnings.append(
                    "value_is_constant_across_all_records"
                )

            if (
                dominant_ratio >= 0.95
                and unique_count > 1
            ):

                warnings.append(
                    "one_value_dominates_the_mapping"
                )

            if (
                value_range is not None
                and value_range > 72
            ):

                warnings.append(
                    "mapping_range_is_wide"
                )

            # -------------------------------------------------------
            # Final validation classification
            # -------------------------------------------------------

            if (
                validation_score >= 85.0
                and midi_ratio >= 0.90
                and not invalid_values
            ):

                validation = (
                    "validated_midi_mapping"
                )

                confidence = (
                    "high"
                )

            elif (
                validation_score >= 70.0
                and midi_ratio >= 0.75
            ):

                validation = (
                    "probable_midi_mapping"
                )

                confidence = (
                    "medium"
                )

            elif (
                validation_score >= 55.0
                and midi_ratio >= 0.50
            ):

                validation = (
                    "possible_midi_mapping"
                )

                confidence = (
                    "low"
                )

            else:

                validation = (
                    "unvalidated_mapping"
                )

                confidence = (
                    "low"
                )

            # -------------------------------------------------------
            # Final result
            # -------------------------------------------------------

            validation_report.append(
                {
                    "field_id": field.get(
                        "field_id"
                    ),
                    "relative_offset": offset,
                    "offsets": field.get(
                        "offsets",
                        [],
                    ),
                    "record_count": record_count,
                    "unique_value_count": (
                        unique_count
                    ),
                    "unique_values": (
                        unique_values
                    ),
                    "hex_values": [
                        f"{value:02X}"
                        for value
                        in unique_values
                    ],
                    "valid_midi_values": (
                        valid_midi_values
                    ),
                    "invalid_values": (
                        invalid_values
                    ),
                    "midi_note_names": (
                        midi_note_names
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
                    "midi_ratio": round(
                        midi_ratio,
                        4,
                    ),
                    "change_ratio": round(
                        change_ratio,
                        4,
                    ),
                    "valid_transition_ratio": round(
                        valid_transition_ratio,
                        4,
                    ),
                    "dominant_ratio": round(
                        dominant_ratio,
                        4,
                    ),
                    "ascending_ratio": round(
                        ascending_ratio,
                        4,
                    ),
                    "descending_ratio": round(
                        descending_ratio,
                        4,
                    ),
                    "compact_range_score": round(
                        compact_range_score,
                        4,
                    ),
                    "midi_validity_score": round(
                        midi_validity_score,
                        2,
                    ),
                    "behavior_score": round(
                        behavior_score,
                        2,
                    ),
                    "field_midi_score": field.get(
                        "field_midi_score",
                        0.0,
                    ),
                    "group_relationship_score": field.get(
                        "group_relationship_score",
                        0.0,
                    ),
                    "validation_score": round(
                        validation_score,
                        2,
                    ),
                    "validation": (
                        validation
                    ),
                    "confidence": (
                        confidence
                    ),
                    "evidence": evidence,
                    "warnings": warnings,
                }
            )

        # -----------------------------------------------------------
        # Sort strongest validations first
        # -----------------------------------------------------------

        validation_report.sort(
            key=lambda item: (
                item[
                    "validation_score"
                ],
                item[
                    "midi_ratio"
                ],
                item[
                    "compact_range_score"
                ],
                item[
                    "valid_transition_ratio"
                ],
            ),
            reverse=True,
        )

        # -----------------------------------------------------------
        # Add rank
        # -----------------------------------------------------------

        for rank, item in enumerate(
            validation_report,
            start=1,
        ):
            item["rank"] = rank

        return validation_report

    def find_validated_midi_mappings(
        self,
    ) -> list[dict]:
        """
        Returns only highly validated MIDI mappings.
        """

        report = (
            self.validate_midi_mapping_candidates()
        )

        return [
            item
            for item in report
            if item[
                "validation"
            ]
            == "validated_midi_mapping"
        ]

    def find_probable_midi_mappings(
        self,
    ) -> list[dict]:
        """
        Returns validated and probable MIDI mappings.
        """

        report = (
            self.validate_midi_mapping_candidates()
        )

        return [
            item
            for item in report
            if item[
                "validation"
            ]
            in (
                "validated_midi_mapping",
                "probable_midi_mapping",
            )
        ]

    def build_midi_validation_report(
        self,
    ) -> dict:
        """
        Complete #36 MIDI validation report.
        """

        report = (
            self.validate_midi_mapping_candidates()
        )

        validated = [
            item
            for item in report
            if item[
                "validation"
            ]
            == "validated_midi_mapping"
        ]

        probable = [
            item
            for item in report
            if item[
                "validation"
            ]
            == "probable_midi_mapping"
        ]

        possible = [
            item
            for item in report
            if item[
                "validation"
            ]
            == "possible_midi_mapping"
        ]

        return {
            "drum_kit_count": len(
                self.find_drum_kit_name_records()
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "candidates_validated": len(
                report
            ),
            "validated_midi_mappings": (
                validated
            ),
            "probable_midi_mappings": (
                probable
            ),
            "possible_midi_mappings": (
                possible
            ),
            "all_validations": report,
        }
```
