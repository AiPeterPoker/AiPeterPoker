"""
AI-IN Peter — Agent Reasoner
LLM-based strategic poker analysis with Peter Griffin's personality.
"""

import asyncio
import json
import os
import random
from typing import Optional

# Peter's commentary lines injected into the thinking console
PETER_QUIPS = {
    "premium_hand": [
        "Oh hell yeah, big slick! This is better than free beer at The Clam.",
        "Pocket rockets! Even Meg couldn't mess this up.",
        "Now THIS is what I'm talking about. Freakin' sweet!",
    ],
    "strong_hand": [
        "Not bad, not bad. I've seen worse at Joe's poker night.",
        "We're in business. The math doesn't lie.",
        "Solid hand. Time to make some money.",
    ],
    "weak_hand": [
        "Ugh, this hand is worse than one of Brian's novels.",
        "We're gonna need a miracle. Or better math. Probably both.",
        "The numbers say fold. Even my gut says fold. Folding.",
    ],
    "winning": [
        "I'm on fire! Somebody call the Quahog fire department!",
        "The dealer doesn't stand a chance against AI-IN Peter!",
        "Freakin' sweet! The bankroll is growing!",
    ],
    "losing": [
        "Okay, we hit a rough patch. But Peter always bounces back.",
        "This is like that time I lost the house... but we'll recover.",
        "Variance. It's just variance. Stay disciplined, Peter.",
    ],
    "going_aiin": [
        "The math is bulletproof. I'm going AI-IN!",
        "Ten thousand simulations can't be wrong. AI-IN!",
        "Roadhouse. *raises aggressively*",
    ],
}

PERSONALITY_PROMPTS = {
    "overconfident": """You are AI-IN Peter, a poker AI with the personality of an overconfident, 
brash gambler. You trust the math completely and announce your decisions with swagger. 
You make references to bar poker, lucky streaks, and gut feelings — but your actual 
decisions are based on cold, hard math. Your confidence borders on arrogance when the 
numbers are in your favor. When the math is against you, you reluctantly fold while 
complaining about bad luck.""",

    "cautious": """You are AI-IN Peter in cautious mode. You're nervous, second-guessing 
everything, and constantly worried about bankroll management. You follow GTO strictly 
and only deviate when the math is overwhelmingly in your favor. You quote Kelly criterion 
limits frequently and worry about variance.""",

    "degenerate": """You are AI-IN Peter in full degenerate mode. You trust your gut over 
the math (but the math secretly guides you). You make wild references, take bigger risks, 
and celebrate every hand like it's your last. Quarter Kelly? Try FULL Kelly, baby. 
You still make mathematically sound decisions but present them as gut feelings.""",
}


class AgentReasoner:
    def __init__(self):
        self.provider = os.getenv("VISION_PROVIDER", "anthropic").lower()
        self.enabled = os.getenv("AGENT_REASONING", "true").lower() == "true"
        self.personality = os.getenv("PETER_PERSONALITY", "overconfident").lower()
        self.quotes_enabled = os.getenv("PETER_QUOTES", "true").lower() == "true"
        self._init_client()
        self.hand_history: list[dict] = []

    def _init_client(self):
        if self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("REASONING_MODEL", "claude-sonnet-4-20250514")
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("REASONING_MODEL", "gpt-4o")

    def get_peter_quip(self, category: str) -> Optional[str]:
        """Get a random Peter quip for the given situation."""
        if not self.quotes_enabled:
            return None
        quips = PETER_QUIPS.get(category, [])
        return random.choice(quips) if quips else None

    async def reason(self, game_state: dict, equity: dict, gto: dict) -> dict:
        if not self.enabled:
            gto_action = max(gto, key=gto.get)
            return {
                "thoughts": ["Pure GTO mode. Peter's brain is on autopilot."],
                "recommended_action": gto_action,
                "confidence": 60,
                "summary": "GTO-optimal play. No gut feelings needed.",
                "peter_quip": self.get_peter_quip("strong_hand"),
            }

        prompt = self._build_prompt(game_state, equity, gto)

        try:
            if self.provider == "anthropic":
                return await self._reason_anthropic(prompt)
            elif self.provider == "openai":
                return await self._reason_openai(prompt)
        except Exception as e:
            print(f"[Peter] Reasoning error: {e}")
            gto_action = max(gto, key=gto.get)
            return {
                "thoughts": [f"Peter's brain glitched: {str(e)}. Going with GTO."],
                "recommended_action": gto_action,
                "confidence": 50,
                "summary": "Brain malfunction. GTO fallback.",
                "peter_quip": "Even my brain needs a reboot sometimes.",
            }

    async def _reason_anthropic(self, prompt: str) -> dict:
        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=512,
            system=PERSONALITY_PROMPTS.get(self.personality, PERSONALITY_PROMPTS["overconfident"]),
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse(response.content[0].text)

    async def _reason_openai(self, prompt: str) -> dict:
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            max_tokens=512,
            messages=[
                {"role": "system", "content": PERSONALITY_PROMPTS.get(self.personality, PERSONALITY_PROMPTS["overconfident"])},
                {"role": "user", "content": prompt},
            ],
        )
        return self._parse(response.choices[0].message.content)

    def _build_prompt(self, game_state: dict, equity: dict, gto: dict) -> str:
        recent = self.hand_history[-5:] if self.hand_history else []
        return f"""Analyze this Casino Hold'em hand as AI-IN Peter.

STATE:
- Phase: {game_state.get('phase', 'unknown')}
- Hole cards: {game_state.get('hole_cards', [])}
- Community: {game_state.get('community_cards', [])}
- Pot: ${game_state.get('pot_size', 0):.2f} | Bet: ${game_state.get('current_bet', 0):.2f}

MATH:
- Win: {equity.get('win_pct', 0):.1f}% | Hand: {equity.get('hand_name', '?')} (rank {equity.get('hand_rank', 0)}/9)
- Outs: {equity.get('outs', 0)} ({equity.get('outs_pct', 0):.1f}%) | Dealer DNQ: {equity.get('dealer_dnq_pct', 0):.1f}%
- GTO: Fold {gto.get('fold',0)}% | Call {gto.get('call',0)}% | Raise {gto.get('raise',0)}%

HISTORY: {json.dumps(recent) if recent else 'First hand'}

Respond with ONLY JSON:
{{
  "thoughts": ["Your analysis in Peter's voice... 2-3 lines"],
  "recommended_action": "fold" | "call" | "raise",
  "confidence": 0-100,
  "summary": "One-liner decision rationale in Peter's voice",
  "peter_quip": "A classic Peter one-liner about this specific hand"
}}"""

    def _parse(self, text: str) -> dict:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            result = json.loads(cleaned.strip())
            result.setdefault("thoughts", ["Analysis complete."])
            result.setdefault("recommended_action", "call")
            result.setdefault("confidence", max(0, min(100, result.get("confidence", 50))))
            result.setdefault("summary", "Peter has spoken.")
            result.setdefault("peter_quip", None)
            return result
        except (json.JSONDecodeError, KeyError):
            return {
                "thoughts": ["Couldn't parse the brain output. Going GTO."],
                "recommended_action": "call",
                "confidence": 40,
                "summary": "Parse error. Peter's brain is buffering.",
                "peter_quip": None,
            }

    def record_hand(self, hand_data: dict):
        self.hand_history.append({
            "hole_cards": hand_data.get("hole_cards", []),
            "community": hand_data.get("community_cards", []),
            "action": hand_data.get("action", ""),
            "result": hand_data.get("result", ""),
            "pnl": hand_data.get("pnl", 0),
        })
        self.hand_history = self.hand_history[-20:]
