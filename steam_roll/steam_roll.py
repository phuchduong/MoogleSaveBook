"""
Author: Phuc H Duong (https://github.com/phuchduong)
Purpose: Randomly selects an installed Steam game and displays its official vertical cover art 
         from local Steam cache files or Steam CDN fallback inside a Tkinter GUI.
Date Created: September 23, 2026
Last Updated: September 23, 2026
Platform: Windows
"""

import io
import os
import re
import random
import glob
import winreg
import urllib.request
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


def get_steam_path() -> str:
    """Finds Steam installation path from the Windows Registry."""
    print("\n--- DEBUG: Locating Steam Installation ---")
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"
        )
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        norm_path = os.path.normpath(steam_path)
        print(f"[+] Found Steam path in Registry: {norm_path}")
        return norm_path
    except Exception as err:
        print(f"[-] Could not read Registry key: {err}")
        default_path = r"C:\Program Files (x86)\Steam"
        if os.path.exists(default_path):
            print(f"[+] Falling back to default path: {default_path}")
            return default_path
        else:
            print(f"[-] Default path does not exist: {default_path}")
            return ""


class SteamGridPickerApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.steam_root = get_steam_path()
        self.games_data = []

        self.root.title("Steam Random Game Picker")
        self.root.geometry("450x650")
        self.root.resizable(False, False)

        # Container Frame using Grid layout
        container = tk.Frame(root, padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        container.columnconfigure(0, weight=1)

        # 1. Header Title
        self.header_label = tk.Label(
            container, text="Random Steam Game Picker", font=("Segoe UI", 14, "bold")
        )
        self.header_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

        # 2. Selected Game Name Title
        self.title_label = tk.Label(
            container,
            text="Loading games...",
            font=("Segoe UI", 11, "bold"),
            wraplength=400,
            justify="center",
            fg="#2c3e50",
            height=2,
        )
        self.title_label.grid(row=1, column=0, pady=5, sticky="ew")

        # 3. Interactive Canvas Display Area (260x390)
        self.canvas = tk.Canvas(
            container, width=260, height=390, bg="#1b2838", highlightthickness=1, highlightbackground="#2a475e"
        )
        self.canvas.grid(row=2, column=0, pady=10)

        # 4. Action Button
        self.pick_button = tk.Button(
            container,
            text="ROLL GAME",
            font=("Segoe UI", 12, "bold"),
            bg="#171a21",
            fg="#66c0f4",
            activebackground="#2a475e",
            activeforeground="#ffffff",
            padx=25,
            pady=10,
            cursor="hand2",
            command=self.pick_random_game,
        )
        self.pick_button.grid(row=3, column=0, pady=(10, 0))

        self.tk_image = None
        self.load_installed_games()

        # Automatically roll the first game upon startup
        if self.games_data:
            self.pick_random_game()

    def get_library_paths(self) -> list[str]:
        """Reads libraryfolders.vdf to find all Steam library locations."""
        libraries = []
        if not self.steam_root:
            return libraries

        main_steamapps = os.path.join(self.steam_root, "steamapps")
        if os.path.exists(main_steamapps):
            libraries.append(main_steamapps)

        vdf_path = os.path.join(main_steamapps, "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                for p in paths:
                    norm_p = os.path.normpath(p.replace("\\\\", "\\"))
                    s_apps = os.path.join(norm_p, "steamapps")
                    if os.path.exists(s_apps) and s_apps not in libraries:
                        libraries.append(s_apps)
            except Exception:
                pass

        return libraries

    def find_cover_art(self, appid: str) -> str:
        """Searches local cache for artwork."""
        if not appid or not self.steam_root:
            return ""

        cache_dir = os.path.join(self.steam_root, "appcache", "librarycache")
        patterns = [
            os.path.join(cache_dir, f"{appid}_library_600x900.jpg"),
            os.path.join(cache_dir, f"{appid}_library_600x900_2x.jpg"),
            os.path.join(cache_dir, f"{appid}_header.jpg"),
        ]

        for path in patterns:
            if os.path.exists(path):
                return path

        userdata_dir = os.path.join(self.steam_root, "userdata")
        if os.path.exists(userdata_dir):
            custom_grid_matches = glob.glob(
                os.path.join(userdata_dir, "*", "config", "grid", f"{appid}p.*")
            )
            if custom_grid_matches:
                return custom_grid_matches[0]

        return ""

    def fetch_remote_cover(self, appid: str) -> Image.Image | None:
        """Fetches cover image from Steam CDN if local art is missing."""
        if not appid:
            return None

        urls = [
            f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
            f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg",
        ]

        for url in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    print(f"[+] Downloaded remote cover for AppID {appid}")
                    return Image.open(io.BytesIO(resp.read()))
            except Exception:
                continue

        return None

    def load_installed_games(self) -> None:
        """Scans all detected Steam libraries for installed games."""
        library_paths = self.get_library_paths()
        if not library_paths:
            messagebox.showerror("Error", "Could not locate any Steam library folders.")
            return

        seen_appids = set()

        for lib in library_paths:
            manifest_files = glob.glob(os.path.join(lib, "appmanifest_*.acf"))

            for manifest in manifest_files:
                try:
                    with open(manifest, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    appid_match = re.search(r'"appid"\s+"(\d+)"', content)
                    name_match = re.search(r'"name"\s+"([^"]+)"', content)

                    if appid_match and name_match:
                        appid = appid_match.group(1)
                        game_name = name_match.group(1)

                        if appid not in seen_appids:
                            seen_appids.add(appid)
                            cover_path = self.find_cover_art(appid)
                            self.games_data.append({
                                "name": game_name,
                                "appid": appid,
                                "cover_path": cover_path
                            })
                except Exception:
                    continue

        if not self.games_data:
            self.title_label.config(text="No installed games found.")

    def render_fallback_card(self, game_name: str, appid: str) -> None:
        """Draws a custom placeholder card directly on the Canvas if image fails."""
        self.canvas.delete("all")
        self.canvas.create_rectangle(10, 10, 250, 380, outline="#66c0f4", width=2)
        self.canvas.create_text(
            130, 160, text=game_name, fill="#ffffff", font=("Segoe UI", 12, "bold"), width=220, justify="center"
        )
        self.canvas.create_text(
            130, 230, text=f"AppID: {appid}", fill="#c6d4df", font=("Segoe UI", 9)
        )

    def pick_random_game(self) -> None:
        """Selects a random game and updates canvas."""
        if not self.games_data:
            return

        selected = random.choice(self.games_data)
        game_name = selected["name"]
        cover_path = selected["cover_path"]
        appid = selected["appid"]

        print(f"\n[+] Selected: {game_name} (AppID: {appid})")
        self.title_label.config(text=game_name)

        img = None
        if cover_path and os.path.exists(cover_path):
            try:
                img = Image.open(cover_path)
            except Exception:
                img = None

        if img is None and appid:
            img = self.fetch_remote_cover(appid)

        if img:
            try:
                img = img.resize((260, 390), Image.Resampling.LANCZOS)
                self.tk_image = ImageTk.PhotoImage(img)
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            except Exception as err:
                print(f"[-] Canvas render error: {err}")
                self.render_fallback_card(game_name, appid)
        else:
            print("[-] Image unavailable. Drawing canvas fallback card.")
            self.render_fallback_card(game_name, appid)


def main():
    root = tk.Tk()
    app = SteamGridPickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

