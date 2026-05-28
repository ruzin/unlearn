import { useState } from "react";

import { apiPost } from "../lib/apiClient";
import { getToken } from "../lib/auth";

export function useCreateBooking() {
  const [pending, setPending] = useState(false);

  async function create(payload: {
    userId: string;
    itineraryId: string;
    passengerIds: string[];
  }) {
    setPending(true);
    try {
      return await apiPost("/bookings", payload, getToken() ?? undefined);
    } finally {
      setPending(false);
    }
  }

  return { create, pending };
}
