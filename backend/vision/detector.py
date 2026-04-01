"""
Vision Module — Game State Detector
Captures screenshots and uses AI vision (GPT-4o/Claude) to parse the poker table.
Optimized for Solcasino.io Casino Hold'em by Pragmatic Play.
"""

import base64
import io
import json
import os
import time
import zlib
from typing import Optional

import cv2
import mss
import mss.tools
import numpy as np
from PIL import Image


class GameStateDetector:
    def __init__(self):
        self.provider = os.getenv("VISION_PROVIDER", "openai").lower()
        self.monitor_index = int(os.getenv("MONITOR_INDEX", "1"))
        self.crop_region = None
        self._last_screenshot_hash: Optional[str] = None
        self._last_capture_time: float = 0
        self._last_game_state: Optional[dict] = None
        self._last_face: Optional[tuple] = None  # (x, y, w, h) of dealer face
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        # Card identity cache: maps (x//20, y//20) → card name (e.g. "Ah")
        self._card_id_cache: dict[tuple, str] = {}
        # Load calibrated zones if saved
        self._load_calibrated_zones()
        self._init_client()

    def _load_calibrated_zones(self):
        """Load zone positions from calibrated_zones.json if it exists."""
        from pathlib import Path
        zones_file = Path(__file__).parent.parent / "data" / "calibrated_zones.json"
        if zones_file.exists():
            try:
                import json as json_mod
                data = json_mod.loads(zones_file.read_text())
                for zone_name, coords in data.items():
                    if zone_name in self.TABLE_ZONES:
                        self.TABLE_ZONES[zone_name]["region_x"] = coords["x"]
                        self.TABLE_ZONES[zone_name]["region_y"] = coords["y"]
                        self.TABLE_ZONES[zone_name]["region_w"] = coords["w"]
                        self.TABLE_ZONES[zone_name]["region_h"] = coords["h"]
                print(f"[Vision] Loaded calibrated zones: {list(data.keys())}")
            except Exception as e:
                print(f"[Vision] Could not load calibrated zones: {e}")

    def _init_client(self):
        if self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("VISION_MODEL", "claude-sonnet-4-20250514")
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("VISION_MODEL", "gpt-4o-mini")
        else:
            raise ValueError(f"Unknown vision provider: {self.provider}")

    def capture_screen(self) -> Optional[str]:
        """Capture screenshot. Returns base64-encoded JPEG."""
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                if self.monitor_index >= len(monitors):
                    self.monitor_index = 1

                monitor = monitors[self.monitor_index]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                if self.crop_region:
                    img = img.crop(self.crop_region)

                # Resize — 768px balances speed vs card readability
                max_width = 768
                if img.width > max_width:
                    ratio = max_width / img.width
                    img = img.resize((max_width, int(img.height * ratio)), Image.BILINEAR)

                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=70)
                img_bytes = buffer.getvalue()

                # Quick hash to detect if screen actually changed (CRC32 faster than MD5)
                img_hash = zlib.crc32(img_bytes)
                if img_hash == self._last_screenshot_hash:
                    return None  # Screen hasn't changed, skip API call

                self._last_screenshot_hash = img_hash
                self._last_capture_time = time.time()
                return base64.b64encode(img_bytes).decode("utf-8")

        except Exception as e:
            print(f"[Vision] Screen capture error: {e}")
            return None

    def force_next_capture(self):
        """Reset hash so next capture is always sent to API."""
        self._last_screenshot_hash = None

    async def detect_game_state(self, screenshot_b64: str) -> Optional[dict]:
        """Send screenshot to AI vision and extract game state."""
        prompt = self._build_prompt()

        try:
            if self.provider == "anthropic":
                return await self._detect_anthropic(screenshot_b64, prompt)
            elif self.provider == "openai":
                return await self._detect_openai(screenshot_b64, prompt)
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "authentication" in error_str.lower():
                raise
            print(f"[Vision] Detection error: {e}")
            return None

    async def read_cards_fast(self, strip_b64: str, num_total: int, num_from_mesa: int = 0) -> Optional[dict]:
        """Fast card reading from a cropped card strip. ~400ms with gpt-4o-mini.

        In Casino Hold'em, the PLAYER display shows ALL visible cards (2 hole + community).
        The first 2 are always the player's hole cards, the rest are community cards.
        """
        prompt = f"""This is Casino Hold'em. Read {num_total} poker cards in this image.
Look at the TOP-LEFT corner of each card for rank and suit.
Ranks: A,2,3,4,5,6,7,8,9,10,J,Q,K  Suits: h=hearts d=diamonds s=spades c=clubs

IMPORTANT: The first 2 cards are the player's HOLE cards. Any remaining cards are COMMUNITY cards.
Read left to right. Return ONLY this JSON:
{{"hole_cards":["Ah","Kd"],"community_cards":["5s","8c","Jh"]}}"""

        try:
            if self.provider == "openai":
                import asyncio
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    max_tokens=60,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{strip_b64}", "detail": "low"}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                return self._parse_response(response.choices[0].message.content)
            elif self.provider == "anthropic":
                import asyncio
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=60,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": strip_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                return self._parse_response(response.content[0].text)
        except Exception as e:
            print(f"[Vision] Fast read error: {e}")
            return None

    def identify_cards_from_screenshot(self, screenshot_bgra: bytes, size: tuple, card_regions: list[dict]) -> list[dict]:
        """Crop each face-up card, build a numbered grid image for LLM identification.
        Returns updated card_regions with 'card_name' field added.
        Also updates the card identity cache.
        """
        img = np.frombuffer(screenshot_bgra, dtype=np.uint8).reshape(size[1], size[0], 4)
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        face_up_cards = []
        for c in card_regions:
            if c.get("is_zone") or c.get("face") in ("tracker", "down"):
                continue
            if c.get("face") != "up":
                continue

            # Check cache — same position (within 20px) = same card
            cache_key = (c["x"] // 20, c["y"] // 20)
            if cache_key in self._card_id_cache:
                c["card_name"] = self._card_id_cache[cache_key]
                continue

            # Crop this card from image (coords relative to game region)
            x = max(0, c["x"])
            y = max(0, c["y"])
            w, h = c["w"], c["h"]
            if x + w > size[0]: w = size[0] - x
            if y + h > size[1]: h = size[1] - y
            if w <= 0 or h <= 0:
                continue

            crop = bgr[y:y+h, x:x+w]
            if crop.size == 0:
                continue

            # Resize to 100px tall for consistency
            card_h = 100
            ratio = card_h / crop.shape[0]
            card_w = max(1, int(crop.shape[1] * ratio))
            crop = cv2.resize(crop, (card_w, card_h))

            face_up_cards.append((c, crop, cache_key))

        # Label each card in the regions that have cached names
        # For uncached cards, we need to call LLM (done async in esp_loop)
        return face_up_cards

    def build_card_grid(self, card_crops: list) -> Optional[str]:
        """Build a numbered grid image from card crops for LLM identification.
        Returns base64 JPEG.
        """
        if not card_crops:
            return None

        crops = [crop for _, crop, _ in card_crops]

        # Build horizontal strip with numbered labels
        labeled = []
        for i, crop in enumerate(crops):
            # Add number label on top
            label = np.zeros((18, crop.shape[1], 3), dtype=np.uint8)
            cv2.putText(label, str(i + 1), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            labeled.append(np.vstack([label, crop]))

        # Pad all to same height
        max_h = max(l.shape[0] for l in labeled)
        padded = []
        for l in labeled:
            if l.shape[0] < max_h:
                pad = np.zeros((max_h - l.shape[0], l.shape[1], 3), dtype=np.uint8)
                l = np.vstack([l, pad])
            padded.append(l)
            # Small gap between cards
            padded.append(np.zeros((max_h, 4, 3), dtype=np.uint8))

        strip = np.hstack(padded[:-1])

        _, buf = cv2.imencode(".jpg", strip, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    async def identify_card_names(self, grid_b64: str, count: int) -> list[str]:
        """Send numbered card grid to LLM. Returns list of card names in order."""
        prompt = f"""These are {count} poker cards numbered 1-{count}.
For each card read the rank and suit from its face.
Format: Rank + suit letter (h=hearts, d=diamonds, s=spades, c=clubs)
Examples: Ah Kd 10s 5c Jh Qs 2d
Return ONLY a JSON array of {count} strings, e.g. ["Ah","Kd","10s"]"""

        try:
            import asyncio
            if self.provider == "openai":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    max_tokens=60,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{grid_b64}", "detail": "low"}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                text = response.choices[0].message.content
            elif self.provider == "anthropic":
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=60,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": grid_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                text = response.content[0].text
            else:
                return []

            # Parse JSON array
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            names = json.loads(cleaned)
            if isinstance(names, list):
                return [str(n) for n in names]
            return []

        except Exception as e:
            print(f"[Vision] Card identify error: {e}")
            return []

    def clear_card_cache(self):
        """Clear cached card identities (call on new hand)."""
        self._card_id_cache.clear()

    async def _detect_anthropic(self, screenshot_b64: str, prompt: str) -> Optional[dict]:
        import asyncio
        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": screenshot_b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return self._parse_response(response.content[0].text)

    async def _detect_openai(self, screenshot_b64: str, prompt: str) -> Optional[dict]:
        import asyncio
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}", "detail": "auto"}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return self._parse_response(response.choices[0].message.content)

    def _build_prompt(self) -> str:
        return """Casino Hold'em table (Pragmatic Play, Solcasino.io).

CARD LAYOUT:
- BOTTOM-LEFT: Player's cards displayed in a row (up to 5 cards face-up)
  - The FIRST 2 cards are the player's HOLE CARDS
  - The remaining cards (3rd, 4th, 5th) are COMMUNITY CARDS
- CENTER: Dealer's cards (usually face-down, red backs)
- The player display combines hole + community into one row

READ each card's rank and suit from the TOP-LEFT corner.
Ranks: A,2,3,4,5,6,7,8,9,10,J,Q,K
Suits: h=hearts(red) d=diamonds(red/blue) s=spades(black) c=clubs(black)

BALANCE: number at bottom-left after "$" symbol.

Return ONLY this JSON:
{"phase":"waiting","hole_cards":[],"community_cards":[],"balance":0,"buttons_visible":[]}

phase: "waiting" if no cards visible, "flop" if cards dealt
hole_cards: ONLY the first 2 player cards
community_cards: the 3rd/4th/5th cards (if visible)
balance: the dollar amount shown at bottom-left"""

    def _parse_response(self, text: str) -> Optional[dict]:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

            game_state = json.loads(cleaned)

            for field in ["phase", "hole_cards", "community_cards"]:
                if field not in game_state:
                    game_state[field] = [] if field != "phase" else "waiting"

            return game_state

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[Vision] Parse error: {e} — Raw: {text[:200]}")
            return None

    # ── Table zones — calibrated from foto3.png (909x791) ──────────────
    # Pragmatic Play Casino Hold'em layout:
    #   Face at y=18%, dealer/community cards at y=55%, player cards at y=82%
    #   Card shoe at x=75% y=50%, balance at bottom-left
    TABLE_ZONES = {
        "MESA": {
            "region_y": 0.46, "region_h": 0.18,
            "region_x": 0.15, "region_w": 0.70,
            "max_cards": 5, "color": "mesa", "detect_facedown": True,
        },
        "TUS CARTAS": {
            "region_y": 0.75, "region_h": 0.15,
            "region_x": 0.0, "region_w": 0.25,
            "max_cards": 5, "color": "player", "detect_facedown": False,
        },
        "SHOE": {
            "region_y": 0.45, "region_h": 0.16,
            "region_x": 0.72, "region_w": 0.22,
            "max_cards": 0, "color": "shoe", "detect_facedown": True,
        },
        "BALANCE": {
            "region_y": 0.90, "region_h": 0.04,
            "region_x": 0.0, "region_w": 0.10,
            "max_cards": 0, "color": "balance", "detect_facedown": False,
        },
    }

    def _detect_dealer_face(self, gray: np.ndarray, img_w: int, img_h: int) -> Optional[tuple]:
        """Detect the dealer's face. Returns (cx, cy, w, h) or None.
        Handles dealer changes by expiring stale cache after 30 frames without detection.
        """
        search_h = int(img_h * 0.55)
        roi = gray[:search_h, :]

        faces = self._face_cascade.detectMultiScale(
            roi, scaleFactor=1.1, minNeighbors=3,
            minSize=(int(img_w * 0.04), int(img_h * 0.04)),
            maxSize=(int(img_w * 0.45), int(img_h * 0.45)),
        )

        if len(faces) == 0:
            # Expire stale cache — don't use old dealer position forever
            self._face_miss_count = getattr(self, '_face_miss_count', 0) + 1
            if self._face_miss_count > 30:
                self._last_face = None  # Reset after ~2.5 sec of no detection
            return self._last_face

        self._face_miss_count = 0

        # Pick largest face, but prefer faces near center-x of image
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        best = faces[0]

        # If multiple faces, prefer the one closest to horizontal center
        if len(faces) > 1:
            center_x = img_w // 2
            best = min(faces[:3], key=lambda f: abs(f[0] + f[2] // 2 - center_x))

        fx, fy, fw, fh = best
        cx = fx + fw // 2
        cy = fy + fh // 2
        self._last_face = (cx, cy, fw, fh)
        return (cx, cy, fw, fh)

    def _find_cards_in_roi(self, hsv_roi: np.ndarray, detect_facedown: bool = False) -> list[tuple]:
        """Find card contours in an HSV ROI."""
        results = []

        # Face-up: white/light cards — broader threshold
        mask = cv2.inRange(hsv_roi, np.array([0, 0, 160]), np.array([180, 70, 255]))
        results += self._extract_cards(mask, "up")

        if detect_facedown:
            r1 = cv2.inRange(hsv_roi, np.array([0, 50, 40]), np.array([15, 255, 220]))
            r2 = cv2.inRange(hsv_roi, np.array([160, 50, 40]), np.array([180, 255, 220]))
            results += self._extract_cards(cv2.bitwise_or(r1, r2), "down")

        results.sort(key=lambda r: r[0])
        return results

    def _extract_cards(self, mask: np.ndarray, face: str) -> list[tuple]:
        """Extract card rectangles from binary mask."""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 600 or area > 40000:
                continue

            r = cv2.minAreaRect(cnt)
            rw, rh = r[1]
            if rw == 0 or rh == 0:
                continue
            if rw > rh:
                rw, rh = rh, rw
            aspect = rh / rw
            if aspect < 1.1 or aspect > 2.0:
                continue

            bx, by, bw, bh = cv2.boundingRect(cnt)
            rect_area = bw * bh
            if rect_area == 0:
                continue
            if area / rect_area < 0.60:
                continue
            # Min pixel size; face-up cards must be portrait, face-down can be landscape
            if bw < 18 or bh < 18:
                continue
            if face == "up" and bh < bw:
                continue

            rects.append((bx, by, bw, bh, face))

        return rects

    def _build_zones(self, img_w: int, img_h: int, face: Optional[tuple]) -> list[tuple]:
        """Build zone rectangles from TABLE_ZONES. Face X shifts dealer/mesa horizontally.
        Returns [(zone_name, zone_cfg, x, y, w, h), ...]
        """
        # If face detected, use it to shift X center for dealer/mesa zones
        face_cx = face[0] if face else img_w // 2

        zones = []
        for zname, zcfg in self.TABLE_ZONES.items():
            zy = int(zcfg["region_y"] * img_h)
            zh = int(zcfg["region_h"] * img_h)
            zw = int(zcfg["region_w"] * img_w)

            # Fixed position zones (poker player/shoe/balance + all blackjack zones)
            if zname in ("TUS CARTAS", "SHOE", "BALANCE", "DEALER", "PLAYER", "PLAYER_SPLIT"):
                zx = int(zcfg["region_x"] * img_w)
            else:
                # Mesa (poker): center on face X position
                zx = int(face_cx - zw // 2)

            zx = max(0, min(zx, img_w - zw))
            zy = max(0, min(zy, img_h - zh))
            zw = min(zw, img_w - zx)
            zh = min(zh, img_h - zy)

            if zw > 0 and zh > 0:
                zones.append((zname, zcfg, zx, zy, zw, zh))

        return zones

    # Balance region (bottom-left corner where balance is shown)
    BALANCE_REGION = (0.0, 0.92, 0.20, 0.08)

    def read_balance_ocr(self, screenshot_bgra: bytes, size: tuple) -> Optional[float]:
        """Read balance from the BALANCE zone using local OpenCV digit matching.
        No LLM needed. Runs in ~5-10ms.
        """
        from vision.balance_reader import read_balance_local
        try:
            img = np.frombuffer(screenshot_bgra, dtype=np.uint8).reshape(size[1], size[0], 4)
            bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img_h, img_w = bgr.shape[:2]

            zone = self.TABLE_ZONES["BALANCE"]
            zy = int(zone["region_y"] * img_h)
            zh = int(zone["region_h"] * img_h)
            zx = int(zone["region_x"] * img_w)
            zw = int(zone["region_w"] * img_w)

            roi = bgr[zy:zy+zh, zx:zx+zw]
            if roi.size == 0:
                return None

            return read_balance_local(roi)

        except Exception as e:
            print(f"[Vision] Balance read error: {e}")
            return None

    def read_balance_ocr_sync(self, screenshot_bgra: bytes, size: tuple) -> Optional[float]:
        """Sync alias for read_balance_ocr."""
        return self.read_balance_ocr(screenshot_bgra, size)

    @staticmethod
    def extract_balance_from_state(game_state: Optional[dict]) -> Optional[float]:
        """Extract balance from an existing detect_game_state / read_cards_fast result.
        Returns float or None if not present or zero.
        """
        if not game_state:
            return None
        bal = game_state.get("balance")
        if bal is not None:
            try:
                val = float(bal)
                return val if val > 0 else None
            except (ValueError, TypeError):
                return None
        return None

    def detect_card_regions(self, screenshot_bgra: bytes, size: tuple, crop_offset: tuple = (0, 0)) -> list[dict]:
        """Detect cards on the table. Uses face tracking when available, fixed zones as fallback."""
        img = np.frombuffer(screenshot_bgra, dtype=np.uint8).reshape(size[1], size[0], 4)
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        img_h, img_w = bgr.shape[:2]

        all_items = []

        # Try face detection
        face = self._detect_dealer_face(gray, img_w, img_h)

        # Add face tracker if found
        if face:
            fcx, fcy, fw, fh = face
            all_items.append({
                "x": int(fcx - fw // 2 + crop_offset[0]),
                "y": int(fcy - fh // 2 + crop_offset[1]),
                "w": int(fw), "h": int(fh),
                "zone": "face", "label": "DEALER",
                "is_zone": False, "face": "tracker",
            })

        # Build zones (face-anchored or fixed fallback)
        zones = self._build_zones(img_w, img_h, face)

        for zone_name, zcfg, zx, zy, zw, zh in zones:
            roi = hsv[zy:zy+zh, zx:zx+zw]
            if roi.size == 0:
                continue

            cards = self._find_cards_in_roi(roi, detect_facedown=zcfg.get("detect_facedown", False))
            cards = cards[:zcfg["max_cards"]]

            # SHOE and BALANCE: always show zone outline
            always_show = zone_name in ("SHOE", "BALANCE")

            if not cards and not always_show:
                continue

            all_items.append({
                "x": int(zx + crop_offset[0]),
                "y": int(zy + crop_offset[1]),
                "w": int(zw), "h": int(zh),
                "zone": zcfg["color"], "label": zone_name,
                "is_zone": True,
            })

            for bx, by, bw, bh, face_dir in cards:
                all_items.append({
                    "x": int(bx + zx + crop_offset[0]),
                    "y": int(by + zy + crop_offset[1]),
                    "w": int(bw), "h": int(bh),
                    "zone": zcfg["color"], "label": zone_name,
                    "face": face_dir,
                })

        return all_items

    def crop_cards_strip(self, screenshot_bgra: bytes, size: tuple, card_regions: list[dict]) -> Optional[str]:
        """Crop all face-up cards and compose a single row image for LLM reading.
        Cards are ordered left-to-right as they appear on screen.
        In Casino Hold'em the first 2 are hole cards, rest are community.
        """
        img = np.frombuffer(screenshot_bgra, dtype=np.uint8).reshape(size[1], size[0], 4)
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Collect all face-up cards sorted left to right
        cards = []
        for c in card_regions:
            if c.get("is_zone") or c.get("face") in ("tracker", "down"):
                continue
            if c.get("face") != "up":
                continue

            x, y = max(0, c["x"]), max(0, c["y"])
            w, h = c["w"], c["h"]
            if x + w > size[0]: w = size[0] - x
            if y + h > size[1]: h = size[1] - y
            if w <= 0 or h <= 0:
                continue

            crop = bgr[y:y+h, x:x+w]
            if crop.size == 0:
                continue

            # Resize to 200px tall
            card_h = 200
            ratio = card_h / crop.shape[0]
            card_w = max(1, int(crop.shape[1] * ratio))
            crop = cv2.resize(crop, (card_w, card_h), interpolation=cv2.INTER_LANCZOS4)
            cards.append((x, crop))

        if not cards:
            return None

        # Sort left to right
        cards.sort(key=lambda c: c[0])
        crops = [c[1] for c in cards]

        # Build single row with small gaps
        gap = np.zeros((200, 6, 3), dtype=np.uint8)
        parts = []
        for i, crop in enumerate(crops):
            if i > 0:
                parts.append(gap)
            parts.append(crop)

        strip = np.hstack(parts)

        # Add label
        label = np.zeros((28, strip.shape[1], 3), dtype=np.uint8)
        cv2.putText(label, f"{len(crops)} CARDS",
                    (4, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        strip = np.vstack([label, strip])

        _, buf = cv2.imencode(".jpg", strip, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    def capture_esp_only(self) -> tuple[list[dict], tuple, Optional[str]]:
        """Fast ESP capture + card strip for LLM reading."""
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                if self.monitor_index >= len(monitors):
                    self.monitor_index = 1
                monitor = monitors[self.monitor_index]

                if self.crop_region:
                    game_mon = {
                        "left": monitor["left"] + self.crop_region[0],
                        "top": monitor["top"] + self.crop_region[1],
                        "width": self.crop_region[2] - self.crop_region[0],
                        "height": self.crop_region[3] - self.crop_region[1],
                    }
                    shot = sct.grab(game_mon)
                else:
                    shot = sct.grab(monitor)

                size = (shot.width, shot.height)
                regions = self.detect_card_regions(shot.bgra, size, crop_offset=(0, 0))

                # Apply cached card names for ESP display
                for card in regions:
                    if card.get("face") == "up" and not card.get("is_zone"):
                        ck = (card["x"] // 20, card["y"] // 20)
                        if ck in self._card_id_cache:
                            card["card_name"] = self._card_id_cache[ck]

                # Build card strip for LLM — include ALL face-up cards (even cached)
                # The ESP loop decides when to trigger a new LLM read
                all_face_up = [c for c in regions if c.get("face") == "up" and not c.get("is_zone")]
                strip_b64 = self.crop_cards_strip(shot.bgra, size, regions) if all_face_up else None

                return regions, size, strip_b64

        except Exception as e:
            import traceback
            print(f"[Vision] ESP capture error: {e}")
            traceback.print_exc()
            return [], (0, 0), None

    def set_table_zones(self, zones: dict):
        """Swap table zones (e.g., switch between poker and blackjack layouts)."""
        self.TABLE_ZONES = zones
        self.clear_card_cache()
        self.force_next_capture()

    async def read_blackjack_cards_fast(self, strip_b64: str, num_player: int = 0, num_dealer: int = 0) -> dict | None:
        """Read blackjack cards from a card strip. Returns dealer + player cards."""
        total = num_player + num_dealer
        prompt = f"""This is Evolution Infinite Blackjack (live dealer, Solcasino.io).
Read {total} cards in this image.
Look at the TOP-LEFT corner of each card for rank and suit.
Ranks: A,2,3,4,5,6,7,8,9,10,J,Q,K  Suits: h=hearts d=diamonds s=spades c=clubs

LAYOUT: DEALER cards are at the TOP (smaller, on the green felt).
PLAYER cards are at the BOTTOM (larger, closer to camera).
If a card is face-down (red/blue back), report it as "XX".
Return ONLY this JSON:
{{"dealer_cards":["10h","XX"],"player_cards":["Ah","Kd"]}}"""

        try:
            import asyncio
            if self.provider == "openai":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    max_tokens=80,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{strip_b64}", "detail": "low"}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                return self._parse_response(response.choices[0].message.content)
            elif self.provider == "anthropic":
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=80,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": strip_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                return self._parse_response(response.content[0].text)
        except Exception as e:
            print(f"[Vision] Blackjack fast read error: {e}")
            return None

    def set_crop_region(self, x: int, y: int, w: int, h: int):
        self.crop_region = (x, y, x + w, y + h)

    def clear_crop_region(self):
        self.crop_region = None
