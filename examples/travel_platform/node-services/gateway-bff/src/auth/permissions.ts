// PLANTED CYCLE 3 of 3:
// permissions.ts -> auth/session.ts -> middleware/rateLimit.ts -> permissions.ts
//
// Permissions are derived from the current session. Closes the loop.
import { getSession } from "./session";

const PERMS_BY_TIER: Record<string, string[]> = {
  anonymous: ["search:read"],
  user: ["search:read", "booking:write", "loyalty:read"],
  admin: ["admin:*"],
};

export function getPermissions(token: string): string[] {
  const session = getSession(token);
  if (!session) return PERMS_BY_TIER.anonymous;
  return PERMS_BY_TIER[session.tier] ?? PERMS_BY_TIER.anonymous;
}

export function requirePermission(token: string, perm: string): boolean {
  return getPermissions(token).includes(perm);
}
