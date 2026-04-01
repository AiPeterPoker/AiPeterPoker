"""
Session Database — SQLite-backed hand history and session tracking.
Records every hand with full agent reasoning for post-session review.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

DB_PATH = Path(__file__).parent.parent / "data" / "ai-in-peter.db"


class SessionDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialized = False

    async def _ensure_init(self):
        """Lazy init — create tables on first use."""
        if self._initialized:
            return
        await self._init_db()
        self._initialized = True

    async def _init_db(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    total_hands INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    win_rate REAL DEFAULT 0.0,
                    starting_bankroll REAL DEFAULT 0.0,
                    ending_bankroll REAL DEFAULT 0.0,
                    config TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS hands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    hand_number INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    phase TEXT,
                    hole_cards TEXT,
                    community_cards TEXT,
                    dealer_cards TEXT,
                    pot_size REAL,
                    win_probability REAL,
                    hand_name TEXT,
                    hand_strength REAL,
                    gto_recommendation TEXT,
                    agent_reasoning TEXT,
                    decision_action TEXT,
                    decision_amount REAL,
                    decision_confidence INTEGER,
                    expected_value REAL,
                    result TEXT,
                    pnl REAL DEFAULT 0.0,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_hands_session
                ON hands(session_id)
            """)
            await db.commit()

    async def create_session(self, starting_bankroll: float = 1500.0, config: dict = None) -> int:
        """Start a new session. Returns session ID."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO sessions (started_at, starting_bankroll, config)
                   VALUES (?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    starting_bankroll,
                    json.dumps(config or {}),
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def end_session(self, session_id: int, stats: dict):
        """End a session with final stats."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE sessions
                   SET ended_at = ?, total_hands = ?, total_pnl = ?,
                       win_rate = ?, ending_bankroll = ?
                   WHERE id = ?""",
                (
                    datetime.now().isoformat(),
                    stats.get("total_hands", 0),
                    stats.get("total_pnl", 0),
                    stats.get("win_rate", 0),
                    stats.get("ending_bankroll", 0),
                    session_id,
                ),
            )
            await db.commit()

    async def save_hand(self, session_id: int, game_state: dict, decision: dict):
        """Save a hand record."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            # Get hand number
            cursor = await db.execute(
                "SELECT COUNT(*) FROM hands WHERE session_id = ?",
                (session_id,),
            )
            row = await cursor.fetchone()
            hand_number = (row[0] if row else 0) + 1

            await db.execute(
                """INSERT INTO hands
                   (session_id, hand_number, timestamp, phase,
                    hole_cards, community_cards, dealer_cards,
                    pot_size, win_probability, hand_name, hand_strength,
                    gto_recommendation, agent_reasoning,
                    decision_action, decision_amount, decision_confidence,
                    expected_value)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    hand_number,
                    datetime.now().isoformat(),
                    game_state.get("phase"),
                    json.dumps(game_state.get("hole_cards", [])),
                    json.dumps(game_state.get("community_cards", [])),
                    json.dumps(game_state.get("dealer_cards", [])),
                    game_state.get("pot_size", 0),
                    game_state.get("win_probability", 0),
                    game_state.get("hand_name", ""),
                    game_state.get("hand_strength", 0),
                    json.dumps(game_state.get("gto_recommendation", {})),
                    json.dumps(decision.get("reasoning", "")),
                    decision.get("action"),
                    decision.get("amount", 0),
                    decision.get("confidence", 0),
                    decision.get("expected_value", 0),
                ),
            )
            await db.commit()

    async def get_session_hands(self, session_id: int) -> list[dict]:
        """Get all hands for a session."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM hands WHERE session_id = ? ORDER BY hand_number",
                (session_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_sessions(self) -> list[dict]:
        """Get all sessions summary."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_lifetime_stats(self) -> dict:
        """Get aggregate lifetime statistics."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(*) as total_hands,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl_per_hand,
                    MAX(pnl) as best_hand,
                    MIN(pnl) as worst_hand,
                    AVG(win_probability) as avg_win_prob,
                    AVG(decision_confidence) as avg_confidence
                FROM hands
            """)
            row = await cursor.fetchone()
            if row:
                return {
                    "total_sessions": row[0] or 0,
                    "total_hands": row[1] or 0,
                    "total_pnl": round(row[2] or 0, 2),
                    "avg_pnl_per_hand": round(row[3] or 0, 4),
                    "best_hand": round(row[4] or 0, 2),
                    "worst_hand": round(row[5] or 0, 2),
                    "avg_win_probability": round(row[6] or 0, 1),
                    "avg_confidence": round(row[7] or 0, 1),
                }
            return {}
