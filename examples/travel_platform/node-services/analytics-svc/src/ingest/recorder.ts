import type { Event } from "./validator";
import { writeToS3 } from "../sinks/s3Sink";
import { writeToWarehouse } from "../sinks/warehouseSink";

export async function recordEvent(event: Event): Promise<void> {
  await Promise.all([writeToS3(event), writeToWarehouse(event)]);
}
