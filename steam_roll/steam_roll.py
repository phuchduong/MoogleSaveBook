"""
Author: Phuc H Duong (https://github.com/phuchduong)
Purpose: Randomly selects an installed Steam game from the designated library folder
         and displays the result in a persistent graphical user interface.
Date Created: September 23, 2026
Last Updated: September 23, 2026
Platform: Windows
"""

import os
import random
import tkinter as tk
from tkinter import messagebox

# Default Steam library path on Windows
DEFAULT_STEAM_DIR = r"C:\Program Files (x86)\Steam\steamapps\common"


class SteamGamePickerApp:

    def __init__(self, root: tk.Tk, steam_dir: str):
        self.root = root
        self.steam_dir = steam_dir
        self.games_list = []

        self.root.title("Steam Random Game Picker")
        self.root.geometry("450x220")
        self.root.resizable(False, False)

        # Main frame padding
        frame = tk.Frame(root, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Header Label
        self.header_label = tk.Label(
            frame,
            text="Random Steam Game Picker",
            font=("Segoe UI", 14, "bold"),
        )
        self.header_label.pack(pady=(0, 10))

        # Selected Game Display Label
        self.result_label = tk.Label(
            frame,
            text="Click below to pick a game!",
            font=("Segoe UI", 11),
            wraplength=400,
            justify="center",
            fg="#2c3e50",
        )
        self.result_label.pack(pady=15, fill=tk.BOTH, expand=True)

        # Action Button
        self.pick_button = tk.Button(
            frame,
            text="Pick a Game",
            font=("Segoe UI", 10, "bold"),
            bg="#007acc",
            fg="white",
            activebackground="#005999",
            activeforeground="white",
            padx=10,
            pady=5,
            command=self.pick_random_game,
        )
        self.pick_button.pack(pady=(5, 0))

        # Load installed games into memory
        self.load_games()

    def load_games(self) -> None:
        """Scans the designated directory and populates the games list with subfolders."""
        if not os.path.exists(self.steam_dir):
            messagebox.showerror(
                "Directory Not Found",
                f"The specified Steam path does not exist:\n{self.steam_dir}",
            )
            return

        try:
            # Gather all top-level directories under steamapps/common
            self.games_list = [
                entry.name
                for entry in os.scandir(self.steam_dir)
                if entry.is_dir()
            ]

            if not self.games_list:
                self.result_label.config(
                    text="No installed game folders found in the directory."
                )
        except Exception as err:
            messagebox.showerror(
                "Read Error", f"Failed to access directory:\n{err}"
            )

    def pick_random_game(self) -> None:
        """Selects a game at random from the gathered list."""
        if not self.games_list:
            messagebox.showwarning(
                "No Games Found",
                "No game folders were found in the specified path.",
            )
            return

        selected_game = random.choice(self.games_list)
        self.result_label.config(
            text=f"Selected Game:\n\n{selected_game}",
            font=("Segoe UI", 12, "bold"),
        )


def main():
    root = tk.Tk()
    app = SteamGamePickerApp(root, DEFAULT_STEAM_DIR)
    root.mainloop()


if __name__ == "__main__":
    main()
