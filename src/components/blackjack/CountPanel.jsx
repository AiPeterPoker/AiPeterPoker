import React from 'react';

const S = {
  panel: {
    background: 'var(--hud-bg-panel)', borderRadius: '8px',
    padding: '8px 10px', border: '0.5px solid var(--hud-border-subtle)',
  },
  title: { fontSize: '9px', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px', marginBottom: '6px' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', marginBottom: '8px' },
  stat: { textAlign: 'center' },
  statVal: { fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)' },
  statLbl: { fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.5px', fontWeight: 600 },
  actionBox: {
    textAlign: 'center', padding: '6px 0', borderRadius: '6px',
    fontSize: '16px', fontWeight: 900, letterSpacing: '1px',
  },
  deviationTag: {
    fontSize: '9px', fontWeight: 700, color: '#FFD740',
    background: 'rgba(255,215,64,0.15)', padding: '2px 8px', borderRadius: '4px',
    display: 'inline-block', marginTop: '4px',
  },
  betRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginTop: '6px', padding: '4px 8px', borderRadius: '4px',
    background: 'var(--hud-bg-panel-hover)',
  },
  betLbl: { fontSize: '9px', color: 'var(--text-muted)', fontWeight: 600 },
  betVal: { fontSize: '12px', fontWeight: 700, fontFamily: 'var(--font-mono)' },
  reason: { fontSize: '9px', color: 'var(--text-secondary)', marginTop: '4px', textAlign: 'center' },
  insuranceTag: {
    fontSize: '9px', fontWeight: 700, color: 'var(--accent)',
    background: 'var(--accent-dim)', padding: '2px 8px', borderRadius: '4px',
    display: 'inline-block', marginTop: '4px', marginLeft: '4px',
  },
};

const ACTION_COLORS = {
  HIT: { bg: 'rgba(255,215,64,0.15)', color: '#FFD740' },
  STAND: { bg: 'rgba(76,175,80,0.15)', color: '#4CAF50' },
  DOUBLE: { bg: 'rgba(255,152,0,0.15)', color: '#FF9800' },
  SPLIT: { bg: 'rgba(33,150,243,0.15)', color: '#2196F3' },
  DOUBLE_STAND: { bg: 'rgba(255,152,0,0.15)', color: '#FF9800' },
};

export default function CountPanel({ bjState }) {
  if (!bjState) return null;

  const count = bjState.count || {};
  const action = bjState.recommended_action;
  const bet = bjState.bet_recommendation || {};
  const tcColor = (count.true_count || 0) >= 2 ? 'var(--accent)' :
                  (count.true_count || 0) <= -2 ? 'var(--danger)' : 'var(--text-primary)';
  const edgeColor = (count.edge_pct || 0) > 0 ? 'var(--accent)' : 'var(--danger)';
  const ac = ACTION_COLORS[action] || { bg: 'var(--hud-bg-panel-hover)', color: 'var(--text-primary)' };

  return (
    <div style={S.panel}>
      <div style={S.title}>HI-LO COUNT</div>

      <div style={S.grid}>
        <div style={S.stat}>
          <div style={{ ...S.statVal, color: 'var(--text-primary)' }}>{count.running_count || 0}</div>
          <div style={S.statLbl}>RUNNING</div>
        </div>
        <div style={S.stat}>
          <div style={{ ...S.statVal, color: tcColor }}>
            {(count.true_count || 0) >= 0 ? '+' : ''}{(count.true_count || 0).toFixed(1)}
          </div>
          <div style={S.statLbl}>TRUE COUNT</div>
        </div>
        <div style={S.stat}>
          <div style={{ ...S.statVal, color: 'var(--text-secondary)' }}>{count.decks_remaining || '?'}</div>
          <div style={S.statLbl}>DECKS LEFT</div>
        </div>
      </div>

      {/* Recommended Action */}
      {action && (
        <>
          <div style={{ ...S.actionBox, background: ac.bg, color: ac.color }}>
            {action}
          </div>
          {bjState.is_deviation && (
            <div style={{ textAlign: 'center' }}>
              <span style={S.deviationTag}>DEVIATION</span>
            </div>
          )}
          {bjState.insurance && (
            <div style={{ textAlign: 'center' }}>
              <span style={S.insuranceTag}>TAKE INSURANCE (TC {'\u2265'} +3)</span>
            </div>
          )}
          {bjState.reason && <div style={S.reason}>{bjState.reason}</div>}
        </>
      )}

      {/* Bet Recommendation */}
      <div style={S.betRow}>
        <span style={S.betLbl}>BET</span>
        <span style={{ ...S.betVal, color: edgeColor }}>
          {bet.bet_units || 1}x ({bet.bet_amount ? `$${bet.bet_amount.toFixed(2)}` : '-'})
        </span>
      </div>
      <div style={S.betRow}>
        <span style={S.betLbl}>EDGE</span>
        <span style={{ ...S.betVal, color: edgeColor }}>
          {(count.edge_pct || 0) >= 0 ? '+' : ''}{(count.edge_pct || 0).toFixed(1)}%
        </span>
        <span style={{ ...S.betLbl, color: count.favorable ? 'var(--accent)' : 'var(--danger)' }}>
          {count.favorable ? 'FAVORABLE' : 'HOUSE EDGE'}
        </span>
      </div>
    </div>
  );
}
