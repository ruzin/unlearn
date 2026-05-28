import { dispatch } from "../channels/dispatcher";

const QUEUE: Array<{ channel: "email" | "sms" | "push"; userId: string; template: string; payload: Record<string, unknown> }> = [];

export function enqueue(job: typeof QUEUE[number]): void {
  QUEUE.push(job);
}

export function startQueueWorker(): void {
  setInterval(async () => {
    while (QUEUE.length) {
      const job = QUEUE.shift()!;
      await dispatch(job.channel, job.userId, job.template, job.payload);
    }
  }, 250);
}
