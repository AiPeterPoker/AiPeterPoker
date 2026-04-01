import React, { useMemo } from 'react';

const S = {
  panel: {
    background: 'var(--hud-bg-panel)',
    border: '0.5px solid var(--hud-border-subtle)',
    borderRadius: 'var(--radius-md)',
    padding: '12px 14px',
  },
  title: {
    fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '10px',
    display: 'flex', alignItems: 'center', gap: '6px',
  },
  dot: { width: 4, height: 4, borderRadius: '50%', display: 'inline-block' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '8px', marginBottom: '12px' },
  stat: {
    padding: '8px 10px', borderRadius: '6px',
    background: 'rgba(255,255,255,0.03)',
  },
  statLabel: { fontSize: '8px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' },
  statVal: { fontSize: '16px', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '2px' },
  chartArea: { position: 'relative', height: '100px', marginBottom: '12px' },
  sparkline: { width: '100%', height: '100%' },
  barRow: { display: 'flex', gap: '4px', alignItems: 'flex-end', height: '40px', marginBottom: '4px' },
  bar: { flex: 1, borderRadius: '3px 3px 0 0', transition: 'height 0.5s', minHeight: '2px' },
  barLabel: { display: 'flex', justifyContent: 'space-between', fontSize: '8px', color: 'var(--text-muted)' },
  section: { marginBottom: '12px' },
  sectionTitle: { fontSize: '9px', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' },
  actionBar: { display: 'flex', gap: '6px' },
  actionItem: { flex: 1, textAlign: 'center', padding: '6px', borderRadius: '5px', background: 'rgba(255,255,255,0.03)' },
  actionPct: { fontSize: '14px', fontWeight: 700, fontFamily: 'var(--font-mono)' },
  actionLabel: { fontSize: '8px', color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: '2px' },
};

function MiniSparkline({ data, color = 'var(--accent)', height = 80 }) {
  if (!data || data.length < 2) {
    return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '10px' }}>Collecting data...</div>;
  }

  const values = data.map(d => d.cumulative || 0);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 100;

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = height - ((v - min) / range) * (height - 10) - 5;
    return `${x},${y}`;
  }).join(' ');

  const fillPoints = `0,${height} ${points} ${w},${height}`;
  const isPositive = values[values.length - 1] >= values[0];
  const lineColor = isPositive ? 'var(--accent)' : 'var(--danger)';
  const fillColor = isPositive ? 'rgba(76,175,80,0.1)' : 'rgba(255,82,82,0.1)';

  return (
    <svg viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none" style={{ width: '100%', height }}>
      <polygon points={fillPoints} fill={fillColor} />
      <polyline points={points} fill="none" stroke={lineColor} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export default function AnalyticsDashboard({ analytics, session }) {
  const {
    pnl_series = [],
    action_distribution = {},
    total_hands = 0,
  } = analytics || {};

  const totalActions = Object.values(action_distribution).reduce((a, b) => a + b, 0) || 1;
  const actionPcts = {
    fold: Math.round((action_distribution.fold || 0) / totalActions * 100),
    call: Math.round((action_distribution.call || 0) / totalActions * 100),
    raise: Math.round((action_distribution.raise || 0) / totalActions * 100),
  };

  const biggestWin = pnl_series.length > 0 ? Math.max(...pnl_series.map(d => d.pnl || 0)) : 0;
  const biggestLoss = pnl_series.length > 0 ? Math.min(...pnl_series.map(d => d.pnl || 0)) : 0;
  const avgConfidence = pnl_series.length > 0
    ? Math.round(pnl_series.reduce((s, d) => s + (d.confidence || 0), 0) / pnl_series.length)
    : 0;

  return (
    <div style={S.panel}>
      <div style={S.title}>
        <div style={{ ...S.dot, background: 'var(--info)' }} />
        Session analytics
      </div>

      {/* Quick stats */}
      <div style={S.grid}>
        <div style={S.stat}>
          <div style={S.statLabel}>Session P&L</div>
          <div style={{ ...S.statVal, color: (session?.session_pnl || 0) >= 0 ? 'var(--accent)' : 'var(--danger)' }}>
            {(session?.session_pnl || 0) >= 0 ? '+' : ''}${(session?.session_pnl || 0).toFixed(0)}
          </div>
        </div>
        <div style={S.stat}>
          <div style={S.statLabel}>Best hand</div>
          <div style={{ ...S.statVal, color: 'var(--accent)' }}>+${biggestWin.toFixed(0)}</div>
        </div>
        <div style={S.stat}>
          <div style={S.statLabel}>Worst hand</div>
          <div style={{ ...S.statVal, color: 'var(--danger)' }}>${biggestLoss.toFixed(0)}</div>
        </div>
        <div style={S.stat}>
          <div style={S.statLabel}>Avg confidence</div>
          <div style={{ ...S.statVal, color: 'var(--accent2)' }}>{avgConfidence}%</div>
        </div>
      </div>

      {/* P&L Sparkline */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Cumulative P&L</div>
        <MiniSparkline data={pnl_series} height={70} />
      </div>

      {/* Action distribution */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Action distribution</div>
        <div style={S.actionBar}>
          <div style={S.actionItem}>
            <div style={{ ...S.actionPct, color: 'var(--danger)' }}>{actionPcts.fold}%</div>
            <div style={S.actionLabel}>Fold</div>
          </div>
          <div style={S.actionItem}>
            <div style={{ ...S.actionPct, color: 'var(--accent2)' }}>{actionPcts.call}%</div>
            <div style={S.actionLabel}>Call</div>
          </div>
          <div style={S.actionItem}>
            <div style={{ ...S.actionPct, color: 'var(--accent)' }}>{actionPcts.raise}%</div>
            <div style={S.actionLabel}>Raise</div>
          </div>
        </div>
      </div>
    </div>
  );
}
