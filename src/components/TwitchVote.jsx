import React, { useState, useEffect } from 'react';

const S = {
  panel: {
    background: 'rgba(145, 70, 255, 0.06)',
    border: '0.5px solid rgba(145, 70, 255, 0.2)',
    borderRadius: 'var(--radius-md)',
    padding: '10px 12px',
    marginBottom: '8px',
    flexShrink: 0,
  },
  title: {
    fontSize: '9px', fontWeight: 700, color: '#9146FF',
    textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  },
  dot: { width: 4, height: 4, borderRadius: '50%', background: '#9146FF', display: 'inline-block', marginRight: '6px' },
  timer: { fontSize: '11px', fontWeight: 700, color: '#9146FF', fontFamily: 'var(--font-mono)' },
  voteRow: { display: 'flex', gap: '6px', marginBottom: '6px' },
  voteOption: {
    flex: 1, padding: '8px 6px', borderRadius: '6px', textAlign: 'center',
    border: '0.5px solid rgba(255,255,255,0.06)', transition: 'all 0.3s',
    position: 'relative', overflow: 'hidden',
  },
  voteFill: {
    position: 'absolute', left: 0, bottom: 0, height: '100%',
    transition: 'width 0.5s ease', opacity: 0.15, borderRadius: '6px',
  },
  votePct: { fontSize: '16px', fontWeight: 700, fontFamily: 'var(--font-mono)', position: 'relative', zIndex: 1 },
  voteLabel: { fontSize: '9px', textTransform: 'uppercase', position: 'relative', zIndex: 1, marginTop: '2px' },
  voteCount: { fontSize: '8px', color: 'var(--text-muted)', position: 'relative', zIndex: 1 },
  footer: { display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-muted)' },
  chatLine: {
    fontSize: '10px', padding: '1px 0', display: 'flex', gap: '4px',
    fontFamily: 'var(--font-mono)', lineHeight: 1.5,
  },
  chatUser: { color: '#9146FF', fontWeight: 600, flexShrink: 0 },
  chatMsg: { color: 'var(--text-secondary)' },
  chatBox: {
    marginTop: '6px', padding: '6px 8px',
    background: 'rgba(0,0,0,0.2)', borderRadius: '5px',
    maxHeight: '60px', overflowY: 'auto',
  },
};

const ACTION_COLORS = {
  fold: 'var(--danger)',
  call: 'var(--accent2)',
  raise: 'var(--accent)',
};

export default function TwitchVote({ voteData, chatMessages = [], isOpen = false }) {
  if (!isOpen && (!voteData || voteData.total === 0)) return null;

  const { total = 0, percentages = {}, winner = 'call', time_remaining = 0 } = voteData || {};

  return (
    <div style={S.panel}>
      <div style={S.title}>
        <span><span style={S.dot} />Twitch chat vote</span>
        {isOpen && <span style={S.timer}>{time_remaining}s</span>}
      </div>

      <div style={S.voteRow}>
        {['fold', 'call', 'raise'].map((action) => {
          const pct = percentages[action] || 0;
          const isWinner = action === winner && total > 0;
          const color = ACTION_COLORS[action];

          return (
            <div
              key={action}
              style={{
                ...S.voteOption,
                ...(isWinner ? { borderColor: color, background: 'rgba(255,255,255,0.03)' } : {}),
              }}
            >
              <div style={{ ...S.voteFill, width: `${pct}%`, background: color }} />
              <div style={{ ...S.votePct, color: isWinner ? color : 'var(--text-muted)' }}>{pct}%</div>
              <div style={{ ...S.voteLabel, color: isWinner ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                {action}
              </div>
            </div>
          );
        })}
      </div>

      <div style={S.footer}>
        <span>{total} votes</span>
        <span>{isOpen ? 'Voting open' : `Chat says: ${winner.toUpperCase()}`}</span>
      </div>

      {chatMessages.length > 0 && (
        <div style={S.chatBox}>
          {chatMessages.slice(-5).map((msg, i) => (
            <div key={i} style={S.chatLine}>
              <span style={S.chatUser}>{msg.username}:</span>
              <span style={S.chatMsg}>{msg.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
