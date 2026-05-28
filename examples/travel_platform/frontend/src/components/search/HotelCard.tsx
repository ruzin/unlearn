import { Card } from "../common/Card";

interface Props {
  title: string;
  display: string;
}

export function HotelCard({ title, display }: Props) {
  return (
    <Card>
      <h3>{title}</h3>
      <p>{display}</p>
    </Card>
  );
}
