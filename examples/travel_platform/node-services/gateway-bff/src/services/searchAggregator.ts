import { searchFlights, searchHotels } from "@travel/ts-common";

export async function aggregateSearch(origin: string, destination: string) {
  const [flights, hotels] = await Promise.all([
    searchFlights(origin, destination),
    searchHotels(destination),
  ]);
  return { flights, hotels };
}
