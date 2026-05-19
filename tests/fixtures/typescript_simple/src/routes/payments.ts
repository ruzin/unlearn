import { authMiddleware } from "../auth/middleware";
import { makeUser } from "../types/user";
import { makePayment, PaymentType } from "../types/payment";
import { chargeCustomer } from "../services/stripe";

export function createPaymentEndpoint(req: { token: string; amount: number }): { payment: PaymentType } | { error: string } {
  const payload = authMiddleware(req);
  if (payload === null) return { error: "Unauthorized" };
  const user = makeUser(payload.userId, "user@example.com");
  const payment = makePayment(user, req.amount);
  chargeCustomer(user, payment);
  return { payment };
}
