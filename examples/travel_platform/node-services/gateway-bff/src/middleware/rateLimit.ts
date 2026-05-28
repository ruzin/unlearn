// PLANTED CYCLE 2 of 3:
// rateLimit.ts -> auth/permissions.ts -> auth/session.ts -> rateLimit.ts
//
// Rate-limiting policy depends on the caller's permission set: admins get
// looser limits than anonymous users.
import type { Request, Response, NextFunction } from "express";

import { getPermissions } from "../auth/permissions";

const BUCKETS = new Map<string, number>();

export function getRateLimitBucket(userId: string): string {
  if (userId.startsWith("admin")) return "premium";
  if (userId.startsWith("anon")) return "anonymous";
  return "standard";
}

export function rateLimitMiddleware(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const token = (req.headers["authorization"] ?? "") as string;
  const perms = getPermissions(token);
  const limit = perms.includes("admin:*") ? 10_000 : 100;
  const used = BUCKETS.get(token) ?? 0;
  if (used >= limit) {
    res.status(429).json({ error: "rate_limited" });
    return;
  }
  BUCKETS.set(token, used + 1);
  next();
}
