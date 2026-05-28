import { TravelError } from "../errors/TravelError";

const BASE = process.env.LOYALTY_SVC_URL ?? "http://loyalty-svc";

export async function getLoyaltyAccount(userId: string) {
  const res = await fetch(`${BASE}/loyalty/accounts/${userId}`);
  if (!res.ok) throw new TravelError("getLoyaltyAccount failed");
  return res.json();
}

export async function redeemPoints(userId: string, points: number) {
  const res = await fetch(`${BASE}/loyalty/redemption/${userId}?points=${points}`, {
    method: "POST",
  });
  if (!res.ok) throw new TravelError("redeemPoints failed");
  return res.json();
}
