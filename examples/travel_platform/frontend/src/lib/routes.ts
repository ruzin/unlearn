export const routes = {
  home: "/",
  searchFlights: (origin: string, destination: string) =>
    `/search/flights?origin=${origin}&destination=${destination}`,
  searchHotels: (city: string) => `/search/hotels?city=${city}`,
  booking: (id: string) => `/booking/${id}`,
  account: "/account",
  loyalty: "/loyalty",
};
