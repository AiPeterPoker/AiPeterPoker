import React from 'react';

const S = {
  panel: {
    background: 'var(--hud-bg-panel)', borderRadius: '8px',
    padding: '8px 10px', border: '0.5px solid var(--hud-border-subtle)',
  },
  title: { fontSize: '9px', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px', marginBottom: '6px' },
  handRow: { display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px' },
  card: {
    padding: '4px 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 700,
    fontFamily: 'var(--font-mono)', background: 'var(--hud-bg-panel-hover)',
    border: '1px solid var(--hud-border-subtle)', color: 'var(--text-primary)',
    minWidth: '28px', textAlign: 'center',
  },
  cardRed: { color: '#ef5350' },
  cardFaceDown: { background: '#1a472a', color: 'var(--accent)', borderColor: 'var(--accent)' },
  total: {
    fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)', marginLeft: '8px',
  },
  softLabel: { fontSize: '9px', color: 'var(--accent2)', fontWeight: 600 },
  bjLabel: {
    fontSize: '10px', fontWeight: 800, color: '#FFD740',
    background: 'rgba(255,215,64,0.15)', padding: '2px 8px', borderRadius: '4px',
    marginLeft: '8px',
  },
  bustLabel: {
    fontSize: '10px', fontWeight: 800, color: 'var(--danger)',
    background: 'var(--danger-dim)', padding: '2px 8px', borderRadius: '4px',
    marginLeft: '8px',
  },
  label: { fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '2px' },
  vs: { fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, margin: '2px 0' },
};

function CardPill({ card }) {
  if (card === 'XX') return <span style={{ ...S.card, ...S.cardFaceDown }}>??</span>;
  const suit = card.slice(-1);
  const isRed = suit === 'h' || suit === 'd';
  return <span style={{ ...S.card, ...(isRed ? S.cardRed : {}) }}>{card}</span>;
}

export default function BlackjackHandDisplay({ bjState }) {
  if (!bjState) return null;

  const playerHands = bjState.player_hands || [];
  const dealer = bjState.dealer_hand || { cards: [], total: null };
  const phase = bjState.phase;

  return (
    <div style={S.panel}>
      <div style={S.title}>BLACKJACK HANDS</div>

      {/* Dealer */}
      <div style={S.label}>DEALER</div>
      <div style={S.handRow}>
        {(dealer.cards || []).map((c, i) => <CardPill key={i} card={c} />)}
        {dealer.total != null && (
          <span style={S.total}>{dealer.total}</span>
        )}
        {dealer.is_busted && <span style={S.bustLabel}>BUST</span>}
      </div>

      <div style={S.vs}>vs</div>

      {/* Player hand(s) */}
      {playerHands.map((hand, hi) => (
        <div key={hi}>
          <div style={S.label}>{playerHands.length > 1 ? `HAND ${hi + 1}` : 'YOU'}</div>
          <div style={S.handRow}>
            {(hand.cards || []).map((c, i) => <CardPill key={i} card={c} />)}
            <span style={S.total}>{hand.total}</span>
            {hand.is_soft && <span style={S.softLabel}>SOFT</span>}
            {hand.is_blackjack && <span style={S.bjLabel}>BLACKJACK!</span>}
            {hand.is_busted && <span style={S.bustLabel}>BUST</span>}
          </div>
        </div>
      ))}

      {phase === 'result' && bjState.result && (
        <div style={{
          textAlign: 'center', padding: '4px 0', fontSize: '14px', fontWeight: 800,
          color: bjState.result === 'win' || bjState.result === 'blackjack' ? 'var(--accent)' :
                 bjState.result === 'lose' ? 'var(--danger)' : 'var(--accent2)',
        }}>
          {bjState.result === 'blackjack' ? 'BLACKJACK WINS!' :
           bjState.result === 'win' ? 'WIN' :
           bjState.result === 'lose' ? 'LOSE' : 'PUSH'}
        </div>
      )}
    </div>
  );
}
