import React from 'react';

const S = {
  box: {
    background: 'rgba(76,175,80,0.06)', border: '0.5px solid rgba(76,175,80,0.2)',
    borderRadius: 'var(--radius-md)', padding: '10px 12px', marginBottom: '8px',
    flexShrink: 0, animation: 'slideUp 0.3s ease',
  },
  label: { fontSize: '9px', color: 'var(--accent)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' },
  row: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  action: { fontSize: '18px', fontWeight: 800, color: '#fff' },
  reason: { fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px', fontStyle: 'italic' },
  ev: { textAlign: 'right', flexShrink: 0, marginLeft: '12px' },
  evVal: { fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)' },
  evSub: { fontSize: '9px', color: 'var(--text-muted)' },
  conf: { display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px' },
  confBar: { flex: 1, height: 3, borderRadius: 2, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' },
  confFill: { height: '100%', borderRadius: 2, background: 'var(--accent)', transition: 'width 0.5s' },
};

const ACTION_QUIPS = {
  raise: '"The math is bulletproof. I\'m going AI-IN!"',
  call: '"Playing it cool... but I\'m watching you, dealer."',
  fold: '"Even Peter knows when to walk away. Temporarily."',
};

export default function DecisionBox({ decision }) {
  if (!decision) return null;
  const { action = 'call', amount = 0, confidence = 0, reasoning = '', expected_value = 0 } = decision;
  const actionColor = action === 'fold' ? 'var(--danger)' : action === 'raise' ? 'var(--accent)' : 'var(--accent2)';
  const evColor = expected_value >= 0 ? 'var(--accent)' : 'var(--danger)';
  const quip = ACTION_QUIPS[action.toLowerCase()] || ACTION_QUIPS.call;

  return (
    <div style={S.box}>
      <div style={S.label}>Peter's decision</div>
      <div style={S.row}>
        <div>
          <div style={{ ...S.action, color: actionColor }}>
            {action.toUpperCase()}{amount > 0 ? ` — $${amount.toFixed(2)}` : ''}
          </div>
          <div style={S.reason}>{quip}</div>
        </div>
        <div style={S.ev}>
          <div style={{ ...S.evVal, color: evColor }}>{expected_value >= 0 ? '+' : ''}EV</div>
          <div style={S.evSub}>${Math.abs(expected_value).toFixed(2)}</div>
        </div>
      </div>
      <div style={S.conf}>
        <span style={{ fontSize: 8, color: 'var(--text-muted)' }}>CONF</span>
        <div style={S.confBar}><div style={{ ...S.confFill, width: `${confidence}%` }} /></div>
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>{confidence}%</span>
      </div>
    </div>
  );
}
