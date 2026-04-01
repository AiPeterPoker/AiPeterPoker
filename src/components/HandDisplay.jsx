import React from 'react';

const SUIT_SYMBOLS = { h: '\u2665', d: '\u2666', s: '\u2660', c: '\u2663' };
const SUIT_COLORS = { h: '#ef4444', d: '#42A5F5', s: '#c8ccd4', c: '#c8ccd4' };

function Card({ card, size = 'normal' }) {
  const w = size === 'small' ? 36 : 44;
  const h = size === 'small' ? 50 : 60;
  if (!card) return (
    <div style={{ width: w, height: h, borderRadius: 6, background: 'linear-gradient(135deg,#1a2332,#2a3548)', border: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: 'rgba(255,255,255,0.15)', fontWeight: 700 }}>?</div>
  );
  const suit = card.slice(-1);
  const rank = card.slice(0, -1).toUpperCase();
  const color = SUIT_COLORS[suit] || '#c8ccd4';
  const fs = size === 'small' ? 13 : 15;
  return (
    <div style={{ width: w, height: h, borderRadius: 6, background: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: fs, color, border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 2px 8px rgba(0,0,0,0.3)', lineHeight: 1 }}>
      <span>{rank}</span>
      <span style={{ fontSize: fs - 2, marginTop: -1 }}>{SUIT_SYMBOLS[suit] || suit}</span>
    </div>
  );
}

const S = {
  panel: { background: 'var(--hud-bg-panel)', border: '0.5px solid var(--hud-border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' },
  title: { fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' },
  dot: { width: 5, height: 5, borderRadius: '50%', background: 'var(--accent)' },
  lbl: { fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 },
  row: { display: 'flex', gap: '4px' },
  strBar: { display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' },
  track: { flex: 1, height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' },
  fill: { height: '100%', borderRadius: 4, background: 'linear-gradient(90deg, var(--danger), var(--accent2), var(--accent))', transition: 'width 0.6s' },
};

export default function HandDisplay({ gameState }) {
  const { hole_cards, community_cards, hand_strength, hand_name } = gameState;
  const slots = [0,1,2,3,4].map(i => community_cards?.[i] || null);
  const pct = hand_strength ? Math.round(hand_strength * 100) : 0;

  return (
    <div style={S.panel}>
      <div style={S.title}><div style={S.dot} />Your Hand</div>
      <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
        <div>
          <div style={S.lbl}>Hole</div>
          <div style={S.row}>
            {hole_cards?.length > 0 ? hole_cards.map((c,i) => <Card key={i} card={c} />) : <><Card card={null} /><Card card={null} /></>}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={S.lbl}>Community</div>
          <div style={S.row}>{slots.map((c,i) => <Card key={i} card={c} size="small" />)}</div>
        </div>
      </div>
      <div style={S.strBar}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>STR</span>
        <div style={S.track}><div style={{ ...S.fill, width: `${pct}%` }} /></div>
        <span style={{ fontSize: 14, fontWeight: 700, color: pct > 70 ? 'var(--accent)' : pct > 40 ? 'var(--accent2)' : 'var(--danger)', fontFamily: 'var(--font-mono)', minWidth: 35, textAlign: 'right' }}>{pct}%</span>
      </div>
      {hand_name && <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)', marginTop: '4px' }}>{hand_name}</div>}
    </div>
  );
}
