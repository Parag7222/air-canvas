import os
import time
from datetime import datetime
import cv2
import numpy as np
from hand_tracker import HandTracker

# ----------------- Configuration & Palette -----------------
WINDOW_NAME = "AI Air Canvas - Virtual Painter"
CAM_WIDTH = 1280
CAM_HEIGHT = 720
HEADER_HEIGHT = 100

# BGR color definitions
PALETTE = {
    "Red": (50, 50, 240),
    "Blue": (240, 150, 30),
    "Green": (50, 220, 50),
    "Yellow": (30, 230, 240),
    "Purple": (230, 50, 200),
    "White": (255, 255, 255)
}

COLOR_KEYS = list(PALETTE.keys())
DEFAULT_COLOR_NAME = "Red"
DEFAULT_BRUSH_THICKNESS = 8
DEFAULT_ERASER_THICKNESS = 45

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class VirtualPainter:
    def __init__(self):
        self.tracker = HandTracker()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

        # Drawing state
        self.current_color_name = DEFAULT_COLOR_NAME
        self.current_color = PALETTE[self.current_color_name]
        self.brush_thickness = DEFAULT_BRUSH_THICKNESS
        self.eraser_thickness = DEFAULT_ERASER_THICKNESS
        self.is_eraser = False
        self.whiteboard_mode = False

        self.prev_x = 0
        self.prev_y = 0

        self.canvas = None
        self.notification_text = ""
        self.notification_expiry = 0

        # UI Toolbar button bounds: list of (name, (x1, y1, x2, y2), color_bgr)
        self.buttons = []

    def set_notification(self, text, duration_sec=2.0):
        self.notification_text = text
        self.notification_expiry = time.time() + duration_sec

    def setup_ui_layout(self, width):
        """Precomputes button positions for the header toolbar."""
        self.buttons = []
        # Margins & sizing
        btn_y1 = 15
        btn_y2 = HEADER_HEIGHT - 15
        btn_w = 90
        btn_h = btn_y2 - btn_y1
        spacing = 15
        start_x = 30

        # Color buttons
        x = start_x
        for name in COLOR_KEYS:
            self.buttons.append({
                "type": "color",
                "name": name,
                "rect": (x, btn_y1, x + btn_w, btn_y2),
                "color": PALETTE[name]
            })
            x += btn_w + spacing

        # Separator gap
        x += 20

        # Eraser button
        self.buttons.append({
            "type": "eraser",
            "name": "Eraser",
            "rect": (x, btn_y1, x + btn_w + 10, btn_y2),
            "color": (80, 80, 80)
        })
        x += btn_w + 10 + spacing

        # Clear All button
        self.buttons.append({
            "type": "clear",
            "name": "Clear",
            "rect": (x, btn_y1, x + btn_w + 10, btn_y2),
            "color": (50, 50, 180)
        })
        x += btn_w + 10 + spacing

        # Brush size down button
        self.buttons.append({
            "type": "size_down",
            "name": "Size -",
            "rect": (x, btn_y1, x + 70, btn_y2),
            "color": (60, 60, 60)
        })
        x += 70 + spacing

        # Brush size up button
        self.buttons.append({
            "type": "size_up",
            "name": "Size +",
            "rect": (x, btn_y1, x + 70, btn_y2),
            "color": (60, 60, 60)
        })

    def draw_header(self, frame):
        """Draws a modern translucent top toolbar overlay."""
        h, w, _ = frame.shape
        if not self.buttons:
            self.setup_ui_layout(w)

        # Translucent dark header bar
        header_overlay = frame.copy()
        cv2.rectangle(header_overlay, (0, 0), (w, HEADER_HEIGHT), (25, 25, 35), -1)
        cv2.addWeighted(header_overlay, 0.85, frame, 0.15, 0, frame)

        # Draw border line under header
        cv2.line(frame, (0, HEADER_HEIGHT), (w, HEADER_HEIGHT), (70, 70, 90), 2)

        # Draw buttons
        for btn in self.buttons:
            x1, y1, x2, y2 = btn["rect"]
            btype = btn["type"]
            name = btn["name"]

            # Highlight active tool
            is_active = False
            if btype == "color" and not self.is_eraser and name == self.current_color_name:
                is_active = True
            elif btype == "eraser" and self.is_eraser:
                is_active = True

            # Button background
            btn_bg = btn["color"]
            if btype in ["color"]:
                cv2.rectangle(frame, (x1, y1), (x2, y2), btn_bg, -1, cv2.LINE_AA)
            else:
                bg = (80, 120, 200) if is_active else btn_bg
                cv2.rectangle(frame, (x1, y1), (x2, y2), bg, -1, cv2.LINE_AA)

            # Border
            border_color = (255, 255, 255) if is_active else (100, 100, 120)
            border_thickness = 3 if is_active else 1
            cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, border_thickness, cv2.LINE_AA)

            # Label text
            text_color = (20, 20, 20) if (name in ["White", "Yellow"] and btype == "color") else (255, 255, 255)
            font_scale = 0.55
            (tw, th), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
            tx = x1 + (x2 - x1 - tw) // 2
            ty = y1 + (y2 - y1 + th) // 2
            cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 1, cv2.LINE_AA)

        # Current Size Indicator
        size_label = f"Size: {self.brush_thickness}px"
        cv2.putText(frame, size_label, (w - 180, HEADER_HEIGHT // 2 + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 230, 255), 1, cv2.LINE_AA)

    def draw_hud_info(self, frame, mode_str, fps):
        """Draws status badges at the bottom of the screen."""
        h, w, _ = frame.shape

        # Translucent HUD bar at bottom
        bar_y = h - 45
        cv2.rectangle(frame, (0, bar_y), (w, h), (20, 20, 25), -1)
        cv2.line(frame, (0, bar_y), (w, bar_y), (60, 60, 75), 1)

        # Mode status
        cv2.putText(frame, f"Mode: {mode_str}", (25, h - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 150), 2, cv2.LINE_AA)

        # Hotkey guide
        guide_text = "[W] Board  [S] Save  [C] Clear  [+/-] Size  [Q] Quit"
        cv2.putText(frame, guide_text, (280, h - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 200, 210), 1, cv2.LINE_AA)

        # FPS
        cv2.putText(frame, f"FPS: {fps:0.1f}", (w - 130, h - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 200, 255), 1, cv2.LINE_AA)

        # Notification message
        if time.time() < self.notification_expiry:
            (nw, nh), _ = cv2.getTextSize(self.notification_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            nx = (w - nw) // 2
            ny = h - 65
            cv2.rectangle(frame, (nx - 15, ny - nh - 10), (nx + nw + 15, ny + 10), (10, 80, 20), -1)
            cv2.rectangle(frame, (nx - 15, ny - nh - 10), (nx + nw + 15, ny + 10), (50, 220, 100), 2)
            cv2.putText(frame, self.notification_text, (nx, ny),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    def handle_selection(self, x, y):
        """Processes button clicks in selection mode."""
        for btn in self.buttons:
            x1, y1, x2, y2 = btn["rect"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                btype = btn["type"]
                name = btn["name"]

                if btype == "color":
                    self.is_eraser = False
                    self.current_color_name = name
                    self.current_color = PALETTE[name]
                    self.set_notification(f"Color: {name}", 1.2)
                elif btype == "eraser":
                    self.is_eraser = True
                    self.set_notification("Eraser Active", 1.2)
                elif btype == "clear":
                    if self.canvas is not None:
                        self.canvas[:] = 0
                    self.set_notification("Canvas Cleared!", 1.2)
                elif btype == "size_down":
                    self.brush_thickness = max(2, self.brush_thickness - 2)
                    self.set_notification(f"Brush: {self.brush_thickness}px", 1.0)
                elif btype == "size_up":
                    self.brush_thickness = min(60, self.brush_thickness + 2)
                    self.set_notification(f"Brush: {self.brush_thickness}px", 1.0)
                break

    def save_drawing(self, frame_to_save):
        """Saves current painting to output folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"air_canvas_{timestamp}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        cv2.imwrite(filepath, frame_to_save)
        self.set_notification(f"Saved: {filename}", 2.5)
        print(f"[VirtualPainter] Artwork saved to: {filepath}")

    def run(self):
        if not self.cap.isOpened():
            print("[Error] Could not open webcam. Please verify your camera is connected.")
            return

        print("\n=======================================================")
        print("          AI Air Canvas - Virtual Painter")
        print("=======================================================")
        print("  Controls:")
        print("    1 Finger (Index)        -> Draw")
        print("    2 Fingers (Index+Middle) -> Hover / Select Tools")
        print("    Fist / Hand Closed      -> Pause")
        print("    [W] Toggle Whiteboard mode")
        print("    [S] Save Artwork snapshot")
        print("    [C] Clear Canvas")
        print("    [+/-] Adjust brush thickness")
        print("    [Q / ESC] Quit")
        print("=======================================================\n")

        prev_time = time.time()
        fps = 30.0

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[Warning] Failed to grab frame from camera.")
                break

            # Mirror frame horizontally for intuitive interaction
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Initialize canvas if needed
            if self.canvas is None or self.canvas.shape != frame.shape:
                self.canvas = np.zeros_like(frame)

            # Compute FPS
            cur_time = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(0.001, cur_time - prev_time))
            prev_time = cur_time

            # Hand tracking
            landmarks = self.tracker.process_frame(frame)
            fingers = self.tracker.get_fingers_up(landmarks)

            mode_str = "No Hand"

            if len(landmarks) >= 21:
                # Landmark 8: Index tip, Landmark 12: Middle tip
                x_index, y_index = landmarks[8]
                x_middle, y_middle = landmarks[12]

                is_index_up = fingers[1]
                is_middle_up = fingers[2]

                # Draw subtle skeleton on frame
                self.tracker.draw_skeleton(frame, landmarks)

                # State 1: SELECTION / HOVER MODE (Both Index & Middle fingers up)
                if is_index_up and is_middle_up:
                    mode_str = "Selecting / Hover"
                    self.prev_x, self.prev_y = 0, 0

                    mid_x = (x_index + x_middle) // 2
                    mid_y = (y_index + y_middle) // 2

                    # Draw selection cursor
                    cv2.circle(frame, (mid_x, mid_y), 14, (240, 180, 50), 2, cv2.LINE_AA)
                    cv2.circle(frame, (mid_x, mid_y), 6, (240, 180, 50), -1, cv2.LINE_AA)

                    # Check button interactions
                    if mid_y < HEADER_HEIGHT:
                        self.handle_selection(mid_x, mid_y)

                # State 2: DRAWING MODE (Index finger up only)
                elif is_index_up and not is_middle_up:
                    mode_str = "Erasing" if self.is_eraser else "Drawing"

                    # Fingertip visual indicator
                    cursor_color = (255, 255, 255) if self.is_eraser else self.current_color
                    cursor_rad = self.eraser_thickness // 2 if self.is_eraser else self.brush_thickness
                    cv2.circle(frame, (x_index, y_index), cursor_rad, cursor_color, -1, cv2.LINE_AA)

                    # Avoid drawing in header area
                    if y_index > HEADER_HEIGHT:
                        if self.prev_x == 0 and self.prev_y == 0:
                            self.prev_x, self.prev_y = x_index, y_index

                        # Draw stroke
                        if self.is_eraser:
                            cv2.line(self.canvas, (self.prev_x, self.prev_y), (x_index, y_index),
                                     (0, 0, 0), self.eraser_thickness, cv2.LINE_AA)
                        else:
                            cv2.line(self.canvas, (self.prev_x, self.prev_y), (x_index, y_index),
                                     self.current_color, self.brush_thickness, cv2.LINE_AA)

                        self.prev_x, self.prev_y = x_index, y_index
                    else:
                        self.prev_x, self.prev_y = 0, 0

                # State 3: PAUSED / IDLE (Fist or other fingers)
                else:
                    mode_str = "Paused (Fist)"
                    self.prev_x, self.prev_y = 0, 0
            else:
                self.prev_x, self.prev_y = 0, 0

            # Composite Drawing Canvas onto Output Frame
            # Create binary mask of the canvas
            canvas_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, mask_inv = cv2.threshold(canvas_gray, 10, 255, cv2.THRESH_BINARY_INV)

            if self.whiteboard_mode:
                # White background canvas
                display_frame = np.full_like(frame, 255)
                display_frame = cv2.bitwise_and(display_frame, display_frame, mask=mask_inv)
                display_frame = cv2.bitwise_or(display_frame, self.canvas)
            else:
                # Augmented reality webcam blend
                display_frame = cv2.bitwise_and(frame, frame, mask=mask_inv)
                display_frame = cv2.bitwise_or(display_frame, self.canvas)

            # Draw Toolbar Header & HUD
            self.draw_header(display_frame)
            self.draw_hud_info(display_frame, mode_str, fps)

            cv2.imshow(WINDOW_NAME, display_frame)

            # Key controls
            key = cv2.waitKey(1) & 0xFF
            if key in [ord('q'), ord('Q'), 27]:  # Q or ESC
                print("[VirtualPainter] Closing application...")
                break
            elif key in [ord('c'), ord('C')]:
                self.canvas[:] = 0
                self.set_notification("Canvas Cleared!", 1.2)
            elif key in [ord('w'), ord('W')]:
                self.whiteboard_mode = not self.whiteboard_mode
                mode_name = "Whiteboard" if self.whiteboard_mode else "Webcam Overlay"
                self.set_notification(f"Switched to: {mode_name}", 1.5)
            elif key in [ord('s'), ord('S')]:
                self.save_drawing(display_frame)
            elif key in [ord('+'), ord('=')]:
                self.brush_thickness = min(60, self.brush_thickness + 2)
                self.set_notification(f"Brush: {self.brush_thickness}px", 1.0)
            elif key in [ord('-'), ord('_')]:
                self.brush_thickness = max(2, self.brush_thickness - 2)
                self.set_notification(f"Brush: {self.brush_thickness}px", 1.0)

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = VirtualPainter()
    app.run()
