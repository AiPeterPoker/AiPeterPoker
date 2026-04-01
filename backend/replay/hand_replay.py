"""
AI-IN Peter — Hand Replay System
Browse, search, and analyze past hands with Peter's full reasoning.
"""

import json
from typing import Optional
from datetime import datetime

import aiosqlite
from db.session import DB_PATH


class HandReplay:
    def __init__(self):
        self.db_path = str(DB_PATH)

    async def get_hand(self, hand_id: int) -> Optional[dict]:
        """Get a single hand with full details."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM hands WHERE id = ?", (hand_id,))
            row = await cursor.fetchone()
            if row:
                return self._format_hand(dict(row))
        return None

    async def get_session_hands(self, session_id: int, limit: int = 100) -> list[dict]:
        """Get all hands from a session for replay."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM hands WHERE session_id = ? ORDER BY hand_number LIMIT ?",
                (session_id, limit),
            )
            rows = await cursor.fetchall()
            return [self._format_hand(dict(r)) for r in rows]

    async def get_recent_hands(self, limit: int = 20) -> list[dict]:
        """Get most recent hands across all sessions."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM hands ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = await cursor.fetchall()
            return [self._format_hand(dict(r)) for r in rows]

    async def get_best_hands(self, limit: int = 10) -> list[dict]:
        """Get hands with highest PnL."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM hands WHERE pnl > 0 ORDER BY pnl DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [self._format_hand(dict(r)) for r in rows]

    async def get_worst_hands(self, limit: int = 10) -> list[dict]:
        """Get hands with lowest PnL."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM hands WHERE pnl < 0 ORDER BY pnl ASC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [self._format_hand(dict(r)) for r in rows]

    async def search_hands(self, hand_name: str = None, action: str = None, min_confidence: int = None) -> list[dict]:
        """Search hands by criteria."""
        conditions = []
        params = []

        if hand_name:
            conditions.append("hand_name LIKE ?")
            params.append(f"%{hand_name}%")
        if action:
            conditions.append("decision_action = ?")
            params.append(action)
        if min_confidence is not None:
            conditions.append("decision_confidence >= ?")
            params.append(min_confidence)

        where = " AND ".join(conditions) if conditions else "1=1"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                f"SELECT * FROM hands WHERE {where} ORDER BY id DESC LIMIT 50",
                params,
            )
            rows = await cursor.fetchall()
            return [self._format_hand(dict(r)) for r in rows]

    async def get_analytics(self, session_id: int = None) -> dict:
        """Get analytics data for charts."""
        where = f"WHERE session_id = {session_id}" if session_id else ""

        async with aiosqlite.connect(self.db_path) as db:
            # PnL over time
            cursor = await db.execute(f"""
                SELECT hand_number, pnl,
                       SUM(pnl) OVER (ORDER BY id) as cumulative_pnl,
                       win_probability, decision_confidence, hand_name,
                       decision_action
                FROM hands {where}
                ORDER BY id
            """)
            rows = await cursor.fetchall()

            pnl_series = []
            action_dist = {"fold": 0, "call": 0, "raise": 0}
            hand_dist = {}
            confidence_buckets = {f"{i*10}-{i*10+9}": 0 for i in range(10)}
            win_when_confident = {"high": {"wins": 0, "total": 0}, "low": {"wins": 0, "total": 0}}

            for row in rows:
                hand_num, pnl, cum_pnl, win_prob, conf, hand_name, action = row

                pnl_series.append({
                    "hand": hand_num,
                    "pnl": pnl or 0,
                    "cumulative": cum_pnl or 0,
                    "win_prob": win_prob or 0,
                    "confidence": conf or 0,
                })

                if action:
                    action_dist[action] = action_dist.get(action, 0) + 1
                if hand_name:
                    hand_dist[hand_name] = hand_dist.get(hand_name, 0) + 1

                if conf:
                    bucket = min(9, conf // 10)
                    bucket_key = f"{bucket*10}-{bucket*10+9}"
                    confidence_buckets[bucket_key] = confidence_buckets.get(bucket_key, 0) + 1

                    tier = "high" if conf >= 70 else "low"
                    win_when_confident[tier]["total"] += 1
                    if pnl and pnl > 0:
                        win_when_confident[tier]["wins"] += 1

            # Win rate by confidence
            for tier in win_when_confident:
                t = win_when_confident[tier]
                t["win_rate"] = round(t["wins"] / t["total"] * 100, 1) if t["total"] > 0 else 0

            return {
                "pnl_series": pnl_series,
                "action_distribution": action_dist,
                "hand_distribution": hand_dist,
                "confidence_buckets": confidence_buckets,
                "win_by_confidence": win_when_confident,
                "total_hands": len(rows),
            }

    def _format_hand(self, hand: dict) -> dict:
        """Format a hand record for display."""
        for field in ("hole_cards", "community_cards", "dealer_cards", "gto_recommendation"):
            if field in hand and isinstance(hand[field], str):
                try:
                    hand[field] = json.loads(hand[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return hand
