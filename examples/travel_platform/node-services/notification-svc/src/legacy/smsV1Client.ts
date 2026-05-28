// DEAD CODE — v1 SMS gateway (Twilio classic). Replaced by ../channels/smsClient.ts.
// Nothing imports this file. Planted dead-code scenario.

export async function sendSmsV1(phoneNumber: string, body: string): Promise<void> {
  console.log(`[sms-v1 -> ${phoneNumber}] ${body}`);
}

export function legacyFormatPhone(raw: string): string {
  return raw.replace(/[^0-9+]/g, "");
}

export async function legacySendBulkSms(
  recipients: string[],
  body: string,
): Promise<void> {
  for (const r of recipients) {
    await sendSmsV1(r, body);
  }
}
