"""
Local Card Reader — Contour Feature Matching
Reads card rank + suit from cropped card images using OpenCV.
No LLM needed. Runs in <5ms per card.

Strategy:
1. Upscale the card crop 4x for better feature extraction
2. Threshold to isolate symbols on white card background
3. Suit: detect by color (red/blue = hearts/diamonds, black = spades/clubs)
4. Rank: use Hu moments (scale-invariant) + aspect ratio + pixel density
5. Templates auto-captured from first clear card reading
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
from typing import Optional

RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
SUITS = ['s', 'h', 'd', 'c']

# Template storage
TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "card_templates"
_rank_features: dict[str, list] = {}  # rank -> list of Hu moment vectors
_loaded = False


def _ensure_templates_dir():
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def _compute_contour_features(binary: np.ndarray) -> Optional[dict]:
    """Extract features from a binary image of a rank/suit symbol."""
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Use all contours together
    all_pts = np.vstack(contours)
    x, y, w, h = cv2.boundingRect(all_pts)
    if w == 0 or h == 0:
        return None

    roi = binary[y:y+h, x:x+w]
    if roi.size == 0:
        return None

    # Normalize to fixed size for consistent features
    norm = cv2.resize(roi, (20, 28), interpolation=cv2.INTER_NEAREST)

    # Hu moments (scale/rotation invariant)
    moments = cv2.moments(norm)
    hu = cv2.HuMoments(moments).flatten()
    # Log-transform for numerical stability
    hu_log = [-np.sign(h) * np.log10(abs(h) + 1e-10) for h in hu]

    # Additional features
    pixel_density = np.count_nonzero(norm) / norm.size
    aspect_ratio = w / h if h > 0 else 1
    n_holes = 0
    if hierarchy is not None:
        # Count enclosed regions (holes)
        for i, h_entry in enumerate(hierarchy[0]):
            if h_entry[3] >= 0:  # Has parent = it's a hole
                n_holes += 1

    return {
        "hu": hu_log,
        "density": pixel_density,
        "aspect": aspect_ratio,
        "holes": n_holes,
        "pixel_pattern": norm.flatten().tolist(),
    }


def save_rank_template(rank: str, binary_roi: np.ndarray):
    """Save a rank template from a known card reading."""
    _ensure_templates_dir()
    features = _compute_contour_features(binary_roi)
    if not features:
        return

    filepath = TEMPLATES_DIR / f"rank_{rank}.json"
    templates = []
    if filepath.exists():
        try:
            templates = json.loads(filepath.read_text())
        except Exception:
            templates = []

    # Don't save too many (keep best 5)
    templates.append(features)
    if len(templates) > 5:
        templates = templates[-5:]

    filepath.write_text(json.dumps(templates))
    _rank_features[rank] = templates


def load_templates():
    """Load saved rank templates from disk."""
    global _rank_features, _loaded
    if _loaded:
        return

    _ensure_templates_dir()
    for filepath in TEMPLATES_DIR.glob("rank_*.json"):
        rank = filepath.stem.replace("rank_", "")
        try:
            _rank_features[rank] = json.loads(filepath.read_text())
        except Exception:
            continue

    _loaded = True
    if _rank_features:
        print(f"[CardReader] Loaded templates for: {', '.join(sorted(_rank_features.keys()))}")


def _match_rank_features(features: dict) -> tuple[str, float]:
    """Match features against saved templates. Returns (rank, confidence)."""
    load_templates()

    if not _rank_features:
        return '?', 0

    best_rank = '?'
    best_score = float('inf')

    query_pattern = np.array(features["pixel_pattern"], dtype=np.float32)

    for rank, templates in _rank_features.items():
        for tmpl in templates:
            # Compare pixel patterns (normalized cross-correlation)
            tmpl_pattern = np.array(tmpl["pixel_pattern"], dtype=np.float32)
            if len(query_pattern) != len(tmpl_pattern):
                continue

            # Pixel correlation
            corr = cv2.matchTemplate(
                query_pattern.reshape(28, 20),
                tmpl_pattern.reshape(28, 20),
                cv2.TM_CCOEFF_NORMED
            )
            pixel_score = corr[0][0]

            # Hu moment distance
            hu_dist = sum((a - b) ** 2 for a, b in zip(features["hu"], tmpl["hu"])) ** 0.5

            # Combined score (lower is better)
            score = hu_dist * 0.3 + (1 - pixel_score) * 0.7

            if score < best_score:
                best_score = score
                best_rank = rank

    confidence = max(0, 1 - best_score)
    return best_rank, confidence


def _match_rank_generated(binary: np.ndarray) -> tuple[str, float]:
    """Fallback: match against programmatically generated templates."""
    features = _compute_contour_features(binary)
    if not features:
        return '?', 0

    # Use structural features for a rough guess
    density = features["density"]
    aspect = features["aspect"]
    holes = features["holes"]

    # Heuristic rules based on structural features
    if holes >= 2:
        return '8', 0.5  # 8 has 2 holes
    if holes == 1:
        if aspect > 0.7:
            return '0', 0.4  # Wide with hole → likely 0 (part of 10)
        if density > 0.4:
            return '4', 0.4  # 4 has enclosed triangle
        return 'A', 0.4  # A has a hole
    # No holes
    if aspect > 0.8:
        return '10', 0.3  # Wide = two characters
    if density > 0.5:
        return 'K', 0.3
    if density < 0.25:
        return '7', 0.3

    return '?', 0


# ─── Suit Detection ──────────────────────────────────────────────────────────

def _detect_suit(card_bgr: np.ndarray) -> str:
    """Detect suit from card image using color analysis."""
    hsv = cv2.cvtColor(card_bgr, cv2.COLOR_BGR2HSV)

    # Red mask (hearts)
    r1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([12, 255, 255]))
    r2 = cv2.inRange(hsv, np.array([160, 70, 70]), np.array([180, 255, 255]))
    red_pixels = cv2.countNonZero(cv2.bitwise_or(r1, r2))

    # Blue mask (diamonds in Pragmatic Play)
    blue = cv2.inRange(hsv, np.array([95, 50, 50]), np.array([135, 255, 255]))
    blue_pixels = cv2.countNonZero(blue)

    total = card_bgr.shape[0] * card_bgr.shape[1]

    if red_pixels / total > 0.02:
        return 'h'  # Red → hearts (could also be diamonds on some tables)
    if blue_pixels / total > 0.02:
        return 'd'  # Blue → diamonds (Pragmatic Play style)

    # Black — need to distinguish spades from clubs
    # Spades ♠ are pointed at top, clubs ♣ have 3 round lobes
    # Use the suit symbol area (bottom half of top-left corner)
    h, w = card_bgr.shape[:2]
    suit_region = card_bgr[int(h*0.45):int(h*0.75), :int(w*0.45)]

    if suit_region.size == 0:
        return 's'  # Default black to spades

    gray = cv2.cvtColor(suit_region, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 's'

    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    hull_area = cv2.contourArea(cv2.convexHull(cnt))

    if hull_area == 0:
        return 's'

    # Solidity: clubs are less solid (3 lobes with gaps)
    solidity = area / hull_area
    if solidity < 0.75:
        return 'c'  # Clubs have lower solidity
    return 's'  # Spades are more solid/convex


# ─── Main Reader ─────────────────────────────────────────────────────────────

def read_card_local(card_bgr: np.ndarray) -> Optional[str]:
    """
    Read a single card from its BGR image crop.
    Returns card string (e.g., 'Ah', 'Kd') or None.
    Works on cards as small as 20x30 pixels.
    """
    if card_bgr is None or card_bgr.size == 0:
        return None

    h, w = card_bgr.shape[:2]
    if h < 15 or w < 10:
        return None

    # Upscale small cards aggressively — need at least 150px tall for good features
    scale = 1
    if h < 150:
        scale = max(3, 150 // h)
        card_bgr = cv2.resize(card_bgr, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)
        h, w = card_bgr.shape[:2]

    # ── Suit detection (color-based, on original-scale for speed) ────
    suit = _detect_suit(card_bgr)

    # ── Rank detection ───────────────────────────────────────────────
    # Crop top-left corner where rank symbol is
    corner_w = max(20, int(w * 0.50))
    corner_h = max(30, int(h * 0.50))
    corner = card_bgr[:corner_h, :corner_w]

    gray = cv2.cvtColor(corner, cv2.COLOR_BGR2GRAY)

    # Threshold — dark text on white card background
    # Use fixed threshold since card bg is always white
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    binary = 255 - binary  # Invert: symbols become white on black

    # Clean
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # Find rank contours (top portion only, exclude suit symbol)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Filter: keep contours in upper 55% (rank area), min area
    rank_h = int(corner_h * 0.55)
    min_area = max(30, (h * w) * 0.001)
    rank_contours = []
    for cnt in contours:
        bx, by, bw, bh = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        if by + bh / 2 < rank_h:
            rank_contours.append(cnt)

    if not rank_contours:
        return None

    # Merge all rank contours into one binary ROI
    all_pts = np.vstack(rank_contours)
    rx, ry, rw, rh = cv2.boundingRect(all_pts)
    rank_roi = binary[ry:ry+rh, rx:rx+rw]

    if rank_roi.size == 0:
        return None

    # Extract features
    features = _compute_contour_features(rank_roi)
    if not features:
        return None

    # Try saved templates first
    rank, confidence = _match_rank_features(features)

    # Fallback to heuristic if no templates or low confidence
    if confidence < 0.4:
        rank_gen, conf_gen = _match_rank_generated(rank_roi)
        if conf_gen > confidence:
            rank = rank_gen
            confidence = conf_gen

    if rank == '?' or confidence < 0.15:
        return None

    return f"{rank}{suit}"


def read_cards_batch(card_crops: list[np.ndarray]) -> list[Optional[str]]:
    """Read multiple card images."""
    return [read_card_local(crop) for crop in card_crops]


def learn_card(card_bgr: np.ndarray, known_rank: str):
    """Learn a card's rank from a known reading (e.g., from LLM).
    Saves the template for future local matching.
    """
    if not known_rank or known_rank not in RANKS:
        return

    h, w = card_bgr.shape[:2]
    scale = 1
    if h < 150:
        scale = max(3, 150 // h)
        card_bgr = cv2.resize(card_bgr, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)
        h, w = card_bgr.shape[:2]

    corner_w = max(20, int(w * 0.50))
    corner_h = max(30, int(h * 0.50))
    corner = card_bgr[:corner_h, :corner_w]

    gray = cv2.cvtColor(corner, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    binary = 255 - binary
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    rank_h = int(corner_h * 0.55)
    min_area = max(30, (h * w) * 0.001)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rank_contours = [c for c in contours if cv2.contourArea(c) > min_area
                     and cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3] / 2 < rank_h]

    if not rank_contours:
        return

    all_pts = np.vstack(rank_contours)
    rx, ry, rw, rh = cv2.boundingRect(all_pts)
    rank_roi = binary[ry:ry+rh, rx:rx+rw]

    if rank_roi.size > 0:
        save_rank_template(known_rank, rank_roi)
        print(f"[CardReader] Learned template for rank '{known_rank}'")


def init_templates():
    """Load templates at startup."""
    load_templates()
