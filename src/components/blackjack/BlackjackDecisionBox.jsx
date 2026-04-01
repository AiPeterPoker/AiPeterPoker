import React from 'react';

const S = {
  box: {
    textAlign: 'center', padding: '10px', borderRadius: '8px',
    border: '0.5px solid var(--hud-border-subtle)',
    background: 'var(--hud-bg-panel)',
  },
  action: {
    fontSize: '22px', fontWeight: 900, letterSpacing: '2px',
    marginBottom: '4px',
  },
  confidence: {
    fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600,
  },
  reason: {
    fontSize: '10px', color: 'var(--text-secondary)', marginTop: '4px',
    fontStyle: 'italic',
  },
  deviationBadge: {
    display: 'inline-block', marginTop: '4px', padding: '2px 10px',
    borderRadius: '4px', fontSize: '9px', fontWeight: 700,
    color: '#FFD740', background: 'rgba(255,215,64,0.15)',
  },
};

const ACTION_STYLES = {
  HIT:    { color: '#FFD740', borderColor: 'rgba(255,215,64,0.3)' },
  STAND:  { color: '#4CAF50', borderColor: 'rgba(76,175,80,0.3)' },
  DOUBLE: { color: '#FF9800', borderColor: 'rgba(255,152,0,0.3)' },
  SPLIT:  { color: '#2196F3', borderColor: 'rgba(33,150,243,0.3)' },
  DOUBLE_STAND: { color: '#FF9800', borderColor: 'rgba(255,152,0,0.3)' },
};

export default function BlackjackDecisionBox({ bjState }) {
  const action = bjState?.recommended_action;
  if (!action) return null;

  const style = ACTION_STYLES[action] || { color: 'var(--text-primary)', borderColor: 'var(--hud-border-subtle)' };

  return (
    <div style={{ ...S.box, borderColor: style.borderColor }}>
      <div style={{ ...S.action, color: style.color }}>{action}</div>
      <div style={S.confidence}>
        {bjState.is_deviation ? 'Count-adjusted' : 'Basic strategy'}
      </div>
      {bjState.reason && <div style={S.reason}>{bjState.reason}</div>}
      {bjState.is_deviation && <span style={S.deviationBadge}>ILLUSTRIOUS 18</span>}
    </div>
  );
}
