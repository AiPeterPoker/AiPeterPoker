"""
AI-IN Peter — Voice Synthesis (ElevenLabs)
Peter narrates his decisions out loud for streaming.
"""

import asyncio
import base64
import io
import os
from typing import Optional


class PeterVoice:
    def __init__(self):
        self.enabled = os.getenv("ELEVENLABS_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Default: Adam
        self.model = os.getenv("ELEVENLABS_MODEL", "eleven_monolingual_v1")
        self.stability = float(os.getenv("ELEVENLABS_STABILITY", "0.35"))
        self.similarity = float(os.getenv("ELEVENLABS_SIMILARITY", "0.75"))
        self.style = float(os.getenv("ELEVENLABS_STYLE", "0.4"))

        if self.enabled and not self.api_key:
            print("[Voice] ElevenLabs enabled but no API key set. Disabling.")
            self.enabled = False

    async def speak(self, text: str) -> Optional[str]:
        """
        Generate speech from text using ElevenLabs API.
        Returns base64-encoded MP3 audio string, or None on failure.
        """
        if not self.enabled:
            return None

        try:
            import httpx

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

            payload = {
                "text": text,
                "model_id": self.model,
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity,
                    "style": self.style,
                    "use_speaker_boost": True,
                },
            }

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=15)

                if response.status_code == 200:
                    audio_b64 = base64.b64encode(response.content).decode("utf-8")
                    return audio_b64
                else:
                    print(f"[Voice] ElevenLabs error: {response.status_code} {response.text[:200]}")
                    return None

        except ImportError:
            print("[Voice] httpx not installed. Run: pip install httpx")
            return None
        except Exception as e:
            print(f"[Voice] TTS error: {e}")
            return None

    async def narrate_decision(self, decision: dict, hand_name: str = "") -> Optional[str]:
        """
        Generate a Peter-style narration for a decision.
        Returns base64 audio or None.
        """
        action = decision.get("action", "call").upper()
        amount = decision.get("amount", 0)
        confidence = decision.get("confidence", 0)
        reasoning = decision.get("reasoning", "")

        # Build narration text
        if action == "RAISE":
            lines = [
                f"I'm going AI-IN! Raise to {amount:.0f} dollars.",
                f"Confidence: {confidence} percent. {reasoning}" if reasoning else "",
                "The math doesn't lie, baby!",
            ]
        elif action == "FOLD":
            lines = [
                "Folding this one.",
                f"Only {confidence} percent confidence. Not worth the risk.",
                "Even Peter knows when to walk away. Temporarily.",
            ]
        else:
            lines = [
                f"Calling. {amount:.0f} dollars.",
                f"{hand_name}. " if hand_name else "",
                f"Confidence at {confidence} percent.",
            ]

        text = " ".join(l for l in lines if l)
        return await self.speak(text)

    async def narrate_quip(self, quip: str) -> Optional[str]:
        """Speak a Peter quip."""
        return await self.speak(quip)

    def set_voice(self, voice_id: str):
        """Change the ElevenLabs voice."""
        self.voice_id = voice_id

    def set_settings(self, stability: float = None, similarity: float = None, style: float = None):
        """Adjust voice settings."""
        if stability is not None:
            self.stability = max(0, min(1, stability))
        if similarity is not None:
            self.similarity = max(0, min(1, similarity))
        if style is not None:
            self.style = max(0, min(1, style))
