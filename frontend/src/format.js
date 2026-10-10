/** Format a price the way the rest of the app shows it: $1.50. */
export const money = (value) => `$${Number(value || 0).toFixed(2)}`;
