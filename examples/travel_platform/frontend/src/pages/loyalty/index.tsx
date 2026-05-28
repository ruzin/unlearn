import { useEffect, useState } from "react";

import { apiGet } from "../../lib/apiClient";
import { getToken } from "../../lib/auth";

export default function LoyaltyPage() {
  const [data, setData] = useState<{ points: number; tier: string } | null>(null);
  useEffect(() => {
    apiGet<{ loyalty: { points: number; tier: string } }>(
      "/account/usr_current",
      getToken() ?? undefined,
    ).then((d) => setData(d.loyalty));
  }, []);
  if (!data) return <p>Loading…</p>;
  return (
    <main>
      <h1>Loyalty</h1>
      <p>Points: {data.points}</p>
      <p>Tier: {data.tier}</p>
    </main>
  );
}
