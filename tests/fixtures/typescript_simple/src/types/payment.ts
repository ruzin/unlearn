import { UserType } from "./user";

export interface PaymentType {
  id: number;
  user: UserType;
  amount: number;
  currency: string;
}

export function makePayment(user: UserType, amount: number): PaymentType {
  return { id: 1, user, amount, currency: "usd" };
}
