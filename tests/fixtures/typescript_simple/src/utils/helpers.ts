export function formatCurrency(amount: number, currency: string = "usd"): string {
  return `${currency.toUpperCase()} ${amount.toFixed(2)}`;
}

export const slug = (value: string): string => value.toLowerCase().replace(/\s+/g, "-");
