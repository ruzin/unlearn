import type { Money } from "@travel/ts-common";

import { PriceTag } from "../common/PriceTag";

export function PaymentSummary({ subtotal, taxes, total }: { subtotal: Money; taxes: Money; total: Money }) {
  return (
    <div className="payment-summary">
      <div>Subtotal: <PriceTag money={subtotal} /></div>
      <div>Taxes: <PriceTag money={taxes} /></div>
      <strong>Total: <PriceTag money={total} /></strong>
    </div>
  );
}
