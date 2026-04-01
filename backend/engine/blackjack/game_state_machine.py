"""
Blackjack game state machine.
Tracks phases: WAITING → PLAYER_TURN → DEALER_TURN → RESULT
Transitions driven by ESP card detection changes.
"""

import time
from enum import Enum


class Phase(str, Enum):
    WAITING = "waiting"
    PLAYER_TURN = "player_turn"
    DEALER_TURN = "dealer_turn"
    RESULT = "result"


PHASE_TIMEOUTS = {
    Phase.WAITING: 60,
    Phase.PLAYER_TURN: 30,
    Phase.DEALER_TURN: 15,
    Phase.RESULT: 10,
}


class BlackjackStateMachine:
    def __init__(self):
        self.phase = Phase.WAITING
        self._phase_start = time.time()
        self._last_card_count = 0
        self._player_card_count = 0
        self._dealer_card_count = 0
        self._dealer_revealed = False
        self._acted = False  # Player has finished their turn

    def reset(self):
        """Reset for new hand."""
        self.phase = Phase.WAITING
        self._phase_start = time.time()
        self._last_card_count = 0
        self._player_card_count = 0
        self._dealer_card_count = 0
        self._dealer_revealed = False
        self._acted = False

    def _transition(self, new_phase: Phase) -> dict | None:
        """Transition to a new phase. Returns transition info or None if same phase."""
        if new_phase == self.phase:
            return None
        old = self.phase
        self.phase = new_phase
        self._phase_start = time.time()
        return {"from": old.value, "to": new_phase.value, "time": time.time()}

    @property
    def phase_elapsed(self) -> float:
        return time.time() - self._phase_start

    def process(
        self,
        player_cards: int,
        dealer_cards: int,
        dealer_hole_visible: bool = False,
    ) -> dict | None:
        """
        Process current card state from ESP detection.

        Args:
            player_cards: Number of player cards detected
            dealer_cards: Number of dealer cards detected
            dealer_hole_visible: Whether dealer's hole card is face-up

        Returns:
            Transition dict if phase changed, None otherwise
        """
        total_cards = player_cards + dealer_cards

        if self.phase == Phase.WAITING:
            # Cards appeared → game started
            # In Evolution BJ: player gets 2 face-up, dealer gets 1 up + 1 down
            # Be lenient: transition if we see at least 2 player cards OR any total >= 3
            if player_cards >= 2 or (player_cards >= 1 and dealer_cards >= 1 and player_cards + dealer_cards >= 3):
                self._player_card_count = player_cards
                self._dealer_card_count = dealer_cards
                return self._transition(Phase.PLAYER_TURN)

        elif self.phase == Phase.PLAYER_TURN:
            self._player_card_count = player_cards
            self._dealer_card_count = dealer_cards

            # Dealer hole card revealed means player turn is over
            if dealer_hole_visible and dealer_cards >= 2:
                self._dealer_revealed = True
                self._acted = True
                return self._transition(Phase.DEALER_TURN)

            # Timeout: assume player stood
            if self.phase_elapsed > PHASE_TIMEOUTS[Phase.PLAYER_TURN]:
                self._acted = True
                return self._transition(Phase.DEALER_TURN)

        elif self.phase == Phase.DEALER_TURN:
            self._dealer_card_count = dealer_cards

            # Dealer has finished (no new cards for a while, or bust)
            if self.phase_elapsed > 5 and dealer_cards == self._dealer_card_count:
                return self._transition(Phase.RESULT)

            # Timeout
            if self.phase_elapsed > PHASE_TIMEOUTS[Phase.DEALER_TURN]:
                return self._transition(Phase.RESULT)

        elif self.phase == Phase.RESULT:
            # Cards disappeared → new hand
            if total_cards == 0 or (total_cards < self._last_card_count - 2):
                self.reset()
                return {"from": "result", "to": "waiting", "time": time.time()}

            # Timeout → force reset
            if self.phase_elapsed > PHASE_TIMEOUTS[Phase.RESULT]:
                self.reset()
                return {"from": "result", "to": "waiting", "time": time.time()}

        self._last_card_count = total_cards
        return None

    def get_state(self) -> dict:
        return {
            "phase": self.phase.value,
            "phase_elapsed": round(self.phase_elapsed, 1),
            "player_cards": self._player_card_count,
            "dealer_cards": self._dealer_card_count,
            "dealer_revealed": self._dealer_revealed,
            "acted": self._acted,
        }
