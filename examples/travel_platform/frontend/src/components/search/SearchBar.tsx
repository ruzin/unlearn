import { useState } from "react";

import { Button } from "../common/Button";

interface Props {
  onSearch: (origin: string, destination: string) => void;
}

export function SearchBar({ onSearch }: Props) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSearch(origin, destination);
      }}
    >
      <input value={origin} onChange={(e) => setOrigin(e.target.value)} placeholder="From" />
      <input
        value={destination}
        onChange={(e) => setDestination(e.target.value)}
        placeholder="To"
      />
      <Button type="submit">Search</Button>
    </form>
  );
}
