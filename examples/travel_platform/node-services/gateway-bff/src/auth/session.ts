// PLANTED CYCLE 1 of 3:
// session.ts -> middleware/rateLimit.ts -> auth/permissions.ts -> session.ts
//
// session needs to ask the rate-limiter how aggressive it should be for
// the current bucket (since heavy users get tighter session checks).
import { getRateLimitBucket } from "../middleware/rateLimit";

export interface Session {
  userId: string;
  token: string;
  tier: "anonymous" | "user" | "admin";
  bucket: string;
}

const SESSIONS = new Map<string, Session>();

export function createSession(token: string, userId: string): Session {
  const bucket = getRateLimitBucket(userId);
  const session: Session = {
    userId,
    token,
    tier: userId === "admin" ? "admin" : "user",
    bucket,
  };
  SESSIONS.set(token, session);
  return session;
}

export function getSession(token: string): Session | undefined {
  return SESSIONS.get(token);
}

export function expireSession(token: string): void {
  SESSIONS.delete(token);
}
