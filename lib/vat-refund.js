// Vietnam's tourist VAT refund. Foreign passport holders get back 85% of the
// VAT on eligible goods; the refunding bank keeps the other 15%
// (Decree 181/2025/ND-CP, Appendix IV; procedures in Circular 84/2026/TT-BTC).
// Shop prices include VAT.
export const REFUND_SHARE_OF_VAT = 0.85;

// Standard VAT is 10%, cut to 8% from 1 Jul 2025 to 31 Dec 2026
// (Resolution 204/2025/QH15, Decree 174/2025/ND-CP). Since July 2025 the cut
// also covers IT goods such as computers and phones.
const STANDARD_VAT_PERCENT = 10;
const REDUCED_VAT_PERCENT = 8;
const REDUCED_VAT_ENDS = new Date("2027-01-01T00:00:00+07:00");

export function vatPercentOn(date = new Date()) {
  return date < REDUCED_VAT_ENDS ? REDUCED_VAT_PERCENT : STANDARD_VAT_PERCENT;
}

// Share of a VAT-inclusive price paid back: 8/108 x 85% = 6.30% while VAT is
// 8%, 10/110 x 85% = 7.73% at 10%.
export function refundShareOfPrice(date = new Date()) {
  const vat = vatPercentOn(date);
  return (vat / (100 + vat)) * REFUND_SHARE_OF_VAT;
}

export function vatRefundFor(priceIncludingVat, date = new Date()) {
  return priceIncludingVat * refundShareOfPrice(date);
}
