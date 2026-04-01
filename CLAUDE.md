# AI-IN Peter

AI poker agent para Casino Hold'em en Solcasino.io (Pragmatic Play).
El nombre es un wordplay entre "All-In" y "AI-In".

## Stack
- Frontend: Electron + React (overlay transparente para OBS)
- Backend: Python FastAPI + WebSocket en backend/server.py (puerto 8765)
- Vision: GPT-4o via OpenAI (backend/vision/detector.py)
- Engine: Monte Carlo + GTO (backend/engine/)
- DB: SQLite para hand history (backend/db/session.py)

## Configuración actual (.env)
- VISION_PROVIDER=openai
- VISION_MODEL=gpt-4o
- FAST_MODE=true (sin LLM reasoning, GTO puro, 2k MC iterations)
- Game region: mitad izquierda de pantalla 1920x1080 (GAME_REGION_W=960)
- AUTO_PLAY=false (necesita calibración de botones)

## Problemas conocidos
- GPT-4o a veces lee mal las community cards (el logo "Casino Hold'em" las tapa parcialmente)
- El auto-play necesita calibración manual de posiciones de botones
- La lectura tarda 2-3 segundos, a veces se pasa del timer del juego
- En Casino Hold'em los botones son "2x PLAY" (call) y "FOLD", no hay raise

## Comandos
- npm start = lanza backend + overlay simultáneamente
- python tests/test_engine.py = corre 36 tests
- El overlay se conecta por WebSocket a ws://localhost:8765/ws

## Flujo del agente
Screenshot (mss) → GPT-4o vision → parse cartas → Monte Carlo equity → GTO lookup → decisión → mostrar en overlay
