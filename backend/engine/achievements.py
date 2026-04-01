"""
AI-IN Peter — Achievements System
Tracks milestones and unlocks badges with Peter-style quips.
"""

from typing import Optional


ACHIEVEMENTS = {
    "first_blood": {
        "name": "First blood",
        "desc": "Win your first hand",
        "icon": "1",
        "condition": lambda s: s["wins"] >= 1,
        "quip": "We're in business, baby! First win in the bag!",
    },
    "ten_streak": {
        "name": "Hot streak",
        "desc": "Win 10 hands total",
        "icon": "10",
        "condition": lambda s: s["wins"] >= 10,
        "quip": "Ten wins! I'm like a poker machine... which I literally am.",
    },
    "fifty_hands": {
        "name": "The grinder",
        "desc": "Play 50 hands",
        "icon": "50",
        "condition": lambda s: s["hands"] >= 50,
        "quip": "Fifty hands deep. This is a marathon, not a sprint. Actually it's both.",
    },
    "hundred_club": {
        "name": "Century club",
        "desc": "Play 100 hands",
        "icon": "100",
        "condition": lambda s: s["hands"] >= 100,
        "quip": "ONE HUNDRED HANDS! I deserve a trophy. And a beer.",
    },
    "five_hundred": {
        "name": "Iron butt",
        "desc": "Play 500 hands in one session",
        "icon": "500",
        "condition": lambda s: s["hands"] >= 500,
        "quip": "500 hands. My butt is numb but my bankroll isn't.",
    },
    "big_winner": {
        "name": "Big winner",
        "desc": "Win $100+ in a session",
        "icon": "$",
        "condition": lambda s: s["pnl"] >= 100,
        "quip": "A hundred bucks profit! That's like... a lot of beers at The Clam!",
    },
    "whale": {
        "name": "The whale",
        "desc": "Win $500+ in a session",
        "icon": "W",
        "condition": lambda s: s["pnl"] >= 500,
        "quip": "FIVE HUNDRED DOLLARS! I'm basically a professional now!",
    },
    "comeback_kid": {
        "name": "Comeback kid",
        "desc": "Go from -$50 to positive in a session",
        "icon": "CK",
        "condition": lambda s: s.get("was_down_50") and s["pnl"] > 0,
        "quip": "From the ashes, like a beautiful, mathematically optimal phoenix!",
    },
    "perfect_read": {
        "name": "Perfect read",
        "desc": "Win with 95%+ confidence",
        "icon": "PR",
        "condition": lambda s: s.get("last_conf", 0) >= 95 and s.get("last_won", False),
        "quip": "95% confidence and I nailed it. The math is ALWAYS right!",
    },
    "royal_flush": {
        "name": "Royal treatment",
        "desc": "Get a royal flush",
        "icon": "RF",
        "condition": lambda s: s.get("best_hand_rank", 0) >= 9,
        "quip": "ROYAL FLUSH! This is the greatest moment of my life! After Stewie was born. Maybe.",
    },
    "straight_flush": {
        "name": "Straight and narrow",
        "desc": "Get a straight flush",
        "icon": "SF",
        "condition": lambda s: s.get("best_hand_rank", 0) >= 8,
        "quip": "Straight flush! The probability gods smile upon Peter Griffin!",
    },
    "four_kind": {
        "name": "Quad damage",
        "desc": "Get four of a kind",
        "icon": "4K",
        "condition": lambda s: s.get("best_hand_rank", 0) >= 7,
        "quip": "FOUR OF A KIND! That's like having quadruplets but way better!",
    },
    "gto_master": {
        "name": "GTO master",
        "desc": "Follow GTO for 20 consecutive hands",
        "icon": "GT",
        "condition": lambda s: s.get("gto_streak", 0) >= 20,
        "quip": "Twenty hands of pure GTO. I'm basically a computer. Wait, I AM a computer.",
    },
    "kelly_disciple": {
        "name": "Kelly's disciple",
        "desc": "Stay within Kelly bounds for 50 hands",
        "icon": "K",
        "condition": lambda s: s.get("kelly_streak", 0) >= 50,
        "quip": "Fifty hands of disciplined sizing. Kelly would be proud. Whoever she is.",
    },
    "twitch_favorite": {
        "name": "Chat's favorite",
        "desc": "Get 50+ votes in a single round",
        "icon": "TV",
        "condition": lambda s: s.get("max_votes", 0) >= 50,
        "quip": "Fifty people voted! I'm more popular than Brian's podcast!",
    },
    "survivor": {
        "name": "Survivor",
        "desc": "Play 200 hands without going bust",
        "icon": "SV",
        "condition": lambda s: s["hands"] >= 200 and s["bankroll"] > 0,
        "quip": "200 hands and still standing. Bankroll management, baby!",
    },
    "double_up": {
        "name": "Double up",
        "desc": "Double your starting bankroll",
        "icon": "2x",
        "condition": lambda s: s["bankroll"] >= s.get("starting_bankroll", 1500) * 2,
        "quip": "DOUBLED THE BANKROLL! This calls for TWO beers!",
    },
}


class AchievementTracker:
    def __init__(self):
        self.unlocked: set = set()
        self.state = {
            "hands": 0,
            "wins": 0,
            "pnl": 0.0,
            "bankroll": 1500,
            "starting_bankroll": 1500,
            "best_hand_rank": 0,
            "gto_streak": 0,
            "kelly_streak": 0,
            "max_votes": 0,
            "was_down_50": False,
            "last_conf": 0,
            "last_won": False,
        }

    def update(self, hand_result: dict) -> list[dict]:
        """
        Update tracker state and check for newly unlocked achievements.
        Returns list of newly unlocked achievement dicts.
        """
        self.state["hands"] += 1
        pnl = hand_result.get("pnl", 0)
        self.state["pnl"] += pnl
        self.state["bankroll"] = hand_result.get("bankroll", self.state["bankroll"])
        self.state["last_conf"] = hand_result.get("confidence", 0)
        self.state["last_won"] = pnl > 0

        if pnl > 0:
            self.state["wins"] += 1

        hand_rank = hand_result.get("hand_rank", 0)
        if hand_rank > self.state["best_hand_rank"]:
            self.state["best_hand_rank"] = hand_rank

        if self.state["pnl"] <= -50:
            self.state["was_down_50"] = True

        # GTO streak
        if hand_result.get("followed_gto", False):
            self.state["gto_streak"] += 1
        else:
            self.state["gto_streak"] = 0

        # Kelly streak
        if hand_result.get("within_kelly", True):
            self.state["kelly_streak"] += 1
        else:
            self.state["kelly_streak"] = 0

        # Twitch votes
        votes = hand_result.get("total_votes", 0)
        if votes > self.state["max_votes"]:
            self.state["max_votes"] = votes

        # Check for new achievements
        newly_unlocked = []
        for key, ach in ACHIEVEMENTS.items():
            if key not in self.unlocked:
                try:
                    if ach["condition"](self.state):
                        self.unlocked.add(key)
                        newly_unlocked.append({
                            "key": key,
                            "name": ach["name"],
                            "desc": ach["desc"],
                            "icon": ach["icon"],
                            "quip": ach["quip"],
                        })
                except Exception:
                    pass

        return newly_unlocked

    def get_all(self) -> list[dict]:
        """Get all achievements with unlocked status."""
        result = []
        for key, ach in ACHIEVEMENTS.items():
            result.append({
                "key": key,
                "name": ach["name"],
                "desc": ach["desc"],
                "icon": ach["icon"],
                "unlocked": key in self.unlocked,
            })
        return result

    def get_unlocked(self) -> list[dict]:
        """Get only unlocked achievements."""
        return [a for a in self.get_all() if a["unlocked"]]
