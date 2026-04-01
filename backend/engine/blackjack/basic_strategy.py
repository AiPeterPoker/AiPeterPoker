"""
Multi-deck (6-8 decks) basic strategy for Blackjack.
Includes Illustrious 18 deviations when true count is provided.

Dealer upcard is represented as 2-11 (11 = Ace).
Actions: H = Hit, S = Stand, D = Double (hit if can't), P = Split, Ds = Double (stand if can't)
"""

from .hand import BlackjackHand, CARD_VALUES, parse_rank

H, S, D, P, Ds = "HIT", "STAND", "DOUBLE", "SPLIT", "DOUBLE_STAND"

ACTIONS = {H, S, D, P, Ds}

# Hard totals: HARD_TABLE[player_total][dealer_upcard]
# Dealer: 2  3  4  5  6  7  8  9  10  A(11)
HARD_TABLE = {
    5:  {2:H, 3:H, 4:H, 5:H, 6:H, 7:H, 8:H, 9:H, 10:H, 11:H},
    6:  {2:H, 3:H, 4:H, 5:H, 6:H, 7:H, 8:H, 9:H, 10:H, 11:H},
    7:  {2:H, 3:H, 4:H, 5:H, 6:H, 7:H, 8:H, 9:H, 10:H, 11:H},
    8:  {2:H, 3:H, 4:H, 5:H, 6:H, 7:H, 8:H, 9:H, 10:H, 11:H},
    9:  {2:H, 3:D, 4:D, 5:D, 6:D, 7:H, 8:H, 9:H, 10:H, 11:H},
    10: {2:D, 3:D, 4:D, 5:D, 6:D, 7:D, 8:D, 9:D, 10:H, 11:H},
    11: {2:D, 3:D, 4:D, 5:D, 6:D, 7:D, 8:D, 9:D, 10:D, 11:D},
    12: {2:H, 3:H, 4:S, 5:S, 6:S, 7:H, 8:H, 9:H, 10:H, 11:H},
    13: {2:S, 3:S, 4:S, 5:S, 6:S, 7:H, 8:H, 9:H, 10:H, 11:H},
    14: {2:S, 3:S, 4:S, 5:S, 6:S, 7:H, 8:H, 9:H, 10:H, 11:H},
    15: {2:S, 3:S, 4:S, 5:S, 6:S, 7:H, 8:H, 9:H, 10:H, 11:H},
    16: {2:S, 3:S, 4:S, 5:S, 6:S, 7:H, 8:H, 9:H, 10:H, 11:H},
    17: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
    18: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
    19: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
    20: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
    21: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
}

# Soft totals: SOFT_TABLE[player_total][dealer_upcard]
SOFT_TABLE = {
    13: {2:H, 3:H, 4:H, 5:D, 6:D, 7:H, 8:H, 9:H, 10:H, 11:H},
    14: {2:H, 3:H, 4:H, 5:D, 6:D, 7:H, 8:H, 9:H, 10:H, 11:H},
    15: {2:H, 3:H, 4:D, 5:D, 6:D, 7:H, 8:H, 9:H, 10:H, 11:H},
    16: {2:H, 3:H, 4:D, 5:D, 6:D, 7:H, 8:H, 9:H, 10:H, 11:H},
    17: {2:H, 3:D, 4:D, 5:D, 6:D, 7:H, 8:H, 9:H, 10:H, 11:H},
    18: {2:Ds,3:Ds,4:Ds,5:Ds,6:Ds,7:S, 8:S, 9:H, 10:H, 11:H},
    19: {2:S, 3:S, 4:S, 5:S, 6:Ds,7:S, 8:S, 9:S, 10:S, 11:S},
    20: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
    21: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
}

# Pair splits: PAIR_TABLE[pair_card_value][dealer_upcard]
# pair_card_value: 2-10 for number pairs, 11 for Aces
PAIR_TABLE = {
    2:  {2:P, 3:P, 4:P, 5:P, 6:P, 7:P, 8:H, 9:H, 10:H, 11:H},
    3:  {2:P, 3:P, 4:P, 5:P, 6:P, 7:P, 8:H, 9:H, 10:H, 11:H},
    4:  {2:H, 3:H, 4:H, 5:P, 6:P, 7:H, 8:H, 9:H, 10:H, 11:H},
    5:  {2:D, 3:D, 4:D, 5:D, 6:D, 7:D, 8:D, 9:D, 10:H, 11:H},
    6:  {2:P, 3:P, 4:P, 5:P, 6:P, 7:H, 8:H, 9:H, 10:H, 11:H},
    7:  {2:P, 3:P, 4:P, 5:P, 6:P, 7:P, 8:H, 9:H, 10:H, 11:H},
    8:  {2:P, 3:P, 4:P, 5:P, 6:P, 7:P, 8:P, 9:P, 10:P, 11:P},
    9:  {2:P, 3:P, 4:P, 5:P, 6:P, 7:S, 8:P, 9:P, 10:S, 11:S},
    10: {2:S, 3:S, 4:S, 5:S, 6:S, 7:S, 8:S, 9:S, 10:S, 11:S},
    11: {2:P, 3:P, 4:P, 5:P, 6:P, 7:P, 8:P, 9:P, 10:P, 11:P},
}

# Illustrious 18 deviations: (player_total, dealer_upcard, is_soft, tc_threshold, deviation_action)
# If true_count >= tc_threshold, use deviation_action instead of basic strategy
ILLUSTRIOUS_18 = [
    # Insurance: take at TC >= +3 (handled separately)
    (16, 10, False, 0,  S),   # 16 vs 10: Stand at TC >= 0 (normally Hit)
    (15, 10, False, 4,  S),   # 15 vs 10: Stand at TC >= +4
    (20, 5,  False, 5,  P),   # 10,10 vs 5: Split at TC >= +5 (pair deviation)
    (20, 6,  False, 4,  P),   # 10,10 vs 6: Split at TC >= +4
    (10, 10, False, 4,  D),   # 10 vs 10: Double at TC >= +4
    (12, 3,  False, 2,  S),   # 12 vs 3: Stand at TC >= +2
    (12, 2,  False, 3,  S),   # 12 vs 2: Stand at TC >= +3
    (11, 11, False, 1,  D),   # 11 vs A: Double at TC >= +1
    (9,  2,  False, 1,  D),   # 9 vs 2: Double at TC >= +1
    (10, 11, False, 4,  D),   # 10 vs A: Double at TC >= +4
    (9,  7,  False, 3,  D),   # 9 vs 7: Double at TC >= +3
    (16, 9,  False, 5,  S),   # 16 vs 9: Stand at TC >= +5
    (13, 2,  False, -1, H),   # 13 vs 2: Hit at TC <= -1
    (12, 4,  False, 0,  H),   # 12 vs 4: Hit at TC <= 0 (negative deviation)
    (12, 5,  False, -2, H),   # 12 vs 5: Hit at TC <= -2
    (12, 6,  False, -1, H),   # 12 vs 6: Hit at TC <= -1
    (13, 3,  False, -2, H),   # 13 vs 3: Hit at TC <= -2
]

INSURANCE_TC_THRESHOLD = 3


def _check_illustrious_18(player_total: int, dealer_upcard: int, is_soft: bool, true_count: float) -> str | None:
    """Check if any Illustrious 18 deviation applies. Returns action or None."""
    for p_total, d_up, soft, tc_thresh, dev_action in ILLUSTRIOUS_18:
        if p_total != player_total or d_up != dealer_upcard or soft != is_soft:
            continue
        # Negative deviations: deviate when count is LOW
        if dev_action == H and tc_thresh <= 0:
            if true_count <= tc_thresh:
                return dev_action
        # Positive deviations: deviate when count is HIGH
        else:
            if true_count >= tc_thresh:
                return dev_action
    return None


def dealer_upcard_value(card: str) -> int:
    """Convert dealer upcard string to numeric value (2-11, Ace=11)."""
    rank = parse_rank(card)
    return CARD_VALUES.get(rank, 0)


def get_action(
    hand: BlackjackHand,
    dealer_upcard: int,
    can_double: bool = True,
    can_split: bool = True,
    true_count: float | None = None,
) -> dict:
    """
    Get optimal blackjack action.

    Args:
        hand: Player's BlackjackHand
        dealer_upcard: Dealer's visible card value (2-11)
        can_double: Whether doubling is allowed (usually only on first 2 cards)
        can_split: Whether splitting is allowed
        true_count: Hi-Lo true count for deviations (None = basic strategy only)

    Returns:
        dict with keys: action, reason, is_deviation
    """
    total = hand.total
    is_deviation = False
    reason = "Basic strategy"

    # Check Illustrious 18 deviations first
    if true_count is not None:
        dev = _check_illustrious_18(total, dealer_upcard, hand.is_soft, true_count)
        if dev is not None:
            # Validate the deviation is possible
            if dev == D and not can_double:
                dev = H
            if dev == P and not (can_split and hand.is_pair):
                dev = None
            if dev is not None:
                is_deviation = True
                reason = f"Illustrious 18 deviation (TC={true_count:+.1f})"
                action = dev
                if action == Ds:
                    action = D if can_double else S
                return {"action": action, "reason": reason, "is_deviation": is_deviation}

    # Pair splitting
    if can_split and hand.is_pair and hand.pair_value in PAIR_TABLE:
        action = PAIR_TABLE[hand.pair_value].get(dealer_upcard, H)
        if action == P:
            return {"action": P, "reason": f"Split {hand.pair_value}s vs {dealer_upcard}", "is_deviation": False}
        # If table says don't split, fall through to hard/soft

    # Soft totals
    if hand.is_soft and total in SOFT_TABLE:
        action = SOFT_TABLE[total].get(dealer_upcard, H)
    # Hard totals
    elif total in HARD_TABLE:
        action = HARD_TABLE[total].get(dealer_upcard, H)
    else:
        action = H if total < 5 else S

    # Handle DOUBLE restrictions
    if action == D and not can_double:
        action = H
    elif action == Ds and not can_double:
        action = S
    elif action == Ds:
        action = D

    return {"action": action, "reason": reason, "is_deviation": is_deviation}


def should_take_insurance(true_count: float | None) -> bool:
    """Insurance is +EV only when true count >= +3."""
    if true_count is None:
        return False
    return true_count >= INSURANCE_TC_THRESHOLD
