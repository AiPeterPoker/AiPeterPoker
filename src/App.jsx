import React, { useState, useEffect, useCallback } from 'react';
import Overlay from './components/Overlay';
import wsManager from './utils/websocket';

const PETER_QUOTES = [
  "Holy crap, Lois! The math says we're golden. I'm goin' AI-IN.",
  "You know what grinds my gears? Folding pocket aces. Never happening.",
  "This is like that time I counted cards at Foxwoods... but legal.",
  "Shut up, Meg. Daddy's calculating pot odds.",
  "Remember when I said I was good at poker? I was right. Statistically.",
  "The dealer doesn't know I've got 10,000 Monte Carlo sims backing me up.",
  "I haven't been this confident since I fought that chicken.",
  "Roadhouse. *raises 2x*",
  "My EV is positive and my beer is cold. Life is good.",
  "Freakin' sweet! The numbers don't lie and neither does Peter Griffin.",
  "I'm not just gambling. I'm gambling with MATH. Big difference.",
  "The Kelly Criterion says I should bet this much. Kelly's a smart lady.",
  "GTO stands for 'Griffin Takes Over'. Look it up.",
  "If this hand doesn't work out, I'll blame Quagmire.",
];

const DEFAULT_STATE = {
  status: 'waiting', hand_number: 0, phase: 'idle',
  hole_cards: [], community_cards: [], pot_size: 0, current_bet: 0, balance: 0,
  hand_strength: null, hand_name: '', win_probability: 0, pot_odds: null,
  expected_value: 0, outs: 0, outs_percentage: 0,
  gto_recommendation: { fold: 0, call: 0, raise: 0 },
  decision: null, dealer_qualifies_pct: 0, remaining_deck: 52, favorable_outs: 0,
};

const DEFAULT_SESSION = {
  total_hands: 0, win_rate: 0, session_pnl: 0, ev_per_hand: 0, bankroll: 0, streak: 0,
};

export default function App() {
  const [gameState, setGameState] = useState(DEFAULT_STATE);
  const [session, setSession] = useState(DEFAULT_SESSION);
  const [consoleLines, setConsoleLines] = useState([]);
  const [dealtCards, setDealtCards] = useState(new Set());
  const [connected, setConnected] = useState(false);
  const [agentPaused, setAgentPaused] = useState(false);
  const [currentQuote, setCurrentQuote] = useState(PETER_QUOTES[0]);
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [twitchVoteData, setTwitchVoteData] = useState(null);
  const [twitchChatMessages, setTwitchChatMessages] = useState([]);
  const [twitchVotingOpen, setTwitchVotingOpen] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [scanStatus, setScanStatus] = useState({ status: 'idle' });
  const [gameMode, setGameMode] = useState('poker');
  const [bjState, setBjState] = useState(null);

  useEffect(() => {
    wsManager.connect();
    const unsubs = [
      wsManager.on('connection', ({ status }) => {
        setConnected(status === 'connected');
        addConsoleLine('SYS', status === 'connected' ? "Peter is online. Let's do this." : 'Peter disconnected.');
      }),
      wsManager.on('game_state', (state) => {
        setGameState((prev) => ({ ...prev, ...state }));
        const cards = new Set();
        if (state.hole_cards) state.hole_cards.forEach((c) => cards.add(c));
        if (state.community_cards) state.community_cards.forEach((c) => cards.add(c));
        setDealtCards(cards);
      }),
      wsManager.on('decision', (data) => {
        setGameState((prev) => ({ ...prev, decision: data }));
        addConsoleLine('AI-IN', `Decision: ${data.action.toUpperCase()} — $${data.amount?.toFixed(2) || '0'} | Confidence: ${data.confidence}%`);
        nextQuote();
      }),
      wsManager.on('thinking', (data) => addConsoleLine(data.tag || 'THINK', data.message)),
      wsManager.on('session_update', (data) => {
        setSession((prev) => ({ ...prev, ...data }));
        if (data.total_hands && data.total_hands % 10 === 0) wsManager.send('get_analytics');
      }),
      wsManager.on('analytics', (data) => setAnalytics(data)),
      wsManager.on('twitch_vote', (data) => { setTwitchVoteData(data); setTwitchVotingOpen(!!data.is_open); }),
      wsManager.on('twitch_chat', (msg) => setTwitchChatMessages((prev) => [...prev.slice(-49), msg])),
      wsManager.on('voice_audio', (data) => {
        if (data.audio) {
          try { const a = new Audio(`data:audio/mp3;base64,${data.audio}`); a.volume = 0.8; a.play().catch(() => {}); } catch (e) {}
        }
      }),
      wsManager.on('balance_update', (data) => {
        setSession((prev) => ({
          ...prev,
          bankroll: data.balance,
          session_pnl: data.pnl,
          starting_balance: data.starting_balance,
        }));
      }),
      wsManager.on('scan_status', (data) => setScanStatus(data)),
      wsManager.on('achievement', (data) => {
        setAchievements((prev) => [...prev, { ...data, id: Date.now() }]);
        addConsoleLine('PETER', `Achievement: ${data.name}! "${data.quip}"`);
      }),
      wsManager.on('blackjack_state', (data) => setBjState(data)),
      wsManager.on('game_mode_changed', (data) => {
        setGameMode(data.mode);
        addConsoleLine('SYS', `Game mode: ${data.mode.toUpperCase()}`);
      }),
      wsManager.on('calibration_status', (data) => {
        if (data.enabled) addConsoleLine('PETER', 'Auto-play ENABLED. Peter takes the wheel.');
        if (data.just_calibrated) addConsoleLine('SYS', `Calibrated: ${data.just_calibrated}`);
      }),
      wsManager.on('error', (data) => addConsoleLine('ERROR', data.message || 'Something broke.')),
    ];
    return () => { unsubs.forEach((u) => u()); wsManager.disconnect(); };
  }, []);

  const addConsoleLine = useCallback((tag, message) => {
    const time = new Date().toTimeString().slice(0, 8);
    setConsoleLines((prev) => [...prev, { time, tag, message, id: Date.now() + Math.random() }].slice(-200));
  }, []);

  const nextQuote = useCallback(() => {
    setQuoteIndex((prev) => { const n = (prev + 1) % PETER_QUOTES.length; setCurrentQuote(PETER_QUOTES[n]); return n; });
  }, []);

  return (
    <Overlay
      gameState={gameState} session={session} consoleLines={consoleLines}
      dealtCards={dealtCards} connected={connected} agentPaused={agentPaused}
      currentQuote={currentQuote}
      onPauseToggle={useCallback(() => {
        const np = !agentPaused; setAgentPaused(np);
        wsManager.send(np ? 'pause_agent' : 'resume_agent');
        addConsoleLine('PETER', np ? '"Beer break."' : '"I\'m back!"');
      }, [agentPaused, addConsoleLine])}
      onStopSession={useCallback(() => { wsManager.send('stop_session'); addConsoleLine('PETER', '"That\'s a wrap."'); }, [addConsoleLine])}
      onStartCapture={useCallback(() => { wsManager.send('start_capture', { interval: 2000 }); addConsoleLine('SYS', 'Capture started'); }, [addConsoleLine])}
      onNextQuote={nextQuote}
      twitchVoteData={twitchVoteData} twitchChatMessages={twitchChatMessages}
      twitchVotingOpen={twitchVotingOpen} analytics={analytics} achievements={achievements}
      scanStatus={scanStatus}
      gameMode={gameMode}
      bjState={bjState}
      onGameModeSwitch={useCallback((mode) => {
        wsManager.send('set_game_mode', { mode });
        addConsoleLine('SYS', `Switching to ${mode.toUpperCase()}...`);
      }, [addConsoleLine])}
    />
  );
}
