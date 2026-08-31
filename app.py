
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class KorgDrumKitEditorGUI:
    """
    #46 MIDI Mapping Editor GUI

    GUI sloj za postojeći KorgDrumKitEditor parser.

    VAŽNO:
    - ne mijenja originalni SET/PCG fajl
    - koristi postojeći parser/session sistem kada je dostupan
    - GUI je pripremljen za MIDI mapping pregled i uređivanje
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Korg Drum Kit Editor")
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)

        self.session = None
        self.current_kit_index = None
        self.mapping_data = []

        self.create_widgets()

    # ============================================================
    # MAIN GUI
    # ============================================================

    def create_widgets(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Button(
            top,
            text="Open SET / PCG",
            command=self.open_file,
        ).pack(side="left", padx=5)

        ttk.Button(
            top,
            text="Refresh",
            command=self.refresh_editor,
        ).pack(side="left", padx=5)

        ttk.Button(
            top,
            text="Edit MIDI",
            command=self.edit_selected_midi,
        ).pack(side="left", padx=5)

        ttk.Button(
            top,
            text="Undo",
            command=self.undo,
        ).pack(side="left", padx=5)

        ttk.Button(
            top,
            text="Redo",
            command=self.redo,
        ).pack(side="left", padx=5)

        ttk.Button(
            top,
            text="Validate",
            command=self.validate_mapping,
        ).pack(side="left", padx=5)

        status_frame = ttk.Frame(self.root, padding=(10, 0))
        status_frame.pack(fill="x")

        self.status_label = ttk.Label(
            status_frame,
            text="No file loaded.",
        )
        self.status_label.pack(side="left")

        self.modified_label = ttk.Label(
            status_frame,
            text="Source file modified: NO",
        )
        self.modified_label.pack(side="right")

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

        # --------------------------------------------------------
        # KIT LIST
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # MIDI MAPPING
        # --------------------------------------------------------

        mapping_frame = ttk.LabelFrame(
            main,
            text="MIDI Mapping Editor",
            padding=5,
        )

        main.add(
            mapping_frame,
            weight=4,
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

        # --------------------------------------------------------
        # BOTTOM INFORMATION
        # --------------------------------------------------------

        bottom = ttk.Frame(
            self.root,
            padding=10,
        )

        bottom.pack(
            fill="x",
        )

        self.info_label = ttk.Label(
            bottom,
            text="Mapping count: 0",
        )

        self.info_label.pack(
            side="left",
        )

        self.validation_label = ttk.Label(
            bottom,
            text="Validation: not checked",
        )

        self.validation_label.pack(
            side="right",
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
            text=f"Loaded: {filename}"
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
            self.status_label.config(
                text="No active parser session."
            )
            return

        self.load_kits_from_session()

    # ============================================================
    # SESSION
    # ============================================================

    def set_session(self, session):
        """
        Omogućava parseru da GUI dobije postojeću session strukturu.
        """

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

    def on_kit_selected(self, event=None):
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
    # PARSER
    # ============================================================

    def get_parser(self):
        """
        Pokušava koristiti postojeći Korg parser.

        Ako parser nije dostupan, GUI i dalje može
        da se pokrene bez rušenja.
        """

        try:
            from korg.set_parser import KorgSetParser

            return KorgSetParser()

        except Exception:
            return None

    # ============================================================
    # EDIT MIDI
    # ============================================================

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
    # UNDO / REDO
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

