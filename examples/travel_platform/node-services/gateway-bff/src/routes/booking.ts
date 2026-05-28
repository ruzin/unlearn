import { Router } from "express";

import {
  createBooking,
  confirmBooking,
  cancelBooking,
} from "@travel/ts-common";
import { requirePermission } from "../auth/permissions";

export const bookingRouter = Router();

bookingRouter.post("/", async (req, res) => {
  const token = (req.headers.authorization ?? "") as string;
  if (!requirePermission(token, "booking:write")) {
    res.status(403).json({ error: "forbidden" });
    return;
  }
  res.json(await createBooking(req.body));
});

bookingRouter.post("/:id/confirm", async (req, res) => {
  res.json(await confirmBooking(req.params.id));
});

bookingRouter.post("/:id/cancel", async (req, res) => {
  res.json(await cancelBooking(req.params.id));
});
