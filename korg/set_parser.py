```python
    # ===============================================================
    # #40 FINAL DRUM KIT MODEL
    # ===============================================================

    def build_final_drum_kit_model(
        self,
    ) -> list[dict]:
        """
        #40

        Gradi konačni interni model Drum Kit strukture.

        Koristi:
        #32 - Mapping Consistency
        #33 - Mapping Relationships
        #34 - Mapping Field Detection
        #35 - Mapping Field Interpretation
        #36 - MIDI Mapping Validation
        #37 - Drum Kit Structure Reconstruction
        #38 - Human-Readable Report
        #39 - Final Mapping Verification

        Cilj:
        - napraviti stabilan model svakog Drum Kita
        - izdvojiti potvrđene i vjerovatne MIDI mapping pozicije
        - sačuvati raw bytes
        - sačuvati offsets
        - povezati fieldove
        - pripremiti podatke za budući editor
        - NE mijenjati originalni PCG/SET fajl
        """

        records = (
            self.find_drum_kit_name_records()
        )

        if not records:
            return []

        final_verification = (
            self.build_final_mapping_verification_report()
        )

        structure_report = (
            self.reconstruct_drum_kit_structure()
        )

        human_report = (
            self.build_human_readable_drum_kit_report()
        )

        verification_candidates = (
            final_verification.get(
                "all_candidates",
                [],
            )
        )

        structure_by_index = {
            item.get(
                "record_index"
            ): item
            for item in structure_report
        }

        # -----------------------------------------------------------
        # Global mapping confidence by offset
        # -----------------------------------------------------------

        confidence_by_offset = {}

        for candidate in verification_candidates:

            offset = candidate.get(
                "relative_offset"
            )

            if offset is None:
                continue

            confidence_by_offset[
                offset
            ] = candidate

        # -----------------------------------------------------------
        # Build model for every Drum Kit
        # -----------------------------------------------------------

        final_model = []

        for kit_index, record in enumerate(
            records,
            start=1,
        ):

            try:
                raw_bytes = bytes(
                    record
                )
            except (
                TypeError,
                ValueError,
            ):
                raw_bytes = bytes(
                    record[
                        :self.DRUM_KIT_RECORD_SIZE
                    ]
                )

            raw_bytes = raw_bytes[
                :self.DRUM_KIT_RECORD_SIZE
            ]

            structure = (
                structure_by_index.get(
                    kit_index,
                    {},
                )
            )

            # -------------------------------------------------------
            # Name extraction
            # -------------------------------------------------------

            kit_name = None

            if isinstance(
                record,
                dict,
            ):

                kit_name = (
                    record.get(
                        "name"
                    )
                    or record.get(
                        "drum_kit_name"
                    )
                    or record.get(
                        "kit_name"
                    )
                )

            # -------------------------------------------------------
            # Build parameters
            # -------------------------------------------------------

            parameters = []

            for offset, value in enumerate(
                raw_bytes
            ):

                candidate = (
                    confidence_by_offset.get(
                        offset
                    )
                )

                parameter_type = (
                    "unknown"
                )

                confidence = (
                    "none"
                )

                confidence_score = 0.0

                classification = None

                if candidate:

                    classification = candidate.get(
                        "classification"
                    )

                    confidence = candidate.get(
                        "confidence",
                        "low",
                    )

                    confidence_score = candidate.get(
                        "final_confidence_score",
                        0.0,
                    )

                    if classification == (
                        "confirmed_midi_mapping"
                    ):

                        parameter_type = (
                            "midi_mapping"
                        )

                    elif classification == (
                        "high_confidence_midi_mapping"
                    ):

                        parameter_type = (
                            "midi_mapping"
                        )

                    elif classification == (
                        "probable_midi_mapping"
                    ):

                        parameter_type = (
                            "probable_midi_mapping"
                        )

                    elif classification == (
                        "possible_midi_mapping"
                    ):

                        parameter_type = (
                            "possible_mapping"
                        )

                # ---------------------------------------------------
                # MIDI note
                # ---------------------------------------------------

                midi_note = None
                midi_note_name = None

                if (
                    parameter_type
                    in (
                        "midi_mapping",
                        "probable_midi_mapping",
                        "possible_mapping",
                    )
                    and 0 <= value <= 127
                ):

                    midi_note = value

                    try:
                        midi_note_name = (
                            midi_to_note(
                                value
                            )
                        )
                    except Exception:
                        midi_note_name = None

                parameters.append(
                    {
                        "offset": offset,
                        "hex_offset": (
                            f"0x{offset:02X}"
                        ),
                        "value": value,
                        "hex": (
                            f"{value:02X}"
                        ),
                        "parameter_type": (
                            parameter_type
                        ),
                        "classification": (
                            classification
                        ),
                        "confidence": (
                            confidence
                        ),
                        "confidence_score": round(
                            confidence_score,
                            2,
                        ),
                        "midi_note": midi_note,
                        "midi_note_name": (
                            midi_note_name
                        ),
                    }
                )

            # -------------------------------------------------------
            # Mapping positions
            # -------------------------------------------------------

            midi_mapping = []

            probable_mapping = []

            possible_mapping = []

            for parameter in parameters:

                parameter_type = parameter.get(
                    "parameter_type"
                )

                if parameter_type == (
                    "midi_mapping"
                ):

                    midi_mapping.append(
                        parameter
                    )

                elif parameter_type == (
                    "probable_midi_mapping"
                ):

                    probable_mapping.append(
                        parameter
                    )

                elif parameter_type == (
                    "possible_mapping"
                ):

                    possible_mapping.append(
                        parameter
                    )

            # -------------------------------------------------------
            # Field model
            # -------------------------------------------------------

            fields = []

            for field in structure.get(
                "mapping_fields",
                [],
            ):

                field_id = field.get(
                    "field_id"
                )

                offsets = field.get(
                    "offsets",
                    [],
                )

                field_parameters = [
                    parameter
                    for parameter
                    in parameters
                    if parameter[
                        "offset"
                    ]
                    in offsets
                ]

                fields.append(
                    {
                        "field_id": field_id,
                        "offsets": offsets,
                        "start_offset": field.get(
                            "start_offset"
                        ),
                        "end_offset": field.get(
                            "end_offset"
                        ),
                        "field_size": field.get(
                            "field_size"
                        ),
                        "classification": field.get(
                            "classification"
                        ),
                        "score": field.get(
                            "group_score",
                            0.0,
                        ),
                        "parameters": field_parameters,
                    }
                )

            # -------------------------------------------------------
            # Raw representation
            # -------------------------------------------------------

            raw_hex = " ".join(
                f"{value:02X}"
                for value
                in raw_bytes
            )

            # -------------------------------------------------------
            # Reconstruction score
            # -------------------------------------------------------

            reconstruction_score = structure.get(
                "reconstruction_score",
                0.0,
            )

            reconstruction_confidence = structure.get(
                "reconstruction_confidence",
                "low",
            )

            # -------------------------------------------------------
            # Final model object
            # -------------------------------------------------------

            final_model.append(
                {
                    "model_version": (
                        "#40"
                    ),
                    "kit_index": (
                        kit_index
                    ),
                    "kit_name": (
                        kit_name
                    ),
                    "record_size": (
                        len(raw_bytes)
                    ),
                    "raw_bytes": list(
                        raw_bytes
                    ),
                    "raw_hex": raw_hex,

                    "reconstruction": {
                        "score": (
                            reconstruction_score
                        ),
                        "confidence": (
                            reconstruction_confidence
                        ),
                    },

                    "mapping": {
                        "confirmed": (
                            midi_mapping
                        ),
                        "probable": (
                            probable_mapping
                        ),
                        "possible": (
                            possible_mapping
                        ),
                    },

                    "fields": fields,

                    "parameters": parameters,

                    "statistics": {
                        "confirmed_midi_count": (
                            len(
                                midi_mapping
                            )
                        ),
                        "probable_midi_count": (
                            len(
                                probable_mapping
                            )
                        ),
                        "possible_mapping_count": (
                            len(
                                possible_mapping
                            )
                        ),
                        "field_count": (
                            len(
                                fields
                            )
                        ),
                        "unknown_parameter_count": (
                            sum(
                                1
                                for parameter
                                in parameters
                                if parameter[
                                    "parameter_type"
                                ]
                                == "unknown"
                            )
                        ),
                    },

                    "editing": {
                        "editable": False,
                        "write_back": False,
                        "source_verified": True,
                    },

                    "warning": (
                        "This model is analytical only. "
                        "It does not modify the source "
                        "PCG/SET file."
                    ),
                }
            )

        return final_model

    def get_final_drum_kit_model(
        self,
    ) -> dict:
        """
        Returns the complete #40 model.
        """

        model = (
            self.build_final_drum_kit_model()
        )

        return {
            "model_version": (
                "#40"
            ),
            "drum_kit_count": (
                len(model)
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "kits": model,
            "mapping_status": (
                self.build_final_mapping_verification_report().get(
                    "overall_status"
                )
            ),
            "editable": False,
            "write_back": False,
            "safe_for_source_file": True,
        }

    def get_drum_kit_by_index(
        self,
        kit_index: int,
    ) -> dict | None:
        """
        Returns one Drum Kit from the #40 model.
        """

        model = (
            self.build_final_drum_kit_model()
        )

        for kit in model:

            if kit.get(
                "kit_index"
            ) == kit_index:

                return kit

        return None

    def get_confirmed_midi_mapping_model(
        self,
    ) -> list[dict]:
        """
        Returns only confirmed MIDI mapping
        parameters from the final model.
        """

        model = (
            self.build_final_drum_kit_model()
        )

        result = []

        for kit in model:

            confirmed = kit.get(
                "mapping",
                {},
            ).get(
                "confirmed",
                [],
            )

            if not confirmed:
                continue

            result.append(
                {
                    "kit_index": kit.get(
                        "kit_index"
                    ),
                    "kit_name": kit.get(
                        "kit_name"
                    ),
                    "confirmed_mappings": (
                        confirmed
                    ),
                }
            )

        return result

    def build_complete_drum_kit_model_report(
        self,
    ) -> dict:
        """
        Complete #40 report.

        Ovo je glavni ulaz za budući editor.
        """

        model = (
            self.build_final_drum_kit_model()
        )

        confirmed_count = 0
        probable_count = 0
        possible_count = 0

        for kit in model:

            mapping = kit.get(
                "mapping",
                {},
            )

            confirmed_count += len(
                mapping.get(
                    "confirmed",
                    [],
                )
            )

            probable_count += len(
                mapping.get(
                    "probable",
                    [],
                )
            )

            possible_count += len(
                mapping.get(
                    "possible",
                    [],
                )
            )

        return {
            "model_version": (
                "#40"
            ),
            "title": (
                "Korg Drum Kit Final Internal Model"
            ),
            "description": (
                "Final analytical model of the "
                "reconstructed Drum Kit structure."
            ),
            "drum_kit_count": (
                len(model)
            ),
            "record_size": (
                self.DRUM_KIT_RECORD_SIZE
            ),
            "mapping_summary": {
                "confirmed": (
                    confirmed_count
                ),
                "probable": (
                    probable_count
                ),
                "possible": (
                    possible_count
                ),
            },
            "kits": model,
            "pipeline": [
                "#32 Mapping Consistency",
                "#33 Mapping Relationships",
                "#34 Mapping Field Detection",
                "#35 Mapping Field Interpretation",
                "#36 MIDI Mapping Validation",
                "#37 Drum Kit Structure Reconstruction",
                "#38 Human-Readable Drum Kit Report",
                "#39 Final Mapping Confidence & Verification",
                "#40 Final Drum Kit Internal Model",
            ],
            "editor_ready": True,
            "write_back_ready": False,
            "source_file_modified": False,
            "warning": (
                "Editor-ready means the analytical model "
                "is available for UI development. "
                "Binary write-back is intentionally disabled."
            ),
        }
```
