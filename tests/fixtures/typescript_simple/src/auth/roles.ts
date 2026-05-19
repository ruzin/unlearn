import { authMiddleware } from "./middleware";

export function hasRole(userId: number, role: string): boolean {
  return userId > 0 && role !== "";
}

export function requireRole(req: { token: string }, role: string): boolean {
  const payload = authMiddleware(req);
  if (payload === null) return false;
  return hasRole(payload.userId, role);
}
