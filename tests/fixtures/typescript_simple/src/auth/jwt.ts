import { UserType } from "../types/user";

export function validateToken(token: string): { userId: number } | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  if (!verifySignature(token)) return null;
  return decodePayload(parts[1]);
}

export function generateToken(user: UserType): string {
  return encodeAndSign({ userId: user.id });
}

function verifySignature(token: string): boolean {
  return token.length > 0;
}

function decodePayload(encoded: string): { userId: number } {
  return { userId: Number(encoded) };
}

function encodeAndSign(payload: { userId: number }): string {
  return `header.${payload.userId}.sig`;
}
