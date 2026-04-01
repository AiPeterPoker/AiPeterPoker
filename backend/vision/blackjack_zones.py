"""
Table zone definitions for Evolution Infinite Blackjack on Solcasino.io.

Evolution layout (live dealer, top-down camera):
- Dealer cards: center-top area, on the green felt
- Player cards: bottom-center, larger cards closer to camera
- "MAKE YOUR DECISION" text appears between dealer and player
- Action buttons (HIT/STAND/DOUBLE/SPLIT): bottom bar
- Balance: bottom-right

Adjusted from foto10.png observations.
Infinite Blackjack uses 8 decks.
"""

BLACKJACK_TABLE_ZONES = {
    "DEALER": {
        "region_y": 0.25, "region_h": 0.25,
        "region_x": 0.15, "region_w": 0.70,
        "max_cards": 7, "color": "mesa", "detect_facedown": True,
    },
    "PLAYER": {
        "region_y": 0.65, "region_h": 0.25,
        "region_x": 0.10, "region_w": 0.80,
        "max_cards": 7, "color": "player", "detect_facedown": False,
    },
    "PLAYER_SPLIT": {
        "region_y": 0.50, "region_h": 0.18,
        "region_x": 0.10, "region_w": 0.80,
        "max_cards": 7, "color": "player", "detect_facedown": False,
    },
    "BALANCE": {
        "region_y": 0.92, "region_h": 0.06,
        "region_x": 0.70, "region_w": 0.28,
        "max_cards": 0, "color": "balance", "detect_facedown": False,
    },
}
