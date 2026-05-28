import { Router } from "express";

import { dispatch } from "../channels/dispatcher";

export const notifyRouter = Router();

notifyRouter.post("/", async (req, res) => {
  const { userId, channel, template, payload } = req.body as {
    userId: string;
    channel: "email" | "sms" | "push";
    template: string;
    payload: Record<string, unknown>;
  };
  await dispatch(channel, userId, template, payload);
  res.json({ ok: true });
});
