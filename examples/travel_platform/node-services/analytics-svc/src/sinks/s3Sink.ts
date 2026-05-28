import type { Event } from "../ingest/validator";

export async function writeToS3(event: Event): Promise<void> {
  console.log(`[s3] event ${event.name}`);
}
