import React from 'react';

const S = {
  panel: { background: 'var(--hud-bg-panel)', border: '0.5px solid var(--hud-border-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px' },
  title: { fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' },
  dot: { width: 5, height: 5, borderRadius: '50%', background: 'var(--peter-orange)', display: 'inline-block' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '3px 0', fontSize: '13px' },
  label: { color: 'var(--text-secondary)' },
  val: { fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: '13px' },
  insight: { marginTop: '8px', padding: '6px 8px', background: 'var(--beer-dim)', borderRadius: '6px', border: '0.5px solid rgba(212,160,23,0.12)' },
  insightT: { fontSize: '10px', color: 'var(--beer)', fontWeight: 700, marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.3px' },
  insightM: { fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, fontStyle: 'italic' },
};

const GUT_FEELINGS = [
  "This dealer's been shaky. AI confidence is high, Peter's gut agrees.",
  "Something feels off. The math is good but Peter's spider sense is tingling.",
  "The vibes are immaculate. Math and gut are in perfect harmony.",
  "Peter's seen this pattern before. The dealer's about to get wrecked.",
  "Steady session. The numbers say keep grinding.",
];

export default function SessionStats({ session, gameState }) {
  const { dealer_qualifies_pct = 0, remaining_deck = 52, favorable_outs = 0 } = gameState;
  const gutIdx = session.total_hands % GUT_FEELINGS.length;
  const gutFeeling = session.total_hands > 0 ? GUT_FEELINGS[gutIdx] : "Waiting for hand data...";

  return (
    <div style={S.panel}>
      <div style={S.title}><div style={S.dot} />Peter's Read</div>
      <div style={S.row}><span style={S.label}>Dealer qualifies</span><span style={{ ...S.val, color: 'var(--accent2)' }}>~{dealer_qualifies_pct}%</span></div>
      <div style={S.row}><span style={S.label}>Remaining deck</span><span style={S.val}>{remaining_deck}</span></div>
      <div style={S.row}><span style={S.label}>Favorable outs</span><span style={{ ...S.val, color: 'var(--accent)' }}>{favorable_outs}/{remaining_deck}</span></div>
      <div style={S.insight}>
        <div style={S.insightT}>Peter's Gut</div>
        <div style={S.insightM}>{gutFeeling}</div>
      </div>
    </div>
  );
}
