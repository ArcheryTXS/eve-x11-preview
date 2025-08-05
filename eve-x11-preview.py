import subprocess
import os
import tkinter as tk
from PIL import Image, ImageTk
from time import time

# Config
PREVIEW_DIR = "/tmp/eve_previews"
UPDATE_INTERVAL = 2000  # in milliseconds
THUMBNAIL_SIZE = "200x150"

os.makedirs(PREVIEW_DIR, exist_ok=True)

class EvePreviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EVE Online Window Previews")
        self.root.attributes("-topmost", True)
        self.win_data = {}  # win_id: {btn, label}
        self.update_thumbnails()

    def get_eve_windows(self):
        output = subprocess.check_output(["wmctrl", "-lx"]).decode()
        eve_windows = []
        for line in output.strip().split("\n"):
            parts = line.split()
            if len(parts) < 5:
                continue
            win_id, class_full = parts[0], parts[2]
            title = " ".join(parts[4:])
            if "steam_app_" in class_full and "EVE" in title and "Launcher" not in title:
                eve_windows.append((win_id, title))
        return eve_windows

    def capture_thumbnail(self, win_id, out_path):
        try:
            xwd_proc = subprocess.Popen(
                ["xwd", "-silent", "-id", win_id],
                stdout=subprocess.PIPE
            )
            subprocess.run(
                ["magick", "xwd:-", "-resize", THUMBNAIL_SIZE, out_path],
                stdin=xwd_proc.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=True
            )
            xwd_proc.stdout.close()
            return os.path.exists(out_path) and os.path.getsize(out_path) > 10000
        except Exception as e:
            print(f"Capture failed for {win_id}: {e}")
            return False

    def focus_window(self, win_id):
        subprocess.run(["wmctrl", "-ia", win_id])

    def update_thumbnails(self):
        current_windows = dict(self.get_eve_windows())

        # Remove closed windows
        for win_id in list(self.win_data.keys()):
            if win_id not in current_windows:
                self.win_data[win_id]["btn"].destroy()
                self.win_data[win_id]["label"].destroy()
                del self.win_data[win_id]

        # Update or create thumbnails
        for idx, (win_id, title) in enumerate(current_windows.items()):
            img_path = os.path.join(PREVIEW_DIR, f"{win_id}.png")

            self.capture_thumbnail(win_id, img_path)

            try:
                img = Image.open(img_path)
                thumb = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Image load failed for {win_id}: {e}")
                continue

            if win_id not in self.win_data:
                btn = tk.Button(self.root, image=thumb,
                                command=lambda wid=win_id: self.focus_window(wid))
                btn.image = thumb
                btn.grid(row=idx // 3 * 2, column=idx % 3)

                label = tk.Label(self.root, text=title[:30])
                label.grid(row=idx // 3 * 2 + 1, column=idx % 3)

                self.win_data[win_id] = {
                    "btn": btn,
                    "label": label,
                }
            else:
                self.win_data[win_id]["btn"].config(image=thumb)
                self.win_data[win_id]["btn"].image = thumb

        self.root.after(UPDATE_INTERVAL, self.update_thumbnails)

if __name__ == "__main__":
    root = tk.Tk()
    app = EvePreviewApp(root)
    root.mainloop()
