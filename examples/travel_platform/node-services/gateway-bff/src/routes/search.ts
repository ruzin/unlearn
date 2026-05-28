import { Router } from "express";

import { searchFlights, searchHotels } from "@travel/ts-common";
import { aggregateSearch } from "../services/searchAggregator";

export const searchRouter = Router();

searchRouter.get("/flights", async (req, res) => {
  const { origin, destination } = req.query as Record<string, string>;
  const results = await searchFlights(origin, destination);
  res.json(results);
});

searchRouter.get("/hotels", async (req, res) => {
  const { city } = req.query as Record<string, string>;
  res.json(await searchHotels(city));
});

searchRouter.get("/all", async (req, res) => {
  const { origin, destination } = req.query as Record<string, string>;
  res.json(await aggregateSearch(origin, destination));
});
