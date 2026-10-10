/** Format a price the way the rest of the app shows it: ₹219, ₹1,234.50. */
export const money = (value) =>
  `₹${Number(value || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
