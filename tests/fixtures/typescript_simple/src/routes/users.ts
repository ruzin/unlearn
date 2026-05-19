import { authMiddleware } from "../auth/middleware";
import { makeUser, UserType } from "../types/user";
import { sendWelcomeEmail } from "../services/email";

export function getUser(req: { token: string; userId: number }): { user: UserType } | { error: string } {
  const payload = authMiddleware(req);
  if (payload === null) return { error: "Unauthorized" };
  return { user: makeUser(req.userId, "test@example.com") };
}

export function createUser(req: { token: string; email: string }): { user: UserType } | { error: string } {
  const payload = authMiddleware(req);
  if (payload === null) return { error: "Unauthorized" };
  const user = makeUser(1, req.email);
  sendWelcomeEmail(user);
  return { user };
}
