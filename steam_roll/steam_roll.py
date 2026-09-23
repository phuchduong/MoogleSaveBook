"""
Author: Phuc H Duong (https://github.com/phuchduong)
Purpose: Randomly selects an installed Steam game using a synchronized 3D 
         vertical wheel-scroll animator with accurate ease-out landing.
Date Created: September 23, 2026
Last Updated: September 23, 2026
Platform: Windows
"""

import io
import os
import re
import math
import random
import glob
import winreg
import urllib.request
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps


def get_steam_path() -> str:
    """Finds Steam installation path from the Windows Registry."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"
        )
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return os.path.normpath(steam_path)
    except Exception:
        default_path = r"C:\Program Files (x86)\Steam"
        return default_path if os.path.exists(default_path) else ""


class SteamWheelPickerApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.steam_root = get_steam_path()
        self.games_data = []
        self.is_spinning = False

        # Wheel animation parameters
        self.item_height = 45
        self.scroll_offset = 0.0
        self.selected_index = 0

        # Animation timing control
        self.anim_start_offset = 0.0
        self.anim_target_offset = 0.0
        self.anim_step = 0
        self.anim_total_steps = 120  # ~2 seconds at 60 FPS (16ms per frame)

        self.root.title("Steam Game Wheel Picker")
        self.root.geometry("820x550")
        self.root.resizable(False, False)

        main_container = tk.Frame(root, bg="#171a21", padx=15, pady=15)
        main_container.pack(fill=tk.BOTH, expand=True)

        # ---------------- LEFT PANEL: Vertical Wheel Drum ----------------
        left_frame = tk.Frame(main_container, bg="#171a21")
        left_frame.pack(side=tk.LEFT, padx=10, fill=tk.Y)

        wheel_title = tk.Label(
            left_frame,
            text="Steam Library Wheel",
            font=("Segoe UI", 14, "bold"),
            fg="#66c0f4",
            bg="#171a21",
        )
        wheel_title.pack(pady=(0, 10))

        # Vertical Wheel Canvas
        self.wheel_canvas = tk.Canvas(
            left_frame,
            width=360,
            height=360,
            bg="#1b2838",
            highlightthickness=2,
            highlightbackground="#2a475e",
        )
        self.wheel_canvas.pack()

        # Spin Button
        self.spin_button = tk.Button(
            left_frame,
            text="SPIN WHEEL",
            font=("Segoe UI", 12, "bold"),
            bg="#1b2838",
            fg="#66c0f4",
            activebackground="#2a475e",
            activeforeground="#ffffff",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.start_wheel_spin,
        )
        self.spin_button.pack(pady=15)

        # ---------------- RIGHT PANEL: Game Cover Art ----------------
        right_frame = tk.Frame(main_container, bg="#171a21")
        right_frame.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH, expand=True)

        self.title_label = tk.Label(
            right_frame,
            text="Spin to pick a game!",
            font=("Segoe UI", 12, "bold"),
            wraplength=380,
            justify="center",
            fg="#c6d4df",
            bg="#171a21",
            height=2,
        )
        self.title_label.pack(pady=(0, 5))

        # Canvas bounding box (280x360)
        self.canvas_w = 280
        self.canvas_h = 360
        self.cover_canvas = tk.Canvas(
            right_frame,
            width=self.canvas_w,
            height=self.canvas_h,
            bg="#1b2838",
            highlightthickness=1,
            highlightbackground="#2a475e",
        )
        self.cover_canvas.pack(pady=5)

        self.tk_image = None

        self.load_installed_games()
        self.draw_wheel()

    def get_library_paths(self) -> list[str]:
        """Reads libraryfolders.vdf to locate Steam library paths."""
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
        """Searches local cache for artwork files."""
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
        """Fetches cover image from Steam CDN as fallback."""
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

    def draw_wheel(self) -> None:
        """Renders the vertical drum picker with cylindrical projection effects."""
        self.wheel_canvas.delete("all")

        canvas_width = 360
        canvas_height = 360
        center_y = canvas_height / 2
        total_games = len(self.games_data)

        if total_games == 0:
            return

        box_h = 50
        self.wheel_canvas.create_rectangle(
            15,
            center_y - box_h / 2,
            canvas_width - 15,
            center_y + box_h / 2,
            fill="#2a475e",
            outline="#66c0f4",
            width=2,
        )

        visible_range = 5
        center_index_float = self.scroll_offset / self.item_height

        for offset in range(-visible_range, visible_range + 1):
            idx = (math.floor(center_index_float) + offset) % total_games
            game = self.games_data[idx]

            y_pos = center_y + (offset - (center_index_float % 1)) * self.item_height
            norm_y = (y_pos - center_y) / (center_y * 0.95)

            if -1.0 <= norm_y <= 1.0:
                angle = norm_y * (math.pi / 2.3)
                cos_val = math.cos(angle)

                font_size = max(8, int(13 * cos_val))
                opacity_factor = max(0.2, cos_val ** 2)

                if abs(y_pos - center_y) < (self.item_height / 2):
                    color = "#ffffff"
                    font_style = ("Segoe UI", 12, "bold")
                else:
                    gray_val = int(198 * opacity_factor)
                    color = f"#{gray_val:02x}{gray_val:02x}{gray_val:02x}"
                    font_style = ("Segoe UI", font_size)

                game_text = game["name"]
                if len(game_text) > 32:
                    game_text = game_text[:30] + ".."

                self.wheel_canvas.create_text(
                    canvas_width / 2,
                    y_pos,
                    text=game_text,
                    fill=color,
                    font=font_style,
                    justify="center",
                )

        self.wheel_canvas.create_polygon(
            22, center_y - 8, 22, center_y + 8, 32, center_y, fill="#66c0f4"
        )
        self.wheel_canvas.create_polygon(
            canvas_width - 22, center_y - 8, canvas_width - 22, center_y + 8, canvas_width - 32, center_y, fill="#66c0f4"
        )

    def start_wheel_spin(self) -> None:
        """Triggers synchronized easing animation directly to selected game."""
        if not self.games_data or self.is_spinning:
            return

        self.is_spinning = True
        self.spin_button.config(state=tk.DISABLED)

        total_games = len(self.games_data)
        self.selected_index = random.randint(0, total_games - 1)

        # Current continuous position
        self.anim_start_offset = self.scroll_offset

        # Number of full wheel rotations before stopping (3 to 5 full loops)
        full_rotations = random.randint(3, 5)

        # Calculate exact target offset so winning item lands precisely in center box
        current_item_index = self.anim_start_offset / self.item_height
        
        # Calculate extra slots needed to reach target index
        slots_to_target = (self.selected_index - (current_item_index % total_games)) % total_games
        total_slots_to_move = (full_rotations * total_games) + slots_to_target

        self.anim_target_offset = self.anim_start_offset + (total_slots_to_move * self.item_height)
        
        self.anim_step = 0
        self.anim_total_steps = 130  # ~2.1 seconds smooth easing animation

        self._animate_easing()

    def _animate_easing(self) -> None:
        """Uses Cubic Ease-Out curve for a seamless transition without jumps."""
        if self.anim_step <= self.anim_total_steps:
            # Normalized progress t from 0.0 to 1.0
            t = self.anim_step / self.anim_total_steps

            # Cubic Ease-Out formula: 1 - (1 - t)^3
            ease_out = 1.0 - math.pow(1.0 - t, 3)

            # Interpolate offset
            self.scroll_offset = self.anim_start_offset + (
                (self.anim_target_offset - self.anim_start_offset) * ease_out
            )

            self.draw_wheel()

            # Update live header label during spin
            current_idx = int(round(self.scroll_offset / self.item_height)) % len(self.games_data)
            self.title_label.config(text=self.games_data[current_idx]["name"])

            self.anim_step += 1
            self.root.after(16, self._animate_easing)
        else:
            # Lock precisely to target offset at the end
            self.scroll_offset = self.anim_target_offset
            self.draw_wheel()

            self.is_spinning = False
            self.spin_button.config(state=tk.NORMAL)

            selected_game = self.games_data[self.selected_index]
            self.display_selected_game(selected_game)

    def display_selected_game(self, game: dict) -> None:
        """Loads and displays cover art preserving aspect ratio."""
        game_name = game["name"]
        cover_path = game["cover_path"]
        appid = game["appid"]

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
                fitted_img = ImageOps.contain(
                    img, (self.canvas_w, self.canvas_h), method=Image.Resampling.LANCZOS
                )
                self.tk_image = ImageTk.PhotoImage(fitted_img)
                self.cover_canvas.delete("all")
                
                self.cover_canvas.create_image(
                    self.canvas_w / 2,
                    self.canvas_h / 2,
                    anchor=tk.CENTER,
                    image=self.tk_image,
                )
            except Exception:
                self.render_fallback_card(game_name, appid)
        else:
            self.render_fallback_card(game_name, appid)

    def render_fallback_card(self, game_name: str, appid: str) -> None:
        """Draws fallback placeholder card if artwork is unavailable."""
        self.cover_canvas.delete("all")
        self.cover_canvas.create_rectangle(10, 10, self.canvas_w - 10, self.canvas_h - 10, outline="#66c0f4", width=2)
        self.cover_canvas.create_text(
            self.canvas_w / 2, 150, text=game_name, fill="#ffffff", font=("Segoe UI", 11, "bold"), width=self.canvas_w - 40, justify="center"
        )
        self.cover_canvas.create_text(
            self.canvas_w / 2, 220, text=f"AppID: {appid}", fill="#c6d4df", font=("Segoe UI", 9)
        )


def main():
    root = tk.Tk()
    app = SteamWheelPickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()