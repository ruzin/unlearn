import { validateToken } from "./jwt";
import { hasRole } from "./roles";

export function authMiddleware(req: { token: string }): { userId: number } | null {
  const payload = validateToken(req.token);
  if (payload === null) return null;
  if (!hasRole(payload.userId, "user")) return null;
  return payload;
}
