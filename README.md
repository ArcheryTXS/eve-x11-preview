# 🪞 EVE Online X11 Window Preview

Attemnt to create linux alternative eve-o-preview 
for multiboxing control in EvE Online
https://www.eveonline.com/

Using simple linux tools, general idea of window managing plus some Ai help for coding (and this summary)

This probably will work with any open window if you tweak
and change search from "EVE" to anything else ))


## 🛠️ Tools Used

### 🐍 Python (Standard + External Libraries)
| Library    | Purpose                                           |
|------------|---------------------------------------------------|
| `tkinter`  | GUI to show thumbnails and handle click           |
| `Pillow`   | Resize and process window preview images          |
| `subprocess` | Run CLI tools like `xwd`, `xdotool`, `xwininfo` |
| `threading`, `os`, `time`, `tempfile` | Window management      |

### 🧰 Linux CLI Tools (X11-native)
| Tool                             | Purpose                                  |
| -------------------------------- | ---------------------------------------- |
| `xwininfo`                       | Find windows matching "EVE" pattern      |
| `xwd`                            | Dump raw screenshots of specific windows |
| `ImageMagick` (`magick convert`) | Convert `.xwd` to `.png` for GUI display |
| `xdotool`                        | Raise/focus the clicked window           |


## 🚀 Setup & Usage

Clone the repo:

    git clone https://github.com/ArcheryTXS/eve-x11-preview.git
    cd eve-x11-preview

Make sure required packages are installed (see above)

Run the script:

    python eve-x11-preview.py

 Or chmod it
    
    chmod +x eve-x11-preview.py
    ./eve-x11-preview.py

#### 💡 You can change the refresh rate (default 2 seconds) by editing the constant inside the script.
#### 💡 Manually set "Above all windows" if it fails to do by script

   
## ⚙️ How It Works

- Script scans open X11 windows via xwininfo
- Filters windows with "EVE" in the name but excludes "EVE Launcher"
- Captures each game window using xwd, converts via magick convert
- Displays preview in a small tkinter window
- Background thread refreshes preview every 2 seconds (adjustable)
- Clicking a preview uses xdotool to bring the real window to the front

## ⚠️ Known Issues & Limitations

- Same picture preview for all open window for period of time before refresh catches up
- Previews may flicker briefly during refresh (due to image reloading)
- Not a true "live feed" — it's periodic screenshots
- Requires X11 (not compatible with Wayland)
- No layout customization yet (defaults to a vertical stack)

## 🧭 Future Improvements

- Add instalation script to check for needed libs and tools
- Better refresh/alternatives
- Smarter layout/grid preview positioning
- Add CLI flags for refresh rate, window match pattern, size
- Optional support for per-window process names (Steam/Proton helper)
- Better performance with caching


Created by ArcheryTXS 

Inspired by similar idea of u/Fitzsimmons - https://codeberg.org/JSFitzsimmons/eve-k-preview
