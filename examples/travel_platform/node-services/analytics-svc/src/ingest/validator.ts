export interface Event {
  name: string;
  userId?: string;
  ts: number;
  props: Record<string, unknown>;
}

export function validateEvent(raw: Record<string, unknown>): Event {
  if (typeof raw.name !== "string") throw new Error("event.name required");
  return {
    name: raw.name,
    userId: typeof raw.userId === "string" ? raw.userId : undefined,
    ts: typeof raw.ts === "number" ? raw.ts : Date.now(),
    props: (raw.props as Record<string, unknown>) ?? {},
  };
}
