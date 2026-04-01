/**
 * GTO Lookup Tables for Casino Hold'em
 * Client-side reference for displaying GTO recommendations.
 */

export const PREFLOP_CHART = {
  premium:  { fold: 0,  call: 15, raise: 85, description: 'AA, KK, QQ, AKs — Always play aggressively' },
  strong:   { fold: 5,  call: 30, raise: 65, description: 'JJ-1010, AQs, AKo — Strong starting hands' },
  playable: { fold: 10, call: 55, raise: 35, description: '99-77, AJs, KQs — Playable with position' },
  marginal: { fold: 30, call: 55, raise: 15, description: '66-22, suited connectors — Situational' },
  weak:     { fold: 60, call: 35, raise: 5,  description: 'Low offsuit hands — Usually fold' },
  trash:    { fold: 85, call: 15, raise: 0,  description: 'Worst hands — Almost always fold' },
};

export const POSTFLOP_CHART = {
  monster:  { fold: 0,  call: 10, raise: 90, description: 'Straight+, top set — Maximum value' },
  strong:   { fold: 5,  call: 25, raise: 70, description: 'Overpair, TPTK — Build the pot' },
  good:     { fold: 10, call: 50, raise: 40, description: 'Top pair, two pair — Solid hand' },
  drawing:  { fold: 20, call: 60, raise: 20, description: 'Flush/straight draw — Need improvement' },
  marginal: { fold: 40, call: 50, raise: 10, description: 'Mid pair, weak draw — Proceed with caution' },
  weak:     { fold: 70, call: 25, raise: 5,  description: 'Bottom pair, no draw — Usually fold' },
  nothing:  { fold: 85, call: 15, raise: 0,  description: 'No pair, no draw — Almost always fold' },
};

/**
 * Get the best GTO action from a recommendation
 * @param {{ fold: number, call: number, raise: number }} gto
 * @returns {string} Best action
 */
export function bestGTOAction(gto) {
  return Object.entries(gto)
    .filter(([k]) => ['fold', 'call', 'raise'].includes(k))
    .sort((a, b) => b[1] - a[1])[0][0];
}

/**
 * Casino Hold'em specific: should we ante?
 * Basic strategy says play ~82% of hands in Casino Hold'em.
 */
export const CASINO_HOLDEM_PLAY_THRESHOLD = 18; // Fold worst 18% of hands
