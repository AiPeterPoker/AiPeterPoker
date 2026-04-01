"""
Hi-Lo card counting system for Blackjack.
2-6 = +1, 7-9 = 0, 10/J/Q/K/A = -1
"""

from .hand import CARD_VALUES, parse_rank

HI_LO_VALUES = {
    2: +1, 3: +1, 4: +1, 5: +1, 6: +1,
    7: 0, 8: 0, 9: 0,
    10: -1, 11: -1,  # 11 = Ace
}


class CardCounter:
    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.running_count = 0
        self.cards_seen = 0
        self._counted_cards: list[str] = []

    @property
    def decks_remaining(self) -> float:
        return max(0.5, self.num_decks - self.cards_seen / 52)

    @property
    def true_count(self) -> float:
        return self.running_count / self.decks_remaining

    @property
    def cards_in_shoe(self) -> int:
        return self.num_decks * 52 - self.cards_seen

    def count_card(self, card: str) -> int:
        """Count a single card. Returns its Hi-Lo value."""
        rank = parse_rank(card)
        value = CARD_VALUES.get(rank, 0)
        # Map face cards (all value 10) and Ace (11) to Hi-Lo
        if value >= 10:
            hi_lo = -1
        elif value <= 6:
            hi_lo = +1
        else:
            hi_lo = 0

        self.running_count += hi_lo
        self.cards_seen += 1
        self._counted_cards.append(card)
        return hi_lo

    def count_cards(self, cards: list[str]) -> None:
        """Count multiple cards at once."""
        for card in cards:
            self.count_card(card)

    def reset(self):
        """Reset for new shoe."""
        self.running_count = 0
        self.cards_seen = 0
        self._counted_cards.clear()

    def bet_recommendation(self, min_bet: float = 1.0) -> dict:
        """
        Recommend bet size based on true count using 1-8 spread.
        Returns dict with bet_units, bet_amount, edge_estimate.
        """
        tc = self.true_count

        if tc <= 0:
            units = 1
        elif tc <= 1:
            units = 1
        elif tc <= 2:
            units = 2
        elif tc <= 3:
            units = 4
        elif tc <= 4:
            units = 6
        else:
            units = 8

        # Approximate edge: base house edge ~0.5%, each TC adds ~0.5%
        edge_pct = -0.5 + (tc * 0.5)

        return {
            "bet_units": units,
            "bet_amount": min_bet * units,
            "true_count": round(tc, 1),
            "edge_pct": round(edge_pct, 1),
            "favorable": edge_pct > 0,
        }

    def get_state(self) -> dict:
        """Get current counter state for UI display."""
        bet = self.bet_recommendation()
        return {
            "running_count": self.running_count,
            "true_count": round(self.true_count, 1),
            "cards_seen": self.cards_seen,
            "decks_remaining": round(self.decks_remaining, 1),
            "cards_in_shoe": self.cards_in_shoe,
            "bet_units": bet["bet_units"],
            "edge_pct": bet["edge_pct"],
            "favorable": bet["favorable"],
        }

    @staticmethod
    def hi_lo_value(card: str) -> int:
        """Get Hi-Lo value of a card without counting it."""
        rank = parse_rank(card)
        value = CARD_VALUES.get(rank, 0)
        if value >= 10:
            return -1
        elif value <= 6:
            return +1
        return 0

    def __repr__(self):
        return (
            f"CardCounter(RC={self.running_count}, TC={self.true_count:.1f}, "
            f"seen={self.cards_seen}/{self.num_decks * 52})"
        )
