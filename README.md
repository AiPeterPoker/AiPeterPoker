# 🃏 AI-IN Peter

**"Holy crap, Lois! The math says we're golden. I'm goin' AI-IN."**

Open-source AI poker agent for Casino Hold'em with transparent overlay, ESP card tracking, GTO engine, and the overconfident personality of a certain Quahog resident.

Inspired by *Family Guy* — *High Stakes Griffin* and Peter's gambling persona.

![License](https://img.shields.io/badge/license-MIT-green)
![Node](https://img.shields.io/badge/node-%3E%3D18-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)

---

## What Is AI-IN Peter?

**AI-IN Peter** is a wordplay between "All-In" and "AI-In" — an AI agent that commits fully when the math supports it. Built for streaming on Twitch/YouTube via OBS, Peter reads the table through computer vision, calculates equity through Monte Carlo simulation, follows GTO-optimal strategy, and announces every decision with the swagger of a man who once fought a giant chicken over a coupon.

The overlay runs on your PC as a transparent Electron window. The backend runs locally in Python. Your API keys stay on your machine. Anyone can fork the repo and deploy their own Peter.

---

## Features

- **AI Vision** — Screenshots the browser, uses Claude/GPT-4o to read cards, buttons, and game state
- **Monte Carlo Engine** — 10,000+ simulated runouts to calculate hand equity
- **GTO Strategy** — Pre-computed Game Theory Optimal tables for Casino Hold'em
- **ESP Card Tracker** — Visual grid showing every dealt/remaining card in the deck
- **Peter's Brain Console** — Real-time log of every thought, calculation, and Peter-ism
- **Kelly Criterion Sizing** — Automatic bet sizing based on edge and bankroll
- **Peter's Personality** — Overconfident quips, gut feelings, and commentary in the console
- **Transparent Overlay** — Frameless Electron window, perfect for OBS window capture
- **Hand History** — SQLite database records every hand with full agent reasoning
- **100% Open Source** — Fork it, customize it, make your own AI poker persona

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              AI-IN Peter (Electron)              │
│  ┌──────────────┐  ┌─────────────────────────┐  │
│  │  Transparent  │  │    React Components      │  │
│  │   Overlay     │  │  - Peter's Hand          │  │
│  │   Window      │  │  - Odds Engine           │  │
│  │              │  │  - ESP Tracker            │  │
│  │              │  │  - Peter's Brain Console  │  │
│  │              │  │  - Decision Box           │  │
│  └──────┬───────┘  └──────────┬──────────────┘  │
│         └──────────┬───────────┘                  │
└────────────────────┼─────────────────────────────┘
                     │ WebSocket
        ┌────────────▼────────────────┐
        │    Python Backend            │
        │  ┌─────────┐ ┌───────────┐  │
        │  │ Vision   │ │ Decision  │  │
        │  │ (Claude/ │ │ Engine    │  │
        │  │  GPT-4o) │ │ (GTO+MC) │  │
        │  └─────────┘ └───────────┘  │
        │  ┌─────────┐ ┌───────────┐  │
        │  │ Screen   │ │ Peter's   │  │
        │  │ Capture  │ │ Reasoner  │  │
        │  └─────────┘ └───────────┘  │
        └─────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js >= 18
- Python >= 3.10
- An API key for Claude or OpenAI (for vision)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/ai-in-peter.git
cd ai-in-peter
bash scripts/setup.sh
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys — Peter needs eyes to see the cards
```

### 3. Run

```bash
npm start
```

### 4. Stream with OBS

1. Open OBS
2. Add a **Window Capture** source → select "AI-IN Peter"
3. The overlay is transparent — composites over your game
4. Peter's brain is now visible to your viewers

---

## Peter's Personality Modes

| Mode | GTO | Risk | Console Style |
|------|-----|------|---------------|
| **Overconfident** (default) | 0.8 | Medium | Trash talk + math |
| **Cautious** | 0.95 | Low | Nervous + GTO-focused |
| **Degenerate** | 0.4 | High | Full Peter, gut-driven |

---

## The Agent Loop

```
Screenshot → AI Vision → Parse State → Monte Carlo → GTO Lookup
     ↑                                                    │
     │            Peter's Brain (LLM reasoning)  ◄────────┤
     │            Kelly Criterion Sizing  ◄───────────────┤
     └──── wait for next phase ◄──── Display Decision ◄──┘
```

---

## Disclaimer

This project is for **educational and entertainment purposes only**. It is a parody/fan project. *Family Guy* and Peter Griffin are trademarks of 20th Television. Not affiliated with or endorsed by Fox, Disney, or Seth MacFarlane.

Online gambling may be illegal in your jurisdiction. Always gamble responsibly — even if Peter wouldn't.

## License

MIT — see [LICENSE](LICENSE)
