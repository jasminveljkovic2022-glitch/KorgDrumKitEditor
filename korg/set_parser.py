```python
    # ===============================================================
    # #33 MAPPING RELATIONSHIP ANALYSIS
    # ===============================================================

    def analyze_mapping_relationships(
        self,
    ) -> list[dict]:
        """
        #33

        Analizira odnose između byte pozicija kroz
        sve pronađene Drum Kit records.

        Cilj:
        - pronaći pozicije koje se mijenjaju zajedno
        - otkriti povezane mapping pozicije
        - pronaći konstantne odnose između byte vrijednosti
        - koristiti rezultate #32 kao dodatni dokaz
        - NE mijenjati originalni PCG fajl
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        consistency_report = (
            self.analyze_mapping_consistency()
        )

        if not consistency_report:
            return []

        # -----------------------------------------------------------
        # Build value table
        # -----------------------------------------------------------

        position_values = {}

        for item in consistency_report:

            offset = item[
                "relative_offset"
            ]

            position_values[
                offset
            ] = []

        # -----------------------------------------------------------
        # Read values from all records
        # -----------------------------------------------------------

        for record in records:

            for offset in position_values:

                try:
                    value = record[
                        offset
                    ]
                except (
                    IndexError,
                    TypeError,
                ):
                    continue

                position_values[
                    offset
                ].append(value)

        offsets = sorted(
            position_values.keys()
        )

        relationships = []

        # -----------------------------------------------------------
        # Analyze every pair of positions
        # -----------------------------------------------------------

        for index, offset_a in enumerate(
            offsets
        ):

            values_a = position_values[
                offset_a
            ]

            if not values_a:
                continue

            for offset_b in offsets[
                index + 1:
            ]:

                values_b = position_values[
                    offset_b
                ]

                if not values_b:
                    continue

                record_count = min(
                    len(values_a),
                    len(values_b),
                )

                if record_count < 2:
                    continue

                values_a = values_a[
                    :record_count
                ]

                values_b = values_b[
                    :record_count
                ]

                # ---------------------------------------------------
                # Basic relationship statistics
                # ---------------------------------------------------

                pair_values = list(
                    zip(
                        values_a,
                        values_b,
                    )
                )

                unique_pairs = sorted(
                    set(pair_values)
                )

                # ---------------------------------------------------
                # Detect simultaneous changes
                # ---------------------------------------------------

                transitions = (
                    record_count - 1
                )

                co_change_count = 0
                change_a_count = 0
                change_b_count = 0
                same_direction_count = 0

                for i in range(
                    1,
                    record_count,
                ):

                    previous_a = (
                        values_a[i - 1]
                    )

                    current_a = (
                        values_a[i]
                    )

                    previous_b = (
                        values_b[i - 1]
                    )

                    current_b = (
                        values_b[i]
                    )

                    delta_a = (
                        current_a
                        - previous_a
                    )

                    delta_b = (
                        current_b
                        - previous_b
                    )

                    changed_a = (
                        delta_a != 0
                    )

                    changed_b = (
                        delta_b != 0
                    )

                    if changed_a:
                        change_a_count += 1

                    if changed_b:
                        change_b_count += 1

                    if (
                        changed_a
                        and changed_b
                    ):
                        co_change_count += 1

                        if (
                            (
                                delta_a > 0
                                and delta_b > 0
                            )
                            or
                            (
                                delta_a < 0
                                and delta_b < 0
                            )
                        ):
                            same_direction_count += 1

                # ---------------------------------------------------
                # Ratios
                # ---------------------------------------------------

                co_change_ratio = (
                    co_change_count
                    / transitions
                    if transitions
                    else 0.0
                )

                change_a_ratio = (
                    change_a_count
                    / transitions
                    if transitions
                    else 0.0
                )

                change_b_ratio = (
                    change_b_count
                    / transitions
                    if transitions
                    else 0.0
                )

                direction_ratio = (
                    same_direction_count
                    / co_change_count
                    if co_change_count
                    else 0.0
                )

                # ---------------------------------------------------
                # Constant difference analysis
                # ---------------------------------------------------

                deltas = [
                    b - a
                    for a, b
                    in pair_values
                ]

                unique_deltas = sorted(
                    set(deltas)
                )

                constant_delta = (
                    unique_deltas[0]
                    if len(unique_deltas) == 1
                    else None
                )

                delta_consistency = (
                    1.0
                    if len(unique_deltas) == 1
                    else (
                        1.0
                        / len(unique_deltas)
                    )
                )

                # ---------------------------------------------------
                # Equality relationship
                # ---------------------------------------------------

                equal_count = sum(
                    1
                    for a, b
                    in pair_values
                    if a == b
                )

                equality_ratio = (
                    equal_count
                    / record_count
                    if record_count
                    else 0.0
                )

                # ---------------------------------------------------
                # Simple correlation
                # ---------------------------------------------------

                mean_a = (
                    sum(values_a)
                    / record_count
                )

                mean_b = (
                    sum(values_b)
                    / record_count
                )

                numerator = sum(
                    (
                        a - mean_a
                    )
                    * (
                        b - mean_b
                    )
                    for a, b
                    in pair_values
                )

                denominator_a = sum(
                    (
                        a - mean_a
                    ) ** 2
                    for a in values_a
                )

                denominator_b = sum(
                    (
                        b - mean_b
                    ) ** 2
                    for b in values_b
                )

                denominator = (
                    denominator_a
                    * denominator_b
                ) ** 0.5

                correlation = (
                    numerator
                    / denominator
                    if denominator
                    else 0.0
                )

                # ---------------------------------------------------
                # Get #32 evidence
                # ---------------------------------------------------

                report_a = next(
                    (
                        item
                        for item
                        in consistency_report
                        if item[
                            "relative_offset"
                        ]
                        == offset_a
                    ),
                    None,
                )

                report_b = next(
                    (
                        item
                        for item
                        in consistency_report
                        if item[
                            "relative_offset"
                        ]
                        == offset_b
                    ),
                    None,
                )

                score_a = (
                    report_a[
                        "consistency_score"
                    ]
                    if report_a
                    else 0.0
                )

                score_b = (
                    report_b[
                        "consistency_score"
                    ]
                    if report_b
                    else 0.0
                )

                midi_a = (
                    report_a[
                        "midi_ratio"
                    ]
                    if report_a
                    else 0.0
                )

                midi_b = (
                    report_b[
                        "midi_ratio"
                    ]
                    if report_b
                    else 0.0
                )

                # ---------------------------------------------------
                # Relationship score
                # ---------------------------------------------------

                relationship_score = (
                    co_change_ratio * 30.0
                    + direction_ratio * 15.0
                    + abs(correlation) * 20.0
                    + delta_consistency * 15.0
                    + max(
                        midi_a,
                        midi_b,
                    ) * 10.0
                    + (
                        (
                            score_a
                            + score_b
                        )
                        / 200.0
                    )
                    * 10.0
                )

                relationship_score = min(
                    relationship_score,
                    100.0,
                )

                # ---------------------------------------------------
                # Evidence
                # ---------------------------------------------------

                evidence = []

                if co_change_ratio >= 0.75:
                    evidence.append(
                        "positions_change_together_frequently"
                    )

                elif co_change_ratio >= 0.50:
                    evidence.append(
                        "positions_show_moderate_co_change"
                    )

                if direction_ratio >= 0.90:
                    evidence.append(
                        "changes_usually_move_in_same_direction"
                    )

                if constant_delta is not None:
                    evidence.append(
                        "constant_value_relationship"
                    )

                if equality_ratio >= 0.75:
                    evidence.append(
                        "positions_often_have_equal_values"
                    )

                if abs(correlation) >= 0.90:
                    evidence.append(
                        "strong_statistical_correlation"
                    )

                if (
                    midi_a >= 0.75
                    or midi_b >= 0.75
                ):
                    evidence.append(
                        "one_or_both_positions_have_midi_evidence"
                    )

                # ---------------------------------------------------
                # Classification
                # ---------------------------------------------------

                if (
                    relationship_score >= 80.0
                    and co_change_ratio >= 0.75
                    and abs(correlation) >= 0.80
                ):
                    classification = (
                        "strong_related_mapping"
                    )

                elif (
                    relationship_score >= 65.0
                    and (
                        co_change_ratio >= 0.50
                        or abs(correlation) >= 0.70
                    )
                ):
                    classification = (
                        "possible_related_mapping"
                    )

                elif (
                    constant_delta is not None
                    and record_count >= 3
                ):
                    classification = (
                        "constant_relationship"
                    )

                else:
                    classification = (
                        "weak_relationship"
                    )

                # ---------------------------------------------------
                # Final result
                # ---------------------------------------------------

                relationships.append(
                    {
                        "offset_a": offset_a,
                        "offset_b": offset_b,
                        "record_count": record_count,
                        "unique_pair_count": len(
                            unique_pairs
                        ),
                        "unique_pairs": (
                            unique_pairs
                        ),
                        "co_change_count": (
                            co_change_count
                        ),
                        "change_a_count": (
                            change_a_count
                        ),
                        "change_b_count": (
                            change_b_count
                        ),
                        "co_change_ratio": round(
                            co_change_ratio,
                            4,
                        ),
                        "change_a_ratio": round(
                            change_a_ratio,
                            4,
                        ),
                        "change_b_ratio": round(
                            change_b_ratio,
                            4,
                        ),
                        "same_direction_count": (
                            same_direction_count
                        ),
                        "direction_ratio": round(
                            direction_ratio,
                            4,
                        ),
                        "unique_deltas": (
                            unique_deltas
                        ),
                        "constant_delta": (
                            constant_delta
                        ),
                        "delta_consistency": round(
                            delta_consistency,
                            4,
                        ),
                        "equal_count": (
                            equal_count
                        ),
                        "equality_ratio": round(
                            equality_ratio,
                            4,
                        ),
                        "correlation": round(
                            correlation,
                            4,
                        ),
                        "position_a_score": (
                            score_a
                        ),
                        "position_b_score": (
                            score_b
                        ),
                        "position_a_midi_ratio": (
                            midi_a
                        ),
                        "position_b_midi_ratio": (
                            midi_b
                        ),
                        "relationship_score": round(
                            relationship_score,
                            2,
                        ),
                        "classification": (
                            classification
                        ),
                        "evidence": evidence,
                    }
                )

        # -----------------------------------------------------------
        # Sort strongest relationships first
        # -----------------------------------------------------------

        relationships.sort(
            key=lambda item: (
                item[
                    "relationship_score"
                ],
                item[
                    "co_change_ratio"
                ],
                abs(
                    item[
                        "correlation"
                    ]
                ),
            ),
            reverse=True,
        )

        # -----------------------------------------------------------
        # Add rank
        # -----------------------------------------------------------

        for rank, item in enumerate(
            relationships,
            start=1,
        ):
            item["rank"] = rank

        return relationships

    def find_strong_mapping_relationships(
        self,
    ) -> list[dict]:
        """
        Returns only strong mapping relationships.
        """

        report = (
            self.analyze_mapping_relationships()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            == "strong_related_mapping"
        ]

    def find_possible_mapping_relationships(
        self,
    ) -> list[dict]:
        """
        Returns strong, possible and constant
        mapping relationships.
        """

        report = (
            self.analyze_mapping_relationships()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            in (
                "strong_related_mapping",
                "possible_related_mapping",
                "constant_relationship",
            )
        ]

    def build_mapping_relationship_report(
        self,
    ) -> dict:
        """
        Complete #33 report.
        """

        report = (
            self.analyze_mapping_relationships()
        )

        strong_relationships = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "strong_related_mapping"
        ]

        possible_relationships = [
            item
            for item in report
            if item[
                "classification"
            ]
            in (
                "possible_related_mapping",
                "constant_relationship",
            )
        ]

        return {
            "drum_kit_count": len(
                self.find_drum_kit_name_records()
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "relationships_analyzed": len(
                report
            ),
            "strong_relationships": (
                strong_relationships
            ),
            "possible_relationships": (
                possible_relationships
            ),
            "all_relationships": report,
        }
```
