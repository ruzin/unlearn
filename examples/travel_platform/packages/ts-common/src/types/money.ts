export type CurrencyCode =
  | "USD"
  | "EUR"
  | "GBP"
  | "JPY"
  | "AUD"
  | "CAD"
  | "INR";

export interface Money {
  amount: string;
  currency: CurrencyCode;
}

export interface DisplayMoney extends Money {
  display: string;
}
