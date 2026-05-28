import { useRouter } from "next/router";

import { Button } from "../../components/common/Button";
import { apiPost } from "../../lib/apiClient";
import { getToken } from "../../lib/auth";

export default function BookingDetailPage() {
  const router = useRouter();
  const id = router.query.id as string;
  return (
    <main>
      <h1>Booking {id}</h1>
      <Button
        onClick={() => apiPost(`/bookings/${id}/confirm`, {}, getToken() ?? undefined)}
      >
        Confirm
      </Button>
    </main>
  );
}
