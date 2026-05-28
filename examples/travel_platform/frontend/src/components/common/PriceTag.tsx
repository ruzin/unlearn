import type { Money } from "@travel/ts-common";

import { formatPrice } from "../../lib/formatPrice";

export function PriceTag({ money }: { money: Money }) {
  return <span className="price">{formatPrice(money)}</span>;
}
