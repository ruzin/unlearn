import { BOOKING_CONFIRMED } from "./bookingConfirmed";
import { BOOKING_CANCELLED } from "./bookingCancelled";
import { WELCOME } from "./welcome";

const TEMPLATES: Record<string, string> = {
  booking_confirmed: BOOKING_CONFIRMED,
  booking_cancelled: BOOKING_CANCELLED,
  welcome: WELCOME,
};

export function renderTemplate(
  template: string,
  payload: Record<string, unknown>,
): string {
  let body = TEMPLATES[template] ?? "(unknown template)";
  for (const [k, v] of Object.entries(payload)) {
    body = body.replaceAll(`{{${k}}}`, String(v));
  }
  return body;
}
