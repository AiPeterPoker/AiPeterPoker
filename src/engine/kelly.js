/**
 * Kelly Criterion Calculator
 * Calculates optimal bet sizing based on edge and bankroll.
 */

/**
 * Full Kelly bet size
 * f* = (bp - q) / b
 * @param {number} winPct - Win probability (0-100)
 * @param {number} odds - Pot odds ratio (e.g., 3.2 for 3.2:1)
 * @param {number} bankroll - Current bankroll
 * @returns {number} Optimal bet size
 */
export function kellyBet(winPct, odds, bankroll) {
  const p = winPct / 100;
  const q = 1 - p;
  const b = Math.max(odds, 0.01);
  const kelly = Math.max(0, (b * p - q) / b);
  return Math.round(bankroll * kelly * 100) / 100;
}

/**
 * Fractional Kelly bet size (safer)
 * @param {number} winPct - Win probability (0-100)
 * @param {number} odds - Pot odds ratio
 * @param {number} bankroll - Current bankroll
 * @param {number} fraction - Kelly fraction (0.25 = quarter Kelly)
 * @returns {number} Conservative bet size
 */
export function fractionalKelly(winPct, odds, bankroll, fraction = 0.25) {
  return Math.round(kellyBet(winPct, odds, bankroll) * fraction * 100) / 100;
}

/**
 * Calculate risk of ruin given Kelly sizing
 * @param {number} winPct - Win probability (0-100)
 * @param {number} kellyFraction - Fraction of Kelly being used
 * @returns {number} Risk of ruin percentage (0-100)
 */
export function riskOfRuin(winPct, kellyFraction = 0.25) {
  const p = winPct / 100;
  const q = 1 - p;
  if (p <= q) return 100; // Negative edge
  const ror = Math.pow(q / p, 1 / kellyFraction);
  return Math.round(ror * 10000) / 100;
}

/**
 * Check if a bet is within Kelly bounds
 * @param {number} betSize - Proposed bet
 * @param {number} bankroll - Current bankroll
 * @param {number} maxKellyPct - Maximum % of bankroll per bet (default 5%)
 * @returns {{ safe: boolean, maxBet: number, pctOfBankroll: number }}
 */
export function validateBetSize(betSize, bankroll, maxKellyPct = 5) {
  const pct = (betSize / bankroll) * 100;
  const maxBet = bankroll * (maxKellyPct / 100);
  return {
    safe: pct <= maxKellyPct,
    maxBet: Math.round(maxBet * 100) / 100,
    pctOfBankroll: Math.round(pct * 100) / 100,
  };
}
