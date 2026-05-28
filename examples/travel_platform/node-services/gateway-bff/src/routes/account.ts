import { Router } from "express";

import { getUser, getLoyaltyAccount } from "@travel/ts-common";

export const accountRouter = Router();

accountRouter.get("/:id", async (req, res) => {
  const [user, loyalty] = await Promise.all([
    getUser(req.params.id),
    getLoyaltyAccount(req.params.id),
  ]);
  res.json({ user, loyalty });
});
