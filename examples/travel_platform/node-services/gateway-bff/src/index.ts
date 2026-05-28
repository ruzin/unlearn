import express from "express";

import { searchRouter } from "./routes/search";
import { bookingRouter } from "./routes/booking";
import { accountRouter } from "./routes/account";
import { sessionMiddleware } from "./middleware/session";
import { rateLimitMiddleware } from "./middleware/rateLimit";

const app = express();
app.use(express.json());
app.use(sessionMiddleware);
app.use(rateLimitMiddleware);
app.use("/search", searchRouter);
app.use("/bookings", bookingRouter);
app.use("/account", accountRouter);

app.get("/healthz", (_, res) => res.json({ status: "ok" }));

const port = Number(process.env.PORT ?? 8080);
app.listen(port, () => console.log(`gateway-bff listening on ${port}`));
