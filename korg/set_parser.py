
    # ===============================================================
    # #45 MIDI MAPPING EDITOR INTERFACE
    # ===============================================================

    def build_midi_mapping_editor(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        #45

        Priprema kompletan MIDI Mapping prikaz
        za GUI editor.

        Koristi postojeći #43 mapping model.

        NE mijenja originalni SET/PCG fajl.
        """

        if not isinstance(session, dict):
            raise TypeError(
                "session must be a dictionary."
            )

        kit = self._find_session_kit(
            session,
            kit_index,
        )

        mappings = self.build_editor_midi_mapping_list(
            session,
            kit_index,
        )

        result = []

        for mapping in mappings:

            midi_note = mapping.get(
                "midi_note"
            )

            try:
                if midi_note is not None:
                    midi_note = int(
                        midi_note
                    )
            except (
                TypeError,
                ValueError,
            ):
                midi_note = None

            midi_valid = (
                midi_note is not None
                and 0 <= midi_note <= 127
            )

            if midi_valid:
                try:
                    note_name = midi_to_note(
                        midi_note
                    )
                except Exception:
                    note_name = (
                        mapping.get(
                            "midi_note_name"
                        )
                        or ""
                    )
            else:
                note_name = (
                    mapping.get(
                        "midi_note_name"
                    )
                    or ""
                )

            confidence_score = mapping.get(
                "confidence_score",
                0.0,
            )

            try:
                confidence_score = float(
                    confidence_score
                )
            except (
                TypeError,
                ValueError,
            ):
                confidence_score = 0.0

            result.append(
                {
                    "kit_index": kit_index,
                    "offset": mapping.get(
                        "offset"
                    ),
                    "hex_offset": mapping.get(
                        "hex_offset"
                    ),
                    "value": mapping.get(
                        "value"
                    ),
                    "hex": mapping.get(
                        "hex"
                    ),
                    "midi_note": midi_note,
                    "midi_note_name": note_name,
                    "midi_valid": midi_valid,
                    "parameter_type": mapping.get(
                        "parameter_type"
                    ),
                    "classification": mapping.get(
                        "classification"
                    ),
                    "confidence": mapping.get(
                        "confidence"
                    ),
                    "confidence_score": round(
                        confidence_score,
                        2,
                    ),
                    "editable": True,
                    "source_file_modified": False,
                }
            )

        result.sort(
            key=lambda item: (
                item.get("midi_note")
                if item.get("midi_note") is not None
                else 999,
                item.get("offset")
                if item.get("offset") is not None
                else 999999,
            )
        )

        confirmed_count = sum(
            1
            for item in result
            if (
                item.get("classification")
                == "confirmed"
                or item.get("parameter_type")
                == "midi_mapping"
            )
        )

        probable_count = sum(
            1
            for item in result
            if (
                item.get("classification")
                == "probable"
                or item.get("parameter_type")
                == "probable_midi_mapping"
            )
        )

        possible_count = sum(
            1
            for item in result
            if (
                item.get("classification")
                == "possible"
                or item.get("parameter_type")
                == "possible_mapping"
            )
        )

        valid_midi_count = sum(
            1
            for item in result
            if item.get(
                "midi_valid",
                False,
            )
        )

        return {
            "success": True,
            "kit_index": kit.get(
                "kit_index",
                kit_index,
            ),
            "kit_name": kit.get(
                "kit_name"
            ),
            "record_size": kit.get(
                "record_size"
            ),
            "mapping_count": len(
                result
            ),
            "valid_midi_count": (
                valid_midi_count
            ),
            "confirmed_count": (
                confirmed_count
            ),
            "probable_count": (
                probable_count
            ),
            "possible_count": (
                possible_count
            ),
            "mappings": result,
            "dirty": session.get(
                "dirty",
                False,
            ),
            "undo_available": session.get(
                "undo_available",
                False,
            ),
            "redo_available": session.get(
                "redo_available",
                False,
            ),
            "write_back": False,
            "source_file_modified": False,
        }


    def find_midi_mapping_by_note(
        self,
        session: dict,
        kit_index: int,
        midi_note: int,
    ) -> list[dict]:
        """
        #45

        Pronalazi sve mapping zapise
        za određenu MIDI notu.
        """

        try:
            midi_note = int(
                midi_note
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "midi_note must be an integer."
            )

        if not 0 <= midi_note <= 127:
            raise ValueError(
                "midi_note must be between 0 and 127."
            )

        data = self.build_midi_mapping_editor(
            session,
            kit_index,
        )

        return [
            item
            for item in data.get(
                "mappings",
                [],
            )
            if item.get(
                "midi_note"
            ) == midi_note
        ]


    def find_midi_mapping_by_offset(
        self,
        session: dict,
        kit_index: int,
        relative_offset: int,
    ) -> dict | None:
        """
        #45

        Pronalazi MIDI mapping prema
        relativnom offsetu.
        """

        try:
            relative_offset = int(
                relative_offset
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "relative_offset must be an integer."
            )

        data = self.build_midi_mapping_editor(
            session,
            kit_index,
        )

        for item in data.get(
            "mappings",
            [],
        ):
            if item.get(
                "offset"
            ) == relative_offset:
                return item

        return None


    def get_midi_mapping_statistics(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        #45

        Statistika MIDI mapping podataka.
        """

        data = self.build_midi_mapping_editor(
            session,
            kit_index,
        )

        mappings = data.get(
            "mappings",
            [],
        )

        midi_values = []

        for item in mappings:

            value = item.get(
                "midi_note"
            )

            if (
                isinstance(value, int)
                and 0 <= value <= 127
            ):
                midi_values.append(
                    value
                )

        unique_midi_values = sorted(
            set(
                midi_values
            )
        )

        duplicate_midi_values = [
            value
            for value in unique_midi_values
            if midi_values.count(
                value
            ) > 1
        ]

        confidence_scores = []

        for item in mappings:

            score = item.get(
                "confidence_score",
                0.0,
            )

            try:
                score = float(
                    score
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            confidence_scores.append(
                score
            )

        average_confidence = (
            sum(
                confidence_scores
            )
            / len(
                confidence_scores
            )
            if confidence_scores
            else 0.0
        )

        return {
            "kit_index": kit_index,
            "mapping_count": len(
                mappings
            ),
            "valid_midi_count": len(
                midi_values
            ),
            "unique_midi_count": len(
                unique_midi_values
            ),
            "duplicate_midi_count": len(
                duplicate_midi_values
            ),
            "duplicate_midi_values": (
                duplicate_midi_values
            ),
            "minimum_midi": (
                min(
                    midi_values
                )
                if midi_values
                else None
            ),
            "maximum_midi": (
                max(
                    midi_values
                )
                if midi_values
                else None
            ),
            "average_confidence": round(
                average_confidence,
                2,
            ),
            "source_file_modified": False,
        }


    def validate_midi_mapping_editor(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        #45

        Validira MIDI mapping podatke
        prije GUI prikaza.
        """

        data = self.build_midi_mapping_editor(
            session,
            kit_index,
        )

        mappings = data.get(
            "mappings",
            [],
        )

        errors = []
        warnings = []

        for item in mappings:

            offset = item.get(
                "offset"
            )

            value = item.get(
                "value"
            )

            midi_note = item.get(
                "midi_note"
            )

            if offset is None:
                errors.append(
                    "mapping_without_offset"
                )

            if value is not None:

                try:
                    byte_value = int(
                        value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    errors.append(
                        "mapping_with_invalid_byte"
                    )
                else:

                    if not 0 <= byte_value <= 255:
                        errors.append(
                            "mapping_byte_out_of_range"
                        )

            if midi_note is not None:

                try:
                    midi_value = int(
                        midi_note
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    errors.append(
                        "mapping_with_invalid_midi"
                    )
                else:

                    if not 0 <= midi_value <= 127:
                        errors.append(
                            "midi_note_out_of_range"
                        )

            if not item.get(
                "midi_valid",
                False,
            ):
                warnings.append(
                    {
                        "offset": offset,
                        "message": (
                            "MIDI value is not "
                            "currently confirmed."
                        ),
                    }
                )

        statistics = (
            self.get_midi_mapping_statistics(
                session,
                kit_index,
            )
        )

        if statistics.get(
            "duplicate_midi_count",
            0,
        ) > 0:

            warnings.append(
                {
                    "message": (
                        "Duplicate MIDI notes "
                        "were detected."
                    ),
                    "values": statistics.get(
                        "duplicate_midi_values",
                        [],
                    ),
                }
            )

        return {
            "valid": not bool(
                errors
            ),
            "kit_index": kit_index,
            "mapping_count": len(
                mappings
            ),
            "errors": errors,
            "warnings": warnings,
            "statistics": statistics,
            "source_file_modified": False,
        }


    def build_editor_midi_mapping_package(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        #45

        Kompletan GUI paket za
        MIDI Mapping Editor.
        """

        editor = (
            self.build_midi_mapping_editor(
                session,
                kit_index,
            )
        )

        validation = (
            self.validate_midi_mapping_editor(
                session,
                kit_index,
            )
        )

        return {
            "editor_version": "#45",
            "success": editor.get(
                "success",
                False,
            ),
            "valid": validation.get(
                "valid",
                False,
            ),
            "kit_index": kit_index,
            "kit_name": editor.get(
                "kit_name"
            ),
            "record_size": editor.get(
                "record_size"
            ),
            "mappings": editor.get(
                "mappings",
                [],
            ),
            "mapping_count": editor.get(
                "mapping_count",
                0,
            ),
            "mapping_statistics": (
                validation.get(
                    "statistics",
                    {},
                )
            ),
            "errors": validation.get(
                "errors",
                [],
            ),
            "warnings": validation.get(
                "warnings",
                [],
            ),
            "capabilities": {
                "view_midi_mapping": True,
                "find_by_note": True,
                "find_by_offset": True,
                "edit_midi_note": True,
                "undo": True,
                "redo": True,
                "validation": True,
                "write_back": False,
                "source_file_modification": False,
            },
            "dirty": session.get(
                "dirty",
                False,
            ),
            "undo_available": session.get(
                "undo_available",
                False,
            ),
            "redo_available": session.get(
                "redo_available",
                False,
            ),
            "source_file_modified": False,
        }
    # ===============================================================
    # #49 DRUM KIT FIELD EDITOR
    # ===============================================================

    def build_field_editor(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        #49

        Priprema kompletan Field Editor prikaz
        za odabrani Drum Kit.

        Ne mijenja originalni SET/PCG fajl.
        """

        if not isinstance(session, dict):
            raise TypeError(
                "session must be a dictionary."
            )

        kit = self._find_session_kit(
            session,
            kit_index,
        )

        fields = kit.get(
            "fields",
            [],
        )

        result = []

        for field in fields:

            offsets = list(
                field.get(
                    "offsets",
                    [],
                )
            )

            parameters = field.get(
                "parameters",
                [],
            )

            result.append(
                {
                    "kit_index": kit_index,
                    "field_id": field.get(
                        "field_id"
                    ),
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
                        "score",
                        0.0,
                    ),
                    "parameter_count": len(
                        parameters
                    ),
                    "editable": True,
                    "source_file_modified": False,
                }
            )

        return {
            "success": True,
            "kit_index": kit.get(
                "kit_index",
                kit_index,
            ),
            "kit_name": kit.get(
                "kit_name"
            ),
            "record_size": kit.get(
                "record_size"
            ),
            "field_count": len(
                result
            ),
            "fields": result,
            "dirty": session.get(
                "dirty",
                False,
            ),
            "undo_available": session.get(
                "undo_available",
                False,
            ),
            "redo_available": session.get(
                "redo_available",
                False,
            ),
            "write_back": False,
            "source_file_modified": False,
        }


    def get_field_editor_field(
        self,
        session: dict,
        kit_index: int,
        field_id,
    ) -> dict | None:
        """
        #49

        Pronalazi jedan Field prema field_id.
        """

        data = self.build_field_editor(
            session,
            kit_index,
        )

        for field in data.get(
            "fields",
            [],
        ):
            if field.get(
                "field_id"
            ) == field_id:
                return field

        return None


    def get_field_editor_parameters(
        self,
        session: dict,
        kit_index: int,
        field_id,
    ) -> list[dict]:
        """
        #49

        Vraća parametre pripadajućeg fielda.
        """

        kit = self._find_session_kit(
            session,
            kit_index,
        )

        for field in kit.get(
            "fields",
            [],
        ):

            if field.get(
                "field_id"
            ) != field_id:
                continue

            parameters = field.get(
                "parameters",
                [],
            )

            result = []

            for parameter in parameters:

                result.append(
                    {
                        "offset": parameter.get(
                            "offset"
                        ),
                        "hex_offset": parameter.get(
                            "hex_offset"
                        ),
                        "value": parameter.get(
                            "value"
                        ),
                        "hex": parameter.get(
                            "hex"
                        ),
                        "parameter_type": parameter.get(
                            "parameter_type",
                            "unknown",
                        ),
                        "classification": parameter.get(
                            "classification"
                        ),
                        "confidence": parameter.get(
                            "confidence"
                        ),
                        "confidence_score": parameter.get(
                            "confidence_score",
                            0.0,
                        ),
                        "midi_note": parameter.get(
                            "midi_note"
                        ),
                        "midi_note_name": parameter.get(
                            "midi_note_name"
                        ),
                        "editable": True,
                    }
                )

            return result

        return []


    def edit_field_parameter(
        self,
        session: dict,
        kit_index: int,
        field_id,
        relative_offset: int,
        value: int,
    ) -> dict:
        """
        #49

        Sigurno uređivanje jednog byte parametra
        unutar odabranog fielda.

        Koristi postojeći #42/#47 editing layer.
        """

        field = self.get_field_editor_field(
            session,
            kit_index,
            field_id,
        )

        if field is None:
            return {
                "success": False,
                "changed": False,
                "error": "field_not_found",
                "kit_index": kit_index,
                "field_id": field_id,
                "source_file_modified": False,
            }

        try:
            relative_offset = int(
                relative_offset
            )
        except (
            TypeError,
            ValueError,
        ):
            return {
                "success": False,
                "changed": False,
                "error": "invalid_offset",
                "kit_index": kit_index,
                "field_id": field_id,
                "source_file_modified": False,
            }

        try:
            value = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return {
                "success": False,
                "changed": False,
                "error": "invalid_value",
                "kit_index": kit_index,
                "field_id": field_id,
                "source_file_modified": False,
            }

        if not 0 <= value <= 255:
            return {
                "success": False,
                "changed": False,
                "error": "value_out_of_range",
                "kit_index": kit_index,
                "field_id": field_id,
                "source_file_modified": False,
            }

        field_offsets = field.get(
            "offsets",
            [],
        )

        if field_offsets:
            try:
                field_offsets_int = [
                    int(offset)
                    for offset in field_offsets
                ]
            except (
                TypeError,
                ValueError,
            ):
                field_offsets_int = []

            if field_offsets_int:
                if relative_offset not in field_offsets_int:
                    return {
                        "success": False,
                        "changed": False,
                        "error": "offset_not_in_field",
                        "kit_index": kit_index,
                        "field_id": field_id,
                        "relative_offset": relative_offset,
                        "source_file_modified": False,
                    }

        result = self.edit_session_byte(
            session=session,
            kit_index=kit_index,
            relative_offset=relative_offset,
            value=value,
        )

        return {
            "success": result.get(
                "success",
                False,
            ),
            "changed": result.get(
                "changed",
                False,
            ),
            "kit_index": kit_index,
            "field_id": field_id,
            "relative_offset": relative_offset,
            "value": value,
            "change": result.get(
                "change"
            ),
            "dirty": session.get(
                "dirty",
                False,
            ),
            "undo_available": session.get(
                "undo_available",
                False,
            ),
            "redo_available": session.get(
                "redo_available",
                False,
            ),
            "write_back": False,
            "source_file_modified": False,
        }


    def validate_field_editor(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        #49

        Validira Field Editor strukturu.
        """

        data = self.build_field_editor(
            session,
            kit_index,
        )

        fields = data.get(
            "fields",
            [],
        )

        errors = []
        warnings = []

        field_ids = set()

        for field in fields:

            field_id = field.get(
                "field_id"
            )

            if field_id in field_ids:
                errors.append(
                    {
                        "field_id": field_id,
                        "error": "duplicate_field_id",
                    }
                )
            else:
                field_ids.add(
                    field_id
                )

            start_offset = field.get(
                "start_offset"
            )

            end_offset = field.get(
                "end_offset"
            )

            field_size = field.get(
                "field_size"
            )

            if (
                start_offset is not None
                and end_offset is not None
            ):

                try:
                    start_offset = int(
                        start_offset
                    )

                    end_offset = int(
                        end_offset
                    )

                    if end_offset < start_offset:
                        errors.append(
                            {
                                "field_id": field_id,
                                "error": (
                                    "invalid_field_range"
                                ),
                            }
                        )

                except (
                    TypeError,
                    ValueError,
                ):
                    errors.append(
                        {
                            "field_id": field_id,
                            "error": (
                                "invalid_field_offsets"
                            ),
                        }
                    )

            if field_size is not None:

                try:
                    field_size = int(
                        field_size
                    )

                    if field_size < 0:
                        errors.append(
                            {
                                "field_id": field_id,
                                "error": (
                                    "negative_field_size"
                                ),
                            }
                        )

                except (
                    TypeError,
                    ValueError,
                ):
                    errors.append(
                        {
                            "field_id": field_id,
                            "error": (
                                "invalid_field_size"
                            ),
                        }
                    )

            offsets = field.get(
                "offsets",
                [],
            )

            if not isinstance(
                offsets,
                list,
            ):
                errors.append(
                    {
                        "field_id": field_id,
                        "error": (
                            "invalid_offsets_list"
                        ),
                    }
                )

            if not field.get(
                "classification"
            ):
                warnings.append(
                    {
                        "field_id": field_id,
                        "warning": (
                            "missing_classification"
                        ),
                    }
                )

        return {
            "valid": not bool(
                errors
            ),
            "kit_index": kit_index,
            "field_count": len(
                fields
            ),
            "errors": errors,
            "warnings": warnings,
            "source_file_modified": False,
        }


    def build_editor_field_package(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        #49

        Kompletan GUI paket za
        Drum Kit Field Editor.
        """

        editor = self.build_field_editor(
            session,
            kit_index,
        )

        validation = (
            self.validate_field_editor(
                session,
                kit_index,
            )
        )

        return {
            "editor_version": "#49",
            "success": editor.get(
                "success",
                False,
            ),
            "valid": validation.get(
                "valid",
                False,
            ),
            "kit_index": kit_index,
            "kit_name": editor.get(
                "kit_name"
            ),
            "record_size": editor.get(
                "record_size"
            ),
            "field_count": editor.get(
                "field_count",
                0,
            ),
            "fields": editor.get(
                "fields",
                [],
            ),
            "errors": validation.get(
                "errors",
                [],
            ),
            "warnings": validation.get(
                "warnings",
                [],
            ),
            "capabilities": {
                "view_fields": True,
                "view_field_parameters": True,
                "edit_field_parameters": True,
                "validate_fields": True,
                "undo": True,
                "redo": True,
                "write_back": False,
                "source_file_modification": False,
            },
            "dirty": session.get(
                "dirty",
                False,
            ),
            "undo_available": session.get(
                "undo_available",
                False,
            ),
            "redo_available": session.get(
                "redo_available",
                False,
            ),
            "write_back": False,
            "source_file_modified": False,
        }
