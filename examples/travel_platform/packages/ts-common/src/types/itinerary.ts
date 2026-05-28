import type { Money } from "./money";

export type TripType = "flight" | "hotel" | "car" | "package";

export interface Itinerary {
  id: string;
  tripType: TripType;
  origin: string;
  destination: string;
  departAt: string;
  returnAt?: string;
  basePrice: Money;
}
