import React, { useState, useEffect } from 'react';

const S = {
  container: { position: 'relative', flexShrink: 0 },
  toast: {
    display: 'flex', alignItems: 'center', gap: '10px',
    padding: '10px 14px', borderRadius: '10px',
    background: 'rgba(255, 215, 64, 0.08)',
    border: '1px solid rgba(255, 215, 64, 0.25)',
    marginBottom: '6px', animation: 'slideUp 0.4s ease',
    transition: 'opacity 0.5s', overflow: 'hidden', position: 'relative',
  },
  glow: {
    position: 'absolute', top: 0, left: 0, right: 0, height: '1px',
    background: 'linear-gradient(90deg, transparent, #FFD740, transparent)',
    opacity: 0.6,
  },
  icon: {
    width: '36px', height: '36px', borderRadius: '8px',
    background: 'rgba(255, 215, 64, 0.15)', border: '1px solid rgba(255, 215, 64, 0.25)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: '13px', fontWeight: 800, color: '#FFD740',
    fontFamily: 'var(--font-mono)', flexShrink: 0,
  },
  content: { flex: 1, minWidth: 0 },
  label: { fontSize: '8px', color: '#FFD740', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px' },
  name: { fontSize: '13px', fontWeight: 700, color: '#fff', marginTop: '1px' },
  desc: { fontSize: '10px', color: 'var(--text-secondary)', marginTop: '1px' },
  quip: { fontSize: '10px', color: 'var(--beer)', fontStyle: 'italic', marginTop: '3px' },
};

export default function AchievementToast({ achievements = [] }) {
  const [visible, setVisible] = useState([]);

  useEffect(() => {
    if (achievements.length === 0) return;
    const latest = achievements[achievements.length - 1];
    if (!latest) return;

    setVisible((prev) => [...prev, { ...latest, showTime: Date.now() }]);

    // Auto-dismiss after 8 seconds
    const timer = setTimeout(() => {
      setVisible((prev) => prev.filter((a) => Date.now() - a.showTime < 8000));
    }, 8000);

    return () => clearTimeout(timer);
  }, [achievements.length]);

  if (visible.length === 0) return null;

  return (
    <div style={S.container}>
      {visible.slice(-2).map((ach) => (
        <div key={ach.id || ach.key} style={S.toast}>
          <div style={S.glow} />
          <div style={S.icon}>{ach.icon}</div>
          <div style={S.content}>
            <div style={S.label}>Achievement unlocked</div>
            <div style={S.name}>{ach.name}</div>
            <div style={S.desc}>{ach.desc}</div>
            {ach.quip && <div style={S.quip}>"{ach.quip}"</div>}
          </div>
        </div>
      ))}
    </div>
  );
}
