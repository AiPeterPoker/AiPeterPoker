import React, { useEffect, useRef } from 'react';

const TAG_STYLES = {
  THINK:  { bg: 'var(--peter-orange-dim)', color: 'var(--peter-orange)' },
  'AI-IN':{ bg: 'var(--accent-dim)', color: 'var(--accent)' },
  ACTION: { bg: 'var(--accent-dim)', color: 'var(--accent)' },
  ODDS:   { bg: 'var(--accent2-dim)', color: 'var(--accent2)' },
  READ:   { bg: 'var(--info-dim)', color: 'var(--info)' },
  RISK:   { bg: 'var(--danger-dim)', color: 'var(--danger)' },
  ERROR:  { bg: 'var(--danger-dim)', color: 'var(--danger)' },
  SYS:    { bg: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)' },
  PETER:  { bg: 'var(--beer-dim)', color: 'var(--beer)' },
  VISION: { bg: 'var(--info-dim)', color: 'var(--info)' },
  GTO:    { bg: 'var(--accent2-dim)', color: 'var(--accent2)' },
  KELLY:  { bg: 'var(--peter-orange-dim)', color: 'var(--peter-orange)' },
};

const S = {
  wrap: { flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 },
  title: {
    fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px',
    display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0,
  },
  dot: { width: 5, height: 5, borderRadius: '50%', background: 'var(--peter-orange)' },
  console: {
    flex: 1, background: 'rgba(0,0,0,0.35)',
    border: '0.5px solid var(--hud-border-subtle)', borderRadius: 'var(--radius-md)',
    padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: '12px',
    lineHeight: 1.8, overflowY: 'auto', minHeight: 0,
  },
  line: { display: 'flex', gap: '6px', alignItems: 'flex-start' },
  time: { color: 'var(--text-muted)', minWidth: '50px', fontSize: '10px', flexShrink: 0, paddingTop: '2px' },
  tag: {
    fontSize: '10px', padding: '1px 6px', borderRadius: '3px', fontWeight: 700,
    minWidth: '44px', textAlign: 'center', flexShrink: 0, letterSpacing: '0.3px',
  },
  msg: { color: 'rgba(255,255,255,0.7)', wordBreak: 'break-word' },
};

export default function ConsoleLog({ lines }) {
  const ref = useRef(null);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [lines]);

  return (
    <div style={S.wrap}>
      <div style={S.title}><div style={S.dot} />Peter's Brain</div>
      <div style={S.console} ref={ref}>
        {lines.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Peter's brain is warming up...
          </div>
        ) : lines.map((line) => {
          const ts = TAG_STYLES[line.tag] || TAG_STYLES.SYS;
          return (
            <div key={line.id} style={S.line}>
              <span style={S.time}>{line.time}</span>
              <span style={{ ...S.tag, background: ts.bg, color: ts.color }}>{line.tag}</span>
              <span style={S.msg}>{line.message}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
