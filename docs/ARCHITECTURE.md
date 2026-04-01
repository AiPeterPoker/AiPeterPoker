# Architecture — AI-IN Peter

## System Overview

AI-IN Peter is a three-tier AI poker agent: an **Electron overlay** (React frontend), a **Python backend** (vision + decision engine + Peter's brain), and **SQLite** for hand history.

## The AI-IN Loop

```
Screenshot → AI Vision → Parse Cards → Monte Carlo (10k sims) → GTO Lookup
     ↑                                                              │
     │              Peter's Brain (LLM + personality)  ◄────────────┤
     │              Kelly Criterion Sizing  ◄───────────────────────┤
     │                                                              │
     └──── wait ◄──── Display Decision + Peter Quip  ◄─────────────┘
```

## Peter's Personality System

The agent has three personality modes configured via `PETER_PERSONALITY`:

**Overconfident** (default, GTO=0.8): Peter trusts the math and announces decisions with swagger. Console output mixes cold analysis with trash talk. This is the streaming-friendly mode.

**Cautious** (GTO=0.95): Nervous Peter. Strict GTO adherence, constant bankroll worrying, Kelly criterion quotes. For conservative play.

**Degenerate** (GTO=0.4): Full Peter. Gut-driven commentary with mathematically sound decisions presented as feelings. Bigger Kelly fractions, more risk tolerance. Maximum entertainment value.

All three modes make *mathematically identical* core decisions — the personality only affects presentation, confidence thresholds, and Kelly fraction. The math is always right; Peter's delivery varies.

## Module Architecture

### Vision (`backend/vision/detector.py`)
- Screen capture via `mss` library (cross-platform)
- Image sent to Claude/GPT-4o vision API
- Structured JSON extraction: cards, phase, pot, buttons
- Card validation and normalization (`card_recognition.py`)

### Monte Carlo (`backend/engine/monte_carlo.py`)
- Full hand evaluator (royal flush → high card)
- Itertools-based best-5-of-7 evaluation
- Casino Hold'em specific: dealer qualification check (pair of 4s+)
- Outs counting with improvement tracking

### Decision Engine (`backend/engine/decision.py`)
- Pre-flop hand categorization (premium → trash)
- Post-flop strength classification (monster → nothing)
- GTO action distribution lookup tables
- Kelly criterion bet sizing with fractional safety
- Expected value and pot odds calculation

### Peter's Brain (`backend/models/agent.py`)
- LLM-based situational reasoning with personality prompts
- Context-aware quip generation based on hand strength
- Hand history tracking for pattern recognition
- Three personality modes with distinct system prompts

### Session DB (`backend/db/session.py`)
- SQLite with sessions and hands tables
- Full hand recording: cards, equity, reasoning, decision
- Lifetime statistics aggregation

## WebSocket Protocol

Messages: `{type, payload, timestamp}`

Backend → Frontend: `game_state`, `decision`, `thinking`, `session_update`, `error`
Frontend → Backend: `start_capture`, `stop_session`, `pause_agent`, `resume_agent`, `update_settings`

## OBS Integration

Electron window uses `transparent: true` + `frame: false`. OBS Window Capture sees only the overlay UI. The scanline gradient and dark HUD aesthetic are designed for stream visibility against casino game backgrounds.
