"""
AI-IN Peter — Auto Player
Two modes:
  1. CALIBRATED: User clicks each button once to save positions (reliable)
  2. MANUAL: Peter just advises, you click (default)

The old approach of asking GPT for pixel coordinates doesn't work —
vision models can't accurately report pixel positions.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional, Tuple

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
    pyautogui.PAUSE = 0.15
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    from pynput import mouse as pynput_mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

# Saved button positions file
POSITIONS_FILE = Path(__file__).parent.parent / "data" / "button_positions.json"


class AutoPlayer:
    def __init__(self):
        self.enabled = os.getenv("AUTO_PLAY", "false").lower() == "true"
        self.click_delay = float(os.getenv("AUTO_PLAY_DELAY", "0.5"))
        self.last_action_time = 0
        self.min_action_interval = 0.5  # Min time between clicks
        self.positions: dict[str, list[int]] = {}
        self.calibrating: Optional[str] = None  # Which button we're calibrating

        # Load saved positions
        self._load_positions()

    def is_available(self) -> bool:
        return HAS_PYAUTOGUI and self.enabled and len(self.positions) > 0

    def _load_positions(self):
        """Load calibrated button positions from disk."""
        try:
            if POSITIONS_FILE.exists():
                with open(POSITIONS_FILE) as f:
                    self.positions = json.load(f)
                print(f"[AutoPlay] Loaded {len(self.positions)} button positions")
        except Exception as e:
            print(f"[AutoPlay] Could not load positions: {e}")

    def _save_positions(self):
        """Save button positions to disk."""
        try:
            os.makedirs(POSITIONS_FILE.parent, exist_ok=True)
            with open(POSITIONS_FILE, "w") as f:
                json.dump(self.positions, f, indent=2)
            print(f"[AutoPlay] Saved {len(self.positions)} button positions")
        except Exception as e:
            print(f"[AutoPlay] Could not save positions: {e}")

    def save_position(self, button_name: str, x: int, y: int):
        """Save a button position."""
        self.positions[button_name.lower()] = [x, y]
        self._save_positions()

    async def wait_for_click(self, button_name: str) -> Optional[Tuple[int, int]]:
        """
        Wait for exactly 1 mouse click, save position, stop immediately.
        Returns (x, y) of where the user clicked.
        """
        if not HAS_PYNPUT:
            return None

        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def on_click(x, y, button, pressed):
            if pressed and button == pynput_mouse.Button.left:
                if not future.done():
                    loop.call_soon_threadsafe(future.set_result, (x, y))
                return False  # Stop listener after 1 click

        listener = pynput_mouse.Listener(on_click=on_click)
        listener.start()

        try:
            coords = await asyncio.wait_for(future, timeout=15.0)
            listener.stop()  # Ensure listener is fully stopped
            x, y = coords
            self.positions[button_name.lower()] = [x, y]
            self._save_positions()
            self.calibrating = None
            return (x, y)
        except asyncio.TimeoutError:
            listener.stop()
            self.calibrating = None
            return None

    def get_calibration_status(self, game_mode: str = "poker") -> dict:
        """Get which buttons have been calibrated."""
        if game_mode == "blackjack":
            needed = ["chip", "bet", "hit", "stand", "double", "split"]
        else:
            needed = ["ante", "play", "fold"]
        return {
            btn: btn in self.positions
            for btn in needed
        }

    async def execute_action(self, action: str, game_state: dict = None) -> bool:
        """Click the button for the given action using calibrated positions."""
        if not self.is_available():
            return False

        now = time.time()
        if now - self.last_action_time < self.min_action_interval:
            return False

        # Map action to button names (all lowercase keys)
        button_map = {
            # Poker
            "fold": ["fold"],
            "call": ["play", "call"],
            "raise": ["play", "raise"],
            "ante": ["ante"],
            # Blackjack
            "hit": ["hit"],
            "stand": ["stand"],
            "double": ["double"],
            "double_stand": ["double"],
            "split": ["split"],
            "bet": ["bet"],
            "chip": ["chip"],
        }

        targets = button_map.get(action.lower(), [])

        for btn_name in targets:
            if btn_name in self.positions:
                pos = self.positions[btn_name]
                success = await self._click_at(pos[0], pos[1], btn_name)
                if success:
                    self.last_action_time = time.time()
                    return True

        return False

    async def _click_at(self, x: int, y: int, label: str = "") -> bool:
        """Click at calibrated coordinates."""
        try:
            await asyncio.sleep(self.click_delay)
            await asyncio.to_thread(pyautogui.click, x, y)
            print(f"[AutoPlay] Clicked '{label}' at ({x}, {y})")
            return True
        except Exception as e:
            print(f"[AutoPlay] Click error: {e}")
            return False

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_delay(self, delay: float):
        self.click_delay = max(0.1, min(3.0, delay))

    def update_button_positions(self, positions: dict):
        """Update positions from external source (NOT from vision — that's unreliable)."""
        for btn, pos in positions.items():
            if isinstance(pos, list) and len(pos) == 2:
                self.positions[btn.lower()] = pos
        self._save_positions()
