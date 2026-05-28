import type { Request, Response, NextFunction } from "express";

import { createSession, getSession } from "../auth/session";

export function sessionMiddleware(
  req: Request,
  _res: Response,
  next: NextFunction,
): void {
  const token = (req.headers["authorization"] ?? "") as string;
  if (!getSession(token) && token) {
    createSession(token, `anon_${token.slice(0, 6)}`);
  }
  next();
}
