import { useRouter } from "next/router";

import { HotelCard } from "../../components/search/HotelCard";

export default function HotelSearchPage() {
  const router = useRouter();
  const city = (router.query.city as string) ?? "";
  return (
    <main>
      <h1>Hotels in {city}</h1>
      <HotelCard title={`Hotel in ${city}`} display="$199.00" />
    </main>
  );
}
