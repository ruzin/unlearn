import type { Itinerary } from "./itinerary";
import type { Money } from "./money";

export type BookingStatus =
  | "pending"
  | "confirmed"
  | "cancelled"
  | "refunded";

export interface Passenger {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  loyaltyId?: string;
}

export interface Booking {
  id: string;
  userId: string;
  itinerary: Itinerary;
  passengers: Passenger[];
  status: BookingStatus;
  total: Money;
}
