```python
    # ===============================================================
    # #32 MAPPING CONSISTENCY ANALYSIS
    # ===============================================================

    def analyze_mapping_consistency(
        self,
    ) -> list[dict]:
        """
        #32

        Analizira koliko je konzistentno ponašanje svake
        byte pozicije kroz sve pronađene Drum Kit records.

        Cilj:
        - pronaći pozicije koje se mijenjaju na predvidiv način
        - razlikovati stabilne i nestabilne pozicije
        - koristiti postojeće MIDI i change-pattern dokaze
        - NE mijenjati originalni PCG fajl
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        change_patterns = (
            self.analyze_change_patterns()
        )

        consistency_report = []

        for pattern in change_patterns:

            relative_offset = pattern[
                "relative_offset"
            ]

            values = pattern[
                "values"
            ]

            unique_values = sorted(
                set(values)
            )

            record_count = len(values)

            if record_count == 0:
                continue

            # -------------------------------------------------------
            # Basic statistics
            # -------------------------------------------------------

            unique_count = len(
                unique_values
            )

            changed_count = sum(
                1
                for index in range(
                    1,
                    record_count,
                )
                if values[index]
                != values[index - 1]
            )

            unchanged_count = (
                record_count
                - 1
                - changed_count
            )

            transition_count = max(
                record_count - 1,
                0,
            )

            change_ratio = (
                changed_count
                / transition_count
                if transition_count
                else 0.0
            )

            stability_ratio = (
                unchanged_count
                / transition_count
                if transition_count
                else 1.0
            )

            # -------------------------------------------------------
            # MIDI values
            # -------------------------------------------------------

            midi_values = [
                value
                for value in unique_values
                if self.is_midi_value(
                    value
                )
            ]

            midi_ratio = (
                len(midi_values)
                / unique_count
                if unique_count
                else 0.0
            )

            # -------------------------------------------------------
            # Check whether values form a compact range
            # -------------------------------------------------------

            range_score = 0.0

            if midi_values:

                minimum_value = min(
                    midi_values
                )

                maximum_value = max(
                    midi_values
                )

                value_range = (
                    maximum_value
                    - minimum_value
                )

                if value_range <= 12:
                    range_score = 1.0

                elif value_range <= 24:
                    range_score = 0.85

                elif value_range <= 36:
                    range_score = 0.70

                elif value_range <= 48:
                    range_score = 0.50

                else:
                    range_score = 0.25

            else:

                minimum_value = None
                maximum_value = None
                value_range = None

            # -------------------------------------------------------
            # Repeated value evidence
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
            # Consistency score
            # -------------------------------------------------------

            consistency_score = (
                midi_ratio * 25.0
                + range_score * 20.0
                + stability_ratio * 20.0
                + dominant_ratio * 20.0
            )

            # Variable positions receive additional evidence.
            if unique_count > 1:
                consistency_score += 15.0

            consistency_score = min(
                consistency_score,
                100.0,
            )

            # -------------------------------------------------------
            # Evidence
            # -------------------------------------------------------

            evidence = []

            if unique_count == 1:
                evidence.append(
                    "position_is_constant_across_kits"
                )

            if unique_count > 1:
                evidence.append(
                    "position_changes_across_kits"
                )

            if midi_ratio == 1.0:
                evidence.append(
                    "all_unique_values_are_midi_values"
                )

            elif midi_ratio >= 0.75:
                evidence.append(
                    "most_unique_values_are_midi_values"
                )

            if range_score >= 0.85:
                evidence.append(
                    "midi_values_form_compact_range"
                )

            if dominant_ratio >= 0.75:
                evidence.append(
                    "one_value_is_highly_repeated"
                )

            if stability_ratio >= 0.75:
                evidence.append(
                    "position_is_highly_stable"
                )

            if change_ratio >= 0.75:
                evidence.append(
                    "position_changes_frequently"
                )

            # -------------------------------------------------------
            # Classification
            # -------------------------------------------------------

            if (
                consistency_score >= 80.0
                and unique_count > 1
                and midi_ratio >= 0.75
            ):
                classification = (
                    "strong_mapping_candidate"
                )

            elif (
                consistency_score >= 65.0
                and unique_count > 1
            ):
                classification = (
                    "possible_mapping_candidate"
                )

            elif (
                unique_count == 1
            ):
                classification = (
                    "constant_position"
                )

            else:
                classification = (
                    "weak_candidate"
                )

            # -------------------------------------------------------
            # Final result
            # -------------------------------------------------------

            consistency_report.append(
                {
                    "relative_offset": (
                        relative_offset
                    ),
                    "record_count": (
                        record_count
                    ),
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
                    "midi_values": (
                        midi_values
                    ),
                    "midi_note_names": [
                        midi_to_note(value)
                        for value
                        in midi_values
                    ],
                    "minimum_value": (
                        minimum_value
                    ),
                    "maximum_value": (
                        maximum_value
                    ),
                    "value_range": (
                        value_range
                    ),
                    "changed_count": (
                        changed_count
                    ),
                    "unchanged_count": (
                        unchanged_count
                    ),
                    "change_ratio": round(
                        change_ratio,
                        4,
                    ),
                    "stability_ratio": round(
                        stability_ratio,
                        4,
                    ),
                    "midi_ratio": round(
                        midi_ratio,
                        4,
                    ),
                    "range_score": round(
                        range_score,
                        4,
                    ),
                    "dominant_ratio": round(
                        dominant_ratio,
                        4,
                    ),
                    "consistency_score": round(
                        consistency_score,
                        2,
                    ),
                    "classification": (
                        classification
                    ),
                    "evidence": evidence,
                }
            )

        consistency_report.sort(
            key=lambda item: (
                item[
                    "consistency_score"
                ],
                item[
                    "midi_ratio"
                ],
                item[
                    "unique_value_count"
                ],
            ),
            reverse=True,
        )

        for rank, item in enumerate(
            consistency_report,
            start=1,
        ):
            item["rank"] = rank

        return consistency_report

    def find_strong_mapping_candidates(
        self,
    ) -> list[dict]:
        """
        Returns only positions classified as
        strong_mapping_candidate.
        """

        report = (
            self.analyze_mapping_consistency()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            == "strong_mapping_candidate"
        ]

    def find_possible_mapping_candidates(
        self,
    ) -> list[dict]:
        """
        Returns strong and possible mapping
        candidates.
        """

        report = (
            self.analyze_mapping_consistency()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            in (
                "strong_mapping_candidate",
                "possible_mapping_candidate",
            )
        ]

    def build_mapping_consistency_report(
        self,
    ) -> dict:
        """
        Complete #32 report.
        """

        report = (
            self.analyze_mapping_consistency()
        )

        strong_candidates = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "strong_mapping_candidate"
        ]

        possible_candidates = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "possible_mapping_candidate"
        ]

        return {
            "drum_kit_count": len(
                self.find_drum_kit_name_records()
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "positions_analyzed": len(
                report
            ),
            "strong_mapping_candidates": (
                strong_candidates
            ),
            "possible_mapping_candidates": (
                possible_candidates
            ),
            "all_positions": report,
        }
```
