import type { Money } from "@travel/ts-common";

const SYMBOLS: Record<string, string> = {
  USD: "$",
  EUR: "€",
  GBP: "£",
  JPY: "¥",
  AUD: "A$",
  CAD: "C$",
  INR: "₹",
};

export function formatPrice(money: Money): string {
  const symbol = SYMBOLS[money.currency] ?? money.currency;
  return `${symbol}${money.amount}`;
}
