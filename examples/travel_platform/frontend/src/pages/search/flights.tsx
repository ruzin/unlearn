import { useRouter } from "next/router";

import { FlightCard } from "../../components/search/FlightCard";
import { useFlightSearch } from "../../hooks/useSearch";

export default function FlightSearchPage() {
  const router = useRouter();
  const origin = (router.query.origin as string) ?? "";
  const destination = (router.query.destination as string) ?? "";
  const { results, loading } = useFlightSearch(origin, destination);

  if (loading) return <p>Searching…</p>;

  return (
    <main>
      <h1>Flights {origin} → {destination}</h1>
      {results.map((r) => {
        const result = r as { itinerary_id: string; title: string; display: string };
        return (
          <FlightCard
            key={result.itinerary_id}
            title={result.title}
            display={result.display}
            onSelect={() => router.push(`/booking/new?it=${result.itinerary_id}`)}
          />
        );
      })}
    </main>
  );
}
