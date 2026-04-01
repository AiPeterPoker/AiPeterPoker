import React, { useState, useEffect, useCallback } from 'react';

const SUIT_SYM = { h: '\u2665', d: '\u2666', s: '\u2660', c: '\u2663' };
const SUIT_COL = { h: '#ef4444', d: '#42A5F5', s: '#c8ccd4', c: '#c8ccd4' };

function MiniCard({ card }) {
  if (!card) return null;
  const suit = card.slice(-1);
  const rank = card.slice(0, -1).toUpperCase();
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '1px',
      padding: '2px 5px', borderRadius: '3px', background: '#fff',
      color: SUIT_COL[suit] || '#1a1a2e', fontWeight: 700, fontSize: '10px',
      fontFamily: 'var(--font-mono)', border: '1px solid rgba(0,0,0,0.08)',
      boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
    }}>
      {rank}<span style={{ fontSize: '8px' }}>{SUIT_SYM[suit] || suit}</span>
    </span>
  );
}

const S = {
  panel: {
    background: 'var(--hud-bg-panel)', border: '0.5px solid var(--hud-border-subtle)',
    borderRadius: 'var(--radius-md)', padding: '12px 14px',
    maxHeight: '400px', display: 'flex', flexDirection: 'column',
  },
  title: {
    fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0,
  },
  dot: { width: 4, height: 4, borderRadius: '50%', background: 'var(--info)', display: 'inline-block', marginRight: '6px' },
  tabs: { display: 'flex', gap: '4px', marginBottom: '8px', flexShrink: 0 },
  tab: {
    padding: '4px 10px', borderRadius: '4px', fontSize: '9px', fontWeight: 600,
    cursor: 'pointer', border: 'none', fontFamily: 'var(--font-display)',
    transition: 'all 0.15s',
  },
  tabActive: { background: 'var(--accent-dim)', color: 'var(--accent)' },
  tabInactive: { background: 'rgba(255,255,255,0.04)', color: 'var(--text-muted)' },
  list: { flex: 1, overflowY: 'auto', minHeight: 0 },
  handRow: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '6px 8px', borderRadius: '5px', marginBottom: '3px',
    background: 'rgba(255,255,255,0.02)', cursor: 'pointer',
    border: '0.5px solid transparent', transition: 'all 0.15s',
  },
  handRowHover: { background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.06)' },
  handNum: {
    fontSize: '9px', fontWeight: 700, color: 'var(--text-muted)',
    fontFamily: 'var(--font-mono)', minWidth: '24px',
  },
  handCards: { display: 'flex', gap: '3px', flex: 1 },
  handAction: {
    fontSize: '9px', fontWeight: 700, padding: '2px 6px',
    borderRadius: '3px', textTransform: 'uppercase', letterSpacing: '0.3px',
  },
  handPnl: { fontSize: '10px', fontWeight: 700, fontFamily: 'var(--font-mono)', minWidth: '50px', textAlign: 'right' },
  handConf: { fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', minWidth: '30px', textAlign: 'right' },
  detail: {
    padding: '10px 12px', background: 'rgba(0,0,0,0.2)',
    borderRadius: '6px', marginTop: '4px', animation: 'slideUp 0.2s ease',
  },
  detailRow: { display: 'flex', justifyContent: 'space-between', fontSize: '10px', padding: '2px 0' },
  detailLabel: { color: 'var(--text-muted)' },
  detailVal: { fontWeight: 600, fontFamily: 'var(--font-mono)' },
  reasoning: {
    marginTop: '6px', padding: '6px 8px', background: 'var(--beer-dim)',
    borderRadius: '4px', fontSize: '10px', color: 'var(--text-secondary)',
    fontStyle: 'italic', lineHeight: 1.5,
  },
  empty: { color: 'var(--text-muted)', fontSize: '11px', textAlign: 'center', padding: '20px', fontStyle: 'italic' },
  closeBtn: { fontSize: '10px', color: 'var(--text-muted)', cursor: 'pointer', background: 'none', border: 'none', padding: '2px 6px' },
};

const ACTION_STYLES = {
  fold: { background: 'var(--danger-dim)', color: 'var(--danger)' },
  call: { background: 'var(--accent2-dim)', color: 'var(--accent2)' },
  raise: { background: 'var(--accent-dim)', color: 'var(--accent)' },
};

export default function HandReplayViewer({ onClose }) {
  const [hands, setHands] = useState([]);
  const [activeTab, setActiveTab] = useState('recent');
  const [selectedHand, setSelectedHand] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchHands = useCallback(async (tab) => {
    setLoading(true);
    try {
      const endpoints = {
        recent: '/api/replay/recent?limit=30',
        best: '/api/replay/best?limit=20',
        worst: '/api/replay/worst?limit=20',
      };
      const res = await fetch(`http://localhost:8765${endpoints[tab]}`);
      const data = await res.json();
      setHands(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Replay fetch error:', e);
      setHands([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchHands(activeTab); }, [activeTab, fetchHands]);

  const parseCards = (val) => {
    if (Array.isArray(val)) return val;
    try { return JSON.parse(val); } catch { return []; }
  };

  return (
    <div style={S.panel}>
      <div style={S.title}>
        <span><span style={S.dot} />Hand replay</span>
        <button style={S.closeBtn} onClick={onClose}>Close</button>
      </div>

      <div style={S.tabs}>
        {['recent', 'best', 'worst'].map((tab) => (
          <button
            key={tab}
            style={{ ...S.tab, ...(activeTab === tab ? S.tabActive : S.tabInactive) }}
            onClick={() => { setActiveTab(tab); setSelectedHand(null); }}
          >
            {tab === 'recent' ? 'Recent' : tab === 'best' ? 'Best hands' : 'Worst hands'}
          </button>
        ))}
      </div>

      <div style={S.list}>
        {loading ? (
          <div style={S.empty}>Loading Peter's history...</div>
        ) : hands.length === 0 ? (
          <div style={S.empty}>No hands recorded yet. Start a session first!</div>
        ) : (
          hands.map((hand) => {
            const holeCards = parseCards(hand.hole_cards);
            const communityCards = parseCards(hand.community_cards);
            const action = hand.decision_action || 'call';
            const pnl = hand.pnl || 0;
            const isSelected = selectedHand === hand.id;
            const astyle = ACTION_STYLES[action] || ACTION_STYLES.call;

            return (
              <div key={hand.id}>
                <div
                  style={{ ...S.handRow, ...(isSelected ? S.handRowHover : {}) }}
                  onClick={() => setSelectedHand(isSelected ? null : hand.id)}
                >
                  <span style={S.handNum}>#{hand.hand_number}</span>
                  <div style={S.handCards}>
                    {holeCards.map((c, i) => <MiniCard key={`h${i}`} card={c} />)}
                    {communityCards.length > 0 && (
                      <span style={{ color: 'var(--text-muted)', fontSize: '8px', alignSelf: 'center', margin: '0 2px' }}>|</span>
                    )}
                    {communityCards.map((c, i) => <MiniCard key={`c${i}`} card={c} />)}
                  </div>
                  <span style={{ ...S.handAction, ...astyle }}>{action}</span>
                  <span style={{ ...S.handPnl, color: pnl >= 0 ? 'var(--accent)' : 'var(--danger)' }}>
                    {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                  </span>
                  <span style={S.handConf}>{hand.decision_confidence || 0}%</span>
                </div>

                {isSelected && (
                  <div style={S.detail}>
                    <div style={S.detailRow}>
                      <span style={S.detailLabel}>Hand</span>
                      <span style={S.detailVal}>{hand.hand_name || 'N/A'}</span>
                    </div>
                    <div style={S.detailRow}>
                      <span style={S.detailLabel}>Win probability</span>
                      <span style={{ ...S.detailVal, color: 'var(--accent)' }}>{hand.win_probability?.toFixed(1) || 0}%</span>
                    </div>
                    <div style={S.detailRow}>
                      <span style={S.detailLabel}>Expected value</span>
                      <span style={{ ...S.detailVal, color: (hand.expected_value || 0) >= 0 ? 'var(--accent)' : 'var(--danger)' }}>
                        {(hand.expected_value || 0) >= 0 ? '+' : ''}${(hand.expected_value || 0).toFixed(2)}
                      </span>
                    </div>
                    <div style={S.detailRow}>
                      <span style={S.detailLabel}>Confidence</span>
                      <span style={{ ...S.detailVal, color: 'var(--accent2)' }}>{hand.decision_confidence || 0}%</span>
                    </div>
                    <div style={S.detailRow}>
                      <span style={S.detailLabel}>Pot size</span>
                      <span style={S.detailVal}>${(hand.pot_size || 0).toFixed(2)}</span>
                    </div>
                    {hand.agent_reasoning && (
                      <div style={S.reasoning}>
                        Peter's take: {typeof hand.agent_reasoning === 'string'
                          ? hand.agent_reasoning.replace(/^"|"$/g, '')
                          : JSON.stringify(hand.agent_reasoning)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
