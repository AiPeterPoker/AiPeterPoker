"""
Card Recognition Utilities
Helper functions for parsing and validating card strings from vision output.
"""

import re
from typing import Optional

# ─── Constants ───────────────────────────────────────────────────────────────

VALID_RANKS = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
VALID_SUITS = {'h', 'd', 's', 'c'}

RANK_ALIASES = {
    'ace': 'A', '1': 'A', '14': 'A',
    'king': 'K', '13': 'K',
    'queen': 'Q', '12': 'Q',
    'jack': 'J', '11': 'J',
    'ten': '10', 't': '10',
}

SUIT_ALIASES = {
    'hearts': 'h', 'heart': 'h', '♥': 'h', '♡': 'h',
    'diamonds': 'd', 'diamond': 'd', '♦': 'd', '♢': 'd',
    'spades': 's', 'spade': 's', '♠': 's', '♤': 's',
    'clubs': 'c', 'club': 'c', '♣': 'c', '♧': 'c',
}

SUIT_SYMBOLS = {'h': '♥', 'd': '♦', 's': '♠', 'c': '♣'}
SUIT_NAMES = {'h': 'Hearts', 'd': 'Diamonds', 's': 'Spades', 'c': 'Clubs'}

# ─── Parsing ─────────────────────────────────────────────────────────────────

def parse_card(card_str: str) -> Optional[tuple[str, str]]:
    """
    Parse a card string into (rank, suit).
    Handles many formats: 'Ah', 'A♥', 'ace of hearts', '14h', etc.
    Returns None if invalid.
    """
    if not card_str or not isinstance(card_str, str):
        return None

    card_str = card_str.strip()

    # Try direct format: "Ah", "10s", "Kd"
    match = re.match(r'^(10|[2-9]|[AKQJ])([hdsc])$', card_str, re.IGNORECASE)
    if match:
        rank = match.group(1).upper()
        suit = match.group(2).lower()
        if rank in VALID_RANKS and suit in VALID_SUITS:
            return (rank, suit)

    # Try with Unicode suits: "A♥", "10♠"
    for symbol, suit_letter in SUIT_ALIASES.items():
        if symbol in card_str:
            rank_part = card_str.replace(symbol, '').strip().upper()
            rank_part = RANK_ALIASES.get(rank_part.lower(), rank_part)
            if rank_part in VALID_RANKS:
                return (rank_part, suit_letter)

    # Try verbose: "ace of hearts", "king of spades"
    match = re.match(r'^(\w+)\s+of\s+(\w+)$', card_str, re.IGNORECASE)
    if match:
        rank_word = match.group(1).lower()
        suit_word = match.group(2).lower()
        rank = RANK_ALIASES.get(rank_word, rank_word.upper())
        suit = SUIT_ALIASES.get(suit_word)
        if rank in VALID_RANKS and suit in VALID_SUITS:
            return (rank, suit)

    return None


def normalize_card(card_str: str) -> Optional[str]:
    """
    Normalize a card string to standard format: 'Ah', '10s', 'Kd'.
    Returns None if invalid.
    """
    parsed = parse_card(card_str)
    if parsed:
        return f"{parsed[0]}{parsed[1]}"
    return None


def normalize_card_list(cards: list[str]) -> list[str]:
    """Normalize a list of card strings, filtering out invalid ones."""
    result = []
    for card in cards:
        normalized = normalize_card(card)
        if normalized:
            result.append(normalized)
    return result


def card_to_display(card_str: str) -> str:
    """Convert 'Ah' to 'A♥' for display."""
    parsed = parse_card(card_str)
    if parsed:
        return f"{parsed[0]}{SUIT_SYMBOLS.get(parsed[1], parsed[1])}"
    return card_str


def validate_game_state_cards(game_state: dict) -> dict:
    """
    Validate and normalize all card fields in a game state dict.
    Removes duplicates and invalid cards.
    """
    cleaned = dict(game_state)

    for field in ['hole_cards', 'community_cards', 'dealer_cards']:
        if field in cleaned and isinstance(cleaned[field], list):
            cleaned[field] = normalize_card_list(cleaned[field])

    # Check for duplicate cards across all fields
    all_cards = []
    for field in ['hole_cards', 'community_cards', 'dealer_cards']:
        all_cards.extend(cleaned.get(field, []))

    if len(all_cards) != len(set(all_cards)):
        # Duplicates found — likely a vision error
        seen = set()
        for field in ['hole_cards', 'community_cards', 'dealer_cards']:
            if field in cleaned:
                deduped = []
                for card in cleaned[field]:
                    if card not in seen:
                        seen.add(card)
                        deduped.append(card)
                cleaned[field] = deduped

    return cleaned


# ─── Deck Operations ─────────────────────────────────────────────────────────

def full_deck() -> list[str]:
    """Generate a full 52-card deck."""
    return [f"{r}{s}" for r in VALID_RANKS for s in VALID_SUITS]


def remaining_deck(known_cards: list[str]) -> list[str]:
    """Return cards not yet seen."""
    known = set(normalize_card_list(known_cards))
    return [c for c in full_deck() if c not in known]
