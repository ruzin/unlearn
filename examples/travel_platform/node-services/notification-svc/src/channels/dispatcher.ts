import { sendEmail } from "./emailClient";
import { sendPush } from "./pushClient";
import { sendSms } from "./smsClient";
import { renderTemplate } from "../templates/render";

export async function dispatch(
  channel: "email" | "sms" | "push",
  userId: string,
  template: string,
  payload: Record<string, unknown>,
): Promise<void> {
  const body = renderTemplate(template, payload);
  switch (channel) {
    case "email":
      return sendEmail(userId, body);
    case "sms":
      return sendSms(userId, body);
    case "push":
      return sendPush(userId, body);
  }
}
