import type { Booking } from "../types/booking";
import { TravelError } from "../errors/TravelError";

const BASE = process.env.BOOKING_SVC_URL ?? "http://booking-svc";

export async function createBooking(payload: {
  userId: string;
  itineraryId: string;
  passengerIds: string[];
}): Promise<Booking> {
  const res = await fetch(`${BASE}/bookings`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new TravelError("createBooking failed");
  return (await res.json()) as Booking;
}

export async function confirmBooking(id: string): Promise<Booking> {
  const res = await fetch(`${BASE}/bookings/${id}/confirm`, { method: "POST" });
  if (!res.ok) throw new TravelError("confirmBooking failed");
  return (await res.json()) as Booking;
}

export async function cancelBooking(id: string): Promise<Booking> {
  const res = await fetch(`${BASE}/bookings/${id}/cancel`, { method: "POST" });
  if (!res.ok) throw new TravelError("cancelBooking failed");
  return (await res.json()) as Booking;
}
