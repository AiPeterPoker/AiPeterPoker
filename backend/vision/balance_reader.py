"""
Local Balance Reader — Pixel-based digit matching
Reads casino balance from screen using OpenCV.
Designed for Pragmatic Play's specific balance font.
No external OCR needed. ~2ms.
"""

import cv2
import numpy as np
import json
from pathlib import Path
from typing import Optional

TEMPLATES_FILE = Path(__file__).parent.parent / "data" / "digit_templates.json"
_digit_templates: dict[str, np.ndarray] = {}
_digit_h = 0


def _load_digit_templates():
    """Load learned digit templates from disk."""
    global _digit_templates, _digit_h
    if _digit_templates:
        return
    if TEMPLATES_FILE.exists():
        try:
            data = json.loads(TEMPLATES_FILE.read_text())
            for ch, pixels in data.items():
                _digit_templates[ch] = np.array(pixels, dtype=np.uint8)
                _digit_h = _digit_templates[ch].shape[0]
            if _digit_templates:
                print(f"[BalanceReader] Loaded digit templates: {list(_digit_templates.keys())}")
        except Exception:
            pass


def learn_digit(char: str, binary_roi: np.ndarray):
    """Learn a digit or symbol template from a known reading.
    binary_roi should be a binary image of a single character (white on black).
    """
    if not char or char not in '0123456789$':
        return

    # Normalize to fixed height
    h, w = binary_roi.shape[:2]
    target_h = 20
    scale = target_h / h
    target_w = max(3, int(w * scale))
    normalized = cv2.resize(binary_roi, (target_w, target_h), interpolation=cv2.INTER_AREA)
    _, normalized = cv2.threshold(normalized, 127, 255, cv2.THRESH_BINARY)

    _digit_templates[char] = normalized
    global _digit_h
    _digit_h = target_h

    # Save all templates
    TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {ch: tmpl.tolist() for ch, tmpl in _digit_templates.items()}
    TEMPLATES_FILE.write_text(json.dumps(data))


def _segment_and_read(binary: np.ndarray) -> str:
    """Segment digits from binary image using vertical projection and match each."""
    _load_digit_templates()

    h, w = binary.shape
    if h < 3 or w < 3:
        return ""

    # Vertical projection
    proj = np.sum(binary > 0, axis=0)
    threshold = max(1, proj.max() * 0.08)

    # Find character segments
    segments = []
    in_char = False
    start = 0
    for i in range(w):
        if proj[i] > threshold:
            if not in_char:
                start = i
                in_char = True
        else:
            if in_char:
                segments.append((start, i))
                in_char = False
    if in_char:
        segments.append((start, w))

    if not segments:
        return ""

    # Get reference height
    ref_h = h

    result = ""
    for s, e in segments:
        seg_w = e - s
        if seg_w < 2:
            continue

        col = binary[:, s:e]
        rows = np.where(np.any(col > 0, axis=1))[0]
        if len(rows) == 0:
            continue

        y1, y2 = rows[0], rows[-1] + 1
        seg_h = y2 - y1

        # Decimal dot: short and narrow
        if seg_h < ref_h * 0.4 and seg_w < ref_h * 0.4:
            result += "."
            continue

        if seg_h < ref_h * 0.4:
            continue

        roi = binary[y1:y2, s:e]

        # Wide segment = multiple digits stuck together → split by equal width
        if seg_w > seg_h * 1.2 and seg_w > 15:
            n_digits = max(2, round(seg_w / seg_h))
            digit_w = seg_w // n_digits
            for d in range(n_digits):
                xs = d * digit_w
                xe = (d + 1) * digit_w if d < n_digits - 1 else seg_w
                sub_roi = roi[:, xs:xe]
                if sub_roi.size > 0:
                    ch, conf = _match_single(sub_roi)
                    if ch != '$' and conf > 0.3:
                        result += ch
        else:
            # Single character
            ch, conf = _match_single(roi)
            if ch == '$':
                continue  # Skip dollar sign
            if conf > 0.3:
                result += ch

    return result


def _match_single(roi: np.ndarray) -> tuple[str, float]:
    """Match a single digit ROI against templates."""
    if not _digit_templates:
        return '?', 0

    # Normalize to template height
    h, w = roi.shape
    target_h = _digit_h or 20
    scale = target_h / h
    target_w = max(3, int(w * scale))
    resized = cv2.resize(roi, (target_w, target_h), interpolation=cv2.INTER_AREA)
    _, resized = cv2.threshold(resized, 127, 255, cv2.THRESH_BINARY)

    best_ch = '?'
    best_score = -1

    for ch, tmpl in _digit_templates.items():
        th, tw = tmpl.shape

        # Pad to same width for comparison
        max_w = max(tw, target_w)
        t_padded = np.zeros((target_h, max_w), dtype=np.uint8)
        r_padded = np.zeros((target_h, max_w), dtype=np.uint8)
        t_padded[:, :tw] = tmpl
        r_padded[:, :target_w] = resized

        # Normalized cross correlation
        score = cv2.matchTemplate(r_padded, t_padded, cv2.TM_CCOEFF_NORMED)[0][0]
        if score > best_score:
            best_score = score
            best_ch = ch

    return best_ch, best_score


def read_balance_local(balance_bgr: np.ndarray) -> Optional[float]:
    """Read balance from cropped BGR image. Expects "$XX.XX" white text on dark bg."""
    if balance_bgr is None or balance_bgr.size == 0:
        return None

    h, w = balance_bgr.shape[:2]
    if h < 5 or w < 10:
        return None

    gray = cv2.cvtColor(balance_bgr, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)

    # Number row: bottom 45% (skip "BALANCE" label)
    number_row = binary[int(h * 0.55):, :]
    nh, nw = number_row.shape
    if nh < 3:
        return None

    # Upscale if tiny
    if nh < 20:
        scale = max(3, 20 // nh)
        number_row = cv2.resize(number_row, (nw * scale, nh * scale), interpolation=cv2.INTER_CUBIC)
        _, number_row = cv2.threshold(number_row, 127, 255, cv2.THRESH_BINARY)

    # If we have digit templates, use our custom reader
    _load_digit_templates()
    if _digit_templates:
        text = _segment_and_read(number_row)
    else:
        # Fallback: try EasyOCR
        try:
            import easyocr
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            results = reader.readtext(number_row, allowlist='0123456789.', detail=0)
            text = ''.join(results).strip()
        except Exception:
            return None

    if not text:
        return None

    # Clean up
    text = text.replace('$', '').replace(',', '').replace(' ', '')

    # Remove non-numeric chars
    cleaned = ''
    for c in text:
        if c.isdigit() or c == '.':
            cleaned += c

    if not cleaned:
        return None

    # Auto-insert decimal if missing
    if '.' not in cleaned and len(cleaned) >= 3:
        cleaned = cleaned[:-2] + '.' + cleaned[-2:]

    try:
        value = float(cleaned)
        if value < 0 or value > 999999:
            return None
        return round(value, 2)
    except (ValueError, TypeError):
        return None


def learn_from_known_balance(balance_bgr: np.ndarray, known_value: float):
    """Learn digit templates from a balance image with a known value.
    Call this when LLM confirms the balance amount.
    """
    if balance_bgr is None or known_value <= 0:
        return

    h, w = balance_bgr.shape[:2]
    gray = cv2.cvtColor(balance_bgr, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)

    number_row = binary[int(h * 0.55):, :]
    nh, nw = number_row.shape
    if nh < 3:
        return

    if nh < 20:
        scale = max(3, 20 // nh)
        number_row = cv2.resize(number_row, (nw * scale, nh * scale), interpolation=cv2.INTER_CUBIC)
        _, number_row = cv2.threshold(number_row, 127, 255, cv2.THRESH_BINARY)

    # Format the known value as string
    value_str = f"{known_value:.2f}"  # e.g., "8.25"

    # Segment the image
    proj = np.sum(number_row > 0, axis=0)
    threshold = max(1, proj.max() * 0.08)

    segments = []
    in_char = False
    start = 0
    for i in range(number_row.shape[1]):
        if proj[i] > threshold:
            if not in_char:
                start = i
                in_char = True
        else:
            if in_char:
                segments.append((start, i))
                in_char = False
    if in_char:
        segments.append((start, number_row.shape[1]))

    # Skip first segment if it's likely the $ sign
    ref_h = number_row.shape[0]
    digit_segments = []
    for s, e in segments:
        col = number_row[:, s:e]
        rows = np.where(np.any(col > 0, axis=1))[0]
        if len(rows) == 0:
            continue
        seg_h = rows[-1] - rows[0] + 1
        seg_w = e - s
        # Skip dots (small)
        if seg_h < ref_h * 0.4 and seg_w < ref_h * 0.4:
            continue
        digit_segments.append((s, e, rows[0], rows[-1] + 1))

    # First segment is always the $ sign — learn it and remove from list
    digits_in_value = [c for c in value_str if c.isdigit()]
    if digit_segments:
        ds = digit_segments[0]
        dollar_roi = number_row[ds[2]:ds[3], ds[0]:ds[1]]
        if dollar_roi.size > 0:
            learn_digit('$', dollar_roi)
        digit_segments = digit_segments[1:]  # Always remove $

    # Split wide segments (multiple digits stuck together) into individual chars
    all_rois = []
    for s, e, y1, y2 in digit_segments:
        seg_w = e - s
        seg_h = y2 - y1
        roi = number_row[y1:y2, s:e]

        if seg_w > seg_h * 1.2:
            # Estimate number of digits: each digit is roughly as wide as it is tall
            n_digits = max(2, round(seg_w / seg_h))
            digit_w = seg_w // n_digits
            for d in range(n_digits):
                x_start = d * digit_w
                x_end = (d + 1) * digit_w if d < n_digits - 1 else seg_w
                sub = roi[:, x_start:x_end]
                if sub.size > 0:
                    all_rois.append(sub)
        else:
            all_rois.append(roi)

    # Map ROIs to known digit characters
    if len(all_rois) == len(digits_in_value):
        for droi, digit_char in zip(all_rois, digits_in_value):
            if droi.size > 0:
                learn_digit(digit_char, droi)
        print(f"[BalanceReader] Learned digits from ${known_value:.2f}: {digits_in_value}")
    else:
        print(f"[BalanceReader] Segment count mismatch: {len(all_rois)} rois vs {len(digits_in_value)} digits")
