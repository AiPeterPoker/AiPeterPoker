import React, { useState, useEffect, useCallback } from 'react';
import wsManager from '../utils/websocket';

const S = {
  panel: {
    background: 'var(--hud-bg-panel)',
    border: '0.5px solid var(--hud-border-subtle)',
    borderRadius: 'var(--radius-md)',
    padding: '12px 14px',
    maxHeight: '50vh',
    overflowY: 'auto',
  },
  title: {
    fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '10px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  },
  dot: { width: 4, height: 4, borderRadius: '50%', background: 'var(--text-muted)', display: 'inline-block', marginRight: '6px' },
  row: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '6px 0', borderBottom: '0.5px solid rgba(255,255,255,0.03)',
  },
  label: { fontSize: '11px', color: 'var(--text-secondary)' },
  sublabel: { fontSize: '9px', color: 'var(--text-muted)', marginTop: '1px' },
  slider: {
    width: '120px', height: '4px', appearance: 'none', background: 'rgba(255,255,255,0.1)',
    borderRadius: '2px', outline: 'none', cursor: 'pointer',
  },
  sliderVal: { fontSize: '11px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--accent)', minWidth: '36px', textAlign: 'right' },
  toggle: {
    width: '32px', height: '18px', borderRadius: '9px', position: 'relative',
    cursor: 'pointer', transition: 'background 0.2s',
  },
  toggleDot: {
    width: '14px', height: '14px', borderRadius: '50%', background: '#fff',
    position: 'absolute', top: '2px', transition: 'left 0.2s',
  },
  select: {
    background: 'rgba(255,255,255,0.06)', border: '0.5px solid rgba(255,255,255,0.1)',
    borderRadius: '4px', padding: '4px 8px', fontSize: '11px', color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)', outline: 'none', cursor: 'pointer',
  },
  closeBtn: {
    fontSize: '10px', color: 'var(--text-muted)', cursor: 'pointer',
    background: 'none', border: 'none', padding: '2px 6px',
  },
  sectionTitle: {
    fontSize: '10px', fontWeight: 700, color: 'var(--accent)',
    textTransform: 'uppercase', letterSpacing: '1px', marginTop: '12px', marginBottom: '6px',
    paddingTop: '8px', borderTop: '0.5px solid rgba(255,255,255,0.06)',
  },
  calibBtn: {
    padding: '4px 10px', borderRadius: '4px', fontSize: '10px', fontWeight: 600,
    border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)',
  },
  calibDone: { background: 'rgba(76,175,80,0.15)', color: '#4CAF50' },
  calibPending: { background: 'rgba(255,215,64,0.15)', color: '#FFD740' },
  calibActive: { background: 'rgba(76,175,80,0.3)', color: '#fff', animation: 'pulse 1s infinite' },
  calibHint: { fontSize: '9px', color: 'var(--text-muted)', marginTop: '6px', lineHeight: '1.4' },
};

export default function SettingsPanel({ settings, onSettingsChange, onClose, gameMode = 'poker' }) {
  const [local, setLocal] = useState({
    gtoStrictness: settings?.gtoStrictness ?? 0.8,
    captureInterval: settings?.captureInterval ?? 2000,
    personality: settings?.personality ?? 'overconfident',
    overlayOpacity: settings?.overlayOpacity ?? 92,
    mcIterations: settings?.mcIterations ?? 10000,
  });

  const [autoPlay, setAutoPlay] = useState(false);
  const pokerBtns = { ante: false, play: false, fold: false };
  const bjBtns = { chip: false, bet: false, hit: false, stand: false, double: false, split: false };
  const [calibration, setCalibration] = useState(gameMode === 'blackjack' ? bjBtns : pokerBtns);
  const [calibrating, setCalibrating] = useState(null); // which button we're calibrating

  useEffect(() => {
    wsManager.send('get_calibration');
    const unsub = wsManager.on('calibration_status', (data) => {
      if (data.calibration) setCalibration(data.calibration);
      if (data.enabled !== undefined) setAutoPlay(data.enabled);
    });
    return unsub;
  }, []);

  // Listen for calibration completion — reset to idle after 1 click
  useEffect(() => {
    if (!calibrating) return;
    const unsub = wsManager.on('calibration_status', (data) => {
      if (data.just_calibrated === calibrating) {
        // Only clear if this is the button we were waiting for
        setCalibrating(null);
        if (data.calibration) setCalibration(data.calibration);
      }
    });
    return unsub;
  }, [calibrating]);

  const toggleAutoPlay = () => {
    const next = !autoPlay;
    setAutoPlay(next);
    wsManager.send('toggle_autoplay', { enabled: next });
  };

  const startCalibration = (button) => {
    setCalibrating(button);
    wsManager.send('calibrate_button', { button });
  };

  const update = (key, value) => {
    const next = { ...local, [key]: value };
    setLocal(next);
    if (onSettingsChange) onSettingsChange(next);
  };

  return (
    <div style={S.panel}>
      <div style={S.title}>
        <span><span style={S.dot} />Peter's settings</span>
        <button style={S.closeBtn} onClick={onClose}>Close</button>
      </div>

      {/* Personality */}
      <div style={S.row}>
        <div>
          <div style={S.label}>Peter's personality</div>
          <div style={S.sublabel}>Changes console tone & risk level</div>
        </div>
        <select
          style={S.select}
          value={local.personality}
          onChange={(e) => update('personality', e.target.value)}
        >
          <option value="overconfident">Overconfident</option>
          <option value="cautious">Cautious</option>
          <option value="degenerate">Degenerate</option>
        </select>
      </div>

      {/* GTO Strictness */}
      <div style={S.row}>
        <div>
          <div style={S.label}>GTO strictness</div>
          <div style={S.sublabel}>0 = Peter's gut, 1 = pure math</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            type="range" min="0" max="100" step="5"
            value={local.gtoStrictness * 100}
            onChange={(e) => update('gtoStrictness', parseInt(e.target.value) / 100)}
            style={S.slider}
          />
          <span style={S.sliderVal}>{(local.gtoStrictness * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Monte Carlo Iterations */}
      <div style={S.row}>
        <div>
          <div style={S.label}>Monte Carlo iterations</div>
          <div style={S.sublabel}>More = accurate, slower</div>
        </div>
        <select
          style={S.select}
          value={local.mcIterations}
          onChange={(e) => update('mcIterations', parseInt(e.target.value))}
        >
          <option value="1000">1,000 (fast)</option>
          <option value="5000">5,000</option>
          <option value="10000">10,000 (default)</option>
          <option value="50000">50,000 (precise)</option>
        </select>
      </div>

      {/* Capture Interval */}
      <div style={S.row}>
        <div>
          <div style={S.label}>Capture interval</div>
          <div style={S.sublabel}>Screenshot frequency</div>
        </div>
        <select
          style={S.select}
          value={local.captureInterval}
          onChange={(e) => update('captureInterval', parseInt(e.target.value))}
        >
          <option value="1000">1s (aggressive)</option>
          <option value="2000">2s (default)</option>
          <option value="3000">3s (chill)</option>
          <option value="5000">5s (lazy)</option>
        </select>
      </div>

      {/* Auto-Play Section */}
      <div style={S.sectionTitle}>Auto-Play</div>

      {/* Auto-Play Toggle */}
      <div style={S.row}>
        <div>
          <div style={S.label}>Peter clicks for you</div>
          <div style={S.sublabel}>Requires calibrated buttons</div>
        </div>
        <div
          style={{ ...S.toggle, background: autoPlay ? 'var(--accent)' : 'rgba(255,255,255,0.15)' }}
          onClick={toggleAutoPlay}
        >
          <div style={{ ...S.toggleDot, left: autoPlay ? '16px' : '2px' }} />
        </div>
      </div>

      {/* Calibration Buttons */}
      {(gameMode === 'blackjack' ? ['chip', 'bet', 'hit', 'stand', 'double', 'split'] : ['ante', 'play', 'fold']).map((btn) => (
        <div style={S.row} key={btn}>
          <div>
            <div style={S.label}>{btn.charAt(0).toUpperCase() + btn.slice(1)} button</div>
            <div style={S.sublabel}>{calibration[btn] ? 'Calibrated' : 'Not set'}</div>
          </div>
          <button
            style={{
              ...S.calibBtn,
              ...(calibrating === btn ? S.calibActive : calibration[btn] ? S.calibDone : S.calibPending),
              ...(calibrating && calibrating !== btn ? { opacity: 0.3, pointerEvents: 'none' } : {}),
            }}
            disabled={!!calibrating && calibrating !== btn}
            onClick={() => !calibrating && startCalibration(btn)}
          >
            {calibrating === btn ? 'Click on casino...' : calibration[btn] ? 'Recalibrate' : 'Calibrate'}
          </button>
        </div>
      ))}

      {calibrating && (
        <div style={S.calibHint}>
          Click the <strong>{calibrating.toUpperCase()}</strong> button on your casino window. Peter will remember where it is.
        </div>
      )}

      {!calibration.ante && !calibration.play && !calibration.fold && (
        <div style={S.calibHint}>
          Calibrate each button by clicking it on the casino screen. Peter needs to know where to click.
        </div>
      )}
    </div>
  );
}
