"""
AI-IN Peter — Twitch Chat Integration
Connects to Twitch IRC and lets viewers vote on Peter's decisions.
Democracy mode: viewers type !fold, !call, or !raise to vote.
"""

import asyncio
import os
import re
import time
from collections import Counter
from typing import Optional, Callable

TWITCH_IRC_HOST = "irc.chat.twitch.tv"
TWITCH_IRC_PORT = 6667


class TwitchIntegration:
    def __init__(self):
        self.channel = os.getenv("TWITCH_CHANNEL", "")
        self.bot_name = os.getenv("TWITCH_BOT_NAME", "AIINPeterBot")
        self.oauth_token = os.getenv("TWITCH_OAUTH_TOKEN", "")
        self.enabled = bool(self.channel and self.oauth_token)
        self.connected = False
        self.reader = None
        self.writer = None

        # Voting state
        self.voting_open = False
        self.votes: Counter = Counter()
        self.voters: set = set()
        self.vote_deadline = 0
        self.vote_duration = int(os.getenv("TWITCH_VOTE_DURATION", "15"))

        # Chat log for overlay display
        self.chat_log: list[dict] = []
        self.max_chat_log = 50

        # Callbacks
        self.on_vote_update: Optional[Callable] = None
        self.on_chat_message: Optional[Callable] = None

    async def connect(self):
        """Connect to Twitch IRC."""
        if not self.enabled:
            print("[Twitch] Not configured. Set TWITCH_CHANNEL and TWITCH_OAUTH_TOKEN in .env")
            return False

        try:
            self.reader, self.writer = await asyncio.open_connection(
                TWITCH_IRC_HOST, TWITCH_IRC_PORT
            )

            # Authenticate
            self.writer.write(f"PASS {self.oauth_token}\r\n".encode())
            self.writer.write(f"NICK {self.bot_name}\r\n".encode())
            self.writer.write(f"JOIN #{self.channel}\r\n".encode())
            await self.writer.drain()

            # Request tags for user info
            self.writer.write(b"CAP REQ :twitch.tv/tags\r\n")
            await self.writer.drain()

            self.connected = True
            print(f"[Twitch] Connected to #{self.channel}")

            # Send greeting
            await self.send_message(
                "AI-IN Peter is in the house! Type !fold !call or !raise to vote when voting is open. "
                "Peter might listen... or he might just do what the math says. 🃏"
            )

            return True
        except Exception as e:
            print(f"[Twitch] Connection failed: {e}")
            return False

    async def listen(self):
        """Main loop: read and process IRC messages."""
        if not self.connected:
            return

        while self.connected:
            try:
                line = await self.reader.readline()
                if not line:
                    break

                message = line.decode("utf-8", errors="ignore").strip()

                # Respond to PING to stay connected
                if message.startswith("PING"):
                    self.writer.write(b"PONG :tmi.twitch.tv\r\n")
                    await self.writer.drain()
                    continue

                # Parse PRIVMSG
                parsed = self._parse_message(message)
                if parsed:
                    await self._handle_message(parsed)

            except Exception as e:
                print(f"[Twitch] Listen error: {e}")
                await asyncio.sleep(1)

    async def send_message(self, text: str):
        """Send a message to the Twitch chat."""
        if not self.connected:
            return
        try:
            self.writer.write(f"PRIVMSG #{self.channel} :{text}\r\n".encode())
            await self.writer.drain()
        except Exception as e:
            print(f"[Twitch] Send error: {e}")

    def _parse_message(self, raw: str) -> Optional[dict]:
        """Parse a Twitch IRC PRIVMSG into structured data."""
        match = re.search(
            r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)",
            raw,
        )
        if not match:
            return None

        username = match.group(1)
        text = match.group(2).strip()

        return {"username": username, "text": text, "timestamp": time.time()}

    async def _handle_message(self, msg: dict):
        """Process a chat message — check for votes and commands."""
        username = msg["username"]
        text = msg["text"].lower().strip()

        # Add to chat log
        self.chat_log.append(msg)
        if len(self.chat_log) > self.max_chat_log:
            self.chat_log = self.chat_log[-self.max_chat_log:]

        if self.on_chat_message:
            await self.on_chat_message(msg)

        # Handle commands
        if text.startswith("!"):
            cmd = text.split()[0]

            if cmd in ("!fold", "!call", "!raise") and self.voting_open:
                await self._register_vote(username, cmd[1:])

            elif cmd == "!stats":
                await self.send_message(
                    f"Peter's session: Hands played, win rate, and bankroll are shown on the overlay!"
                )

            elif cmd == "!peter":
                await self.send_message(
                    "AI-IN Peter is an AI poker agent that uses Monte Carlo simulation + GTO strategy. "
                    "The AI does the math, Peter does the trash talk. github.com/ai-in-peter"
                )

            elif cmd == "!help":
                await self.send_message(
                    "Commands: !fold !call !raise (vote during voting) | !stats | !peter | !help"
                )

    async def _register_vote(self, username: str, action: str):
        """Register a viewer's vote."""
        if username in self.voters:
            return  # One vote per person per hand

        self.voters.add(username)
        self.votes[action] += 1

        if self.on_vote_update:
            await self.on_vote_update(self.get_vote_results())

    # ── Voting lifecycle ──────────────────────────────────────────────────

    async def open_voting(self, hand_info: str = ""):
        """Open voting for viewers."""
        self.voting_open = True
        self.votes = Counter()
        self.voters = set()
        self.vote_deadline = time.time() + self.vote_duration

        await self.send_message(
            f"🗳️ VOTE NOW! Peter wants your input. "
            f"Type !fold !call or !raise — you have {self.vote_duration}s! "
            f"{hand_info}"
        )

        # Auto-close after duration
        asyncio.create_task(self._auto_close_voting())

    async def _auto_close_voting(self):
        """Auto-close voting after the deadline."""
        await asyncio.sleep(self.vote_duration)
        if self.voting_open:
            await self.close_voting()

    async def close_voting(self) -> dict:
        """Close voting and announce results."""
        self.voting_open = False
        results = self.get_vote_results()
        total = results["total"]

        if total == 0:
            await self.send_message(
                "Nobody voted? Fine, Peter's going with the math. As usual."
            )
        else:
            winner = results["winner"]
            pct = results["percentages"].get(winner, 0)
            await self.send_message(
                f"🗳️ Results: FOLD {results['percentages'].get('fold',0)}% | "
                f"CALL {results['percentages'].get('call',0)}% | "
                f"RAISE {results['percentages'].get('raise',0)}% — "
                f"Chat says {winner.upper()}! ({total} votes) "
                f"{'Peter agrees!' if pct > 50 else 'Peter might disagree...'}"
            )

        return results

    def get_vote_results(self) -> dict:
        """Get current voting results."""
        total = sum(self.votes.values())
        if total == 0:
            return {
                "total": 0,
                "votes": dict(self.votes),
                "percentages": {"fold": 0, "call": 0, "raise": 0},
                "winner": "call",
                "time_remaining": max(0, int(self.vote_deadline - time.time())),
            }

        percentages = {
            action: round(count / total * 100)
            for action, count in self.votes.items()
        }
        # Fill missing
        for a in ("fold", "call", "raise"):
            percentages.setdefault(a, 0)

        winner = self.votes.most_common(1)[0][0] if self.votes else "call"

        return {
            "total": total,
            "votes": dict(self.votes),
            "percentages": percentages,
            "winner": winner,
            "time_remaining": max(0, int(self.vote_deadline - time.time())),
        }

    async def disconnect(self):
        """Disconnect from Twitch."""
        if self.connected:
            await self.send_message("AI-IN Peter is leaving the table. GG everyone! 🃏")
            self.connected = False
            if self.writer:
                self.writer.close()
