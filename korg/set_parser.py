```python
    # ===============================================================
    # #42 UNDO / REDO + CHANGE HISTORY
    # ===============================================================

    def create_editor_session(
        self,
    ) -> dict:
        """
        #42

        Kreira novu editor sesiju.

        Sve promjene postoje samo u memoriji.
        Originalni PCG/SET fajl se NE mijenja.
        """

        import copy

        model = (
            self.create_editable_drum_kit_model()
        )

        return {
            "session_version": "#42",
            "model": model,
            "history": [],
            "redo_stack": [],
            "change_count": 0,
            "undo_available": False,
            "redo_available": False,
            "dirty": False,
            "write_back": False,
            "source_file_modified": False,
        }

    def _find_session_kit(
        self,
        session: dict,
        kit_index: int,
    ) -> dict:
        """
        Internal helper.

        Pronalazi Drum Kit unutar editor sesije.
        """

        if not isinstance(
            session,
            dict,
        ):
            raise TypeError(
                "session must be a dictionary."
            )

        kits = session.get(
            "model",
            {},
        ).get(
            "kits",
            [],
        )

        for kit in kits:

            if kit.get(
                "kit_index"
            ) == kit_index:

                return kit

        raise IndexError(
            f"Drum Kit {kit_index} was not found."
        )

    def _find_session_parameter(
        self,
        session: dict,
        kit_index: int,
        relative_offset: int,
    ) -> dict:
        """
        Internal helper.

        Pronalazi byte parameter u sesiji.
        """

        kit = self._find_session_kit(
            session,
            kit_index,
        )

        parameters = kit.get(
            "parameters",
            [],
        )

        for parameter in parameters:

            if parameter.get(
                "offset"
            ) == relative_offset:

                return parameter

        raise IndexError(
            f"Offset {relative_offset} was not found "
            f"in Drum Kit {kit_index}."
        )

    def _update_session_parameter(
        self,
        session: dict,
        kit_index: int,
        relative_offset: int,
        value: int,
    ) -> None:
        """
        Internal helper.

        Ažurira parameter i raw byte.
        """

        kit = self._find_session_kit(
            session,
            kit_index,
        )

        parameter = self._find_session_parameter(
            session,
            kit_index,
            relative_offset,
        )

        parameter[
            "value"
        ] = value

        parameter[
            "hex"
        ] = f"{value:02X}"

        parameter_type = parameter.get(
            "parameter_type"
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

            parameter[
                "midi_note"
            ] = value

            try:

                parameter[
                    "midi_note_name"
                ] = midi_to_note(
                    value
                )

            except Exception:

                parameter[
                    "midi_note_name"
                ] = None

        else:

            parameter[
                "midi_note"
            ] = None

            parameter[
                "midi_note_name"
            ] = None

        raw_bytes = kit.get(
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
                "Offset is outside raw byte array."
            )

        raw_bytes[
            relative_offset
        ] = value

        kit[
            "raw_bytes"
        ] = raw_bytes

        kit[
            "raw_hex"
        ] = " ".join(
            f"{byte:02X}"
            for byte in raw_bytes
        )

    def _record_editor_change(
        self,
        session: dict,
        change: dict,
    ) -> None:
        """
        Internal helper.

        Dodaje promjenu u history i briše redo stack.
        """

        session.setdefault(
            "history",
            [],
        ).append(
            change
        )

        session[
            "redo_stack"
        ] = []

        session[
            "change_count"
        ] = len(
            session.get(
                "history",
                [],
            )
        )

        session[
            "undo_available"
        ] = bool(
            session.get(
                "history",
                [],
            )
        )

        session[
            "redo_available"
        ] = False

        session[
            "dirty"
        ] = True

    def edit_session_byte(
        self,
        session: dict,
        kit_index: int,
        relative_offset: int,
        value: int,
    ) -> dict:
        """
        #42

        Mijenja jedan byte u editor sesiji.

        Promjena se zapisuje u history.
        """

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

        parameter = self._find_session_parameter(
            session,
            kit_index,
            relative_offset,
        )

        old_value = parameter.get(
            "value"
        )

        if old_value == value:

            return {
                "success": True,
                "changed": False,
                "message": (
                    "Value is already set."
                ),
                "session": session,
            }

        change = {
            "kit_index": kit_index,
            "relative_offset": relative_offset,
            "old_value": old_value,
            "new_value": value,
            "old_hex": (
                f"{old_value:02X}"
                if isinstance(
                    old_value,
                    int,
                )
                else None
            ),
            "new_hex": f"{value:02X}",
        }

        self._update_session_parameter(
            session,
            kit_index,
            relative_offset,
            value,
        )

        self._record_editor_change(
            session,
            change,
        )

        return {
            "success": True,
            "changed": True,
            "change": change,
            "session": session,
            "dirty": True,
            "source_file_modified": False,
        }

    def edit_session_midi_note(
        self,
        session: dict,
        kit_index: int,
        relative_offset: int,
        midi_note: int,
    ) -> dict:
        """
        #42

        Mijenja MIDI note u editor sesiji.
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

        result = self.edit_session_byte(
            session=session,
            kit_index=kit_index,
            relative_offset=relative_offset,
            value=midi_note,
        )

        if result.get(
            "changed"
        ):

            result[
                "midi_note"
            ] = midi_note

            try:

                result[
                    "midi_note_name"
                ] = midi_to_note(
                    midi_note
                )

            except Exception:

                result[
                    "midi_note_name"
                ] = None

        return result

    def undo_editor_change(
        self,
        session: dict,
    ) -> dict:
        """
        #42

        Poništava posljednju promjenu.
        """

        history = session.get(
            "history",
            [],
        )

        if not history:

            session[
                "undo_available"
            ] = False

            return {
                "success": False,
                "message": (
                    "Nothing to undo."
                ),
                "session": session,
            }

        change = history.pop()

        kit_index = change[
            "kit_index"
        ]

        relative_offset = change[
            "relative_offset"
        ]

        old_value = change[
            "old_value"
        ]

        new_value = change[
            "new_value"
        ]

        self._update_session_parameter(
            session,
            kit_index,
            relative_offset,
            old_value,
        )

        session.setdefault(
            "redo_stack",
            [],
        ).append(
            change
        )

        session[
            "change_count"
        ] = len(
            history
        )

        session[
            "undo_available"
        ] = bool(
            history
        )

        session[
            "redo_available"
        ] = True

        session[
            "dirty"
        ] = bool(
            history
        )

        return {
            "success": True,
            "operation": "undo",
            "kit_index": kit_index,
            "relative_offset": relative_offset,
            "restored_value": old_value,
            "undone_value": new_value,
            "session": session,
            "source_file_modified": False,
        }

    def redo_editor_change(
        self,
        session: dict,
    ) -> dict:
        """
        #42

        Ponovo primjenjuje posljednju undo promjenu.
        """

        redo_stack = session.get(
            "redo_stack",
            [],
        )

        if not redo_stack:

            session[
                "redo_available"
            ] = False

            return {
                "success": False,
                "message": (
                    "Nothing to redo."
                ),
                "session": session,
            }

        change = redo_stack.pop()

        kit_index = change[
            "kit_index"
        ]

        relative_offset = change[
            "relative_offset"
        ]

        old_value = change[
            "old_value"
        ]

        new_value = change[
            "new_value"
        ]

        self._update_session_parameter(
            session,
            kit_index,
            relative_offset,
            new_value,
        )

        session.setdefault(
            "history",
            [],
        ).append(
            change
        )

        session[
            "change_count"
        ] = len(
            session[
                "history"
            ]
        )

        session[
            "undo_available"
        ] = True

        session[
            "redo_available"
        ] = bool(
            redo_stack
        )

        session[
            "dirty"
        ] = True

        return {
            "success": True,
            "operation": "redo",
            "kit_index": kit_index,
            "relative_offset": relative_offset,
            "restored_value": new_value,
            "previous_value": old_value,
            "session": session,
            "source_file_modified": False,
        }

    def get_editor_change_history(
        self,
        session: dict,
    ) -> list[dict]:
        """
        #42

        Vraća kompletnu historiju promjena.
        """

        return list(
            session.get(
                "history",
                [],
            )
        )

    def get_editor_redo_history(
        self,
        session: dict,
    ) -> list[dict]:
        """
        #42

        Vraća trenutno dostupne redo promjene.
        """

        return list(
            session.get(
                "redo_stack",
                [],
            )
        )

    def clear_editor_history(
        self,
        session: dict,
    ) -> dict:
        """
        #42

        Briše undo/redo historiju.

        Trenutne vrijednosti modela ostaju iste.
        """

        session[
            "history"
        ] = []

        session[
            "redo_stack"
        ] = []

        session[
            "change_count"
        ] = 0

        session[
            "undo_available"
        ] = False

        session[
            "redo_available"
        ] = False

        return {
            "success": True,
            "history_cleared": True,
            "change_count": 0,
            "dirty": session.get(
                "dirty",
                False,
            ),
            "source_file_modified": False,
        }

    def validate_editor_session(
        self,
        session: dict,
    ) -> dict:
        """
        #42

        Validira trenutno stanje editor sesije.
        """

        model = session.get(
            "model"
        )

        if model is None:

            return {
                "valid": False,
                "errors": [
                    "Session has no model."
                ],
            }

        validation = (
            self.validate_editable_drum_kit_model(
                model
            )
        )

        errors = list(
            validation.get(
                "errors",
                [],
            )
        )

        warnings = list(
            validation.get(
                "warnings",
                [],
            )
        )

        if session.get(
            "source_file_modified",
            False,
        ):

            errors.append(
                "Source file modification detected."
            )

        if session.get(
            "write_back",
            False,
        ):

            errors.append(
                "Write-back must remain disabled."
            )

        return {
            "valid": (
                len(errors) == 0
            ),
            "errors": errors,
            "warnings": warnings,
            "change_count": session.get(
                "change_count",
                0,
            ),
            "undo_available": session.get(
                "undo_available",
                False,
            ),
            "redo_available": session.get(
                "redo_available",
                False,
            ),
            "dirty": session.get(
                "dirty",
                False,
            ),
            "source_file_modified": (
                session.get(
                    "source_file_modified",
                    False,
                )
            ),
            "write_back": session.get(
                "write_back",
                False,
            ),
        }

    def get_editor_session_status(
        self,
        session: dict,
    ) -> dict:
        """
        #42

        Vraća kratak status editor sesije.
        """

        return {
            "session_version": (
                session.get(
                    "session_version",
                    "#42",
                )
            ),
            "dirty": session.get(
                "dirty",
                False,
            ),
            "change_count": session.get(
                "change_count",
                0,
            ),
            "undo_available": session.get(
                "undo_available",
                False,
            ),
            "redo_available": session.get(
                "redo_available",
                False,
            ),
            "write_back": session.get(
                "write_back",
                False,
            ),
            "source_file_modified": (
                session.get(
                    "source_file_modified",
                    False,
                )
            ),
        }
```
