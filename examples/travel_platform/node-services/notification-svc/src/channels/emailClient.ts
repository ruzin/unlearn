export async function sendEmail(userId: string, body: string): Promise<void> {
  console.log(`[email -> ${userId}] ${body}`);
}
