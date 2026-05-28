import { useRouter } from "next/router";

import { PassengerForm } from "../../components/booking/PassengerForm";
import { useCreateBooking } from "../../hooks/useBooking";

export default function NewBookingPage() {
  const router = useRouter();
  const itineraryId = (router.query.it as string) ?? "";
  const { create, pending } = useCreateBooking();

  return (
    <main>
      <h1>New booking</h1>
      <p>Itinerary: {itineraryId}</p>
      <PassengerForm
        onSubmit={async (p) => {
          const result = await create({
            userId: "usr_current",
            itineraryId,
            passengerIds: [`${p.firstName}-${p.lastName}`],
          });
          const booking = result as { id: string };
          router.push(`/booking/${booking.id}`);
        }}
      />
      {pending && <p>Creating…</p>}
    </main>
  );
}
