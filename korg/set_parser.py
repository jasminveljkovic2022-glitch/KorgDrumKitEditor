```python
    # ===============================================================
    # #41 SAFE DRUM KIT EDITING LAYER
    # ===============================================================

    def create_editable_drum_kit_model(
        self,
    ) -> dict:
        """
        #41

        Kreira editable kopiju #40 Drum Kit modela.

        VAŽNO:
        - Originalni PCG/SET se NE mijenja.
        - Promjene se rade samo nad kopijom u memoriji.
        - Write-back u originalni fajl još nije omogućen.
        """

        import copy

        source_model = (
            self.build_complete_drum_kit_model_report()
        )

        editable_model = copy.deepcopy(
            source_model
        )

        editable_model[
            "model_version"
        ] = "#41"

        editable_model[
            "editable"
        ] = True

        editable_model[
            "write_back"
        ] = False

        editable_model[
            "source_file_modified"
        ] = False

        editable_model[
            "changes"
        ] = []

        editable_model[
            "change_count"
        ] = 0

        editable_model[
            "warning"
        ] = (
            "Editing is performed only on an "
            "in-memory copy. The original "
            "PCG/SET file is never modified."
        )

        return editable_model

    def set_drum_kit_byte(
        self,
        kit_index: int,
        relative_offset: int,
        value: int,
    ) -> dict:
        """
        #41

        Mijenja jedan byte u editable Drum Kit modelu.

        Ne mijenja originalni PCG/SET fajl.

        Args:
            kit_index:
                1-based Drum Kit index.

            relative_offset:
                Byte offset unutar Drum Kit recorda.

            value:
                Nova vrijednost 0-255.
        """

        if not isinstance(
            kit_index,
            int,
        ):
            raise TypeError(
                "kit_index must be an integer."
            )

        if not isinstance(
            relative_offset,
            int,
        ):
            raise TypeError(
                "relative_offset must be an integer."
            )

        if not isinstance(
            value,
            int,
        ):
            raise TypeError(
                "value must be an integer."
            )

        if value < 0 or value > 255:
            raise ValueError(
                "Byte value must be between 0 and 255."
            )

        editable_model = (
            self.create_editable_drum_kit_model()
        )

        kits = editable_model.get(
            "kits",
            [],
        )

        target_kit = None

        for kit in kits:

            if kit.get(
                "kit_index"
            ) == kit_index:

                target_kit = kit
                break

        if target_kit is None:

            raise IndexError(
                f"Drum Kit {kit_index} was not found."
            )

        parameters = target_kit.get(
            "parameters",
            [],
        )

        target_parameter = None

        for parameter in parameters:

            if parameter.get(
                "offset"
            ) == relative_offset:

                target_parameter = parameter
                break

        if target_parameter is None:

            raise IndexError(
                "Relative offset "
                f"{relative_offset} was not found "
                f"in Drum Kit {kit_index}."
            )

        old_value = target_parameter.get(
            "value"
        )

        # -----------------------------------------------------------
        # Update parameter
        # -----------------------------------------------------------

        target_parameter[
            "value"
        ] = value

        target_parameter[
            "hex"
        ] = f"{value:02X}"

        # -----------------------------------------------------------
        # Update MIDI information
        # -----------------------------------------------------------

        parameter_type = (
            target_parameter.get(
                "parameter_type"
            )
        )

        if (
            parameter_type
            in (
                "midi_mapping",
                "probable_midi_mapping",
                "possible_mapping",
            )
            and 0 <= value <= 127
        ):

            target_parameter[
                "midi_note"
            ] = value

            try:

                target_parameter[
                    "midi_note_name"
                ] = midi_to_note(
                    value
                )

            except Exception:

                target_parameter[
                    "midi_note_name"
                ] = None

        else:

            target_parameter[
                "midi_note"
            ] = None

            target_parameter[
                "midi_note_name"
            ] = None

        # -----------------------------------------------------------
        # Update raw bytes
        # -----------------------------------------------------------

        raw_bytes = target_kit.get(
            "raw_bytes",
            [],
        )

        if (
            relative_offset < 0
            or relative_offset >= len(
                raw_bytes
            )
        ):

            raise IndexError(
                "Relative offset is outside "
                "the raw byte array."
            )

        raw_bytes[
            relative_offset
        ] = value

        target_kit[
            "raw_bytes"
        ] = raw_bytes

        target_kit[
            "raw_hex"
        ] = " ".join(
            f"{byte:02X}"
            for byte in raw_bytes
        )

        # -----------------------------------------------------------
        # Register change
        # -----------------------------------------------------------

        change = {
            "kit_index": kit_index,
            "relative_offset": relative_offset,
            "hex_offset": (
                f"0x{relative_offset:02X}"
            ),
            "old_value": old_value,
            "old_hex": (
                f"{old_value:02X}"
                if isinstance(
                    old_value,
                    int,
                )
                else None
            ),
            "new_value": value,
            "new_hex": f"{value:02X}",
        }

        editable_model[
            "changes"
        ].append(
            change
        )

        editable_model[
            "change_count"
        ] = len(
            editable_model[
                "changes"
            ]
        )

        return {
            "success": True,
            "kit_index": kit_index,
            "relative_offset": relative_offset,
            "old_value": old_value,
            "new_value": value,
            "change": change,
            "model": editable_model,
            "source_file_modified": False,
            "write_back": False,
        }

    def set_drum_kit_midi_note(
        self,
        kit_index: int,
        relative_offset: int,
        midi_note: int,
    ) -> dict:
        """
        #41

        Sigurniji helper za promjenu MIDI note.

        MIDI vrijednost mora biti 0-127.
        """

        if not isinstance(
            midi_note,
            int,
        ):
            raise TypeError(
                "midi_note must be an integer."
            )

        if midi_note < 0 or midi_note > 127:
            raise ValueError(
                "MIDI note must be between 0 and 127."
            )

        result = self.set_drum_kit_byte(
            kit_index=kit_index,
            relative_offset=relative_offset,
            value=midi_note,
        )

        parameter = None

        for item in result[
            "model"
        ].get(
            "kits",
            [],
        ):

            if item.get(
                "kit_index"
            ) != kit_index:
                continue

            for candidate in item.get(
                "parameters",
                [],
            ):

                if candidate.get(
                    "offset"
                ) == relative_offset:

                    parameter = candidate
                    break

        result[
            "midi_note"
        ] = midi_note

        result[
            "midi_note_name"
        ] = (
            parameter.get(
                "midi_note_name"
            )
            if parameter
            else None
        )

        return result

    def validate_editable_drum_kit_model(
        self,
        model: dict,
    ) -> dict:
        """
        #41

        Provjerava integritet editable modela.

        Ne radi nikakav write-back.
        """

        errors = []
        warnings = []

        if not isinstance(
            model,
            dict,
        ):

            return {
                "valid": False,
                "errors": [
                    "Model must be a dictionary."
                ],
                "warnings": [],
            }

        kits = model.get(
            "kits",
            [],
        )

        expected_record_size = (
            self.DRUM_KIT_RECORD_SIZE
        )

        for kit in kits:

            kit_index = kit.get(
                "kit_index"
            )

            raw_bytes = kit.get(
                "raw_bytes",
                [],
            )

            if len(
                raw_bytes
            ) != expected_record_size:

                errors.append(
                    {
                        "kit_index": kit_index,
                        "error": (
                            "Invalid record size."
                        ),
                        "actual_size": len(
                            raw_bytes
                        ),
                        "expected_size": (
                            expected_record_size
                        ),
                    }
                )

            parameters = kit.get(
                "parameters",
                [],
            )

            for parameter in parameters:

                offset = parameter.get(
                    "offset"
                )

                value = parameter.get(
                    "value"
                )

                if not isinstance(
                    offset,
                    int,
                ):

                    errors.append(
                        {
                            "kit_index": kit_index,
                            "error": (
                                "Invalid parameter offset."
                            ),
                            "offset": offset,
                        }
                    )

                    continue

                if (
                    offset < 0
                    or offset >= len(
                        raw_bytes
                    )
                ):

                    errors.append(
                        {
                            "kit_index": kit_index,
                            "error": (
                                "Parameter offset "
                                "outside record."
                            ),
                            "offset": offset,
                        }
                    )

                if (
                    not isinstance(
                        value,
                        int,
                    )
                    or value < 0
                    or value > 255
                ):

                    errors.append(
                        {
                            "kit_index": kit_index,
                            "offset": offset,
                            "error": (
                                "Invalid byte value."
                            ),
                            "value": value,
                        }
                    )

        if model.get(
            "write_back"
        ):

            warnings.append(
                "Write-back flag is enabled."
            )

        if model.get(
            "source_file_modified"
        ):

            warnings.append(
                "Model reports source file modification."
            )

        return {
            "valid": (
                len(errors) == 0
            ),
            "errors": errors,
            "warnings": warnings,
            "kit_count": len(
                kits
            ),
            "change_count": model.get(
                "change_count",
                0,
            ),
            "write_back": model.get(
                "write_back",
                False,
            ),
            "source_file_modified": model.get(
                "source_file_modified",
                False,
            ),
        }

    def preview_drum_kit_changes(
        self,
        model: dict,
    ) -> list[dict]:
        """
        #41

        Vraća samo promjene koje bi bile
        napravljene na editable modelu.

        Originalni fajl se ne dira.
        """

        if not isinstance(
            model,
            dict,
        ):
            return []

        return list(
            model.get(
                "changes",
                [],
            )
        )

    def reset_drum_kit_edits(
        self,
    ) -> dict:
        """
        #41

        Odbacuje sve edit promjene i ponovo
        gradi čisti editable model iz originalne
        analize.

        Originalni PCG/SET ostaje nepromijenjen.
        """

        model = (
            self.create_editable_drum_kit_model()
        )

        validation = (
            self.validate_editable_drum_kit_model(
                model
            )
        )

        return {
            "success": validation[
                "valid"
            ],
            "model": model,
            "validation": validation,
            "changes_removed": True,
            "source_file_modified": False,
            "write_back": False,
        }

    def build_safe_editor_data(
        self,
    ) -> dict:
        """
        #41

        Glavni ulaz za budući Drum Kit Editor.

        Editor dobiva:
        - Drum Kit modele
        - MIDI mapping
        - byte parametre
        - editable kopiju
        - validation status
        - change tracking

        Write-back još nije omogućen.
        """

        model = (
            self.create_editable_drum_kit_model()
        )

        validation = (
            self.validate_editable_drum_kit_model(
                model
            )
        )

        return {
            "editor_version": "#41",
            "editor_ready": validation[
                "valid"
            ],
            "editable": True,
            "write_back": False,
            "source_file_modified": False,
            "validation": validation,
            "change_count": (
                model.get(
                    "change_count",
                    0,
                )
            ),
            "model": model,
        }
```
