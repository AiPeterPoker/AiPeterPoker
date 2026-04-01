import React, { useState, useMemo, useCallback } from 'react';
import HandDisplay from './HandDisplay';
import OddsPanel from './OddsPanel';
import CardTracker from './CardTracker';
import ConsoleLog from './ConsoleLog';
import SessionStats from './SessionStats';
import TwitchVote from './TwitchVote';
import AnalyticsDashboard from './AnalyticsDashboard';
import HandReplayViewer from './HandReplayViewer';
import SettingsPanel from './SettingsPanel';
import AchievementToast from './AchievementToast';
import BlackjackHandDisplay from './blackjack/BlackjackHandDisplay';
import CountPanel from './blackjack/CountPanel';
import BlackjackDecisionBox from './blackjack/BlackjackDecisionBox';

const S = {
  root: {
    background: 'var(--hud-bg)',
    border: '1px solid var(--hud-border)',
    borderRadius: '12px',
    padding: '12px 14px',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    position: 'relative',
  },
  scanline: {
    position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
    background: 'linear-gradient(90deg, transparent, #4CAF50, #FFD740, #4CAF50, transparent)',
    opacity: 0.5, borderRadius: '12px 12px 0 0',
  },
  hdr: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    marginBottom: '6px', paddingBottom: '8px',
    borderBottom: '0.5px solid var(--hud-border-subtle)', flexShrink: 0,
    WebkitAppRegion: 'drag', cursor: 'grab',
  },
  logo: { display: 'flex', alignItems: 'center', gap: '8px' },
  logoIcon: {
    width: '28px', height: '28px', borderRadius: '6px',
    background: '#1a472a', border: '2px solid var(--accent)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: '13px', fontWeight: 900, color: '#fff',
  },
  logoText: { fontSize: '15px', fontWeight: 800, color: '#fff', letterSpacing: '-0.5px' },
  logoAccent: { color: 'var(--accent)' },
  logoSub: { fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '1.5px', fontWeight: 600 },
  pill: {
    display: 'flex', alignItems: 'center', gap: '5px',
    padding: '3px 10px', borderRadius: '20px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px',
    WebkitAppRegion: 'no-drag',
  },
  pillLive: { background: 'var(--accent-dim)', color: 'var(--accent)' },
  pillOff: { background: 'var(--danger-dim)', color: 'var(--danger)' },
  dot: { width: '6px', height: '6px', borderRadius: '50%', animation: 'pulse 2s infinite' },

  // Balance bar — the hero section
  balanceBar: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '8px 12px', marginBottom: '6px',
    background: 'var(--hud-bg-panel)', borderRadius: '8px',
    border: '0.5px solid var(--hud-border-subtle)', flexShrink: 0,
  },
  balLbl: { fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.5px', textTransform: 'uppercase' },
  balVal: { fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' },
  balStat: { textAlign: 'center' },
  balStatVal: { fontSize: '14px', fontWeight: 700, fontFamily: 'var(--font-mono)' },
  balStatLbl: { fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.5px' },

  quote: {
    fontSize: '11px', color: 'var(--beer)', fontStyle: 'italic',
    padding: '5px 10px', marginBottom: '6px',
    borderLeft: '2px solid var(--beer)', borderRadius: '0 4px 4px 0',
    background: 'rgba(212,160,23,0.05)', flexShrink: 0, cursor: 'pointer', WebkitAppRegion: 'no-drag',
  },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '6px', flexShrink: 0 },
  consoleWrap: { flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' },
  bar: { display: 'flex', gap: '4px', marginTop: '6px', flexShrink: 0, flexWrap: 'wrap' },
  btn: {
    padding: '5px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 600,
    border: 'none', cursor: 'pointer', fontFamily: 'var(--font-display)', WebkitAppRegion: 'no-drag',
  },
  btnGo: { background: 'var(--accent)', color: '#0a0c10' },
  btnSec: { background: 'var(--hud-bg-panel-hover)', color: 'var(--text-secondary)', border: '0.5px solid var(--hud-border-subtle)' },
  btnStop: { background: 'var(--danger-dim)', color: 'var(--danger)', border: '0.5px solid rgba(255,82,82,0.2)', marginLeft: 'auto' },
};

export default function Overlay({
  gameState, session, consoleLines, dealtCards, connected, agentPaused,
  currentQuote, onPauseToggle, onStopSession, onStartCapture, onNextQuote,
  twitchVoteData, twitchChatMessages, twitchVotingOpen, analytics,
  achievements, scanStatus, gameMode = 'poker', bjState = null, onGameModeSwitch,
}) {
  const [showSettings, setShowSettings] = useState(false);
  const [showReplay, setShowReplay] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const stableSettings = useMemo(() => ({}), []);
  const stableOnSettingsChange = useCallback((s) => {}, []);
  const stableOnCloseSettings = useCallback(() => setShowSettings(false), []);
  const isLive = connected && !agentPaused;
  const statusText = !connected ? 'OFFLINE' : agentPaused ? 'PAUSED' : `HAND #${session.total_hands}`;

  const pnl = session.session_pnl;
  const pnlColor = pnl >= 0 ? 'var(--accent)' : 'var(--danger)';
  const winRate = session.win_rate;
  const wrColor = winRate >= 50 ? 'var(--accent)' : winRate >= 35 ? 'var(--accent2)' : 'var(--danger)';

  return (
    <div style={S.root}>
      <div style={S.scanline} />

      {/* Header */}
      <div style={S.hdr}>
        <div style={S.logo}>
          <div style={S.logoIcon}>P</div>
          <div>
            <div style={S.logoText}><span style={S.logoAccent}>AI-IN</span> Peter</div>
            <div style={S.logoSub}>{gameMode === 'blackjack' ? 'INFINITE BLACKJACK' : "CASINO HOLD'EM"}</div>
          </div>
        </div>
        <div style={{ ...S.pill, ...(isLive ? S.pillLive : S.pillOff) }}>
          <div style={{ ...S.dot, background: isLive ? 'var(--accent)' : 'var(--danger)' }} />
          {statusText}
        </div>
      </div>

      {/* Balance Bar */}
      <div style={S.balanceBar}>
        <div>
          <div style={S.balLbl}>Balance</div>
          <div style={S.balVal}>${session.bankroll.toFixed(2)}</div>
        </div>
        <div style={S.balStat}>
          <div style={{ ...S.balStatVal, color: pnlColor }}>{pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}</div>
          <div style={S.balStatLbl}>SESSION P&L</div>
        </div>
        <div style={S.balStat}>
          <div style={{ ...S.balStatVal, color: wrColor }}>{winRate.toFixed(0)}%</div>
          <div style={S.balStatLbl}>WIN RATE</div>
        </div>
        <div style={S.balStat}>
          <div style={S.balStatVal}>{session.total_hands}</div>
          <div style={S.balStatLbl}>HANDS</div>
        </div>
      </div>

      {/* Peter Quote */}
      <div style={S.quote} onClick={onNextQuote}>"{currentQuote}"</div>

      {/* Main Grid */}
      {gameMode === 'blackjack' ? (
        <div style={S.grid}>
          <BlackjackHandDisplay bjState={bjState} />
          <CountPanel bjState={bjState} />
          <CardTracker
            dealtCards={dealtCards}
            holeCards={bjState?.player_hands?.[0]?.cards || []}
            communityCards={[]}
            scanStatus={scanStatus}
            countInfo={bjState?.count}
          />
          <SessionStats session={session} gameState={gameState} />
        </div>
      ) : (
        <div style={S.grid}>
          <HandDisplay gameState={gameState} />
          <OddsPanel gameState={gameState} />
          <CardTracker
            dealtCards={dealtCards}
            holeCards={gameState.hole_cards || []}
            communityCards={gameState.community_cards || []}
            scanStatus={scanStatus}
          />
          <SessionStats session={session} gameState={gameState} />
        </div>
      )}

      {/* Twitch */}
      <TwitchVote voteData={twitchVoteData} chatMessages={twitchChatMessages} isOpen={twitchVotingOpen} />
      <AchievementToast achievements={achievements} />

      {/* Panels */}
      {showAnalytics && <AnalyticsDashboard analytics={analytics} session={session} />}
      {showReplay && <HandReplayViewer onClose={() => setShowReplay(false)} />}
      {showSettings && <SettingsPanel key="settings-panel" settings={stableSettings} onSettingsChange={stableOnSettingsChange} onClose={stableOnCloseSettings} gameMode={gameMode} />}

      {/* Console */}
      <div style={S.consoleWrap}>
        <ConsoleLog lines={consoleLines} />
      </div>

      {/* Buttons */}
      <div style={S.bar}>
        <button
          style={{ ...S.btn, ...S.btnSec, fontSize: '10px', padding: '5px 8px' }}
          onClick={() => onGameModeSwitch?.(gameMode === 'poker' ? 'blackjack' : 'poker')}
        >
          {gameMode === 'poker' ? 'BJ' : 'PKR'}
        </button>
        <button style={{ ...S.btn, ...S.btnGo }} onClick={onStartCapture}>Start</button>
        <button style={{ ...S.btn, ...S.btnSec }} onClick={onPauseToggle}>{agentPaused ? 'Resume' : 'Pause'}</button>
        <button style={{ ...S.btn, ...S.btnSec }} onClick={() => setShowAnalytics(!showAnalytics)}>Stats</button>
        <button style={{ ...S.btn, ...S.btnSec }} onClick={() => setShowReplay(!showReplay)}>Replay</button>
        <button style={{ ...S.btn, ...S.btnSec }} onClick={() => setShowSettings(!showSettings)}>Settings</button>
        <button style={{ ...S.btn, ...S.btnStop }} onClick={onStopSession}>Stop</button>
      </div>
    </div>
  );
}
