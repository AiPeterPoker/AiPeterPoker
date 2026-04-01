"""
Tests for the Blackjack engine: hand evaluation, basic strategy, card counting.
Run: python tests/test_blackjack.py
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from engine.blackjack.hand import BlackjackHand
from engine.blackjack.basic_strategy import (
    get_action, should_take_insurance, dealer_upcard_value,
    H, S, D, P,
)
from engine.blackjack.card_counter import CardCounter
from engine.blackjack.game_state_machine import BlackjackStateMachine, Phase


class TestBlackjackHand(unittest.TestCase):

    def test_simple_total(self):
        h = BlackjackHand(["5h", "3d"])
        self.assertEqual(h.total, 8)
        self.assertFalse(h.is_soft)
        self.assertFalse(h.is_busted)

    def test_face_cards(self):
        h = BlackjackHand(["Kh", "Qd"])
        self.assertEqual(h.total, 20)

    def test_ace_soft(self):
        h = BlackjackHand(["Ah", "6d"])
        self.assertEqual(h.total, 17)
        self.assertTrue(h.is_soft)

    def test_ace_hard(self):
        h = BlackjackHand(["Ah", "6d", "8s"])
        self.assertEqual(h.total, 15)
        self.assertFalse(h.is_soft)

    def test_two_aces(self):
        h = BlackjackHand(["Ah", "Ad"])
        self.assertEqual(h.total, 12)
        self.assertTrue(h.is_soft)

    def test_blackjack(self):
        h = BlackjackHand(["Ah", "Kd"])
        self.assertTrue(h.is_blackjack)
        self.assertEqual(h.total, 21)

    def test_not_blackjack_three_cards(self):
        h = BlackjackHand(["7h", "7d", "7s"])
        self.assertEqual(h.total, 21)
        self.assertFalse(h.is_blackjack)

    def test_bust(self):
        h = BlackjackHand(["Kh", "Qd", "5s"])
        self.assertTrue(h.is_busted)
        self.assertEqual(h.total, 25)

    def test_pair(self):
        h = BlackjackHand(["8h", "8d"])
        self.assertTrue(h.is_pair)
        self.assertEqual(h.pair_value, 8)

    def test_pair_face_cards(self):
        h = BlackjackHand(["Kh", "Qd"])
        self.assertTrue(h.is_pair)  # Both value 10
        self.assertEqual(h.pair_value, 10)

    def test_not_pair_three_cards(self):
        h = BlackjackHand(["8h", "8d", "3s"])
        self.assertFalse(h.is_pair)

    def test_add_card(self):
        h = BlackjackHand(["5h", "3d"])
        h.add_card("Ah")
        self.assertEqual(h.total, 19)
        self.assertTrue(h.is_soft)


class TestBasicStrategy(unittest.TestCase):

    def test_hard_16_vs_10_stand(self):
        """16 vs 10 normally hits, but at TC >= 0 should stand (Illustrious 18)."""
        h = BlackjackHand(["10h", "6d"])
        result = get_action(h, 10, true_count=0)
        self.assertEqual(result["action"], S)
        self.assertTrue(result["is_deviation"])

    def test_hard_16_vs_10_hit_negative_count(self):
        h = BlackjackHand(["10h", "6d"])
        result = get_action(h, 10, true_count=-1)
        self.assertEqual(result["action"], H)

    def test_always_split_aces(self):
        h = BlackjackHand(["Ah", "Ad"])
        result = get_action(h, 6)
        self.assertEqual(result["action"], P)

    def test_always_split_eights(self):
        h = BlackjackHand(["8h", "8d"])
        result = get_action(h, 10)
        self.assertEqual(result["action"], P)

    def test_never_split_tens(self):
        h = BlackjackHand(["Kh", "Qd"])
        result = get_action(h, 6)
        self.assertEqual(result["action"], S)

    def test_double_11_vs_6(self):
        h = BlackjackHand(["6h", "5d"])
        result = get_action(h, 6)
        self.assertEqual(result["action"], D)

    def test_double_downgrade_to_hit(self):
        """Can't double after 3+ cards."""
        h = BlackjackHand(["4h", "3d", "4s"])
        result = get_action(h, 6, can_double=False)
        self.assertEqual(result["action"], H)

    def test_soft_18_vs_2(self):
        h = BlackjackHand(["Ah", "7d"])
        result = get_action(h, 2)
        # Ds → double if possible, stand otherwise
        self.assertIn(result["action"], [D, S])

    def test_soft_18_vs_9_hit(self):
        h = BlackjackHand(["Ah", "7d"])
        result = get_action(h, 9)
        self.assertEqual(result["action"], H)

    def test_hard_17_always_stand(self):
        h = BlackjackHand(["10h", "7d"])
        for dealer in range(2, 12):
            result = get_action(h, dealer)
            self.assertEqual(result["action"], S, f"17 vs {dealer} should stand")

    def test_hard_12_vs_4_stand(self):
        h = BlackjackHand(["10h", "2d"])
        result = get_action(h, 4)
        self.assertEqual(result["action"], S)

    def test_hard_12_vs_2_hit(self):
        h = BlackjackHand(["10h", "2d"])
        result = get_action(h, 2)
        self.assertEqual(result["action"], H)

    def test_insurance_positive_count(self):
        self.assertTrue(should_take_insurance(3.0))
        self.assertTrue(should_take_insurance(5.0))

    def test_insurance_negative_count(self):
        self.assertFalse(should_take_insurance(2.0))
        self.assertFalse(should_take_insurance(None))

    def test_dealer_upcard_value(self):
        self.assertEqual(dealer_upcard_value("Ah"), 11)
        self.assertEqual(dealer_upcard_value("Kd"), 10)
        self.assertEqual(dealer_upcard_value("7s"), 7)


class TestCardCounter(unittest.TestCase):

    def test_initial_state(self):
        c = CardCounter(num_decks=6)
        self.assertEqual(c.running_count, 0)
        self.assertEqual(c.cards_seen, 0)
        self.assertAlmostEqual(c.true_count, 0)

    def test_count_low_cards(self):
        c = CardCounter(num_decks=6)
        for card in ["2h", "3d", "4s", "5c", "6h"]:
            c.count_card(card)
        self.assertEqual(c.running_count, 5)

    def test_count_high_cards(self):
        c = CardCounter(num_decks=6)
        for card in ["Kh", "Qd", "Js", "10c", "Ah"]:
            c.count_card(card)
        self.assertEqual(c.running_count, -5)

    def test_count_neutral_cards(self):
        c = CardCounter(num_decks=6)
        for card in ["7h", "8d", "9s"]:
            c.count_card(card)
        self.assertEqual(c.running_count, 0)

    def test_true_count(self):
        c = CardCounter(num_decks=6)
        # Count 12 low cards → RC = +12
        for rank in ["2", "3", "4", "5", "6", "2"]:
            c.count_card(f"{rank}h")
        for rank in ["3", "4", "5", "6", "2", "3"]:
            c.count_card(f"{rank}d")
        self.assertEqual(c.running_count, 12)
        # ~5.77 decks remaining → TC ≈ 2.08
        self.assertAlmostEqual(c.true_count, 12 / c.decks_remaining, places=1)

    def test_reset(self):
        c = CardCounter(num_decks=6)
        c.count_card("Ah")
        c.reset()
        self.assertEqual(c.running_count, 0)
        self.assertEqual(c.cards_seen, 0)

    def test_bet_recommendation_neutral(self):
        c = CardCounter(num_decks=6)
        bet = c.bet_recommendation(min_bet=1.0)
        self.assertEqual(bet["bet_units"], 1)
        self.assertFalse(bet["favorable"])

    def test_bet_recommendation_positive(self):
        c = CardCounter(num_decks=6)
        # Force high true count
        c.running_count = 18
        c.cards_seen = 52  # 1 deck seen → 5 remaining → TC = 3.6
        bet = c.bet_recommendation(min_bet=1.0)
        self.assertGreater(bet["bet_units"], 1)
        self.assertTrue(bet["favorable"])

    def test_hi_lo_value_static(self):
        self.assertEqual(CardCounter.hi_lo_value("2h"), 1)
        self.assertEqual(CardCounter.hi_lo_value("7d"), 0)
        self.assertEqual(CardCounter.hi_lo_value("Ks"), -1)
        self.assertEqual(CardCounter.hi_lo_value("Ah"), -1)


class TestIllustrious18(unittest.TestCase):

    def test_16_vs_10_stand_at_0(self):
        h = BlackjackHand(["10h", "6d"])
        r = get_action(h, 10, true_count=0.0)
        self.assertEqual(r["action"], S)
        self.assertTrue(r["is_deviation"])

    def test_15_vs_10_stand_at_4(self):
        h = BlackjackHand(["10h", "5d"])
        r = get_action(h, 10, true_count=4.0)
        self.assertEqual(r["action"], S)
        self.assertTrue(r["is_deviation"])

    def test_15_vs_10_hit_at_3(self):
        h = BlackjackHand(["10h", "5d"])
        r = get_action(h, 10, true_count=3.0)
        self.assertEqual(r["action"], H)
        self.assertFalse(r["is_deviation"])

    def test_12_vs_3_stand_at_2(self):
        h = BlackjackHand(["10h", "2d"])
        r = get_action(h, 3, true_count=2.0)
        self.assertEqual(r["action"], S)
        self.assertTrue(r["is_deviation"])

    def test_12_vs_2_stand_at_3(self):
        h = BlackjackHand(["10h", "2d"])
        r = get_action(h, 2, true_count=3.0)
        self.assertEqual(r["action"], S)
        self.assertTrue(r["is_deviation"])

    def test_13_vs_2_hit_at_neg1(self):
        """Negative deviation: 13 vs 2 hit at TC <= -1."""
        h = BlackjackHand(["10h", "3d"])
        r = get_action(h, 2, true_count=-1.0)
        self.assertEqual(r["action"], H)
        self.assertTrue(r["is_deviation"])

    def test_13_vs_2_stand_at_0(self):
        """Normal basic strategy: 13 vs 2 stand."""
        h = BlackjackHand(["10h", "3d"])
        r = get_action(h, 2, true_count=0.0)
        self.assertEqual(r["action"], S)
        self.assertFalse(r["is_deviation"])


class TestStateMachine(unittest.TestCase):

    def test_initial_phase(self):
        sm = BlackjackStateMachine()
        self.assertEqual(sm.phase, Phase.WAITING)

    def test_waiting_to_player_turn(self):
        sm = BlackjackStateMachine()
        t = sm.process(player_cards=2, dealer_cards=1)
        self.assertIsNotNone(t)
        self.assertEqual(sm.phase, Phase.PLAYER_TURN)

    def test_player_to_dealer_turn(self):
        sm = BlackjackStateMachine()
        sm.process(player_cards=2, dealer_cards=1)
        t = sm.process(player_cards=2, dealer_cards=2, dealer_hole_visible=True)
        self.assertIsNotNone(t)
        self.assertEqual(sm.phase, Phase.DEALER_TURN)

    def test_reset_on_card_disappear(self):
        sm = BlackjackStateMachine()
        sm.process(player_cards=2, dealer_cards=1)
        sm.process(player_cards=2, dealer_cards=2, dealer_hole_visible=True)
        # Force to result
        sm.phase = Phase.RESULT
        sm._phase_start = 0  # Trigger timeout
        t = sm.process(player_cards=0, dealer_cards=0)
        self.assertEqual(sm.phase, Phase.WAITING)


if __name__ == "__main__":
    unittest.main()
