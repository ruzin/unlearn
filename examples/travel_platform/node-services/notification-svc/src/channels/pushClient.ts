export async function sendPush(userId: string, body: string): Promise<void> {
  console.log(`[push -> ${userId}] ${body}`);
}
