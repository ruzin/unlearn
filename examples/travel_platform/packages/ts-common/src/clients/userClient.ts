import type { User } from "../types/user";
import { TravelError } from "../errors/TravelError";

const BASE = process.env.USER_SVC_URL ?? "http://user-svc";

export async function getUser(id: string): Promise<User> {
  const res = await fetch(`${BASE}/users/${id}`);
  if (!res.ok) throw new TravelError("getUser failed");
  return (await res.json()) as User;
}
