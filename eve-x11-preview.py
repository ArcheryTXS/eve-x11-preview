#!/usr/bin/env python3

import subprocess
import os
import tkinter as tk
from PIL import Image, ImageTk
import logging
from Xlib import X, display, error

# --- Configuration ---
PREVIEW_DIR = "/tmp/eve_previews"
# Lower interval for "near-live" updates. 250ms = 4 FPS.
UPDATE_INTERVAL_MS = 250
THUMBNAIL_SIZE = "200x150" # This is used as a max-size tuple for PIL
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
        # Create the mss screen capture object once for performance
        #self.sct = mss.mss()

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
        """Captures a window's content directly, even when obscured."""
        try:
            # Get the window object from its ID
            window = self.disp.create_resource_object('window', int(win_id, 16))

            # Get window geometry
            geom = window.get_geometry()

            # Get the raw pixel data from the server for the window
            # This works even if the window is covered
            raw_image = window.get_image(0, 0, geom.width, geom.height, X.ZPixmap, 0xffffffff)
            
            # Create a PIL Image from the raw data
            img = Image.frombytes("RGB", (geom.width, geom.height), raw_image.data, "raw", "BGRX")

            # Resize it to a thumbnail
            thumbnail_tuple = (int(THUMBNAIL_SIZE.split('x')[0]), int(THUMBNAIL_SIZE.split('x')[1]))
            img.thumbnail(thumbnail_tuple)

            # Save the thumbnail
            img.save(out_path, "PNG")
            return True

        except (error.BadWindow, error.BadDrawable):
            logging.warning(f"Failed to capture {win_id}, window may have closed.")
            return False
        except Exception as e:
            logging.error(f"An unexpected error during X11 capture for {win_id}: {e}")
            return False

    def _focus_window(self, win_id):
        """Brings the specified window to the foreground using wmctrl for reliability."""
        try:
            command = ["wmctrl", "-ia", win_id]
            subprocess.run(
                command, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.error(f"Failed to focus window {win_id} with wmctrl: {e}")
            logging.error("Please ensure 'wmctrl' is installed and in your system's PATH.")

    def _update_gui(self):
        """The main loop to update, add, and remove window previews."""
        current_windows = self._get_eve_windows()

        # Clean up closed windows
        closed_ids = self.win_data.keys() - current_windows.keys()
        for win_id in list(closed_ids):
            if win_id in self.win_data:
                self.win_data[win_id]["btn"].destroy()
                self.win_data[win_id]["label"].destroy()
                del self.win_data[win_id]

        # Update and add new windows
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
                # Create new widgets
                btn = tk.Button(
                    self.root,
                    image=thumb,
                    command=lambda wid=win_id: self._focus_window(wid)
                )
                label = tk.Label(self.root, text=title[:30], font=("", 12))
                btn.grid(row=row, column=col, padx=5, pady=2)
                label.grid(row=row + 1, column=col, pady=2)
                self.win_data[win_id] = {"btn": btn, "label": label, "thumb": thumb}
            else:
                # Update existing widgets
                btn = self.win_data[win_id]["btn"]
                btn.config(image=thumb)
                self.win_data[win_id]["thumb"] = thumb # Keep a reference

            # IMPORTANT: Keep a reference to the image to prevent garbage collection
            self.win_data[win_id]["btn"].image = thumb

        # Schedule the next update
        self.update_job = self.root.after(UPDATE_INTERVAL_MS, self._update_gui)

    def run(self):
        """Starts the application."""
        self._update_gui()
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = EvePreviewApp(root)
    app.run()