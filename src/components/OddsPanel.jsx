import React from 'react';

const S = {
  panel: { background: 'var(--hud-bg-panel)', border: '0.5px solid var(--hud-border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' },
  title: { fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' },
  dot: { width: 5, height: 5, borderRadius: '50%', background: 'var(--accent2)' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2px 0', fontSize: '13px' },
  label: { color: 'var(--text-secondary)' },
  val: { fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '13px' },
  bar: { height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)', margin: '3px 0 6px', overflow: 'hidden', position: 'relative' },
  gtoRow: { display: 'flex', gap: '4px', marginTop: '6px' },
  gtoO: { flex: 1, padding: '6px 4px', borderRadius: '6px', textAlign: 'center', border: '0.5px solid rgba(255,255,255,0.05)' },
  gtoSel: { borderColor: 'rgba(76,175,80,0.4)', background: 'rgba(76,175,80,0.10)' },
  gtoSelFold: { borderColor: 'rgba(255,82,82,0.4)', background: 'rgba(255,82,82,0.10)' },
  gtoLbl: { fontSize: '10px', color: 'var(--text-muted)', marginTop: '6px', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 },
  drawTag: {
    display: 'inline-block', fontSize: '10px', fontWeight: 700, padding: '2px 8px',
    borderRadius: '4px', background: 'var(--info-dim)', color: 'var(--info)',
    border: '0.5px solid rgba(66,165,245,0.3)', marginTop: '4px',
  },
};

export default function OddsPanel({ gameState }) {
  const {
    win_probability = 0, expected_value = 0, outs = 0, outs_percentage = 0,
    gto_recommendation, dealer_qualifies_pct = 55,
  } = gameState;

  // Draw info from equity
  const drawType = gameState.draw_type;
  const drawOuts = gameState.draw_outs || 0;

  const gto = gto_recommendation || { fold: 50, call: 50 };
  const best = Object.entries(gto).sort((a, b) => b[1] - a[1])[0][0];
  const wc = win_probability >= 65 ? 'var(--accent)' : win_probability >= 40 ? 'var(--accent2)' : 'var(--danger)';
  const dnqColor = dealer_qualifies_pct <= 50 ? 'var(--accent)' : dealer_qualifies_pct >= 70 ? 'var(--danger)' : 'var(--accent2)';

  return (
    <div style={S.panel}>
      <div style={S.title}><div style={S.dot} />Odds Engine</div>

      {/* Win % with bar */}
      <div style={S.row}>
        <span style={S.label}>Win %</span>
        <span style={{ ...S.val, color: wc, fontSize: '16px' }}>{win_probability.toFixed(1)}%</span>
      </div>
      <div style={S.bar}>
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${win_probability}%`, borderRadius: 3, background: wc, transition: 'width 0.5s' }} />
      </div>

      {/* Key stats */}
      <div style={S.row}>
        <span style={S.label}>EV</span>
        <span style={{ ...S.val, color: expected_value >= 0 ? 'var(--accent)' : 'var(--danger)' }}>
          {expected_value >= 0 ? '+' : ''}${expected_value.toFixed(2)}
        </span>
      </div>
      <div style={S.row}>
        <span style={S.label}>Dealer qualifies</span>
        <span style={{ ...S.val, color: dnqColor }}>~{dealer_qualifies_pct}%</span>
      </div>
      <div style={S.row}>
        <span style={S.label}>Outs</span>
        <span style={{ ...S.val, color: 'var(--accent2)' }}>{outs} ({outs_percentage.toFixed(0)}%)</span>
      </div>

      {/* Draw indicator */}
      {drawType && (
        <div style={S.drawTag}>
          {drawType.toUpperCase()} ({drawOuts} outs)
        </div>
      )}

      {/* GTO Decision: FOLD vs 2x PLAY */}
      <div style={S.gtoLbl}>Optimal Decision</div>
      <div style={S.gtoRow}>
        {['fold', 'call'].map(a => {
          const pct = gto[a] || 0;
          const sel = a === best;
          const label = a === 'call' ? '2x PLAY' : 'FOLD';
          const selStyle = a === 'fold' ? S.gtoSelFold : S.gtoSel;
          return (
            <div key={a} style={{ ...S.gtoO, ...(sel ? selStyle : {}) }}>
              <div style={{
                fontSize: 22, fontWeight: 800, fontFamily: 'var(--font-mono)',
                color: sel ? (a === 'fold' ? 'var(--danger)' : 'var(--accent)') : 'var(--text-muted)',
              }}>{pct}%</div>
              <div style={{
                fontSize: 12, fontWeight: 700, marginTop: 2,
                color: sel ? 'var(--text-primary)' : 'var(--text-muted)',
              }}>{label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
