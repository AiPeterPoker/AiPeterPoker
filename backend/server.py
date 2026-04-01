"""
AI-IN Peter — Backend Server
"The math doesn't lie and neither does Peter Griffin."
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path

import cv2
import mss
import numpy as np
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from vision.detector import GameStateDetector
from vision.blackjack_zones import BLACKJACK_TABLE_ZONES
from engine.decision import DecisionEngine
from engine.monte_carlo import MonteCarloEquity
from engine.achievements import AchievementTracker
from engine.blackjack import BlackjackHand, get_action as bj_get_action, CardCounter
from engine.blackjack.basic_strategy import dealer_upcard_value, should_take_insurance
from engine.blackjack.game_state_machine import BlackjackStateMachine, Phase as BJPhase
from db.session import SessionDB
from models.agent import AgentReasoner
from integrations.twitch import TwitchIntegration
from integrations.voice import PeterVoice
from integrations.autoplayer import AutoPlayer
from replay.hand_replay import HandReplay

load_dotenv(Path(__file__).parent.parent / ".env")

app = FastAPI(title="AI-IN Peter Backend")


class AppState:
    def __init__(self):
        self.ws_clients: list[WebSocket] = []
        self.is_capturing = False
        self.is_paused = False
        self.capture_interval = float(os.getenv("CAPTURE_INTERVAL_MS", "1500")) / 1000
        self.detector = GameStateDetector()
        self.mc_engine = MonteCarloEquity(iterations=int(os.getenv("MONTE_CARLO_ITERATIONS", "10000")))
        self.decision_engine = DecisionEngine(
            gto_strictness=float(os.getenv("GTO_STRICTNESS", "0.8")),
            kelly_fraction=float(os.getenv("KELLY_FRACTION", "0.25")),
        )
        self.agent = AgentReasoner()
        self.twitch = TwitchIntegration()
        self.voice = PeterVoice()
        self.autoplayer = AutoPlayer()
        self.achievements = AchievementTracker()
        self.replay = HandReplay()
        self.db = SessionDB()
        # Fast mode: skip LLM reasoning, reduce MC iterations, pure GTO
        self.fast_mode = os.getenv("FAST_MODE", "true").lower() == "true"
        # Game mode: "poker" or "blackjack"
        self.game_mode = "poker"
        # Blackjack-specific state
        self.bj_state_machine = BlackjackStateMachine()
        self.bj_counter = CardCounter(num_decks=int(os.getenv("BJ_NUM_DECKS", "8")))
        self.bj_player_cards: list[str] = []
        self.bj_dealer_cards: list[str] = []
        self._poker_zones = None  # Saved poker zones for switching back
        self.session_id = None
        self.hand_count = 0
        self.session_pnl = 0.0
        self.wins = 0
        self.bankroll = 0.0  # Will be set from screen balance reading
        self.last_game_state = {}
        self.capture_task = None
        self.esp_task = None
        self.esp_interval = float(os.getenv("ESP_INTERVAL_MS", "80")) / 1000  # ~12 FPS
        self._esp_card_result = None  # Card read from ESP fast path
        self._last_esp_regions = []  # Latest ESP card regions for state machine
        # Balance tracking from screen
        self.starting_balance: float | None = None
        self.screen_balance: float = 0.0

state = AppState()


async def broadcast(msg_type: str, payload: dict):
    message = json.dumps({"type": msg_type, "payload": payload})
    disconnected = []
    for ws in state.ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        state.ws_clients.remove(ws)


async def think(tag: str, message: str):
    await broadcast("thinking", {"tag": tag, "message": message})


async def update_balance_from_state(game_state: dict):
    """Extract balance from a game state dict (LLM or ESP) and broadcast balance_update."""
    from vision.detector import GameStateDetector
    bal = GameStateDetector.extract_balance_from_state(game_state)
    if bal is not None and bal > 0:
        state.screen_balance = bal
        state.bankroll = bal
        if state.starting_balance is None:
            state.starting_balance = bal
            await think("SYS", f"Starting balance: ${bal:.2f}")
        pnl = bal - state.starting_balance
        state.session_pnl = pnl
        await broadcast("balance_update", {
            "balance": round(bal, 2),
            "pnl": round(pnl, 2),
            "starting_balance": round(state.starting_balance, 2),
        })


async def capture_loop():
    """Main game loop — driven by GameStateMachine.
    ESP loop feeds card data, this loop processes decisions.
    """
    from engine.game_state_machine import GameStateMachine, GamePhase
    from engine.decision import optimal_decision

    await think("PETER", '"Alright, let\'s see what we\'re working with here..."')

    # Auto-crop to game area
    game_x = int(os.getenv("GAME_REGION_X", "0"))
    game_y = int(os.getenv("GAME_REGION_Y", "0"))
    game_w = int(os.getenv("GAME_REGION_W", "960"))
    game_h = int(os.getenv("GAME_REGION_H", "1080"))
    if game_w > 0 and game_h > 0:
        state.detector.set_crop_region(game_x, game_y, game_w, game_h)

    gsm = GameStateMachine()
    balance_check_counter = 0

    while state.is_capturing:
        if state.is_paused:
            await asyncio.sleep(0.5)
            continue

        try:
            # ── Feed ESP data to state machine ───────────────────────
            card_regions = state._last_esp_regions or []
            transition = gsm.process_esp(card_regions)
            if transition:
                await think("STATE", transition)

            # Broadcast current phase
            await broadcast("game_phase", {"phase": gsm.phase.value, "hand": gsm.hand_number})

            # ── WAITING: clear UI + auto-ante + read balance ─────────
            if gsm.phase == GamePhase.WAITING:
                if gsm.should_clear_ui():
                    state._esp_card_result = None
                    state.detector.clear_card_cache()
                    state.detector.force_next_capture()
                    await broadcast("game_state", {
                        "phase": "waiting", "hole_cards": [], "community_cards": [],
                        "hand_strength": 0, "hand_name": "", "win_probability": 0,
                        "outs": 0, "outs_percentage": 0, "expected_value": 0,
                        "gto_recommendation": {"fold": 50, "call": 50},
                        "decision": None, "draw_type": None, "draw_outs": 0,
                        "pot_size": 0, "current_bet": 0, "dealer_qualifies_pct": 55,
                        "remaining_deck": 52, "favorable_outs": 0,
                    })

                # Read balance via LLM periodically while idle
                balance_check_counter += 1
                if balance_check_counter % 20 == 1:
                    try:
                        fb = await asyncio.to_thread(state.detector.capture_screen)
                        if fb:
                            gs = await state.detector.detect_game_state(fb)
                            if gs:
                                await update_balance_from_state(gs)
                    except Exception:
                        pass

                # Auto-ante
                if gsm.should_click_ante() and state.autoplayer.is_available() and "ante" in state.autoplayer.positions:
                    clicked = await state.autoplayer.execute_action("ante")
                    if clicked:
                        msg = gsm.mark_ante_clicked()
                        await think("AI-IN", f"Auto-ANTE | {msg}")

                await asyncio.sleep(0.3)
                continue

            # ── BETTING: just wait for cards ──────────────────────────
            if gsm.phase == GamePhase.BETTING:
                await asyncio.sleep(0.3)
                continue

            # ── CARDS_DEALT: read cards with LLM ──────────────────────
            if gsm.phase == GamePhase.CARDS_DEALT:
                try:
                    await broadcast("scan_status", {"status": "reading"})
                    read_start = time.time()

                    # Try fast strip read first (uses ESP card crops → faster)
                    regions, size, strip_b64 = await asyncio.to_thread(
                        state.detector.capture_esp_only)
                    face_up = [c for c in regions if c.get("face") == "up" and not c.get("is_zone")]
                    n_total = len(face_up)

                    llm_result = None
                    if strip_b64 and n_total > 0:
                        llm_result = await state.detector.read_cards_fast(strip_b64, n_total)

                    # Fallback: full screenshot
                    if not llm_result or not llm_result.get("hole_cards"):
                        fb = await asyncio.to_thread(state.detector.capture_screen)
                        if fb:
                            llm_result = await state.detector.detect_game_state(fb)

                    read_ms = int((time.time() - read_start) * 1000)

                    if llm_result:
                        hole = llm_result.get("hole_cards", [])
                        comm = llm_result.get("community_cards", [])
                        await update_balance_from_state(llm_result)

                        if hole:
                            await think("READ", f"[{read_ms}ms] hole={hole} community={comm}")
                            await broadcast("scan_status", {"status": "done", "read_ms": read_ms})
                            gsm.current_hand = {"hole_cards": hole, "community_cards": comm}
                            msg = gsm.transition(GamePhase.DECIDING, f"hole={hole}")
                            await think("STATE", msg)
                            continue

                except Exception as e:
                    await think("ERROR", f"Card read: {e}")

                if gsm.phase_duration > 8:
                    msg = gsm.transition(GamePhase.WAITING, "read timeout")
                    await think("STATE", msg)

                await asyncio.sleep(0.3)
                continue

            # ── DECIDING: run Monte Carlo + GTO + make decision ───────
            if gsm.phase == GamePhase.DECIDING:
                hole = gsm.current_hand.get("hole_cards", [])
                community = gsm.current_hand.get("community_cards", [])

                if not hole:
                    await asyncio.sleep(0.3)
                    continue

                await think("READ", f"Hole: {hole} | Community: {community}")

                # ── Step 1: Monte Carlo (5k iterations) ──────────────
                await think("ODDS", "Running Monte Carlo simulations...")
                mc_iters = 5000 if state.fast_mode else state.mc_engine.iterations
                old_iters = state.mc_engine.iterations
                state.mc_engine.iterations = mc_iters
                equity = await asyncio.to_thread(state.mc_engine.calculate_equity, hole, community)
                state.mc_engine.iterations = old_iters

                draw_msg = f" | {equity['draw_type']} ({equity['draw_outs']} outs)" if equity.get("draw_type") else ""
                await think("ODDS", f"Win: {equity['win_pct']:.1f}% | DNQ: {equity.get('dealer_dnq_pct',0):.0f}% | {equity.get('hand_name','?')}{draw_msg}")

                # ── Step 2: Broadcast hand info to UI (so viewer sees the analysis) ──
                game_state = {
                    "phase": "flop" if community else "pre_flop",
                    "hole_cards": hole, "community_cards": community,
                    "pot_size": 0, "current_bet": 1,
                    "win_probability": round(equity["win_pct"], 1),
                    "outs": equity.get("outs", 0),
                    "outs_percentage": equity.get("outs_pct", 0),
                    "hand_strength": equity.get("hand_strength", 0),
                    "hand_name": equity.get("hand_name", ""),
                    "draw_type": equity.get("draw_type"),
                    "draw_outs": equity.get("draw_outs", 0),
                    "dealer_dnq_pct": equity.get("dealer_dnq_pct", 55),
                    "remaining_deck": 52 - len(hole) - len(community),
                    "favorable_outs": equity.get("favorable_outs", 0),
                }
                # Show analysis to UI immediately
                await broadcast("game_state", game_state)

                # ── Step 3: GTO optimal decision ─────────────────────
                opt = optimal_decision(hole, community, equity.get("hand_rank", 0),
                                       equity.get("win_pct", 50), equity.get("dealer_dnq_pct", 55))
                gto = {"fold": opt["fold_pct"], "call": opt["call_pct"]}
                game_state["gto_recommendation"] = gto
                game_state["expected_value"] = state.decision_engine.calculate_ev(
                    {"pot_size": 0, "current_bet": 1}, equity)
                game_state["dealer_qualifies_pct"] = state.decision_engine.estimate_dealer_qualification(community)

                await think("GTO", f"{opt['action'].upper()} — {opt['reason']} [{opt['category']}]")

                # ── Step 5: Reasoning ─────────────────────────────────
                reasoning = {
                    "thoughts": [f"Optimal: {opt['action'].upper()} — {opt['reason']}"],
                    "recommended_action": opt["action"],
                    "confidence": opt["call_pct"] if opt["action"] == "call" else opt["fold_pct"],
                    "summary": f"{opt['reason']} [{opt['category']}]",
                }

                if not state.fast_mode:
                    try:
                        await think("THINK", "Peter's analyzing the board...")
                        llm_reasoning = await state.agent.reason(
                            {"hole_cards": hole, "community_cards": community}, equity, gto)
                        for thought in llm_reasoning.get("thoughts", []):
                            await think("THINK", thought)
                        reasoning = llm_reasoning
                    except Exception:
                        pass

                # ── Step 6: Final decision ────────────────────────────
                decision = state.decision_engine.make_decision(game_state, equity, gto, reasoning, state.bankroll)
                game_state["decision"] = decision
                game_state["gto_recommendation"] = gto

                action_verb = "2x PLAY" if decision["action"] == "call" else "FOLD"
                await think("AI-IN", f">>> {action_verb} <<< | {decision.get('reasoning', '')} | Confidence: {decision['confidence']}%")

                # ── Step 7: Broadcast final decision to UI ────────────
                await broadcast("game_state", game_state)
                await broadcast("decision", decision)
                await state.db.save_hand(state.session_id, game_state, decision)

                # Auto-click
                if state.autoplayer.is_available():
                    clicked = await state.autoplayer.execute_action(decision["action"], game_state)
                    if clicked:
                        await think("AI-IN", f"Auto-clicked: {action_verb}")
                        msg = gsm.mark_decision_made(decision)
                        await think("STATE", msg)
                    else:
                        await think("AI-IN", f"Button not calibrated for '{action_verb}'")
                        gsm.mark_decision_made(decision)
                else:
                    # Manual mode — just mark decision made
                    gsm.mark_decision_made(decision)

                # Update stats
                state.hand_count += 1
                win_rate = (state.wins / state.hand_count * 100) if state.hand_count > 0 else 0
                await broadcast("session_update", {
                    "total_hands": state.hand_count,
                    "win_rate": round(win_rate, 1),
                    "session_pnl": round(state.session_pnl, 2),
                    "ev_per_hand": round(state.session_pnl / state.hand_count, 2) if state.hand_count else 0,
                    "bankroll": round(state.bankroll, 2),
                })

                continue

            # ── ACTED / SHOWDOWN: wait for resolution ─────────────────
            if gsm.phase in (GamePhase.ACTED, GamePhase.SHOWDOWN):
                await asyncio.sleep(0.3)
                continue

            # ── RESULT: auto-transitions back to WAITING via process_esp
            if gsm.phase == GamePhase.RESULT:
                if gsm.needs_card_cache_clear():
                    state.detector.clear_card_cache()
                    state.detector.force_next_capture()
                await asyncio.sleep(0.2)
                continue

            # ── IDLE: wait for table detection ────────────────────────
            await asyncio.sleep(0.5)

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                await think("ERROR", "API KEY INVALID!")
                await asyncio.sleep(30)
                continue
            await think("ERROR", f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(1)

    await think("PETER", '"That\'s a wrap. Time for a beer."')


async def blackjack_capture_loop():
    """Blackjack game loop — screenshot → LLM reads full game state → decide → act.

    Key principle: the LLM tells us the PHASE (betting/playing/dealer/waiting).
    We NEVER assume cards exist — we trust what the LLM sees.
    """
    await think("PETER", '"Alright, time for some Infinite Blackjack. The count starts now..."')

    game_x = int(os.getenv("GAME_REGION_X", "0"))
    game_y = int(os.getenv("GAME_REGION_Y", "0"))
    game_w = int(os.getenv("GAME_REGION_W", "960"))
    game_h = int(os.getenv("GAME_REGION_H", "1080"))
    if game_w > 0 and game_h > 0:
        state.detector.set_crop_region(game_x, game_y, game_w, game_h)

    counter = state.bj_counter
    min_bet = float(os.getenv("MIN_BET", "0.50"))
    last_action_phase = None  # Track what we already did this hand

    while state.is_capturing:
        if state.is_paused:
            await asyncio.sleep(0.5)
            continue

        try:
            # ── Step 1: Screenshot → LLM reads full game state ──
            state.detector.force_next_capture()
            fb = await asyncio.to_thread(state.detector.capture_screen)
            if not fb:
                await asyncio.sleep(1)
                continue

            result = await _read_blackjack_table(fb)
            if not result:
                await think("BJ", "Could not read table")
                await asyncio.sleep(2)
                continue

            phase = result.get("phase", "unknown")
            p_cards = result.get("player_cards", [])
            d_cards = result.get("dealer_cards", [])
            await think("BJ", f"Phase: {phase} | Player: {p_cards} | Dealer: {d_cards}")

            # ── Step 2: Act based on phase ──────────────────────

            if phase == "betting":
                # Table is in betting phase — place bet
                last_action_phase = None
                state.bj_player_cards = []
                state.bj_dealer_cards = []

                if state.autoplayer.is_available() and "bet" in state.autoplayer.positions:
                    if "chip" in state.autoplayer.positions:
                        await state.autoplayer.execute_action("chip")
                        await asyncio.sleep(0.3)
                    await state.autoplayer.execute_action("bet")
                    await think("AI-IN", "Auto-BET placed")

                await broadcast("blackjack_state", {
                    "phase": "waiting", "player_hands": [],
                    "dealer_hand": {"cards": [], "total": 0},
                    "count": counter.get_state(),
                    "recommended_action": None,
                    "bet_recommendation": counter.bet_recommendation(min_bet),
                    "is_deviation": False,
                })
                await asyncio.sleep(2)

            elif phase == "playing" and len(p_cards) >= 2 and len(d_cards) >= 1:
                # Cards dealt, player's turn — decide and act
                if last_action_phase == "playing" and p_cards == state.bj_player_cards:
                    # Already acted on these exact cards, wait for change
                    await asyncio.sleep(1)
                    continue

                # Count new cards
                for c in p_cards:
                    if c not in state.bj_player_cards and c != "XX":
                        counter.count_card(c)
                for c in d_cards:
                    if c not in state.bj_dealer_cards and c != "XX":
                        counter.count_card(c)
                state.bj_player_cards = p_cards
                state.bj_dealer_cards = d_cards

                player_hand = BlackjackHand(p_cards)
                visible_dealer = [c for c in d_cards if c != "XX"]
                if not visible_dealer:
                    await asyncio.sleep(1)
                    continue

                d_up_val = dealer_upcard_value(visible_dealer[0])
                decision = bj_get_action(
                    player_hand, d_up_val,
                    can_double=player_hand.num_cards == 2,
                    can_split=player_hand.is_pair and player_hand.num_cards == 2,
                    true_count=counter.true_count,
                )
                insurance = should_take_insurance(counter.true_count) if d_up_val == 11 else False

                await think("BJ", f"{p_cards} ({player_hand.total}{'S' if player_hand.is_soft else 'H'}) vs {visible_dealer[0]} → {decision['action']}")

                await broadcast("blackjack_state", {
                    "phase": "player_turn",
                    "player_hands": [{"cards": p_cards, "total": player_hand.total,
                                      "is_soft": player_hand.is_soft, "is_blackjack": player_hand.is_blackjack,
                                      "is_busted": player_hand.is_busted}],
                    "dealer_hand": {"cards": d_cards, "upcard": visible_dealer[0], "total": None},
                    "count": counter.get_state(),
                    "recommended_action": decision["action"], "reason": decision["reason"],
                    "is_deviation": decision["is_deviation"], "insurance": insurance,
                    "bet_recommendation": counter.bet_recommendation(min_bet),
                })
                await broadcast("decision", {
                    "action": decision["action"], "confidence": 95 if not decision["is_deviation"] else 80,
                    "reasoning": decision["reason"], "game_mode": "blackjack",
                })

                # Auto-click
                if state.autoplayer.is_available():
                    clicked = await state.autoplayer.execute_action(decision["action"])
                    if clicked:
                        await think("AI-IN", f"Auto-clicked: {decision['action']}")

                last_action_phase = "playing"
                await asyncio.sleep(2)  # Wait for animation before re-reading

            elif phase == "dealer":
                # Dealer is playing — just read and count cards
                for c in d_cards:
                    if c not in state.bj_dealer_cards and c != "XX":
                        counter.count_card(c)
                state.bj_dealer_cards = d_cards

                dealer_hand = BlackjackHand([c for c in d_cards if c != "XX"])
                player_hand = BlackjackHand(state.bj_player_cards) if state.bj_player_cards else None
                await broadcast("blackjack_state", {
                    "phase": "dealer_turn",
                    "player_hands": [{"cards": state.bj_player_cards, "total": player_hand.total if player_hand else 0,
                                      "is_soft": player_hand.is_soft if player_hand else False,
                                      "is_blackjack": player_hand.is_blackjack if player_hand else False,
                                      "is_busted": player_hand.is_busted if player_hand else False}] if player_hand else [],
                    "dealer_hand": {"cards": d_cards, "total": dealer_hand.total, "is_busted": dealer_hand.is_busted},
                    "count": counter.get_state(), "recommended_action": None,
                    "bet_recommendation": counter.bet_recommendation(min_bet), "is_deviation": False,
                })
                last_action_phase = "dealer"
                await asyncio.sleep(2)

            elif phase == "result":
                # Hand is over
                if last_action_phase != "result":
                    player_hand = BlackjackHand(state.bj_player_cards) if state.bj_player_cards else None
                    dealer_hand = BlackjackHand([c for c in state.bj_dealer_cards if c != "XX"])
                    r = "push"
                    if player_hand:
                        if player_hand.is_busted: r = "lose"
                        elif dealer_hand.is_busted: r = "win"
                        elif player_hand.is_blackjack and not dealer_hand.is_blackjack: r = "blackjack"
                        elif player_hand.total > dealer_hand.total: r = "win"
                        elif player_hand.total < dealer_hand.total: r = "lose"
                    if r in ("win", "blackjack"):
                        state.wins += 1
                    state.hand_count += 1
                    await think("BJ", f"Result: {r.upper()} | Count: RC={counter.running_count} TC={counter.true_count:.1f}")
                    win_rate = (state.wins / state.hand_count * 100) if state.hand_count else 0
                    await broadcast("session_update", {
                        "total_hands": state.hand_count, "win_rate": round(win_rate, 1),
                        "session_pnl": round(state.session_pnl, 2),
                        "ev_per_hand": round(state.session_pnl / state.hand_count, 2) if state.hand_count else 0,
                        "bankroll": round(state.bankroll, 2),
                    })
                    last_action_phase = "result"
                await asyncio.sleep(3)

            else:
                # Unknown or waiting — just wait
                await asyncio.sleep(2)

        except Exception as e:
            await think("ERROR", f"BJ Error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(2)

    await think("PETER", '"Blackjack session over. The count lives in my head rent-free."')


async def _read_blackjack_table(screenshot_b64: str) -> dict | None:
    """Send screenshot to LLM and ask it to read the FULL blackjack game state.
    The LLM must tell us the phase — we never assume cards exist."""
    prompt = """This is Evolution Infinite Blackjack (live dealer) on Solcasino.io.
Look at the screen and tell me the CURRENT GAME STATE.

IMPORTANT: Only report cards you can ACTUALLY SEE face-up on the table.
If no cards are visible, phase is "betting" or "waiting".

Phases:
- "betting" = timer counting down, "PLACE YOUR BETS" or chips visible, no cards dealt yet
- "playing" = player has cards, "MAKE YOUR DECISION" or HIT/STAND buttons visible
- "dealer" = dealer is revealing cards, player has already acted
- "result" = hand is over, showing win/lose/push
- "waiting" = between rounds, "NEXT GAME SOON" or no activity

Card format: rank + suit letter (Ah Kd 10s 5c Jh Qs 2d)
Face-down cards = "XX"

Return ONLY this JSON:
{"phase":"betting","player_cards":[],"dealer_cards":[],"balance":0}

If phase is "betting" or "waiting", player_cards and dealer_cards MUST be empty arrays [].
Only put cards in arrays if you actually see them face-up on the table."""

    try:
        if state.detector.provider == "openai":
            import asyncio
            response = await asyncio.to_thread(
                state.detector.client.chat.completions.create,
                model=state.detector.model,
                max_tokens=100,
                temperature=0,
                messages=[{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}", "detail": "auto"}},
                    {"type": "text", "text": prompt},
                ]}],
            )
            return state.detector._parse_response(response.choices[0].message.content)
        elif state.detector.provider == "anthropic":
            import asyncio
            response = await asyncio.to_thread(
                state.detector.client.messages.create,
                model=state.detector.model,
                max_tokens=100,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": screenshot_b64}},
                    {"type": "text", "text": prompt},
                ]}],
            )
            return state.detector._parse_response(response.content[0].text)
    except Exception as e:
        print(f"[BJ] Table read error: {e}")
        return None


async def esp_loop():
    """ESP overlay (~12 FPS) + LLM card reading when new cards appear."""
    await asyncio.sleep(0.5)
    last_card_sig = ""
    read_task = None

    while state.is_capturing:
        if state.is_paused:
            await asyncio.sleep(0.3)
            continue

        try:
            card_regions, screen_size, strip_b64 = await asyncio.to_thread(
                state.detector.capture_esp_only
            )

            # Feed state machine
            state._last_esp_regions = card_regions

            # Broadcast ESP boxes
            await broadcast("esp_boxes", {
                "cards": card_regions,
                "screen_w": screen_size[0],
                "screen_h": screen_size[1],
            })

            # Detect new face-up cards
            face_up = [c for c in card_regions if c.get("face") == "up" and not c.get("is_zone")]
            card_sig = f"{len(face_up)}:" + ",".join(f"{c['x']//20}_{c['y']//20}" for c in face_up)

            # New cards detected → read with LLM
            if card_sig != last_card_sig and face_up and strip_b64:
                if last_card_sig.startswith("0:") or last_card_sig == "":
                    state.detector.clear_card_cache()
                last_card_sig = card_sig

                if read_task and not read_task.done():
                    read_task.cancel()

                n_total = len(face_up)

                async def _do_read(s_b64, n_):
                    t0 = time.time()

                    if state.game_mode == "blackjack":
                        # Blackjack: use blackjack-specific prompt
                        player_up = [c for c in face_up if c.get("label") in ("PLAYER", "PLAYER_SPLIT")]
                        dealer_up = [c for c in face_up if c.get("label") == "DEALER"]
                        result = await state.detector.read_blackjack_cards_fast(
                            s_b64, num_player=len(player_up), num_dealer=len(dealer_up))
                    else:
                        result = await state.detector.read_cards_fast(s_b64, n_)

                    if not result:
                        fb = await asyncio.to_thread(state.detector.capture_screen)
                        if fb:
                            result = await state.detector.detect_game_state(fb)

                    ms = int((time.time() - t0) * 1000)
                    if result:
                        if state.game_mode == "blackjack":
                            p_cards = result.get("player_cards", [])
                            d_cards = result.get("dealer_cards", [])
                            all_names = p_cards + d_cards
                            if p_cards or d_cards:
                                await think("READ", f"[{ms}ms] player={p_cards} dealer={d_cards}")
                                await broadcast("scan_status", {"status": "done", "read_ms": ms})
                        else:
                            hole = result.get("hole_cards", [])
                            comm = result.get("community_cards", [])
                            all_names = hole + comm
                            if hole or comm:
                                await think("READ", f"[{ms}ms] hole={hole} community={comm}")
                                await broadcast("scan_status", {"status": "done", "read_ms": ms})

                        await update_balance_from_state(result)

                        # Cache card names for ESP display
                        for card, name in zip(face_up, all_names):
                            if name and name != "XX":
                                ck = (card["x"] // 20, card["y"] // 20)
                                state.detector._card_id_cache[ck] = name
                                card["card_name"] = name

                        await broadcast("esp_boxes", {
                            "cards": card_regions,
                            "screen_w": screen_size[0],
                            "screen_h": screen_size[1],
                        })

                        for r in state._last_esp_regions:
                            if r.get("face") == "up" and not r.get("is_zone"):
                                rk = (r["x"] // 20, r["y"] // 20)
                                cached = state.detector._card_id_cache.get(rk)
                                if cached:
                                    r["card_name"] = cached

                read_task = asyncio.create_task(_do_read(strip_b64, n_total))

            elif not face_up:
                last_card_sig = "0:"

        except Exception as e:
            print(f"[ESP] Error: {e}")

        await asyncio.sleep(state.esp_interval)


def _grab_game_screenshot():
    """Grab raw game region screenshot for card cropping."""
    with mss.mss() as sct:
        monitors = sct.monitors
        idx = state.detector.monitor_index
        if idx >= len(monitors):
            idx = 1
        monitor = monitors[idx]

        if state.detector.crop_region:
            game_mon = {
                "left": monitor["left"] + state.detector.crop_region[0],
                "top": monitor["top"] + state.detector.crop_region[1],
                "width": state.detector.crop_region[2] - state.detector.crop_region[0],
                "height": state.detector.crop_region[3] - state.detector.crop_region[1],
            }
            shot = sct.grab(game_mon)
        else:
            shot = sct.grab(monitor)

        return shot.bgra, (shot.width, shot.height)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    state.ws_clients.append(ws)

    try:
        await ws.send_text(json.dumps({"type": "connection", "payload": {"status": "connected"}}))

        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")
            payload = msg.get("payload", {})

            if msg_type == "set_game_mode":
                new_mode = payload.get("mode", "poker")
                if new_mode in ("poker", "blackjack"):
                    # Stop current loops if running
                    if state.is_capturing:
                        state.is_capturing = False
                        if state.capture_task:
                            state.capture_task.cancel()
                            state.capture_task = None
                        if state.esp_task:
                            state.esp_task.cancel()
                            state.esp_task = None

                    # Switch zones
                    if new_mode == "blackjack":
                        if state._poker_zones is None:
                            state._poker_zones = dict(state.detector.TABLE_ZONES)
                        state.detector.set_table_zones(BLACKJACK_TABLE_ZONES)
                        state.bj_state_machine.reset()
                    else:
                        if state._poker_zones:
                            state.detector.set_table_zones(state._poker_zones)

                    state.game_mode = new_mode
                    await think("SYS", f"Game mode: {new_mode.upper()}")
                    await broadcast("game_mode_changed", {"mode": new_mode})

            elif msg_type == "start_capture":
                if not state.is_capturing:
                    state.is_capturing = True
                    state.is_paused = False
                    state.capture_interval = payload.get("interval", 2000) / 1000
                    state.session_id = await state.db.create_session()
                    if state.game_mode == "blackjack":
                        state.capture_task = asyncio.create_task(blackjack_capture_loop())
                    else:
                        state.capture_task = asyncio.create_task(capture_loop())
                    state.esp_task = asyncio.create_task(esp_loop())
            elif msg_type == "stop_session":
                state.is_capturing = False
                if state.capture_task:
                    state.capture_task.cancel()
                    state.capture_task = None
                if state.esp_task:
                    state.esp_task.cancel()
                    state.esp_task = None
            elif msg_type == "pause_agent":
                state.is_paused = True
            elif msg_type == "resume_agent":
                state.is_paused = False
            elif msg_type == "update_settings":
                if "capture_interval" in payload:
                    state.capture_interval = payload["capture_interval"] / 1000
                if "gto_strictness" in payload:
                    state.decision_engine.gto_strictness = payload["gto_strictness"]
                if "kelly_fraction" in payload:
                    state.decision_engine.kelly_fraction = payload["kelly_fraction"]
                if "mc_iterations" in payload:
                    state.mc_engine.iterations = payload["mc_iterations"]
                if "personality" in payload:
                    state.agent.personality = payload["personality"]
                if "peter_quotes" in payload:
                    state.agent.quotes_enabled = payload["peter_quotes"]

            elif msg_type == "connect_twitch":
                success = await state.twitch.connect()
                if success:
                    asyncio.create_task(state.twitch.listen())
                    async def on_vote(results):
                        await broadcast("twitch_vote", results)
                    state.twitch.on_vote_update = on_vote
                    async def on_chat(msg):
                        await broadcast("twitch_chat", msg)
                    state.twitch.on_chat_message = on_chat
                    await think("SYS", f"Twitch connected to #{state.twitch.channel}")

            elif msg_type == "disconnect_twitch":
                await state.twitch.disconnect()
                await think("SYS", "Twitch disconnected")

            elif msg_type == "get_analytics":
                analytics = await state.replay.get_analytics(state.session_id)
                await ws.send_text(json.dumps({"type": "analytics", "payload": analytics}))

            elif msg_type == "toggle_autoplay":
                state.autoplayer.set_enabled(payload.get("enabled", False))
                status = "ON" if state.autoplayer.enabled else "OFF"
                cal = state.autoplayer.get_calibration_status(state.game_mode)
                missing = [k for k, v in cal.items() if not v]
                if missing and state.autoplayer.enabled:
                    await think("SYS", f"Auto-play ON but buttons not calibrated: {missing}. Use Settings > Calibrate.")
                else:
                    await think("SYS", f"Auto-play {status}")
                await ws.send_text(json.dumps({
                    "type": "calibration_status",
                    "payload": {"calibration": cal, "enabled": state.autoplayer.enabled}
                }))

            elif msg_type == "calibrate_button":
                btn = payload.get("button", "")
                if btn:
                    state.autoplayer.calibrating = btn.lower()
                    await think("SYS", f"Click the '{btn}' button on the casino screen...")
                    coords = await state.autoplayer.wait_for_click(btn)
                    if coords:
                        x, y = coords
                        await think("SYS", f"Calibrated '{btn}' button at ({x}, {y})")
                    else:
                        await think("SYS", f"Calibration timed out for '{btn}'")
                    cal = state.autoplayer.get_calibration_status(state.game_mode)
                    await ws.send_text(json.dumps({
                        "type": "calibration_status",
                        "payload": {"calibration": cal, "enabled": state.autoplayer.enabled, "just_calibrated": btn, "game_mode": state.game_mode}
                    }))

            elif msg_type == "get_calibration":
                cal = state.autoplayer.get_calibration_status(state.game_mode)
                await ws.send_text(json.dumps({
                    "type": "calibration_status",
                    "payload": {"calibration": cal, "enabled": state.autoplayer.enabled, "game_mode": state.game_mode}
                }))

            elif msg_type == "calibrate_zones":
                # Update detector zones from calibration overlay
                zones_data = payload
                for zone_name, coords in zones_data.items():
                    if zone_name in state.detector.TABLE_ZONES:
                        state.detector.TABLE_ZONES[zone_name]["region_x"] = coords["x"]
                        state.detector.TABLE_ZONES[zone_name]["region_y"] = coords["y"]
                        state.detector.TABLE_ZONES[zone_name]["region_w"] = coords["w"]
                        state.detector.TABLE_ZONES[zone_name]["region_h"] = coords["h"]

                # Save to file for persistence
                import json as json_mod
                zones_file = Path(__file__).parent / "data" / "calibrated_zones.json"
                zones_file.parent.mkdir(parents=True, exist_ok=True)
                zones_file.write_text(json_mod.dumps(zones_data, indent=2))
                await think("SYS", f"Zones calibrated and saved: {list(zones_data.keys())}")

            elif msg_type == "toggle_fast_mode":
                state.fast_mode = payload.get("enabled", True)
                status = "ON" if state.fast_mode else "OFF"
                await think("SYS", f"Fast mode {status} — {'pure GTO, 2k MC' if state.fast_mode else 'full reasoning, 10k MC'}")

    except WebSocketDisconnect:
        state.ws_clients.remove(ws)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if ws in state.ws_clients:
            state.ws_clients.remove(ws)


@app.get("/health")
async def health():
    return {"status": "Peter is alive", "capturing": state.is_capturing, "paused": state.is_paused, "hands": state.hand_count}


# ─── Replay & Analytics API ──────────────────────────────────────────────────

@app.get("/api/replay/recent")
async def replay_recent(limit: int = 20):
    return await state.replay.get_recent_hands(limit)

@app.get("/api/replay/hand/{hand_id}")
async def replay_hand(hand_id: int):
    hand = await state.replay.get_hand(hand_id)
    if not hand:
        return {"error": "Hand not found"}
    return hand

@app.get("/api/replay/session/{session_id}")
async def replay_session(session_id: int, limit: int = 100):
    return await state.replay.get_session_hands(session_id, limit)

@app.get("/api/replay/best")
async def replay_best(limit: int = 10):
    return await state.replay.get_best_hands(limit)

@app.get("/api/replay/worst")
async def replay_worst(limit: int = 10):
    return await state.replay.get_worst_hands(limit)

@app.get("/api/analytics")
async def analytics(session_id: int = None):
    return await state.replay.get_analytics(session_id)

@app.get("/api/sessions")
async def sessions():
    return await state.db.get_all_sessions()

@app.get("/api/stats/lifetime")
async def lifetime_stats():
    return await state.db.get_lifetime_stats()

@app.get("/api/achievements")
async def get_achievements():
    return state.achievements.get_all()

@app.get("/api/achievements/unlocked")
async def get_unlocked_achievements():
    return state.achievements.get_unlocked()


# ─── Twitch API ───────────────────────────────────────────────────────────────

@app.post("/api/twitch/connect")
async def twitch_connect():
    success = await state.twitch.connect()
    if success:
        asyncio.create_task(state.twitch.listen())
        # Wire up vote updates to broadcast
        async def on_vote(results):
            await broadcast("twitch_vote", results)
        state.twitch.on_vote_update = on_vote
        async def on_chat(msg):
            await broadcast("twitch_chat", msg)
        state.twitch.on_chat_message = on_chat
        return {"status": "connected", "channel": state.twitch.channel}
    return {"status": "failed"}

@app.post("/api/twitch/disconnect")
async def twitch_disconnect():
    await state.twitch.disconnect()
    return {"status": "disconnected"}

@app.get("/api/twitch/votes")
async def twitch_votes():
    return state.twitch.get_vote_results()


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8765, reload=True, log_level="info")
