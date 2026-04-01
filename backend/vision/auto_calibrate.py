"""
Auto-calibration: detect the casino game region on screen.
Finds the green felt table area and sets the game region automatically.
Also provides a manual calibration endpoint for the overlay.
"""

import cv2
import numpy as np
import mss
from typing import Optional
from pathlib import Path
import json


def detect_game_region(monitor_index: int = 1) -> Optional[dict]:
    """Auto-detect the casino game region by finding the green felt table.
    Returns {"x": int, "y": int, "w": int, "h": int} or None.
    """
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            if monitor_index >= len(monitors):
                monitor_index = 1
            monitor = monitors[monitor_index]
            screenshot = sct.grab(monitor)

            img = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(
                screenshot.height, screenshot.width, 4
            )
            bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

            # Green felt: H=35-85, S>30, V>30
            mask = cv2.inRange(hsv, np.array([35, 30, 30]), np.array([85, 255, 255]))

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None

            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            screen_area = screenshot.width * screenshot.height
            if area < screen_area * 0.05:
                return None

            x, y, w, h = cv2.boundingRect(largest)

            # Expand to include the full casino window:
            # - Above: dealer area (~60% of felt height above the table)
            # - Below: buttons/balance (~30% below)
            # - Sides: small margin
            expand_top = int(h * 0.7)
            expand_bottom = int(h * 0.4)
            expand_side = 20

            x = max(0, x - expand_side)
            y = max(0, y - expand_top)
            w = min(screenshot.width - x, w + expand_side * 2)
            h = min(screenshot.height - y, h + expand_top + expand_bottom)

            return {"x": x, "y": y, "w": w, "h": h}

    except Exception as e:
        print(f"[AutoCalibrate] Error: {e}")
        return None


def save_zones(zones: dict, filepath: str = None):
    """Save calibrated zones to JSON file."""
    if filepath is None:
        filepath = str(Path(__file__).parent.parent / "data" / "calibrated_zones.json")
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    Path(filepath).write_text(json.dumps(zones, indent=2))
    print(f"[Calibrate] Saved zones to {filepath}")


def load_zones(filepath: str = None) -> Optional[dict]:
    """Load calibrated zones from JSON file."""
    if filepath is None:
        filepath = str(Path(__file__).parent.parent / "data" / "calibrated_zones.json")
    try:
        if Path(filepath).exists():
            return json.loads(Path(filepath).read_text())
    except Exception:
        pass
    return None


if __name__ == "__main__":
    # Run auto-detection
    region = detect_game_region()
    if region:
        print(f"Detected game region: {region}")
        print(f"Update your .env with:")
        print(f"  GAME_REGION_X={region['x']}")
        print(f"  GAME_REGION_Y={region['y']}")
        print(f"  GAME_REGION_W={region['w']}")
        print(f"  GAME_REGION_H={region['h']}")
    else:
        print("Could not detect game region. Make sure the casino is visible on screen.")
