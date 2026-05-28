import type { Event } from "../ingest/validator";

export async function writeToWarehouse(event: Event): Promise<void> {
  console.log(`[warehouse] event ${event.name}`);
}
