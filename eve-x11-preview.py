#!/usr/bin/env python3

import subprocess
import os
import tkinter as tk
from PIL import Image, ImageTk
import logging
from Xlib import X, display

# --- Configuration ---
PREVIEW_DIR = "/tmp/eve_previews"
UPDATE_INTERVAL_MS = 2000
THUMBNAIL_SIZE = "200x150"
GRID_COLUMNS = 3

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
os.makedirs(PREVIEW_DIR, exist_ok=True)


class EvePreviewApp:
    def __init__(self, root):
        """Initializes the application window and data structures."""
        self.root = root
        self.root.title("EVE Online Previews")
        self.root.attributes("-topmost", True)
        self.disp = display.Display()
        self.win_data = {}

    def _get_eve_windows(self):
        """Finds all EVE Online client windows using wmctrl."""
        try:
            command = ["wmctrl", "-lx"]
            output = subprocess.check_output(command).decode("utf-8")
            eve_windows = []
            for line in output.strip().split("\n"):
                parts = line.split(maxsplit=4)
                if len(parts) < 5: continue
                win_id, win_class, title = parts[0], parts[2], parts[4]
                if "steam_app_" in win_class and "EVE -" in title:
                    char_name = title.replace("EVE - ", "").strip()
                    eve_windows.append((win_id, char_name))
            return dict(eve_windows)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.error("`wmctrl` command failed. Is it installed and in your PATH?")
            return {}

    def _capture_thumbnail(self, win_id, out_path):
        """Captures a specific window's content using ImageMagick."""
        try:
            command = [
                "import", "-window", win_id,
                "-resize", THUMBNAIL_SIZE,
                "-quality", "85",
                out_path
            ]
            subprocess.run(
                command, check=True, timeout=3,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logging.warning(f"Capture failed for window {win_id}: {e}")
            return False
        except FileNotFoundError:
            logging.error("`import` command failed. Is ImageMagick installed?")
            if hasattr(self, 'update_job'): self.root.after_cancel(self.update_job)
            return False

    def _focus_window(self, win_id):
        """Brings the specified window to the foreground using direct X11 commands."""
        try:
            # Create a resource object for the window ID
            window = self.disp.create_resource_object('window', int(win_id, 16))

            # 1. Raise the window to the top of the stack
            window.raise_window()

            # 2. Give the window input focus
            self.disp.set_input_focus(window, X.RevertToParent, X.CurrentTime)

            # Ensure the commands are sent to the X server immediately
            self.disp.sync()

        except Exception as e:
            logging.error(f"Failed to focus window {win_id} with Xlib: {e}")

    def _update_gui(self):
        """The main loop to update, add, and remove window previews."""
        current_windows = self._get_eve_windows()

        closed_ids = self.win_data.keys() - current_windows.keys()
        for win_id in list(closed_ids):
            if win_id in self.win_data:
                self.win_data[win_id]["btn"].destroy()
                self.win_data[win_id]["label"].destroy()
                del self.win_data[win_id]

        for idx, (win_id, title) in enumerate(current_windows.items()):
            img_path = os.path.join(PREVIEW_DIR, f"{win_id}.png")

            if not self._capture_thumbnail(win_id, img_path):
                continue

            try:
                img = Image.open(img_path)
                thumb = ImageTk.PhotoImage(img)
            except (FileNotFoundError, Image.UnidentifiedImageError) as e:
                logging.warning(f"Could not load image {img_path}: {e}")
                continue

            row = (idx // GRID_COLUMNS) * 2
            col = idx % GRID_COLUMNS

            if win_id not in self.win_data:
                btn = tk.Button(
                    self.root,
                    image=thumb,
                    command=lambda wid=win_id: self._focus_window(wid)
                )
                label = tk.Label(self.root, text=title[:30], font=("", 12))
                btn.grid(row=row, column=col, padx=5, pady=2)
                label.grid(row=row + 1, column=col, pady=2)
                self.win_data[win_id] = {"btn": btn, "label": label}
            else:
                btn = self.win_data[win_id]["btn"]
                btn.config(image=thumb)

            self.win_data[win_id]["btn"].image = thumb

        self.update_job = self.root.after(UPDATE_INTERVAL_MS, self._update_gui)

    def run(self):
        """Starts the application."""
        self._update_gui()
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = EvePreviewApp(root)
    app.run()
