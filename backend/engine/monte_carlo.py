"""
Monte Carlo Equity Calculator — Casino Hold'em
Optimized for speed and accuracy. Runs N simulations to estimate:
- Win/loss/tie probability (including dealer non-qualification)
- Draw detection (flush draw, straight draw)
- Outs counting
- Hand strength by street
"""

import random
from collections import Counter
from itertools import combinations
from typing import Optional

# ─── Card Utilities ──────────────────────────────────────────────────────────

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['h', 'd', 's', 'c']
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}
RANK_NAMES = {i: r for r, i in RANK_VALUES.items()}

def parse_card(card_str: str) -> tuple[str, str]:
    suit = card_str[-1].lower()
    rank = card_str[:-1].upper()
    return (rank, suit)

def card_value(rank: str) -> int:
    return RANK_VALUES.get(rank, 0)

def full_deck() -> list[str]:
    return [f"{r}{s}" for r in RANKS for s in SUITS]


# ─── Hand Evaluation ─────────────────────────────────────────────────────────

HAND_NAMES = {
    9: 'Royal Flush', 8: 'Straight Flush', 7: 'Four Of A Kind',
    6: 'Full House', 5: 'Flush', 4: 'Straight',
    3: 'Three Of A Kind', 2: 'Two Pair', 1: 'One Pair', 0: 'High Card',
}

def evaluate_hand(cards: list[str]) -> tuple[int, list[int], str]:
    """Evaluate best 5-card hand from given cards. Returns (rank, kickers, name)."""
    if len(cards) < 5:
        ranks = sorted([card_value(parse_card(c)[0]) for c in cards], reverse=True)
        return (0, ranks, 'High Card')

    parsed = [parse_card(c) for c in cards]
    best = (0, [], 'High Card')

    for combo in combinations(range(len(parsed)), 5):
        hand = [parsed[i] for i in combo]
        result = _evaluate_five(hand)
        if result[0] > best[0] or (result[0] == best[0] and result[1] > best[1]):
            best = result

    return best

def _evaluate_five(hand: list[tuple[str, str]]) -> tuple[int, list[int], str]:
    ranks = sorted([card_value(r) for r, s in hand], reverse=True)
    suits = [s for r, s in hand]
    rank_counts = Counter(ranks)
    counts = sorted(rank_counts.values(), reverse=True)
    unique_ranks = sorted(rank_counts.keys(), reverse=True)

    is_flush = len(set(suits)) == 1

    is_straight = False
    straight_high = 0
    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
            straight_high = unique_ranks[0]
        elif unique_ranks == [12, 3, 2, 1, 0]:
            is_straight = True
            straight_high = 3

    if is_straight and is_flush:
        return (9, [straight_high], 'Royal Flush') if straight_high == 12 else (8, [straight_high], 'Straight Flush')
    elif counts == [4, 1]:
        quad = [r for r, c in rank_counts.items() if c == 4][0]
        kick = [r for r, c in rank_counts.items() if c == 1][0]
        return (7, [quad, kick], 'Four Of A Kind')
    elif counts == [3, 2]:
        trip = [r for r, c in rank_counts.items() if c == 3][0]
        pair = [r for r, c in rank_counts.items() if c == 2][0]
        return (6, [trip, pair], 'Full House')
    elif is_flush:
        return (5, ranks, 'Flush')
    elif is_straight:
        return (4, [straight_high], 'Straight')
    elif counts == [3, 1, 1]:
        trip = [r for r, c in rank_counts.items() if c == 3][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
        return (3, [trip] + kickers, 'Three Of A Kind')
    elif counts == [2, 2, 1]:
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        kick = [r for r, c in rank_counts.items() if c == 1][0]
        return (2, pairs + [kick], 'Two Pair')
    elif counts == [2, 1, 1, 1]:
        pair = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
        return (1, [pair] + kickers, 'One Pair')
    else:
        return (0, ranks, 'High Card')


# ─── Draw Detection ──────────────────────────────────────────────────────────

def detect_draws(hole: list[str], community: list[str]) -> dict:
    """Detect flush draws, straight draws, and other draw potential."""
    all_cards = hole + community
    parsed = [parse_card(c) for c in all_cards]
    values = [card_value(r) for r, s in parsed]
    suits = [s for r, s in parsed]

    # Flush draw: 4 cards of same suit
    suit_counts = Counter(suits)
    flush_draw = False
    flush_suit = None
    flush_cards = 0
    for s, c in suit_counts.items():
        if c >= 4:
            flush_draw = True
            flush_suit = s
            flush_cards = c
            break

    made_flush = flush_cards >= 5

    # Straight draw detection
    unique_vals = sorted(set(values))
    # Add ace-low
    if 12 in unique_vals:
        unique_vals = [-1] + unique_vals

    oesd = False  # Open-ended straight draw
    gutshot = False
    made_straight = False

    for start in range(-1, 10):
        window = [v for v in unique_vals if start <= v <= start + 4]
        if len(window) == 5:
            made_straight = True
        elif len(window) == 4:
            missing = [i for i in range(start, start + 5) if i not in window]
            if missing[0] == start or missing[0] == start + 4:
                oesd = True
            else:
                gutshot = True

    # Backdoor draws (only on flop — need 2 more cards)
    backdoor_flush = False
    if len(community) <= 3:
        for s, c in suit_counts.items():
            if c == 3:
                backdoor_flush = True
                break

    return {
        "flush_draw": flush_draw and not made_flush,
        "made_flush": made_flush,
        "flush_outs": (9 - (flush_cards - 4)) if flush_draw and not made_flush else 0,
        "oesd": oesd and not made_straight,
        "gutshot": gutshot and not made_straight and not oesd,
        "made_straight": made_straight,
        "straight_outs": 8 if oesd else (4 if gutshot else 0),
        "backdoor_flush": backdoor_flush and not flush_draw,
        "total_draw_outs": (
            (9 if flush_draw and not made_flush else 0) +
            (8 if oesd and not made_straight else 0) +
            (4 if gutshot and not made_straight and not oesd else 0)
        ),
    }


# ─── Outs Calculator ─────────────────────────────────────────────────────────

def count_outs(hole: list[str], community: list[str], deck: list[str]) -> dict:
    """Count cards that improve the hand."""
    current = evaluate_hand(hole + community)
    current_rank = current[0]
    outs = 0
    improvements = {}

    for card in deck:
        new_hand = evaluate_hand(hole + community + [card])
        if new_hand[0] > current_rank or (
            new_hand[0] == current_rank and new_hand[1] > current[1]
        ):
            outs += 1
            name = new_hand[2]
            improvements[name] = improvements.get(name, 0) + 1

    return {
        "outs": outs,
        "improvements": improvements,
        "remaining": len(deck),
        "outs_pct": (outs / len(deck) * 100) if deck else 0,
    }


# ─── Monte Carlo Equity ──────────────────────────────────────────────────────

class MonteCarloEquity:
    def __init__(self, iterations: int = 10000):
        self.iterations = iterations

    def calculate_equity(
        self,
        hole_cards: list[str],
        community_cards: list[str],
        num_opponents: int = 1,
    ) -> dict:
        """
        Casino Hold'em Monte Carlo equity calculation.

        Results separate dealer-doesn't-qualify from actual wins for accurate EV.
        Also detects draws and counts outs.
        """
        if not hole_cards:
            return self._empty_result()

        known_cards = set(hole_cards + community_cards)
        deck = [c for c in full_deck() if c not in known_cards]
        cards_to_deal = 5 - len(community_cards)
        sample_size = cards_to_deal + 2  # community remainder + dealer hole

        wins_vs_dealer = 0  # Wins when dealer qualifies
        losses = 0
        ties = 0
        dealer_dnq = 0  # Dealer doesn't qualify (auto-win ante)
        total = self.iterations

        for _ in range(total):
            # Only sample the cards we need (faster than shuffling full deck)
            sampled = random.sample(deck, sample_size)

            sim_community = list(community_cards) + sampled[:cards_to_deal]
            dealer_hole = sampled[cards_to_deal:cards_to_deal + 2]

            player_hand = evaluate_hand(hole_cards + sim_community)
            dealer_hand = evaluate_hand(dealer_hole + sim_community)

            # Dealer qualification: pair of 4s or better
            # hand_rank >= 2 (two pair+) always qualifies
            # hand_rank == 1 (one pair) qualifies if pair rank >= 2 (which is 4s)
            dq = dealer_hand[0] >= 2 or (dealer_hand[0] == 1 and dealer_hand[1][0] >= 2)

            if not dq:
                dealer_dnq += 1
                continue

            # Compare hands
            if (player_hand[0], player_hand[1]) > (dealer_hand[0], dealer_hand[1]):
                wins_vs_dealer += 1
            elif (player_hand[0], player_hand[1]) < (dealer_hand[0], dealer_hand[1]):
                losses += 1
            else:
                ties += 1

        # Total wins = wins vs qualified dealer + dealer DNQ
        total_wins = wins_vs_dealer + dealer_dnq
        win_pct = total_wins / total * 100
        lose_pct = losses / total * 100
        tie_pct = ties / total * 100
        dnq_pct = dealer_dnq / total * 100

        # Separate equity: win% when dealer qualifies
        qualified_hands = total - dealer_dnq
        win_vs_qualified_pct = (wins_vs_dealer / qualified_hands * 100) if qualified_hands > 0 else 0

        # Current hand evaluation
        current = evaluate_hand(hole_cards + community_cards)
        hand_strength = min(1.0, win_pct / 100)

        # Draw detection
        draws = detect_draws(hole_cards, community_cards)

        # Outs — use full deck
        outs_info = count_outs(hole_cards, community_cards, deck)

        return {
            "win_pct": round(win_pct, 1),
            "lose_pct": round(lose_pct, 1),
            "tie_pct": round(tie_pct, 1),
            "dealer_dnq_pct": round(dnq_pct, 1),
            "win_vs_qualified_pct": round(win_vs_qualified_pct, 1),
            "hand_strength": round(hand_strength, 2),
            "hand_name": current[2],
            "hand_rank": current[0],
            "outs": outs_info["outs"],
            "outs_pct": round(outs_info["outs_pct"], 1),
            "favorable_outs": outs_info["outs"],
            "improvements": outs_info.get("improvements", {}),
            # Draw info
            "flush_draw": draws["flush_draw"],
            "straight_draw": draws["oesd"] or draws["gutshot"],
            "draw_type": (
                "flush draw" if draws["flush_draw"] else
                "open-ended straight" if draws["oesd"] else
                "gutshot" if draws["gutshot"] else
                "backdoor flush" if draws["backdoor_flush"] else
                None
            ),
            "draw_outs": draws["total_draw_outs"],
        }

    def _empty_result(self) -> dict:
        return {
            "win_pct": 0, "lose_pct": 0, "tie_pct": 0, "dealer_dnq_pct": 0,
            "win_vs_qualified_pct": 0, "hand_strength": 0, "hand_name": "",
            "hand_rank": 0, "outs": 0, "outs_pct": 0, "favorable_outs": 0,
            "improvements": {}, "flush_draw": False, "straight_draw": False,
            "draw_type": None, "draw_outs": 0,
        }
