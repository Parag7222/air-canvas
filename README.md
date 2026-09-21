# 🖐️ AI Air Canvas & Virtual Painter

Draw anything in thin air using your fingers! Powered by Computer Vision, OpenCV, and MediaPipe Hand Tracking.

---

## 🚀 Quick Start

### Option 1: Native Desktop App (Python)

1. Make sure your webcam is plugged in and accessible.
2. Run the application:
   ```cmd
   cd C:\Users\parag\.gemini\antigravity\scratch\air_canvas
   python virtual_painter.py
   ```
   *Alternatively, double click `run.bat`.*

### Option 2: Web Browser App (Zero Installation)

1. Open `web/index.html` in **Google Chrome**, **Microsoft Edge**, or any modern browser:
   - Path: `C:\Users\parag\.gemini\antigravity\scratch\air_canvas\web\index.html`
2. Allow webcam permission when prompted.
3. Draw directly in the browser!

---

## ✋ Hand Gestures & Controls

| Gesture | Mode | Description |
| :--- | :--- | :--- |
| ☝️ **1 Finger (Index Only)** | **Draw Mode** | Draw freehand with the selected color and brush size |
| ✌️ **2 Fingers (Index + Middle)** | **Selection / Hover Mode** | Move cursor to select colors, eraser, or clear button on top bar |
| ✊ **Fist / Closed Hand** | **Pause Mode** | Disables drawing so you can reposition your hand freely |
| ✋ **Open Palm (5 Fingers)** | **Quick Wipe / Hover** | Hover without drawing |

---

## ⌨️ Keyboard Shortcuts (Desktop App)

| Key | Action |
| :---: | :--- |
| `W` | **Toggle Whiteboard**: Switch between drawing over camera feed and a crisp whiteboard |
| `S` | **Save Artwork**: Saves a high-res PNG image into the `output/` folder |
| `C` | **Clear Canvas**: Clears all current drawings |
| `+` / `-` | **Brush Size**: Increase or decrease the stroke width |
| `Q` / `ESC` | **Quit Application** |

---

## 🛠️ Project Structure

```
air_canvas/
├── hand_tracker.py       # Modular MediaPipe hand tracking & gesture analyzer
├── virtual_painter.py    # Main desktop painter application
├── requirements.txt      # Python dependencies (opencv-python, mediapipe, numpy)
├── run.bat               # Windows 1-click launcher
├── README.md             # Documentation and gesture guide
├── output/               # Saved drawings (created automatically on save)
└── web/
    └── index.html        # Zero-install standalone browser edition
```
