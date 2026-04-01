"""
Casino Hold'em Game State Machine
Manages the lifecycle of each hand with clear state transitions.

States:
  IDLE        → No game detected, waiting for table
  WAITING     → "WAIT FOR NEXT GAME" screen, ready to ante
  BETTING     → Ante placed, waiting for cards to be dealt
  CARDS_DEALT → Cards visible, need to read them
  DECIDING    → Cards read, calculating decision
  ACTED       → Play/Fold clicked, waiting for showdown
  SHOWDOWN    → Dealer reveals, animation playing
  RESULT      → Hand complete, record result
  (→ back to WAITING)

Each state knows:
  - What to look for (ESP signals)
  - What action to take
  - When to transition to next state
  - Timeout (auto-transition if stuck)
"""

import time
from enum import Enum
from typing import Optional


class GamePhase(Enum):
    IDLE = "idle"
    WAITING = "waiting"
    BETTING = "betting"
    CARDS_DEALT = "cards_dealt"
    DECIDING = "deciding"
    ACTED = "acted"
    SHOWDOWN = "showdown"
    RESULT = "result"


class GameStateMachine:
    def __init__(self):
        self.phase = GamePhase.IDLE
        self.phase_entered_at: float = time.time()
        self.hand_number: int = 0
        self.current_hand: dict = {}
        self.last_decision: Optional[dict] = None
        self._prev_face_up_count: int = 0
        self._prev_card_sig: str = ""

    @property
    def phase_duration(self) -> float:
        """Seconds spent in current phase."""
        return time.time() - self.phase_entered_at

    def transition(self, new_phase: GamePhase, reason: str = "") -> str:
        """Transition to a new phase. Returns log message."""
        old = self.phase
        self.phase = new_phase
        self.phase_entered_at = time.time()
        msg = f"{old.value} -> {new_phase.value}"
        if reason:
            msg += f" ({reason})"
        return msg

    def process_esp(self, card_regions: list[dict]) -> Optional[str]:
        """Process ESP data and determine if a state transition should happen.
        Returns transition message or None.
        """
        face_up = [c for c in card_regions if c.get("face") == "up" and not c.get("is_zone")]
        face_down = [c for c in card_regions if c.get("face") == "down" and not c.get("is_zone")]
        has_face = any(c.get("face") == "tracker" for c in card_regions)
        n_face_up = len(face_up)

        card_sig = f"{n_face_up}:" + ",".join(
            f"{c['x']//20}_{c['y']//20}" for c in face_up
        )

        # Build named cards list
        named_cards = [(c.get("card_name"), c.get("zone")) for c in face_up if c.get("card_name")]

        result = None

        if self.phase == GamePhase.IDLE:
            # Detected a table (face found)
            if has_face:
                result = self.transition(GamePhase.WAITING, "table detected")

        elif self.phase == GamePhase.WAITING:
            # No cards visible, waiting for ante or new deal
            if n_face_up > 0:
                result = self.transition(GamePhase.CARDS_DEALT, f"{n_face_up} cards appeared")
            elif self.phase_duration > 30:
                # Stuck waiting too long
                result = self.transition(GamePhase.WAITING, "timeout reset")

        elif self.phase == GamePhase.BETTING:
            # Ante placed, waiting for cards
            if n_face_up > 0:
                result = self.transition(GamePhase.CARDS_DEALT, f"{n_face_up} cards dealt")
            elif self.phase_duration > 8:
                # Ante click might have failed
                result = self.transition(GamePhase.WAITING, "betting timeout")

        elif self.phase == GamePhase.CARDS_DEALT:
            # Cards visible, check if we have names for them
            player_named = [n for n, z in named_cards if z == "player"]
            if len(player_named) >= 2:
                self.current_hand = {
                    "hole_cards": player_named,
                    "community_cards": [n for n, z in named_cards if z == "mesa"],
                }
                result = self.transition(GamePhase.DECIDING, f"hole={player_named}")
            elif self.phase_duration > 5:
                # Cards detected but can't read names — try anyway with what we have
                if named_cards:
                    self.current_hand = {
                        "hole_cards": [n for n, z in named_cards if z == "player"],
                        "community_cards": [n for n, z in named_cards if z == "mesa"],
                    }
                    result = self.transition(GamePhase.DECIDING, "partial read, proceeding")

        elif self.phase == GamePhase.DECIDING:
            # Waiting for decision engine — this is handled by capture_loop
            if self.phase_duration > 10:
                result = self.transition(GamePhase.WAITING, "decision timeout")

        elif self.phase == GamePhase.ACTED:
            # Clicked play/fold, waiting for showdown animation
            if n_face_up == 0 and self.phase_duration > 2:
                # Cards disappeared — hand over
                result = self.transition(GamePhase.RESULT, "cards cleared")
            elif card_sig != self._prev_card_sig and n_face_up > self._prev_face_up_count:
                # New cards appeared (turn/river or showdown)
                pass  # Stay in ACTED, still resolving
            elif self.phase_duration > 8:
                # Showdown taking too long, force transition
                result = self.transition(GamePhase.RESULT, "showdown timeout")

        elif self.phase == GamePhase.SHOWDOWN:
            if n_face_up == 0 and self.phase_duration > 1:
                result = self.transition(GamePhase.RESULT, "cards cleared")
            elif self.phase_duration > 10:
                result = self.transition(GamePhase.RESULT, "showdown timeout")

        elif self.phase == GamePhase.RESULT:
            # Record result, then go back to waiting
            self.hand_number += 1
            self.current_hand = {}
            self.last_decision = None
            result = self.transition(GamePhase.WAITING, f"hand #{self.hand_number} complete")

        # Save state for next frame
        self._prev_face_up_count = n_face_up
        self._prev_card_sig = card_sig

        return result

    def mark_ante_clicked(self) -> str:
        """Called when ante button is clicked."""
        return self.transition(GamePhase.BETTING, "ante clicked")

    def mark_decision_made(self, decision: dict) -> str:
        """Called when play/fold decision is executed."""
        self.last_decision = decision
        action = decision.get("action", "?")
        return self.transition(GamePhase.ACTED, f"{action} clicked")

    def should_click_ante(self) -> bool:
        """Should we auto-click ante?"""
        return self.phase == GamePhase.WAITING and self.phase_duration > 1.5

    def should_read_cards(self) -> bool:
        """Should we try to read/identify cards?"""
        return self.phase == GamePhase.CARDS_DEALT

    def should_decide(self) -> bool:
        """Should we run the decision engine?"""
        return self.phase == GamePhase.DECIDING

    def should_clear_ui(self) -> bool:
        """Should we clear the UI (old cards)?"""
        return self.phase in (GamePhase.RESULT, GamePhase.WAITING) and self.phase_duration < 0.5

    def needs_card_cache_clear(self) -> bool:
        """Should we clear the card template cache?"""
        return self.phase == GamePhase.RESULT
