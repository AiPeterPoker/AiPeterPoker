"""
Decision Engine — Casino Hold'em Optimal Strategy
Based on mathematically computed optimal play (Wizard of Odds / Beating Bonuses).

Casino Hold'em rules:
- Player and dealer get 2 hole cards each
- 3 community cards dealt (flop)
- Player decides: FOLD (lose ante) or PLAY (2x ante)
- Turn + river dealt, showdown
- Dealer needs pair of 4s+ to qualify
- If dealer DNQ: ante pays 1:1, play pushes
- Optimal fold rate: ~18%, play rate: ~82%
- House edge: ~2.16% with perfect play

Key insight: This is NOT Texas Hold'em. There's no raise, no bluffing,
no multi-way. It's a pure math decision: PLAY or FOLD.
"""

from collections import Counter
from typing import Optional

RANK_VALUES = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
               '9': 7, '10': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}

# Ante bonus paytable (Pay Table 3 — most common)
ANTE_BONUS = {
    9: 100,  # Royal Flush → 100:1
    8: 20,   # Straight Flush → 20:1
    7: 10,   # Four of a Kind → 10:1
    6: 3,    # Full House → 3:1
    5: 2,    # Flush → 2:1
}
# Straight or lower → 1:1 (default)


def parse_card(card_str: str) -> tuple:
    """Parse 'Ah' → (12, 'h')"""
    suit = card_str[-1].lower()
    rank = card_str[:-1].upper()
    return RANK_VALUES.get(rank, 0), suit


def has_pair_or_better(hole_cards: list[str], community_cards: list[str]) -> bool:
    """Check if player has at least one pair using at least 1 hole card."""
    if not hole_cards:
        return False
    all_cards = hole_cards + community_cards
    ranks = [parse_card(c)[0] for c in all_cards]
    hole_ranks = set(parse_card(c)[0] for c in hole_cards)

    counts = Counter(ranks)
    for rank, count in counts.items():
        if count >= 2 and rank in hole_ranks:
            return True
    return False


def has_flush_draw(hole_cards: list[str], community_cards: list[str]) -> bool:
    """Check if 4+ cards of the same suit (flush draw or made flush)."""
    all_cards = hole_cards + community_cards
    suits = [parse_card(c)[1] for c in all_cards]
    counts = Counter(suits)
    return any(c >= 4 for c in counts.values())


def has_straight_draw(hole_cards: list[str], community_cards: list[str]) -> str:
    """Check for open-ended straight draw (OESD) or gutshot.
    Returns 'oesd', 'gutshot', or 'none'.
    """
    all_cards = hole_cards + community_cards
    ranks = sorted(set(parse_card(c)[0] for c in all_cards))

    # Add ace as low (0→-1 mapped to 12)
    if 12 in ranks:
        ranks = [-1] + ranks

    # Check all windows of 5 consecutive ranks
    for start in range(-1, 13):
        window = [r for r in ranks if start <= r <= start + 4]
        if len(window) >= 4:
            # 4 out of 5 consecutive = OESD or gutshot
            gaps = []
            for i in range(start, start + 5):
                if i not in window:
                    gaps.append(i)
            if len(gaps) == 1:
                if gaps[0] == start or gaps[0] == start + 4:
                    return "oesd"  # Open-ended
                else:
                    return "gutshot"  # Inside gap
    return "none"


def is_board_monotone(community_cards: list[str]) -> tuple:
    """Check if all 3 flop cards are same suit. Returns (is_monotone, suit)."""
    if len(community_cards) < 3:
        return False, None
    suits = [parse_card(c)[1] for c in community_cards[:3]]
    if suits[0] == suits[1] == suits[2]:
        return True, suits[0]
    return False, None


def player_has_suit(hole_cards: list[str], suit: str) -> bool:
    """Check if player has a card of the given suit."""
    return any(parse_card(c)[1] == suit for c in hole_cards)


def get_high_card_value(hole_cards: list[str]) -> int:
    """Get the highest card value from hole cards."""
    if not hole_cards:
        return 0
    return max(parse_card(c)[0] for c in hole_cards)


def get_low_card_value(hole_cards: list[str]) -> int:
    """Get the lowest card value from hole cards."""
    if not hole_cards:
        return 0
    return min(parse_card(c)[0] for c in hole_cards)


def board_is_low(community_cards: list[str]) -> bool:
    """Board has mostly low cards (dealer less likely to qualify)."""
    if not community_cards:
        return False
    ranks = [parse_card(c)[0] for c in community_cards]
    return all(r <= 3 for r in ranks)  # All 5 or lower


def board_has_pair(community_cards: list[str]) -> bool:
    """Board has a pair (dealer more likely to qualify)."""
    ranks = [parse_card(c)[0] for c in community_cards]
    return len(ranks) != len(set(ranks))


def optimal_decision(hole_cards: list[str], community_cards: list[str],
                     hand_rank: int = 0, win_pct: float = 50.0,
                     dealer_dnq_pct: float = 55.0) -> dict:
    """
    Determine the mathematically optimal PLAY/FOLD decision for Casino Hold'em.

    Implements the simplified optimal strategy that is within 0.003% of perfect play:

    ALWAYS PLAY:
    1. Any pair or better (using at least 1 hole card)
    2. Any 4-to-a-flush draw
    3. Any open-ended straight draw
    4. Ace with 4+ kicker (A4+)
    5. King with 7+ kicker (K7+)

    ALWAYS FOLD:
    1. 2/3 through 2/7 without a straight draw
    2. 3/4 through 3/7 without a straight draw

    CONDITIONAL:
    - Q/J high: PLAY unless board is monotone and you lack the suit
    - Everything else: use equity threshold (~38%)

    Returns: {"action": "call"|"fold", "reason": str, "category": str, "fold_pct": int, "call_pct": int}
    """
    if not hole_cards or len(hole_cards) < 2:
        return {"action": "fold", "reason": "No cards detected", "category": "unknown",
                "fold_pct": 100, "call_pct": 0}

    high = get_high_card_value(hole_cards)
    low = get_low_card_value(hole_cards)
    monotone, mono_suit = is_board_monotone(community_cards)
    flush_draw = has_flush_draw(hole_cards, community_cards)
    straight_draw = has_straight_draw(hole_cards, community_cards)
    pair_or_better = has_pair_or_better(hole_cards, community_cards) or hand_rank >= 1

    # ── TIER 1: ALWAYS PLAY ───────────────────────────────────────────

    # 1. Any pair or better
    if pair_or_better:
        return {"action": "call", "reason": f"Made hand (rank {hand_rank})", "category": "made_hand",
                "fold_pct": 0, "call_pct": 100}

    # 2. Flush draw (4 to a flush)
    if flush_draw:
        return {"action": "call", "reason": "Flush draw (4 to flush)", "category": "flush_draw",
                "fold_pct": 0, "call_pct": 100}

    # 3. Open-ended straight draw
    if straight_draw == "oesd":
        return {"action": "call", "reason": "Open-ended straight draw", "category": "oesd",
                "fold_pct": 0, "call_pct": 100}

    # 4. Ace with 4+ kicker
    if high == 12 and low >= 2:  # A4+
        return {"action": "call", "reason": f"Ace-high (A{low+2}+)", "category": "ace_high",
                "fold_pct": 0, "call_pct": 100}

    # 5. King with 7+ kicker
    if high == 11 and low >= 5:  # K7+
        return {"action": "call", "reason": f"King-high (K{low+2}+)", "category": "king_high",
                "fold_pct": 2, "call_pct": 98}

    # ── TIER 2: ALWAYS FOLD ───────────────────────────────────────────

    # 2/3 through 2/7 without straight draw
    if high <= 5 and low == 0 and straight_draw == "none":  # 2 with 3-7
        return {"action": "fold", "reason": "Low deuce hand, no draw", "category": "trash",
                "fold_pct": 95, "call_pct": 5}

    # 3/4 through 3/7 without straight draw
    if high <= 5 and low == 1 and straight_draw == "none":  # 3 with 4-7
        return {"action": "fold", "reason": "Low trey hand, no draw", "category": "trash",
                "fold_pct": 90, "call_pct": 10}

    # ── TIER 3: CONDITIONAL ───────────────────────────────────────────

    # Ace with low kicker (A2, A3)
    if high == 12:
        return {"action": "call", "reason": "Ace-high (low kicker)", "category": "ace_low",
                "fold_pct": 10, "call_pct": 90}

    # King with low kicker (K2-K6)
    if high == 11:
        if low >= 3:  # K5-K6
            return {"action": "call", "reason": f"King-high (K-{low+2})", "category": "king_marginal",
                    "fold_pct": 30, "call_pct": 70}
        return {"action": "fold", "reason": f"King-low (K-{low+2})", "category": "king_low",
                "fold_pct": 60, "call_pct": 40}

    # Queen or Jack high
    if high == 10:  # Q
        if monotone and not player_has_suit(hole_cards, mono_suit):
            return {"action": "fold", "reason": "Q-high vs monotone, no suit",
                    "category": "monotone_fold", "fold_pct": 80, "call_pct": 20}
        return {"action": "call", "reason": "Queen-high, playable", "category": "queen_high",
                "fold_pct": 15, "call_pct": 85}

    if high == 9:  # J
        if monotone and not player_has_suit(hole_cards, mono_suit):
            return {"action": "fold", "reason": "J-high vs monotone, no suit",
                    "category": "monotone_fold", "fold_pct": 80, "call_pct": 20}
        return {"action": "call", "reason": "Jack-high, playable", "category": "jack_high",
                "fold_pct": 20, "call_pct": 80}

    # 10-high with gutshot
    if high == 8 and straight_draw == "gutshot":
        return {"action": "call", "reason": "10-high with gutshot", "category": "gutshot_high",
                "fold_pct": 35, "call_pct": 65}

    # Gutshot with any high card
    if straight_draw == "gutshot" and high >= 7:
        return {"action": "call", "reason": "Gutshot with high card", "category": "gutshot_high",
                "fold_pct": 30, "call_pct": 70}

    # Low board = dealer unlikely to qualify → be more aggressive
    if board_is_low(community_cards) and dealer_dnq_pct > 45:
        if high >= 6:
            return {"action": "call", "reason": "Low board, dealer unlikely to qualify",
                    "category": "low_board_play", "fold_pct": 30, "call_pct": 70}

    # ── TIER 4: EQUITY-BASED FALLBACK ─────────────────────────────────

    # Adjust equity for dealer non-qualification
    # If dealer DNQ, player wins ante regardless
    adjusted_equity = win_pct + (dealer_dnq_pct * 0.35)

    if adjusted_equity >= 42:
        return {"action": "call", "reason": f"Equity {win_pct:.0f}% + DNQ {dealer_dnq_pct:.0f}% = play",
                "category": "equity_play", "fold_pct": 35, "call_pct": 65}

    # ── DEFAULT: FOLD ─────────────────────────────────────────────────
    return {"action": "fold", "reason": f"Weak hand ({win_pct:.0f}% equity), no draws",
            "category": "default_fold", "fold_pct": 80, "call_pct": 20}


class DecisionEngine:
    def __init__(self, gto_strictness: float = 0.8, kelly_fraction: float = 0.25):
        self.gto_strictness = gto_strictness
        self.kelly_fraction = kelly_fraction

    def get_gto_recommendation(self, game_state: dict, equity: dict) -> dict:
        """Get optimal action for Casino Hold'em using deterministic strategy."""
        hole_cards = game_state.get("hole_cards", [])
        community_cards = game_state.get("community_cards", [])
        hand_rank = equity.get("hand_rank", 0)
        win_pct = equity.get("win_pct", 50)
        dealer_dnq_pct = equity.get("dealer_dnq_pct", 55)

        result = optimal_decision(hole_cards, community_cards, hand_rank, win_pct, dealer_dnq_pct)
        return {"fold": result["fold_pct"], "call": result["call_pct"]}

    def calculate_pot_odds(self, game_state: dict) -> Optional[float]:
        """In Casino Hold'em, pot odds are fixed: risk 2x ante to win pot."""
        pot = game_state.get("pot_size", 0)
        bet = game_state.get("current_bet", 0)
        if bet <= 0:
            return None
        return round(pot / bet, 1)

    def calculate_ev(self, game_state: dict, equity: dict) -> float:
        """Calculate Casino Hold'em EV of playing vs folding.

        If FOLD: lose ante (-1 unit)
        If PLAY:
          - Dealer DNQ (dnq%): win ante (+1), play pushes (0) = +1 unit
          - Dealer qualifies (1-dnq%):
            - Player wins (win%): +1 ante + play pays 1:1 = +3 units
            - Player loses (1-win%): lose ante + play = -3 units
        """
        ante = game_state.get("current_bet", 1) or 1
        win_pct = equity.get("win_pct", 50) / 100
        dnq_pct = equity.get("dealer_dnq_pct", 55) / 100

        fold_ev = -ante

        # EV of playing
        play_ev = (
            dnq_pct * ante +  # Dealer doesn't qualify: win ante
            (1 - dnq_pct) * (
                win_pct * 3 * ante +       # Win: ante + 2x play
                (1 - win_pct) * -3 * ante  # Lose: ante + 2x play
            )
        )

        # Add ante bonus EV for strong hands
        hand_rank = equity.get("hand_rank", 0)
        if hand_rank in ANTE_BONUS:
            play_ev += ANTE_BONUS[hand_rank] * ante

        return round(play_ev, 2)

    def kelly_bet_size(self, win_pct: float, dealer_dnq_pct: float, bankroll: float) -> float:
        """Kelly Criterion for Casino Hold'em (1:1 payoff structure)."""
        p = win_pct / 100
        dnq = dealer_dnq_pct / 100
        # Effective win probability including DNQ
        effective_p = dnq + (1 - dnq) * p
        q = 1 - effective_p
        # For 1:1 payoff: f* = p - q = 2p - 1
        kelly = 2 * effective_p - 1
        kelly = max(0, kelly)
        fractional = kelly * self.kelly_fraction
        bet = bankroll * fractional
        return round(bet, 2)

    def estimate_dealer_qualification(self, community_cards: list[str]) -> int:
        """Estimate probability that dealer qualifies (pair of 4s or better)."""
        if not community_cards:
            return 55

        ranks = [parse_card(c)[0] for c in community_cards]

        if board_has_pair(community_cards):
            return 82

        # High cards on board help dealer
        high_count = sum(1 for r in ranks if r >= 8)
        if high_count >= 2:
            return 68
        elif high_count >= 1:
            return 62

        # Low board = hard for dealer to qualify
        if all(r <= 3 for r in ranks):
            return 42
        elif all(r <= 5 for r in ranks):
            return 48

        return 55

    def make_decision(self, game_state: dict, equity: dict, gto: dict,
                      reasoning: dict, bankroll: float) -> dict:
        """Make final Casino Hold'em decision: PLAY (2x) or FOLD."""
        hole_cards = game_state.get("hole_cards", [])
        community_cards = game_state.get("community_cards", [])
        win_pct = equity.get("win_pct", 50)
        hand_rank = equity.get("hand_rank", 0)
        dealer_dnq_pct = equity.get("dealer_dnq_pct", 55)
        bet = game_state.get("current_bet", 1) or 1

        # Get optimal decision
        decision = optimal_decision(
            hole_cards, community_cards, hand_rank, win_pct, dealer_dnq_pct
        )
        gto_action = decision["action"]

        # Agent reasoning (minor influence)
        agent_action = reasoning.get("recommended_action", gto_action)
        if agent_action in ("raise", "play", "2x"):
            agent_action = "call"
        agent_confidence = reasoning.get("confidence", 50)

        # In Casino Hold'em, math is king — always follow optimal strategy
        final_action = gto_action

        # EV
        ev = self.calculate_ev(game_state, equity)

        # Amount
        amount = bet * 2 if final_action == "call" else 0

        # Kelly info
        kelly_size = self.kelly_bet_size(win_pct, dealer_dnq_pct, bankroll)

        # Confidence based on decision clarity
        call_pct = decision["call_pct"]
        if call_pct >= 95 or call_pct <= 5:
            confidence = 95  # Clear decision
        elif call_pct >= 80 or call_pct <= 20:
            confidence = 80
        elif call_pct >= 65 or call_pct <= 35:
            confidence = 65
        else:
            confidence = 50  # Marginal / coin flip

        return {
            "action": final_action,
            "amount": round(amount, 2),
            "confidence": confidence,
            "reasoning": decision["reason"],
            "category": decision["category"],
            "expected_value": ev,
            "kelly_info": f"Kelly: ${kelly_size:.2f} ({self.kelly_fraction * 100:.0f}% frac)",
            "gto_action": gto_action,
            "agent_action": agent_action,
        }
