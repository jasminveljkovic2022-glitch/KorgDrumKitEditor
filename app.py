import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_NAME = "Korg Drum Kit Editor"
APP_VERSION = "2.0 Analyzer"


class KorgDrumKitEditor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.current_file = None
        self.current_set = None

        self.create_gui()

    # ---------------------------------------------------------
    # GUI
    # ---------------------------------------------------------

    def create_gui(self):

        title = tk.Label(
            self.root,
            text=APP_NAME,
            font=("Arial", 22, "bold")
        )
        title.pack(pady=(15, 2))

        version = tk.Label(
            self.root,
            text=f"Version {APP_VERSION} — READ ONLY",
            font=("Arial", 10)
        )
        version.pack()

        toolbar = tk.Frame(self.root)
        toolbar.pack(pady=15)

        tk.Button(
            toolbar,
            text="Open SET",
            width=18,
            command=self.open_set
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="Open PCG",
            width=18,
            command=self.open_pcg
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="Hex Viewer",
            width=18,
            command=self.show_hex
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="File List",
            width=18,
            command=self.show_file_list
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="Clear",
            width=12,
            command=self.clear
        ).pack(side=tk.LEFT, padx=5)

        # Main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(
            fill=tk.BOTH,
            expand=True,
            padx=15,
            pady=10
        )

        # Information tab
        self.info_frame = tk.Frame(self.notebook)
        self.notebook.add(
            self.info_frame,
            text="Information"
        )

        self.info_text = tk.Text(
            self.info_frame,
            font=("Consolas", 11),
            wrap=tk.NONE
        )
        self.info_text.pack(
            fill=tk.BOTH,
            expand=True
        )

        # Hex tab
        self.hex_frame = tk.Frame(self.notebook)
        self.notebook.add(
            self.hex_frame,
            text="Hex Viewer"
        )

        self.hex_text = tk.Text(
            self.hex_frame,
            font=("Consolas", 10),
            wrap=tk.NONE
        )
        self.hex_text.pack(
            fill=tk.BOTH,
            expand=True
        )

        # File list tab
        self.files_frame = tk.Frame(self.notebook)
        self.notebook.add(
            self.files_frame,
            text="SET Files"
        )

        columns = (
            "path",
            "size"
        )

        self.file_tree = ttk.Treeview(
            self.files_frame,
            columns=columns,
            show="headings"
        )

        self.file_tree.heading(
            "path",
            text="File"
        )

        self.file_tree.heading(
            "size",
            text="Size (bytes)"
        )

        self.file_tree.column(
            "path",
            width=750
        )

        self.file_tree.column(
            "size",
            width=150,
            anchor=tk.E
        )

        scrollbar = ttk.Scrollbar(
            self.files_frame,
            orient=tk.VERTICAL,
            command=self.file_tree.yview
        )

        self.file_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.file_tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        # Status bar
        self.status = tk.Label(
            self.root,
            text="Ready",
            anchor=tk.W,
            relief=tk.SUNKEN
        )
        self.status.pack(
            side=tk.BOTTOM,
            fill=tk.X
        )

        self.write_info(
            "KORG DRUM KIT EDITOR\n"
            "=====================\n\n"
            "READ ONLY ANALYZER\n\n"
            "Open a Korg .SET folder or USERDK.PCG file.\n\n"
            "The original files are never modified.\n\n"
            "Next development stage:\n"
            "- Korg PCG structure detection\n"
            "- Drum Kit detection\n"
            "- Piano keyboard map\n"
            "- Layer detection\n"
            "- Velocity ranges\n"
            "- Size analysis\n"
        )

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    def write_info(self, text):
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, text)

    def clear(self):
        self.current_file = None
        self.current_set = None

        self.write_info(
            "Analyzer cleared.\n\n"
            "Choose Open SET or Open PCG."
        )

        self.hex_text.delete(
            "1.0",
            tk.END
        )

        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        self.status.config(
            text="Ready"
        )

    # ---------------------------------------------------------
    # SET
    # ---------------------------------------------------------

    def open_set(self):

        folder = filedialog.askdirectory(
            title="Select Korg SET folder"
        )

        if not folder:
            return

        self.current_set = folder

        self.status.config(
            text=f"Analyzing SET: {folder}"
        )

        files = []

        for root, dirs, filenames in os.walk(folder):

            for filename in filenames:

                full_path = os.path.join(
                    root,
                    filename
                )

                try:
                    size = os.path.getsize(
                        full_path
                    )
                except OSError:
                    size = 0

                relative = os.path.relpath(
                    full_path,
                    folder
                )

                files.append(
                    (relative, size)
                )

        files.sort(
            key=lambda x: x[0].lower()
        )

        # Clear tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # Add files
        for relative, size in files:

            self.file_tree.insert(
                "",
                tk.END,
                values=(
                    relative,
                    f"{size:,}"
                )
            )

        # Search for PCG
        pcg_files = []

        for relative, size in files:

            if relative.upper().endswith(".PCG"):

                pcg_files.append(
                    (relative, size)
                )

        userdk = []

        for relative, size in pcg_files:

            if os.path.basename(
                relative
            ).upper() == "USERDK.PCG":

                userdk.append(
                    (relative, size)
                )

        info = []

        info.append(
            "KORG SET ANALYSIS"
        )

        info.append(
            "=================\n"
        )

        info.append(
            f"SET folder:\n{folder}\n"
        )

        info.append(
            f"Total files: {len(files):,}"
        )

        info.append(
            f"PCG files:   {len(pcg_files):,}"
        )

        info.append("")

        if userdk:

            info.append(
                "USERDK.PCG FOUND"
            )

            info.append(
                "----------------"
            )

            for relative, size in userdk:

                full_path = os.path.join(
                    folder,
                    relative
                )

                info.append(
                    f"Path: {relative}"
                )

                info.append(
                    f"Size: {size:,} bytes"
                )

                info.append(
                    f"Size: {self.format_size(size)}"
                )

                sha = self.sha256(
                    full_path
                )

                info.append(
                    f"SHA-256: {sha}"
                )

                info.append("")

                # Automatically prepare hex preview
                self.load_hex_preview(
                    full_path
                )

        else:

            info.append(
                "USERDK.PCG NOT FOUND"
            )

            info.append(
                "--------------------"
            )

            info.append(
                "The SET may use another PCG structure."
            )

        self.write_info(
            "\n".join(info)
        )

        self.notebook.select(
            self.info_frame
        )

        self.status.config(
            text="SET analysis complete — READ ONLY"
        )

    # ---------------------------------------------------------
    # PCG
    # ---------------------------------------------------------

    def open_pcg(self):

        filename = filedialog.askopenfilename(
            title="Open Korg PCG",
            filetypes=[
                (
                    "Korg PCG files",
                    "*.PCG *.pcg"
                ),
                (
                    "All files",
                    "*.*"
                )
            ]
        )

        if not filename:
            return

        self.current_file = filename

        try:
            size = os.path.getsize(
                filename
            )

            sha = self.sha256(
                filename
            )

            with open(
                filename,
                "rb"
            ) as f:

                data = f.read(
                    1024
                )

            info = (
                "KORG PCG ANALYSIS\n"
                "=================\n\n"
                f"File:\n{filename}\n\n"
                f"File size: {size:,} bytes\n"
                f"File size: {self.format_size(size)}\n\n"
                f"SHA-256:\n{sha}\n\n"
                "Format status:\n"
                "Binary Korg file detected.\n\n"
                "Drum Kit parser:\n"
                "NOT YET IMPLEMENTED\n\n"
                "Current version is READ ONLY.\n"
            )

            self.write_info(
                info
            )

            self.load_hex_preview(
                filename
            )

            self.notebook.select(
                self.info_frame
            )

            self.status.config(
                text="PCG loaded — READ ONLY"
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to read PCG:\n\n{e}"
            )

    # ---------------------------------------------------------
    # HEX
    # ---------------------------------------------------------

    def load_hex_preview(
        self,
        filename,
        max_bytes=4096
    ):

        self.hex_text.delete(
            "1.0",
            tk.END
        )

        try:

            with open(
                filename,
                "rb"
            ) as f:

                data = f.read(
                    max_bytes
                )

            lines = []

            for offset in range(
                0,
                len(data),
                16
            ):

                chunk = data[
                    offset:offset + 16
                ]

                hex_part = " ".join(
                    f"{b:02X}"
                    for b in chunk
                )

                hex_part = (
                    hex_part.ljust(47)
                )

                ascii_part = "".join(
                    chr(b)
                    if 32 <= b <= 126
                    else "."
                    for b in chunk
                )

                lines.append(
                    f"{offset:08X}  "
                    f"{hex_part}  "
                    f"{ascii_part}"
                )

            self.hex_text.insert(
                tk.END,
                "\n".join(lines)
            )

            self.hex_text.insert(
                tk.END,
                "\n\n"
                f"Displayed first "
                f"{len(data):,} bytes."
            )

        except Exception as e:

            self.hex_text.insert(
                tk.END,
                f"HEX ERROR: {e}"
            )

    def show_hex(self):

        if not self.current_file:

            messagebox.showinfo(
                "Hex Viewer",
                "First open a PCG file."
            )

            return

        if os.path.isfile(
            self.current_file
        ):

            self.load_hex_preview(
                self.current_file
            )

            self.notebook.select(
                self.hex_frame
            )

    # ---------------------------------------------------------
    # FILE LIST
    # ---------------------------------------------------------

    def show_file_list(self):

        if not self.current_set:

            messagebox.showinfo(
                "SET Files",
                "First open a SET folder."
            )

            return

        self.notebook.select(
            self.files_frame
        )

    # ---------------------------------------------------------
    # HASH
    # ---------------------------------------------------------

    @staticmethod
    def sha256(filename):

        h = hashlib.sha256()

        with open(
            filename,
            "rb"
        ) as f:

            while True:

                chunk = f.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                h.update(
                    chunk
                )

        return h.hexdigest()

    # ---------------------------------------------------------
    # SIZE
    # ---------------------------------------------------------

    @staticmethod
    def format_size(size):

        units = [
            "B",
            "KB",
            "MB",
            "GB"
        ]

        value = float(size)

        for unit in units:

            if value < 1024:
                return f"{value:.2f} {unit}"

            value /= 1024

        return f"{value:.2f} TB"


def main():

    root = tk.Tk()

    app = KorgDrumKitEditor(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()
