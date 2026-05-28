import { useEffect, useState } from "react";

import { apiGet } from "../lib/apiClient";

export function useFlightSearch(origin: string, destination: string) {
  const [results, setResults] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!origin || !destination) return;
    setLoading(true);
    apiGet<{ results: unknown[] }>(
      `/search/flights?origin=${origin}&destination=${destination}`,
    )
      .then((data) => setResults(data.results))
      .finally(() => setLoading(false));
  }, [origin, destination]);

  return { results, loading };
}
