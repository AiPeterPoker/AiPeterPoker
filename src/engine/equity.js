/**
 * Client-side equity display helpers.
 * Heavy lifting is done server-side; these format results for the overlay.
 */

/** Format win probability with color class */
export function formatWinPct(pct) {
  const rounded = Math.round(pct * 10) / 10;
  let color = 'var(--danger)';
  if (rounded >= 65) color = 'var(--accent)';
  else if (rounded >= 40) color = 'var(--accent2)';
  return { value: `${rounded}%`, color };
}

/** Format expected value */
export function formatEV(ev) {
  const sign = ev >= 0 ? '+' : '';
  const color = ev >= 0 ? 'var(--accent)' : 'var(--danger)';
  return { value: `${sign}$${Math.abs(ev).toFixed(2)}`, color };
}

/** Format pot odds */
export function formatPotOdds(odds) {
  if (!odds || odds <= 0) return { value: '—', color: 'var(--text-muted)' };
  return { value: `${odds.toFixed(1)}:1`, color: 'var(--accent2)' };
}

/** Map hand rank number to human-readable tier */
export function handTier(rank) {
  const tiers = {
    9: { name: 'Royal Flush', tier: 'legendary', color: '#ffd700' },
    8: { name: 'Straight Flush', tier: 'legendary', color: '#ffd700' },
    7: { name: 'Four of a Kind', tier: 'monster', color: 'var(--accent)' },
    6: { name: 'Full House', tier: 'monster', color: 'var(--accent)' },
    5: { name: 'Flush', tier: 'strong', color: 'var(--accent)' },
    4: { name: 'Straight', tier: 'strong', color: 'var(--accent)' },
    3: { name: 'Three of a Kind', tier: 'good', color: 'var(--accent2)' },
    2: { name: 'Two Pair', tier: 'good', color: 'var(--accent2)' },
    1: { name: 'One Pair', tier: 'marginal', color: 'var(--text-secondary)' },
    0: { name: 'High Card', tier: 'weak', color: 'var(--danger)' },
  };
  return tiers[rank] || tiers[0];
}

/** Calculate simplified outs percentage using rule of 2 and 4 */
export function quickOutsPct(outs, cardsTocome) {
  if (cardsTocome === 2) return Math.min(outs * 4, 100);
  if (cardsTocome === 1) return Math.min(outs * 2, 100);
  return 0;
}
