
# ===============================================================
# KORG PA300 DRUM KIT EDITOR
# #44 GUI APPLICATION
# ===============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from korg.set_parser import KorgSetParser


# ===============================================================
# MAIN APPLICATION
# ===============================================================

class KorgDrumKitEditorApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Korg PA300 Drum Kit Editor #44"
        )

        self.root.geometry(
            "1250x780"
        )

        self.root.minsize(
            1000,
            650
        )

        self.parser = None
        self.session = None
        self.current_file = None
        self.current_kit_index = None

        self._build_gui()

        self._set_editor_state(False)


    # ===========================================================
    # GUI
    # ===========================================================

    def _build_gui(self):

        main = ttk.Frame(
            self.root,
            padding=10
        )

        main.pack(
            fill=tk.BOTH,
            expand=True
        )


        # -------------------------------------------------------
        # TITLE
        # -------------------------------------------------------

        title = ttk.Label(
            main,
            text="KORG PA300 DRUM KIT EDITOR",
            font=(
                "TkDefaultFont",
                16,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            pady=(0, 8)
        )


        # -------------------------------------------------------
        # TOOLBAR
        # -------------------------------------------------------

        toolbar = ttk.Frame(main)

        toolbar.pack(
            fill=tk.X,
            pady=(0, 8)
        )


        self.open_button = ttk.Button(
            toolbar,
            text="Open SET",
            command=self._open_set_file
        )

        self.open_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.undo_button = ttk.Button(
            toolbar,
            text="Undo",
            command=self._undo
        )

        self.undo_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.redo_button = ttk.Button(
            toolbar,
            text="Redo",
            command=self._redo
        )

        self.redo_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.reset_button = ttk.Button(
            toolbar,
            text="Reset",
            command=self._reset
        )

        self.reset_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.history_button = ttk.Button(
            toolbar,
            text="History",
            command=self._show_history
        )

        self.history_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.validate_button = ttk.Button(
            toolbar,
            text="Validate",
            command=self._validate
        )

        self.validate_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.file_var = tk.StringVar(
            value="No SET file loaded"
        )


        file_label = ttk.Label(
            toolbar,
            textvariable=self.file_var
        )

        file_label.pack(
            side=tk.LEFT,
            padx=15
        )


        self.status_var = tk.StringVar(
            value="Ready"
        )


        status_label = ttk.Label(
            toolbar,
            textvariable=self.status_var
        )

        status_label.pack(
            side=tk.RIGHT
        )


        # -------------------------------------------------------
        # MAIN PANED WINDOW
        # -------------------------------------------------------

        pane = ttk.PanedWindow(
            main,
            orient=tk.HORIZONTAL
        )

        pane.pack(
            fill=tk.BOTH,
            expand=True
        )


        # =======================================================
        # LEFT PANEL
        # =======================================================

        left = ttk.Frame(
            pane,
            padding=5
        )

        pane.add(
            left,
            weight=1
        )


        ttk.Label(
            left,
            text="DRUM KITS",
            font=(
                "TkDefaultFont",
                11,
                "bold"
            )
        ).pack(
            anchor="w",
            pady=(0, 5)
        )


        self.kit_tree = ttk.Treeview(
            left,
            columns=(
                "index",
                "name",
                "confidence",
                "midi"
            ),
            show="headings"
        )


        self.kit_tree.heading(
            "index",
            text="#"
        )

        self.kit_tree.heading(
            "name",
            text="Name"
        )

        self.kit_tree.heading(
            "confidence",
            text="Confidence"
        )

        self.kit_tree.heading(
            "midi",
            text="MIDI"
        )


        self.kit_tree.column(
            "index",
            width=45,
            anchor="center"
        )

        self.kit_tree.column(
            "name",
            width=170
        )

        self.kit_tree.column(
            "confidence",
            width=100,
            anchor="center"
        )

        self.kit_tree.column(
            "midi",
            width=70,
            anchor="center"
        )


        kit_scroll = ttk.Scrollbar(
            left,
            orient=tk.VERTICAL,
            command=self.kit_tree.yview
        )


        self.kit_tree.configure(
            yscrollcommand=kit_scroll.set
        )


        self.kit_tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )


        kit_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        self.kit_tree.bind(
            "<<TreeviewSelect>>",
            self._on_kit_selected
        )


        # =======================================================
        # RIGHT PANEL
        # =======================================================

        right = ttk.Frame(
            pane,
            padding=5
        )

        pane.add(
            right,
            weight=4
        )


        # -------------------------------------------------------
        # SELECTED KIT
        # -------------------------------------------------------

        info = ttk.LabelFrame(
            right,
            text="Selected Drum Kit",
            padding=8
        )

        info.pack(
            fill=tk.X,
            pady=(0, 8)
        )


        self.kit_index_var = tk.StringVar(
            value="-"
        )

        self.kit_name_var = tk.StringVar(
            value="-"
        )

        self.kit_confidence_var = tk.StringVar(
            value="-"
        )

        self.kit_record_size_var = tk.StringVar(
            value="-"
        )


        ttk.Label(
            info,
            text="Index:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )


        ttk.Label(
            info,
            textvariable=self.kit_index_var
        ).grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Label(
            info,
            text="Name:"
        ).grid(
            row=0,
            column=2,
            padx=20
        )


        ttk.Label(
            info,
            textvariable=self.kit_name_var
        ).grid(
            row=0,
            column=3,
            padx=5
        )


        ttk.Label(
            info,
            text="Confidence:"
        ).grid(
            row=0,
            column=4,
            padx=20
        )


        ttk.Label(
            info,
            textvariable=self.kit_confidence_var
        ).grid(
            row=0,
            column=5,
            padx=5
        )


        ttk.Label(
            info,
            text="Record:"
        ).grid(
            row=0,
            column=6,
            padx=20
        )


        ttk.Label(
            info,
            textvariable=self.kit_record_size_var
        ).grid(
            row=0,
            column=7,
            padx=5
        )


        # =======================================================
        # PARAMETERS
        # =======================================================

        parameter_frame = ttk.LabelFrame(
            right,
            text="Drum Kit Parameters",
            padding=5
        )

        parameter_frame.pack(
            fill=tk.BOTH,
            expand=True
        )


        columns = (
            "offset",
            "hex_offset",
            "value",
            "hex",
            "type",
            "midi",
            "note",
            "confidence"
        )


        headings = {
            "offset": "Offset",
            "hex_offset": "Hex Offset",
            "value": "Value",
            "hex": "Hex",
            "type": "Type",
            "midi": "MIDI",
            "note": "Note",
            "confidence": "Confidence"
        }


        widths = {
            "offset": 65,
            "hex_offset": 85,
            "value": 65,
            "hex": 60,
            "type": 145,
            "midi": 65,
            "note": 85,
            "confidence": 95
        }


        self.parameter_tree = ttk.Treeview(
            parameter_frame,
            columns=columns,
            show="headings"
        )


        for column in columns:

            self.parameter_tree.heading(
                column,
                text=headings[column]
            )

            self.parameter_tree.column(
                column,
                width=widths[column],
                anchor="center"
            )


        parameter_scroll = ttk.Scrollbar(
            parameter_frame,
            orient=tk.VERTICAL,
            command=self.parameter_tree.yview
        )


        self.parameter_tree.configure(
            yscrollcommand=parameter_scroll.set
        )


        self.parameter_tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )


        parameter_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        self.parameter_tree.bind(
            "<<TreeviewSelect>>",
            self._on_parameter_selected
        )


        # =======================================================
        # EDIT PANEL
        # =======================================================

        edit_frame = ttk.LabelFrame(
            right,
            text="Edit",
            padding=8
        )

        edit_frame.pack(
            fill=tk.X,
            pady=(8, 0)
        )


        self.selected_offset_var = tk.StringVar(
            value="-"
        )

        self.selected_value_var = tk.StringVar(
            value=""
        )

        self.selected_midi_var = tk.StringVar(
            value=""
        )


        ttk.Label(
            edit_frame,
            text="Offset:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )


        ttk.Label(
            edit_frame,
            textvariable=self.selected_offset_var
        ).grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Label(
            edit_frame,
            text="Byte 0-255:"
        ).grid(
            row=0,
            column=2,
            padx=10
        )


        self.byte_entry = ttk.Entry(
            edit_frame,
            textvariable=self.selected_value_var,
            width=8
        )

        self.byte_entry.grid(
            row=0,
            column=3,
            padx=5
        )


        self.apply_byte_button = ttk.Button(
            edit_frame,
            text="Apply Byte",
            command=self._apply_byte
        )

        self.apply_byte_button.grid(
            row=0,
            column=4,
            padx=5
        )


        ttk.Label(
            edit_frame,
            text="MIDI 0-127:"
        ).grid(
            row=0,
            column=5,
            padx=10
        )


        self.midi_entry = ttk.Entry(
            edit_frame,
            textvariable=self.selected_midi_var,
            width=8
        )

        self.midi_entry.grid(
            row=0,
            column=6,
            padx=5
        )


        self.apply_midi_button = ttk.Button(
            edit_frame,
            text="Apply MIDI",
            command=self._apply_midi
        )

        self.apply_midi_button.grid(
            row=0,
            column=7,
            padx=5
        )


        # -------------------------------------------------------
        # WARNING
        # -------------------------------------------------------

        warning = ttk.Label(
            main,
            text=(
                "SAFE EDIT MODE: "
                "Original PCG/SET file is NOT modified. "
                "Write-back is disabled."
            )
        )

        warning.pack(
            anchor="w",
            pady=(6, 0)
        )


    # ===========================================================
    # EDITOR STATE
    # ===========================================================

    def _set_editor_state(self, enabled):

        state = (
            tk.NORMAL
            if enabled
            else tk.DISABLED
        )

        self.undo_button.configure(
            state=state
        )

        self.redo_button.configure(
            state=state
        )

        self.reset_button.configure(
            state=state
        )

        self.history_button.configure(
            state=state
        )

        self.validate_button.configure(
            state=state
        )

        self.apply_byte_button.configure(
            state=state
        )

        self.apply_midi_button.configure(
            state=state
        )


    # ===========================================================
    # OPEN FILE
    # ===========================================================

    def _open_set_file(self):

        path = filedialog.askopenfilename(
            title="Open Korg SET / PCG file",
            filetypes=[
                (
                    "Korg files",
                    "*.SET *.set *.PCG *.pcg"
                ),
                (
                    "All files",
                    "*.*"
                )
            ]
        )

        if not path:
            return

        self._load_file(path)


    def _load_file(self, path):

        try:

            parser = KorgSetParser(path)

        except Exception as error:

            messagebox.showerror(
                "Load error",
                (
                    "Could not create parser.\n\n"
                    f"{error}"
                )
            )

            return


        self.parser = parser

        self.current_file = path

        self.file_var.set(path)

        self.current_kit_index = None

        self.session = None


        # -------------------------------------------------------
        # Try to create editor session.
        # -------------------------------------------------------

        try:

            self.session = (
                parser.create_editor_session()
            )

        except AttributeError:

            messagebox.showwarning(
                "Editor interface",
                (
                    "The current parser does not expose "
                    "create_editor_session().\n\n"
                    "The GUI was loaded, but editor "
                    "functions are disabled."
                )
            )

            self._set_editor_state(False)

            self.status_var.set(
                "File loaded, editor interface unavailable."
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Session error",
                str(error)
            )

            return


        self._set_editor_state(True)

        self._refresh_kit_list()

        self.status_var.set(
            "SET/PCG loaded."
        )


    # ===========================================================
    # KIT LIST
    # ===========================================================

    def _refresh_kit_list(self):

        for item in self.kit_tree.get_children():

            self.kit_tree.delete(item)


        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            kits = (
                self.parser.build_editor_kit_list(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showwarning(
                "Editor interface",
                (
                    "build_editor_kit_list() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Editor error",
                str(error)
            )

            return


        for kit in kits:

            self.kit_tree.insert(
                "",
                tk.END,
                values=(
                    kit.get(
                        "kit_index",
                        "-"
                    ),
                    kit.get(
                        "kit_name",
                        "-"
                    ) or "-",
                    kit.get(
                        "confidence",
                        "-"
                    ) or "-",
                    kit.get(
                        "confirmed_midi_count",
                        0
                    )
                )
            )


        children = (
            self.kit_tree.get_children()
        )


        if children:

            self.kit_tree.selection_set(
                children[0]
            )

            self.kit_tree.focus(
                children[0]
            )


    # ===========================================================
    # KIT SELECTION
    # ===========================================================

    def _on_kit_selected(self, event=None):

        selection = (
            self.kit_tree.selection()
        )

        if not selection:
            return


        item = self.kit_tree.item(
            selection[0]
        )


        values = item.get(
            "values",
            []
        )


        if not values:
            return


        try:

            self.current_kit_index = int(
                values[0]
            )

        except (
            TypeError,
            ValueError
        ):

            return


        self._refresh_selected_kit()


    # ===========================================================
    # SELECTED KIT
    # ===========================================================

    def _refresh_selected_kit(self):

        if (
            self.parser is None
            or self.session is None
            or self.current_kit_index is None
        ):
            return


        try:

            data = (
                self.parser.build_editor_selected_kit_data(
                    self.session,
                    self.current_kit_index
                )
            )

        except AttributeError:

            return

        except Exception as error:

            messagebox.showerror(
                "Kit error",
                str(error)
            )

            return


        self.kit_index_var.set(
            str(
                data.get(
                    "kit_index",
                    "-"
                )
            )
        )


        self.kit_name_var.set(
            data.get(
                "kit_name",
                "-"
            ) or "-"
        )


        reconstruction = data.get(
            "reconstruction",
            {}
        )


        self.kit_confidence_var.set(
            str(
                reconstruction.get(
                    "confidence",
                    "-"
                )
            )
        )


        self.kit_record_size_var.set(
            str(
                data.get(
                    "record_size",
                    "-"
                )
            )
        )


        self._refresh_parameter_table(
            data.get(
                "parameters",
                []
            )
        )


        self._update_status()


    # ===========================================================
    # PARAMETER TABLE
    # ===========================================================

    def _refresh_parameter_table(
        self,
        parameters
    ):

        for item in (
            self.parameter_tree.get_children()
        ):

            self.parameter_tree.delete(item)


        for parameter in parameters:

            self.parameter_tree.insert(
                "",
                tk.END,
                values=(
                    parameter.get(
                        "offset",
                        ""
                    ),
                    parameter.get(
                        "hex_offset",
                        ""
                    ),
                    parameter.get(
                        "value",
                        ""
                    ),
                    parameter.get(
                        "hex",
                        ""
                    ),
                    parameter.get(
                        "editor_type",
                        ""
                    ),
                    parameter.get(
                        "midi_note",
                        ""
                    ),
                    parameter.get(
                        "midi_note_name",
                        ""
                    ) or "",
                    parameter.get(
                        "confidence",
                        ""
                    ) or ""
                )
            )


    # ===========================================================
    # PARAMETER SELECTION
    # ===========================================================

    def _on_parameter_selected(
        self,
        event=None
    ):

        selection = (
            self.parameter_tree.selection()
        )

        if not selection:
            return


        item = self.parameter_tree.item(
            selection[0]
        )


        values = item.get(
            "values",
            []
        )


        if len(values) < 3:
            return


        self.selected_offset_var.set(
            str(values[0])
        )


        self.selected_value_var.set(
            str(values[2])
        )


        if len(values) > 5:

            self.selected_midi_var.set(
                str(values[5] or "")
            )


    # ===========================================================
    # APPLY BYTE
    # ===========================================================

    def _apply_byte(self):

        if (
            self.parser is None
            or self.session is None
            or self.current_kit_index is None
        ):
            return


        try:

            offset = int(
                self.selected_offset_var.get()
            )

            value = int(
                self.selected_value_var.get()
            )

        except ValueError:

            messagebox.showerror(
                "Invalid value",
                "Offset and byte must be integers."
            )

            return


        if value < 0 or value > 255:

            messagebox.showerror(
                "Invalid byte",
                "Byte must be between 0 and 255."
            )

            return


        try:

            result = (
                self.parser.edit_editor_parameter(
                    self.session,
                    self.current_kit_index,
                    offset,
                    value
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Editor error",
                (
                    "edit_editor_parameter() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Edit error",
                str(error)
            )

            return


        if not result.get(
            "success",
            False
        ):

            messagebox.showerror(
                "Edit failed",
                "The byte could not be changed."
            )

            return


        self._refresh_selected_kit()

        self.status_var.set(
            "Byte changed in memory."
        )


    # ===========================================================
    # APPLY MIDI
    # ===========================================================

    def _apply_midi(self):

        if (
            self.parser is None
            or self.session is None
            or self.current_kit_index is None
        ):
            return


        try:

            offset = int(
                self.selected_offset_var.get()
            )

            midi_value = int(
                self.selected_midi_var.get()
            )

        except ValueError:

            messagebox.showerror(
                "Invalid MIDI",
                "Offset and MIDI must be integers."
            )

            return


        if midi_value < 0 or midi_value > 127:

            messagebox.showerror(
                "Invalid MIDI",
                "MIDI value must be between 0 and 127."
            )

            return


        try:

            result = (
                self.parser.edit_editor_midi_mapping(
                    self.session,
                    self.current_kit_index,
                    offset,
                    midi_value
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Editor error",
                (
                    "edit_editor_midi_mapping() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "MIDI edit error",
                str(error)
            )

            return


        if not result.get(
            "success",
            False
        ):

            messagebox.showerror(
                "MIDI edit failed",
                "The MIDI mapping could not be changed."
            )

            return


        self._refresh_selected_kit()

        self.status_var.set(
            "MIDI mapping changed."
        )


    # ===========================================================
    # UNDO
    # ===========================================================

    def _undo(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            result = (
                self.parser.undo_editor_change(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Undo error",
                (
                    "undo_editor_change() "
                    "is not available."
                )
            )

            return


        if not result.get(
            "success",
            False
        ):

            self.status_var.set(
                "Nothing to undo."
            )

            return


        self._refresh_selected_kit()

        self._refresh_kit_list()

        self._update_status()

        self.status_var.set(
            "Undo completed."
        )


    # ===========================================================
    # REDO
    # ===========================================================

    def _redo(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            result = (
                self.parser.redo_editor_change(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Redo error",
                (
                    "redo_editor_change() "
                    "is not available."
                )
            )

            return


        if not result.get(
            "success",
            False
        ):

            self.status_var.set(
                "Nothing to redo."
            )

            return


        self._refresh_selected_kit()

        self._refresh_kit_list()

        self._update_status()

        self.status_var.set(
            "Redo completed."
        )


    # ===========================================================
    # RESET
    # ===========================================================

    def _reset(self):

        if self.parser is None:
            return


        answer = messagebox.askyesno(
            "Reset",
            (
                "Discard all editor changes?\n\n"
                "Original SET/PCG file will remain unchanged."
            )
        )


        if not answer:
            return


        try:

            result = (
                self.parser.reset_drum_kit_edits()
            )

        except AttributeError:

            messagebox.showerror(
                "Reset error",
                (
                    "reset_drum_kit_edits() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Reset error",
                str(error)
            )

            return


        if not result.get(
            "success",
            False
        ):

            messagebox.showerror(
                "Reset failed",
                "Could not reset editor."
            )

            return


        self.session = result.get(
            "model",
            self.session
        )


        self.current_kit_index = None

        self._refresh_kit_list()

        self._update_status()

        self.status_var.set(
            "All changes reset."
        )


    # ===========================================================
    # HISTORY
    # ===========================================================

    def _show_history(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            history = (
                self.parser.get_editor_change_history(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "History error",
                (
                    "get_editor_change_history() "
                    "is not available."
                )
            )

            return


        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Change History"
        )

        window.geometry(
            "750x420"
        )


        frame = ttk.Frame(
            window,
            padding=10
        )

        frame.pack(
            fill=tk.BOTH,
            expand=True
        )


        tree = ttk.Treeview(
            frame,
            columns=(
                "kit",
                "offset",
                "old",
                "new"
            ),
            show="headings"
        )


        tree.heading(
            "kit",
            text="Kit"
        )

        tree.heading(
            "offset",
            text="Offset"
        )

        tree.heading(
            "old",
            text="Old"
        )

        tree.heading(
            "new",
            text="New"
        )


        tree.column(
            "kit",
            width=70,
            anchor="center"
        )

        tree.column(
            "offset",
            width=100,
            anchor="center"
        )

        tree.column(
            "old",
            width=100,
            anchor="center"
        )

        tree.column(
            "new",
            width=100,
            anchor="center"
        )


        scroll = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=tree.yview
        )


        tree.configure(
            yscrollcommand=scroll.set
        )


        tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )


        scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        for change in history:

            tree.insert(
                "",
                tk.END,
                values=(
                    change.get(
                        "kit_index",
                        ""
                    ),
                    change.get(
                        "relative_offset",
                        ""
                    ),
                    change.get(
                        "old_hex",
                        ""
                    ),
                    change.get(
                        "new_hex",
                        ""
                    )
                )
            )


    # ===========================================================
    # VALIDATE
    # ===========================================================

    def _validate(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            result = (
                self.parser.validate_editor_session(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Validation error",
                (
                    "validate_editor_session() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Validation error",
                str(error)
            )

            return


        if result.get(
            "valid",
            False
        ):

            messagebox.showinfo(
                "Validation successful",
                (
                    "Editor model is valid.\n\n"
                    f"Changes: "
                    f"{result.get('change_count', 0)}\n"
                    f"Undo available: "
                    f"{result.get('undo_available', False)}\n"
                    f"Redo available: "
                    f"{result.get('redo_available', False)}\n\n"
                    "Original file modified: NO\n"
                    "Write-back: DISABLED"
                )
            )

            self.status_var.set(
                "Validation successful."
            )

        else:

            errors = result.get(
                "errors",
                []
            )


            messagebox.showerror(
                "Validation failed",
                "\n".join(
                    str(error)
                    for error in errors
                )
            )


    # ===========================================================
    # STATUS
    # ===========================================================

    def _update_status(self):

        if (
            self.parser is None
            or self.session is None
        ):

            self.status_var.set(
                "Ready"
            )

            return


        try:

            status = (
                self.parser.get_editor_session_status(
                    self.session
                )
            )

        except AttributeError:

            return

        except Exception:

            return


        self.undo_button.configure(
            state=(
                tk.NORMAL
                if status.get(
                    "undo_available",
                    False
                )
                else tk.DISABLED
            )
        )


        self.redo_button.configure(
            state=(
                tk.NORMAL
                if status.get(
                    "redo_available",
                    False
                )
                else tk.DISABLED
            )
        )


        if status.get(
            "dirty",
            False
        ):

            self.status_var.set(
                (
                    "Modified in memory | "
                    f"Changes: "
                    f"{status.get('change_count', 0)}"
                )
            )

        else:

            self.status_var.set(
                "Loaded | No changes"
            )


# ===============================================================
# APPLICATION START
# ===============================================================

def main():

    root = tk.Tk()

    KorgDrumKitEditorApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()


# ===============================================================
# KORG PA300 DRUM KIT EDITOR
# #44 GUI APPLICATION
# ===============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from korg.set_parser import KorgSetParser


# ===============================================================
# MAIN APPLICATION
# ===============================================================

class KorgDrumKitEditorApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Korg PA300 Drum Kit Editor #44"
        )

        self.root.geometry(
            "1250x780"
        )

        self.root.minsize(
            1000,
            650
        )

        self.parser = None
        self.session = None
        self.current_file = None
        self.current_kit_index = None

        self._build_gui()

        self._set_editor_state(False)


    # ===========================================================
    # GUI
    # ===========================================================

    def _build_gui(self):

        main = ttk.Frame(
            self.root,
            padding=10
        )

        main.pack(
            fill=tk.BOTH,
            expand=True
        )


        # -------------------------------------------------------
        # TITLE
        # -------------------------------------------------------

        title = ttk.Label(
            main,
            text="KORG PA300 DRUM KIT EDITOR",
            font=(
                "TkDefaultFont",
                16,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            pady=(0, 8)
        )


        # -------------------------------------------------------
        # TOOLBAR
        # -------------------------------------------------------

        toolbar = ttk.Frame(main)

        toolbar.pack(
            fill=tk.X,
            pady=(0, 8)
        )


        self.open_button = ttk.Button(
            toolbar,
            text="Open SET",
            command=self._open_set_file
        )

        self.open_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.undo_button = ttk.Button(
            toolbar,
            text="Undo",
            command=self._undo
        )

        self.undo_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.redo_button = ttk.Button(
            toolbar,
            text="Redo",
            command=self._redo
        )

        self.redo_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.reset_button = ttk.Button(
            toolbar,
            text="Reset",
            command=self._reset
        )

        self.reset_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.history_button = ttk.Button(
            toolbar,
            text="History",
            command=self._show_history
        )

        self.history_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.validate_button = ttk.Button(
            toolbar,
            text="Validate",
            command=self._validate
        )

        self.validate_button.pack(
            side=tk.LEFT,
            padx=3
        )


        self.file_var = tk.StringVar(
            value="No SET file loaded"
        )


        file_label = ttk.Label(
            toolbar,
            textvariable=self.file_var
        )

        file_label.pack(
            side=tk.LEFT,
            padx=15
        )


        self.status_var = tk.StringVar(
            value="Ready"
        )


        status_label = ttk.Label(
            toolbar,
            textvariable=self.status_var
        )

        status_label.pack(
            side=tk.RIGHT
        )


        # -------------------------------------------------------
        # MAIN PANED WINDOW
        # -------------------------------------------------------

        pane = ttk.PanedWindow(
            main,
            orient=tk.HORIZONTAL
        )

        pane.pack(
            fill=tk.BOTH,
            expand=True
        )


        # =======================================================
        # LEFT PANEL
        # =======================================================

        left = ttk.Frame(
            pane,
            padding=5
        )

        pane.add(
            left,
            weight=1
        )


        ttk.Label(
            left,
            text="DRUM KITS",
            font=(
                "TkDefaultFont",
                11,
                "bold"
            )
        ).pack(
            anchor="w",
            pady=(0, 5)
        )


        self.kit_tree = ttk.Treeview(
            left,
            columns=(
                "index",
                "name",
                "confidence",
                "midi"
            ),
            show="headings"
        )


        self.kit_tree.heading(
            "index",
            text="#"
        )

        self.kit_tree.heading(
            "name",
            text="Name"
        )

        self.kit_tree.heading(
            "confidence",
            text="Confidence"
        )

        self.kit_tree.heading(
            "midi",
            text="MIDI"
        )


        self.kit_tree.column(
            "index",
            width=45,
            anchor="center"
        )

        self.kit_tree.column(
            "name",
            width=170
        )

        self.kit_tree.column(
            "confidence",
            width=100,
            anchor="center"
        )

        self.kit_tree.column(
            "midi",
            width=70,
            anchor="center"
        )


        kit_scroll = ttk.Scrollbar(
            left,
            orient=tk.VERTICAL,
            command=self.kit_tree.yview
        )


        self.kit_tree.configure(
            yscrollcommand=kit_scroll.set
        )


        self.kit_tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )


        kit_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        self.kit_tree.bind(
            "<<TreeviewSelect>>",
            self._on_kit_selected
        )


        # =======================================================
        # RIGHT PANEL
        # =======================================================

        right = ttk.Frame(
            pane,
            padding=5
        )

        pane.add(
            right,
            weight=4
        )


        # -------------------------------------------------------
        # SELECTED KIT
        # -------------------------------------------------------

        info = ttk.LabelFrame(
            right,
            text="Selected Drum Kit",
            padding=8
        )

        info.pack(
            fill=tk.X,
            pady=(0, 8)
        )


        self.kit_index_var = tk.StringVar(
            value="-"
        )

        self.kit_name_var = tk.StringVar(
            value="-"
        )

        self.kit_confidence_var = tk.StringVar(
            value="-"
        )

        self.kit_record_size_var = tk.StringVar(
            value="-"
        )


        ttk.Label(
            info,
            text="Index:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )


        ttk.Label(
            info,
            textvariable=self.kit_index_var
        ).grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Label(
            info,
            text="Name:"
        ).grid(
            row=0,
            column=2,
            padx=20
        )


        ttk.Label(
            info,
            textvariable=self.kit_name_var
        ).grid(
            row=0,
            column=3,
            padx=5
        )


        ttk.Label(
            info,
            text="Confidence:"
        ).grid(
            row=0,
            column=4,
            padx=20
        )


        ttk.Label(
            info,
            textvariable=self.kit_confidence_var
        ).grid(
            row=0,
            column=5,
            padx=5
        )


        ttk.Label(
            info,
            text="Record:"
        ).grid(
            row=0,
            column=6,
            padx=20
        )


        ttk.Label(
            info,
            textvariable=self.kit_record_size_var
        ).grid(
            row=0,
            column=7,
            padx=5
        )


        # =======================================================
        # PARAMETERS
        # =======================================================

        parameter_frame = ttk.LabelFrame(
            right,
            text="Drum Kit Parameters",
            padding=5
        )

        parameter_frame.pack(
            fill=tk.BOTH,
            expand=True
        )


        columns = (
            "offset",
            "hex_offset",
            "value",
            "hex",
            "type",
            "midi",
            "note",
            "confidence"
        )


        headings = {
            "offset": "Offset",
            "hex_offset": "Hex Offset",
            "value": "Value",
            "hex": "Hex",
            "type": "Type",
            "midi": "MIDI",
            "note": "Note",
            "confidence": "Confidence"
        }


        widths = {
            "offset": 65,
            "hex_offset": 85,
            "value": 65,
            "hex": 60,
            "type": 145,
            "midi": 65,
            "note": 85,
            "confidence": 95
        }


        self.parameter_tree = ttk.Treeview(
            parameter_frame,
            columns=columns,
            show="headings"
        )


        for column in columns:

            self.parameter_tree.heading(
                column,
                text=headings[column]
            )

            self.parameter_tree.column(
                column,
                width=widths[column],
                anchor="center"
            )


        parameter_scroll = ttk.Scrollbar(
            parameter_frame,
            orient=tk.VERTICAL,
            command=self.parameter_tree.yview
        )


        self.parameter_tree.configure(
            yscrollcommand=parameter_scroll.set
        )


        self.parameter_tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )


        parameter_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        self.parameter_tree.bind(
            "<<TreeviewSelect>>",
            self._on_parameter_selected
        )


        # =======================================================
        # EDIT PANEL
        # =======================================================

        edit_frame = ttk.LabelFrame(
            right,
            text="Edit",
            padding=8
        )

        edit_frame.pack(
            fill=tk.X,
            pady=(8, 0)
        )


        self.selected_offset_var = tk.StringVar(
            value="-"
        )

        self.selected_value_var = tk.StringVar(
            value=""
        )

        self.selected_midi_var = tk.StringVar(
            value=""
        )


        ttk.Label(
            edit_frame,
            text="Offset:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )


        ttk.Label(
            edit_frame,
            textvariable=self.selected_offset_var
        ).grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Label(
            edit_frame,
            text="Byte 0-255:"
        ).grid(
            row=0,
            column=2,
            padx=10
        )


        self.byte_entry = ttk.Entry(
            edit_frame,
            textvariable=self.selected_value_var,
            width=8
        )

        self.byte_entry.grid(
            row=0,
            column=3,
            padx=5
        )


        self.apply_byte_button = ttk.Button(
            edit_frame,
            text="Apply Byte",
            command=self._apply_byte
        )

        self.apply_byte_button.grid(
            row=0,
            column=4,
            padx=5
        )


        ttk.Label(
            edit_frame,
            text="MIDI 0-127:"
        ).grid(
            row=0,
            column=5,
            padx=10
        )


        self.midi_entry = ttk.Entry(
            edit_frame,
            textvariable=self.selected_midi_var,
            width=8
        )

        self.midi_entry.grid(
            row=0,
            column=6,
            padx=5
        )


        self.apply_midi_button = ttk.Button(
            edit_frame,
            text="Apply MIDI",
            command=self._apply_midi
        )

        self.apply_midi_button.grid(
            row=0,
            column=7,
            padx=5
        )


        # -------------------------------------------------------
        # WARNING
        # -------------------------------------------------------

        warning = ttk.Label(
            main,
            text=(
                "SAFE EDIT MODE: "
                "Original PCG/SET file is NOT modified. "
                "Write-back is disabled."
            )
        )

        warning.pack(
            anchor="w",
            pady=(6, 0)
        )


    # ===========================================================
    # EDITOR STATE
    # ===========================================================

    def _set_editor_state(self, enabled):

        state = (
            tk.NORMAL
            if enabled
            else tk.DISABLED
        )

        self.undo_button.configure(
            state=state
        )

        self.redo_button.configure(
            state=state
        )

        self.reset_button.configure(
            state=state
        )

        self.history_button.configure(
            state=state
        )

        self.validate_button.configure(
            state=state
        )

        self.apply_byte_button.configure(
            state=state
        )

        self.apply_midi_button.configure(
            state=state
        )


    # ===========================================================
    # OPEN FILE
    # ===========================================================

    def _open_set_file(self):

        path = filedialog.askopenfilename(
            title="Open Korg SET / PCG file",
            filetypes=[
                (
                    "Korg files",
                    "*.SET *.set *.PCG *.pcg"
                ),
                (
                    "All files",
                    "*.*"
                )
            ]
        )

        if not path:
            return

        self._load_file(path)


    def _load_file(self, path):

        try:

            parser = KorgSetParser(path)

        except Exception as error:

            messagebox.showerror(
                "Load error",
                (
                    "Could not create parser.\n\n"
                    f"{error}"
                )
            )

            return


        self.parser = parser

        self.current_file = path

        self.file_var.set(path)

        self.current_kit_index = None

        self.session = None


        # -------------------------------------------------------
        # Try to create editor session.
        # -------------------------------------------------------

        try:

            self.session = (
                parser.create_editor_session()
            )

        except AttributeError:

            messagebox.showwarning(
                "Editor interface",
                (
                    "The current parser does not expose "
                    "create_editor_session().\n\n"
                    "The GUI was loaded, but editor "
                    "functions are disabled."
                )
            )

            self._set_editor_state(False)

            self.status_var.set(
                "File loaded, editor interface unavailable."
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Session error",
                str(error)
            )

            return


        self._set_editor_state(True)

        self._refresh_kit_list()

        self.status_var.set(
            "SET/PCG loaded."
        )


    # ===========================================================
    # KIT LIST
    # ===========================================================

    def _refresh_kit_list(self):

        for item in self.kit_tree.get_children():

            self.kit_tree.delete(item)


        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            kits = (
                self.parser.build_editor_kit_list(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showwarning(
                "Editor interface",
                (
                    "build_editor_kit_list() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Editor error",
                str(error)
            )

            return


        for kit in kits:

            self.kit_tree.insert(
                "",
                tk.END,
                values=(
                    kit.get(
                        "kit_index",
                        "-"
                    ),
                    kit.get(
                        "kit_name",
                        "-"
                    ) or "-",
                    kit.get(
                        "confidence",
                        "-"
                    ) or "-",
                    kit.get(
                        "confirmed_midi_count",
                        0
                    )
                )
            )


        children = (
            self.kit_tree.get_children()
        )


        if children:

            self.kit_tree.selection_set(
                children[0]
            )

            self.kit_tree.focus(
                children[0]
            )


    # ===========================================================
    # KIT SELECTION
    # ===========================================================

    def _on_kit_selected(self, event=None):

        selection = (
            self.kit_tree.selection()
        )

        if not selection:
            return


        item = self.kit_tree.item(
            selection[0]
        )


        values = item.get(
            "values",
            []
        )


        if not values:
            return


        try:

            self.current_kit_index = int(
                values[0]
            )

        except (
            TypeError,
            ValueError
        ):

            return


        self._refresh_selected_kit()


    # ===========================================================
    # SELECTED KIT
    # ===========================================================

    def _refresh_selected_kit(self):

        if (
            self.parser is None
            or self.session is None
            or self.current_kit_index is None
        ):
            return


        try:

            data = (
                self.parser.build_editor_selected_kit_data(
                    self.session,
                    self.current_kit_index
                )
            )

        except AttributeError:

            return

        except Exception as error:

            messagebox.showerror(
                "Kit error",
                str(error)
            )

            return


        self.kit_index_var.set(
            str(
                data.get(
                    "kit_index",
                    "-"
                )
            )
        )


        self.kit_name_var.set(
            data.get(
                "kit_name",
                "-"
            ) or "-"
        )


        reconstruction = data.get(
            "reconstruction",
            {}
        )


        self.kit_confidence_var.set(
            str(
                reconstruction.get(
                    "confidence",
                    "-"
                )
            )
        )


        self.kit_record_size_var.set(
            str(
                data.get(
                    "record_size",
                    "-"
                )
            )
        )


        self._refresh_parameter_table(
            data.get(
                "parameters",
                []
            )
        )


        self._update_status()


    # ===========================================================
    # PARAMETER TABLE
    # ===========================================================

    def _refresh_parameter_table(
        self,
        parameters
    ):

        for item in (
            self.parameter_tree.get_children()
        ):

            self.parameter_tree.delete(item)


        for parameter in parameters:

            self.parameter_tree.insert(
                "",
                tk.END,
                values=(
                    parameter.get(
                        "offset",
                        ""
                    ),
                    parameter.get(
                        "hex_offset",
                        ""
                    ),
                    parameter.get(
                        "value",
                        ""
                    ),
                    parameter.get(
                        "hex",
                        ""
                    ),
                    parameter.get(
                        "editor_type",
                        ""
                    ),
                    parameter.get(
                        "midi_note",
                        ""
                    ),
                    parameter.get(
                        "midi_note_name",
                        ""
                    ) or "",
                    parameter.get(
                        "confidence",
                        ""
                    ) or ""
                )
            )


    # ===========================================================
    # PARAMETER SELECTION
    # ===========================================================

    def _on_parameter_selected(
        self,
        event=None
    ):

        selection = (
            self.parameter_tree.selection()
        )

        if not selection:
            return


        item = self.parameter_tree.item(
            selection[0]
        )


        values = item.get(
            "values",
            []
        )


        if len(values) < 3:
            return


        self.selected_offset_var.set(
            str(values[0])
        )


        self.selected_value_var.set(
            str(values[2])
        )


        if len(values) > 5:

            self.selected_midi_var.set(
                str(values[5] or "")
            )


    # ===========================================================
    # APPLY BYTE
    # ===========================================================

    def _apply_byte(self):

        if (
            self.parser is None
            or self.session is None
            or self.current_kit_index is None
        ):
            return


        try:

            offset = int(
                self.selected_offset_var.get()
            )

            value = int(
                self.selected_value_var.get()
            )

        except ValueError:

            messagebox.showerror(
                "Invalid value",
                "Offset and byte must be integers."
            )

            return


        if value < 0 or value > 255:

            messagebox.showerror(
                "Invalid byte",
                "Byte must be between 0 and 255."
            )

            return


        try:

            result = (
                self.parser.edit_editor_parameter(
                    self.session,
                    self.current_kit_index,
                    offset,
                    value
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Editor error",
                (
                    "edit_editor_parameter() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Edit error",
                str(error)
            )

            return


        if not result.get(
            "success",
            False
        ):

            messagebox.showerror(
                "Edit failed",
                "The byte could not be changed."
            )

            return


        self._refresh_selected_kit()

        self.status_var.set(
            "Byte changed in memory."
        )


    # ===========================================================
    # APPLY MIDI
    # ===========================================================

    def _apply_midi(self):

        if (
            self.parser is None
            or self.session is None
            or self.current_kit_index is None
        ):
            return


        try:

            offset = int(
                self.selected_offset_var.get()
            )

            midi_value = int(
                self.selected_midi_var.get()
            )

        except ValueError:

            messagebox.showerror(
                "Invalid MIDI",
                "Offset and MIDI must be integers."
            )

            return


        if midi_value < 0 or midi_value > 127:

            messagebox.showerror(
                "Invalid MIDI",
                "MIDI value must be between 0 and 127."
            )

            return


        try:

            result = (
                self.parser.edit_editor_midi_mapping(
                    self.session,
                    self.current_kit_index,
                    offset,
                    midi_value
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Editor error",
                (
                    "edit_editor_midi_mapping() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "MIDI edit error",
                str(error)
            )

            return


        if not result.get(
            "success",
            False
        ):

            messagebox.showerror(
                "MIDI edit failed",
                "The MIDI mapping could not be changed."
            )

            return


        self._refresh_selected_kit()

        self.status_var.set(
            "MIDI mapping changed."
        )


    # ===========================================================
    # UNDO
    # ===========================================================

    def _undo(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            result = (
                self.parser.undo_editor_change(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Undo error",
                (
                    "undo_editor_change() "
                    "is not available."
                )
            )

            return


        if not result.get(
            "success",
            False
        ):

            self.status_var.set(
                "Nothing to undo."
            )

            return


        self._refresh_selected_kit()

        self._refresh_kit_list()

        self._update_status()

        self.status_var.set(
            "Undo completed."
        )


    # ===========================================================
    # REDO
    # ===========================================================

    def _redo(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            result = (
                self.parser.redo_editor_change(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Redo error",
                (
                    "redo_editor_change() "
                    "is not available."
                )
            )

            return


        if not result.get(
            "success",
            False
        ):

            self.status_var.set(
                "Nothing to redo."
            )

            return


        self._refresh_selected_kit()

        self._refresh_kit_list()

        self._update_status()

        self.status_var.set(
            "Redo completed."
        )


    # ===========================================================
    # RESET
    # ===========================================================

    def _reset(self):

        if self.parser is None:
            return


        answer = messagebox.askyesno(
            "Reset",
            (
                "Discard all editor changes?\n\n"
                "Original SET/PCG file will remain unchanged."
            )
        )


        if not answer:
            return


        try:

            result = (
                self.parser.reset_drum_kit_edits()
            )

        except AttributeError:

            messagebox.showerror(
                "Reset error",
                (
                    "reset_drum_kit_edits() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Reset error",
                str(error)
            )

            return


        if not result.get(
            "success",
            False
        ):

            messagebox.showerror(
                "Reset failed",
                "Could not reset editor."
            )

            return


        self.session = result.get(
            "model",
            self.session
        )


        self.current_kit_index = None

        self._refresh_kit_list()

        self._update_status()

        self.status_var.set(
            "All changes reset."
        )


    # ===========================================================
    # HISTORY
    # ===========================================================

    def _show_history(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            history = (
                self.parser.get_editor_change_history(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "History error",
                (
                    "get_editor_change_history() "
                    "is not available."
                )
            )

            return


        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Change History"
        )

        window.geometry(
            "750x420"
        )


        frame = ttk.Frame(
            window,
            padding=10
        )

        frame.pack(
            fill=tk.BOTH,
            expand=True
        )


        tree = ttk.Treeview(
            frame,
            columns=(
                "kit",
                "offset",
                "old",
                "new"
            ),
            show="headings"
        )


        tree.heading(
            "kit",
            text="Kit"
        )

        tree.heading(
            "offset",
            text="Offset"
        )

        tree.heading(
            "old",
            text="Old"
        )

        tree.heading(
            "new",
            text="New"
        )


        tree.column(
            "kit",
            width=70,
            anchor="center"
        )

        tree.column(
            "offset",
            width=100,
            anchor="center"
        )

        tree.column(
            "old",
            width=100,
            anchor="center"
        )

        tree.column(
            "new",
            width=100,
            anchor="center"
        )


        scroll = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=tree.yview
        )


        tree.configure(
            yscrollcommand=scroll.set
        )


        tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )


        scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        for change in history:

            tree.insert(
                "",
                tk.END,
                values=(
                    change.get(
                        "kit_index",
                        ""
                    ),
                    change.get(
                        "relative_offset",
                        ""
                    ),
                    change.get(
                        "old_hex",
                        ""
                    ),
                    change.get(
                        "new_hex",
                        ""
                    )
                )
            )


    # ===========================================================
    # VALIDATE
    # ===========================================================

    def _validate(self):

        if (
            self.parser is None
            or self.session is None
        ):
            return


        try:

            result = (
                self.parser.validate_editor_session(
                    self.session
                )
            )

        except AttributeError:

            messagebox.showerror(
                "Validation error",
                (
                    "validate_editor_session() "
                    "is not available."
                )
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Validation error",
                str(error)
            )

            return


        if result.get(
            "valid",
            False
        ):

            messagebox.showinfo(
                "Validation successful",
                (
                    "Editor model is valid.\n\n"
                    f"Changes: "
                    f"{result.get('change_count', 0)}\n"
                    f"Undo available: "
                    f"{result.get('undo_available', False)}\n"
                    f"Redo available: "
                    f"{result.get('redo_available', False)}\n\n"
                    "Original file modified: NO\n"
                    "Write-back: DISABLED"
                )
            )

            self.status_var.set(
                "Validation successful."
            )

        else:

            errors = result.get(
                "errors",
                []
            )


            messagebox.showerror(
                "Validation failed",
                "\n".join(
                    str(error)
                    for error in errors
                )
            )


    # ===========================================================
    # STATUS
    # ===========================================================

    def _update_status(self):

        if (
            self.parser is None
            or self.session is None
        ):

            self.status_var.set(
                "Ready"
            )

            return


        try:

            status = (
                self.parser.get_editor_session_status(
                    self.session
                )
            )

        except AttributeError:

            return

        except Exception:

            return


        self.undo_button.configure(
            state=(
                tk.NORMAL
                if status.get(
                    "undo_available",
                    False
                )
                else tk.DISABLED
            )
        )


        self.redo_button.configure(
            state=(
                tk.NORMAL
                if status.get(
                    "redo_available",
                    False
                )
                else tk.DISABLED
            )
        )


        if status.get(
            "dirty",
            False
        ):

            self.status_var.set(
                (
                    "Modified in memory | "
                    f"Changes: "
                    f"{status.get('change_count', 0)}"
                )
            )

        else:

            self.status_var.set(
                "Loaded | No changes"
            )


# ===============================================================
# APPLICATION START
# ===============================================================

def main():

    root = tk.Tk()

    KorgDrumKitEditorApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()

