import React, { useState, useEffect, useRef } from 'react';

const SUITS = [
  { key: 's', symbol: '\u2660', color: '#c8ccd4' },
  { key: 'h', symbol: '\u2665', color: '#ef4444' },
  { key: 'd', symbol: '\u2666', color: '#3b82f6' },
  { key: 'c', symbol: '\u2663', color: '#c8ccd4' },
];

const RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];

const STATUS_COLORS = {
  scanning: '#FFD740',
  reading: '#4CAF50',
  done: '#4CAF50',
  idle: 'rgba(255,255,255,0.3)',
};

const STATUS_LABELS = {
  scanning: 'SCANNING',
  reading: 'READING',
  done: 'READY',
  idle: 'IDLE',
};

function hiLoValue(rank) {
  const v = { A: -1, K: -1, Q: -1, J: -1, '10': -1, '9': 0, '8': 0, '7': 0, '6': 1, '5': 1, '4': 1, '3': 1, '2': 1 };
  return v[rank] ?? 0;
}

export default function CardTracker({ dealtCards, holeCards = [], communityCards = [], scanStatus = {}, countInfo = null }) {
  const dealtCount = dealtCards ? dealtCards.size : 0;
  const remaining = 52 - dealtCount;
  const [justDetected, setJustDetected] = useState(new Set());
  const prevDealtRef = useRef(new Set());
  const status = scanStatus.status || 'idle';
  const readMs = scanStatus.read_ms;

  useEffect(() => {
    if (!dealtCards) return;
    const prev = prevDealtRef.current;
    const newCards = new Set();
    dealtCards.forEach((c) => { if (!prev.has(c)) newCards.add(c); });
    if (newCards.size > 0) {
      setJustDetected(newCards);
      const timer = setTimeout(() => setJustDetected(new Set()), 1500);
      return () => clearTimeout(timer);
    }
    prevDealtRef.current = new Set(dealtCards);
  }, [dealtCards]);

  const holeSet = new Set(holeCards);
  const communitySet = new Set(communityCards);

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <div style={styles.title}>
          <div style={{
            ...styles.statusDot,
            background: STATUS_COLORS[status],
            boxShadow: status === 'reading' ? `0 0 8px ${STATUS_COLORS.reading}` : 'none',
            animation: status === 'reading' || status === 'scanning' ? 'pulse 1s infinite' : 'none',
          }} />
          Card Tracker
        </div>
        <div style={{
          ...styles.statusBadge,
          background: status === 'reading' ? 'rgba(76,175,80,0.15)' : 'rgba(255,255,255,0.05)',
          color: STATUS_COLORS[status],
          borderColor: STATUS_COLORS[status],
        }}>
          {STATUS_LABELS[status]}
          {readMs && status === 'done' && <span style={styles.readTime}> {readMs}ms</span>}
        </div>
      </div>

      <div style={styles.legend}>
        <span style={styles.legendItem}><span style={{ ...styles.legendDot, background: '#4CAF50' }} />Hole</span>
        <span style={styles.legendItem}><span style={{ ...styles.legendDot, background: '#FFD740' }} />Community</span>
        <span style={styles.legendItem}><span style={{ ...styles.legendDot, background: 'rgba(239,68,68,0.5)' }} />Dealt</span>
      </div>

      {SUITS.map((suit) => (
        <div key={suit.key} style={styles.suitRow}>
          <span style={{ ...styles.suitLabel, color: suit.color }}>{suit.symbol}</span>
          <div style={styles.grid}>
            {RANKS.map((rank) => {
              const cardKey = `${rank}${suit.key}`;
              const isHole = holeSet.has(cardKey);
              const isCommunity = communitySet.has(cardKey);
              const isDealt = dealtCards && dealtCards.has(cardKey);
              const isNew = justDetected.has(cardKey);

              let cellStyle;
              if (isHole) cellStyle = styles.cellHole;
              else if (isCommunity) cellStyle = styles.cellCommunity;
              else if (isDealt) cellStyle = styles.cellDealt;
              else cellStyle = styles.cellDefault;

              return (
                <div key={cardKey} style={{ ...styles.cell, ...cellStyle, ...(isNew ? styles.cellFlash : {}) }}>
                  {rank}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <div style={styles.footer}>
        <span>Dealt: <strong style={{ color: '#ef4444' }}>{dealtCount}</strong>/52</span>
        <span>Deck: <strong style={{ color: 'var(--accent)' }}>{remaining}</strong></span>
        {countInfo && (
          <span>RC: <strong style={{ color: countInfo.true_count >= 2 ? 'var(--accent)' : countInfo.true_count <= -2 ? 'var(--danger)' : 'var(--text-primary)' }}>
            {countInfo.running_count >= 0 ? '+' : ''}{countInfo.running_count}
          </strong> TC: <strong>{countInfo.true_count >= 0 ? '+' : ''}{countInfo.true_count?.toFixed(1)}</strong></span>
        )}
      </div>

      <style>{`
        @keyframes cardFlash {
          0% { transform: scale(1); box-shadow: 0 0 0 rgba(76,175,80,0); }
          30% { transform: scale(1.3); box-shadow: 0 0 12px rgba(76,175,80,0.8); }
          100% { transform: scale(1); box-shadow: 0 0 0 rgba(76,175,80,0); }
        }
      `}</style>
    </div>
  );
}

const styles = {
  panel: {
    background: 'var(--hud-bg-panel)',
    border: '0.5px solid var(--hud-border-subtle)',
    borderRadius: 'var(--radius-md)',
    padding: '10px 12px',
    position: 'relative',
    overflow: 'hidden',
  },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px',
  },
  title: {
    fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.8px',
    display: 'flex', alignItems: 'center', gap: '6px',
  },
  statusDot: { width: 6, height: 6, borderRadius: '50%', transition: 'all 0.3s ease' },
  statusBadge: {
    fontSize: '10px', fontWeight: 700, padding: '2px 8px', borderRadius: '10px',
    border: '0.5px solid', letterSpacing: '0.5px', display: 'flex', alignItems: 'center',
    gap: '3px', fontFamily: 'var(--font-mono)',
  },
  readTime: { fontSize: '9px', opacity: 0.7 },
  legend: {
    display: 'flex', gap: '10px', marginBottom: '6px', fontSize: '10px', color: 'var(--text-muted)',
  },
  legendItem: { display: 'flex', alignItems: 'center', gap: '4px' },
  legendDot: { width: 6, height: 6, borderRadius: '2px' },
  suitRow: { display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2px' },
  suitLabel: { fontSize: '12px', width: '16px', textAlign: 'center', flexShrink: 0 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(13, 1fr)', gap: '2px', flex: 1 },
  cell: {
    aspectRatio: '1', borderRadius: '3px', fontSize: '9px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontWeight: 700, fontFamily: 'var(--font-mono)', transition: 'all 0.3s ease', cursor: 'default',
  },
  cellDefault: {
    background: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.40)',
    border: '0.5px solid rgba(255,255,255,0.04)',
  },
  cellDealt: {
    background: 'rgba(239,68,68,0.12)', color: 'rgba(239,68,68,0.4)',
    border: '0.5px solid rgba(239,68,68,0.15)', textDecoration: 'line-through', opacity: 0.5,
  },
  cellHole: {
    background: 'rgba(76,175,80,0.25)', color: '#4CAF50',
    border: '1px solid rgba(76,175,80,0.6)', fontWeight: 800,
    boxShadow: '0 0 6px rgba(76,175,80,0.3)',
  },
  cellCommunity: {
    background: 'rgba(255,215,64,0.2)', color: '#FFD740',
    border: '1px solid rgba(255,215,64,0.5)', fontWeight: 800,
    boxShadow: '0 0 6px rgba(255,215,64,0.3)',
  },
  cellFlash: { animation: 'cardFlash 0.6s ease-out' },
  footer: {
    marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)',
    display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)',
  },
};
