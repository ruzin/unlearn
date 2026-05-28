import { TravelError } from "../errors/TravelError";

const BASE = process.env.SEARCH_SVC_URL ?? "http://search-svc";

export async function searchFlights(origin: string, destination: string) {
  const res = await fetch(
    `${BASE}/search/flights?origin=${origin}&destination=${destination}`,
  );
  if (!res.ok) throw new TravelError("searchFlights failed");
  return res.json();
}

export async function searchHotels(city: string) {
  const res = await fetch(`${BASE}/search/hotels?city=${city}`);
  if (!res.ok) throw new TravelError("searchHotels failed");
  return res.json();
}
