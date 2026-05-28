import { Card } from "../common/Card";

interface Props {
  title: string;
  display: string;
  onSelect: () => void;
}

export function FlightCard({ title, display, onSelect }: Props) {
  return (
    <Card>
      <div className="flight-card">
        <h3>{title}</h3>
        <p>{display}</p>
        <button onClick={onSelect}>Book</button>
      </div>
    </Card>
  );
}
