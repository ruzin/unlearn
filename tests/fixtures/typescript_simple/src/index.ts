import { getUser, createUser } from "./routes/users";
import { createPaymentEndpoint } from "./routes/payments";

export const routes = {
  "GET /users/:id": getUser,
  "POST /users": createUser,
  "POST /payments": createPaymentEndpoint,
};

export function main(): typeof routes {
  return routes;
}
