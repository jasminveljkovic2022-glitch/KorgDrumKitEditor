import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class KorgDrumKitEditorGUI:
    """
    #48 DRUM KIT PARAMETER EDITOR GUI

    GUI sloj za Korg Drum Kit Editor.

    Omogućava:
    - prikaz Drum Kitova
    - MIDI Mapping Editor
    - prikaz byte parametara
    - uređivanje byte vrijednosti 0-255
    - Undo / Redo
    - Validation
    - promjene samo u memoriji

    ORIGINALNI SET/PCG FAJL SE NE MIJENJA.
    """

    def __init__(self, root):
        self.root = root

        self.root.title(
            "Korg Drum Kit Editor"
        )

        self.root.geometry(
            "1350x800"
        )

        self.root.minsize(
            1000,
            650,
        )

        self.session = None
        self.current_kit_index = None

        self.mapping_data = []
        self.parameter_data = []

        self.create_widgets()

    # ============================================================
    # MAIN GUI
    # ============================================================

    def create_widgets(self):

        top = ttk.Frame(
            self.root,
            padding=10,
        )

        top.pack(
            fill="x"
        )

        ttk.Button(
            top,
            text="Open SET / PCG",
            command=self.open_file,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            top,
            text="Refresh",
            command=self.refresh_editor,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            top,
            text="Edit MIDI",
            command=self.edit_selected_midi,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            top,
            text="Edit Parameter",
            command=self.edit_selected_parameter,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            top,
            text="Undo",
            command=self.undo,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            top,
            text="Redo",
            command=self.redo,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            top,
            text="Validate",
            command=self.validate_mapping,
        ).pack(
            side="left",
            padx=5,
        )

        status_frame = ttk.Frame(
            self.root,
            padding=(10, 0),
        )

        status_frame.pack(
            fill="x"
        )

        self.status_label = ttk.Label(
            status_frame,
            text="No file loaded.",
        )

        self.status_label.pack(
            side="left"
        )

        self.modified_label = ttk.Label(
            status_frame,
            text="Source file modified: NO",
        )

        self.modified_label.pack(
            side="right"
        )

        main = ttk.PanedWindow(
            self.root,
            orient="horizontal",
        )

        main.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        # ========================================================
        # DRUM KIT LIST
        # ========================================================

        kit_frame = ttk.LabelFrame(
            main,
            text="Drum Kits",
            padding=5,
        )

        main.add(
            kit_frame,
            weight=1,
        )

        self.kit_tree = ttk.Treeview(
            kit_frame,
            columns=(
                "index",
                "name",
                "size",
            ),
            show="headings",
        )

        self.kit_tree.heading(
            "index",
            text="Index",
        )

        self.kit_tree.heading(
            "name",
            text="Name",
        )

        self.kit_tree.heading(
            "size",
            text="Size",
        )

        self.kit_tree.column(
            "index",
            width=60,
        )

        self.kit_tree.column(
            "name",
            width=180,
        )

        self.kit_tree.column(
            "size",
            width=70,
        )

        self.kit_tree.pack(
            fill="both",
            expand=True,
        )

        self.kit_tree.bind(
            "<<TreeviewSelect>>",
            self.on_kit_selected,
        )

        # ========================================================
        # RIGHT SIDE NOTEBOOK
        # ========================================================

        editor_frame = ttk.Frame(
            main,
            padding=5,
        )

        main.add(
            editor_frame,
            weight=5,
        )

        self.notebook = ttk.Notebook(
            editor_frame
        )

        self.notebook.pack(
            fill="both",
            expand=True,
        )

        self.create_midi_tab()

        self.create_parameter_tab()

        # ========================================================
        # BOTTOM INFORMATION
        # ========================================================

        bottom = ttk.Frame(
            self.root,
            padding=10,
        )

        bottom.pack(
            fill="x"
        )

        self.info_label = ttk.Label(
            bottom,
            text="Mapping count: 0",
        )

        self.info_label.pack(
            side="left"
        )

        self.validation_label = ttk.Label(
            bottom,
            text="Validation: not checked",
        )

        self.validation_label.pack(
            side="right"
        )

    # ============================================================
    # MIDI TAB
    # ============================================================

    def create_midi_tab(self):

        mapping_frame = ttk.Frame(
            self.notebook,
            padding=5,
        )

        self.notebook.add(
            mapping_frame,
            text="MIDI Mapping",
        )

        columns = (
            "midi",
            "name",
            "offset",
            "hex_offset",
            "value",
            "hex",
            "classification",
            "confidence",
        )

        self.mapping_tree = ttk.Treeview(
            mapping_frame,
            columns=columns,
            show="headings",
        )

        headings = {
            "midi": "MIDI",
            "name": "Note",
            "offset": "Offset",
            "hex_offset": "HEX Offset",
            "value": "Value",
            "hex": "HEX",
            "classification": "Classification",
            "confidence": "Confidence",
        }

        widths = {
            "midi": 55,
            "name": 80,
            "offset": 80,
            "hex_offset": 100,
            "value": 65,
            "hex": 65,
            "classification": 130,
            "confidence": 90,
        }

        for column in columns:

            self.mapping_tree.heading(
                column,
                text=headings[column],
            )

            self.mapping_tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        self.mapping_tree.pack(
            fill="both",
            expand=True,
        )

        self.mapping_tree.bind(
            "<Double-1>",
            self.on_mapping_double_click,
        )

    # ============================================================
    # PARAMETER TAB
    # ============================================================

    def create_parameter_tab(self):

        parameter_frame = ttk.Frame(
            self.notebook,
            padding=5,
        )

        self.notebook.add(
            parameter_frame,
            text="Parameters",
        )

        parameter_top = ttk.Frame(
            parameter_frame
        )

        parameter_top.pack(
            fill="x",
            pady=(0, 5),
        )

        ttk.Button(
            parameter_top,
            text="Edit Selected Parameter",
            command=self.edit_selected_parameter,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            parameter_top,
            text="Refresh Parameters",
            command=self.refresh_current_parameters,
        ).pack(
            side="left",
            padx=3,
        )

        columns = (
            "offset",
            "hex_offset",
            "value",
            "hex",
            "type",
            "classification",
            "confidence",
        )

        self.parameter_tree = ttk.Treeview(
            parameter_frame,
            columns=columns,
            show="headings",
        )

        headings = {
            "offset": "Offset",
            "hex_offset": "HEX Offset",
            "value": "Value",
            "hex": "HEX",
            "type": "Parameter Type",
            "classification": "Classification",
            "confidence": "Confidence",
        }

        widths = {
            "offset": 90,
            "hex_offset": 110,
            "value": 70,
            "hex": 70,
            "type": 180,
            "classification": 140,
            "confidence": 100,
        }

        for column in columns:

            self.parameter_tree.heading(
                column,
                text=headings[column],
            )

            self.parameter_tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        self.parameter_tree.pack(
            fill="both",
            expand=True,
        )

        self.parameter_tree.bind(
            "<Double-1>",
            self.on_parameter_double_click,
        )

    # ============================================================
    # FILE
    # ============================================================

    def open_file(self):

        filename = filedialog.askopenfilename(
            title="Open Korg SET / PCG file",
            filetypes=[
                (
                    "Korg files",
                    "*.SET *.PCG *.set *.pcg",
                ),
                (
                    "All files",
                    "*.*",
                ),
            ],
        )

        if not filename:
            return

        self.status_label.config(
            text=f"Selected: {filename}"
        )

        messagebox.showinfo(
            "File selected",
            "File selected successfully.\n\n"
            "The original file will NOT be modified.",
        )

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh_editor(self):

        if self.session is None:

            self.clear_mapping_table()

            self.clear_parameter_table()

            self.status_label.config(
                text="No active parser session."
            )

            return

        self.load_kits_from_session()

    # ============================================================
    # SESSION
    # ============================================================

    def set_session(
        self,
        session,
    ):

        self.session = session

        self.load_kits_from_session()

    def load_kits_from_session(self):

        self.kit_tree.delete(
            *self.kit_tree.get_children()
        )

        if not isinstance(
            self.session,
            dict,
        ):
            return

        model = self.session.get(
            "model",
            {},
        )

        kits = model.get(
            "kits",
            [],
        )

        for kit in kits:

            self.kit_tree.insert(
                "",
                "end",
                values=(
                    kit.get(
                        "kit_index"
                    ),
                    kit.get(
                        "kit_name"
                    ),
                    kit.get(
                        "record_size"
                    ),
                ),
            )

        self.status_label.config(
            text=f"Loaded kits: {len(kits)}"
        )

    # ============================================================
    # KIT SELECTION
    # ============================================================

    def on_kit_selected(
        self,
        event=None,
    ):

        selection = self.kit_tree.selection()

        if not selection:
            return

        item = self.kit_tree.item(
            selection[0]
        )

        values = item.get(
            "values",
            [],
        )

        if not values:
            return

        try:

            kit_index = int(
                values[0]
            )

        except (
            TypeError,
            ValueError,
        ):

            return

        self.current_kit_index = kit_index

        self.load_midi_mapping(
            kit_index
        )

        self.load_parameters(
            kit_index
        )

    # ============================================================
    # MIDI MAPPING
    # ============================================================

    def load_midi_mapping(
        self,
        kit_index,
    ):

        self.clear_mapping_table()

        if self.session is None:
            return

        parser = self.get_parser()

        if parser is None:
            return

        try:

            data = parser.build_midi_mapping_editor(
                self.session,
                kit_index,
            )

        except Exception as exc:

            messagebox.showerror(
                "MIDI Mapping Error",
                str(exc),
            )

            return

        self.mapping_data = data.get(
            "mappings",
            [],
        )

        for mapping in self.mapping_data:

            self.mapping_tree.insert(
                "",
                "end",
                values=(
                    mapping.get(
                        "midi_note"
                    ),
                    mapping.get(
                        "midi_note_name"
                    ),
                    mapping.get(
                        "offset"
                    ),
                    mapping.get(
                        "hex_offset"
                    ),
                    mapping.get(
                        "value"
                    ),
                    mapping.get(
                        "hex"
                    ),
                    mapping.get(
                        "classification"
                    ),
                    mapping.get(
                        "confidence_score"
                    ),
                ),
            )

        self.info_label.config(
            text=(
                f"Mapping count: "
                f"{len(self.mapping_data)}"
            )
        )

        self.validation_label.config(
            text="Validation: loaded"
        )

    def clear_mapping_table(self):

        self.mapping_tree.delete(
            *self.mapping_tree.get_children()
        )

        self.mapping_data = []

        self.info_label.config(
            text="Mapping count: 0"
        )

    # ============================================================
    # PARAMETERS
    # ============================================================

    def load_parameters(
        self,
        kit_index,
    ):

        self.clear_parameter_table()

        if self.session is None:
            return

        parser = self.get_parser()

        if parser is None:
            return

        try:

            data = parser.build_editor_parameter_list(
                self.session,
                kit_index,
            )

        except Exception as exc:

            messagebox.showerror(
                "Parameter Error",
                str(exc),
            )

            return

        self.parameter_data = data

        for parameter in self.parameter_data:

            self.parameter_tree.insert(
                "",
                "end",
                values=(
                    parameter.get(
                        "offset"
                    ),
                    parameter.get(
                        "hex_offset"
                    ),
                    parameter.get(
                        "value"
                    ),
                    parameter.get(
                        "hex"
                    ),
                    parameter.get(
                        "parameter_type"
                    ),
                    parameter.get(
                        "classification"
                    ),
                    parameter.get(
                        "confidence_score"
                    ),
                ),
            )

        self.status_label.config(
            text=(
                f"Kit {kit_index}: "
                f"{len(self.parameter_data)} parameters"
            )
        )

    def clear_parameter_table(self):

        self.parameter_tree.delete(
            *self.parameter_tree.get_children()
        )

        self.parameter_data = []

    def refresh_current_parameters(self):

        if self.current_kit_index is None:
            return

        self.load_parameters(
            self.current_kit_index
        )

    # ============================================================
    # PARAMETER SELECTION
    # ============================================================

    def on_parameter_double_click(
        self,
        event=None,
    ):

        self.edit_selected_parameter()

    def edit_selected_parameter(self):

        selection = self.parameter_tree.selection()

        if not selection:

            messagebox.showwarning(
                "No selection",
                "Select a parameter first.",
            )

            return

        item_id = selection[0]

        item = self.parameter_tree.item(
            item_id
        )

        values = item.get(
            "values",
            [],
        )

        if not values:
            return

        current_offset = values[0]

        current_value = values[2]

        self.open_parameter_editor(
            item_id,
            current_offset,
            current_value,
        )

    # ============================================================
    # PARAMETER EDIT WINDOW
    # ============================================================

    def open_parameter_editor(
        self,
        item_id,
        current_offset,
        current_value,
    ):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Edit Drum Kit Parameter"
        )

        window.geometry(
            "420x300"
        )

        window.resizable(
            False,
            False,
        )

        window.transient(
            self.root
        )

        ttk.Label(
            window,
            text="Drum Kit Parameter",
            font=(
                "TkDefaultFont",
                12,
                "bold",
            ),
        ).pack(
            pady=(20, 10)
        )

        info_frame = ttk.Frame(
            window
        )

        info_frame.pack(
            fill="x",
            padx=30,
        )

        ttk.Label(
            info_frame,
            text=f"Offset: {current_offset}",
        ).pack(
            anchor="w",
            pady=3,
        )

        ttk.Label(
            info_frame,
            text=(
                "Byte value must be between 0 and 255."
            ),
        ).pack(
            anchor="w",
            pady=3,
        )

        value_var = tk.StringVar(
            value=str(
                current_value
            )
        )

        ttk.Label(
            window,
            text="New value:",
        ).pack(
            pady=(20, 5)
        )

        entry = ttk.Entry(
            window,
            textvariable=value_var,
            width=20,
        )

        entry.pack(
            pady=5
        )

        def apply_change():

            try:

                new_value = int(
                    value_var.get()
                )

            except (
                TypeError,
                ValueError,
            ):

                messagebox.showerror(
                    "Invalid value",
                    "Parameter value must be an integer.",
                    parent=window,
                )

                return

            if not 0 <= new_value <= 255:

                messagebox.showerror(
                    "Invalid value",
                    "Parameter value must be between 0 and 255.",
                    parent=window,
                )

                return

            self.apply_parameter_change(
                item_id,
                current_offset,
                new_value,
            )

            window.destroy()

        buttons = ttk.Frame(
            window
        )

        buttons.pack(
            pady=25
        )

        ttk.Button(
            buttons,
            text="Apply",
            command=apply_change,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            buttons,
            text="Cancel",
            command=window.destroy,
        ).pack(
            side="left",
            padx=5,
        )

        entry.focus_set()

        entry.select_range(
            0,
            tk.END,
        )

    # ============================================================
    # APPLY PARAMETER CHANGE
    # ============================================================

    def apply_parameter_change(
        self,
        item_id,
        relative_offset,
        new_value,
    ):

        if self.session is None:

            messagebox.showwarning(
                "No session",
                "No active parser session.",
            )

            return

        parser = self.get_parser()

        if parser is None:

            messagebox.showwarning(
                "Parser unavailable",
                "Existing Korg parser could not be loaded.",
            )

            return

        try:

            relative_offset = int(
                relative_offset
            )

        except (
            TypeError,
            ValueError,
        ):

            messagebox.showerror(
                "Edit error",
                "Invalid parameter offset.",
            )

            return

        try:

            new_value = int(
                new_value
            )

        except (
            TypeError,
            ValueError,
        ):

            messagebox.showerror(
                "Edit error",
                "Invalid parameter value.",
            )

            return

        if not 0 <= new_value <= 255:

            messagebox.showerror(
                "Edit error",
                "Parameter value must be between 0 and 255.",
            )

            return

        try:

            result = parser.edit_editor_parameter(
                self.session,
                self.current_kit_index,
                relative_offset,
                new_value,
            )

        except Exception as exc:

            messagebox.showerror(
                "Edit error",
                str(exc),
            )

            return

        if not result.get(
            "success",
            False,
        ):

            messagebox.showerror(
                "Edit failed",
                "The parameter could not be changed.",
            )

            return

        self.refresh_current_parameters()

        self.modified_label.config(
            text="Source file modified: NO"
        )

        self.status_label.config(
            text=(
                f"Parameter at offset "
                f"{relative_offset} changed in memory."
            )
        )

    # ============================================================
    # MIDI EDIT
    # ============================================================
    ttk.Button(
            top,
            text="Field Editor",
            command=self.open_field_editor,
        ).pack(
            side="left",
            padx=5,
        )

    def edit_selected_midi(self):

        selection = self.mapping_tree.selection()

        if not selection:

            messagebox.showwarning(
                "No selection",
                "Select a MIDI mapping first.",
            )

            return

        item_id = selection[0]

        item = self.mapping_tree.item(
            item_id
        )

        values = item.get(
            "values",
            [],
        )

        if not values:
            return

        current_midi = values[0]

        self.open_midi_editor(
            item_id,
            current_midi,
        )

    def on_mapping_double_click(
        self,
        event=None,
    ):

        self.edit_selected_midi()

    def open_midi_editor(
        self,
        item_id,
        current_midi,
    ):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Edit MIDI Mapping"
        )

        window.geometry(
            "360x220"
        )

        window.transient(
            self.root
        )

        ttk.Label(
            window,
            text="MIDI Note (0–127)",
        ).pack(
            pady=(20, 5)
        )

        midi_var = tk.StringVar(
            value=str(
                current_midi
            )
        )

        entry = ttk.Entry(
            window,
            textvariable=midi_var,
            width=15,
        )

        entry.pack(
            pady=5
        )

        def apply_change():

            try:

                new_midi = int(
                    midi_var.get()
                )

            except (
                TypeError,
                ValueError,
            ):

                messagebox.showerror(
                    "Invalid MIDI",
                    "MIDI note must be an integer.",
                    parent=window,
                )

                return

            if not 0 <= new_midi <= 127:

                messagebox.showerror(
                    "Invalid MIDI",
                    "MIDI note must be between 0 and 127.",
                    parent=window,
                )

                return

            self.apply_midi_change(
                item_id,
                new_midi,
            )

            window.destroy()

        buttons = ttk.Frame(
            window
        )

        buttons.pack(
            pady=20
        )

        ttk.Button(
            buttons,
            text="Apply",
            command=apply_change,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            buttons,
            text="Cancel",
            command=window.destroy,
        ).pack(
            side="left",
            padx=5,
        )

        entry.focus_set()

    def apply_midi_change(
        self,
        item_id,
        new_midi,
    ):

        if self.session is None:
            return

        item = self.mapping_tree.item(
            item_id
        )

        values = list(
            item.get(
                "values",
                [],
            )
        )

        if not values:
            return

        try:

            offset = int(
                values[2]
            )

        except (
            TypeError,
            ValueError,
        ):

            messagebox.showerror(
                "Edit error",
                "Invalid mapping offset.",
            )

            return

        parser = self.get_parser()

        if parser is None:

            messagebox.showwarning(
                "Parser unavailable",
                "Existing Korg parser could not be loaded.",
            )

            return

        try:

            result = parser.edit_editor_midi_mapping(
                self.session,
                self.current_kit_index,
                offset,
                new_midi,
            )

        except Exception as exc:

            messagebox.showerror(
                "Edit error",
                str(exc),
            )

            return

        if not result.get(
            "success",
            False,
        ):

            messagebox.showerror(
                "Edit failed",
                "The MIDI mapping could not be changed.",
            )

            return

        values[0] = result.get(
            "midi_note",
            new_midi,
        )

        values[1] = result.get(
            "midi_note_name",
            "",
        )

        self.mapping_tree.item(
            item_id,
            values=values,
        )

        self.modified_label.config(
            text="Source file modified: NO"
        )

        self.status_label.config(
            text="MIDI mapping changed in memory."
        )

    # ============================================================
    # PARSER
    # ============================================================

    def get_parser(self):

        try:

            from korg.set_parser import KorgSetParser

            return KorgSetParser()

        except Exception:

            return None

    # ============================================================
    # UNDO
    # ============================================================

    def undo(self):

        if self.session is None:
            return

        parser = self.get_parser()

        if parser is None:
            return

        try:

            result = parser.undo_session_change(
                self.session
            )

        except Exception:

            result = None

        if result:

            self.refresh_current_mapping()

            self.refresh_current_parameters()

            self.status_label.config(
                text="Undo applied."
            )

    # ============================================================
    # REDO
    # ============================================================

    def redo(self):

        if self.session is None:
            return

        parser = self.get_parser()

        if parser is None:
            return

        try:

            result = parser.redo_session_change(
                self.session
            )

        except Exception:

            result = None

        if result:

            self.refresh_current_mapping()

            self.refresh_current_parameters()

            self.status_label.config(
                text="Redo applied."
            )

    # ============================================================
    # REFRESH CURRENT MAPPING
    # ============================================================

    def refresh_current_mapping(self):

        if self.current_kit_index is not None:

            self.load_midi_mapping(
                self.current_kit_index
            )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_mapping(self):

        if self.session is None:

            messagebox.showwarning(
                "Validation",
                "No active session.",
            )

            return

        if self.current_kit_index is None:

            messagebox.showwarning(
                "Validation",
                "Select a Drum Kit first.",
            )

            return

        parser = self.get_parser()

        if parser is None:
            return

        try:

            result = parser.validate_midi_mapping_editor(
                self.session,
                self.current_kit_index,
            )

        except Exception as exc:

            messagebox.showerror(
                "Validation Error",
                str(exc),
            )

            return

        if result.get(
            "valid",
            False,
        ):

            self.validation_label.config(
                text="Validation: OK"
            )

            messagebox.showinfo(
                "Validation",
                "MIDI Mapping validation passed.",
            )

        else:

            self.validation_label.config(
                text="Validation: ERRORS"
            )

            errors = result.get(
                "errors",
                [],
            )

            messagebox.showerror(
                "Validation",
                "\n".join(
                    str(error)
                    for error in errors
                )
                if errors
                else "Validation failed.",
            )

```python
    # ============================================================
    # #50 DRUM KIT FIELD EDITOR GUI
    # ============================================================

    def open_field_editor(self):
        """
        #50

        Otvara GUI za pregled i uređivanje
        Field strukture odabranog Drum Kita.

        Promjene se rade samo u session memoriji.
        Originalni SET/PCG fajl se ne mijenja.
        """

        if self.session is None:
            messagebox.showwarning(
                "Field Editor",
                "No active parser session.",
            )
            return

        if self.current_kit_index is None:
            messagebox.showwarning(
                "Field Editor",
                "Select a Drum Kit first.",
            )
            return

        parser = self.get_parser()

        if parser is None:
            messagebox.showerror(
                "Field Editor",
                "Korg parser could not be loaded.",
            )
            return

        try:
            fields = parser.build_editor_field_list(
                self.session,
                self.current_kit_index,
            )
        except Exception as exc:
            messagebox.showerror(
                "Field Editor Error",
                str(exc),
            )
            return

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Drum Kit Field Editor"
        )

        window.geometry(
            "1050x650"
        )

        window.transient(
            self.root
        )

        # --------------------------------------------------------
        # TOP INFORMATION
        # --------------------------------------------------------

        header = ttk.Frame(
            window,
            padding=10,
        )

        header.pack(
            fill="x"
        )

        ttk.Label(
            header,
            text=(
                f"Drum Kit: "
                f"{self.current_kit_index}"
            ),
            font=(
                "TkDefaultFont",
                11,
                "bold",
            ),
        ).pack(
            side="left"
        )

        ttk.Label(
            header,
            text=(
                f"Fields: {len(fields)}"
            ),
        ).pack(
            side="right"
        )

        # --------------------------------------------------------
        # FIELD TABLE
        # --------------------------------------------------------

        table_frame = ttk.Frame(
            window,
            padding=(10, 0),
        )

        table_frame.pack(
            fill="both",
            expand=True,
        )

        columns = (
            "field_id",
            "start",
            "end",
            "size",
            "classification",
            "score",
            "parameters",
        )

        field_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        headings = {
            "field_id": "Field ID",
            "start": "Start Offset",
            "end": "End Offset",
            "size": "Size",
            "classification": "Classification",
            "score": "Score",
            "parameters": "Parameters",
        }

        widths = {
            "field_id": 100,
            "start": 110,
            "end": 110,
            "size": 80,
            "classification": 160,
            "score": 90,
            "parameters": 100,
        }

        for column in columns:
            field_tree.heading(
                column,
                text=headings[column],
            )

            field_tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=field_tree.yview,
        )

        field_tree.configure(
            yscrollcommand=scrollbar.set
        )

        field_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        # --------------------------------------------------------
        # INSERT FIELDS
        # --------------------------------------------------------

        for field in fields:

            field_tree.insert(
                "",
                "end",
                values=(
                    field.get(
                        "field_id"
                    ),
                    field.get(
                        "start_offset"
                    ),
                    field.get(
                        "end_offset"
                    ),
                    field.get(
                        "field_size"
                    ),
                    field.get(
                        "classification"
                    ),
                    field.get(
                        "score"
                    ),
                    field.get(
                        "parameter_count"
                    ),
                ),
            )

        # --------------------------------------------------------
        # DETAILS
        # --------------------------------------------------------

        details = ttk.LabelFrame(
            window,
            text="Selected Field",
            padding=10,
        )

        details.pack(
            fill="x",
            padx=10,
            pady=10,
        )

        details_label = ttk.Label(
            details,
            text="No field selected.",
        )

        details_label.pack(
            anchor="w"
        )

        # --------------------------------------------------------
        # FIELD SELECTION
        # --------------------------------------------------------

        def show_field_details(
            event=None
        ):

            selection = field_tree.selection()

            if not selection:
                return

            item = field_tree.item(
                selection[0]
            )

            values = item.get(
                "values",
                [],
            )

            if not values:
                return

            details_label.config(
                text=(
                    f"Field ID: {values[0]}    "
                    f"Offset: {values[1]} - {values[2]}    "
                    f"Size: {values[3]}    "
                    f"Classification: {values[4]}    "
                    f"Score: {values[5]}    "
                    f"Parameters: {values[6]}"
                )
            )

        field_tree.bind(
            "<<TreeviewSelect>>",
            show_field_details,
        )

        # --------------------------------------------------------
        # EDIT PARAMETER
        # --------------------------------------------------------

        def edit_field_parameter():

            selection = field_tree.selection()

            if not selection:
                messagebox.showwarning(
                    "Field Editor",
                    "Select a field first.",
                    parent=window,
                )
                return

            item = field_tree.item(
                selection[0]
            )

            values = item.get(
                "values",
                [],
            )

            if not values:
                return

            try:
                start_offset = int(
                    values[1]
                )

                end_offset = int(
                    values[2]
                )

            except (
                TypeError,
                ValueError,
            ):
                messagebox.showerror(
                    "Field Editor",
                    "Invalid field offsets.",
                    parent=window,
                )
                return

            try:
                parameters = parser.build_editor_parameter_list(
                    self.session,
                    self.current_kit_index,
                )
            except Exception as exc:
                messagebox.showerror(
                    "Field Editor",
                    str(exc),
                    parent=window,
                )
                return

            field_parameters = []

            for parameter in parameters:

                offset = parameter.get(
                    "offset"
                )

                try:
                    offset_int = int(
                        offset
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                if (
                    start_offset
                    <= offset_int
                    <= end_offset
                ):
                    field_parameters.append(
                        parameter
                    )

            if not field_parameters:
                messagebox.showinfo(
                    "Field Editor",
                    "No editable parameters were found in this field.",
                    parent=window,
                )
                return

            parameter_window = tk.Toplevel(
                window
            )

            parameter_window.title(
                "Field Parameters"
            )

            parameter_window.geometry(
                "900x500"
            )

            parameter_window.transient(
                window
            )

            parameter_tree = ttk.Treeview(
                parameter_window,
                columns=(
                    "offset",
                    "hex_offset",
                    "value",
                    "hex",
                    "type",
                    "classification",
                    "confidence",
                ),
                show="headings",
                selectmode="browse",
            )

            parameter_headings = {
                "offset": "Offset",
                "hex_offset": "HEX Offset",
                "value": "Value",
                "hex": "HEX",
                "type": "Parameter Type",
                "classification": "Classification",
                "confidence": "Confidence",
            }

            parameter_widths = {
                "offset": 80,
                "hex_offset": 100,
                "value": 70,
                "hex": 70,
                "type": 170,
                "classification": 140,
                "confidence": 90,
            }

            for column in parameter_headings:

                parameter_tree.heading(
                    column,
                    text=parameter_headings[
                        column
                    ],
                )

                parameter_tree.column(
                    column,
                    width=parameter_widths[
                        column
                    ],
                    anchor="center",
                )

            parameter_tree.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10,
            )

            for parameter in field_parameters:

                parameter_tree.insert(
                    "",
                    "end",
                    values=(
                        parameter.get(
                            "offset"
                        ),
                        parameter.get(
                            "hex_offset"
                        ),
                        parameter.get(
                            "value"
                        ),
                        parameter.get(
                            "hex"
                        ),
                        parameter.get(
                            "parameter_type"
                        ),
                        parameter.get(
                            "classification"
                        ),
                        parameter.get(
                            "confidence_score"
                        ),
                    ),
                )

            # ----------------------------------------------------
            # EDIT SELECTED VALUE
            # ----------------------------------------------------

            def edit_parameter_value():

                selection = (
                    parameter_tree.selection()
                )

                if not selection:
                    messagebox.showwarning(
                        "Parameter Editor",
                        "Select a parameter first.",
                        parent=parameter_window,
                    )
                    return

                item_id = selection[0]

                item = parameter_tree.item(
                    item_id
                )

                item_values = list(
                    item.get(
                        "values",
                        [],
                    )
                )

                if not item_values:
                    return

                try:
                    offset = int(
                        item_values[0]
                    )

                    current_value = int(
                        item_values[2]
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    messagebox.showerror(
                        "Parameter Editor",
                        "Invalid parameter value.",
                        parent=parameter_window,
                    )
                    return

                edit_window = tk.Toplevel(
                    parameter_window
                )

                edit_window.title(
                    "Edit Parameter"
                )

                edit_window.geometry(
                    "360x220"
                )

                edit_window.transient(
                    parameter_window
                )

                ttk.Label(
                    edit_window,
                    text="Byte Value (0-255)",
                ).pack(
                    pady=(20, 5)
                )

                value_var = tk.StringVar(
                    value=str(
                        current_value
                    )
                )

                entry = ttk.Entry(
                    edit_window,
                    textvariable=value_var,
                    width=15,
                )

                entry.pack(
                    pady=5
                )

                def apply_parameter_change():

                    try:
                        new_value = int(
                            value_var.get()
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        messagebox.showerror(
                            "Invalid Value",
                            "Value must be an integer.",
                            parent=edit_window,
                        )
                        return

                    if not 0 <= new_value <= 255:
                        messagebox.showerror(
                            "Invalid Value",
                            "Value must be between 0 and 255.",
                            parent=edit_window,
                        )
                        return

                    try:
                        result = (
                            parser.edit_editor_parameter(
                                self.session,
                                self.current_kit_index,
                                offset,
                                new_value,
                            )
                        )
                    except Exception as exc:
                        messagebox.showerror(
                            "Edit Error",
                            str(exc),
                            parent=edit_window,
                        )
                        return

                    if not result.get(
                        "success",
                        False,
                    ):
                        messagebox.showerror(
                            "Edit Failed",
                            "Parameter could not be changed.",
                            parent=edit_window,
                        )
                        return

                    item_values[2] = new_value
                    item_values[3] = (
                        f"{new_value:02X}"
                    )

                    parameter_tree.item(
                        item_id,
                        values=item_values,
                    )

                    self.modified_label.config(
                        text=(
                            "Source file modified: NO"
                        )
                    )

                    self.status_label.config(
                        text=(
                            "Drum Kit field parameter "
                            "changed in memory."
                        )
                    )

                    edit_window.destroy()

                buttons = ttk.Frame(
                    edit_window
                )

                buttons.pack(
                    pady=20
                )

                ttk.Button(
                    buttons,
                    text="Apply",
                    command=(
                        apply_parameter_change
                    ),
                ).pack(
                    side="left",
                    padx=5,
                )

                ttk.Button(
                    buttons,
                    text="Cancel",
                    command=(
                        edit_window.destroy
                    ),
                ).pack(
                    side="left",
                    padx=5,
                )

                entry.focus_set()

            ttk.Button(
                parameter_window,
                text="Edit Selected Parameter",
                command=edit_parameter_value,
            ).pack(
                pady=(0, 10)
            )

        # --------------------------------------------------------
        # BOTTOM BUTTONS
        # --------------------------------------------------------

        buttons = ttk.Frame(
            window,
            padding=10,
        )

        buttons.pack(
            fill="x"
        )

        ttk.Button(
            buttons,
            text="Edit Field Parameter",
            command=edit_field_parameter,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=(
                lambda: (
                    window.destroy(),
                    self.open_field_editor(),
                )
            ),
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            buttons,
            text="Close",
            command=window.destroy,
        ).pack(
            side="right",
            padx=5,
        )
```

# ================================================================
# APPLICATION START
# ================================================================

def main():

    root = tk.Tk()

    app = KorgDrumKitEditorGUI(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()
