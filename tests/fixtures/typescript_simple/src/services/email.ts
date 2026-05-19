import { UserType } from "../types/user";

export function sendWelcomeEmail(user: UserType): boolean {
  return sendEmail(user.email, "Welcome!", `Hello ${user.name}`);
}

function sendEmail(to: string, subject: string, body: string): boolean {
  return to.length > 0 && subject.length > 0 && body.length > 0;
}
