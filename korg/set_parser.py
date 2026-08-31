```python
    # ===============================================================
    # #34 MAPPING FIELD / GROUP DETECTION
    # ===============================================================

    def analyze_mapping_fields(
        self,
    ) -> list[dict]:
        """
        #34

        Analizira rezultate #32 i #33 i pokušava
        formirati funkcionalne mapping grupe.

        Cilj:
        - grupirati povezane byte pozicije
        - koristiti #32 consistency evidence
        - koristiti #33 relationship evidence
        - pronaći potencijalne mapping fieldove
        - rangirati jačinu svake grupe
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

        relationship_report = (
            self.analyze_mapping_relationships()
        )

        if not consistency_report:
            return []

        if not relationship_report:
            return []

        # -----------------------------------------------------------
        # Build lookup tables
        # -----------------------------------------------------------

        consistency_by_offset = {
            item[
                "relative_offset"
            ]: item
            for item in consistency_report
        }

        strong_relationships = [
            item
            for item in relationship_report
            if item[
                "classification"
            ]
            == "strong_related_mapping"
        ]

        possible_relationships = [
            item
            for item in relationship_report
            if item[
                "classification"
            ]
            in (
                "strong_related_mapping",
                "possible_related_mapping",
                "constant_relationship",
            )
        ]

        # -----------------------------------------------------------
        # Candidate offsets
        # -----------------------------------------------------------

        candidate_offsets = set()

        for item in consistency_report:

            classification = item[
                "classification"
            ]

            if classification in (
                "strong_mapping_candidate",
                "possible_mapping_candidate",
            ):
                candidate_offsets.add(
                    item[
                        "relative_offset"
                    ]
                )

        # -----------------------------------------------------------
        # Build relationship graph
        # -----------------------------------------------------------

        graph = {}

        for offset in candidate_offsets:
            graph[offset] = set()

        for relationship in possible_relationships:

            offset_a = relationship[
                "offset_a"
            ]

            offset_b = relationship[
                "offset_b"
            ]

            if (
                offset_a not in candidate_offsets
                and offset_b not in candidate_offsets
            ):
                continue

            graph.setdefault(
                offset_a,
                set(),
            )

            graph.setdefault(
                offset_b,
                set(),
            )

            graph[
                offset_a
            ].add(offset_b)

            graph[
                offset_b
            ].add(offset_a)

        # -----------------------------------------------------------
        # Find connected groups
        # -----------------------------------------------------------

        groups = []

        visited = set()

        for start_offset in sorted(
            graph.keys()
        ):

            if start_offset in visited:
                continue

            stack = [
                start_offset
            ]

            group = set()

            while stack:

                current = stack.pop()

                if current in visited:
                    continue

                visited.add(current)
                group.add(current)

                for neighbor in graph.get(
                    current,
                    set(),
                ):

                    if neighbor not in visited:
                        stack.append(
                            neighbor
                        )

            if group:
                groups.append(
                    sorted(group)
                )

        # -----------------------------------------------------------
        # If no graph groups exist, use individual
        # strong candidates as single-position groups.
        # -----------------------------------------------------------

        if not groups:

            strong_candidates = [
                item
                for item in consistency_report
                if item[
                    "classification"
                ]
                == "strong_mapping_candidate"
            ]

            for item in strong_candidates:

                groups.append(
                    [
                        item[
                            "relative_offset"
                        ]
                    ]
                )

        field_report = []

        # -----------------------------------------------------------
        # Analyze every detected group
        # -----------------------------------------------------------

        for group_index, offsets in enumerate(
            groups,
            start=1,
        ):

            if not offsets:
                continue

            position_reports = []

            for offset in offsets:

                report = (
                    consistency_by_offset.get(
                        offset
                    )
                )

                if report:
                    position_reports.append(
                        report
                    )

            if not position_reports:
                continue

            # -------------------------------------------------------
            # Group-level consistency
            # -------------------------------------------------------

            consistency_scores = [
                item[
                    "consistency_score"
                ]
                for item in position_reports
            ]

            midi_ratios = [
                item[
                    "midi_ratio"
                ]
                for item in position_reports
            ]

            group_consistency_score = (
                sum(
                    consistency_scores
                )
                / len(
                    consistency_scores
                )
            )

            group_midi_ratio = (
                sum(
                    midi_ratios
                )
                / len(
                    midi_ratios
                )
            )

            # -------------------------------------------------------
            # Relationship evidence inside group
            # -------------------------------------------------------

            internal_relationships = []

            for relationship in relationship_report:

                offset_a = relationship[
                    "offset_a"
                ]

                offset_b = relationship[
                    "offset_b"
                ]

                if (
                    offset_a in offsets
                    and offset_b in offsets
                ):
                    internal_relationships.append(
                        relationship
                    )

            relationship_scores = [
                item[
                    "relationship_score"
                ]
                for item in internal_relationships
            ]

            group_relationship_score = (
                sum(
                    relationship_scores
                )
                / len(
                    relationship_scores
                )
                if relationship_scores
                else 0.0
            )

            strong_internal_count = sum(
                1
                for item
                in internal_relationships
                if item[
                    "classification"
                ]
                == "strong_related_mapping"
            )

            possible_internal_count = sum(
                1
                for item
                in internal_relationships
                if item[
                    "classification"
                ]
                in (
                    "strong_related_mapping",
                    "possible_related_mapping",
                    "constant_relationship",
                )
            )

            # -------------------------------------------------------
            # Group size evidence
            # -------------------------------------------------------

            group_size = len(
                offsets
            )

            if group_size == 1:
                size_score = 0.50

            elif group_size == 2:
                size_score = 0.85

            elif group_size <= 4:
                size_score = 1.00

            elif group_size <= 8:
                size_score = 0.85

            else:
                size_score = 0.65

            # -------------------------------------------------------
            # Contiguous offset evidence
            # -------------------------------------------------------

            contiguous_count = 0

            for i in range(
                1,
                len(offsets),
            ):

                if (
                    offsets[i]
                    == offsets[i - 1] + 1
                ):
                    contiguous_count += 1

            possible_contiguous_links = max(
                len(offsets) - 1,
                0,
            )

            contiguous_ratio = (
                contiguous_count
                / possible_contiguous_links
                if possible_contiguous_links
                else 1.0
            )

            # -------------------------------------------------------
            # Group score
            # -------------------------------------------------------

            group_score = (
                group_consistency_score
                * 0.30
                + group_relationship_score
                * 0.35
                + group_midi_ratio
                * 100.0
                * 0.15
                + size_score
                * 100.0
                * 0.10
                + contiguous_ratio
                * 100.0
                * 0.10
            )

            group_score = min(
                group_score,
                100.0,
            )

            # -------------------------------------------------------
            # Evidence
            # -------------------------------------------------------

            evidence = []

            if group_size >= 2:
                evidence.append(
                    "multiple_related_positions_form_group"
                )

            if strong_internal_count > 0:
                evidence.append(
                    "group_contains_strong_relationships"
                )

            if (
                possible_internal_count
                >= max(
                    group_size - 1,
                    1,
                )
            ):
                evidence.append(
                    "most_group_positions_are_relationship_connected"
                )

            if group_consistency_score >= 80.0:
                evidence.append(
                    "group_positions_have_high_consistency"
                )

            elif group_consistency_score >= 65.0:
                evidence.append(
                    "group_positions_have_moderate_consistency"
                )

            if group_midi_ratio >= 0.75:
                evidence.append(
                    "group_has_strong_midi_value_evidence"
                )

            elif group_midi_ratio >= 0.50:
                evidence.append(
                    "group_has_partial_midi_value_evidence"
                )

            if contiguous_ratio >= 0.75:
                evidence.append(
                    "group_positions_are_mostly_contiguous"
                )

            if group_relationship_score >= 80.0:
                evidence.append(
                    "group_has_strong_internal_relationship"
                )

            # -------------------------------------------------------
            # Classification
            # -------------------------------------------------------

            if (
                group_score >= 80.0
                and group_size >= 2
                and (
                    strong_internal_count >= 1
                    or group_relationship_score
                    >= 80.0
                )
            ):
                classification = (
                    "strong_mapping_field"
                )

            elif (
                group_score >= 65.0
                and group_size >= 2
            ):
                classification = (
                    "possible_mapping_field"
                )

            elif (
                group_size == 1
                and group_consistency_score
                >= 80.0
            ):
                classification = (
                    "single_position_mapping_field"
                )

            else:
                classification = (
                    "weak_mapping_field"
                )

            # -------------------------------------------------------
            # Collect values for each offset
            # -------------------------------------------------------

            group_values = {}

            for offset in offsets:

                report = (
                    consistency_by_offset.get(
                        offset
                    )
                )

                if report:

                    group_values[
                        offset
                    ] = {
                        "unique_values": (
                            report[
                                "unique_values"
                            ]
                        ),
                        "hex_values": (
                            report[
                                "hex_values"
                            ]
                        ),
                        "midi_values": (
                            report[
                                "midi_values"
                            ]
                        ),
                        "midi_note_names": (
                            report[
                                "midi_note_names"
                            ]
                        ),
                        "consistency_score": (
                            report[
                                "consistency_score"
                            ]
                        ),
                        "classification": (
                            report[
                                "classification"
                            ]
                        ),
                    }

            # -------------------------------------------------------
            # Relationship summary
            # -------------------------------------------------------

            relationship_summary = []

            for relationship in internal_relationships:

                relationship_summary.append(
                    {
                        "offset_a": (
                            relationship[
                                "offset_a"
                            ]
                        ),
                        "offset_b": (
                            relationship[
                                "offset_b"
                            ]
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

            # -------------------------------------------------------
            # Final group result
            # -------------------------------------------------------

            field_report.append(
                {
                    "field_id": (
                        f"MAPPING_FIELD_{group_index:03d}"
                    ),
                    "offsets": offsets,
                    "start_offset": min(
                        offsets
                    ),
                    "end_offset": max(
                        offsets
                    ),
                    "field_size": group_size,
                    "contiguous_ratio": round(
                        contiguous_ratio,
                        4,
                    ),
                    "group_consistency_score": round(
                        group_consistency_score,
                        2,
                    ),
                    "group_midi_ratio": round(
                        group_midi_ratio,
                        4,
                    ),
                    "group_relationship_score": round(
                        group_relationship_score,
                        2,
                    ),
                    "strong_internal_relationships": (
                        strong_internal_count
                    ),
                    "possible_internal_relationships": (
                        possible_internal_count
                    ),
                    "group_score": round(
                        group_score,
                        2,
                    ),
                    "classification": (
                        classification
                    ),
                    "evidence": evidence,
                    "positions": group_values,
                    "relationships": (
                        relationship_summary
                    ),
                }
            )

        # -----------------------------------------------------------
        # Sort strongest fields first
        # -----------------------------------------------------------

        field_report.sort(
            key=lambda item: (
                item[
                    "group_score"
                ],
                item[
                    "group_relationship_score"
                ],
                item[
                    "group_consistency_score"
                ],
                item[
                    "group_midi_ratio"
                ],
            ),
            reverse=True,
        )

        # -----------------------------------------------------------
        # Re-number ranks
        # -----------------------------------------------------------

        for rank, item in enumerate(
            field_report,
            start=1,
        ):
            item["rank"] = rank

        return field_report

    def find_strong_mapping_fields(
        self,
    ) -> list[dict]:
        """
        Returns only strong mapping fields.
        """

        report = (
            self.analyze_mapping_fields()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            == "strong_mapping_field"
        ]

    def find_possible_mapping_fields(
        self,
    ) -> list[dict]:
        """
        Returns strong, possible and
        single-position mapping fields.
        """

        report = (
            self.analyze_mapping_fields()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            in (
                "strong_mapping_field",
                "possible_mapping_field",
                "single_position_mapping_field",
            )
        ]

    def build_mapping_field_report(
        self,
    ) -> dict:
        """
        Complete #34 report.
        """

        report = (
            self.analyze_mapping_fields()
        )

        strong_fields = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "strong_mapping_field"
        ]

        possible_fields = [
            item
            for item in report
            if item[
                "classification"
            ]
            in (
                "possible_mapping_field",
                "single_position_mapping_field",
            )
        ]

        return {
            "drum_kit_count": len(
                self.find_drum_kit_name_records()
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "fields_detected": len(
                report
            ),
            "strong_mapping_fields": (
                strong_fields
            ),
            "possible_mapping_fields": (
                possible_fields
            ),
            "all_fields": report,
        }
```
