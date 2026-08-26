import tkinter as tk
from tkinter import filedialog, messagebox


class KorgDrumKitEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Korg Drum Kit Editor")
        self.root.geometry("900x600")

        self.filename = None

        title = tk.Label(
            root,
            text="KORG DRUM KIT EDITOR",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=15)

        buttons = tk.Frame(root)
        buttons.pack(pady=10)

        tk.Button(
            buttons,
            text="Open PCG",
            width=15,
            command=self.open_pcg
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons,
            text="Open SET",
            width=15,
            command=self.open_set
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons,
            text="Hex Viewer",
            width=15,
            command=self.hex_viewer
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons,
            text="About",
            width=15,
            command=self.about
        ).pack(side=tk.LEFT, padx=5)

        self.info = tk.Text(
            root,
            height=25,
            width=105
        )
        self.info.pack(padx=15, pady=15)

        self.info.insert(
            tk.END,
            "Korg Drum Kit Editor\n"
            "====================\n\n"
            "Program je spreman.\n\n"
            "Sljedeći korak:\n"
            "- učitavanje USERDK.PCG\n"
            "- analiza Drum Kitova\n"
            "- prikaz MIDI nota\n"
            "- prikaz velocity layera\n"
            "- uređivanje layera\n"
        )

    def open_pcg(self):
        filename = filedialog.askopenfilename(
            title="Open Korg PCG",
            filetypes=[
                ("Korg PCG files", "*.PCG"),
                ("All files", "*.*")
            ]
        )

        if filename:
            self.filename = filename
            self.info.delete("1.0", tk.END)
            self.info.insert(
                tk.END,
                f"Otvoren fajl:\n{filename}\n\n"
                "PCG analyzer još nije aktivan.\n"
            )

    def open_set(self):
        filename = filedialog.askdirectory(
            title="Open Korg SET folder"
        )

        if filename:
            self.filename = filename
            self.info.delete("1.0", tk.END)
            self.info.insert(
                tk.END,
                f"Otvoren SET folder:\n{filename}\n\n"
                "SET analyzer još nije aktivan.\n"
            )

    def hex_viewer(self):
        if not self.filename:
            messagebox.showinfo(
                "Hex Viewer",
                "Prvo otvori PCG fajl."
            )
            return

        messagebox.showinfo(
            "Hex Viewer",
            "Hex Viewer će biti dodat u sljedećoj verziji."
        )

    def about(self):
        messagebox.showinfo(
            "About",
            "Korg Drum Kit Editor\n"
            "Windows 11\n\n"
            "Development version"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = KorgDrumKitEditor(root)
    root.mainloop()
