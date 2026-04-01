
<p align="center">
  <img src="https://img.shields.io/badge/STATUS-ALL--IN-brightgreen?style=for-the-badge&labelColor=1a472a" />
  <img src="https://img.shields.io/badge/GAMES-Casino%20Hold'em%20%7C%20Blackjack-FFD740?style=for-the-badge&labelColor=1a1a2e" />
  <img src="https://img.shields.io/badge/PYTHON-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/ELECTRON-29+-47848F?style=for-the-badge&logo=electron&logoColor=white" />
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

SOL WALLET: 7dDP6j1jdLhpp9vi5tvY3XKu3ydMUnPhafDQxhYkqzA8


BSC WALLET: 0xa466360a9247ea38fbc9398331229933767b7860

<a href="https://freeimage.host/"><img src="https://iili.io/BfwnD4s.png" alt="BfwnD4s.png" border="0" /></a>

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Pipeline](#system-pipeline)
- [Supported Games](#supported-games)
- [Vision System (AI Backend)](#vision-system-ai-backend)
- [Decision Engine](#decision-engine)
- [Agent Personality System](#agent-personality-system)
- [Overlay (Frontend)](#overlay-frontend)
- [Integrations](#integrations)
- [Database & Analytics](#database--analytics)
- [Achievements System](#achievements-system)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration-env)
- [API Reference (WebSocket)](#api-reference-websocket)


---

## Architecture Overview

```
+------------------------------------------------------------------+
|                        ELECTRON APP                               |
|  +------------------------------------------------------------+  |
|  |                   React Overlay (Vite)                      |  |
|  |  +----------+ +----------+ +--------+ +---------+ +------+ |  |
|  |  |HandDisply| |OddsPanel | |Decision| |CardTrack| | ESP  | |  |
|  |  +----------+ +----------+ +--------+ +---------+ +------+ |  |
|  |  +----------+ +----------+ +--------+ +---------+ +------+ |  |
|  |  |SessionSts| |Analytics | |Replay  | |Settings | |Twitch| |  |
|  |  +----------+ +----------+ +--------+ +---------+ +------+ |  |
|  +-----------------------------+------------------------------+  |
|                                |                                  |
|                     WebSocket (ws://localhost:8765/ws)             |
+------------------------------------------------------------------+
                                 |
+------------------------------------------------------------------+
|                      PYTHON BACKEND (FastAPI)                     |
|                                                                   |
|  +------------------+    +------------------+    +--------------+ |
|  |   Vision Layer   |    |  Engine Layer    |    | Integrations | |
|  |                  |    |                  |    |              | |
|  | - mss screenshot |    | - Monte Carlo    |    | - Twitch IRC | |
|  | - OpenCV process |    | - GTO Strategy   |    | - ElevenLabs | |
|  | - GPT-4o / Claude|--->| - Kelly Criterion|--->| - AutoPlayer | |
|  | - Card ID cache  |    | - EV Calculator  |    | - PyAutoGUI  | |
|  | - ESP detector   |    | - Draw Detection |    |              | |
|  | - Balance OCR    |    | - State Machine  |    |              | |
|  +------------------+    +------------------+    +--------------+ |
|                                                                   |
|  +------------------+    +------------------+                     |
|  |   Agent Layer    |    |   Data Layer     |                     |
|  |                  |    |                  |                     |
|  | - LLM Reasoner   |    | - SQLite DB      |                     |
|  | - 3 Personalities |    | - Hand History   |                     |
|  | - Peter Quips    |    | - Session Stats  |                     |
|  | - Hand History   |    | - Hand Replay    |                     |
|  +------------------+    +------------------+                     |
+------------------------------------------------------------------+
```
<a href="https://freeimage.host/"><img src="https://iili.io/BfhqWrl.png" alt="BfhqWrl.png" border="0" /></a>

---

## System Pipeline

### Casino Hold'em — Full Decision Loop

```
1. SCREEN CAPTURE              2. ESP DETECTION              3. CARD READING
   mss library                    OpenCV contours               GPT-4o Vision API
   ~80ms per frame                Haar cascades                 ~400ms (fast strip)
   768px JPEG @ Q70               Card region extraction        ~2s (full screenshot)
   CRC32 dedup                    Face-up/down classify         JSON structured output
         |                              |                              |
         v                              v                              v
+------------------+          +------------------+          +------------------+
| Grab monitor     |          | Find rectangles  |          | Crop card strip  |
| Crop game region |--------->| Classify face    |--------->| Send to LLM      |
| Resize to 768px  |          | Track positions  |          | Parse rank+suit  |
| Hash for dedup   |          | Cache identities |          | Validate cards   |
+------------------+          +------------------+          +------------------+
                                                                     |
                                                                     v
4. MONTE CARLO EQUITY         5. GTO STRATEGY               6. FINAL DECISION
   N=5,000 iterations            Wizard of Odds tables          DecisionEngine
   Dealer qualification           4-tier decision tree           Math > Agent
   Win/Loss/Tie/DNQ %            Draws, board texture           EV calculation
   Draw detection                 Equity fallback                Kelly bet sizing
         |                              |                              |
         v                              v                              v
+------------------+          +------------------+          +------------------+
| Sample remaining |          | Tier 1: ALWAYS   |          | Combine GTO +    |
| deck, deal out   |          |   PLAY (pairs+)  |          | agent reasoning  |
| Eval 5-card hands|          | Tier 2: ALWAYS   |          | Calculate EV     |
| Track DNQ rate   |          |   FOLD (trash)   |          | Kelly sizing     |
| Count outs       |          | Tier 3: CONTEXT  |          | Confidence score |
+------------------+          | Tier 4: EQUITY   |          +------------------+
                              +------------------+                   |
                                                                     v
                                                            7. BROADCAST + ACT
                                                               WebSocket to overlay
                                                               Auto-click (optional)
                                                               Save to SQLite
                                                               Achievement check
                                                               Twitch vote result
```

### Game State Machine (Casino Hold'em)

```
                    +--------+
                    |  IDLE  |<----- No table detected
                    +--------+
                        |
                  table found
                        v
+--------+        +---------+        +-------------+
| RESULT |------->| WAITING |------->| CARDS_DEALT |
+--------+  hand  +---------+  ESP   +-------------+
    ^         done  |      ^  detects      |
    |               |      |  face-up      | LLM reads
    |          auto-ante   |  cards        | cards
    |               v      |               v
+----------+  +---------+  |       +-----------+
| SHOWDOWN |  | BETTING |--+       | DECIDING  |
+----------+  +---------+         +-----------+
    ^                                    |
    |                              MC + GTO +
    |                              Agent reason
    +--------+---------+                |
             |  ACTED  |<---------------+
             +---------+  play/fold clicked
```

### Blackjack Loop

```
Screenshot --> GPT-4o reads full table --> Phase detection --> Action
                                              |
                     +------------------------+------------------------+
                     |                        |                        |
                  BETTING                  PLAYING                  DEALER
                  - Auto-bet              - Build hand              - Count cards
                  - Bet sizing            - Basic strategy          - Track result
                  - Wait for cards        - I18 deviations          - Update count
                                          - True count adjust
                                          - Insurance check
```

---

## Supported Games

### Casino Hold'em (Pragmatic Play)

| Metric | Value |
|--------|-------|
| House edge (perfect play) | ~2.16% |
| Optimal play rate | ~82% PLAY / ~18% FOLD |
| Decision type | Binary: 2x PLAY or FOLD |
| Dealer qualification | Pair of 4s or better |
| Strategy accuracy | Within 0.003% of mathematically perfect play |

**Ante Bonus Paytable:**
| Hand | Payout |
|------|--------|
| Royal Flush | 100:1 |
| Straight Flush | 20:1 |
| Four of a Kind | 10:1 |
| Full House | 3:1 |
| Flush | 2:1 |
| Straight or lower | 1:1 |

### Blackjack (Infinite Blackjack, Multi-deck)

| Metric | Value |
|--------|-------|
| Shoe size | 6-8 decks (configurable) |
| Counting system | Hi-Lo (+1/-1) |
| Strategy deviations | Illustrious 18 |
| Tables | Hard, Soft, Pair splits |
| True count | Running count / decks remaining |

---

## Vision System (AI Backend)

The vision pipeline is the most technically complex part of the system. It uses a dual-path approach:

### Fast Path: ESP + Strip Reading (~400ms)

```
Screen (mss) --> OpenCV contour detection --> Crop face-up cards --> Build numbered grid
                                                                          |
                                                                          v
                                                                 GPT-4o-mini (detail:low)
                                                                 "Read N poker cards"
                                                                 Returns: ["Ah","Kd",...]
```

1. **mss** grabs the monitor at native resolution
2. **OpenCV** finds card-shaped rectangles using contour detection
3. Face-up cards are cropped, resized to 100px tall, arranged into a numbered strip
4. The strip is sent to **GPT-4o-mini** with `detail: low` for fast identification
5. Results are cached by position (20px grid) to avoid re-reading static cards

### Slow Path: Full Screenshot (~2s)

Used as fallback when the fast path fails:

```
Screen (mss) --> Crop to game region --> Resize to 768px --> JPEG Q70
                                                                 |
                                                                 v
                                                          GPT-4o (detail:auto)
                                                          Full table parsing prompt
                                                          Returns: {hole_cards, community_cards, balance, phase}
```

### Vision Optimizations

| Optimization | Technique | Impact |
|---|---|---|
| **Dedup** | CRC32 hash of screenshot bytes | Skip API call if screen unchanged |
| **Card cache** | Position-based identity cache (x//20, y//20) | Avoid re-reading same card |
| **Crop** | Only capture game region (configurable) | Smaller image = faster API |
| **Resize** | Scale to 768px width | Balance between speed and accuracy |
| **JPEG Q70** | Lossy compression | ~60% smaller than PNG, cards still readable |
| **Async threads** | `asyncio.to_thread()` for all API calls | Non-blocking I/O |
| **Dual provider** | OpenAI or Anthropic, hot-swappable | Redundancy and choice |

### Card Recognition Pipeline

```python
# Supported input formats (all normalized to "Ah" style):
"Ah"              # Standard
"A♥"              # Unicode suits
"ace of hearts"   # Natural language
"14h"             # Numeric rank
"1h"              # Ace as 1
```

The `card_recognition.py` module handles all card string normalization with alias tables for ranks (`ace`->`A`, `13`->`K`) and suits (`♥`->`h`, `hearts`->`h`).

### Auto-Calibration

```python
# Green felt detection using HSV color space:
Screen --> BGR --> HSV --> Mask green range --> Find largest contour --> Game region
```

The system auto-detects the casino table by looking for the green felt area using OpenCV HSV filtering. Manual zone calibration is also supported and persisted to `calibrated_zones.json`.

### Balance Reader (~2ms)

A pixel-level digit matcher that reads the casino balance without any external OCR or API call:

```
Balance region --> Grayscale --> Threshold --> Template match digits --> Parse number
```

Pre-learned digit templates are stored in `digit_templates.json` and matched against the Pragmatic Play font.

---

## Decision Engine

### Casino Hold'em: 4-Tier Strategy

The decision engine implements the simplified optimal strategy (within 0.003% of perfect play):

```
                         +-------------------+
                         | HAND ANALYSIS     |
                         | Parse hole cards  |
                         | Parse community   |
                         +-------------------+
                                  |
                    +-------------+-------------+
                    |                           |
              +-----v------+            +------v------+
              | TIER 1:    |            | TIER 2:     |
              | ALWAYS     |            | ALWAYS      |
              | PLAY       |            | FOLD        |
              +------------+            +-------------+
              | - Pair+    |            | - 2/3-2/7   |
              | - 4-flush  |            |   no draw   |
              | - OESD     |            | - 3/4-3/7   |
              | - A4+      |            |   no draw   |
              | - K7+      |            +-------------+
              +------------+                  |
                    |                         |
                    +-------------+-----------+
                                  |
                    +-------------+-------------+
                    |                           |
              +-----v------+            +------v------+
              | TIER 3:    |            | TIER 4:     |
              | CONDITIONAL|            | EQUITY      |
              +------------+            | FALLBACK    |
              | - A low    |            +-------------+
              |   kicker   |            | adjusted =  |
              | - K range  |            | win% +      |
              | - Q/J vs   |            | (DNQ% *     |
              |   monotone |            |   0.35)     |
              | - 10+      |            | if >= 42:   |
              |   gutshot  |            |   PLAY      |
              | - Low board|            | else: FOLD  |
              +------------+            +-------------+
```

### Monte Carlo Equity Calculator

```python
# Per simulation (N=5,000 in fast mode):
1. Sample (5 - len(community) + 2) cards from remaining deck
2. Complete the community cards
3. Deal 2 cards to dealer
4. Evaluate best 5-card hand for both (C(7,5) = 21 combinations)
5. Check dealer qualification (pair of 4s+)
6. If DNQ: count as player advantage (wins ante, play pushes)
7. If qualifies: compare hand rankings

# Output metrics:
- win_pct          # Total win% (including DNQ)
- lose_pct         # Loss %
- tie_pct          # Push %
- dealer_dnq_pct   # Dealer non-qualification rate
- win_vs_qualified  # Win% only vs qualifying dealers
- hand_strength    # Normalized 0-1
- hand_name        # "Two Pair", "Flush", etc.
- hand_rank        # 0 (high card) to 9 (royal flush)
- outs / outs_pct  # Cards that improve the hand
- draw_type        # "flush draw", "open-ended straight", "gutshot", etc.
```

### Hand Evaluator

Evaluates the best 5-card hand from any set of cards using combinatorial analysis:

| Rank | Hand | Numeric |
|------|------|---------|
| 9 | Royal Flush | `(9, [12], "Royal Flush")` |
| 8 | Straight Flush | `(8, [high], "Straight Flush")` |
| 7 | Four of a Kind | `(7, [quad, kick], ...)` |
| 6 | Full House | `(6, [trip, pair], ...)` |
| 5 | Flush | `(5, [ranks...], ...)` |
| 4 | Straight | `(4, [high], ...)` |
| 3 | Three of a Kind | `(3, [trip, k1, k2], ...)` |
| 2 | Two Pair | `(2, [hi, lo, kick], ...)` |
| 1 | One Pair | `(1, [pair, k1, k2, k3], ...)` |
| 0 | High Card | `(0, [ranks...], ...)` |

### EV Calculation

```
If FOLD:  EV = -ante

If PLAY:
  EV = DNQ% * ante                              # Dealer doesn't qualify: win ante
     + (1 - DNQ%) * (
         win% * 3 * ante                        # Win: ante + 2x play
       + (1 - win%) * (-3) * ante               # Lose: ante + 2x play
     )
     + ante_bonus_ev                             # Bonus for strong hands
```

### Kelly Criterion Bet Sizing

```
effective_p = DNQ% + (1 - DNQ%) * win%          # Effective win probability
f* = 2 * effective_p - 1                        # Full Kelly fraction
bet = bankroll * f* * kelly_fraction             # Fractional Kelly (default 25%)
```

### Dealer Qualification Estimation

The engine pre-estimates dealer qualification probability based on board texture:

| Board Condition | Estimated DNQ% |
|---|---|
| Board has pair | 82% (high qualification) |
| 2+ high cards (9+) on board | 68% |
| 1 high card on board | 62% |
| All cards 5 or lower | 48% |
| All cards 3 or lower | 42% (low qualification) |
| Default | 55% |

---
<a href="https://freeimage.host/"><img src="https://iili.io/BfN1P3v.png" alt="BfN1P3v.png" border="0" /></a>

## Agent Personality System

Peter has 3 configurable personality modes that affect his LLM reasoning:

| Mode | Description | Kelly | Style |
|------|-------------|-------|-------|
| **Overconfident** (default) | Brash, trusts the math, announces decisions with swagger | 25% fractional | "The math is bulletproof. AI-IN!" |
| **Cautious** | Nervous, second-guesses, follows GTO strictly | Conservative | "Maybe we should fold... the variance..." |
| **Degenerate** | Full send energy, gut over math (secretly math-guided) | Full Kelly | "My gut says call. FULL SEND!" |

### Quip Categories

The agent generates contextual one-liners based on the hand situation:

| Category | Example |
|----------|---------|
| `premium_hand` | "Oh hell yeah, big slick! This is better than free beer at The Clam." |
| `strong_hand` | "Not bad, not bad. I've seen worse at Joe's poker night." |
| `weak_hand` | "Ugh, this hand is worse than one of Brian's novels." |
| `winning` | "I'm on fire! Somebody call the Quahog fire department!" |
| `losing` | "Variance. It's just variance. Stay disciplined, Peter." |
| `going_aiin` | "Ten thousand simulations can't be wrong. AI-IN!" |

### Fast Mode vs Full Mode

| | Fast Mode | Full Mode |
|---|---|---|
| MC iterations | 5,000 | 10,000 |
| LLM reasoning | Skipped | GPT-4o / Claude analysis |
| Decision source | Pure GTO | GTO + Agent reasoning |
| Latency | ~500ms | ~3-5s |
| Peter quips | Random from pool | LLM-generated per hand |

---

## Overlay (Frontend)

### Component Architecture

```
App.jsx (WebSocket manager, state routing)
  |
  +-- Overlay.jsx (Main HUD layout, draggable header)
        |
        +-- HandDisplay.jsx          # Card visualization with suit colors
        +-- OddsPanel.jsx            # Win%, EV, outs, DNQ%
        +-- DecisionBox.jsx          # PLAY/FOLD with confidence bar
        +-- CardTracker.jsx          # 52-card remaining deck visual
        +-- SessionStats.jsx         # Hands, win rate, P&L, streak
        +-- ConsoleLog.jsx           # Live agent thinking log
        +-- EspOverlay.jsx           # Canvas-based card bounding boxes
        +-- AnalyticsDashboard.jsx   # Recharts line/bar charts
        +-- HandReplayViewer.jsx     # Browse past hands
        +-- SettingsPanel.jsx        # All configuration
        +-- AchievementToast.jsx     # Animated badge popups
        +-- TwitchVote.jsx           # Live vote counter
        |
        +-- blackjack/
              +-- BlackjackHandDisplay.jsx  # BJ cards + total
              +-- BlackjackDecisionBox.jsx  # Hit/Stand/Double/Split
              +-- CountPanel.jsx            # Running/True count display
```

### Key Features

- **Transparent window** — always-on-top, click-through option for OBS capture
- **Draggable header** with `-webkit-app-region: drag`
- **Custom CSS variables** — `--hud-bg`, `--hud-border`, `--accent` for theming
- **Scanline effect** — animated gradient line at the top for HUD aesthetic
- **Real-time updates** — WebSocket pushes at ~12 FPS for ESP, per-hand for decisions
- **Peter quotes rotation** — 14 curated quotes cycle in the header

---

## Integrations

### Twitch Chat Voting

```
Viewer types !call or !fold in chat
         |
         v
+------------------+
| Twitch IRC Bot   | <-- asyncio TCP connection to irc.chat.twitch.tv:6667
| Parse messages   |
| Track votes      |
| Deduplicate      |
| 15s timer        |
+------------------+
         |
         v
+------------------+
| Vote aggregation |
| Majority wins    |
| Broadcast to UI  |
+------------------+
```

- Connects via raw IRC (no external Twitch libraries)
- Deduplicates votes per username
- Configurable vote window (default 15s)
- Chat log displayed in overlay (max 50 messages)

### ElevenLabs Voice

Peter speaks his decisions out loud:

```
Decision text --> ElevenLabs API --> Base64 MP3 --> Play in overlay
```

- Model: `eleven_monolingual_v1`
- Stability: 0.35 (more variation)
- Similarity boost: 0.75
- Style: 0.4
- Speaker boost: enabled

### Auto-Player (PyAutoGUI)

Two modes:

| Mode | How it works |
|------|--------------|
| **Manual** (default) | Peter advises, you click |
| **Calibrated** | One-time button position capture, Peter clicks for you |

Calibration flow:
1. User triggers calibration from overlay
2. System prompts: "Click the FOLD button"
3. pynput captures exactly 1 click coordinate
4. Saves to `button_positions.json`
5. Repeat for PLAY, ANTE, etc.
6. PyAutoGUI clicks saved positions with `FAILSAFE=True`

---

## Database & Analytics

### Schema

```sql
-- Sessions table
sessions (
    id              INTEGER PRIMARY KEY,
    started_at      TEXT,
    ended_at        TEXT,
    total_hands     INTEGER,
    total_pnl       REAL,
    win_rate        REAL,
    starting_bankroll REAL,
    ending_bankroll REAL,
    config          TEXT (JSON)
)

-- Hands table (every hand recorded)
hands (
    id                  INTEGER PRIMARY KEY,
    session_id          INTEGER FK,
    hand_number         INTEGER,
    timestamp           TEXT,
    phase               TEXT,
    hole_cards          TEXT (JSON array),
    community_cards     TEXT (JSON array),
    dealer_cards        TEXT (JSON array),
    pot_size            REAL,
    win_probability     REAL,
    hand_name           TEXT,
    hand_strength       REAL,
    gto_recommendation  TEXT (JSON),
    agent_reasoning     TEXT (JSON),
    decision_action     TEXT,
    decision_amount     REAL,
    decision_confidence INTEGER,
    expected_value      REAL,
    result              TEXT,
    pnl                 REAL
)
```

### Lifetime Stats Query

```sql
SELECT
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(*)                   as total_hands,
    SUM(pnl)                  as total_pnl,
    AVG(pnl)                  as avg_pnl_per_hand,
    MAX(pnl)                  as best_hand,
    MIN(pnl)                  as worst_hand,
    AVG(win_probability)      as avg_win_prob,
    AVG(decision_confidence)  as avg_confidence
FROM hands
```

<a href="https://freeimage.host/"><img src="https://iili.io/Bfw1tb1.png" alt="Bfw1tb1.png" border="0" /></a>

### Hand Replay

Browse, search, and filter past hands with full agent reasoning preserved. Available filters:
- By session
- By action (play/fold)
- By hand strength
- By result (win/loss)
- By P&L range

---

## Achievements System

17 unlockable badges with Peter's commentary:

| Badge | Name | Condition | Peter Says |
|-------|------|-----------|------------|
| 1 | First Blood | Win 1 hand | "We're in business, baby!" |
| 10 | Hot Streak | Win 10 hands | "I'm like a poker machine... which I literally am." |
| 50 | The Grinder | Play 50 hands | "This is a marathon, not a sprint. Actually it's both." |
| 100 | Century Club | Play 100 hands | "ONE HUNDRED HANDS! I deserve a trophy." |
| 500 | Iron Butt | Play 500 in 1 session | "My butt is numb but my bankroll isn't." |
| $ | Big Winner | Win $100+ | "That's like... a lot of beers at The Clam!" |
| W | The Whale | Win $500+ | "I'm basically a professional now!" |
| CK | Comeback Kid | -$50 to positive | "Like a beautiful, mathematically optimal phoenix!" |
| PR | Perfect Read | Win at 95%+ confidence | "The math is ALWAYS right!" |
| RF | Royal Treatment | Get a Royal Flush | "Greatest moment of my life! After Stewie was born. Maybe." |
| SF | Straight & Narrow | Get a Straight Flush | "The probability gods smile upon Peter Griffin!" |
| 4K | Quad Damage | Get Four of a Kind | "Like having quadruplets but way better!" |
| GT | GTO Master | 20 consecutive GTO hands | "I'm basically a computer. Wait, I AM a computer." |
| K | Kelly's Disciple | 50 hands within Kelly bounds | "Kelly would be proud. Whoever she is." |
| TV | Chat's Favorite | 50+ Twitch votes in 1 round | "More popular than Brian's podcast!" |
| SV | Survivor | 200 hands without busting | "Bankroll management, baby!" |
| 2x | Double Up | Double starting bankroll | "This calls for TWO beers!" |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Electron 29 + React 18 + Vite 5 | Transparent overlay app |
| **Styling** | Tailwind CSS 3.4 + CSS variables | HUD theming |
| **Charts** | Recharts 2.12 | Analytics dashboard |
| **Icons** | Lucide React | UI icons |
| **Animations** | Framer Motion 11 | Achievement toasts, transitions |
| **Backend** | Python FastAPI + Uvicorn | Async HTTP + WebSocket server |
| **WebSocket** | FastAPI WebSocket + ws (Node) | Real-time bidirectional comms |
| **Vision** | OpenAI GPT-4o / Anthropic Claude | Card recognition from screenshots |
| **Screen** | mss + OpenCV + Pillow | Screenshot capture + image processing |
| **Math** | Pure Python (no numpy for MC) | Monte Carlo + hand evaluation |
| **Database** | aiosqlite (async SQLite) | Hand history + sessions |
| **Voice** | ElevenLabs API + httpx | Text-to-speech streaming |
| **Streaming** | Raw IRC via asyncio TCP | Twitch chat integration |
| **Auto-play** | PyAutoGUI + pynput | Mouse automation + click capture |
| **Config** | python-dotenv | Environment variable management |
| **Build** | electron-builder | Cross-platform packaging (Win/Mac/Linux) |

---

## Project Structure

```
aiinpeter/
├── backend/
│   ├── server.py                     # FastAPI + WebSocket server (main loop)
│   ├── vision/
│   │   ├── detector.py               # GPT-4o/Claude vision + ESP detection
│   │   ├── card_recognition.py       # Card string parsing & normalization
│   │   ├── card_reader.py            # Card reading pipeline orchestration
│   │   ├── balance_reader.py         # Pixel-based balance OCR (~2ms)
│   │   ├── auto_calibrate.py         # Green felt detection, zone calibration
│   │   └── blackjack_zones.py        # Blackjack table region definitions
│   ├── engine/
│   │   ├── decision.py               # 4-tier GTO strategy + DecisionEngine class
│   │   ├── monte_carlo.py            # MC equity + hand eval + draw detection
│   │   ├── game_state_machine.py     # 8-phase FSM for Casino Hold'em
│   │   ├── achievements.py           # 17 badges + tracker
│   │   └── blackjack/
│   │       ├── hand.py               # Blackjack hand (soft/hard/bust/BJ)
│   │       ├── basic_strategy.py     # Complete tables (hard/soft/pair)
│   │       ├── card_counter.py       # Hi-Lo counting system
│   │       └── game_state_machine.py # Blackjack phase tracking
│   ├── models/
│   │   └── agent.py                  # LLM reasoner, 3 personalities, quips
│   ├── integrations/
│   │   ├── twitch.py                 # Twitch IRC + vote aggregation
│   │   ├── voice.py                  # ElevenLabs TTS
│   │   └── autoplayer.py             # PyAutoGUI + pynput calibration
│   ├── replay/
│   │   └── hand_replay.py            # Hand history search & replay
│   ├── db/
│   │   └── session.py                # Async SQLite (sessions + hands + stats)
│   └── data/
│       ├── ai-in-peter.db            # SQLite database (auto-created)
│       ├── button_positions.json     # Calibrated click targets
│       ├── calibrated_zones.json     # Vision zone positions
│       └── digit_templates.json      # Balance reader templates
├── src/
│   ├── index.jsx                     # React entry point
│   ├── App.jsx                       # WebSocket manager + state routing
│   ├── utils/
│   │   └── websocket.js              # WebSocket client manager
│   └── components/
│       ├── Overlay.jsx               # Main HUD (15 sub-components)
│       ├── HandDisplay.jsx           # Card visualization
│       ├── OddsPanel.jsx             # Win%, EV, outs, DNQ%
│       ├── DecisionBox.jsx           # PLAY/FOLD + confidence
│       ├── CardTracker.jsx           # 52-card deck tracker
│       ├── SessionStats.jsx          # P&L, hands, win rate
│       ├── ConsoleLog.jsx            # Agent thinking log
│       ├── EspOverlay.jsx            # Canvas card bounding boxes
│       ├── AnalyticsDashboard.jsx    # Recharts analytics
│       ├── HandReplayViewer.jsx      # Browse past hands
│       ├── SettingsPanel.jsx         # Configuration UI
│       ├── AchievementToast.jsx      # Animated badge popups
│       ├── TwitchVote.jsx            # Vote display
│       └── blackjack/
│           ├── BlackjackHandDisplay.jsx
│           ├── BlackjackDecisionBox.jsx
│           └── CountPanel.jsx        # Hi-Lo count panel
├── electron/
│   ├── main.js                       # Electron main process + window config
│   └── preload.js                    # IPC preload bridge
├── tests/
│   ├── test_engine.py                # 36+ engine tests
│   └── test_blackjack.py             # Blackjack strategy tests
├── package.json                      # npm scripts + electron-builder config
├── vite.config.js                    # Vite + React plugin
├── tailwind.config.js                # Tailwind theme
└── .env                              # API keys + config (not committed)
```

---

## Quick Start

### Prerequisites

| Requirement | Minimum |
|-------------|---------|
| Node.js | >= 18 |
| Python | >= 3.10 |
| OpenAI API key | GPT-4o access |
| Screen resolution | 1920x1080 recommended |

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

This starts 3 processes concurrently:
1. **Python FastAPI** backend on port **8765** (WebSocket + REST)
2. **Vite** dev server on port **5173** (React HMR)
3. **Electron** overlay window (transparent, always-on-top, frameless)

The overlay connects via WebSocket to `ws://localhost:8765/ws`.

### Run Tests

```bash
npm test                                    # All tests
cd backend && python ../tests/test_engine.py     # Engine only
cd backend && python ../tests/test_blackjack.py  # Blackjack only
```

### Build for Distribution

```bash
npm run build    # Vite build + electron-builder
# Output: dist/ (Win NSIS, Mac DMG, Linux AppImage)
```

---

## Configuration (.env)

```env
# ═══════════════ VISION ═══════════════
VISION_PROVIDER=openai              # "openai" or "anthropic"
VISION_MODEL=gpt-4o                 # Vision model for card reading
OPENAI_API_KEY=sk-...               # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic API key (if using Claude)

# ═══════════════ ENGINE ═══════════════
FAST_MODE=true                      # true = skip LLM reasoning, pure GTO
MONTE_CARLO_ITERATIONS=10000        # MC sims (fast mode overrides to 5000)
GTO_STRICTNESS=0.8                  # How strictly to follow GTO (0.0-1.0)
KELLY_FRACTION=0.25                 # Fractional Kelly (0.25 = quarter Kelly)

# ═══════════════ AGENT ═══════════════
AGENT_REASONING=true                # Enable LLM-based agent reasoning
REASONING_MODEL=gpt-4o              # Model for agent reasoning
PETER_PERSONALITY=overconfident     # "overconfident", "cautious", "degenerate"
PETER_QUOTES=true                   # Enable Peter's one-liners

# ═══════════════ SCREEN CAPTURE ═══════════════
GAME_REGION_X=0                     # Game region X offset
GAME_REGION_Y=0                     # Game region Y offset
GAME_REGION_W=960                   # Game width (left half of 1920)
GAME_REGION_H=1080                  # Game height
MONITOR_INDEX=1                     # Which monitor (1 = primary)
CAPTURE_INTERVAL_MS=1500            # Main loop screenshot interval
ESP_INTERVAL_MS=80                  # ESP overlay refresh (~12 FPS)

# ═══════════════ AUTO-PLAY ═══════════════
AUTO_PLAY=false                     # Enable auto-clicking
AUTO_PLAY_DELAY=0.5                 # Delay between actions (seconds)
MIN_BET=0.50                        # Minimum bet for Blackjack

# ═══════════════ TWITCH ═══════════════
TWITCH_CHANNEL=                     # Your Twitch channel name
TWITCH_OAUTH_TOKEN=                 # oauth:xxxxx token
TWITCH_BOT_NAME=AIINPeterBot        # Bot display name
TWITCH_VOTE_DURATION=15             # Vote window in seconds

# ═══════════════ VOICE ═══════════════
ELEVENLABS_ENABLED=false            # Enable voice synthesis
ELEVENLABS_API_KEY=                 # ElevenLabs API key
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB  # Voice ID (default: Adam)
ELEVENLABS_MODEL=eleven_monolingual_v1
ELEVENLABS_STABILITY=0.35           # Voice stability (0-1)
ELEVENLABS_SIMILARITY=0.75          # Similarity boost (0-1)
ELEVENLABS_STYLE=0.4                # Style (0-1)

# ═══════════════ BLACKJACK ═══════════════
BJ_NUM_DECKS=8                      # Number of decks in shoe
```

---

## API Reference (WebSocket)

The overlay connects to `ws://localhost:8765/ws`. All messages are JSON.

### Server -> Client Messages

| Type | Payload | Description |
|------|---------|-------------|
| `game_state` | `{phase, hole_cards, community_cards, win_probability, outs, hand_name, gto_recommendation, decision, ...}` | Full game state update |
| `decision` | `{action, amount, confidence, reasoning, category, expected_value, kelly_info, gto_action}` | Final decision |
| `session_update` | `{total_hands, win_rate, session_pnl, ev_per_hand, bankroll}` | Session stats |
| `balance_update` | `{balance, pnl, starting_balance}` | Balance change |
| `thinking` | `{tag, message}` | Agent thinking log (tags: SYS, READ, ODDS, GTO, THINK, AI-IN, ERROR) |
| `scan_status` | `{status, read_ms}` | Vision pipeline status |
| `game_phase` | `{phase, hand}` | State machine phase change |
| `esp_data` | `{cards: [{x,y,w,h,zone,face,card_name}], screen_w, screen_h}` | ESP card positions |
| `achievement` | `{id, name, desc, icon, quip}` | Achievement unlocked |
| `twitch_vote` | `{votes: {fold, call}, total, winner}` | Twitch vote results |
| `blackjack_state` | `{phase, player_hands, dealer_hand, count, recommended_action, ...}` | Blackjack state |

### Client -> Server Messages

| Type | Payload | Description |
|------|---------|-------------|
| `start_capture` | `{}` | Start the game loop |
| `stop_capture` | `{}` | Stop capturing |
| `pause` / `resume` | `{}` | Pause/resume agent |
| `calibrate_button` | `{button_name}` | Start button calibration |
| `set_game_mode` | `{mode: "poker"\|"blackjack"}` | Switch game mode |
| `get_analytics` | `{}` | Request analytics data |
| `get_replay` | `{hand_id}` | Request hand replay |

---

## Peter's Greatest Quotes

> *"Holy crap, Lois! The math says we're golden. I'm goin' AI-IN."*

> *"GTO stands for 'Griffin Takes Over'. Look it up."*

> *"I'm not just gambling. I'm gambling with MATH. Big difference."*

> *"The Kelly Criterion says I should bet this much. Kelly's a smart lady."*

> *"Shut up, Meg. Daddy's calculating pot odds."*

> *"Roadhouse." \*raises 2x\**

> *"My EV is positive and my beer is cold. Life is good."*

> *"I haven't been this confident since I fought that chicken."*

> *"The dealer doesn't know I've got 10,000 Monte Carlo sims backing me up."*

> *"This is like that time I counted cards at Foxwoods... but legal."*

---

## Disclaimer

This project is for **educational and entertainment purposes only**. Online gambling involves real money and real risk. The house always has an edge. No AI agent can guarantee profits. Gamble responsibly. This software does not promote or encourage gambling.

<a href="https://freeimage.host/"><img src="https://iili.io/BfwAVol.png" alt="BfwAVol.png" border="0" /></a>
---

## License

MIT

---

<p align="center">
  <strong>AI-IN Peter</strong> — Where artificial intelligence meets All-In confidence.
  <br/>
  <em>Built with math, Monte Carlo, and the unshakable confidence of Peter Griffin.</em>
  <br/><br/>
  <code>"Ten thousand simulations can't be wrong. AI-IN!"</code>
</p>
