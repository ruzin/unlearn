// Active SMS client (v2). smsV1Client in ../legacy/ is dead.
export async function sendSms(userId: string, body: string): Promise<void> {
  console.log(`[sms-v2 -> ${userId}] ${body}`);
}
