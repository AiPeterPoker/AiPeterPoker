CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11,
}


def parse_rank(card: str) -> str:
    """Extract rank from card string like 'Ah', '10s', 'Kd'."""
    return card[:-1].upper()


class BlackjackHand:
    def __init__(self, cards: list[str] | None = None):
        self.cards: list[str] = []
        self._ranks: list[str] = []
        if cards:
            for c in cards:
                self.add_card(c)

    def add_card(self, card: str):
        self.cards.append(card)
        self._ranks.append(parse_rank(card))

    @property
    def total(self) -> int:
        total = 0
        aces = 0
        for rank in self._ranks:
            val = CARD_VALUES.get(rank, 0)
            total += val
            if rank == "A":
                aces += 1
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    @property
    def is_soft(self) -> bool:
        total = 0
        aces = 0
        for rank in self._ranks:
            val = CARD_VALUES.get(rank, 0)
            total += val
            if rank == "A":
                aces += 1
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return aces > 0 and total <= 21

    @property
    def is_pair(self) -> bool:
        if len(self.cards) != 2:
            return False
        return CARD_VALUES.get(self._ranks[0], 0) == CARD_VALUES.get(self._ranks[1], 0)

    @property
    def pair_value(self) -> int | None:
        if not self.is_pair:
            return None
        return CARD_VALUES.get(self._ranks[0], 0)

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.total == 21

    @property
    def is_busted(self) -> bool:
        return self.total > 21

    @property
    def num_cards(self) -> int:
        return len(self.cards)

    def __repr__(self):
        return f"BlackjackHand({self.cards}, total={self.total}, soft={self.is_soft})"
