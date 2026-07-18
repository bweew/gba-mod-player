#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import shutil
import re


class SongAdder:

    def get_next_music_number(self, music_dir):
        highest = -1

        for file in music_dir.iterdir():
            match = re.match(r"^(\d+)", file.name)
            if match:
                number = int(match.group(1))
                if number > highest:
                    highest = number

        return highest + 1

    def __init__(self, root):
        self.root = root
        self.root.title("GBA Tracker Song Adder")
        self.root.geometry("600x420")

        self.project = Path.cwd()
        self.mod_file = None
        self.art_file = None

        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="Project Directory").pack(anchor="w", padx=10)

        self.project_entry = tk.Entry(self.root)
        self.project_entry.insert(0, str(self.project))
        self.project_entry.pack(fill="x", padx=10)

        tk.Button(
            self.root,
            text="Select Project",
            command=self.pick_project
        ).pack(padx=10, pady=5)

        tk.Label(self.root, text="Tracker File (.mod .xm .it .s3m)").pack(anchor="w", padx=10)

        self.mod_label = tk.Label(self.root, text="None selected")
        self.mod_label.pack(anchor="w", padx=10)

        tk.Button(
            self.root,
            text="Select Tracker File",
            command=self.pick_mod
        ).pack(padx=10)

        tk.Label(self.root, text="Album Art Template").pack(anchor="w", padx=10)

        self.art_label = tk.Label(self.root, text="None selected")
        self.art_label.pack(anchor="w", padx=10)

        tk.Button(
            self.root,
            text="Select PNG",
            command=self.pick_art
        ).pack(padx=10)

        tk.Label(self.root, text="Asset Name (example: funkyfishmooncell)").pack(anchor="w", padx=10)

        self.asset_entry = tk.Entry(self.root)
        self.asset_entry.pack(fill="x", padx=10)

        tk.Label(self.root, text="Song Display Name").pack(anchor="w", padx=10)

        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack(fill="x", padx=10)

        tk.Button(
            self.root,
            text="Add Song",
            command=self.add_song
        ).pack(pady=20)

    def pick_project(self):
        folder = filedialog.askdirectory()
        if folder:
            self.project = Path(folder)
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, str(self.project))

    def pick_mod(self):
        file = filedialog.askopenfilename(
            filetypes=[
                ("Tracker Files", "*.mod *.xm *.it *.s3m"),
                ("All Files", "*.*")
            ]
        )

        if file:
            self.mod_file = Path(file)
            self.mod_label.config(text=self.mod_file.name)

            if not self.asset_entry.get():
                self.asset_entry.insert(
                    0,
                    self.clean_name(self.mod_file.stem)
                )

    def pick_art(self):
        file = filedialog.askopenfilename(
            initialdir=self.project / "graphics",
            filetypes=[
                ("PNG Images", "*.png")
            ]
        )

        if file:
            self.art_file = Path(file)
            self.art_label.config(text=self.art_file.name)

    def clean_name(self, name):
        name = name.lower()
        name = re.sub(r"[^a-zA-Z0-9_]", "", name)
        return name

    def add_song(self):

        project = Path(self.project_entry.get())

        if not self.mod_file:
            messagebox.showerror("Error", "Select tracker file")
            return

        if not self.art_file:
            messagebox.showerror("Error", "Select album art")
            return

        asset = self.clean_name(self.asset_entry.get())

        if not asset:
            messagebox.showerror("Error", "Enter asset name")
            return

        display_name = self.name_entry.get()

        if not display_name:
            messagebox.showerror("Error", "Enter song name")
            return


        #
        # Copy tracker file
        #

        music_dir = project / "music"
        music_dir.mkdir(exist_ok=True)

        next_number = self.get_next_music_number(music_dir)

        new_music_name = f"{next_number:02d}{self.mod_file.name}"

        shutil.copy(
            self.mod_file,
            music_dir / new_music_name
        )


        #
        # Copy album art
        #

        graphics = project / "graphics"

        png_dest = graphics / f"{asset}.png"
        grit_dest = graphics / f"{asset}.grit"

        shutil.copy(
            self.art_file,
            png_dest
        )

        source_grit = self.art_file.with_suffix(".grit")

        if source_grit.exists():
            shutil.copy(
                source_grit,
                grit_dest
            )


        #
        # Modify main.cpp
        #

        main_cpp = project / "source" / "main.cpp"

        if not main_cpp.exists():
            messagebox.showerror(
                "Error",
                "source/main.cpp not found"
            )
            return

        code = main_cpp.read_text()


        include_line = f'#include "{asset}.h"\n'

        if include_line not in code:

            include_pos = code.find("#include")

            while include_pos != -1:
                next_line = code.find("\n", include_pos)

                if next_line == -1:
                    break

                if not code[next_line+1:].startswith("#include"):
                    break

                include_pos = next_line + 1

            code = (
                code[:next_line+1]
                + include_line
                + code[next_line+1:]
            )


        song_entry = f'''    {{
        {asset}Tiles,
        {asset}Pal,
        "{display_name}"
    }},\n'''

        array_match = re.search(
            r"(song songs\[\]\s*=\s*\{)(.*?)(\n\};)",
            code,
            re.DOTALL
        )

        if not array_match:
            messagebox.showerror(
                "Error",
                "songs[] array not found"
            )
            return

        songs_body = array_match.group(2)

        # Make sure the existing last entry has a comma
        songs_body = songs_body.rstrip()

        if songs_body.endswith("}"):
            songs_body += ","

        new_body = (
            songs_body
            + "\n"
            + song_entry
        )

        code = (
            code[:array_match.start(2)]
            + new_body
            + code[array_match.end(2):]
        )

        main_cpp.write_text(code)

        messagebox.showinfo(
            "Complete",
            f"Added {display_name}\n\n"
            f"Asset: {asset}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = SongAdder(root)
    root.mainloop()
