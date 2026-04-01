"""
AI-IN Peter — Test Suite
Run with: cd backend && python -m pytest ../tests/ -v
Or: cd backend && python ../tests/test_engine.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from engine.monte_carlo import (
    MonteCarloEquity, evaluate_hand, full_deck,
    parse_card, card_value, count_outs
)
from engine.decision import (
    DecisionEngine, categorize_preflop, categorize_postflop
)
from vision.card_recognition import (
    parse_card as cr_parse, normalize_card, normalize_card_list,
    validate_game_state_cards, remaining_deck, card_to_display
)
from engine.achievements import AchievementTracker


# ═══════════════════════════════════════════════════════════════════════
# HAND EVALUATION TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_royal_flush():
    hand = evaluate_hand(['Ah', 'Kh', 'Qh', 'Jh', '10h'])
    assert hand[0] == 9, f"Royal flush should be rank 9, got {hand[0]}"
    assert hand[2] == 'Royal Flush', f"Name should be 'Royal Flush', got {hand[2]}"
    print("  PASS: Royal flush")

def test_straight_flush():
    hand = evaluate_hand(['9s', '8s', '7s', '6s', '5s'])
    assert hand[0] == 8, f"Straight flush should be rank 8, got {hand[0]}"
    print("  PASS: Straight flush")

def test_four_of_a_kind():
    hand = evaluate_hand(['Ah', 'Ad', 'As', 'Ac', 'Kh'])
    assert hand[0] == 7, f"Four of a kind should be rank 7, got {hand[0]}"
    print("  PASS: Four of a kind")

def test_full_house():
    hand = evaluate_hand(['Ah', 'Ad', 'As', 'Kh', 'Kd'])
    assert hand[0] == 6, f"Full house should be rank 6, got {hand[0]}"
    print("  PASS: Full house")

def test_flush():
    hand = evaluate_hand(['Ah', 'Kh', '9h', '5h', '2h'])
    assert hand[0] == 5, f"Flush should be rank 5, got {hand[0]}"
    print("  PASS: Flush")

def test_straight():
    hand = evaluate_hand(['Ah', 'Kd', 'Qs', 'Jc', '10h'])
    assert hand[0] == 4, f"Straight should be rank 4, got {hand[0]}"
    print("  PASS: Straight")

def test_ace_low_straight():
    hand = evaluate_hand(['Ah', '2d', '3s', '4c', '5h'])
    assert hand[0] == 4, f"Ace-low straight should be rank 4, got {hand[0]}"
    print("  PASS: Ace-low straight (wheel)")

def test_three_of_a_kind():
    hand = evaluate_hand(['Ah', 'Ad', 'As', 'Kh', 'Qd'])
    assert hand[0] == 3, f"Three of a kind should be rank 3, got {hand[0]}"
    print("  PASS: Three of a kind")

def test_two_pair():
    hand = evaluate_hand(['Ah', 'Ad', 'Kh', 'Kd', 'Qs'])
    assert hand[0] == 2, f"Two pair should be rank 2, got {hand[0]}"
    print("  PASS: Two pair")

def test_one_pair():
    hand = evaluate_hand(['Ah', 'Ad', 'Kh', 'Qd', 'Js'])
    assert hand[0] == 1, f"One pair should be rank 1, got {hand[0]}"
    print("  PASS: One pair")

def test_high_card():
    hand = evaluate_hand(['Ah', 'Kd', '9s', '5c', '2h'])
    assert hand[0] == 0, f"High card should be rank 0, got {hand[0]}"
    print("  PASS: High card")

def test_best_five_from_seven():
    """Should find the best 5-card hand from 7 cards."""
    hand = evaluate_hand(['Ah', 'Kh', 'Qh', 'Jh', '10h', '2d', '3c'])
    assert hand[0] == 9, f"Should find royal flush in 7 cards, got rank {hand[0]}"
    print("  PASS: Best 5 from 7 cards")

def test_hand_comparison():
    """Higher ranked hand should win."""
    flush = evaluate_hand(['Ah', 'Kh', '9h', '5h', '2h'])
    straight = evaluate_hand(['Ah', 'Kd', 'Qs', 'Jc', '10h'])
    assert flush[0] > straight[0], "Flush should beat straight"
    print("  PASS: Hand comparison (flush > straight)")


# ═══════════════════════════════════════════════════════════════════════
# MONTE CARLO TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_monte_carlo_premium_hand():
    mc = MonteCarloEquity(iterations=2000)
    result = mc.calculate_equity(['Ah', 'Kh'], [])
    assert result['win_pct'] > 40, f"AKs should win >40% preflop, got {result['win_pct']}"
    assert result['win_pct'] < 90, f"AKs shouldn't win >90% preflop, got {result['win_pct']}"
    print(f"  PASS: Monte Carlo AKs preflop = {result['win_pct']:.1f}%")

def test_monte_carlo_made_hand():
    mc = MonteCarloEquity(iterations=2000)
    result = mc.calculate_equity(['Ah', 'Kh'], ['Qh', 'Jh', '10h'])
    assert result['win_pct'] > 80, f"Royal flush draw should win >80%, got {result['win_pct']}"
    assert result['hand_name'] == 'Royal Flush', f"Should be Royal Flush, got {result['hand_name']}"
    print(f"  PASS: Monte Carlo royal flush = {result['win_pct']:.1f}%")

def test_monte_carlo_weak_hand():
    mc = MonteCarloEquity(iterations=2000)
    result = mc.calculate_equity(['2h', '7c'], [])
    assert result['win_pct'] < 55, f"27o should win <55% preflop, got {result['win_pct']}"
    print(f"  PASS: Monte Carlo 27o preflop = {result['win_pct']:.1f}%")

def test_monte_carlo_empty_hand():
    mc = MonteCarloEquity(iterations=100)
    result = mc.calculate_equity([], [])
    assert result['win_pct'] == 0, "Empty hand should have 0% equity"
    print("  PASS: Monte Carlo empty hand = 0%")

def test_outs_counting():
    deck = [c for c in full_deck() if c not in ['Ah', 'Kh', 'Qh', 'Jh', '9d']]
    outs_info = count_outs(['Ah', 'Kh'], ['Qh', 'Jh', '9d'], deck[:20])
    assert outs_info['outs'] >= 0, "Outs should be non-negative"
    print(f"  PASS: Outs counting = {outs_info['outs']} outs")


# ═══════════════════════════════════════════════════════════════════════
# DECISION ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_preflop_categories():
    assert categorize_preflop(['Ah', 'Kh']) == 'premium', "AKs should be premium"
    assert categorize_preflop(['Ah', 'Ac']) == 'premium', "AA should be premium"
    assert categorize_preflop(['Jh', 'Jc']) == 'strong', "JJ should be strong"
    assert categorize_preflop(['7h', '7c']) == 'playable', "77 should be playable"
    assert categorize_preflop(['2h', '7c']) == 'trash', "27o should be trash"
    print("  PASS: Pre-flop categorization")

def test_postflop_categories():
    assert categorize_postflop(5, 'Flush', 75) == 'monster', "Flush should be monster"
    assert categorize_postflop(4, 'Straight', 70) == 'monster', "Straight should be monster"
    assert categorize_postflop(1, 'One Pair', 70) == 'good', "Strong pair should be good"
    assert categorize_postflop(0, 'High Card', 20) == 'nothing', "Weak high card should be nothing"
    print("  PASS: Post-flop categorization")

def test_pot_odds():
    engine = DecisionEngine()
    odds = engine.calculate_pot_odds({'pot_size': 100, 'current_bet': 25})
    assert odds == 4.0, f"100/25 should be 4.0:1, got {odds}"
    print("  PASS: Pot odds = 4.0:1")

def test_expected_value():
    engine = DecisionEngine()
    ev = engine.calculate_ev({'pot_size': 100, 'current_bet': 20}, {'win_pct': 60})
    assert ev > 0, f"60% win chance on 100 pot should be +EV, got {ev}"
    ev_neg = engine.calculate_ev({'pot_size': 50, 'current_bet': 40}, {'win_pct': 30})
    assert ev_neg < 0, f"30% win chance on 50 pot with 40 bet should be -EV, got {ev_neg}"
    print(f"  PASS: EV calculation = +${ev:.2f} / -${abs(ev_neg):.2f}")

def test_kelly_criterion():
    engine = DecisionEngine(kelly_fraction=0.25)
    bet = engine.kelly_bet_size(60, 3.0, 1000)
    assert 0 < bet < 200, f"Kelly bet should be reasonable, got {bet}"
    bet_neg = engine.kelly_bet_size(30, 1.0, 1000)
    assert bet_neg == 0, f"Negative edge should give 0 bet, got {bet_neg}"
    print(f"  PASS: Kelly criterion = ${bet:.2f} (positive), ${bet_neg:.2f} (negative)")

def test_gto_recommendation():
    engine = DecisionEngine()
    gto = engine.get_gto_recommendation(
        {'phase': 'pre_flop', 'hole_cards': ['Ah', 'Kh'], 'community_cards': []},
        {'hand_rank': 0, 'hand_name': '', 'win_pct': 67}
    )
    assert gto['raise'] > gto['fold'], "AKs should recommend raise > fold"
    assert sum(gto.values()) == 100, f"GTO should sum to 100, got {sum(gto.values())}"
    print(f"  PASS: GTO recommendation: fold={gto['fold']}% call={gto['call']}% raise={gto['raise']}%")

def test_dealer_qualification():
    engine = DecisionEngine()
    pct_empty = engine.estimate_dealer_qualification([])
    assert 40 <= pct_empty <= 70, f"Empty board should be ~55%, got {pct_empty}"
    pct_pair = engine.estimate_dealer_qualification(['Ah', 'Ad', '5c'])
    assert pct_pair > pct_empty, "Board pair should increase dealer qualification"
    print(f"  PASS: Dealer qualification = {pct_empty}% (empty), {pct_pair}% (pair on board)")


# ═══════════════════════════════════════════════════════════════════════
# CARD RECOGNITION TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_card_parsing():
    assert cr_parse('Ah') == ('A', 'h'), "Basic parse"
    assert cr_parse('10s') == ('10', 's'), "10 parse"
    assert cr_parse('Kd') == ('K', 'd'), "King parse"
    assert cr_parse('2c') == ('2', 'c'), "Deuce parse"
    assert cr_parse('') is None, "Empty string"
    assert cr_parse('Xx') is None, "Invalid card"
    print("  PASS: Card parsing (6 cases)")

def test_card_normalization():
    assert normalize_card('ah') == 'Ah', "Lowercase to standard"
    assert normalize_card('10S') == '10s', "Uppercase suit"
    assert normalize_card('invalid') is None, "Invalid returns None"
    print("  PASS: Card normalization")

def test_card_list_normalization():
    result = normalize_card_list(['Ah', 'invalid', 'Kd', '', '10s'])
    assert result == ['Ah', 'Kd', '10s'], f"Should filter invalid, got {result}"
    print("  PASS: Card list normalization")

def test_card_display():
    assert card_to_display('Ah') == 'A\u2665', "Hearts display"
    assert card_to_display('Ks') == 'K\u2660', "Spades display"
    print("  PASS: Card display formatting")

def test_duplicate_detection():
    state = validate_game_state_cards({
        'hole_cards': ['Ah', 'Kd'],
        'community_cards': ['Ah', 'Qs', '10c'],  # Ah is duplicate
    })
    all_cards = state['hole_cards'] + state['community_cards']
    assert len(all_cards) == len(set(all_cards)), "Should remove duplicate cards"
    print("  PASS: Duplicate card detection")

def test_remaining_deck():
    known = ['Ah', 'Kd', 'Qs', 'Jh', '10c']
    deck = remaining_deck(known)
    assert len(deck) == 47, f"52 - 5 = 47, got {len(deck)}"
    for card in known:
        assert card not in deck, f"{card} should not be in remaining deck"
    print("  PASS: Remaining deck = 47 cards")


# ═══════════════════════════════════════════════════════════════════════
# ACHIEVEMENT TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_first_win_achievement():
    tracker = AchievementTracker()
    result = tracker.update({"pnl": 10, "bankroll": 1510, "confidence": 80, "hand_rank": 1})
    names = [a["key"] for a in result]
    assert "first_blood" in names, "Should unlock 'first_blood' on first win"
    print("  PASS: First win achievement")

def test_no_duplicate_achievements():
    tracker = AchievementTracker()
    tracker.update({"pnl": 10, "bankroll": 1510, "confidence": 80, "hand_rank": 1})
    result2 = tracker.update({"pnl": 10, "bankroll": 1520, "confidence": 80, "hand_rank": 1})
    names2 = [a["key"] for a in result2]
    assert "first_blood" not in names2, "Should not unlock same achievement twice"
    print("  PASS: No duplicate achievements")

def test_royal_flush_achievement():
    tracker = AchievementTracker()
    result = tracker.update({"pnl": 50, "bankroll": 1550, "confidence": 99, "hand_rank": 9})
    names = [a["key"] for a in result]
    assert "royal_flush" in names, "Should unlock royal flush achievement"
    assert "straight_flush" in names, "Royal flush should also trigger straight flush"
    assert "four_kind" in names, "Royal flush should also trigger four of a kind"
    print("  PASS: Royal flush cascading achievements")

def test_grinder_achievement():
    tracker = AchievementTracker()
    for i in range(49):
        tracker.update({"pnl": 0, "bankroll": 1500, "confidence": 50, "hand_rank": 0})
    result = tracker.update({"pnl": 0, "bankroll": 1500, "confidence": 50, "hand_rank": 0})
    names = [a["key"] for a in result]
    assert "fifty_hands" in names, "Should unlock 'The grinder' at 50 hands"
    print("  PASS: Grinder achievement at 50 hands")

def test_get_all_achievements():
    tracker = AchievementTracker()
    all_achs = tracker.get_all()
    assert len(all_achs) > 10, f"Should have 10+ achievements defined, got {len(all_achs)}"
    assert all("name" in a for a in all_achs), "All achievements should have a name"
    print(f"  PASS: All achievements = {len(all_achs)} defined")


# ═══════════════════════════════════════════════════════════════════════
# RUN ALL TESTS
# ═══════════════════════════════════════════════════════════════════════

def run_all():
    print("\n🃏 AI-IN Peter — Test Suite\n")

    sections = [
        ("Hand Evaluation", [
            test_royal_flush, test_straight_flush, test_four_of_a_kind,
            test_full_house, test_flush, test_straight, test_ace_low_straight,
            test_three_of_a_kind, test_two_pair, test_one_pair, test_high_card,
            test_best_five_from_seven, test_hand_comparison,
        ]),
        ("Monte Carlo Engine", [
            test_monte_carlo_premium_hand, test_monte_carlo_made_hand,
            test_monte_carlo_weak_hand, test_monte_carlo_empty_hand,
            test_outs_counting,
        ]),
        ("Decision Engine", [
            test_preflop_categories, test_postflop_categories,
            test_pot_odds, test_expected_value, test_kelly_criterion,
            test_gto_recommendation, test_dealer_qualification,
        ]),
        ("Card Recognition", [
            test_card_parsing, test_card_normalization,
            test_card_list_normalization, test_card_display,
            test_duplicate_detection, test_remaining_deck,
        ]),
        ("Achievements", [
            test_first_win_achievement, test_no_duplicate_achievements,
            test_royal_flush_achievement, test_grinder_achievement,
            test_get_all_achievements,
        ]),
    ]

    total = 0
    passed = 0
    failed = 0

    for section_name, tests in sections:
        print(f"--- {section_name} ---")
        for test_fn in tests:
            total += 1
            try:
                test_fn()
                passed += 1
            except AssertionError as e:
                failed += 1
                print(f"  FAIL: {test_fn.__name__} — {e}")
            except Exception as e:
                failed += 1
                print(f"  ERROR: {test_fn.__name__} — {e}")
        print()

    print(f"{'='*50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("All tests passed! Peter is ready to play.")
    else:
        print(f"{failed} test(s) failed. Fix before deploying!")
    print()

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
