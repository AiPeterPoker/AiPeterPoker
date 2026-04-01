<p align="center">
  <img src="https://img.shields.io/badge/STATUS-ALL--IN-brightgreen?style=for-the-badge&labelColor=1a472a" />
  <img src="https://img.shields.io/badge/GAMES-Casino%20Hold'em%20%7C%20Blackjack-FFD740?style=for-the-badge&labelColor=1a1a2e" />
  <img src="https://img.shields.io/badge/LICENSE-MIT-blue?style=for-the-badge" />
</p>

<h1 align="center">
  AI-IN Peter
</h1>

<h3 align="center">
  <em>"The math doesn't lie and neither does Peter Griffin."</em>
</h3>

<p align="center">
  Open-source AI agent that plays <strong>Casino Hold'em</strong> and <strong>Blackjack</strong> on Solcasino.io using computer vision, Monte Carlo simulation, and GTO-optimal strategy — all wrapped in a transparent OBS overlay with Peter Griffin's personality.
</p>

<p align="center">
  <strong>AI-IN</strong> = <em>All-In</em> meets <em>AI-In</em>. The name says it all.
</p>

---

## How It Works

```
Screenshot (mss) --> GPT-4o Vision --> Card Detection --> Monte Carlo Equity --> GTO Strategy --> Decision --> OBS Overlay
     ~80ms              ~2s              instant           2K iterations         instant         instant       real-time
```

Peter watches your screen, reads the cards with AI vision, crunches 2,000+ Monte Carlo simulations, applies mathematically optimal strategy, and tells you exactly what to do — in under 3 seconds.

---

## Supported Games

### Casino Hold'em (Pragmatic Play)
- **Optimal strategy engine** based on Wizard of Odds mathematics (~2.16% house edge with perfect play)
- Binary decision: **2x PLAY** or **FOLD** — no raise, no bluffing, pure math
- Dealer qualification tracking (pair of 4s or better)
- Ante bonus paytable awareness (Royal Flush 100:1 down to Flush 2:1)
- ~82% play rate / ~18% fold rate matching published optimal play

### Blackjack (Multi-deck)
- **Complete basic strategy** tables (hard, soft, pair splits)
- **Hi-Lo card counting** with true count calculation
- **Illustrious 18** deviations based on true count
- Insurance decision support
- 6-8 deck shoe tracking with cards remaining

---

## Features

### Vision & Detection
- **GPT-4o / Claude vision** for card recognition from screenshots
- **ESP overlay** — real-time bounding boxes around detected cards (~12 FPS)
- **Auto-calibration** — detects the green felt table region automatically
- **Balance reader** — pixel-based OCR reads your casino balance in ~2ms (no external OCR)
- **Face detection** — locates dealer position using Haar cascades
- **Card identity cache** — avoids re-reading cards that haven't changed

### Decision Engine
- **Monte Carlo equity calculator** — simulates thousands of hands for win/loss/tie probability
- **GTO-optimal strategy** — mathematically computed, within 0.003% of perfect play
- **Expected Value (EV)** calculator with dealer non-qualification factored in
- **Kelly Criterion** bet sizing with fractional Kelly support
- **Draw detection** — flush draws, open-ended straight draws, gutshots, backdoor draws
- **Outs counter** — calculates exact improvement cards remaining in the deck

### Overlay (Electron + React)
- **Transparent HUD** — sits on top of your game, perfect for OBS streaming
- **Hand display** with card graphics
- **Odds panel** — live win%, EV, outs, dealer qualification probability
- **Decision box** — PLAY/FOLD recommendation with confidence level
- **Session stats** — hands played, win rate, P&L, streak tracking
- **Card tracker** — visual remaining deck composition
- **Analytics dashboard** with charts (Recharts)
- **Hand replay viewer** — browse and analyze past hands
- **Settings panel** — configure everything from the overlay
- **Achievement toasts** — unlock milestones with Peter's quips

### Integrations
- **Twitch chat voting** — viewers type `!fold` or `!call` to vote on decisions (democracy mode)
- **ElevenLabs voice** — Peter narrates his decisions out loud for streams
- **Auto-player** — calibrate button positions once, Peter clicks for you (optional)
- **Hand history DB** — every hand logged to SQLite for post-session analysis

### Achievements System
Unlock badges as you play:

| Badge | Name | Condition |
|-------|------|-----------|
| 1 | First Blood | Win your first hand |
| 10 | Hot Streak | Win 10 hands |
| 50 | The Grinder | Play 50 hands |
| 100 | Century Club | Play 100 hands |
| 500 | Iron Butt | Play 500 hands in one session |
| $ | Big Winner | Win $100+ in a session |
| W | The Whale | Win $500+ in a session |

---

## Tech Stack

| Layer | Tech |
|-------|------|
| **Frontend** | Electron + React + Vite + Tailwind CSS |
| **Backend** | Python FastAPI + WebSocket (port 8765) |
| **Vision** | GPT-4o via OpenAI API (or Claude via Anthropic API) |
| **Engine** | Monte Carlo simulation + GTO lookup tables |
| **Blackjack** | Basic strategy + Hi-Lo card counting + Illustrious 18 |
| **Database** | SQLite (hand history, sessions, analytics) |
| **Voice** | ElevenLabs text-to-speech |
| **Streaming** | Twitch IRC integration + transparent OBS overlay |
| **Auto-play** | PyAutoGUI + pynput for button calibration |
| **Charts** | Recharts for analytics dashboard |

---

## Project Structure

```
aiinpeter/
├── backend/
│   ├── server.py                 # FastAPI + WebSocket server
│   ├── vision/
│   │   ├── detector.py           # GPT-4o/Claude card detection
│   │   ├── card_recognition.py   # Card parsing & normalization
│   │   ├── card_reader.py        # Card reading pipeline
│   │   ├── balance_reader.py     # Pixel-based balance OCR (~2ms)
│   │   ├── auto_calibrate.py     # Auto-detect game region
│   │   └── blackjack_zones.py    # Blackjack table zones
│   ├── engine/
│   │   ├── decision.py           # GTO optimal strategy engine
│   │   ├── monte_carlo.py        # Monte Carlo equity calculator
│   │   ├── game_state_machine.py # Poker game state tracking
│   │   ├── achievements.py       # Achievement/badge system
│   │   └── blackjack/
│   │       ├── hand.py           # Blackjack hand evaluation
│   │       ├── basic_strategy.py # Complete basic strategy tables
│   │       ├── card_counter.py   # Hi-Lo card counting
│   │       └── game_state_machine.py
│   ├── models/
│   │   └── agent.py              # LLM agent reasoner
│   ├── integrations/
│   │   ├── twitch.py             # Twitch chat voting
│   │   ├── voice.py              # ElevenLabs TTS
│   │   └── autoplayer.py         # Auto-click with calibration
│   ├── replay/
│   │   └── hand_replay.py        # Hand history browser
│   └── db/
│       └── session.py            # SQLite session management
├── src/
│   ├── App.jsx                   # Main React app
│   └── components/
│       ├── Overlay.jsx           # Main HUD layout
│       ├── HandDisplay.jsx       # Card visualization
│       ├── OddsPanel.jsx         # Win%, EV, outs display
│       ├── DecisionBox.jsx       # PLAY/FOLD recommendation
│       ├── CardTracker.jsx       # Remaining deck tracker
│       ├── SessionStats.jsx      # Session P&L and stats
│       ├── ConsoleLog.jsx        # Live agent log
│       ├── EspOverlay.jsx        # Card detection bounding boxes
│       ├── AnalyticsDashboard.jsx# Charts and analytics
│       ├── HandReplayViewer.jsx  # Past hand browser
│       ├── SettingsPanel.jsx     # Configuration UI
│       ├── AchievementToast.jsx  # Badge notifications
│       ├── TwitchVote.jsx        # Twitch voting display
│       └── blackjack/
│           ├── BlackjackHandDisplay.jsx
│           ├── BlackjackDecisionBox.jsx
│           └── CountPanel.jsx    # Hi-Lo count display
├── electron/
│   ├── main.js                   # Electron main process
│   └── preload.js                # Preload script
├── tests/
│   ├── test_engine.py            # Engine test suite (36+ tests)
│   └── test_blackjack.py         # Blackjack strategy tests
└── package.json
```

---

## Quick Start

### Prerequisites
- **Node.js** >= 18
- **Python** >= 3.10
- **OpenAI API key** (for GPT-4o vision)

### Install & Run

```bash
# Clone
git clone https://github.com/yourusername/aiinpeter.git
cd aiinpeter

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Configure
cp .env.example .env
# Edit .env with your API keys

# Launch everything (backend + overlay)
npm start
```

This starts:
1. **Python FastAPI** backend on port **8765**
2. **Vite** dev server on port **5173**
3. **Electron** overlay window (transparent, always-on-top)

The overlay connects via WebSocket to `ws://localhost:8765/ws`.

### Run Tests

```bash
npm test
# or
cd backend && python ../tests/test_engine.py
```

---

## Configuration (.env)

```env
# Vision
VISION_PROVIDER=openai          # openai or anthropic
VISION_MODEL=gpt-4o             # Vision model to use
OPENAI_API_KEY=sk-...           # Your OpenAI API key

# Engine
FAST_MODE=true                  # Skip LLM reasoning, pure GTO (recommended)
MONTE_CARLO_ITERATIONS=2000     # MC simulations per decision
GTO_STRICTNESS=0.8              # How strictly to follow GTO (0-1)
KELLY_FRACTION=0.25             # Fractional Kelly for bet sizing

# Screen capture
GAME_REGION_W=960               # Game width (left half of 1920x1080)
MONITOR_INDEX=1                 # Which monitor to capture
CAPTURE_INTERVAL_MS=1500        # Screenshot interval
ESP_INTERVAL_MS=80              # ESP overlay refresh (~12 FPS)

# Auto-play (optional)
AUTO_PLAY=false                 # Enable auto-clicking
AUTO_PLAY_DELAY=0.5             # Delay between clicks

# Twitch (optional)
TWITCH_CHANNEL=yourchannel
TWITCH_OAUTH_TOKEN=oauth:...
TWITCH_BOT_NAME=AIINPeterBot
TWITCH_VOTE_DURATION=15         # Seconds to vote

# Voice (optional)
ELEVENLABS_ENABLED=false
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB

# Blackjack
BJ_NUM_DECKS=8                  # Shoe size for card counting
```

---

## Peter's Greatest Quotes

> *"Holy crap, Lois! The math says we're golden. I'm goin' AI-IN."*

> *"GTO stands for 'Griffin Takes Over'. Look it up."*

> *"I'm not just gambling. I'm gambling with MATH. Big difference."*

> *"The Kelly Criterion says I should bet this much. Kelly's a smart lady."*

> *"Shut up, Meg. Daddy's calculating pot odds."*

> *"Roadhouse." \*raises 2x\**

> *"My EV is positive and my beer is cold. Life is good."*

---

## Disclaimer

This project is for **educational and entertainment purposes only**. Online gambling involves real money and real risk. The house always has an edge. No AI agent can guarantee profits. Gamble responsibly.

---

## License

MIT

---

<p align="center">
  <strong>AI-IN Peter</strong> — Where artificial intelligence meets All-In confidence.
  <br/>
  <em>Built with math, Monte Carlo, and the unshakable confidence of Peter Griffin.</em>
</p>
