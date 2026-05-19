import { UserType } from "../types/user";
import { PaymentType } from "../types/payment";

export function chargeCustomer(user: UserType, payment: PaymentType): { id: string } {
  const customer = getOrCreateCustomer(user);
  return createCharge(customer, payment.amount, payment.currency);
}

function getOrCreateCustomer(user: UserType): { id: string } {
  return { id: `cus_${user.id}` };
}

function createCharge(customer: { id: string }, amount: number, currency: string): { id: string } {
  return signCharge({ customerId: customer.id, amount, currency });
}

function signCharge(input: { customerId: string; amount: number; currency: string }): { id: string } {
  return { id: `ch_${input.customerId}_${input.amount}` };
}
