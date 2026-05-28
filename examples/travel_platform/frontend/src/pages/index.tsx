import { useRouter } from "next/router";

import { SearchBar } from "../components/search/SearchBar";
import { routes } from "../lib/routes";

export default function Home() {
  const router = useRouter();
  return (
    <main>
      <h1>Travel</h1>
      <SearchBar onSearch={(o, d) => router.push(routes.searchFlights(o, d))} />
    </main>
  );
}
