import { Router } from "express";

import { recordEvent } from "./recorder";
import { validateEvent } from "./validator";

export const ingestRouter = Router();

ingestRouter.post("/", async (req, res) => {
  const event = req.body as Record<string, unknown>;
  const validated = validateEvent(event);
  await recordEvent(validated);
  res.json({ ok: true });
});
