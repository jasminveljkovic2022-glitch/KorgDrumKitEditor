```python
    # ===============================================================
    # #39 MAPPING CONFIDENCE & FINAL VERIFICATION
    # ===============================================================

    def verify_mapping_confidence(
        self,
    ) -> list[dict]:
        """
        #39

        Završna provjera MIDI mapping kandidata.

        Koristi rezultate:
        #32 - Mapping Consistency
        #33 - Mapping Relationships
        #34 - Mapping Field Detection
        #35 - Mapping Field Interpretation
        #36 - MIDI Mapping Validation
        #37 - Drum Kit Structure Reconstruction
        #38 - Human-Readable Report

        Cilj:
        - objediniti sve prethodne dokaze
        - izračunati final confidence score
        - razlikovati potvrđene i vjerovatne mapping pozicije
        - detektirati konflikte
        - provjeriti stabilnost kroz Drum Kit records
        - NE mijenjati originalni PCG/SET fajl
        """

        consistency_report = (
            self.analyze_mapping_consistency()
        )

        interpretation_report = (
            self.analyze_mapping_field_interpretation()
        )

        validation_report = (
            self.validate_midi_mapping_candidates()
        )

        structure_report = (
            self.reconstruct_drum_kit_structure()
        )

        if not validation_report:
            return []

        consistency_by_offset = {
            item[
                "relative_offset"
            ]: item
            for item in consistency_report
        }

        interpretation_by_offset = {}

        for item in interpretation_report:

            for offset in item.get(
                "offsets",
                [],
            ):

                interpretation_by_offset[
                    offset
                ] = item

        structure_by_offset = {}

        for kit in structure_report:

            for mapping in kit.get(
                "midi_mapping_positions",
                [],
            ):

                offset = mapping.get(
                    "relative_offset"
                )

                if offset is not None:
                    structure_by_offset.setdefault(
                        offset,
                        []
                    ).append(
                        mapping
                    )

        final_report = []

        # -----------------------------------------------------------
        # Verify every candidate
        # -----------------------------------------------------------

        for validation in validation_report:

            offset = validation.get(
                "relative_offset"
            )

            if offset is None:
                continue

            consistency = (
                consistency_by_offset.get(
                    offset,
                    {},
                )
            )

            interpretation = (
                interpretation_by_offset.get(
                    offset,
                    {},
                )
            )

            structure_evidence = (
                structure_by_offset.get(
                    offset,
                    [],
                )
            )

            # -------------------------------------------------------
            # Scores
            # -------------------------------------------------------

            validation_score = float(
                validation.get(
                    "validation_score",
                    0.0,
                )
            )

            consistency_score = float(
                consistency.get(
                    "consistency_score",
                    0.0,
                )
            )

            interpretation_score = float(
                interpretation.get(
                    "interpretation_score",
                    0.0,
                )
            )

            midi_ratio = float(
                validation.get(
                    "midi_ratio",
                    0.0,
                )
            )

            valid_transition_ratio = float(
                validation.get(
                    "valid_transition_ratio",
                    0.0,
                )
            )

            compact_range_score = float(
                validation.get(
                    "compact_range_score",
                    0.0,
                )
            )

            # -------------------------------------------------------
            # Cross-record evidence
            # -------------------------------------------------------

            record_count = int(
                validation.get(
                    "record_count",
                    0,
                )
            )

            unique_count = int(
                validation.get(
                    "unique_value_count",
                    0,
                )
            )

            change_ratio = float(
                validation.get(
                    "change_ratio",
                    0.0,
                )
            )

            # -------------------------------------------------------
            # Strong evidence flags
            # -------------------------------------------------------

            evidence = []

            if validation_score >= 85.0:
                evidence.append(
                    "high_validation_score"
                )

            if consistency_score >= 80.0:
                evidence.append(
                    "high_consistency_score"
                )

            if interpretation_score >= 80.0:
                evidence.append(
                    "high_interpretation_score"
                )

            if midi_ratio >= 0.90:
                evidence.append(
                    "strong_midi_value_evidence"
                )

            if valid_transition_ratio >= 0.90:
                evidence.append(
                    "strong_transition_evidence"
                )

            if compact_range_score >= 0.90:
                evidence.append(
                    "compact_midi_range"
                )

            if unique_count > 1:
                evidence.append(
                    "value_changes_across_records"
                )

            if len(
                structure_evidence
            ) > 0:
                evidence.append(
                    "mapping_appears_in_reconstructed_structure"
                )

            # -------------------------------------------------------
            # Conflict detection
            # -------------------------------------------------------

            conflicts = []

            invalid_values = validation.get(
                "invalid_values",
                [],
            )

            if invalid_values:
                conflicts.append(
                    "invalid_midi_values_present"
                )

            if midi_ratio < 0.75:
                conflicts.append(
                    "insufficient_midi_value_ratio"
                )

            if (
                validation_score < 55.0
            ):
                conflicts.append(
                    "low_validation_score"
                )

            if (
                consistency_score < 50.0
            ):
                conflicts.append(
                    "low_consistency_score"
                )

            if (
                interpretation_score > 0.0
                and interpretation_score < 50.0
            ):
                conflicts.append(
                    "low_interpretation_score"
                )

            if (
                record_count < 2
            ):
                conflicts.append(
                    "insufficient_record_count"
                )

            # -------------------------------------------------------
            # Change behavior verification
            # -------------------------------------------------------

            behavior_verification = (
                "unknown"
            )

            if (
                unique_count > 1
                and 0.0 < change_ratio < 1.0
            ):

                behavior_verification = (
                    "variable_across_kits"
                )

            elif unique_count == 1:

                behavior_verification = (
                    "constant_across_kits"
                )

            elif change_ratio >= 0.95:

                behavior_verification = (
                    "changes_almost_every_record"
                )

            # -------------------------------------------------------
            # Final confidence score
            # -------------------------------------------------------

            final_confidence_score = (
                validation_score * 0.35
                + consistency_score * 0.20
                + interpretation_score * 0.20
                + midi_ratio * 100.0 * 0.10
                + valid_transition_ratio * 100.0 * 0.10
                + compact_range_score * 100.0 * 0.05
            )

            # Penalties
            # -------------------------------------------------------

            if invalid_values:
                final_confidence_score -= 15.0

            if unique_count == 1:
                final_confidence_score -= 10.0

            if record_count < 3:
                final_confidence_score -= 10.0

            if len(
                conflicts
            ) >= 3:
                final_confidence_score -= 10.0

            final_confidence_score = max(
                min(
                    final_confidence_score,
                    100.0,
                ),
                0.0,
            )

            # -------------------------------------------------------
            # Final classification
            # -------------------------------------------------------

            if (
                final_confidence_score >= 90.0
                and not invalid_values
                and midi_ratio >= 0.90
                and record_count >= 3
            ):

                classification = (
                    "confirmed_midi_mapping"
                )

                confidence = (
                    "very_high"
                )

            elif (
                final_confidence_score >= 80.0
                and midi_ratio >= 0.80
            ):

                classification = (
                    "high_confidence_midi_mapping"
                )

                confidence = (
                    "high"
                )

            elif (
                final_confidence_score >= 65.0
                and midi_ratio >= 0.70
            ):

                classification = (
                    "probable_midi_mapping"
                )

                confidence = (
                    "medium"
                )

            elif (
                final_confidence_score >= 50.0
            ):

                classification = (
                    "possible_midi_mapping"
                )

                confidence = (
                    "low"
                )

            else:

                classification = (
                    "rejected_mapping_candidate"
                )

                confidence = (
                    "very_low"
                )

            # -------------------------------------------------------
            # Human-readable explanation
            # -------------------------------------------------------

            if (
                classification
                == "confirmed_midi_mapping"
            ):

                explanation = (
                    "Strong cross-analysis evidence "
                    "indicates that this byte position "
                    "is very likely a MIDI mapping value."
                )

            elif (
                classification
                == "high_confidence_midi_mapping"
            ):

                explanation = (
                    "Multiple independent analyses "
                    "support this position as a MIDI "
                    "mapping candidate."
                )

            elif (
                classification
                == "probable_midi_mapping"
            ):

                explanation = (
                    "The position shows substantial "
                    "MIDI-like behavior but requires "
                    "additional verification."
                )

            elif (
                classification
                == "possible_midi_mapping"
            ):

                explanation = (
                    "Some MIDI evidence exists, but "
                    "the current binary evidence is "
                    "not sufficient for confirmation."
                )

            else:

                explanation = (
                    "Current evidence is insufficient "
                    "to identify this position as a "
                    "reliable MIDI mapping."
                )

            # -------------------------------------------------------
            # Final result
            # -------------------------------------------------------

            final_report.append(
                {
                    "relative_offset": offset,
                    "hex_offset": (
                        f"0x{offset:02X}"
                    ),
                    "record_count": record_count,
                    "unique_value_count": unique_count,
                    "unique_values": validation.get(
                        "unique_values",
                        [],
                    ),
                    "hex_values": validation.get(
                        "hex_values",
                        [],
                    ),
                    "midi_note_names": validation.get(
                        "midi_note_names",
                        [],
                    ),
                    "minimum_value": validation.get(
                        "minimum_value"
                    ),
                    "maximum_value": validation.get(
                        "maximum_value"
                    ),
                    "value_range": validation.get(
                        "value_range"
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
                    "compact_range_score": round(
                        compact_range_score,
                        4,
                    ),
                    "validation_score": round(
                        validation_score,
                        2,
                    ),
                    "consistency_score": round(
                        consistency_score,
                        2,
                    ),
                    "interpretation_score": round(
                        interpretation_score,
                        2,
                    ),
                    "final_confidence_score": round(
                        final_confidence_score,
                        2,
                    ),
                    "classification": classification,
                    "confidence": confidence,
                    "behavior_verification": (
                        behavior_verification
                    ),
                    "evidence": evidence,
                    "conflicts": conflicts,
                    "explanation": explanation,
                    "structure_evidence_count": len(
                        structure_evidence
                    ),
                }
            )

        # -----------------------------------------------------------
        # Sort by final confidence
        # -----------------------------------------------------------

        final_report.sort(
            key=lambda item: (
                item[
                    "final_confidence_score"
                ],
                item[
                    "validation_score"
                ],
                item[
                    "consistency_score"
                ],
            ),
            reverse=True,
        )

        # -----------------------------------------------------------
        # Add final ranks
        # -----------------------------------------------------------

        for rank, item in enumerate(
            final_report,
            start=1,
        ):
            item["rank"] = rank

        return final_report

    def find_confirmed_midi_mappings(
        self,
    ) -> list[dict]:
        """
        Returns only confirmed MIDI mappings.
        """

        report = (
            self.verify_mapping_confidence()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            == "confirmed_midi_mapping"
        ]

    def find_high_confidence_midi_mappings(
        self,
    ) -> list[dict]:
        """
        Returns confirmed and high-confidence
        MIDI mappings.
        """

        report = (
            self.verify_mapping_confidence()
        )

        return [
            item
            for item in report
            if item[
                "classification"
            ]
            in (
                "confirmed_midi_mapping",
                "high_confidence_midi_mapping",
            )
        ]

    def build_final_mapping_verification_report(
        self,
    ) -> dict:
        """
        Complete #39 final verification report.
        """

        report = (
            self.verify_mapping_confidence()
        )

        confirmed = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "confirmed_midi_mapping"
        ]

        high_confidence = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "high_confidence_midi_mapping"
        ]

        probable = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "probable_midi_mapping"
        ]

        possible = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "possible_midi_mapping"
        ]

        rejected = [
            item
            for item in report
            if item[
                "classification"
            ]
            == "rejected_mapping_candidate"
        ]

        # -----------------------------------------------------------
        # Determine overall status
        # -----------------------------------------------------------

        if confirmed:

            overall_status = (
                "MIDI_MAPPING_CONFIRMED"
            )

        elif high_confidence:

            overall_status = (
                "MIDI_MAPPING_HIGH_CONFIDENCE"
            )

        elif probable:

            overall_status = (
                "MIDI_MAPPING_PROBABLE"
            )

        elif possible:

            overall_status = (
                "MIDI_MAPPING_POSSIBLE"
            )

        else:

            overall_status = (
                "NO_RELIABLE_MIDI_MAPPING_FOUND"
            )

        # -----------------------------------------------------------
        # Best candidate
        # -----------------------------------------------------------

        best_candidate = (
            report[0]
            if report
            else None
        )

        return {
            "analysis_version": (
                "#39"
            ),
            "overall_status": (
                overall_status
            ),
            "candidate_count": (
                len(report)
            ),
            "confirmed_count": (
                len(confirmed)
            ),
            "high_confidence_count": (
                len(high_confidence)
            ),
            "probable_count": (
                len(probable)
            ),
            "possible_count": (
                len(possible)
            ),
            "rejected_count": (
                len(rejected)
            ),
            "best_candidate": (
                best_candidate
            ),
            "confirmed_mappings": (
                confirmed
            ),
            "high_confidence_mappings": (
                high_confidence
            ),
            "probable_mappings": (
                probable
            ),
            "possible_mappings": (
                possible
            ),
            "rejected_candidates": (
                rejected
            ),
            "all_candidates": (
                report
            ),
            "analysis_chain": [
                "#32 Mapping Consistency",
                "#33 Mapping Relationships",
                "#34 Mapping Field Detection",
                "#35 Mapping Field Interpretation",
                "#36 MIDI Mapping Validation",
                "#37 Drum Kit Structure Reconstruction",
                "#38 Human-Readable Drum Kit Report",
                "#39 Final Mapping Confidence & Verification",
            ],
            "safe_for_editing": False,
            "write_back_enabled": False,
            "warning": (
                "This report is analytical only. "
                "No PCG/SET data is modified. "
                "A confirmed mapping candidate does "
                "not yet mean that the complete Drum Kit "
                "binary structure has been decoded."
            ),
        }
```
